# src/eval/sessions.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import random

from src.eval.workloads import (
	WorkloadSpec,
	make_uniform_distinct,
	make_zipf_like_distinct,
	make_hot_set_distinct,
)

@dataclass(frozen=True)
class SessionPlan:
	num_sessions: int
	session_length: int
	pattern: str             # "uniform" | "zipf_like" | "hot_set"
	seed: int = 0

	# pattern params
	hot_fraction: float = 0.10
	hot_mass: float = 0.90
	working_set_fraction: float = 0.01

# Returns a list of sessions, each a list of distinct query-values, sampled independently with reproducible seeds
def sample_sessions(
	all_values: List[Any],
	value_counts: Dict[Any, int],
	plan: SessionPlan,
) -> List[List[Any]]:
	sessions: List[List[Any]] = []
	for s in range(plan.num_sessions):
		spec = WorkloadSpec(
			name=plan.pattern,
			num_queries=plan.session_length,
			seed=plan.seed + s,
			hot_fraction=plan.hot_fraction,
			hot_mass=plan.hot_mass,
			working_set_fraction=plan.working_set_fraction,
		)

		if plan.pattern == "uniform":
			qvals = make_uniform_distinct(all_values, spec)
		elif plan.pattern == "zipf_like":
			qvals = make_zipf_like_distinct(all_values, value_counts, spec)
		elif plan.pattern == "hot_set":
			qvals = make_hot_set_distinct(all_values, value_counts, spec)
		else:
			raise ValueError("unknown pattern")

		sessions.append(qvals)

	return sessions
