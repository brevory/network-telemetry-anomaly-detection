# Presentation Findings

This project reproduces and extends the Putina et al. telemetry-based stream-learning pipeline using Cisco Innovation Edge telemetry data, a modern Python 3 DenStream implementation, temporal/spatial alarm logic, event-level evaluation, and baseline comparisons.

## Best-performing Configuration

Best observed row: `DenStream` on `bgpclear_second` with `ControlPlane`, temporal alarm k=4; Alarm precision=1.000, Event recall=0.875, Alarm-event F1=0.933.

Metric labels use alarm/event evaluation: alarm precision is computed over generated alarms, event recall is computed over ground-truth events, and alarm-event F1 combines those quantities.

## Results Table

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

## Five Important Observations

1. Metrics are computed from generated alarms after inference; ground-truth windows are not used for training.
2. ControlPlane, DataPlane, and CompleteFeatures are evaluated with the same DenStream and alarm settings.
3. Temporal and spatial k sweeps usually trade event recall for fewer false alarms as k increases.
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
