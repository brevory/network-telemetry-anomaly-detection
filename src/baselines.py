"""Baseline anomaly detectors used for comparison."""

from __future__ import annotations

import numpy as np
from sklearn.cluster import DBSCAN, MiniBatchKMeans
from sklearn.neighbors import NearestNeighbors


def _auto_dbscan_eps(X_baseline: np.ndarray, min_samples: int = 5) -> float:
    if len(X_baseline) <= 1:
        return 1.0
    neighbors = min(max(2, min_samples), len(X_baseline))
    nn = NearestNeighbors(n_neighbors=neighbors)
    nn.fit(X_baseline)
    distances, _ = nn.kneighbors(X_baseline)
    kth = distances[:, -1]
    eps = float(np.percentile(kth, 95))
    return eps if np.isfinite(eps) and eps > 0 else 1.0


def dbscan_predictions(X: np.ndarray, sample_skip: int = 39, min_samples: int = 5) -> tuple[np.ndarray, np.ndarray, dict]:
    """Run DBSCAN over the whole node matrix.

    This is a transductive baseline and is documented as such because it sees
    the full dataset at once, unlike DenStream.
    """

    X = np.asarray(X, dtype=float)
    baseline = X[: max(1, min(sample_skip, len(X)))]
    eps = _auto_dbscan_eps(baseline, min_samples=min_samples)
    model = DBSCAN(eps=eps, min_samples=min_samples, algorithm="auto")
    labels = model.fit_predict(X)
    outliers = labels == -1
    if hasattr(model, "components_") and len(model.components_) > 0:
        nn = NearestNeighbors(n_neighbors=1).fit(model.components_)
        distances, _ = nn.kneighbors(X)
        scores = distances[:, 0] / max(eps, 1e-9)
    else:
        scores = np.where(outliers, 1.0, 0.0)
    return outliers.astype(bool), scores.astype(float), {"eps": eps, "min_samples": min_samples}


def minibatch_kmeans_predictions(
    X: np.ndarray,
    sample_skip: int = 39,
    n_clusters: int = 3,
    threshold_quantile: float = 0.99,
) -> tuple[np.ndarray, np.ndarray, dict]:
    X = np.asarray(X, dtype=float)
    baseline_rows = max(2, min(sample_skip, len(X)))
    clusters = max(1, min(n_clusters, baseline_rows))
    model = MiniBatchKMeans(n_clusters=clusters, random_state=42, n_init="auto", batch_size=max(16, baseline_rows))
    model.fit(X[:baseline_rows])
    baseline_distances = np.min(model.transform(X[:baseline_rows]), axis=1)
    threshold = float(np.quantile(baseline_distances, threshold_quantile))
    if not np.isfinite(threshold) or threshold <= 0:
        threshold = float(np.mean(baseline_distances) + 3 * np.std(baseline_distances))
    if not np.isfinite(threshold) or threshold <= 0:
        threshold = 1.0

    scores = np.zeros(len(X), dtype=float)
    outliers = np.zeros(len(X), dtype=bool)
    for idx, x in enumerate(X):
        distance = float(np.min(model.transform([x])))
        scores[idx] = distance / max(threshold, 1e-9)
        outliers[idx] = idx >= baseline_rows and distance > threshold
        if not outliers[idx]:
            model.partial_fit([x])
    return outliers, scores, {"n_clusters": clusters, "threshold": threshold, "threshold_quantile": threshold_quantile}
