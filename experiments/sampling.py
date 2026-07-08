from __future__ import annotations

from itertools import combinations

import numpy as np
from sklearn.cluster import KMeans


def twise_sampling(features: np.ndarray, strength: int) -> list[int]:
    """Greedily select real variants until all observed t-wise feature-value tuples are covered."""
    uncovered = _observed_tuples(features, strength)
    selected: list[int] = []
    remaining = set(range(features.shape[0]))

    while uncovered and remaining:
        best_index = max(
            remaining,
            key=lambda index: (len(_covered_tuples(features[index], strength) & uncovered), -index),
        )
        newly_covered = _covered_tuples(features[best_index], strength) & uncovered
        if not newly_covered:
            break

        selected.append(best_index)
        remaining.remove(best_index)
        uncovered -= newly_covered

    return selected


def pairwise_sampling(features: np.ndarray) -> list[int]:
    return twise_sampling(features, strength=2)


def threewise_sampling(features: np.ndarray) -> list[int]:
    return twise_sampling(features, strength=3)


def random_sampling(features: np.ndarray, sample_size: int, rng: np.random.Generator) -> list[int]:
    return rng.choice(features.shape[0], size=sample_size, replace=False).tolist()


def diversity_sampling(features: np.ndarray, sample_size: int) -> list[int]:
    """Farthest-first traversal using Hamming distance over binary feature vectors."""
    n_variants = features.shape[0]
    selected = [0]
    remaining = np.ones(n_variants, dtype=bool)
    remaining[0] = False
    min_distances = _hamming_distances(features, features[0])

    while len(selected) < sample_size:
        candidates = np.flatnonzero(remaining)
        next_index = int(candidates[np.argmax(min_distances[candidates])])
        selected.append(next_index)
        remaining[next_index] = False
        min_distances = np.minimum(min_distances, _hamming_distances(features, features[next_index]))

    return selected


def hamming_distance_matrix(features: np.ndarray) -> np.ndarray:
    return np.mean(features[:, None, :] != features[None, :, :], axis=2, dtype=np.float32)


def kmeans_sampling_orders(
    features: np.ndarray,
    k: int,
    seed: int,
    distance_matrix: np.ndarray | None = None,
) -> dict[str, list[int]]:
    """Create complete K-means sampling orders using different intra-cluster strategies."""
    effective_k = min(k, features.shape[0])
    # Matches the paper's Weka Simple K-means setup: standard K-means with Euclidean distance.
    kmeans = KMeans(n_clusters=effective_k, random_state=seed, n_init=10)
    labels = kmeans.fit_predict(features)
    rng = np.random.default_rng(seed)
    if distance_matrix is None:
        distance_matrix = hamming_distance_matrix(features)

    default_clusters: list[list[int]] = []
    hamming_clusters: list[list[int]] = []
    random_clusters: list[list[int]] = []
    for cluster_id in range(effective_k):
        members = np.flatnonzero(labels == cluster_id).tolist()
        if members:
            default_clusters.append(members.copy())
            hamming_clusters.append(_hamming_prioritized_order(features, distance_matrix, members, rng))
            random_members = members.copy()
            rng.shuffle(random_members)
            random_clusters.append(random_members)

    rng.shuffle(random_clusters)
    return {
        "kmeans_default": _round_robin(default_clusters, features.shape[0]),
        "kmeans_hamming": _round_robin(hamming_clusters, features.shape[0]),
        "kmeans_random": _round_robin(random_clusters, features.shape[0]),
    }


def kmeans_sampling_variants(features: np.ndarray, sample_size: int, k: int, seed: int) -> dict[str, list[int]]:
    """Sample with K-means clusters using different intra-cluster ordering strategies."""
    orders = kmeans_sampling_orders(features, k, seed)
    return {method: order[:sample_size] for method, order in orders.items()}


def kmeans_sampling(features: np.ndarray, sample_size: int, k: int, seed: int) -> list[int]:
    return kmeans_sampling_variants(features, sample_size, k, seed)["kmeans_random"]


def _round_robin(clusters: list[list[int]], sample_size: int) -> list[int]:
    clusters = [cluster.copy() for cluster in clusters if cluster]
    selected: list[int] = []
    cursor = 0
    while len(selected) < sample_size and clusters:
        cluster = clusters[cursor % len(clusters)]
        if cluster:
            selected.append(cluster.pop(0))
        clusters = [cluster for cluster in clusters if cluster]
        cursor += 1
    return selected


def _hamming_prioritized_order(
    features: np.ndarray,
    distance_matrix: np.ndarray,
    members: list[int],
    rng: np.random.Generator,
) -> list[int]:
    """Order cluster members using the paper's similarity-based Hamming prioritization idea."""
    if len(members) <= 1:
        return members.copy()

    member_array = np.array(members, dtype=int)
    feature_counts = features[member_array].sum(axis=1)
    max_count = feature_counts.max()
    first_candidates = member_array[np.flatnonzero(feature_counts == max_count)]
    first = int(rng.choice(first_candidates))

    selected = [first]
    remaining = np.array([member for member in members if member != first], dtype=int)
    min_distances = distance_matrix[remaining, first]

    while len(remaining) > 0:
        max_distance = min_distances.max()
        candidate_positions = np.flatnonzero(min_distances == max_distance)
        position = int(rng.choice(candidate_positions))
        next_member = int(remaining[position])
        selected.append(next_member)

        keep_mask = np.ones(len(remaining), dtype=bool)
        keep_mask[position] = False
        remaining = remaining[keep_mask]
        min_distances = min_distances[keep_mask]
        if len(remaining) > 0:
            min_distances = np.minimum(min_distances, distance_matrix[remaining, next_member])

    return selected


def _observed_tuples(features: np.ndarray, strength: int) -> set[tuple[tuple[int, int], ...]]:
    observed: set[tuple[tuple[int, int], ...]] = set()
    for row in features:
        observed |= _covered_tuples(row, strength)
    return observed


def _covered_tuples(row: np.ndarray, strength: int) -> set[tuple[tuple[int, int], ...]]:
    return {
        tuple((feature, int(row[feature])) for feature in feature_group)
        for feature_group in combinations(range(row.shape[0]), strength)
    }


def _hamming_distances(features: np.ndarray, variant: np.ndarray) -> np.ndarray:
    return np.mean(features != variant, axis=1)
