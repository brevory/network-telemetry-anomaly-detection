# Experiment Log

Generated: 2026-04-24T07:04:27

## Commands

Primary command used by this run:

```bash
python -m src.run_experiments --quick
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
- Kmax: 5
- pruning interval tp: 30

## Run Scope

- Requested datasets: bgpclear_first
- Requested feature modes: ControlPlane,DataPlane,CompleteFeatures
- Use `python -m src.run_experiments --full` to include the larger two-hour BGP Clear datasets.

## Feature Modes

- ControlPlane: exact feature list from `OutlierDenStream-BigDama18/configuration.json`.
- DataPlane: all usable numeric telemetry features after dropping those ControlPlane columns.
- CompleteFeatures: all usable numeric telemetry features except time and text/ID columns.

Normalization was fit on the initial baseline buffer only. Ground truth was not used for training or model construction.

## Baseline Notes

- DBSCAN is run as a full-dataset/transductive baseline, so its assumption differs from DenStream streaming inference.
- MiniBatchKMeans is initialized on the initial baseline buffer and updates online on samples not flagged as outliers.

## Actual Results

| dataset | feature_mode | method | detection_type | k | precision | recall | f1 | true_positive_alarms | false_positives | false_alarm_rate_per_hour | detection_delay_seconds_mean | detection_delay_seconds_median | runtime_seconds | number_of_alarms | event_level_detection_count | event_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bgpclear_first | ControlPlane | DenStream | spatial | 2 | 0.6667 | 0.8182 | 0.7347 | 32 | 16 | 19.27 | 11.22 | 6 | 0.3001 | 48 | 9 | 11 |
| bgpclear_first | ControlPlane | DenStream | spatial | 1 | 0.5183 | 1 | 0.6827 | 85 | 79 | 95.15 | 2.182 | 1 | 0.3001 | 164 | 11 | 11 |
| bgpclear_first | ControlPlane | DenStream | spatial | 3 | 0.7143 | 0.6364 | 0.6731 | 10 | 4 | 4.818 | 24.14 | 22 | 0.3001 | 14 | 7 | 11 |
| bgpclear_first | CompleteFeatures | DBSCAN | spatial | 4 | 0.4896 | 1 | 0.6573 | 94 | 98 | 118 | 20.36 | 14 | 0.4294 | 192 | 11 | 11 |
| bgpclear_first | ControlPlane | DenStream | temporal | 3 | 0.4828 | 1 | 0.6512 | 14 | 15 | 18.07 | 39.73 | 44 | 0.3001 | 29 | 11 | 11 |
| bgpclear_first | CompleteFeatures | DBSCAN | spatial | 5 | 0.5741 | 0.7273 | 0.6417 | 31 | 23 | 27.7 | 27.62 | 26.5 | 0.4294 | 54 | 8 | 11 |
| bgpclear_first | ControlPlane | DenStream | temporal | 4 | 0.5263 | 0.8182 | 0.6406 | 10 | 9 | 10.84 | 43 | 48 | 0.3001 | 19 | 9 | 11 |
| bgpclear_first | ControlPlane | DenStream | temporal | 2 | 0.4217 | 1 | 0.5932 | 35 | 48 | 57.81 | 6 | 5 | 0.3001 | 83 | 11 | 11 |
| bgpclear_first | DataPlane | DenStream | spatial | 5 | 0.44 | 0.9091 | 0.593 | 33 | 42 | 50.59 | 53.2 | 39 | 1.032 | 75 | 10 | 11 |
| bgpclear_first | CompleteFeatures | DenStream | spatial | 5 | 0.4533 | 0.8182 | 0.5834 | 34 | 41 | 49.38 | 45.67 | 35 | 1.212 | 75 | 9 | 11 |

## Runtime Summary

| dataset | feature_mode | method | runtime_seconds |
| --- | --- | --- | --- |
| bgpclear_first | CompleteFeatures | DBSCAN | 0.4294 |
| bgpclear_first | CompleteFeatures | DenStream | 1.212 |
| bgpclear_first | CompleteFeatures | MiniBatchKMeans | 5.937 |
| bgpclear_first | ControlPlane | DenStream | 0.3001 |
| bgpclear_first | DataPlane | DenStream | 1.032 |

## Failures and Skips

No dataset or node failures were logged.
