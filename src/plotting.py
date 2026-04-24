"""Plot generation for the project report and presentation."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def pipeline_diagram(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(13, 2.8))
    ax.axis("off")
    labels = [
        "Streaming\nTelemetry",
        "Preprocessing\nNormalization",
        "DenStream",
        "Outlier\nScoring",
        "Alarm\nLogic",
        "Evaluation",
    ]
    x_positions = range(len(labels))
    palette = ["#4c78a8", "#72b7b2", "#54a24b", "#eeca3b", "#f58518", "#b279a2"]
    for x, label, color in zip(x_positions, labels, palette):
        ax.text(
            x,
            0.5,
            label,
            ha="center",
            va="center",
            fontsize=11,
            bbox={"boxstyle": "round,pad=0.35", "fc": color, "ec": "#222222", "alpha": 0.9},
            color="white" if color not in {"#eeca3b"} else "#222222",
        )
        if x < len(labels) - 1:
            ax.annotate("", xy=(x + 0.72, 0.5), xytext=(x + 0.28, 0.5), arrowprops={"arrowstyle": "->", "lw": 1.8})
    ax.set_xlim(-0.6, len(labels) - 0.4)
    ax.set_ylim(0, 1)
    _save(fig, path)


def timeline_ground_truth_vs_alarms(alarms: pd.DataFrame, ground_truth: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(13, 5.5))
    if ground_truth.empty:
        ax.text(0.5, 0.5, "No ground-truth windows available", ha="center", va="center")
        _save(fig, path)
        return

    nodes = sorted(set(ground_truth["node"].astype(str)) | set(";".join(alarms.get("nodes", pd.Series(dtype=str)).astype(str)).split(";")))
    nodes = [node for node in nodes if node]
    node_to_y = {node: idx for idx, node in enumerate(nodes)}
    for _, event in ground_truth.iterrows():
        y = node_to_y.get(str(event["node"]), 0)
        ax.plot([event["start"], event["end"]], [y, y], lw=8, color="#d62728", alpha=0.5, solid_capstyle="butt")

    plot_alarms = alarms.copy()
    if not plot_alarms.empty:
        plot_alarms = plot_alarms[(plot_alarms["method"] == "DenStream") & (plot_alarms["k"] == 1)]
        for _, alarm in plot_alarms.iterrows():
            for node in str(alarm["nodes"]).split(";"):
                if node in node_to_y:
                    marker = "o" if alarm["detection_type"] == "temporal" else "^"
                    color = "#1f77b4" if alarm["detection_type"] == "temporal" else "#2ca02c"
                    ax.scatter(alarm["timestamp"], node_to_y[node], s=30, marker=marker, color=color, alpha=0.75)

    ax.set_yticks(list(node_to_y.values()))
    ax.set_yticklabels(list(node_to_y.keys()))
    ax.set_xlabel("Unix timestamp (seconds)")
    ax.set_ylabel("Node")
    ax.set_title("Ground-truth anomaly windows and DenStream alarms")
    ax.grid(axis="x", alpha=0.25)
    _save(fig, path)


def precision_recall_f1_by_method(metrics: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    if metrics.empty:
        ax.text(0.5, 0.5, "No metrics available", ha="center", va="center")
        _save(fig, path)
        return
    subset = metrics[(metrics["detection_type"] == "temporal") & (metrics["k"] == 1)].copy()
    if subset.empty:
        subset = metrics.copy()
    melted = subset.melt(id_vars=["method"], value_vars=["precision", "recall", "f1"], var_name="metric", value_name="value")
    sns.barplot(data=melted, x="method", y="value", hue="metric", ax=ax, palette="Set2")
    ax.set_ylim(0, 1.05)
    ax.set_title("Precision, recall, and F1 by method")
    ax.set_xlabel("Method")
    ax.set_ylabel("Score")
    _save(fig, path)


def feature_model_comparison(metrics: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    subset = metrics[(metrics["method"] == "DenStream") & (metrics["detection_type"] == "temporal") & (metrics["k"] == 1)]
    if subset.empty:
        subset = metrics[metrics["method"] == "DenStream"]
    if subset.empty:
        ax.text(0.5, 0.5, "No DenStream metrics available", ha="center", va="center")
    else:
        sns.barplot(data=subset, x="feature_mode", y="f1", hue="dataset", ax=ax, palette="Set3")
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("Feature mode")
        ax.set_ylabel("F1")
        ax.set_title("Feature-mode comparison")
    _save(fig, path)


def temporal_vs_spatial_k_sweep(metrics: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    subset = metrics[metrics["method"] == "DenStream"].copy()
    if subset.empty:
        ax.text(0.5, 0.5, "No DenStream metrics available", ha="center", va="center")
    else:
        sns.lineplot(data=subset, x="k", y="f1", hue="detection_type", style="feature_mode", marker="o", ax=ax)
        ax.set_ylim(0, 1.05)
        ax.set_title("Temporal vs spatial k sweep")
        ax.set_xlabel("k")
        ax.set_ylabel("F1")
    _save(fig, path)


def runtime_comparison(runtime: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    if runtime.empty:
        ax.text(0.5, 0.5, "No runtime records available", ha="center", va="center")
    else:
        summary = runtime.groupby(["method", "feature_mode"], as_index=False)["runtime_seconds"].sum()
        sns.barplot(data=summary, x="method", y="runtime_seconds", hue="feature_mode", ax=ax, palette="Set2")
        ax.set_title("Runtime comparison")
        ax.set_xlabel("Method")
        ax.set_ylabel("Runtime seconds")
    _save(fig, path)


def write_all_figures(
    figures_dir: Path,
    metrics: pd.DataFrame,
    alarms: pd.DataFrame,
    runtime: pd.DataFrame,
    representative_truth: pd.DataFrame,
) -> None:
    pipeline_diagram(figures_dir / "pipeline_diagram.png")
    timeline_ground_truth_vs_alarms(alarms, representative_truth, figures_dir / "timeline_ground_truth_vs_alarms.png")
    precision_recall_f1_by_method(metrics, figures_dir / "precision_recall_f1_by_method.png")
    feature_model_comparison(metrics, figures_dir / "feature_model_comparison.png")
    temporal_vs_spatial_k_sweep(metrics, figures_dir / "temporal_vs_spatial_k_sweep.png")
    runtime_comparison(runtime, figures_dir / "runtime_comparison.png")
