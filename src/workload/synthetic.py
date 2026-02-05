# src/workload/synthetic.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

# Plaintext dataset: values[i] is plaintext attribute value for record i, index maps each value -> list of record IDs where it appears
@dataclass(frozen=True)
class SyntheticDataset:
	n: int
	values: np.ndarray
	index: Dict[int, np.ndarray]
	
	def value_counts(self) -> Dict[int, int]:
		return {v: int(ids.size) for v, ids in self.index.items()}

# Generates a skewed dataset, making volume-based attacks meaningful (vocab is number of distinct plaintext values)
def make_zipf_dataset(n: int, vocab: int = 2**12, a: float = 1.2, seed: int = 0) -> SyntheticDataset:
	rng = np.random.default_rng(seed)
	raw = rng.zipf(a=a, size=n)
	values = (raw % vocab).astype(np.int32)

	index: Dict[int, np.ndarray] = {}
	for v in range(vocab):
		ids = np.nonzero(values == v)[0]
		if ids.size > 0:
			index[int(v)] = ids.astype(np.int32)

	return SyntheticDataset(n=n, values=values, index=index)
