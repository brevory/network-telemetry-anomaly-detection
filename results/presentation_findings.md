# Presentation Findings

This project reproduces and extends the Putina et al. telemetry-based stream-learning pipeline using Cisco Innovation Edge telemetry data, a modern Python 3 DenStream implementation, temporal/spatial alarm logic, event-level evaluation, and baseline comparisons.

## Best-performing Configuration

Best observed row: `DenStream` on `bgpclear_first` with `ControlPlane`, spatial k=2; precision=0.667, recall=0.818, F1=0.735.

## Results Table

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

## Five Important Observations

1. Metrics are computed from generated alarms after inference; ground-truth windows are not used for training.
2. ControlPlane, DataPlane, and CompleteFeatures are evaluated with the same DenStream and alarm settings.
3. Temporal and spatial k sweeps usually trade recall for fewer false alarms as k increases.
4. DBSCAN is useful as a comparison point but is not a streaming detector in this implementation.
5. Runtime is reported per method, feature mode, dataset, and node to expose larger or malformed inputs.

## What Matched the Paper

- The implementation uses the paper reproduction repo's node split, ControlPlane feature list, DenStream defaults, sampleSkip buffer, and temporal/spatial detection criteria.

## What Differed from the Paper

- The original scripts normalize over the loaded node dataframe; this implementation fits normalization only on the initial baseline samples to avoid leakage.
- The DenStream implementation is a Python 3 port with explicit metrics and persisted artifacts rather than Python 2 scripts/notebook-only analysis.

## Likely Reasons for Differences

- Baseline-only normalization, package version changes, and any reduced quick-run dataset choices can shift epsilon, cluster radii, alarms, and final scores.

## My Own Contributions

1. Modernized and ported the pipeline.
2. Cleaned and aligned data.
3. Implemented evaluation.
4. Added baselines and ablations.
5. Generated figures.

## Known Limitations

- DBSCAN is transductive and does not have the same streaming assumption as DenStream.
- Quick runs are meant for smoke testing; use the full command for report-quality coverage.
- Datasets without parseable ground truth are logged and excluded from scored metrics.

## Future Work

- Add more Cisco scenarios such as administrative shutdown and transceiver pull/reinsert when aligned node-level telemetry and ground truth are available.
- Add confidence intervals over repeated parameter sweeps and sensitivity plots for lambda, beta, and epsilon policy.

## Failures Logged

No failures were logged.
