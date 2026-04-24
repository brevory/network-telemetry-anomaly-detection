"""Feature selection, cleaning, and baseline-only normalization."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data_loader import CONTROL_PLANE_FEATURES


FEATURE_MODES = ("ControlPlane", "DataPlane", "CompleteFeatures")
TEXT_OR_ID_COLUMNS = {
    "node",
    "host",
    "event",
    "type",
    "label",
    "labels",
    "class",
    "target",
}


@dataclass
class PreprocessResult:
    X: np.ndarray
    times: np.ndarray
    feature_names: list[str]
    dropped_columns: list[str]
    imputed_columns: list[str]
    baseline_rows: int
    mean: pd.Series
    std: pd.Series


def select_feature_columns(df: pd.DataFrame, feature_mode: str) -> list[str]:
    if feature_mode not in FEATURE_MODES:
        raise ValueError(f"Unsupported feature mode {feature_mode!r}; expected one of {FEATURE_MODES}")

    columns = [col for col in df.columns if str(col) != "time" and str(col).lower() not in TEXT_OR_ID_COLUMNS]
    if feature_mode == "ControlPlane":
        return [col for col in CONTROL_PLANE_FEATURES if col in df.columns]
    if feature_mode == "DataPlane":
        control = set(CONTROL_PLANE_FEATURES)
        return [col for col in columns if col not in control]
    return columns


def preprocess_node_frame(
    df: pd.DataFrame,
    feature_mode: str,
    sample_skip: int = 39,
) -> PreprocessResult:
    if "time" not in df.columns:
        raise ValueError("Expected a 'time' column before preprocessing.")

    selected_columns = select_feature_columns(df, feature_mode)
    if not selected_columns:
        raise ValueError(f"No usable columns for feature mode {feature_mode}.")

    raw_features = df[selected_columns].copy()
    numeric = raw_features.apply(pd.to_numeric, errors="coerce")
    dropped_columns: list[str] = []
    imputed_columns = [col for col in numeric.columns if numeric[col].isna().any()]

    numeric = numeric.replace([np.inf, -np.inf], np.nan)
    baseline_rows = int(min(max(sample_skip, 1), len(numeric)))
    baseline = numeric.iloc[:baseline_rows].copy()
    medians = baseline.median(numeric_only=True).fillna(numeric.median(numeric_only=True)).fillna(0.0)
    numeric = numeric.fillna(medians).fillna(0.0)

    nunique = numeric.nunique(dropna=False)
    constant_columns = nunique[nunique <= 1].index.tolist()
    if constant_columns:
        numeric = numeric.drop(columns=constant_columns)
        dropped_columns.extend(constant_columns)

    if numeric.shape[1] == 0:
        raise ValueError(f"All selected {feature_mode} columns were constant or nonnumeric.")

    baseline = numeric.iloc[:baseline_rows]
    mean = baseline.mean()
    std = baseline.std(ddof=0).replace(0, np.nan)
    std = std.fillna(numeric.std(ddof=0).replace(0, np.nan)).fillna(1.0)
    normalized = (numeric - mean) / std
    normalized = normalized.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return PreprocessResult(
        X=normalized.to_numpy(dtype=float),
        times=df["time"].to_numpy(dtype=float),
        feature_names=list(normalized.columns),
        dropped_columns=dropped_columns,
        imputed_columns=imputed_columns,
        baseline_rows=baseline_rows,
        mean=mean,
        std=std,
    )
