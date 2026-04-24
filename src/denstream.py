"""Modern Python 3 DenStream-style online outlier detection.

This ports the core ideas used by Putina et al.'s OutlierDenStream code:
faded micro-clusters, separate potential/core and outlier micro-clusters,
automatic epsilon estimation from an initial normal buffer, and sample-level
outlier decisions from online merging behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
import copy
import math

import numpy as np


def fading_factor(lamb: float, steps: int | float) -> float:
    return math.pow(2.0, -float(lamb) * float(steps))


@dataclass
class Prediction:
    outlier: bool
    score: float
    nearest_core_distance: float
    nearest_outlier_distance: float
    p_micro_clusters: int
    o_micro_clusters: int


class MicroCluster:
    def __init__(self, creation_timestamp: int, lamb: float, cluster_number: int):
        self.creation_timestamp = int(creation_timestamp)
        self.last_edit_timestamp = int(creation_timestamp)
        self.lamb = float(lamb)
        self.cluster_number = int(cluster_number)
        self.weight = 0.0
        self.linear_sum: np.ndarray | None = None
        self.squared_sum: np.ndarray | None = None
        self.center: np.ndarray | None = None
        self.radius = 0.0
        self.n_samples = 0

    def _ensure_arrays(self, x: np.ndarray) -> None:
        if self.linear_sum is None:
            self.linear_sum = np.zeros_like(x, dtype=float)
            self.squared_sum = np.zeros_like(x, dtype=float)
            self.center = np.zeros_like(x, dtype=float)

    def decay(self, steps: int = 1) -> None:
        factor = fading_factor(self.lamb, steps)
        self.weight *= factor
        if self.linear_sum is not None:
            self.linear_sum *= factor
            self.squared_sum *= factor
            self._recompute_center_radius()

    def insert(self, x: np.ndarray, timestamp: int) -> None:
        x = np.asarray(x, dtype=float)
        self._ensure_arrays(x)
        self.decay(1)
        self.weight += 1.0
        self.linear_sum += x
        self.squared_sum += np.square(x)
        self.n_samples += 1
        self.last_edit_timestamp = int(timestamp)
        self._recompute_center_radius()

    def _recompute_center_radius(self) -> None:
        if self.weight <= 0 or self.linear_sum is None or self.squared_sum is None:
            return
        self.center = self.linear_sum / self.weight
        variance = (self.squared_sum / self.weight) - np.square(self.center)
        variance = np.maximum(variance, 0.0)
        self.radius = float(np.nanmax(np.sqrt(variance))) if variance.size else 0.0

    def distance_to_boundary(self, x: np.ndarray) -> float:
        if self.center is None:
            return float("inf")
        return float(np.linalg.norm(np.asarray(x, dtype=float) - self.center) - self.radius)


class DenStream:
    def __init__(
        self,
        lamb: float = 0.15,
        epsilon: float | str = "auto",
        beta: float = 0.05,
        mu: float | str = "auto",
        tp: int = 30,
        cluster_cap: int | None = None,
    ):
        self.lamb = float(lamb)
        self.epsilon_param = epsilon
        self.beta = float(beta)
        self.mu_param = mu
        self.tp = int(tp)
        self.cluster_cap = int(cluster_cap) if cluster_cap is not None else None
        self.timestamp = 0
        self.p_micro_clusters: list[MicroCluster] = []
        self.o_micro_clusters: list[MicroCluster] = []
        self.epsilon: float | None = None
        self.mu: float | None = None
        self.beta_mu: float | None = None

    def fit_initial(self, X: np.ndarray) -> None:
        X = np.asarray(X, dtype=float)
        if X.ndim != 2 or X.shape[0] == 0:
            raise ValueError("DenStream initialization requires a nonempty 2-D buffer.")

        self.timestamp = 0
        self.p_micro_clusters = []
        self.o_micro_clusters = []
        self.mu = self._resolve_mu()
        self.beta_mu = self.beta * self.mu

        mc = MicroCluster(creation_timestamp=1, lamb=self.lamb, cluster_number=1)
        radii = []
        for idx, x in enumerate(X, start=1):
            self.timestamp = idx
            mc.insert(x, idx)
            radii.append(mc.radius)
        self.p_micro_clusters.append(mc)
        self.epsilon = self._resolve_epsilon(X, radii)

    def _resolve_mu(self) -> float:
        if isinstance(self.mu_param, str):
            if self.mu_param != "auto":
                raise ValueError(f"Unsupported mu mode: {self.mu_param}")
            return 1.0 / (1.0 - fading_factor(self.lamb, 1))
        return float(self.mu_param)

    def _resolve_epsilon(self, X: np.ndarray, radii: list[float]) -> float:
        if not isinstance(self.epsilon_param, str):
            return max(float(self.epsilon_param), 1e-9)
        positive_radii = np.asarray([value for value in radii[10:] if value > 0], dtype=float)
        if positive_radii.size:
            epsilon = float(np.max(positive_radii))
        else:
            center = np.mean(X, axis=0)
            distances = np.linalg.norm(X - center, axis=1)
            epsilon = float(np.percentile(distances, 95)) if distances.size else 1.0
        if not np.isfinite(epsilon) or epsilon <= 0:
            epsilon = 1.0
        return epsilon

    def _nearest(self, x: np.ndarray, clusters: list[MicroCluster]) -> tuple[MicroCluster | None, float]:
        if not clusters:
            return None, float("inf")
        distances = [cluster.distance_to_boundary(x) for cluster in clusters]
        idx = int(np.argmin(distances))
        return clusters[idx], float(distances[idx])

    def _decay_unmerged(self, merged_cluster: MicroCluster | None) -> None:
        for cluster in self.p_micro_clusters + self.o_micro_clusters:
            if cluster is not merged_cluster:
                cluster.decay(1)

    def _replace_cluster(self, clusters: list[MicroCluster], old: MicroCluster, new: MicroCluster) -> None:
        idx = clusters.index(old)
        clusters[idx] = new

    def _prune(self) -> None:
        assert self.beta_mu is not None
        self.p_micro_clusters = [cluster for cluster in self.p_micro_clusters if cluster.weight >= self.beta_mu]
        kept_outliers = []
        for cluster in self.o_micro_clusters:
            xs1 = fading_factor(self.lamb, self.timestamp - cluster.creation_timestamp + self.tp) - 1.0
            xs2 = fading_factor(self.lamb, self.tp) - 1.0
            threshold = xs1 / xs2 if xs2 != 0 else 0.0
            if cluster.weight >= threshold:
                kept_outliers.append(cluster)
        self.o_micro_clusters = kept_outliers
        self._enforce_cluster_cap()

    def _enforce_cluster_cap(self) -> None:
        if self.cluster_cap is None or self.cluster_cap <= 0:
            return
        if len(self.p_micro_clusters) > self.cluster_cap:
            self.p_micro_clusters = sorted(self.p_micro_clusters, key=lambda c: c.weight, reverse=True)[
                : self.cluster_cap
            ]
        if len(self.o_micro_clusters) > self.cluster_cap:
            self.o_micro_clusters = sorted(self.o_micro_clusters, key=lambda c: c.weight, reverse=True)[
                : self.cluster_cap
            ]

    def partial_fit_predict(self, x: np.ndarray) -> Prediction:
        if self.epsilon is None or self.mu is None or self.beta_mu is None:
            raise RuntimeError("Call fit_initial before streaming samples.")

        self.timestamp += 1
        x = np.asarray(x, dtype=float)
        merged = False
        outlier = True
        nearest_core, core_dist = self._nearest(x, self.p_micro_clusters)
        nearest_outlier_dist = float("inf")
        merged_cluster: MicroCluster | None = None

        if nearest_core is not None:
            candidate = copy.deepcopy(nearest_core)
            candidate.insert(x, self.timestamp)
            if candidate.radius <= self.epsilon:
                self._replace_cluster(self.p_micro_clusters, nearest_core, candidate)
                merged = True
                outlier = False
                merged_cluster = candidate

        if not merged:
            nearest_outlier, nearest_outlier_dist = self._nearest(x, self.o_micro_clusters)
            if nearest_outlier is not None:
                candidate = copy.deepcopy(nearest_outlier)
                candidate.insert(x, self.timestamp)
                if candidate.radius <= self.epsilon:
                    self.o_micro_clusters.remove(nearest_outlier)
                    if candidate.weight > self.beta_mu:
                        candidate.cluster_number = len(self.p_micro_clusters) + 1
                        self.p_micro_clusters.append(candidate)
                    else:
                        self.o_micro_clusters.append(candidate)
                    merged = True
                    merged_cluster = candidate

        if not merged:
            candidate = MicroCluster(self.timestamp, self.lamb, len(self.o_micro_clusters) + 1)
            candidate.insert(x, self.timestamp)
            self.o_micro_clusters.append(candidate)
            merged_cluster = candidate

        self._decay_unmerged(merged_cluster)
        if self.tp > 0 and self.timestamp % self.tp == 0:
            self._prune()
        else:
            self._enforce_cluster_cap()

        distance = core_dist if np.isfinite(core_dist) else nearest_outlier_dist
        if not np.isfinite(distance):
            distance = self.epsilon
        score = max(0.0, float(distance / max(self.epsilon, 1e-9)))
        if outlier:
            score = max(score, 1.0)
        return Prediction(
            outlier=outlier,
            score=score,
            nearest_core_distance=core_dist,
            nearest_outlier_distance=nearest_outlier_dist,
            p_micro_clusters=len(self.p_micro_clusters),
            o_micro_clusters=len(self.o_micro_clusters),
        )


def run_denstream(
    X: np.ndarray,
    times: np.ndarray,
    sample_skip: int = 39,
    lamb: float = 0.15,
    beta: float = 0.05,
    epsilon: float | str = "auto",
    mu: float | str = "auto",
    cluster_cap: int | None = None,
    tp: int = 30,
) -> tuple[list[dict], dict]:
    X = np.asarray(X, dtype=float)
    if X.shape[0] <= sample_skip:
        raise ValueError(f"Need more than sample_skip={sample_skip} samples; got {X.shape[0]}.")
    model = DenStream(lamb=lamb, epsilon=epsilon, beta=beta, mu=mu, tp=tp, cluster_cap=cluster_cap)
    model.fit_initial(X[:sample_skip])

    records: list[dict] = []
    for idx in range(X.shape[0]):
        if idx < sample_skip:
            records.append(
                {
                    "timestamp": float(times[idx]),
                    "sample_index": idx,
                    "outlier": False,
                    "score": 0.0,
                    "nearest_core_distance": 0.0,
                    "nearest_outlier_distance": 0.0,
                    "p_micro_clusters": len(model.p_micro_clusters),
                    "o_micro_clusters": len(model.o_micro_clusters),
                }
            )
            continue
        prediction = model.partial_fit_predict(X[idx])
        records.append(
            {
                "timestamp": float(times[idx]),
                "sample_index": idx,
                "outlier": bool(prediction.outlier),
                "score": prediction.score,
                "nearest_core_distance": prediction.nearest_core_distance,
                "nearest_outlier_distance": prediction.nearest_outlier_distance,
                "p_micro_clusters": prediction.p_micro_clusters,
                "o_micro_clusters": prediction.o_micro_clusters,
            }
        )
    metadata = {
        "lambda": lamb,
        "beta": beta,
        "epsilon": model.epsilon,
        "mu": model.mu,
        "cluster_cap": cluster_cap,
        "tp": tp,
        "sample_skip": sample_skip,
    }
    return records, metadata
