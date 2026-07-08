from __future__ import annotations

import argparse
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_percentage_error

from experiments.sampling import diversity_sampling, hamming_distance_matrix, kmeans_sampling_orders, random_sampling


DATASETS = {
    "Apache": Path("AutoML-SPL-Datasets/Apachemeasuresoutput.csv"),
    "BDBC": Path("AutoML-SPL-Datasets/BDBCmeasuresoutput.csv"),
    "BDBJ": Path("AutoML-SPL-Datasets/BDBJmeasuresoutput.csv"),
    "LLVM": Path("AutoML-SPL-Datasets/LLVMmeasuresoutput.csv"),
}
K_VALUES = tuple(range(5, 51))
SAMPLE_FRACTIONS = tuple(value / 100 for value in range(10, 101, 10))
REPETITIONS = 30
TARGET_COLUMN = "Measured_Value"
RESULTS_DIR = Path("results")
PROGRESS_STEP = 2500


@dataclass(frozen=True)
class Dataset:
    name: str
    features: np.ndarray
    target: np.ndarray


def main() -> None:
    args = parse_args()
    RESULTS_DIR.mkdir(exist_ok=True)
    raw_rows: list[dict[str, object]] = []
    datasets = load_datasets()
    total_evaluations = estimate_total_evaluations(datasets)
    completed_evaluations = 0

    def record(row: dict[str, object]) -> None:
        nonlocal completed_evaluations
        raw_rows.append(row)
        completed_evaluations += 1
        if completed_evaluations % PROGRESS_STEP == 0 or completed_evaluations == total_evaluations:
            percent = (completed_evaluations / total_evaluations) * 100
            print(
                f"    progress: {completed_evaluations}/{total_evaluations} evaluations ({percent:.1f}%)",
                flush=True,
            )

    print(f"K values: {K_VALUES[0]}..{K_VALUES[-1]} ({len(K_VALUES)} values)", flush=True)
    print(f"Sample fractions: {len(SAMPLE_FRACTIONS)}", flush=True)
    print(f"Repetitions: {REPETITIONS}", flush=True)
    print(f"Jobs: {args.jobs}", flush=True)
    print(f"Planned evaluations: {total_evaluations}", flush=True)
    if args.jobs > 1:
        print(
            "Tip: for parallel runs, use OMP_NUM_THREADS=1 to avoid CPU oversubscription.",
            flush=True,
        )

    for dataset_index, dataset in enumerate(datasets, start=1):
        print(
            f"Running dataset {dataset_index}/{len(datasets)}: "
            f"{dataset.name} ({len(dataset.target)} variants, {dataset.features.shape[1]} features)",
            flush=True,
        )
        distance_matrix = hamming_distance_matrix(dataset.features)
        for fraction_index, sample_fraction in enumerate(SAMPLE_FRACTIONS, start=1):
            sample_size = fraction_to_sample_size(len(dataset.target), sample_fraction)
            valid_ks = valid_k_values(sample_size)
            print(
                f"  fraction {fraction_index}/{len(SAMPLE_FRACTIONS)}: "
                f"{sample_fraction:.0%} ({sample_size} variants, {len(valid_ks)} K values)",
                flush=True,
            )
            record(
                evaluate(
                    dataset,
                    "diversity",
                    diversity_sampling(dataset.features, sample_size),
                    k=None,
                    repetition=0,
                    sample_fraction=sample_fraction,
                )
            )

        if args.jobs == 1:
            for seed in range(1, REPETITIONS + 1):
                print_repetition_progress(seed)
                for row in run_repetition(dataset, distance_matrix, seed):
                    record(row)
        else:
            completed_repetitions = 0
            with ProcessPoolExecutor(max_workers=args.jobs) as executor:
                futures = [
                    executor.submit(run_repetition, dataset, distance_matrix, seed)
                    for seed in range(1, REPETITIONS + 1)
                ]
                for future in as_completed(futures):
                    for row in future.result():
                        record(row)
                    completed_repetitions += 1
                    print(
                        f"    completed repetitions: {completed_repetitions}/{REPETITIONS}",
                        flush=True,
                    )

    raw_results = pd.DataFrame(raw_rows)
    summary = summarize(raw_results)

    raw_results.to_csv(RESULTS_DIR / "raw_results.csv", index=False)
    summary.to_csv(RESULTS_DIR / "summary_results.csv", index=False)
    print(f"Saved {RESULTS_DIR / 'raw_results.csv'}")
    print(f"Saved {RESULTS_DIR / 'summary_results.csv'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SPL sampling experiments.")
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Number of parallel worker processes. Use 1 for sequential execution.",
    )
    args = parser.parse_args()
    max_jobs = max(1, os.cpu_count() or 1)
    args.jobs = max(1, min(args.jobs, max_jobs))
    return args


def print_repetition_progress(seed: int) -> None:
    if seed == 1 or seed % 5 == 0 or seed == REPETITIONS:
        print(f"    repetition {seed}/{REPETITIONS}", flush=True)


def run_repetition(dataset: Dataset, distance_matrix: np.ndarray, seed: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rng = np.random.default_rng(seed)
    kmeans_cache: dict[int, dict[str, list[int]]] = {}

    for sample_fraction in SAMPLE_FRACTIONS:
        sample_size = fraction_to_sample_size(len(dataset.target), sample_fraction)
        random_indices = random_sampling(dataset.features, sample_size, rng)
        rows.append(evaluate(dataset, "random", random_indices, k=None, repetition=seed, sample_fraction=sample_fraction))

        for k in valid_k_values(sample_size):
            if k not in kmeans_cache:
                kmeans_cache[k] = kmeans_sampling_orders(
                    dataset.features,
                    k,
                    seed,
                    distance_matrix=distance_matrix,
                )
            for method, kmeans_order in kmeans_cache[k].items():
                rows.append(
                    evaluate(
                        dataset,
                        method,
                        kmeans_order[:sample_size],
                        k=k,
                        repetition=seed,
                        sample_fraction=sample_fraction,
                    )
                )

    return rows


def load_datasets() -> list[Dataset]:
    datasets: list[Dataset] = []
    for name, path in DATASETS.items():
        frame = pd.read_csv(path)
        if TARGET_COLUMN not in frame.columns:
            raise ValueError(f"{path} does not contain {TARGET_COLUMN}")
        if (frame[TARGET_COLUMN] <= 0).any():
            raise ValueError(f"{path} contains non-positive target values, which breaks MAPE")

        features = frame.drop(columns=[TARGET_COLUMN]).to_numpy(dtype=int)
        target = frame[TARGET_COLUMN].to_numpy(dtype=float)
        datasets.append(Dataset(name=name, features=features, target=target))
    return datasets


def evaluate(
    dataset: Dataset,
    method: str,
    selected_indices: list[int],
    k: int | None,
    repetition: int,
    sample_fraction: float,
) -> dict[str, object]:
    selected = np.array(selected_indices, dtype=int)
    validate_selection(dataset, selected)

    train_mask = np.zeros(len(dataset.target), dtype=bool)
    train_mask[selected] = True
    test_mask = ~train_mask

    model = LinearRegression()
    model.fit(dataset.features[train_mask], dataset.target[train_mask])
    predictions = model.predict(dataset.features[test_mask])
    mape = mean_absolute_percentage_error(dataset.target[test_mask], predictions)

    return {
        "dataset": dataset.name,
        "sampling_method": method,
        "k": "" if k is None else k,
        "sample_fraction": sample_fraction,
        "repetition": repetition,
        "sample_size": len(selected),
        "mape": mape,
    }


def validate_selection(dataset: Dataset, selected: np.ndarray) -> None:
    if selected.ndim != 1:
        raise ValueError("selected indices must be one-dimensional")
    if len(selected) == 0:
        raise ValueError("sampling returned an empty selection")
    if len(np.unique(selected)) != len(selected):
        raise ValueError(f"{dataset.name}: sampling returned duplicate variants")
    if selected.min() < 0 or selected.max() >= len(dataset.target):
        raise ValueError(f"{dataset.name}: sampling returned out-of-range variants")
    if len(selected) >= len(dataset.target):
        raise ValueError(f"{dataset.name}: sampling selected all variants, leaving no test set")


def fraction_to_sample_size(dataset_size: int, sample_fraction: float) -> int:
    sample_size = int(round(dataset_size * sample_fraction))
    return max(2, min(sample_size, dataset_size - 1))


def valid_k_values(sample_size: int) -> tuple[int, ...]:
    return tuple(k for k in K_VALUES if k <= sample_size)


def estimate_total_evaluations(datasets: list[Dataset]) -> int:
    total = 0
    for dataset in datasets:
        for sample_fraction in SAMPLE_FRACTIONS:
            sample_size = fraction_to_sample_size(len(dataset.target), sample_fraction)
            total += 1
            total += REPETITIONS
            total += REPETITIONS * len(valid_k_values(sample_size)) * 3
    return total


def summarize(raw_results: pd.DataFrame) -> pd.DataFrame:
    summary = (
        raw_results.groupby(["dataset", "sampling_method", "k", "sample_fraction", "sample_size"], dropna=False)["mape"]
        .agg(mean_mape="mean", std_mape="std")
        .reset_index()
        .sort_values(["dataset", "sample_fraction", "sampling_method", "k"])
    )
    summary["std_mape"] = summary["std_mape"].fillna(0.0)
    return summary
