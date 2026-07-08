from __future__ import annotations

from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


RESULTS_DIR = Path("results")
TABLES_DIR = RESULTS_DIR / "tables"
PLOTS_DIR = RESULTS_DIR / "plots"
TABLE_IMAGES_DIR = RESULTS_DIR / "table_images"
RAW_RESULTS = RESULTS_DIR / "raw_results.csv"
SUMMARY_RESULTS = RESULTS_DIR / "summary_results.csv"
KMEANS_METHODS = ("kmeans_default", "kmeans_hamming")
ANALYSIS_MAX_SAMPLE_PERCENT = 70
PAPER_TABLE_IMAGE_NAMES = (
    "methods_summary",
    "best_method_by_dataset",
    "sample_sizes",
    "presentation_summary",
    "best_by_dataset_fraction_mape",
    "mean_k_presentation_summary",
    "best_by_dataset_fraction",
    "mean_k_best_by_dataset_fraction",
    "kmeans_best_k",
    "kmeans_k_frequency",
)


def main() -> None:
    generate_tables()
    generate_plots()


def generate_tables() -> None:
    if not RAW_RESULTS.exists() or not SUMMARY_RESULTS.exists():
        raise SystemExit("Run `uv run python run_experiments.py` before generating tables.")

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    clear_table_outputs()
    TABLE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    clear_table_image_outputs()

    raw = filter_presentation_methods(filter_analysis_window(normalize_raw(pd.read_csv(RAW_RESULTS, keep_default_na=False))))
    summary = filter_presentation_methods(
        filter_analysis_window(normalize_summary(pd.read_csv(SUMMARY_RESULTS, keep_default_na=False)))
    )

    write_table(build_methods_summary(), "methods_summary")
    write_table(build_sample_sizes(summary), "sample_sizes")
    write_table(build_best_method_by_dataset(summary), "best_method_by_dataset")
    write_table(build_best_by_dataset_fraction(summary), "best_by_dataset_fraction")
    write_table(build_best_by_dataset_fraction_mape(summary), "best_by_dataset_fraction_mape")
    write_table(build_kmeans_best_k(summary), "kmeans_best_k")
    write_table(build_kmeans_k_ranking(summary), "kmeans_k_ranking")
    write_table(build_kmeans_k_frequency(summary), "kmeans_k_frequency")
    write_table(build_presentation_summary(summary), "presentation_summary")
    write_table(build_repetition_counts(raw), "repetition_counts")

    mean_k_summary = collapse_kmeans_by_mean_k(summary)
    write_table(build_best_by_dataset_fraction(mean_k_summary), "mean_k_best_by_dataset_fraction")
    write_table(build_kmeans_mean_k(mean_k_summary), "mean_k_kmeans_by_dataset_fraction")
    write_table(build_presentation_summary_mean_k(mean_k_summary), "mean_k_presentation_summary")
    write_paper_table_images()

    print(f"Saved tables in {TABLES_DIR}")
    print(f"Saved table images in {TABLE_IMAGES_DIR}")


def generate_plots() -> None:
    if not SUMMARY_RESULTS.exists():
        raise SystemExit("Run `uv run python run_experiments.py` before generating plots.")

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    clear_plot_outputs()

    summary = filter_presentation_methods(
        filter_analysis_window(normalize_summary(pd.read_csv(SUMMARY_RESULTS, keep_default_na=False)))
    )
    plot_methods_by_dataset(summary)
    plot_kmeans_by_dataset(summary)
    plot_k_frequency(summary)
    plot_k_frequency_by_dataset(summary)
    plot_k_vs_mape_by_dataset(summary)
    plot_k_delta_heatmap_by_dataset(summary)
    plot_best_kmeans_vs_baselines(summary)
    plot_mean_k_methods_by_dataset(summary)
    plot_mean_k_vs_baselines(summary)

    print(f"Saved plots in {PLOTS_DIR}")


def normalize_summary(summary: pd.DataFrame) -> pd.DataFrame:
    normalized = summary.copy()
    normalized["sample_percent"] = (normalized["sample_fraction"].astype(float) * 100).round().astype(int)
    normalized["method_label"] = normalized.apply(method_label, axis=1)
    normalized["mean_mape_percent"] = normalized["mean_mape"].astype(float) * 100.0
    normalized["std_mape_percent"] = normalized["std_mape"].astype(float) * 100.0
    return normalized


def normalize_raw(raw: pd.DataFrame) -> pd.DataFrame:
    normalized = raw.copy()
    normalized["sample_percent"] = (normalized["sample_fraction"].astype(float) * 100).round().astype(int)
    return normalized


def filter_analysis_window(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["sample_percent"] <= ANALYSIS_MAX_SAMPLE_PERCENT].copy()


def filter_presentation_methods(frame: pd.DataFrame) -> pd.DataFrame:
    presentation_methods = {"random", "diversity", *KMEANS_METHODS}
    return frame[frame["sampling_method"].isin(presentation_methods)].copy()


def method_label(row: pd.Series) -> str:
    if row["sampling_method"] in KMEANS_METHODS:
        if row.get("k", "") == "":
            return f"{variant_label(row['sampling_method'])} (mean K)"
        return f"{variant_label(row['sampling_method'])} (K={int(row['k'])})"
    return {
        "random": "Random",
        "diversity": "Diversity",
    }.get(row["sampling_method"], row["sampling_method"])


def variant_label(method: str) -> str:
    return {
        "kmeans_default": "K-means default",
        "kmeans_hamming": "K-means Hamming",
        "kmeans_random": "K-means random",
    }.get(method, method)


def build_methods_summary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Method": "Random",
                "Summary": "Randomly selects variants without replacement.",
            },
            {
                "Method": "Diversity",
                "Summary": "Iteratively selects variants that are farthest from the already selected set using normalized Hamming distance.",
            },
            {
                "Method": "K-means default",
                "Summary": "Uses standard K-means with Euclidean distance; samples by alternating between clusters and preserves the original order inside each cluster.",
            },
            {
                "Method": "K-means Hamming",
                "Summary": "Uses standard K-means with Euclidean distance; samples by alternating between clusters and orders variants inside each cluster by Hamming diversity.",
            },
        ]
    )


def build_sample_sizes(summary: pd.DataFrame) -> pd.DataFrame:
    return (
        summary[["dataset", "sample_percent", "sample_size"]]
        .drop_duplicates()
        .sort_values(["dataset", "sample_percent"])
        .rename(columns={"dataset": "Dataset", "sample_percent": "Sample (%)", "sample_size": "Sample size"})
    )


def build_best_by_dataset_fraction(summary: pd.DataFrame) -> pd.DataFrame:
    best_rows = summary.loc[summary.groupby(["dataset", "sample_percent"])["mean_mape"].idxmin()].copy()
    best_rows = best_rows.sort_values(["dataset", "sample_percent"])
    return pd.DataFrame(
        {
            "Dataset": best_rows["dataset"],
            "Sample (%)": best_rows["sample_percent"],
            "Best method": best_rows["method_label"],
            "MAPE (%)": best_rows["mean_mape_percent"].map(format_percent),
            "Std (%)": best_rows["std_mape_percent"].map(format_percent),
            "Sample size": best_rows["sample_size"],
        }
    )


def build_best_by_dataset_fraction_mape(summary: pd.DataFrame) -> pd.DataFrame:
    best_rows = summary.loc[summary.groupby(["dataset", "sample_percent"])["mean_mape"].idxmin()].copy()
    best_rows = best_rows.sort_values(["dataset", "sample_percent"])
    return pd.DataFrame(
        {
            "Dataset": best_rows["dataset"],
            "Sample (%)": best_rows["sample_percent"],
            "Best method": best_rows["method_label"],
            "MAPE": best_rows["mean_mape_percent"].map(format_percent),
        }
    )


def build_best_method_by_dataset(summary: pd.DataFrame) -> pd.DataFrame:
    best_rows = summary.loc[summary.groupby(["dataset", "sample_percent"])["mean_mape"].idxmin()].copy()
    best_rows["winner"] = best_rows["sampling_method"].map(variant_label)
    best_rows.loc[best_rows["sampling_method"] == "random", "winner"] = "Random"
    best_rows.loc[best_rows["sampling_method"] == "diversity", "winner"] = "Diversity"

    rows = []
    for dataset, group in best_rows.groupby("dataset", sort=True):
        counts = group["winner"].value_counts()
        best_method = counts.index[0]
        wins = int(counts.iloc[0])
        mean_best_mape = group[group["winner"] == best_method]["mean_mape_percent"].mean()
        rows.append(
            {
                "Dataset": dataset,
                "Best method": best_method,
                "Wins": f"{wins}/{group['sample_percent'].nunique()}",
                "MAPE": format_percent(mean_best_mape),
                "Won samples (%)": ", ".join(str(value) for value in group[group["winner"] == best_method]["sample_percent"]),
            }
        )
    return pd.DataFrame(rows)


def build_kmeans_best_k(summary: pd.DataFrame) -> pd.DataFrame:
    kmeans = summary[summary["sampling_method"].isin(KMEANS_METHODS)].copy()
    best_rows = kmeans.loc[kmeans.groupby(["dataset", "sample_percent"])["mean_mape"].idxmin()]
    best_rows = best_rows.sort_values(["dataset", "sample_percent"])
    return pd.DataFrame(
        {
            "Dataset": best_rows["dataset"],
            "Sample (%)": best_rows["sample_percent"],
            "Best variant": best_rows["sampling_method"].map(variant_label),
            "Best K": best_rows["k"].astype(int),
            "MAPE (%)": best_rows["mean_mape_percent"].map(format_percent),
            "Std (%)": best_rows["std_mape_percent"].map(format_percent),
            "Sample size": best_rows["sample_size"],
        }
    )


def build_kmeans_k_ranking(summary: pd.DataFrame) -> pd.DataFrame:
    kmeans = summary[summary["sampling_method"].isin(KMEANS_METHODS)].copy()
    kmeans["rank"] = kmeans.groupby(["dataset", "sample_percent", "sampling_method"])["mean_mape"].rank(method="min")
    best = kmeans.groupby(["dataset", "sample_percent", "sampling_method"])["mean_mape_percent"].transform("min")
    kmeans["delta_to_best"] = kmeans["mean_mape_percent"] - best
    kmeans["delta_to_best_percent"] = (kmeans["delta_to_best"] / best) * 100.0
    kmeans = kmeans.sort_values(["dataset", "sample_percent", "sampling_method", "rank", "k"])
    return pd.DataFrame(
        {
            "Dataset": kmeans["dataset"],
            "Sample (%)": kmeans["sample_percent"],
            "Variant": kmeans["sampling_method"].map(variant_label),
            "K": kmeans["k"].astype(int),
            "Rank": kmeans["rank"].astype(int),
            "MAPE (%)": kmeans["mean_mape_percent"].map(format_percent),
            "Std (%)": kmeans["std_mape_percent"].map(format_percent),
            "Delta to best K": kmeans["delta_to_best"].map(format_percent),
            "Delta to best K (%)": kmeans["delta_to_best_percent"].map(format_percent),
            "Sample size": kmeans["sample_size"],
        }
    )


def build_kmeans_k_frequency(summary: pd.DataFrame) -> pd.DataFrame:
    best_k = build_kmeans_best_k(summary)
    frequency = (
        best_k.groupby(["Best variant", "Best K"])
        .size()
        .reset_index(name="Best count")
        .sort_values(["Best count", "Best variant", "Best K"], ascending=[False, True, True])
    )
    frequency["Share (%)"] = (frequency["Best count"] / frequency["Best count"].sum() * 100.0).map(format_percent)
    return frequency


def build_presentation_summary(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (dataset, sample_percent), group in summary.groupby(["dataset", "sample_percent"], sort=True):
        random = group[group["sampling_method"] == "random"].iloc[0]
        diversity = group[group["sampling_method"] == "diversity"].iloc[0]
        best_kmeans = group[group["sampling_method"].isin(KMEANS_METHODS)].sort_values("mean_mape").iloc[0]
        best_overall = group.sort_values("mean_mape").iloc[0]
        rows.append(
            {
                "Dataset": dataset,
                "Sample (%)": sample_percent,
                "Sample size": int(random["sample_size"]),
                "Random MAPE (%)": format_percent(random["mean_mape_percent"]),
                "Diversity MAPE (%)": format_percent(diversity["mean_mape_percent"]),
                "Best K-means": (
                    f"{variant_label(best_kmeans['sampling_method'])}, "
                    f"K={int(best_kmeans['k'])} ({format_percent(best_kmeans['mean_mape_percent'])}%)"
                ),
                "Best overall": best_overall["method_label"],
            }
        )
    return pd.DataFrame(rows)


def build_presentation_summary_mean_k(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (dataset, sample_percent), group in summary.groupby(["dataset", "sample_percent"], sort=True):
        random = group[group["sampling_method"] == "random"].iloc[0]
        diversity = group[group["sampling_method"] == "diversity"].iloc[0]
        kmeans = group[group["sampling_method"].isin(KMEANS_METHODS)]
        best_kmeans = kmeans.sort_values("mean_mape").iloc[0]
        best_overall = group.sort_values("mean_mape").iloc[0]
        rows.append(
            {
                "Dataset": dataset,
                "Sample (%)": sample_percent,
                "Sample size": int(random["sample_size"]),
                "Random MAPE (%)": format_percent(random["mean_mape_percent"]),
                "Diversity MAPE (%)": format_percent(diversity["mean_mape_percent"]),
                "Best mean-K K-means": (
                    f"{variant_label(best_kmeans['sampling_method'])} "
                    f"({format_percent(best_kmeans['mean_mape_percent'])}%)"
                ),
                "Best overall": best_overall["method_label"],
            }
        )
    return pd.DataFrame(rows)


def build_kmeans_mean_k(summary: pd.DataFrame) -> pd.DataFrame:
    kmeans = summary[summary["sampling_method"].isin(KMEANS_METHODS)].copy()
    kmeans = kmeans.sort_values(["dataset", "sample_percent", "sampling_method"])
    return pd.DataFrame(
        {
            "Dataset": kmeans["dataset"],
            "Sample (%)": kmeans["sample_percent"],
            "Variant": kmeans["sampling_method"].map(variant_label),
            "Mean-K MAPE (%)": kmeans["mean_mape_percent"].map(format_percent),
            "K-to-K Std (%)": kmeans["std_mape_percent"].map(format_percent),
            "Sample size": kmeans["sample_size"],
        }
    )


def build_repetition_counts(raw: pd.DataFrame) -> pd.DataFrame:
    raw = raw.copy()
    counts = (
        raw.groupby(["dataset", "sample_percent", "sampling_method", "k"], dropna=False)
        .size()
        .reset_index(name="repetitions")
        .sort_values(["dataset", "sample_percent", "sampling_method", "k"])
    )
    counts["method_label"] = counts.apply(method_label, axis=1)
    return counts[["dataset", "sample_percent", "method_label", "repetitions"]].rename(
        columns={
            "dataset": "Dataset",
            "sample_percent": "Sample (%)",
            "method_label": "Method",
            "repetitions": "Repetitions",
        }
    )


def plot_methods_by_dataset(summary: pd.DataFrame) -> None:
    for dataset, group in summary.groupby("dataset"):
        best_kmeans = best_kmeans_per_fraction(group)
        baselines = group[group["sampling_method"].isin(["random", "diversity"])]

        plt.figure(figsize=(8, 5))
        for label, method_group in baselines.groupby("method_label"):
            plt.plot(method_group["sample_percent"], method_group["mean_mape_percent"], marker="o", label=label)
        plt.plot(best_kmeans["sample_percent"], best_kmeans["mean_mape_percent"], marker="o", label="Best K-means")
        style_plot(f"{dataset}: MAPE by sample size", "Sample (%)", "MAPE (%)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / f"{dataset.lower()}_methods.png", dpi=180)
        plt.close()


def plot_kmeans_by_dataset(summary: pd.DataFrame) -> None:
    for dataset, group in summary[summary["sampling_method"].isin(KMEANS_METHODS)].groupby("dataset"):
        plt.figure(figsize=(8, 5))
        for method, method_group in group.groupby("sampling_method"):
            best_variant = method_group.loc[method_group.groupby("sample_percent")["mean_mape"].idxmin()]
            plt.plot(
                best_variant["sample_percent"],
                best_variant["mean_mape_percent"],
                marker="o",
                label=variant_label(method),
            )
        style_plot(f"{dataset}: best K by K-means variant", "Sample (%)", "MAPE (%)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / f"{dataset.lower()}_kmeans_k.png", dpi=180)
        plt.close()


def plot_best_kmeans_vs_baselines(summary: pd.DataFrame) -> None:
    rows = []
    for (dataset, sample_percent), group in summary.groupby(["dataset", "sample_percent"]):
        best_kmeans = group[group["sampling_method"].isin(KMEANS_METHODS)].sort_values("mean_mape").iloc[0]
        random = group[group["sampling_method"] == "random"].iloc[0]
        diversity = group[group["sampling_method"] == "diversity"].iloc[0]
        rows.extend(
            [
                {"dataset": dataset, "sample_percent": sample_percent, "method": "Best K-means", "mape": best_kmeans["mean_mape_percent"]},
                {"dataset": dataset, "sample_percent": sample_percent, "method": "Random", "mape": random["mean_mape_percent"]},
                {"dataset": dataset, "sample_percent": sample_percent, "method": "Diversity", "mape": diversity["mean_mape_percent"]},
            ]
        )
    plot_data = pd.DataFrame(rows)
    plt.figure(figsize=(10, 6))
    for label, method_group in plot_data.groupby("method"):
        aggregate = method_group.groupby("sample_percent")["mape"].mean().reset_index()
        plt.plot(aggregate["sample_percent"], aggregate["mape"], marker="o", label=label)
    style_plot("Average MAPE across datasets", "Sample (%)", "Mean MAPE (%)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "average_methods.png", dpi=180)
    plt.close()


def plot_mean_k_methods_by_dataset(summary: pd.DataFrame) -> None:
    mean_k_summary = collapse_kmeans_by_mean_k(summary)
    for dataset, group in mean_k_summary.groupby("dataset"):
        kmeans = group[group["sampling_method"].isin(KMEANS_METHODS)]
        baselines = group[group["sampling_method"].isin(["random", "diversity"])]

        plt.figure(figsize=(8, 5))
        for label, method_group in baselines.groupby("method_label"):
            plt.plot(method_group["sample_percent"], method_group["mean_mape_percent"], marker="o", label=label)
        for method, method_group in kmeans.groupby("sampling_method"):
            plt.plot(
                method_group["sample_percent"],
                method_group["mean_mape_percent"],
                marker="o",
                label=f"{variant_label(method)} (mean K)",
            )
        style_plot(f"{dataset}: MAPE by sample size (mean over K)", "Sample (%)", "MAPE (%)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / f"{dataset.lower()}_methods_mean_k.png", dpi=180)
        plt.close()


def plot_mean_k_vs_baselines(summary: pd.DataFrame) -> None:
    mean_k_summary = collapse_kmeans_by_mean_k(summary)
    rows = []
    for (dataset, sample_percent), group in mean_k_summary.groupby(["dataset", "sample_percent"]):
        best_kmeans = group[group["sampling_method"].isin(KMEANS_METHODS)].sort_values("mean_mape").iloc[0]
        random = group[group["sampling_method"] == "random"].iloc[0]
        diversity = group[group["sampling_method"] == "diversity"].iloc[0]
        rows.extend(
            [
                {"dataset": dataset, "sample_percent": sample_percent, "method": "Best mean-K K-means", "mape": best_kmeans["mean_mape_percent"]},
                {"dataset": dataset, "sample_percent": sample_percent, "method": "Random", "mape": random["mean_mape_percent"]},
                {"dataset": dataset, "sample_percent": sample_percent, "method": "Diversity", "mape": diversity["mean_mape_percent"]},
            ]
        )
    plot_data = pd.DataFrame(rows)
    plt.figure(figsize=(10, 6))
    for label, method_group in plot_data.groupby("method"):
        aggregate = method_group.groupby("sample_percent")["mape"].mean().reset_index()
        plt.plot(aggregate["sample_percent"], aggregate["mape"], marker="o", label=label)
    style_plot("Average MAPE across datasets (mean over K)", "Sample (%)", "Mean MAPE (%)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "average_methods_mean_k.png", dpi=180)
    plt.close()


def plot_k_frequency(summary: pd.DataFrame) -> None:
    best_k = best_kmeans_by_dataset_fraction(summary)
    frequency = best_k["k"].astype(int).value_counts().sort_index()

    plt.figure(figsize=(10, 5))
    plt.bar(frequency.index.astype(str), frequency.values)
    style_plot("Best K frequency", "K", "Best count")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "kmeans_best_k_frequency.png", dpi=180)
    plt.close()


def plot_k_frequency_by_dataset(summary: pd.DataFrame) -> None:
    best_k = best_kmeans_by_dataset_fraction(summary)
    datasets = sorted(best_k["dataset"].unique())

    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharey=True)
    axes_flat = axes.flatten()
    for axis, dataset in zip(axes_flat, datasets):
        dataset_frequency = best_k[best_k["dataset"] == dataset]["k"].astype(int).value_counts().sort_index()
        axis.bar(dataset_frequency.index.astype(str), dataset_frequency.values)
        axis.set_title(dataset)
        axis.set_xlabel("K")
        axis.set_ylabel("Best count")
        axis.grid(True, alpha=0.25)

    for axis in axes_flat[len(datasets) :]:
        axis.axis("off")

    fig.suptitle("Best K frequency by dataset")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "kmeans_best_k_frequency_by_dataset.png", dpi=180)
    plt.close(fig)


def plot_k_vs_mape_by_dataset(summary: pd.DataFrame) -> None:
    kmeans = summary[summary["sampling_method"].isin(KMEANS_METHODS)].copy()
    kmeans["k"] = kmeans["k"].astype(int)
    kmeans_by_k = (
        kmeans.groupby(["dataset", "sampling_method", "k"], as_index=False)
        .agg(mean_mape_percent=("mean_mape_percent", "mean"))
        .sort_values(["dataset", "sampling_method", "k"])
    )

    for dataset, group in kmeans_by_k.groupby("dataset"):
        plt.figure(figsize=(10, 5))
        for method, method_group in group.groupby("sampling_method"):
            plt.plot(method_group["k"], method_group["mean_mape_percent"], marker="o", markersize=3, label=variant_label(method))
        style_plot(f"{dataset}: K vs MAPE", "K", "Mean MAPE across sample sizes (%)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / f"{dataset.lower()}_k_vs_mape.png", dpi=180)
        plt.close()


def plot_k_delta_heatmap_by_dataset(summary: pd.DataFrame) -> None:
    kmeans = summary[summary["sampling_method"].isin(KMEANS_METHODS)].copy()
    kmeans["k"] = kmeans["k"].astype(int)
    best_in_row = kmeans.groupby(["dataset", "sampling_method", "sample_percent"])["mean_mape_percent"].transform("min")
    kmeans["delta_to_best_k_percent"] = ((kmeans["mean_mape_percent"] - best_in_row) / best_in_row) * 100.0

    for dataset, group in kmeans.groupby("dataset"):
        methods = [method for method in KMEANS_METHODS if method in set(group["sampling_method"])]
        fig, axes = plt.subplots(
            1,
            len(methods),
            figsize=(6.5 * len(methods), 5.2),
            sharey=True,
            constrained_layout=True,
        )
        if len(methods) == 1:
            axes = [axes]

        capped_vmax = max(1.0, group["delta_to_best_k_percent"].quantile(0.95))
        colorbar_label = "Worse than best K in same sample (%)"
        if group["delta_to_best_k_percent"].max() > capped_vmax:
            colorbar_label += "\n(capped at 95th percentile)"
        cmap = plt.colormaps["RdYlGn_r"].copy()
        cmap.set_bad(color="#eeeeee")
        image = None

        for axis, method in zip(axes, methods):
            method_group = group[group["sampling_method"] == method]
            pivot = (
                method_group.pivot(index="sample_percent", columns="k", values="delta_to_best_k_percent")
                .sort_index()
                .sort_index(axis=1)
            )
            plot_values = np.ma.masked_invalid(pivot.clip(upper=capped_vmax).to_numpy(dtype=float))
            image = axis.imshow(plot_values, aspect="auto", cmap=cmap, vmin=0.0, vmax=capped_vmax)

            k_values = list(pivot.columns)
            shown_k_positions = [index for index, value in enumerate(k_values) if value == 5 or value % 5 == 0]
            axis.set_xticks(shown_k_positions)
            axis.set_xticklabels([str(k_values[index]) for index in shown_k_positions], rotation=45)

            sample_sizes = method_group.drop_duplicates("sample_percent").set_index("sample_percent")["sample_size"]
            sample_labels = [f"{sample}%\n(n={int(sample_sizes.loc[sample])})" for sample in pivot.index]
            axis.set_yticks(range(len(pivot.index)))
            axis.set_yticklabels(sample_labels)
            axis.set_title(variant_label(method))
            axis.set_xlabel("K")
            axis.set_ylabel("Sample")

        if image is not None:
            fig.colorbar(image, ax=list(axes), label=colorbar_label)
        fig.suptitle(f"{dataset}: K sensitivity controlling for sample size")
        fig.savefig(PLOTS_DIR / f"{dataset.lower()}_k_delta_heatmap.png", dpi=180)
        plt.close(fig)


def best_kmeans_per_fraction(group: pd.DataFrame) -> pd.DataFrame:
    kmeans = group[group["sampling_method"].isin(KMEANS_METHODS)]
    return kmeans.loc[kmeans.groupby("sample_percent")["mean_mape"].idxmin()].sort_values("sample_percent")


def best_kmeans_by_dataset_fraction(summary: pd.DataFrame) -> pd.DataFrame:
    kmeans = summary[summary["sampling_method"].isin(KMEANS_METHODS)].copy()
    return kmeans.loc[kmeans.groupby(["dataset", "sample_percent"])["mean_mape"].idxmin()].copy()


def collapse_kmeans_by_mean_k(summary: pd.DataFrame) -> pd.DataFrame:
    baselines = summary[summary["sampling_method"].isin(["random", "diversity"])].copy()
    kmeans = summary[summary["sampling_method"].isin(KMEANS_METHODS)].copy()
    grouped = (
        kmeans.groupby(["dataset", "sampling_method", "sample_fraction", "sample_percent", "sample_size"], as_index=False)
        .agg(
            mean_mape=("mean_mape", "mean"),
            std_mape=("mean_mape", "std"),
            mean_mape_percent=("mean_mape_percent", "mean"),
            std_mape_percent=("mean_mape_percent", "std"),
        )
        .fillna({"std_mape": 0.0, "std_mape_percent": 0.0})
    )
    grouped["k"] = ""
    grouped["method_label"] = grouped["sampling_method"].map(lambda method: f"{variant_label(method)} (mean K)")
    return pd.concat([baselines, grouped[baselines.columns]], ignore_index=True).sort_values(
        ["dataset", "sample_percent", "sampling_method"]
    )


def style_plot(title: str, xlabel: str, ylabel: str) -> None:
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.25)


def write_table(table: pd.DataFrame, name: str) -> None:
    table.to_csv(TABLES_DIR / f"{name}.csv", index=False)
    (TABLES_DIR / f"{name}.md").write_text(to_markdown(table), encoding="utf-8")


def write_paper_table_images() -> None:
    for name in PAPER_TABLE_IMAGE_NAMES:
        path = TABLES_DIR / f"{name}.csv"
        if not path.exists():
            continue
        table = pd.read_csv(path, keep_default_na=False)
        write_table_image(table, name)


def write_table_image(table: pd.DataFrame, name: str) -> None:
    write_table_image_variant(table, name)
    if name == "methods_summary":
        write_table_image_variant(table, "methods_summary_large", font_size=20, figure_width=13.5, figure_height=7.0)
    if name == "best_by_dataset_fraction_mape":
        write_best_fraction_mape_wide_image(table)


def write_table_image_variant(
    table: pd.DataFrame,
    name: str,
    font_size: float | None = None,
    line_height: float | None = None,
    figure_width: float | None = None,
    figure_height: float | None = None,
) -> None:
    wrapped = wrap_table_cells(table, large=name == "methods_summary_large")
    mape_colors: dict[tuple[int, int], tuple[float, float, float, float]] = {}
    line_counts = [max(str(value).count("\n") + 1 for value in row) for row in wrapped.to_numpy()]
    total_lines = sum(line_counts) + 1
    font_size = font_size or (14 if name == "methods_summary" else 8.5)
    line_height = line_height or (0.62 if name == "methods_summary" else 0.34)
    figure_width = figure_width or (
        12.5 if name == "methods_summary" else min(16.0, max(6.5, 1.8 * len(wrapped.columns) + 1.5))
    )
    figure_height = figure_height or min(24.0, max(3.2, line_height * total_lines + 1.0))

    fig, axis = plt.subplots(figsize=(figure_width, figure_height))
    axis.axis("off")
    table_artist = axis.table(
        cellText=wrapped.to_numpy(),
        colLabels=list(wrapped.columns),
        loc="center",
        cellLoc="left",
        colLoc="left",
        colWidths=table_column_widths(wrapped),
    )
    table_artist.auto_set_font_size(False)
    table_artist.set_fontsize(font_size)

    base_height = 1.0 / (sum(line_counts) + 1.8)
    for (row, column), cell in table_artist.get_celld().items():
        cell.set_edgecolor("#b8b8b8")
        cell.set_linewidth(0.6)
        cell.PAD = 0.04
        if row == 0:
            cell.set_facecolor("#e9ecef")
            cell.set_text_props(weight="bold", color="#111111")
            cell.set_height(base_height * 1.35)
        else:
            cell_color = mape_colors.get((row - 1, column))
            cell.set_facecolor(cell_color or ("#ffffff" if row % 2 else "#f8f9fa"))
            cell.set_height(base_height * line_counts[row - 1] * 1.25)
        if column >= 0 and is_numeric_column(str(wrapped.columns[column])):
            cell.set_text_props(ha="center")

    fig.tight_layout(pad=0.4)
    fig.savefig(TABLE_IMAGES_DIR / f"{name}.png", dpi=220, bbox_inches="tight")
    fig.savefig(TABLE_IMAGES_DIR / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def write_best_fraction_mape_wide_image(table: pd.DataFrame) -> None:
    datasets = list(table["Dataset"].drop_duplicates())
    midpoint = (len(datasets) + 1) // 2
    groups = [datasets[:midpoint], datasets[midpoint:]]

    fig, axes = plt.subplots(1, 2, figsize=(15.5, 7.0))
    for axis, dataset_group in zip(axes, groups):
        axis.axis("off")
        group_table = table[table["Dataset"].isin(dataset_group)].copy()
        wrapped = wrap_table_cells(group_table)
        line_counts = [max(str(value).count("\n") + 1 for value in row) for row in wrapped.to_numpy()]
        table_artist = axis.table(
            cellText=wrapped.to_numpy(),
            colLabels=list(wrapped.columns),
            loc="center",
            cellLoc="left",
            colLoc="left",
            colWidths=table_column_widths(wrapped),
        )
        table_artist.auto_set_font_size(False)
        table_artist.set_fontsize(10.5)

        base_height = 1.0 / (sum(line_counts) + 1.8)
        for (row, column), cell in table_artist.get_celld().items():
            cell.set_edgecolor("#b8b8b8")
            cell.set_linewidth(0.6)
            cell.PAD = 0.04
            if row == 0:
                cell.set_facecolor("#e9ecef")
                cell.set_text_props(weight="bold", color="#111111")
                cell.set_height(base_height * 1.4)
            else:
                cell.set_facecolor("#ffffff" if row % 2 else "#f8f9fa")
                cell.set_height(base_height * line_counts[row - 1] * 1.22)
            if column >= 0 and is_numeric_column(str(wrapped.columns[column])):
                cell.set_text_props(ha="center")

    fig.tight_layout(pad=0.5, w_pad=1.0)
    fig.savefig(TABLE_IMAGES_DIR / "best_by_dataset_fraction_mape_wide.png", dpi=220, bbox_inches="tight")
    fig.savefig(TABLE_IMAGES_DIR / "best_by_dataset_fraction_mape_wide.pdf", bbox_inches="tight")
    plt.close(fig)


def wrap_table_cells(table: pd.DataFrame, large: bool = False) -> pd.DataFrame:
    wrapped = table.copy()
    for column in wrapped.columns:
        width = wrap_width_for_column(str(column), len(wrapped.columns), large=large)
        wrapped[column] = wrapped[column].map(lambda value: wrap_cell(value, width))
    return wrapped


def wrap_cell(value: object, width: int) -> str:
    text = str(value)
    if len(text) <= width:
        return text
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False))


def wrap_width_for_column(column: str, column_count: int, large: bool = False) -> int:
    if large and column == "Summary":
        return 62
    custom_widths = {
        "Summary": 42,
        "Best K-means": 28,
        "Best mean-K K-means": 28,
        "Best method": 26,
        "Best overall": 26,
        "Variant": 22,
        "Method": 22,
    }
    if column in custom_widths:
        return custom_widths[column]
    return max(12, min(24, int(90 / max(1, column_count))))


def table_column_widths(table: pd.DataFrame) -> list[float]:
    weights = []
    for column in table.columns:
        column = str(column)
        if column == "Summary":
            weights.append(3.2)
        elif column in {"Best K-means", "Best mean-K K-means", "Best method", "Best overall"}:
            weights.append(2.1)
        elif column in {"Method", "Variant"}:
            weights.append(1.4)
        elif is_numeric_column(column):
            weights.append(0.95)
        else:
            weights.append(1.2)
    total = sum(weights)
    return [weight / total for weight in weights]


def mape_color_by_dataset(table: pd.DataFrame) -> dict[tuple[int, int], tuple[float, float, float, float]]:
    if "Dataset" not in table.columns or "MAPE" not in table.columns:
        return {}

    mape_column = list(table.columns).index("MAPE")
    colors = {}
    cmap = plt.colormaps["RdYlGn_r"]
    numeric_mape = pd.to_numeric(table["MAPE"], errors="coerce")

    for dataset, indices in table.groupby("Dataset").groups.items():
        values = numeric_mape.loc[indices]
        minimum = values.min()
        maximum = values.max()
        for index in indices:
            value = numeric_mape.loc[index]
            if pd.isna(value):
                continue
            normalized = 0.0 if maximum == minimum else (value - minimum) / (maximum - minimum)
            colors[(int(index), mape_column)] = cmap(0.15 + normalized * 0.7)
    return colors


def is_numeric_column(column: str) -> bool:
    numeric_terms = ("%", "K", "size", "count", "Std", "MAPE", "Sample")
    return any(term in column for term in numeric_terms)


def clear_table_outputs() -> None:
    for pattern in ("*.csv", "*.md"):
        for path in TABLES_DIR.glob(pattern):
            path.unlink()


def clear_table_image_outputs() -> None:
    for pattern in ("*.png", "*.pdf"):
        for path in TABLE_IMAGES_DIR.glob(pattern):
            path.unlink()


def clear_plot_outputs() -> None:
    for path in PLOTS_DIR.glob("*.png"):
        path.unlink()


def format_percent(value: float) -> str:
    return f"{value:.2f}"


def to_markdown(table: pd.DataFrame) -> str:
    columns = [str(column) for column in table.columns]
    rows = [[str(value) for value in row] for row in table.to_numpy()]
    widths = [
        max(len(column), *(len(row[index]) for row in rows)) if rows else len(column)
        for index, column in enumerate(columns)
    ]

    header = "| " + " | ".join(column.ljust(widths[index]) for index, column in enumerate(columns)) + " |"
    separator = "| " + " | ".join("-" * widths[index] for index in range(len(columns))) + " |"
    body = [
        "| " + " | ".join(value.ljust(widths[index]) for index, value in enumerate(row)) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body]) + "\n"
