"""Dataset discovery and loading utilities for Cisco telemetry experiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_DIR = PROJECT_ROOT / "data" / "external"
BIGDAMA_DIR = EXTERNAL_DIR / "OutlierDenStream-BigDama18"
TELEMETRY_DIR = EXTERNAL_DIR / "telemetry"
DATASET_BY_NODES_DIR = BIGDAMA_DIR / "Data" / "DatasetByNodes"
BIGDAMA_GROUND_TRUTH_DIR = BIGDAMA_DIR / "GrounTruth"

DEFAULT_NODES = [
    "leaf1",
    "leaf2",
    "leaf3",
    "leaf5",
    "leaf6",
    "leaf7",
    "leaf8",
    "spine1",
    "spine2",
    "spine3",
    "spine4",
]

CONTROL_PLANE_FEATURES = [
    "active-routes-count",
    "as",
    "backup-routes-count",
    "deleted-routes-count",
    "paths-count",
    "protocol-route-memory",
    "routes-counts",
    "global__established-neighbors-count-total",
    "global__neighbors-count-total",
    "global__nexthop-count",
    "global__restart-count",
    "performance-statistics__global__configuration-items-processed",
    "performance-statistics__global__ipv4rib-server__rib-connection-up-count",
    "performance-statistics__vrf__inbound-update-messages",
    "vrf__neighbors-count",
    "vrf__network-count",
    "vrf__path-count",
    "vrf__update-messages-received",
]


@dataclass(frozen=True)
class NodeDatasetFile:
    dataset: str
    node: str
    path: Path
    size_bytes: int
    source: str = "OutlierDenStream-BigDama18"


def ensure_output_dirs() -> None:
    for rel in ["data/raw", "data/external", "data/processed", "results", "figures", "notebooks"]:
        (PROJECT_ROOT / rel).mkdir(parents=True, exist_ok=True)


def parse_node_dataset_name(path: Path, nodes: Iterable[str] = DEFAULT_NODES) -> tuple[str, str] | None:
    stem = path.stem
    for node in sorted(nodes, key=len, reverse=True):
        if stem.startswith(node):
            dataset = stem[len(node) :]
            if dataset:
                return node, dataset
    return None


def discover_node_datasets(base_dir: Path = DATASET_BY_NODES_DIR) -> list[NodeDatasetFile]:
    if not base_dir.exists():
        return []
    records: list[NodeDatasetFile] = []
    for csv_path in sorted(base_dir.glob("*.csv")):
        parsed = parse_node_dataset_name(csv_path)
        if not parsed:
            continue
        node, dataset = parsed
        records.append(
            NodeDatasetFile(
                dataset=dataset,
                node=node,
                path=csv_path,
                size_bytes=csv_path.stat().st_size,
            )
        )
    return records


def available_datasets(base_dir: Path = DATASET_BY_NODES_DIR) -> dict[str, list[NodeDatasetFile]]:
    grouped: dict[str, list[NodeDatasetFile]] = {}
    for record in discover_node_datasets(base_dir):
        grouped.setdefault(record.dataset, []).append(record)
    return {key: sorted(value, key=lambda item: item.node) for key, value in sorted(grouped.items())}


def ground_truth_path(dataset: str, ground_truth_dir: Path = BIGDAMA_GROUND_TRUTH_DIR) -> Path | None:
    path = ground_truth_dir / f"{dataset}.txt"
    return path if path.exists() else None


def read_ground_truth(path: Path | str) -> pd.DataFrame:
    """Read BigDAMA/Cisco event windows into a normalized DataFrame.

    Output columns are: event_id, node, host, start, end, event, type.
    Timestamps are Unix seconds as floats because the telemetry files store seconds.
    """

    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=["event_id", "node", "host", "start", "end", "event", "type"])

    try:
        df = pd.read_csv(path)
    except pd.errors.ParserError:
        df = pd.read_csv(path, sep="\t", header=None)

    normalized = pd.DataFrame()
    lower_map = {str(col).strip().lower(): col for col in df.columns}
    if {"node", "start", "end"}.issubset(lower_map):
        normalized["node"] = df[lower_map["node"]].astype(str)
        normalized["host"] = df[lower_map.get("host", lower_map["node"])].astype(str)
        normalized["start"] = pd.to_numeric(df[lower_map["start"]], errors="coerce")
        normalized["end"] = pd.to_numeric(df[lower_map["end"]], errors="coerce")
        normalized["event"] = df[lower_map.get("event", lower_map["node"])].astype(str)
        normalized["type"] = df[lower_map.get("type", lower_map["node"])].astype(str)
    else:
        if df.shape[1] < 4:
            raise ValueError(f"Ground-truth file has unsupported schema: {path}")
        normalized["node"] = df.iloc[:, 0].astype(str)
        normalized["host"] = df.iloc[:, 1].astype(str)
        normalized["start"] = pd.to_numeric(df.iloc[:, 2], errors="coerce")
        normalized["end"] = normalized["start"] + 300
        normalized["event"] = df.iloc[:, 3].astype(str)
        normalized["type"] = "single"

    normalized = normalized.dropna(subset=["start", "end"]).copy()
    normalized["event_id"] = range(len(normalized))
    normalized = normalized[["event_id", "node", "host", "start", "end", "event", "type"]]
    return normalized.sort_values(["start", "node"]).reset_index(drop=True)


def load_node_csv(path: Path | str, max_rows: int | None = None) -> pd.DataFrame:
    path = Path(path)
    df = pd.read_csv(path, low_memory=False, nrows=max_rows)
    unnamed = [col for col in df.columns if str(col).startswith("Unnamed")]
    if unnamed:
        df = df.drop(columns=unnamed)
    if "time" not in df.columns:
        raise ValueError(f"Telemetry CSV is missing required 'time' column: {path}")
    df["time"] = pd.to_numeric(df["time"], errors="coerce")
    df = df.dropna(subset=["time"]).copy()
    df = df.sort_values("time").reset_index(drop=True)
    return df


def dataset_files(dataset: str, nodes: Iterable[str] | None = None) -> list[NodeDatasetFile]:
    wanted = set(nodes) if nodes else None
    files = available_datasets().get(dataset, [])
    if wanted is not None:
        files = [record for record in files if record.node in wanted]
    return files


def build_data_inventory() -> pd.DataFrame:
    rows = []
    for record in discover_node_datasets():
        truth = ground_truth_path(record.dataset)
        rows.append(
            {
                "source": record.source,
                "scenario_name": record.dataset,
                "node": record.node,
                "csv_file": str(record.path.relative_to(PROJECT_ROOT)),
                "case_or_ground_truth_file": str(truth.relative_to(PROJECT_ROOT)) if truth else "",
                "file_size_bytes": record.size_bytes,
                "status": "available",
            }
        )

    if TELEMETRY_DIR.exists():
        for path in sorted(TELEMETRY_DIR.rglob("*")):
            if not path.is_file():
                continue
            name = path.name.lower()
            if name.endswith((".txt", ".csv", ".json", ".md")) and (
                "ground" in name or "case" in name or "event" in name or "header" in name
            ):
                rows.append(
                    {
                        "source": "cisco-ie/telemetry",
                        "scenario_name": path.parent.name,
                        "node": "",
                        "csv_file": str(path.relative_to(PROJECT_ROOT)) if path.suffix.lower() == ".csv" else "",
                        "case_or_ground_truth_file": str(path.relative_to(PROJECT_ROOT)),
                        "file_size_bytes": path.stat().st_size,
                        "status": "metadata_available",
                    }
                )
    return pd.DataFrame(rows).sort_values(["source", "scenario_name", "node", "csv_file"]).reset_index(drop=True)


def build_ground_truth_inventory() -> pd.DataFrame:
    rows = []
    for dataset in available_datasets():
        path = ground_truth_path(dataset)
        if path is None:
            rows.append(
                {
                    "dataset": dataset,
                    "ground_truth_file": "",
                    "event_count": 0,
                    "nodes": "",
                    "start_min": "",
                    "end_max": "",
                    "events": "",
                    "status": "missing_ground_truth",
                }
            )
            continue
        try:
            truth = read_ground_truth(path)
            rows.append(
                {
                    "dataset": dataset,
                    "ground_truth_file": str(path.relative_to(PROJECT_ROOT)),
                    "event_count": len(truth),
                    "nodes": ";".join(sorted(truth["node"].dropna().astype(str).unique())),
                    "start_min": truth["start"].min() if len(truth) else "",
                    "end_max": truth["end"].max() if len(truth) else "",
                    "events": ";".join(sorted(truth["event"].dropna().astype(str).unique())),
                    "status": "available",
                }
            )
        except Exception as exc:  # noqa: BLE001 - inventory must report malformed files.
            rows.append(
                {
                    "dataset": dataset,
                    "ground_truth_file": str(path.relative_to(PROJECT_ROOT)),
                    "event_count": 0,
                    "nodes": "",
                    "start_min": "",
                    "end_max": "",
                    "events": "",
                    "status": f"failed_to_parse: {exc}",
                }
            )
    return pd.DataFrame(rows).sort_values("dataset").reset_index(drop=True)


def write_inventories(results_dir: Path | None = None) -> tuple[Path, Path]:
    ensure_output_dirs()
    results_dir = results_dir or PROJECT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    data_path = results_dir / "data_inventory.csv"
    truth_path = results_dir / "ground_truth_inventory.csv"
    build_data_inventory().to_csv(data_path, index=False)
    build_ground_truth_inventory().to_csv(truth_path, index=False)
    return data_path, truth_path
