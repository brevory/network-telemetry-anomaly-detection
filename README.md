# Network Telemetry Anomaly Detection

Reproducible ITCS 5154 implementation for Putina et al. (2018), "Telemetry-based stream-learning of BGP anomalies." The project modernizes the original Python 2 reproduction scripts into a Python 3 command-line pipeline with DenStream, temporal/spatial alarms, event-level metrics, baselines, and saved figures.

## Setup

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Optional activation command:

```powershell
.\.venv\Scripts\Activate.ps1
```

Notebook/Jupyter dependencies are optional and live in `requirements-dev.txt`. Use a short repo path such as `C:\Users\<user>\Github\...` on Windows to avoid long-path package installation issues.

## Data Acquisition

The experiment runner expects the upstream repositories under `data/external`.

```bash
git clone --depth 1 https://github.com/cisco-ie/telemetry data/external/telemetry
git clone --depth 1 https://github.com/anrputina/OutlierDenStream-BigDama18 data/external/OutlierDenStream-BigDama18
git clone --depth 1 https://github.com/anrputina/OutlierDenStream data/external/OutlierDenStream
```

The cloned reproduction repo contains node-level CSVs in `data/external/OutlierDenStream-BigDama18/Data/DatasetByNodes` and ground-truth windows in `data/external/OutlierDenStream-BigDama18/GrounTruth`.

## Commands

Write only the source-data inventories:

```powershell
.\.venv\Scripts\python.exe -m src.run_experiments --inventory-only
```

Smoke test used for quick verification:

```powershell
.\.venv\Scripts\python.exe -m src.run_experiments --quick
```

Full sweep over all discovered BigDAMA node datasets:

```powershell
.\.venv\Scripts\python.exe -m src.run_experiments --full
```

Targeted example:

```powershell
.\.venv\Scripts\python.exe -m src.run_experiments --datasets bgpclear_first,portflap_first --feature-modes ControlPlane,DataPlane,CompleteFeatures
```

K in the k sweep controls alarm aggregation/detection order, not the DenStream micro-cluster count. Use `--max-k` for the alarm sweep. DenStream micro-clusters are uncapped by default; use `--denstream-cluster-cap N` only when explicitly testing a cluster-count cap.

## Outputs

- `results/data_inventory.csv`: discovered telemetry CSVs and metadata/case files.
- `results/ground_truth_inventory.csv`: anomaly-window counts and time ranges.
- `data/processed/sample_predictions.csv`: sample-level outlier flags and scores.
- `results/alarms.csv`: temporal and spatial alarms for k=1..5.
- `results/metrics_summary.csv`: alarm precision, event recall, alarm-event F1, false alarms per hour, detection delay, runtime, and event counts. Compatibility aliases `precision`, `recall`, and `f1` are also retained.
- `results/event_level_results.csv`: per-event detection and delay records.
- `results/runtime_summary.csv`: per-node runtime and feature counts.
- `results/failure_log.csv`: explicit dataset/node failures or skips.
- `results/experiment_log.md`: parameters, feature rules, actual result table, runtime summary, and failures.
- `results/presentation_findings.md`: presentation/report-ready summary.
- `figures/*.png`: pipeline, timeline, model comparison, feature comparison, k sweep, and runtime plots.

## Reproducibility Notes

Ground-truth labels are used only after predictions are generated. DenStream and MiniBatchKMeans normalize using the initial `sampleSkip` baseline buffer only. DBSCAN is included as a transductive baseline and is documented separately because it sees the full node matrix at fit time.

Metrics use alarm/event evaluation, not standard sample-level binary classification: alarm precision is computed over generated alarms, event recall is computed over ground-truth events, and alarm-event F1 is the harmonic mean of those two quantities.
