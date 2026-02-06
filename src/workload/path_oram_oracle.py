# src/workload/path_oram_oracle.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.attacks.types import QueryObservation
from src.attacks.padding import next_power_of_x

# Baseline leakage-free oracle for comparing vs SEAL attacks; exposed: observed_volume, returned_prefixes
@dataclass
class PathOramLeakageOracle:
	dataset_index: Dict[Any, np.ndarray]
	constant_volume: int = 1
	padding_x: Optional[int] = None

	def observe_query(self, value: Any, token_id: int) -> Tuple[Any, QueryObservation]:
		vol = self.constant_volume
		vol = next_power_of_x(vol, self.padding_x)  # optional padding
		obs = QueryObservation(
			token_id=token_id,
			observed_volume=vol,
			returned_prefixes=[],
		)

		return value, obs

	def observe_query_stream(self, values_in_order: List[Any]) -> List[Tuple[Any, QueryObservation]]:
		out: List[Tuple[Any, QueryObservation]] = []
		for t, v in enumerate(values_in_order):
			out.append(self.observe_query(v, token_id=t))
		return out
