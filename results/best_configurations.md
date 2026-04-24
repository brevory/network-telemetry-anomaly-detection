# Best Configurations

Rows are selected by highest alarm-event F1, then event recall and alarm precision. Metric ties prefer ControlPlane and temporal configurations.

| summary_scope | summary_key | dataset | feature_mode | method | detection_type | k | alarm_precision | event_recall | alarm_event_f1 | false_alarm_rate_per_hour | detection_delay_seconds_mean | runtime_seconds | number_of_alarms | event_level_detection_count | event_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Best overall | all | bgpclear_second | ControlPlane | DenStream | temporal | 4 | 1 | 0.875 | 0.9333 | 0 | 29.57 | 0.1775 | 8 | 7 | 8 |
| Best per method | DBSCAN | bgpclear_second | CompleteFeatures | DBSCAN | spatial | 5 | 0.8421 | 0.75 | 0.7934 | 17.45 | 40.5 | 0.2072 | 57 | 6 | 8 |
| Best per method | DenStream | bgpclear_second | ControlPlane | DenStream | temporal | 4 | 1 | 0.875 | 0.9333 | 0 | 29.57 | 0.1775 | 8 | 7 | 8 |
| Best per method | MiniBatchKMeans | bgpclear_second | CompleteFeatures | MiniBatchKMeans | spatial | 5 | 0.5714 | 0.875 | 0.6914 | 87.24 | 62 | 4.582 | 105 | 7 | 8 |
| Best per dataset | bgpclear_apptraffic_2hourRun | bgpclear_apptraffic_2hourRun | ControlPlane | DenStream | temporal | 3 | 1 | 0.8333 | 0.9091 | 0 | 27.3 | 0.7765 | 18 | 10 | 12 |
| Best per dataset | bgpclear_first | bgpclear_first | ControlPlane | DenStream | spatial | 2 | 0.6667 | 0.8182 | 0.7347 | 19.27 | 11.22 | 0.3007 | 48 | 9 | 11 |
| Best per dataset | bgpclear_no_traffic_2hourRun | bgpclear_no_traffic_2hourRun | ControlPlane | DenStream | temporal | 3 | 0.8889 | 0.9167 | 0.9026 | 0.8904 | 34.82 | 0.5965 | 18 | 11 | 12 |
| Best per dataset | bgpclear_second | bgpclear_second | ControlPlane | DenStream | temporal | 4 | 1 | 0.875 | 0.9333 | 0 | 29.57 | 0.1775 | 8 | 7 | 8 |
| Best per dataset | portflap_first | portflap_first | CompleteFeatures | DBSCAN | spatial | 2 | 0.2536 | 1 | 0.4046 | 392.5 | 23 | 0.1983 | 280 | 4 | 4 |
| Best per dataset + method | bgpclear_apptraffic_2hourRun \| DBSCAN | bgpclear_apptraffic_2hourRun | CompleteFeatures | DBSCAN | spatial | 4 | 0.4107 | 0.8333 | 0.5502 | 29.38 | 46.2 | 1.947 | 112 | 10 | 12 |
| Best per dataset + method | bgpclear_apptraffic_2hourRun \| DenStream | bgpclear_apptraffic_2hourRun | ControlPlane | DenStream | temporal | 3 | 1 | 0.8333 | 0.9091 | 0 | 27.3 | 0.7765 | 18 | 10 | 12 |
| Best per dataset + method | bgpclear_apptraffic_2hourRun \| MiniBatchKMeans | bgpclear_apptraffic_2hourRun | CompleteFeatures | MiniBatchKMeans | spatial | 4 | 0.1809 | 0.9167 | 0.3022 | 358.8 | 18.64 | 6.943 | 984 | 11 | 12 |
| Best per dataset + method | bgpclear_first \| DBSCAN | bgpclear_first | CompleteFeatures | DBSCAN | spatial | 4 | 0.4896 | 1 | 0.6573 | 118 | 20.36 | 0.2425 | 192 | 11 | 11 |
| Best per dataset + method | bgpclear_first \| DenStream | bgpclear_first | ControlPlane | DenStream | spatial | 2 | 0.6667 | 0.8182 | 0.7347 | 19.27 | 11.22 | 0.3007 | 48 | 9 | 11 |
| Best per dataset + method | bgpclear_first \| MiniBatchKMeans | bgpclear_first | CompleteFeatures | MiniBatchKMeans | spatial | 5 | 0.2462 | 0.9091 | 0.3875 | 180.7 | 47 | 5.118 | 199 | 10 | 11 |
| Best per dataset + method | bgpclear_no_traffic_2hourRun \| DBSCAN | bgpclear_no_traffic_2hourRun | CompleteFeatures | DBSCAN | spatial | 4 | 0.3614 | 0.6667 | 0.4688 | 23.6 | 27.62 | 0.4099 | 83 | 8 | 12 |
| Best per dataset + method | bgpclear_no_traffic_2hourRun \| DenStream | bgpclear_no_traffic_2hourRun | ControlPlane | DenStream | temporal | 3 | 0.8889 | 0.9167 | 0.9026 | 0.8904 | 34.82 | 0.5965 | 18 | 11 | 12 |
| Best per dataset + method | bgpclear_no_traffic_2hourRun \| MiniBatchKMeans | bgpclear_no_traffic_2hourRun | CompleteFeatures | MiniBatchKMeans | spatial | 5 | 0.2558 | 0.6667 | 0.3697 | 71.23 | 46.62 | 6.438 | 215 | 8 | 12 |
| Best per dataset + method | bgpclear_second \| DBSCAN | bgpclear_second | CompleteFeatures | DBSCAN | spatial | 5 | 0.8421 | 0.75 | 0.7934 | 17.45 | 40.5 | 0.2072 | 57 | 6 | 8 |
| Best per dataset + method | bgpclear_second \| DenStream | bgpclear_second | ControlPlane | DenStream | temporal | 4 | 1 | 0.875 | 0.9333 | 0 | 29.57 | 0.1775 | 8 | 7 | 8 |
| Best per dataset + method | bgpclear_second \| MiniBatchKMeans | bgpclear_second | CompleteFeatures | MiniBatchKMeans | spatial | 5 | 0.5714 | 0.875 | 0.6914 | 87.24 | 62 | 4.582 | 105 | 7 | 8 |
| Best per dataset + method | portflap_first \| DBSCAN | portflap_first | CompleteFeatures | DBSCAN | spatial | 2 | 0.2536 | 1 | 0.4046 | 392.5 | 23 | 0.1983 | 280 | 4 | 4 |
| Best per dataset + method | portflap_first \| DenStream | portflap_first | CompleteFeatures | DenStream | spatial | 4 | 0.2558 | 0.5 | 0.3385 | 60.09 | 66.5 | 0.5663 | 43 | 2 | 4 |
| Best per dataset + method | portflap_first \| MiniBatchKMeans | portflap_first | CompleteFeatures | MiniBatchKMeans | spatial | 5 | 0.3333 | 0.5 | 0.4 | 30.05 | 154 | 4.548 | 24 | 2 | 4 |
| Best DenStream per feature mode | CompleteFeatures | bgpclear_second | CompleteFeatures | DenStream | spatial | 5 | 0.8 | 0.75 | 0.7742 | 23.26 | 40.5 | 0.879 | 60 | 6 | 8 |
| Best DenStream per feature mode | ControlPlane | bgpclear_second | ControlPlane | DenStream | temporal | 4 | 1 | 0.875 | 0.9333 | 0 | 29.57 | 0.1775 | 8 | 7 | 8 |
| Best DenStream per feature mode | DataPlane | bgpclear_second | DataPlane | DenStream | spatial | 5 | 0.8 | 0.75 | 0.7742 | 23.26 | 40.5 | 0.8341 | 60 | 6 | 8 |
| Best DenStream per detection type | spatial | bgpclear_second | ControlPlane | DenStream | spatial | 1 | 0.6909 | 1 | 0.8172 | 65.91 | 2.625 | 0.1775 | 110 | 8 | 8 |
| Best DenStream per detection type | temporal | bgpclear_second | ControlPlane | DenStream | temporal | 4 | 1 | 0.875 | 0.9333 | 0 | 29.57 | 0.1775 | 8 | 7 | 8 |
