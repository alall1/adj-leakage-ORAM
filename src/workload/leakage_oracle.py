# src/workload/leakage_oracle.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

from src.attacks.padding import next_power_of_x
from src.attacks.types import EncryptedTuple, QueryObservation
from src.seal.seal_client import SealClient

# Produces the leakage trace an attacker sees for "point queries", query(v) returns record IDs where dataset value == v
# Leakage per query: observed_volume (potentially padded), list of alpha-prefixes for each returned tuple (oram_index) 
@dataclass
class SealLeakageOracle:
	seal: SealClient
	dataset_index: Dict[Any, np.ndarray]
	padding_x: Optional[int] = None
	rng_seed: int = 1234

	# Build enc(T) with one EncryptedTuple per real record (attacker doesn't see value in reality, but we store to score correctness)
	def build_encrypted_tuples(self) -> List[EncryptedTuple]:
		enc: List[EncryptedTuple] = []
		enc_id = 0
		for value, ids in self.dataset_index.items():
			for rid in ids.tolist():
				oram_index, _ = self.seal.route(int(rid))
				enc.append(EncryptedTuple(enc_id=enc_id, value=value, alpha_prefix=oram_index))
				enc_id += 1
		return enc

	# Create one query per distinct value (worst-case style), returns list of (true_value, QueryObservation)
	def observe_all_queries(self) -> List[Tuple[Any, QueryObservation]]:
		import random
		rnd = random.Random(self.rng_seed)

		obs_list: List[Tuple[Any, QueryObservation]] = []
		token_id = 0

		for value, ids in self.dataset_index.items():
			real_ids = ids.astype(np.int64)
			real_prefixes: List[int] = []
			for rid in real_ids.tolist():
				oram_index, _ = self.seal.route(int(rid))
				real_prefixes.append(oram_index)

			real_vol = len(real_prefixes)
			padded_vol = next_power_of_x(real_vol, self.padding_x)

			# Add dummy prefixes if padding increases volume
			if padded_vol > real_vol:
				extra = padded_vol - real_vol
				# Dummy prefixes are just random ORAM choices (attacker sees only prefix)
				for _ in range(extra):
					real_prefixes.append(rnd.randrange(1 << self.seal.params.alpha) if self.seal.params.alpha > 0 else 0)

			obs = QueryObservation(
				token_id=token_id,
				observed_volume=padded_vol,
				returned_prefixes=real_prefixes,
			)
			obs_list.append((value, obs))
			token_id += 1
		return obs_list
