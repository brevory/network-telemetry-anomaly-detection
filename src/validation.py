"""Post-run artifact validation for experiment regeneration."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .report_artifacts import TimelineConfig, timeline_config_text


REQUIRED_FILES = [
    "metrics_summary.csv",
    "alarms.csv",
    "event_level_results.csv",
    "runtime_summary.csv",
    "failure_log.csv",
    "experiment_log.md",
    "presentation_findings.md",
    "best_configurations.csv",
    "best_configurations.md",
]

REQUIRED_METRIC_COLUMNS = [
    "alarm_precision",
    "event_recall",
    "alarm_event_f1",
    "precision",
    "recall",
    "f1",
]


def _markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    display = df.copy()
    for column in display.columns:
        display[column] = display[column].map(lambda value: "" if pd.isna(value) else str(value))
    lines = [
        "| " + " | ".join(display.columns) + " |",
        "| " + " | ".join(["---"] * len(display.columns)) + " |",
    ]
    for _, row in display.iterrows():
        lines.append("| " + " | ".join(str(row[column]).replace("|", "\\|") for column in display.columns) + " |")
    return "\n".join(lines)


def run_mode(args) -> str:
    if getattr(args, "full", False):
        return "full"
    if getattr(args, "quick", False):
        return "quick"
    if getattr(args, "datasets", None):
        return "datasets"
    return "default"


def expected_metric_row_count(
    datasets: Iterable[str],
    feature_modes: Iterable[str],
    baseline_methods: Iterable[str],
    baseline_feature_modes: Iterable[str],
    max_k: int,
) -> int:
    selected_feature_modes = list(feature_modes)
    selected_baseline_feature_modes = set(baseline_feature_modes)
    baseline_mode_count = sum(1 for mode in selected_feature_modes if mode in selected_baseline_feature_modes)
    configurations_per_dataset = len(selected_feature_modes) + (len(list(baseline_methods)) * baseline_mode_count)
    return len(list(datasets)) * configurations_per_dataset * 2 * int(max_k)


def validate_run_artifacts(
    results_dir: Path,
    figures_dir: Path,
    args,
    datasets: list[str],
    feature_modes: list[str],
    baseline_methods: list[str],
    baseline_feature_modes: set[str],
    timeline_config: TimelineConfig | None,
) -> list[str]:
    warnings: list[str] = []
    file_rows = []
    for filename in REQUIRED_FILES:
        path = results_dir / filename
        exists = path.exists()
        non_empty = exists and path.stat().st_size > 0
        file_rows.append({"file": f"results/{filename}", "exists": exists, "non_empty": non_empty})
        if not exists:
            warnings.append(f"Missing required output: results/{filename}.")
        elif not non_empty:
            warnings.append(f"Required output is empty: results/{filename}.")

    metrics_path = results_dir / "metrics_summary.csv"
    metrics = pd.DataFrame()
    metric_row_count = 0
    metric_column_rows = []
    if metrics_path.exists() and metrics_path.stat().st_size > 0:
        metrics = pd.read_csv(metrics_path)
        metric_row_count = len(metrics)
        for column in REQUIRED_METRIC_COLUMNS:
            metric_column_rows.append({"column": column, "exists": column in metrics.columns})
            if column not in metrics.columns:
                warnings.append(f"metrics_summary.csv is missing expected column: {column}.")
        if metrics.empty:
            warnings.append("metrics_summary.csv exists but has no metric rows.")
    else:
        for column in REQUIRED_METRIC_COLUMNS:
            metric_column_rows.append({"column": column, "exists": False})

    expected_rows = expected_metric_row_count(
        datasets=datasets,
        feature_modes=feature_modes,
        baseline_methods=baseline_methods,
        baseline_feature_modes=baseline_feature_modes,
        max_k=getattr(args, "alarm_max_k", 5),
    )
    if metric_row_count != expected_rows:
        warnings.append(f"Metric row count is {metric_row_count}; expected {expected_rows}.")

    failure_path = results_dir / "failure_log.csv"
    failure_count = 0
    if failure_path.exists() and failure_path.stat().st_size > 0:
        failures = pd.read_csv(failure_path)
        failure_count = len(failures)
        if failure_count > 0:
            warnings.append(f"failure_log.csv contains {failure_count} failure or skip rows.")

    png_count = len(list(figures_dir.glob("*.png"))) if figures_dir.exists() else 0
    if png_count == 0:
        warnings.append("figures directory contains no PNG files.")

    lines = [
        "# Validation Summary",
        "",
        f"- Run mode: {run_mode(args)}",
        f"- Dataset count: {len(datasets)}",
        f"- Metric row count: {metric_row_count}",
        f"- Expected row count: {expected_rows}",
        f"- Required files exist: {'yes' if all(row['exists'] for row in file_rows) else 'no'}",
        f"- Required metric columns exist: {'yes' if all(row['exists'] for row in metric_column_rows) else 'no'}",
        f"- Failure log contains failures: {'yes' if failure_count else 'no'}",
        f"- Figure PNG count: {png_count}",
        f"- Representative timeline configuration: {timeline_config_text(timeline_config)}",
    ]
    if timeline_config is not None:
        lines.extend(
            [
                f"- Representative timeline alarm count: {timeline_config.alarm_count}",
                f"- Representative timeline selection note: {timeline_config.selection_note}",
            ]
        )

    lines.extend(["", "## Required Files", "", _markdown_table(pd.DataFrame(file_rows))])
    lines.extend(["", "## Required Metric Columns", "", _markdown_table(pd.DataFrame(metric_column_rows))])
    lines.extend(["", "## Warnings", ""])
    lines.extend(warnings if warnings else ["No validation warnings."])
    (results_dir / "validation_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    critical = [
        warning
        for warning in warnings
        if warning.startswith("Missing required output: results/metrics_summary.csv")
        or warning == "metrics_summary.csv exists but has no metric rows."
    ]
    if critical:
        raise RuntimeError("Critical validation failure: " + "; ".join(critical))
    return warnings
