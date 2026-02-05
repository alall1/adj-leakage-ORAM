# src/eval/phase3_runner.pyfrom __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.seal.seal_client import SealClient
from src.workload.leakage_oracle import SealLeakageOracle
from src.attacks.query_recovery import query_recovery_attack
from src.attacks.database_recovery import database_recovery_attack
from src.eval.checkpoints import CheckpointSpec, DEFAULT_CHECKPOINTS

@dataclass(frozen=True)
class RunConfig:
	n: int
	Z: int
	alphas: List[int]
	padding_x: Optional[int] = None
	rng_seed: int = 0
	checkpoints: CheckpointSpec = DEFAULT_CHECKPOINTS

@dataclass(frozen=True)
class TimeSeriesResult:
	# keyed by alpha -> list of (t, qrsr, drsr)
	series: Dict[int, List[Tuple[int, float, float]]]

# For each alpha: build SEAL client, build leakage oracle, generate leakage stream for query_values_in_order, and at each checkpoint t run attacks on prefix observations[:t]
def evaluate_over_time(
	dataset_index: Dict[Any, Any],
	value_counts: Dict[Any, int],
	query_values_in_order: List[Any],
	cfg: RunConfig,
) -> TimeSeriesResult:
	series: Dict[int, List[Tuple[int, float, float]]] = {}

	# We want *distinct* query values for paper attacks
	# If caller accidentally includes repeats, we de-dup in order.
	seen = set()
	distinct_in_order = []
	for v in query_values_in_order:
		if v not in seen:
			seen.add(v)
			distinct_in_order.append(v)

	for alpha in cfg.alphas:
		seal = SealClient(n=cfg.n, Z=cfg.Z, alpha=alpha, default_value=0)
		oracle = SealLeakageOracle(seal=seal, dataset_index=dataset_index, padding_x=cfg.padding_x, rng_seed=cfg.rng_seed)

		# Precompute encrypted tuples once per alpha (used in DRSR)
		encT = oracle.build_encrypted_tuples()

		# Build the stream of leakage observations for this workload
		observations = oracle.observe_query_stream(distinct_in_order)

		out: List[Tuple[int, float, float]] = []
		for t in cfg.checkpoints.points:
			t_eff = min(t, len(observations))
			if t_eff <= 0:
				continue

			prefix_obs = observations[:t_eff]
			qrsr = query_recovery_attack(value_counts, prefix_obs, x=cfg.padding_x, rng_seed=cfg.rng_seed)
			drsr = database_recovery_attack(value_counts, encT, prefix_obs, x=cfg.padding_x, rng_seed=cfg.rng_seed)

			out.append((t_eff, qrsr, drsr))

		series[alpha] = out
	return TimeSeriesResult(series=series)
