"""Temporal and spatial alarm generation from sample-level outlier decisions."""

from __future__ import annotations

import pandas as pd


def temporal_alarms(predictions: pd.DataFrame, k_values: range | list[int] = range(1, 6)) -> pd.DataFrame:
    rows = []
    if predictions.empty:
        return pd.DataFrame()
    for (dataset, feature_mode, method, node), group in predictions.groupby(
        ["dataset", "feature_mode", "method", "node"], dropna=False
    ):
        group = group.sort_values("timestamp")
        run_length = 0
        run_scores = []
        emitted_for_run: set[int] = set()
        for row in group.itertuples(index=False):
            if bool(row.outlier):
                run_length += 1
                run_scores.append(float(row.score))
                for k in k_values:
                    if run_length >= k and k not in emitted_for_run:
                        rows.append(
                            {
                                "dataset": dataset,
                                "feature_mode": feature_mode,
                                "method": method,
                                "detection_type": "temporal",
                                "k": k,
                                "timestamp": float(row.timestamp),
                                "nodes": str(node),
                                "score": max(run_scores[-k:]),
                                "outlier_count": k,
                            }
                        )
                        emitted_for_run.add(k)
            else:
                run_length = 0
                run_scores = []
                emitted_for_run = set()
    return pd.DataFrame(rows)


def spatial_alarms(predictions: pd.DataFrame, k_values: range | list[int] = range(1, 6)) -> pd.DataFrame:
    rows = []
    if predictions.empty:
        return pd.DataFrame()
    df = predictions.copy()
    df["time_slot"] = df["timestamp"].round().astype("int64")
    for (dataset, feature_mode, method, time_slot), group in df.groupby(
        ["dataset", "feature_mode", "method", "time_slot"], dropna=False
    ):
        outliers = group[group["outlier"].astype(bool)].copy()
        if outliers.empty:
            continue
        outliers = outliers.sort_values("score", ascending=False)
        for k in k_values:
            if len(outliers) >= k:
                top = outliers.head(k)
                rows.append(
                    {
                        "dataset": dataset,
                        "feature_mode": feature_mode,
                        "method": method,
                        "detection_type": "spatial",
                        "k": k,
                        "timestamp": float(time_slot),
                        "nodes": ";".join(top["node"].astype(str).tolist()),
                        "score": float(top["score"].max()),
                        "outlier_count": int(len(outliers)),
                    }
                )
    return pd.DataFrame(rows)


def build_alarms(predictions: pd.DataFrame, kmax: int = 5) -> pd.DataFrame:
    k_values = range(1, kmax + 1)
    frames = [temporal_alarms(predictions, k_values), spatial_alarms(predictions, k_values)]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        return pd.DataFrame(
            columns=[
                "dataset",
                "feature_mode",
                "method",
                "detection_type",
                "k",
                "timestamp",
                "nodes",
                "score",
                "outlier_count",
            ]
        )
    return pd.concat(frames, ignore_index=True).sort_values(
        ["dataset", "feature_mode", "method", "detection_type", "k", "timestamp"]
    )
