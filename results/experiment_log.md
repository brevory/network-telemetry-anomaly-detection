# Experiment Log

Generated: 2026-04-24T09:05:49

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
| bgpclear_second | CompleteFeatures | DenStream | spatial | 5 | 0.8 | 0.75 | 0.7742 | 23.26 | 40.5 | 60 | 6 | 8 |
| bgpclear_second | DataPlane | DenStream | spatial | 5 | 0.8 | 0.75 | 0.7742 | 23.26 | 40.5 | 60 | 6 | 8 |
| bgpclear_second | ControlPlane | DenStream | temporal | 5 | 1 | 0.625 | 0.7692 | 0 | 32 | 6 | 5 | 8 |

## Runtime Summary

| dataset | feature_mode | method | runtime_seconds |
| --- | --- | --- | --- |
| bgpclear_apptraffic_2hourRun | CompleteFeatures | DBSCAN | 2.007 |
| bgpclear_apptraffic_2hourRun | CompleteFeatures | DenStream | 2.426 |
| bgpclear_apptraffic_2hourRun | CompleteFeatures | MiniBatchKMeans | 9.62 |
| bgpclear_apptraffic_2hourRun | ControlPlane | DenStream | 0.7258 |
| bgpclear_apptraffic_2hourRun | DataPlane | DenStream | 2.427 |
| bgpclear_first | CompleteFeatures | DBSCAN | 0.315 |
| bgpclear_first | CompleteFeatures | DenStream | 3.374 |
| bgpclear_first | CompleteFeatures | MiniBatchKMeans | 7.858 |
| bgpclear_first | ControlPlane | DenStream | 0.8273 |
| bgpclear_first | DataPlane | DenStream | 3.236 |
| bgpclear_no_traffic_2hourRun | CompleteFeatures | DBSCAN | 0.5189 |
| bgpclear_no_traffic_2hourRun | CompleteFeatures | DenStream | 4.078 |
| bgpclear_no_traffic_2hourRun | CompleteFeatures | MiniBatchKMeans | 11.23 |
| bgpclear_no_traffic_2hourRun | ControlPlane | DenStream | 1.644 |
| bgpclear_no_traffic_2hourRun | DataPlane | DenStream | 6.009 |
| bgpclear_second | CompleteFeatures | DBSCAN | 0.31 |
| bgpclear_second | CompleteFeatures | DenStream | 2.765 |
| bgpclear_second | CompleteFeatures | MiniBatchKMeans | 7.403 |
| bgpclear_second | ControlPlane | DenStream | 0.5944 |
| bgpclear_second | DataPlane | DenStream | 2.666 |
| portflap_first | CompleteFeatures | DBSCAN | 0.2661 |
| portflap_first | CompleteFeatures | DenStream | 1.858 |
| portflap_first | CompleteFeatures | MiniBatchKMeans | 6.737 |
| portflap_first | ControlPlane | DenStream | 0.4765 |
| portflap_first | DataPlane | DenStream | 1.614 |

## Failures and Skips

No dataset or node failures were logged.
