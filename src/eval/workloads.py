# src/eval/workloads.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

import random

@dataclass(frozen=True)
class WorkloadSpec:
	name: str
	num_queries: int
	seed: int = 0

	# For zipf/hot-set
	hot_fraction: float = 0.10   # top 10%
	hot_mass: float = 0.85       # 85% of picks from hot set (zipf-like)
	working_set_fraction: float = 0.01  # 1% working set for hot-set

# Simple weighted sampling without replacement (O(k*n))
def _weighted_sample_without_replacement(
	items: Sequence[Any],
	weights: Sequence[float],
	k: int,
	rng: random.Random,
) -> List[Any]:
	items = list(items)
	weights = list(weights)
	chosen: List[Any] = []
	for _ in range(min(k, len(items))):
		total = sum(weights)
		if total <= 0:
			break
		r = rng.random() * total
		acc = 0.0
		idx = 0
		for i, w in enumerate(weights):
			acc += w
			if acc >= r:
				idx = i
				break
		chosen.append(items.pop(idx))
		weights.pop(idx)
	return chosen

def make_uniform_distinct(values: List[Any], spec: WorkloadSpec) -> List[Any]:
	rng = random.Random(spec.seed)
	vals = values[:]
	rng.shuffle(vals)
	return vals[: spec.num_queries]

# Choose fraction of queries from hot set using weights ~ counts, rest from cold set using weights ~ counts
def make_zipf_like_distinct(values: List[Any], value_counts: Dict[Any, int], spec: WorkloadSpec) -> List[Any]:
	rng = random.Random(spec.seed)
	
	# sort values by popularity
	sorted_vals = sorted(values, key=lambda v: value_counts.get(v, 0), reverse=True)
	hot_k = max(1, int(len(sorted_vals) * spec.hot_fraction))
	hot = sorted_vals[:hot_k]
	cold = sorted_vals[hot_k:]

	q_hot = int(spec.num_queries * spec.hot_mass)
	q_cold = spec.num_queries - q_hot

	# weights based on counts (more popular => more likely earlier)
	hot_w = [float(value_counts.get(v, 1)) for v in hot]
	cold_w = [float(value_counts.get(v, 1)) for v in cold] if cold else []

	chosen_hot = _weighted_sample_without_replacement(hot, hot_w, q_hot, rng)
	chosen_cold = _weighted_sample_without_replacement(cold, cold_w, q_cold, rng) if cold else []

	# Mix them to represent an “interleaved” workload
	combined = chosen_hot + chosen_cold
	rng.shuffle(combined)
	return combined[: spec.num_queries]

# Only query within a small fixed subset (hot set), picked as the top fraction by popularity
def make_hot_set_distinct(values: List[Any], value_counts: Dict[Any, int], spec: WorkloadSpec) -> List[Any]:
	rng = random.Random(spec.seed)
	
	sorted_vals = sorted(values, key=lambda v: value_counts.get(v, 0), reverse=True)
	ws_k = max(1, int(len(sorted_vals) * spec.working_set_fraction))
	working_set = sorted_vals[:ws_k]

	# if user asks for more distinct queries than working set size, clamp
	num = min(spec.num_queries, len(working_set))
	ws_w = [float(value_counts.get(v, 1)) for v in working_set]
	chosen = _weighted_sample_without_replacement(working_set, ws_w, num, rng)
	return chosen
