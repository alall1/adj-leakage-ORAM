# src/eval/padding_eval.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.seal.seal_client import SealClient
from src.workload.leakage_oracle import SealLeakageOracle
from src.attacks.query_recovery import query_recovery_attack
from src.attacks.database_recovery import database_recovery_attack

@dataclass(frozen=True)
class PaddingEvalRow:
	alpha: int
	x: Optional[int]          # None = no padding
	num_queries: int
	qrsr: float
	drsr: float
	avg_real_vol: float
	avg_padded_vol: float
	overhead_factor: float    # avg_padded / avg_real

def _safe_mean(vals: List[int]) -> float:
	return float(np.mean(vals)) if vals else 0.0

# Runs attacks for each (alpha, x) and computes padding overhead
def evaluate_padding_sweep(
	dataset_index: Dict[Any, np.ndarray],
	value_counts: Dict[Any, int],
	query_values_in_order: List[Any],
	n: int,
	Z: int,
	alphas: List[int],
	xs: List[Optional[int]],
	rng_seed: int = 0,
) -> List[PaddingEvalRow]:
	rows: List[PaddingEvalRow] = []

	# Ensure distinct queries in order 
	seen = set()
	distinct_q = []
	for v in query_values_in_order:
		if v not in seen:
			seen.add(v)
			distinct_q.append(v)

	# Real volumes are determined by dataset_index (independent of alpha/x)
	real_vols = [int(len(dataset_index[v])) for v in distinct_q]
	avg_real = _safe_mean(real_vols)

	for x in xs:
		for alpha in alphas:
			seal = SealClient(n=n, Z=Z, alpha=alpha, default_value=0)
			oracle = SealLeakageOracle(
				seal=seal,
				dataset_index=dataset_index,
				padding_x=x,
				rng_seed=rng_seed,
			)

			obs = oracle.observe_query_stream(distinct_q)
			encT = oracle.build_encrypted_tuples()

			qrsr = query_recovery_attack(value_counts, obs, x=x, rng_seed=rng_seed)
			drsr = database_recovery_attack(value_counts, encT, obs, x=x, rng_seed=rng_seed)

			padded_vols = [o.observed_volume for _, o in obs]
			avg_pad = _safe_mean(padded_vols)
			overhead = (avg_pad / avg_real) if avg_real > 0 else 0.0

			rows.append(
				PaddingEvalRow(
					alpha=alpha,
					x=x,
					num_queries=len(obs),
					qrsr=qrsr,
					drsr=drsr,
					avg_real_vol=avg_real,
					avg_padded_vol=avg_pad,
					overhead_factor=overhead,
				)
			)
	return rows
