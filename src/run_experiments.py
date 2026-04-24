"""Command-line experiment runner for the ITCS 5154 project."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys
import time
from typing import Iterable

import numpy as np
import pandas as pd

from .alarm_logic import build_alarms
from .baselines import dbscan_predictions, minibatch_kmeans_predictions
from .data_loader import (
    DEFAULT_NODES,
    PROJECT_ROOT,
    available_datasets,
    dataset_files,
    ensure_output_dirs,
    ground_truth_path,
    load_node_csv,
    read_ground_truth,
    write_inventories,
)
from .denstream import run_denstream
from .plotting import write_all_figures
from .preprocessing import FEATURE_MODES, preprocess_node_frame


RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def _parse_list(value: str | None, default: Iterable[str]) -> list[str]:
    if value is None or value.strip() == "":
        return list(default)
    return [part.strip() for part in value.split(",") if part.strip()]


def _parse_auto_or_float(value: str | float) -> str | float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text.lower() == "auto":
        return "auto"
    return float(text)


def _markdown_table(df: pd.DataFrame) -> str:
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


def _metric_column(metrics: pd.DataFrame, explicit_name: str, compatibility_name: str) -> str:
    if explicit_name in metrics.columns:
        return explicit_name
    return compatibility_name


def _ranked_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    if metrics.empty:
        return metrics
    f1_col = _metric_column(metrics, "alarm_event_f1", "f1")
    recall_col = _metric_column(metrics, "event_recall", "recall")
    precision_col = _metric_column(metrics, "alarm_precision", "precision")
    return metrics.sort_values([f1_col, recall_col, precision_col], ascending=False)


def _metric_display_table(metrics: pd.DataFrame) -> pd.DataFrame:
    if metrics.empty:
        return metrics
    column_map = {
        "dataset": "Dataset",
        "feature_mode": "Feature mode",
        "method": "Method",
        "detection_type": "Detection type",
        "k": "Alarm k",
        _metric_column(metrics, "alarm_precision", "precision"): "Alarm precision",
        _metric_column(metrics, "event_recall", "recall"): "Event recall",
        _metric_column(metrics, "alarm_event_f1", "f1"): "Alarm-event F1",
        "false_alarm_rate_per_hour": "False alarms per hour",
        "detection_delay_seconds_mean": "Mean detection delay",
        "number_of_alarms": "Number of alarms",
        "event_level_detection_count": "Detected events",
        "event_count": "Ground-truth events",
    }
    available = [column for column in column_map if column in metrics.columns]
    return metrics[available].rename(columns=column_map)


def _format_cluster_cap(cluster_cap: int | None) -> str:
    if cluster_cap is None or cluster_cap <= 0:
        return "none"
    return str(cluster_cap)


def _includes_two_hour_dataset(datasets: Iterable[str]) -> bool:
    return any("2hour" in dataset.lower() or "two-hour" in dataset.lower() for dataset in datasets)


def _run_scope_text(args: argparse.Namespace, datasets: list[str]) -> str:
    if args.datasets:
        return "This run used an explicit dataset list: " + ", ".join(datasets) + "."
    if args.quick:
        return "This run used --quick and evaluated the quick smoke-test subset only."
    if args.full:
        return (
            "This run used --full and included all discovered BigDAMA node datasets, "
            "including the two-hour BGP Clear datasets."
        )
    return "This run used the default dataset selection and evaluated all discovered BigDAMA node datasets."


def _prediction_frame(
    records: list[dict],
    dataset: str,
    feature_mode: str,
    method: str,
    node: str,
    extra: dict | None = None,
) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    frame["dataset"] = dataset
    frame["feature_mode"] = feature_mode
    frame["method"] = method
    frame["node"] = node
    if extra:
        for key, value in extra.items():
            frame[key] = value
    return frame


def _baseline_frame(
    outliers: np.ndarray,
    scores: np.ndarray,
    times: np.ndarray,
    dataset: str,
    feature_mode: str,
    method: str,
    node: str,
    sample_skip: int,
) -> pd.DataFrame:
    outliers = outliers.astype(bool).copy()
    outliers[: min(sample_skip, len(outliers))] = False
    return pd.DataFrame(
        {
            "timestamp": times.astype(float),
            "sample_index": np.arange(len(times)),
            "outlier": outliers,
            "score": scores.astype(float),
            "nearest_core_distance": np.nan,
            "nearest_outlier_distance": np.nan,
            "p_micro_clusters": np.nan,
            "o_micro_clusters": np.nan,
            "dataset": dataset,
            "feature_mode": feature_mode,
            "method": method,
            "node": node,
        }
    )


def _empty_metric_rows(
    dataset: str,
    feature_mode: str,
    method: str,
    truth: pd.DataFrame,
    runtime_seconds: float,
    total_time_span_seconds: float,
    alarm_max_k: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    event_rows = []
    hours = total_time_span_seconds / 3600.0 if total_time_span_seconds > 0 else np.nan
    false_alarm_rate = 0.0 if np.isfinite(hours) and hours > 0 else np.nan
    for detection_type in ["temporal", "spatial"]:
        for k in range(1, alarm_max_k + 1):
            rows.append(
                {
                    "dataset": dataset,
                    "feature_mode": feature_mode,
                    "method": method,
                    "detection_type": detection_type,
                    "k": k,
                    "alarm_precision": 0.0,
                    "event_recall": 0.0,
                    "alarm_event_f1": 0.0,
                    # Compatibility aliases retained for existing plotting/notebook/report code.
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1": 0.0,
                    "true_positive_alarms": 0,
                    "false_positives": 0,
                    "false_alarm_rate_per_hour": false_alarm_rate,
                    "detection_delay_seconds_mean": np.nan,
                    "detection_delay_seconds_median": np.nan,
                    "runtime_seconds": runtime_seconds,
                    "number_of_alarms": 0,
                    "event_level_detection_count": 0,
                    "event_count": int(len(truth)),
                }
            )
            for _, event in truth.iterrows():
                event_rows.append(
                    {
                        "dataset": dataset,
                        "feature_mode": feature_mode,
                        "method": method,
                        "detection_type": detection_type,
                        "k": k,
                        "event_id": int(event["event_id"]),
                        "node": event["node"],
                        "event": event["event"],
                        "event_start": float(event["start"]),
                        "event_end": float(event["end"]),
                        "detected": False,
                        "first_alarm_timestamp": np.nan,
                        "detection_delay_seconds": np.nan,
                    }
                )
    return pd.DataFrame(rows), pd.DataFrame(event_rows)


def _complete_metric_grid(
    actual_metrics: pd.DataFrame,
    actual_events: pd.DataFrame,
    dataset: str,
    feature_mode: str,
    method: str,
    truth: pd.DataFrame,
    runtime_seconds: float,
    total_time_span_seconds: float,
    alarm_max_k: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    empty_metrics, empty_events = _empty_metric_rows(
        dataset, feature_mode, method, truth, runtime_seconds, total_time_span_seconds, alarm_max_k
    )
    if actual_metrics.empty:
        return empty_metrics, empty_events

    keys = ["dataset", "feature_mode", "method", "detection_type", "k"]
    actual_key_tuples = set(map(tuple, actual_metrics[keys].to_numpy()))
    filler_metrics = empty_metrics[
        ~empty_metrics[keys].apply(lambda row: tuple(row.to_numpy()) in actual_key_tuples, axis=1)
    ]
    if actual_events.empty:
        event_frame = empty_events
    else:
        event_key_tuples = set(map(tuple, actual_events[keys].to_numpy()))
        filler_events = empty_events[
            ~empty_events[keys].apply(lambda row: tuple(row.to_numpy()) in event_key_tuples, axis=1)
        ]
        event_frame = pd.concat([actual_events, filler_events], ignore_index=True)
    metric_frame = pd.concat([actual_metrics, filler_metrics], ignore_index=True)
    return metric_frame, event_frame


def _evaluate_predictions(
    predictions: pd.DataFrame,
    truth: pd.DataFrame,
    dataset: str,
    feature_mode: str,
    method: str,
    runtime_seconds: float,
    alarm_max_k: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    from .evaluation import evaluate_alarms

    alarms = build_alarms(predictions, max_k=alarm_max_k)
    if predictions.empty:
        span = 0.0
    else:
        span = float(predictions["timestamp"].max() - predictions["timestamp"].min())
    actual_metrics, actual_events = evaluate_alarms(alarms, truth, dataset, runtime_seconds, span)
    metrics, events = _complete_metric_grid(
        actual_metrics, actual_events, dataset, feature_mode, method, truth, runtime_seconds, span, alarm_max_k
    )
    return alarms, metrics, events


def run(args: argparse.Namespace) -> int:
    ensure_output_dirs()
    write_inventories(RESULTS_DIR)

    discovered = available_datasets()
    if not discovered:
        raise SystemExit(
            "No BigDAMA node CSV files found. Expected data/external/OutlierDenStream-BigDama18/Data/DatasetByNodes."
        )

    if args.inventory_only:
        print("Wrote data and ground-truth inventories.")
        return 0

    default_datasets = ["bgpclear_first"] if args.quick else list(discovered.keys())
    datasets = _parse_list(args.datasets, default_datasets)
    feature_modes = _parse_list(args.feature_modes, FEATURE_MODES)
    nodes = _parse_list(args.nodes, DEFAULT_NODES)
    baseline_methods = [] if args.no_baselines else ["DBSCAN", "MiniBatchKMeans"]
    if args.quick:
        baseline_feature_modes = {"CompleteFeatures"}
    else:
        baseline_feature_modes = set(_parse_list(args.baseline_feature_modes, ["CompleteFeatures"]))

    all_predictions: list[pd.DataFrame] = []
    all_alarms: list[pd.DataFrame] = []
    all_metrics: list[pd.DataFrame] = []
    all_events: list[pd.DataFrame] = []
    runtime_rows: list[dict] = []
    failures: list[dict] = []
    representative_truth = pd.DataFrame()

    for dataset in datasets:
        truth_file = ground_truth_path(dataset)
        if truth_file is None:
            failures.append(
                {
                    "dataset": dataset,
                    "feature_mode": "",
                    "method": "",
                    "node": "",
                    "stage": "ground_truth",
                    "message": "Missing ground-truth file.",
                }
            )
            continue
        truth = read_ground_truth(truth_file)
        if representative_truth.empty:
            representative_truth = truth.copy()
        files = dataset_files(dataset, nodes)
        if not files:
            failures.append(
                {
                    "dataset": dataset,
                    "feature_mode": "",
                    "method": "",
                    "node": "",
                    "stage": "data_loading",
                    "message": "No node CSV files matched requested nodes.",
                }
            )
            continue

        for feature_mode in feature_modes:
            denstream_predictions: list[pd.DataFrame] = []
            denstream_runtime = 0.0
            for record in files:
                try:
                    df = load_node_csv(record.path, max_rows=args.max_rows)
                    prep = preprocess_node_frame(df, feature_mode=feature_mode, sample_skip=args.sample_skip)
                    start = time.perf_counter()
                    records, metadata = run_denstream(
                        prep.X,
                        prep.times,
                        sample_skip=args.sample_skip,
                        lamb=args.lamb,
                        beta=args.beta,
                        epsilon=args.epsilon,
                        mu=args.mu,
                        cluster_cap=args.denstream_cluster_cap,
                        tp=args.tp,
                    )
                    elapsed = time.perf_counter() - start
                    denstream_runtime += elapsed
                    denstream_predictions.append(
                        _prediction_frame(
                            records,
                            dataset,
                            feature_mode,
                            "DenStream",
                            record.node,
                            {
                                "feature_count": len(prep.feature_names),
                                "epsilon_used": metadata["epsilon"],
                                "mu_used": metadata["mu"],
                                "denstream_cluster_cap": metadata["cluster_cap"],
                            },
                        )
                    )
                    runtime_rows.append(
                        {
                            "dataset": dataset,
                            "feature_mode": feature_mode,
                            "method": "DenStream",
                            "node": record.node,
                            "runtime_seconds": elapsed,
                            "sample_count": len(prep.times),
                            "feature_count": len(prep.feature_names),
                            "status": "ok",
                        }
                    )
                except Exception as exc:  # noqa: BLE001 - failures must be logged and sweep continues.
                    failures.append(
                        {
                            "dataset": dataset,
                            "feature_mode": feature_mode,
                            "method": "DenStream",
                            "node": record.node,
                            "stage": "denstream",
                            "message": repr(exc),
                        }
                    )

            if denstream_predictions:
                predictions = pd.concat(denstream_predictions, ignore_index=True)
                all_predictions.append(predictions)
                alarms, metrics, events = _evaluate_predictions(
                    predictions, truth, dataset, feature_mode, "DenStream", denstream_runtime, args.alarm_max_k
                )
                all_alarms.append(alarms)
                all_metrics.append(metrics)
                all_events.append(events)

            if feature_mode in baseline_feature_modes and baseline_methods:
                for baseline_method in baseline_methods:
                    baseline_predictions: list[pd.DataFrame] = []
                    baseline_runtime = 0.0
                    for record in files:
                        try:
                            df = load_node_csv(record.path, max_rows=args.max_rows)
                            prep = preprocess_node_frame(df, feature_mode=feature_mode, sample_skip=args.sample_skip)
                            start = time.perf_counter()
                            if baseline_method == "DBSCAN":
                                outliers, scores, params = dbscan_predictions(prep.X, sample_skip=args.sample_skip)
                            elif baseline_method == "MiniBatchKMeans":
                                outliers, scores, params = minibatch_kmeans_predictions(
                                    prep.X, sample_skip=args.sample_skip
                                )
                            else:
                                raise ValueError(f"Unknown baseline method {baseline_method}")
                            elapsed = time.perf_counter() - start
                            baseline_runtime += elapsed
                            frame = _baseline_frame(
                                outliers,
                                scores,
                                prep.times,
                                dataset,
                                feature_mode,
                                baseline_method,
                                record.node,
                                args.sample_skip,
                            )
                            for key, value in params.items():
                                frame[key] = value
                            baseline_predictions.append(frame)
                            runtime_rows.append(
                                {
                                    "dataset": dataset,
                                    "feature_mode": feature_mode,
                                    "method": baseline_method,
                                    "node": record.node,
                                    "runtime_seconds": elapsed,
                                    "sample_count": len(prep.times),
                                    "feature_count": len(prep.feature_names),
                                    "status": "ok",
                                }
                            )
                        except Exception as exc:  # noqa: BLE001
                            failures.append(
                                {
                                    "dataset": dataset,
                                    "feature_mode": feature_mode,
                                    "method": baseline_method,
                                    "node": record.node,
                                    "stage": "baseline",
                                    "message": repr(exc),
                                }
                            )
                    if baseline_predictions:
                        predictions = pd.concat(baseline_predictions, ignore_index=True)
                        all_predictions.append(predictions)
                        alarms, metrics, events = _evaluate_predictions(
                            predictions, truth, dataset, feature_mode, baseline_method, baseline_runtime, args.alarm_max_k
                        )
                        all_alarms.append(alarms)
                        all_metrics.append(metrics)
                        all_events.append(events)

    predictions_df = pd.concat(all_predictions, ignore_index=True) if all_predictions else pd.DataFrame()
    alarms_df = pd.concat(all_alarms, ignore_index=True) if all_alarms else pd.DataFrame()
    metrics_df = pd.concat(all_metrics, ignore_index=True) if all_metrics else pd.DataFrame()
    events_df = pd.concat(all_events, ignore_index=True) if all_events else pd.DataFrame()
    runtime_df = pd.DataFrame(runtime_rows)
    failures_df = pd.DataFrame(
        failures,
        columns=["dataset", "feature_mode", "method", "node", "stage", "message"],
    )

    if not alarms_df.empty:
        alarms_df = alarms_df.sort_values(["dataset", "feature_mode", "method", "detection_type", "k", "timestamp"])
    if not metrics_df.empty:
        metrics_df = metrics_df.sort_values(["dataset", "feature_mode", "method", "detection_type", "k"])
    if not events_df.empty:
        events_df = events_df.sort_values(["dataset", "feature_mode", "method", "detection_type", "k", "event_id"])

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    predictions_df.to_csv(PROCESSED_DIR / "sample_predictions.csv", index=False)
    alarms_df.to_csv(RESULTS_DIR / "alarms.csv", index=False)
    metrics_df.to_csv(RESULTS_DIR / "metrics_summary.csv", index=False)
    events_df.to_csv(RESULTS_DIR / "event_level_results.csv", index=False)
    runtime_df.to_csv(RESULTS_DIR / "runtime_summary.csv", index=False)
    failures_df.to_csv(RESULTS_DIR / "failure_log.csv", index=False)

    write_experiment_log(args, metrics_df, runtime_df, failures_df, datasets, feature_modes)
    write_presentation_findings(metrics_df, failures_df)
    write_all_figures(FIGURES_DIR, metrics_df, alarms_df, runtime_df, representative_truth)

    print(f"Wrote {RESULTS_DIR / 'metrics_summary.csv'}")
    print(f"Wrote {RESULTS_DIR / 'alarms.csv'}")
    print(f"Wrote {FIGURES_DIR / 'timeline_ground_truth_vs_alarms.png'}")
    if not failures_df.empty:
        print(f"Logged {len(failures_df)} failures in {RESULTS_DIR / 'failure_log.csv'}")
    return 0


def write_experiment_log(
    args: argparse.Namespace,
    metrics: pd.DataFrame,
    runtime: pd.DataFrame,
    failures: pd.DataFrame,
    datasets: list[str],
    feature_modes: list[str],
) -> None:
    two_hour_included = _includes_two_hour_dataset(datasets)
    lines = [
        "# Experiment Log",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Commands",
        "",
        "Primary command used by this run:",
        "",
        "```bash",
        "python -m src.run_experiments " + " ".join(args.original_argv),
        "```",
        "",
        "## Data Sources",
        "",
        "- Dataset repo: `data/external/telemetry` cloned from https://github.com/cisco-ie/telemetry",
        "- Reproduction repo: `data/external/OutlierDenStream-BigDama18` cloned from https://github.com/anrputina/OutlierDenStream-BigDama18",
        "- Generic DenStream reference: `data/external/OutlierDenStream` cloned from https://github.com/anrputina/OutlierDenStream",
        "",
        "## Parameters",
        "",
        f"- sampleSkip: {args.sample_skip}",
        f"- lambda: {args.lamb}",
        f"- beta: {args.beta}",
        f"- epsilon: {args.epsilon}",
        f"- mu: {args.mu}",
        f"- alarm_max_k: {args.alarm_max_k}",
        f"- denstream_cluster_cap: {_format_cluster_cap(args.denstream_cluster_cap)}",
        f"- pruning interval tp: {args.tp}",
        "",
        "## Run Scope",
        "",
        _run_scope_text(args, datasets),
        "",
        f"- Requested datasets: {', '.join(datasets)}",
        f"- Requested feature modes: {', '.join(feature_modes)}",
        f"- Two-hour datasets included: {'yes' if two_hour_included else 'no'}",
        f"- alarm_max_k: {args.alarm_max_k}",
        f"- denstream_cluster_cap: {_format_cluster_cap(args.denstream_cluster_cap)}",
        "",
        "## Metric Definitions",
        "",
        "- Alarm precision: true-positive alarms divided by generated alarms.",
        "- Event recall: detected ground-truth events divided by ground-truth events.",
        "- Alarm-event F1: harmonic mean of alarm precision and event recall.",
        "- False alarms per hour: false-positive alarms divided by evaluated time span.",
        "- Mean detection delay: average first-alarm delay for detected events.",
        "",
        "## Feature Modes",
        "",
        "- ControlPlane: exact feature list from `OutlierDenStream-BigDama18/configuration.json`.",
        "- DataPlane: all usable numeric telemetry features after dropping those ControlPlane columns.",
        "- CompleteFeatures: all usable numeric telemetry features except time and text/ID columns.",
        "",
        "Normalization was fit on the initial baseline buffer only. Ground truth was not used for training or model construction.",
        "",
        "## Baseline Notes",
        "",
        "- DBSCAN is run as a full-dataset/transductive baseline, so its assumption differs from DenStream streaming inference.",
        "- MiniBatchKMeans is initialized on the initial baseline buffer and updates online on samples not flagged as outliers.",
        "",
        "## Actual Results",
        "",
    ]
    if metrics.empty:
        lines.append("No metrics were generated.")
    else:
        best = _ranked_metrics(metrics).head(10)
        lines.append(_markdown_table(_metric_display_table(best)))
    lines.extend(["", "## Runtime Summary", ""])
    if runtime.empty:
        lines.append("No runtime records were generated.")
    else:
        summary = runtime.groupby(["dataset", "feature_mode", "method"], as_index=False)["runtime_seconds"].sum()
        lines.append(_markdown_table(summary))
    lines.extend(["", "## Failures and Skips", ""])
    if failures.empty:
        lines.append("No dataset or node failures were logged.")
    else:
        lines.append(_markdown_table(failures))
    (RESULTS_DIR / "experiment_log.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_presentation_findings(metrics: pd.DataFrame, failures: pd.DataFrame) -> None:
    lines = [
        "# Presentation Findings",
        "",
        "This project reproduces and extends the Putina et al. telemetry-based stream-learning pipeline using Cisco Innovation Edge telemetry data, a modern Python 3 DenStream implementation, temporal/spatial alarm logic, event-level evaluation, and baseline comparisons.",
        "",
        "## Best-performing Configuration",
        "",
    ]
    if metrics.empty:
        lines.append("No metrics were generated, so no best configuration can be reported.")
        best_table = pd.DataFrame()
    else:
        best_table = _ranked_metrics(metrics).head(10)
        best = best_table.iloc[0]
        lines.append(
            f"Best observed row: `{best['method']}` on `{best['dataset']}` with `{best['feature_mode']}`, "
            f"{best['detection_type']} alarm k={int(best['k'])}; "
            f"Alarm precision={best[_metric_column(metrics, 'alarm_precision', 'precision')]:.3f}, "
            f"Event recall={best[_metric_column(metrics, 'event_recall', 'recall')]:.3f}, "
            f"Alarm-event F1={best[_metric_column(metrics, 'alarm_event_f1', 'f1')]:.3f}."
        )
        lines.extend(
            [
                "",
                "Metric labels use alarm/event evaluation: alarm precision is computed over generated alarms, "
                "event recall is computed over ground-truth events, and alarm-event F1 combines those quantities.",
            ]
        )
    lines.extend(["", "## Results Table", ""])
    lines.append(_markdown_table(_metric_display_table(best_table)) if not best_table.empty else "No results table available.")
    lines.extend(
        [
            "",
            "## Five Important Observations",
            "",
            "1. Metrics are computed from generated alarms after inference; ground-truth windows are not used for training.",
            "2. ControlPlane, DataPlane, and CompleteFeatures are evaluated with the same DenStream and alarm settings.",
            "3. Temporal and spatial k sweeps usually trade event recall for fewer false alarms as k increases.",
            "4. DBSCAN is useful as a comparison point but is not a streaming detector in this implementation.",
            "5. Runtime is reported per method, feature mode, dataset, and node to expose larger or malformed inputs.",
            "",
            "## What Matched the Paper",
            "",
            "- The implementation uses the paper reproduction repo's node split, ControlPlane feature list, DenStream defaults, sampleSkip buffer, and temporal/spatial detection criteria.",
            "",
            "## What Differed from the Paper",
            "",
            "- The original scripts normalize over the loaded node dataframe; this implementation fits normalization only on the initial baseline samples to avoid leakage.",
            "- The DenStream implementation is a Python 3 port with explicit metrics and persisted artifacts rather than Python 2 scripts/notebook-only analysis.",
            "",
            "## Likely Reasons for Differences",
            "",
            "- Baseline-only normalization, package version changes, and any reduced quick-run dataset choices can shift epsilon, cluster radii, alarms, and final scores.",
            "",
            "## My Own Contributions",
            "",
            "1. Modernized and ported the pipeline.",
            "2. Cleaned and aligned data.",
            "3. Implemented evaluation.",
            "4. Added baselines and ablations.",
            "5. Generated figures.",
            "",
            "## Known Limitations",
            "",
            "- DBSCAN is transductive and does not have the same streaming assumption as DenStream.",
            "- Quick runs are meant for smoke testing; use the full command for report-quality coverage.",
            "- Datasets without parseable ground truth are logged and excluded from scored metrics.",
            "",
            "## Future Work",
            "",
            "- Add more Cisco scenarios such as administrative shutdown and transceiver pull/reinsert when aligned node-level telemetry and ground truth are available.",
            "- Add confidence intervals over repeated parameter sweeps and sensitivity plots for lambda, beta, and epsilon policy.",
        ]
    )
    lines.extend(["", "## Failures Logged", ""])
    lines.append("No failures were logged." if failures.empty else _markdown_table(failures))
    (RESULTS_DIR / "presentation_findings.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run streaming telemetry anomaly detection experiments.")
    parser.add_argument("--quick", action="store_true", help="Run a smoke sweep on bgpclear_first.")
    parser.add_argument("--full", action="store_true", help="Run all discovered BigDAMA datasets unless --datasets is set.")
    parser.add_argument("--inventory-only", action="store_true", help="Only write data inventories.")
    parser.add_argument("--datasets", type=str, default=None, help="Comma-separated dataset names.")
    parser.add_argument("--feature-modes", type=str, default=None, help="Comma-separated feature modes.")
    parser.add_argument("--nodes", type=str, default=None, help="Comma-separated node names.")
    parser.add_argument("--baseline-feature-modes", type=str, default=None, help="Comma-separated modes for baselines.")
    parser.add_argument("--no-baselines", action="store_true", help="Skip DBSCAN and MiniBatchKMeans baselines.")
    parser.add_argument("--max-rows", type=int, default=None, help="Optional row cap per node CSV for debugging.")
    parser.add_argument("--sample-skip", type=int, default=39)
    parser.add_argument("--lambda", dest="lamb", type=float, default=0.15)
    parser.add_argument("--beta", type=float, default=0.05)
    parser.add_argument("--epsilon", default="auto")
    parser.add_argument("--mu", default="auto")
    parser.add_argument(
        "--max-k",
        "--kmax",
        dest="alarm_max_k",
        type=int,
        default=5,
        help="Maximum alarm aggregation/detection k to sweep.",
    )
    parser.add_argument(
        "--denstream-cluster-cap",
        type=int,
        default=None,
        help="Optional cap for DenStream potential and outlier micro-clusters; default is no cap.",
    )
    parser.add_argument("--tp", type=int, default=30)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.original_argv = argv if argv is not None else sys.argv[1:]
    args.epsilon = _parse_auto_or_float(args.epsilon)
    args.mu = _parse_auto_or_float(args.mu)
    if args.full:
        args.quick = False
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
