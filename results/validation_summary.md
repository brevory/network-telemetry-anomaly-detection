# Validation Summary

- Run mode: full
- Dataset count: 5
- Metric row count: 250
- Expected row count: 250
- Required files exist: yes
- Required metric columns exist: yes
- Failure log contains failures: no
- Figure PNG count: 7
- Representative timeline configuration: bgpclear_second | DenStream | ControlPlane | temporal k=4
- Representative timeline alarm count: 8
- Representative timeline selection note: Selected best DenStream configuration with alarms.

## Required Files

| file | exists | non_empty |
| --- | --- | --- |
| results/metrics_summary.csv | True | True |
| results/alarms.csv | True | True |
| results/event_level_results.csv | True | True |
| results/runtime_summary.csv | True | True |
| results/failure_log.csv | True | True |
| results/experiment_log.md | True | True |
| results/presentation_findings.md | True | True |
| results/best_configurations.csv | True | True |
| results/best_configurations.md | True | True |

## Required Metric Columns

| column | exists |
| --- | --- |
| alarm_precision | True |
| event_recall | True |
| alarm_event_f1 | True |
| precision | True |
| recall | True |
| f1 | True |

## Warnings

No validation warnings.
