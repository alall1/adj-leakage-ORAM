# src/attacks/query_recovery.py
from __future__ import annotations
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.attacks.padding import next_power_of_x
from src.attacks.types import QueryObservation

# Attacker knows plaintext counts per value, compute padded sizes, then group values by padded size
def build_padded_size_buckets(value_counts: Dict[Any, int], x: Optional[int]) -> Dict[int, List[Any]]:
	buckets: Dict[int, List[Any]] = defaultdict(list)
	for v, c in value_counts.items():
		ps = next_power_of_x(c, x)
		buckets[ps].append(v)
	return buckets

# Implements SEAL query recovery attack
# Inputs: value_counts (plaintext counts per value, attacker knows dataset), observations (iterable of (true_value, QueryObservation)
# Returns: QRSR (fraction of queries correctly guessed)
def query_recovery_attack(
	value_counts: Dict[Any, int],
	observations: Iterable[Tuple[Any, QueryObservation]],
	x: Optional[int] = None,
	rng_seed: int = 1234,
) -> float:
	import random
	rnd = random.Random(rng_seed)

	buckets = build_padded_size_buckets(value_counts, x)
	remaining = {v: True for v in value_counts.keys()}  # attacker removes guesses from T

	correct = 0
	total = 0

	for true_value, obs in observations:
		total += 1
		candidates = [v for v in buckets.get(obs.observed_volume, []) if remaining.get(v, False)]

		# If padding creates collisions or candidates exhausted, attacker "fails gracefully"
		if not candidates:
			guess = None
		else:
			guess = rnd.choice(candidates)
			remaining[guess] = False  # remove chosen value from T

		if guess == true_value:
			correct += 1

	return correct / total if total else 0.0
