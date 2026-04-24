# Experiment Log

Generated: 2026-04-24T07:25:14

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
- Kmax: 5
- pruning interval tp: 30

## Run Scope

- Requested datasets: all discovered datasets
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
| bgpclear_second | ControlPlane | DenStream | temporal | 4 | 1 | 0.875 | 0.9333 | 8 | 0 | 0 | 29.57 | 30 | 0.3035 | 8 | 7 | 8 |
| bgpclear_apptraffic_2hourRun | ControlPlane | DenStream | temporal | 3 | 1 | 0.8333 | 0.9091 | 18 | 0 | 0 | 27.3 | 22.5 | 0.574 | 18 | 10 | 12 |
| bgpclear_apptraffic_2hourRun | ControlPlane | DenStream | temporal | 4 | 1 | 0.8333 | 0.9091 | 13 | 0 | 0 | 32.8 | 28 | 0.574 | 13 | 10 | 12 |
| bgpclear_no_traffic_2hourRun | ControlPlane | DenStream | temporal | 3 | 0.8889 | 0.9167 | 0.9026 | 16 | 2 | 0.8904 | 34.82 | 23 | 1.046 | 18 | 11 | 12 |
| bgpclear_no_traffic_2hourRun | ControlPlane | DenStream | temporal | 4 | 1 | 0.75 | 0.8571 | 13 | 0 | 0 | 36.44 | 27 | 1.046 | 13 | 9 | 12 |
| bgpclear_second | ControlPlane | DenStream | spatial | 1 | 0.6909 | 1 | 0.8172 | 76 | 34 | 65.91 | 2.625 | 2.5 | 0.3035 | 110 | 8 | 8 |
| bgpclear_second | CompleteFeatures | DBSCAN | spatial | 5 | 0.8421 | 0.75 | 0.7934 | 48 | 9 | 17.45 | 40.5 | 27 | 0.2391 | 57 | 6 | 8 |
| bgpclear_second | CompleteFeatures | DenStream | spatial | 5 | 0.8 | 0.75 | 0.7742 | 48 | 12 | 23.26 | 40.5 | 27 | 1.136 | 60 | 6 | 8 |
| bgpclear_second | DataPlane | DenStream | spatial | 5 | 0.8 | 0.75 | 0.7742 | 48 | 12 | 23.26 | 40.5 | 27 | 0.9346 | 60 | 6 | 8 |
| bgpclear_second | ControlPlane | DenStream | temporal | 5 | 1 | 0.625 | 0.7692 | 6 | 0 | 0 | 32 | 35 | 0.3035 | 6 | 5 | 8 |

## Runtime Summary

| dataset | feature_mode | method | runtime_seconds |
| --- | --- | --- | --- |
| bgpclear_apptraffic_2hourRun | CompleteFeatures | DBSCAN | 1.944 |
| bgpclear_apptraffic_2hourRun | CompleteFeatures | DenStream | 3.059 |
| bgpclear_apptraffic_2hourRun | CompleteFeatures | MiniBatchKMeans | 8.249 |
| bgpclear_apptraffic_2hourRun | ControlPlane | DenStream | 0.574 |
| bgpclear_apptraffic_2hourRun | DataPlane | DenStream | 2.708 |
| bgpclear_first | CompleteFeatures | DBSCAN | 0.2996 |
| bgpclear_first | CompleteFeatures | DenStream | 1.586 |
| bgpclear_first | CompleteFeatures | MiniBatchKMeans | 6.521 |
| bgpclear_first | ControlPlane | DenStream | 0.5348 |
| bgpclear_first | DataPlane | DenStream | 1.599 |
| bgpclear_no_traffic_2hourRun | CompleteFeatures | DBSCAN | 0.4807 |
| bgpclear_no_traffic_2hourRun | CompleteFeatures | DenStream | 2.84 |
| bgpclear_no_traffic_2hourRun | CompleteFeatures | MiniBatchKMeans | 7.552 |
| bgpclear_no_traffic_2hourRun | ControlPlane | DenStream | 1.046 |
| bgpclear_no_traffic_2hourRun | DataPlane | DenStream | 2.352 |
| bgpclear_second | CompleteFeatures | DBSCAN | 0.2391 |
| bgpclear_second | CompleteFeatures | DenStream | 1.136 |
| bgpclear_second | CompleteFeatures | MiniBatchKMeans | 5.603 |
| bgpclear_second | ControlPlane | DenStream | 0.3035 |
| bgpclear_second | DataPlane | DenStream | 0.9346 |
| portflap_first | CompleteFeatures | DBSCAN | 0.2163 |
| portflap_first | CompleteFeatures | DenStream | 0.7635 |
| portflap_first | CompleteFeatures | MiniBatchKMeans | 5.434 |
| portflap_first | ControlPlane | DenStream | 0.3696 |
| portflap_first | DataPlane | DenStream | 0.8138 |

## Failures and Skips

No dataset or node failures were logged.
