"""Generated report-ready summary artifacts and configuration selection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


BEST_CONFIG_COLUMNS = [
    "dataset",
    "feature_mode",
    "method",
    "detection_type",
    "k",
    "alarm_precision",
    "event_recall",
    "alarm_event_f1",
    "false_alarm_rate_per_hour",
    "detection_delay_seconds_mean",
    "runtime_seconds",
    "number_of_alarms",
    "event_level_detection_count",
    "event_count",
]


@dataclass(frozen=True)
class TimelineConfig:
    dataset: str
    method: str
    feature_mode: str
    detection_type: str
    k: int
    metric_column: str
    metric_value: float
    alarm_count: int
    selection_note: str


def metric_column(metrics: pd.DataFrame, explicit_name: str, compatibility_name: str) -> str:
    if explicit_name in metrics.columns:
        return explicit_name
    return compatibility_name


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    display_df = df.copy()
    for col in display_df.columns:
        if pd.api.types.is_float_dtype(display_df[col]):
            display_df[col] = display_df[col].map(lambda value: "" if pd.isna(value) else f"{value:.4g}")
        else:
            display_df[col] = display_df[col].map(lambda value: "" if pd.isna(value) else str(value))
    columns = [str(col) for col in display_df.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in display_df.iterrows():
        values = [str(row[col]).replace("|", "\\|") for col in display_df.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def ensure_metric_columns(metrics: pd.DataFrame) -> pd.DataFrame:
    frame = metrics.copy()
    aliases = {
        "alarm_precision": "precision",
        "event_recall": "recall",
        "alarm_event_f1": "f1",
    }
    for explicit, compatibility in aliases.items():
        if explicit not in frame.columns and compatibility in frame.columns:
            frame[explicit] = frame[compatibility]
        elif explicit not in frame.columns:
            frame[explicit] = np.nan
        if compatibility not in frame.columns and explicit in frame.columns:
            frame[compatibility] = frame[explicit]
    for column in BEST_CONFIG_COLUMNS:
        if column not in frame.columns:
            frame[column] = np.nan
    return frame


def ranked_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    frame = ensure_metric_columns(metrics)
    if frame.empty:
        return frame

    numeric_columns = [
        "alarm_precision",
        "event_recall",
        "alarm_event_f1",
        "false_alarm_rate_per_hour",
        "detection_delay_seconds_mean",
        "runtime_seconds",
        "number_of_alarms",
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame["_feature_preference"] = frame["feature_mode"].map(lambda value: 0 if value == "ControlPlane" else 1)
    frame["_detection_preference"] = frame["detection_type"].map(lambda value: 0 if value == "temporal" else 1)
    return frame.sort_values(
        [
            "alarm_event_f1",
            "event_recall",
            "alarm_precision",
            "_feature_preference",
            "_detection_preference",
            "false_alarm_rate_per_hour",
            "detection_delay_seconds_mean",
            "runtime_seconds",
            "number_of_alarms",
        ],
        ascending=[False, False, False, True, True, True, True, True, False],
        na_position="last",
    ).drop(columns=["_feature_preference", "_detection_preference"])


def metric_display_table(metrics: pd.DataFrame) -> pd.DataFrame:
    if metrics.empty:
        return metrics
    frame = ensure_metric_columns(metrics)
    column_map = {
        "dataset": "Dataset",
        "feature_mode": "Feature mode",
        "method": "Method",
        "detection_type": "Detection type",
        "k": "Alarm k",
        "alarm_precision": "Alarm precision",
        "event_recall": "Event recall",
        "alarm_event_f1": "Alarm-event F1",
        "false_alarm_rate_per_hour": "False alarms per hour",
        "detection_delay_seconds_mean": "Mean detection delay",
        "number_of_alarms": "Number of alarms",
        "event_level_detection_count": "Detected events",
        "event_count": "Ground-truth events",
    }
    available = [column for column in column_map if column in frame.columns]
    return frame[available].rename(columns=column_map)


def build_best_configurations(metrics: pd.DataFrame) -> pd.DataFrame:
    frame = ensure_metric_columns(metrics)
    columns = ["summary_scope", "summary_key", *BEST_CONFIG_COLUMNS]
    if frame.empty:
        return pd.DataFrame(columns=columns)

    rows: list[dict] = []

    def append_best(scope: str, key: str, group: pd.DataFrame) -> None:
        if group.empty:
            return
        best = ranked_metrics(group).iloc[0]
        row = {"summary_scope": scope, "summary_key": key}
        for column in BEST_CONFIG_COLUMNS:
            row[column] = best.get(column, np.nan)
        rows.append(row)

    append_best("Best overall", "all", frame)
    for method, group in frame.groupby("method", dropna=False):
        append_best("Best per method", str(method), group)
    for dataset, group in frame.groupby("dataset", dropna=False):
        append_best("Best per dataset", str(dataset), group)
    for (dataset, method), group in frame.groupby(["dataset", "method"], dropna=False):
        append_best("Best per dataset + method", f"{dataset} | {method}", group)

    denstream = frame[frame["method"] == "DenStream"]
    for feature_mode, group in denstream.groupby("feature_mode", dropna=False):
        append_best("Best DenStream per feature mode", str(feature_mode), group)
    for detection_type, group in denstream.groupby("detection_type", dropna=False):
        append_best("Best DenStream per detection type", str(detection_type), group)

    return pd.DataFrame(rows, columns=columns)


def write_best_configuration_artifacts(metrics: pd.DataFrame, results_dir: Path) -> pd.DataFrame:
    best = build_best_configurations(metrics)
    results_dir.mkdir(parents=True, exist_ok=True)
    best.to_csv(results_dir / "best_configurations.csv", index=False)

    lines = [
        "# Best Configurations",
        "",
        "Rows are selected by highest alarm-event F1, then event recall and alarm precision. Metric ties prefer ControlPlane and temporal configurations.",
        "",
    ]
    if best.empty:
        lines.append("No metrics were generated.")
    else:
        lines.append(markdown_table(best))
    (results_dir / "best_configurations.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return best


def timeline_config_text(config: TimelineConfig | None) -> str:
    if config is None:
        return "none"
    return f"{config.dataset} | {config.method} | {config.feature_mode} | {config.detection_type} k={config.k}"


def alarms_for_config(alarms: pd.DataFrame, config: TimelineConfig) -> pd.DataFrame:
    if alarms.empty:
        return alarms.copy()
    required = ["dataset", "method", "feature_mode", "detection_type", "k"]
    if any(column not in alarms.columns for column in required):
        return pd.DataFrame(columns=alarms.columns)
    return alarms[
        (alarms["dataset"].astype(str) == config.dataset)
        & (alarms["method"].astype(str) == config.method)
        & (alarms["feature_mode"].astype(str) == config.feature_mode)
        & (alarms["detection_type"].astype(str) == config.detection_type)
        & (pd.to_numeric(alarms["k"], errors="coerce") == int(config.k))
    ].copy()


def select_representative_timeline_config(metrics: pd.DataFrame, alarms: pd.DataFrame) -> TimelineConfig | None:
    frame = ensure_metric_columns(metrics)
    if frame.empty:
        return None
    denstream = ranked_metrics(frame[frame["method"] == "DenStream"])
    if denstream.empty:
        return None

    metric_name = "alarm_event_f1" if "alarm_event_f1" in metrics.columns else "f1"
    initial = denstream.iloc[0]

    for _, row in denstream.iterrows():
        config = TimelineConfig(
            dataset=str(row["dataset"]),
            method=str(row["method"]),
            feature_mode=str(row["feature_mode"]),
            detection_type=str(row["detection_type"]),
            k=int(row["k"]),
            metric_column=metric_name,
            metric_value=float(row["alarm_event_f1"]) if pd.notna(row["alarm_event_f1"]) else float("nan"),
            alarm_count=0,
            selection_note="Selected best DenStream configuration with alarms.",
        )
        alarm_count = len(alarms_for_config(alarms, config))
        if alarm_count > 0:
            note = "Selected best DenStream configuration with alarms."
            if not row[["dataset", "feature_mode", "method", "detection_type", "k"]].equals(
                initial[["dataset", "feature_mode", "method", "detection_type", "k"]]
            ):
                initial_label = (
                    f"{initial['dataset']} | {initial['method']} | {initial['feature_mode']} | "
                    f"{initial['detection_type']} k={int(initial['k'])}"
                )
                note = f"Best DenStream row {initial_label} had no alarms, so the next best valid DenStream configuration with alarms was selected."
            return TimelineConfig(
                dataset=config.dataset,
                method=config.method,
                feature_mode=config.feature_mode,
                detection_type=config.detection_type,
                k=config.k,
                metric_column=config.metric_column,
                metric_value=config.metric_value,
                alarm_count=alarm_count,
                selection_note=note,
            )

    return TimelineConfig(
        dataset=str(initial["dataset"]),
        method=str(initial["method"]),
        feature_mode=str(initial["feature_mode"]),
        detection_type=str(initial["detection_type"]),
        k=int(initial["k"]),
        metric_column=metric_name,
        metric_value=float(initial["alarm_event_f1"]) if pd.notna(initial["alarm_event_f1"]) else float("nan"),
        alarm_count=0,
        selection_note="No DenStream configuration produced alarms; the timeline uses the best DenStream row with ground-truth windows only.",
    )
