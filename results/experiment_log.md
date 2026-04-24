# Experiment Log

Generated: 2026-04-24T17:27:05

## Commands

Primary command used by this run:

```bash
python -m src.run_experiments --full
```

## Data Sources

- Dataset repo: `data/external/telemetry` cloned from https://github.com/cisco-ie/telemetry
- Reproduction repo: `data/external/OutlierDenStream-BigDama18` cloned from https://github.com/anrputina/OutlierDenStream-BigDama18
- Generic DenStream reference: `data/external/OutlierDenStream` cloned from https://github.com/anrputina/OutlierDenStream

## Parameters

- sampleSkip: 39
- lambda: 0.15
- beta: 0.05
- epsilon: auto
- mu: auto
- alarm_max_k: 5
- denstream_cluster_cap: none
- pruning interval tp: 30

## Run Scope

This run used --full and included all discovered BigDAMA node datasets, including the two-hour BGP Clear datasets.

- Requested datasets: bgpclear_apptraffic_2hourRun, bgpclear_first, bgpclear_no_traffic_2hourRun, bgpclear_second, portflap_first
- Requested feature modes: ControlPlane, DataPlane, CompleteFeatures
- Two-hour datasets included: yes
- alarm_max_k: 5
- denstream_cluster_cap: none

## Metric Definitions

- Alarm precision: true-positive alarms divided by generated alarms.
- Event recall: detected ground-truth events divided by ground-truth events.
- Alarm-event F1: harmonic mean of alarm precision and event recall.
- False alarms per hour: false-positive alarms divided by evaluated time span.
- Mean detection delay: average first-alarm delay for detected events.

## Feature Modes

- ControlPlane: exact feature list from `OutlierDenStream-BigDama18/configuration.json`.
- DataPlane: all usable numeric telemetry features after dropping those ControlPlane columns.
- CompleteFeatures: all usable numeric telemetry features except time and text/ID columns.

Normalization was fit on the initial baseline buffer only. Ground truth was not used for training or model construction.

## Baseline Notes

- DBSCAN is run as a full-dataset/transductive baseline, so its assumption differs from DenStream streaming inference.
- MiniBatchKMeans is initialized on the initial baseline buffer and updates online on samples not flagged as outliers.

## Best Overall Configuration

| summary_scope | summary_key | dataset | feature_mode | method | detection_type | k | alarm_precision | event_recall | alarm_event_f1 | false_alarm_rate_per_hour | detection_delay_seconds_mean | runtime_seconds | number_of_alarms | event_level_detection_count | event_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Best overall | all | bgpclear_second | ControlPlane | DenStream | temporal | 4 | 1 | 0.875 | 0.9333 | 0 | 29.57 | 0.1775 | 8 | 7 | 8 |

Full generated summary: `results/best_configurations.csv` and `results/best_configurations.md`.

## Representative Timeline

- Configuration: bgpclear_second | DenStream | ControlPlane | temporal k=4
- Metric used: alarm_event_f1
- Metric value: 0.9333
- Alarm count in timeline: 8
- Selection note: Selected best DenStream configuration with alarms.

## Actual Results

| Dataset | Feature mode | Method | Detection type | Alarm k | Alarm precision | Event recall | Alarm-event F1 | False alarms per hour | Mean detection delay | Number of alarms | Detected events | Ground-truth events |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bgpclear_second | ControlPlane | DenStream | temporal | 4 | 1 | 0.875 | 0.9333 | 0 | 29.57 | 8 | 7 | 8 |
| bgpclear_apptraffic_2hourRun | ControlPlane | DenStream | temporal | 3 | 1 | 0.8333 | 0.9091 | 0 | 27.3 | 18 | 10 | 12 |
| bgpclear_apptraffic_2hourRun | ControlPlane | DenStream | temporal | 4 | 1 | 0.8333 | 0.9091 | 0 | 32.8 | 13 | 10 | 12 |
| bgpclear_no_traffic_2hourRun | ControlPlane | DenStream | temporal | 3 | 0.8889 | 0.9167 | 0.9026 | 0.8904 | 34.82 | 18 | 11 | 12 |
| bgpclear_no_traffic_2hourRun | ControlPlane | DenStream | temporal | 4 | 1 | 0.75 | 0.8571 | 0 | 36.44 | 13 | 9 | 12 |
| bgpclear_second | ControlPlane | DenStream | spatial | 1 | 0.6909 | 1 | 0.8172 | 65.91 | 2.625 | 110 | 8 | 8 |
| bgpclear_second | CompleteFeatures | DBSCAN | spatial | 5 | 0.8421 | 0.75 | 0.7934 | 17.45 | 40.5 | 57 | 6 | 8 |
| bgpclear_second | DataPlane | DenStream | spatial | 5 | 0.8 | 0.75 | 0.7742 | 23.26 | 40.5 | 60 | 6 | 8 |
| bgpclear_second | CompleteFeatures | DenStream | spatial | 5 | 0.8 | 0.75 | 0.7742 | 23.26 | 40.5 | 60 | 6 | 8 |
| bgpclear_second | ControlPlane | DenStream | temporal | 5 | 1 | 0.625 | 0.7692 | 0 | 32 | 6 | 5 | 8 |

## Runtime Summary

| dataset | feature_mode | method | runtime_seconds |
| --- | --- | --- | --- |
| bgpclear_apptraffic_2hourRun | CompleteFeatures | DBSCAN | 1.947 |
| bgpclear_apptraffic_2hourRun | CompleteFeatures | DenStream | 2.396 |
| bgpclear_apptraffic_2hourRun | CompleteFeatures | MiniBatchKMeans | 6.943 |
| bgpclear_apptraffic_2hourRun | ControlPlane | DenStream | 0.7765 |
| bgpclear_apptraffic_2hourRun | DataPlane | DenStream | 2.766 |
| bgpclear_first | CompleteFeatures | DBSCAN | 0.2425 |
| bgpclear_first | CompleteFeatures | DenStream | 1.319 |
| bgpclear_first | CompleteFeatures | MiniBatchKMeans | 5.118 |
| bgpclear_first | ControlPlane | DenStream | 0.3007 |
| bgpclear_first | DataPlane | DenStream | 1.312 |
| bgpclear_no_traffic_2hourRun | CompleteFeatures | DBSCAN | 0.4099 |
| bgpclear_no_traffic_2hourRun | CompleteFeatures | DenStream | 2.118 |
| bgpclear_no_traffic_2hourRun | CompleteFeatures | MiniBatchKMeans | 6.438 |
| bgpclear_no_traffic_2hourRun | ControlPlane | DenStream | 0.5965 |
| bgpclear_no_traffic_2hourRun | DataPlane | DenStream | 2.128 |
| bgpclear_second | CompleteFeatures | DBSCAN | 0.2072 |
| bgpclear_second | CompleteFeatures | DenStream | 0.879 |
| bgpclear_second | CompleteFeatures | MiniBatchKMeans | 4.582 |
| bgpclear_second | ControlPlane | DenStream | 0.1775 |
| bgpclear_second | DataPlane | DenStream | 0.8341 |
| portflap_first | CompleteFeatures | DBSCAN | 0.1983 |
| portflap_first | CompleteFeatures | DenStream | 0.5663 |
| portflap_first | CompleteFeatures | MiniBatchKMeans | 4.548 |
| portflap_first | ControlPlane | DenStream | 0.1754 |
| portflap_first | DataPlane | DenStream | 0.5514 |

## Failures and Skips

No dataset or node failures were logged.
