"""Plot generation for the project report and presentation."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .report_artifacts import TimelineConfig, alarms_for_config, ranked_metrics, timeline_config_text


def _save(
    fig: plt.Figure,
    path: Path,
    metadata: dict[str, str] | None = None,
    rect: tuple[float, float, float, float] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if rect is None:
        fig.tight_layout()
    else:
        fig.tight_layout(rect=rect)
    fig.savefig(path, dpi=180, metadata=metadata)
    plt.close(fig)


def _metric_column(metrics: pd.DataFrame, explicit_name: str, compatibility_name: str) -> str:
    if explicit_name in metrics.columns:
        return explicit_name
    return compatibility_name


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


def _alarm_nodes(alarms: pd.DataFrame) -> set[str]:
    nodes: set[str] = set()
    if "nodes" not in alarms.columns:
        return nodes
    for node_list in alarms["nodes"].dropna().astype(str):
        nodes.update(node for node in node_list.split(";") if node)
    return nodes


def timeline_ground_truth_vs_alarms(
    alarms: pd.DataFrame,
    ground_truth: pd.DataFrame,
    path: Path,
    config: TimelineConfig | None,
) -> None:
    fig, ax = plt.subplots(figsize=(13, 5.5))
    if config is None:
        ax.text(0.5, 0.5, "No representative timeline configuration available", ha="center", va="center")
        ax.set_title("Ground Truth vs Alarms: no configuration")
        _save(fig, path)
        return

    if "dataset" in ground_truth.columns:
        plot_truth = ground_truth[ground_truth["dataset"].astype(str) == config.dataset].copy()
    else:
        plot_truth = ground_truth.copy()
    plot_alarms = alarms_for_config(alarms, config)

    title = f"Ground Truth vs Alarms: {timeline_config_text(config)}"
    if plot_truth.empty:
        ax.text(0.5, 0.5, f"No ground-truth windows available for {config.dataset}", ha="center", va="center")
        ax.set_title(title)
        _save(
            fig,
            path,
            metadata={"Title": title, "Description": f"Representative timeline filtered to {timeline_config_text(config)}."},
        )
        return

    nodes = sorted(set(plot_truth["node"].astype(str)) | _alarm_nodes(plot_alarms))
    node_to_y = {node: idx for idx, node in enumerate(nodes)}
    ground_truth_labeled = False
    for _, event in plot_truth.iterrows():
        y = node_to_y.get(str(event["node"]), 0)
        ax.plot(
            [float(event["start"]), float(event["end"])],
            [y, y],
            lw=8,
            color="#d62728",
            alpha=0.5,
            solid_capstyle="butt",
            label="Ground truth window" if not ground_truth_labeled else None,
        )
        ground_truth_labeled = True

    if not plot_alarms.empty:
        labeled_markers: set[str] = set()
        for _, alarm in plot_alarms.iterrows():
            for node in str(alarm["nodes"]).split(";"):
                if node in node_to_y:
                    marker = "o" if alarm["detection_type"] == "temporal" else "^"
                    color = "#1f77b4" if alarm["detection_type"] == "temporal" else "#2ca02c"
                    label = f"{alarm['detection_type']} alarm"
                    ax.scatter(
                        float(alarm["timestamp"]),
                        node_to_y[node],
                        s=30,
                        marker=marker,
                        color=color,
                        alpha=0.75,
                        label=label if label not in labeled_markers else None,
                    )
                    labeled_markers.add(label)
    else:
        ax.text(0.01, 0.95, "Selected configuration produced no alarms.", transform=ax.transAxes, va="top")

    ax.set_yticks(list(node_to_y.values()))
    ax.set_yticklabels(list(node_to_y.keys()))
    ax.set_xlabel("Unix timestamp (seconds)")
    ax.set_ylabel("Node")
    ax.set_title(title)
    ax.grid(axis="x", alpha=0.25)
    ax.legend(loc="upper right")
    caption = (
        f"Filtered to dataset={config.dataset}, method={config.method}, feature_mode={config.feature_mode}, "
        f"detection_type={config.detection_type}, k={config.k}; alarms shown={len(plot_alarms)}."
    )
    fig.text(0.01, 0.01, caption, ha="left", fontsize=9)
    _save(
        fig,
        path,
        metadata={"Title": title, "Description": caption},
        rect=(0, 0.06, 1, 1),
    )


def precision_recall_f1_by_method(metrics: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    if metrics.empty:
        ax.text(0.5, 0.5, "No metrics available", ha="center", va="center")
        _save(fig, path)
        return
    subset = metrics[(metrics["detection_type"] == "temporal") & (metrics["k"] == 1)].copy()
    if subset.empty:
        ax.text(0.5, 0.5, "No temporal k=1 metrics available", ha="center", va="center")
        ax.set_title("Fixed-slice alarm/event metrics by method (temporal k=1)")
        _save(fig, path)
        return
    metric_labels = {
        _metric_column(subset, "alarm_precision", "precision"): "Alarm precision",
        _metric_column(subset, "event_recall", "recall"): "Event recall",
        _metric_column(subset, "alarm_event_f1", "f1"): "Alarm-event F1",
    }
    melted = subset.melt(
        id_vars=["method"],
        value_vars=list(metric_labels),
        var_name="metric",
        value_name="value",
    )
    melted["metric"] = melted["metric"].map(metric_labels)
    sns.barplot(data=melted, x="method", y="value", hue="metric", ax=ax, palette="Set2")
    ax.set_ylim(0, 1.05)
    ax.set_title("Fixed-slice alarm/event metrics by method (temporal k=1)")
    ax.set_xlabel("Method")
    ax.set_ylabel("Score")
    _save(fig, path)


def best_method_comparison(metrics: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    if metrics.empty:
        ax.text(0.5, 0.5, "No metrics available", ha="center", va="center")
        _save(fig, path)
        return

    best = ranked_metrics(metrics).groupby("method", sort=False, dropna=False).head(1).copy()
    if best.empty:
        ax.text(0.5, 0.5, "No method metrics available", ha="center", va="center")
        _save(fig, path)
        return
    metric_labels = {
        _metric_column(best, "alarm_precision", "precision"): "Alarm precision",
        _metric_column(best, "event_recall", "recall"): "Event recall",
        _metric_column(best, "alarm_event_f1", "f1"): "Alarm-event F1",
    }
    melted = best.melt(
        id_vars=["method"],
        value_vars=list(metric_labels),
        var_name="metric",
        value_name="value",
    )
    melted["metric"] = melted["metric"].map(metric_labels)
    sns.barplot(data=melted, x="method", y="value", hue="metric", ax=ax, palette="Set2")
    ax.set_ylim(0, 1.05)
    ax.set_title("Best-configuration alarm/event metrics by method")
    ax.set_xlabel("Method")
    ax.set_ylabel("Score")
    caption = "Each method uses the configuration with highest alarm-event F1, with ties preferring ControlPlane and temporal settings."
    fig.text(0.01, 0.01, caption, ha="left", fontsize=9)
    _save(fig, path, metadata={"Title": ax.get_title(), "Description": caption}, rect=(0, 0.06, 1, 1))


def feature_model_comparison(metrics: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    subset = metrics[(metrics["method"] == "DenStream") & (metrics["detection_type"] == "temporal") & (metrics["k"] == 1)]
    if subset.empty:
        ax.text(0.5, 0.5, "No DenStream temporal k=1 metrics available", ha="center", va="center")
        ax.set_title("Fixed-slice DenStream feature-mode comparison (temporal k=1)")
    else:
        f1_col = _metric_column(subset, "alarm_event_f1", "f1")
        sns.barplot(data=subset, x="feature_mode", y=f1_col, hue="dataset", ax=ax, palette="Set3")
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("Feature mode")
        ax.set_ylabel("Alarm-event F1")
        ax.set_title("Fixed-slice DenStream feature-mode comparison (temporal k=1)")
    _save(fig, path)


def temporal_vs_spatial_k_sweep(metrics: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    subset = metrics[metrics["method"] == "DenStream"].copy()
    if subset.empty:
        ax.text(0.5, 0.5, "No DenStream metrics available", ha="center", va="center")
    else:
        f1_col = _metric_column(subset, "alarm_event_f1", "f1")
        sns.lineplot(data=subset, x="k", y=f1_col, hue="detection_type", style="feature_mode", marker="o", ax=ax)
        ax.set_ylim(0, 1.05)
        ax.set_title("DenStream temporal vs spatial alarm-event F1 k sweep")
        ax.set_xlabel("Alarm aggregation k")
        ax.set_ylabel("Alarm-event F1")
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
    ground_truth: pd.DataFrame,
    timeline_config: TimelineConfig | None,
) -> None:
    pipeline_diagram(figures_dir / "pipeline_diagram.png")
    timeline_ground_truth_vs_alarms(alarms, ground_truth, figures_dir / "timeline_ground_truth_vs_alarms.png", timeline_config)
    precision_recall_f1_by_method(metrics, figures_dir / "precision_recall_f1_by_method.png")
    best_method_comparison(metrics, figures_dir / "best_method_comparison.png")
    feature_model_comparison(metrics, figures_dir / "feature_model_comparison.png")
    temporal_vs_spatial_k_sweep(metrics, figures_dir / "temporal_vs_spatial_k_sweep.png")
    runtime_comparison(runtime, figures_dir / "runtime_comparison.png")
