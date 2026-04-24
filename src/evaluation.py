"""Ground-truth evaluation for sample alarms."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _split_nodes(nodes: str | float | None) -> set[str]:
    if nodes is None or (isinstance(nodes, float) and np.isnan(nodes)):
        return set()
    return {part for part in str(nodes).split(";") if part}


def _alarm_matches_event(alarm: pd.Series, event: pd.Series) -> bool:
    if not (float(event["start"]) <= float(alarm["timestamp"]) <= float(event["end"])):
        return False
    alarm_nodes = _split_nodes(alarm.get("nodes"))
    if not alarm_nodes:
        return True
    return str(event["node"]) in alarm_nodes


def evaluate_alarms(
    alarms: pd.DataFrame,
    ground_truth: pd.DataFrame,
    dataset: str,
    runtime_seconds: float,
    total_time_span_seconds: float | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    metric_rows = []
    event_rows = []
    if alarms.empty:
        groups = []
    else:
        groups = list(alarms.groupby(["dataset", "feature_mode", "method", "detection_type", "k"], dropna=False))

    if not groups:
        return pd.DataFrame(), pd.DataFrame()

    for (dataset_name, feature_mode, method, detection_type, k), group in groups:
        if dataset_name != dataset:
            continue
        group = group.sort_values("timestamp").reset_index(drop=True)
        alarm_is_tp = []
        for _, alarm in group.iterrows():
            alarm_is_tp.append(any(_alarm_matches_event(alarm, event) for _, event in ground_truth.iterrows()))
        true_positive_alarms = int(sum(alarm_is_tp))
        false_alarms = int(len(group) - true_positive_alarms)

        detected_events = 0
        delays = []
        for _, event in ground_truth.iterrows():
            matches = group[group.apply(lambda alarm: _alarm_matches_event(alarm, event), axis=1)]
            detected = not matches.empty
            first_alarm = float(matches["timestamp"].min()) if detected else np.nan
            delay = first_alarm - float(event["start"]) if detected else np.nan
            if detected:
                detected_events += 1
                delays.append(delay)
            event_rows.append(
                {
                    "dataset": dataset_name,
                    "feature_mode": feature_mode,
                    "method": method,
                    "detection_type": detection_type,
                    "k": int(k),
                    "event_id": int(event["event_id"]),
                    "node": event["node"],
                    "event": event["event"],
                    "event_start": float(event["start"]),
                    "event_end": float(event["end"]),
                    "detected": bool(detected),
                    "first_alarm_timestamp": first_alarm,
                    "detection_delay_seconds": delay,
                }
            )

        precision = true_positive_alarms / len(group) if len(group) else 0.0
        recall = detected_events / len(ground_truth) if len(ground_truth) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
        hours = total_time_span_seconds / 3600.0 if total_time_span_seconds and total_time_span_seconds > 0 else np.nan
        false_alarm_rate = false_alarms / hours if np.isfinite(hours) and hours > 0 else np.nan
        metric_rows.append(
            {
                "dataset": dataset_name,
                "feature_mode": feature_mode,
                "method": method,
                "detection_type": detection_type,
                "k": int(k),
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "true_positive_alarms": true_positive_alarms,
                "false_positives": false_alarms,
                "false_alarm_rate_per_hour": false_alarm_rate,
                "detection_delay_seconds_mean": float(np.nanmean(delays)) if delays else np.nan,
                "detection_delay_seconds_median": float(np.nanmedian(delays)) if delays else np.nan,
                "runtime_seconds": runtime_seconds,
                "number_of_alarms": int(len(group)),
                "event_level_detection_count": int(detected_events),
                "event_count": int(len(ground_truth)),
            }
        )
    return pd.DataFrame(metric_rows), pd.DataFrame(event_rows)
