# src/eval/session_eval.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from src.attacks.query_recovery import query_recovery_attack
from src.attacks.database_recovery import database_recovery_attack
from src.workload.leakage_oracle import SealLeakageOracle
from src.workload.path_oram_oracle import PathOramLeakageOracle

@dataclass(frozen=True)
class SessionStats:
	qrsr_mean: float
	qrsr_std: float
	drsr_mean: float
	drsr_std: float

def _mean_std(xs: List[float]) -> Tuple[float, float]:
	if not xs:
		return 0.0, 0.0
	arr = np.array(xs, dtype=float)
	return float(arr.mean()), float(arr.std())

# Runs attacks independently per session, reset attacker state by using fresh rng_seed per session
def evaluate_sessions(
	oracle: Union[SealLeakageOracle, PathOramLeakageOracle],
	value_counts: Dict[Any, int],
	encrypted_tuples: Optional[list] ,
	sessions: List[List[Any]],
	padding_x: Optional[int],
	base_seed: int = 0,
) -> SessionStats:
	qrsr_list: List[float] = []
	drsr_list: List[float] = []

	for s_idx, sess_values in enumerate(sessions):
		obs = oracle.observe_query_stream(sess_values)

		# fresh attacker per session:
		seed = base_seed + s_idx

		qrsr = query_recovery_attack(value_counts, obs, x=padding_x, rng_seed=seed)
		qrsr_list.append(qrsr)

		if encrypted_tuples is None:
			# baseline: no identifiers / no meaningful tuple mapping
			drsr = 0.0
		else:
			drsr = database_recovery_attack(value_counts, encrypted_tuples, obs, x=padding_x, rng_seed=seed)
		drsr_list.append(drsr)

	q_mean, q_std = _mean_std(qrsr_list)
	d_mean, d_std = _mean_std(drsr_list)

	return SessionStats(qrsr_mean=q_mean, qrsr_std=q_std, drsr_mean=d_mean, drsr_std=d_std)
