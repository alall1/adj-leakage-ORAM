# src/attacks/database_recovery.py
from __future__ import annotations
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.attacks.padding import next_power_of_x
from src.attacks.query_recovery import build_padded_size_buckets
from src.attacks.types import EncryptedTuple, QueryObservation

# SEAL database recovery attack adapted to this setting
# Attacker steps:
# 1) Guess the queried plaintext value q0 using volume
# 2) For each returned tuple prefix in Sq: pick a random encrypted tuple from enc(T) that has same alpha-prefix and "map" guessed value to it
# 3) Count correct mappings
def database_recovery_attack(
	value_counts: Dict[Any, int],
	encrypted_tuples: List[EncryptedTuple],
	observations: Iterable[Tuple[Any, QueryObservation]],
	x: Optional[int] = None,
	rng_seed: int = 1234,
) -> float:
	import random
	rnd = random.Random(rng_seed)

	# Bucket values by padded size
	size_buckets = build_padded_size_buckets(value_counts, x)
	remaining_values = {v: True for v in value_counts.keys()}

	# Group encrypted tuples by alpha_prefix (attacker can do this from IDs/prefixes)
	by_prefix: Dict[int, List[EncryptedTuple]] = defaultdict(list)
	for t in encrypted_tuples:
		by_prefix[t.alpha_prefix].append(t)

	# We'll remove tuples from enc(T) as the attack assigns them
	live_by_prefix: Dict[int, List[EncryptedTuple]] = {p: lst[:] for p, lst in by_prefix.items()}

	correct = 0
	denom = 0

	for true_value, obs in observations:
		# Step 1: guess the query plaintext value
		candidates = [v for v in size_buckets.get(obs.observed_volume, []) if remaining_values.get(v, False)]
		if not candidates:
			guess = None
		else:
			guess = rnd.choice(candidates)
			remaining_values[guess] = False

		# Step 2: map returned tuples
		for prefix in obs.returned_prefixes:
			denom += 1
			pool = live_by_prefix.get(prefix, [])
			if not pool:
				continue  # nothing left with that prefix; attacker can't map
			chosen_idx = rnd.randrange(len(pool))
			chosen = pool.pop(chosen_idx)  # remove from enc(T)

			if guess is not None and chosen.value == guess:
				correct += 1
	return correct / denom if denom else 0.0
	
