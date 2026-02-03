from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from .types import Bucket
from .utils import path_nodes

@dataclass
class ServerStats:
	buckets_read: int = 0
	buckets_written: int = 0

class ServerTree:
	def __init__(self, depth: int, Z: int, dummy_filler: Any = None):
		self.depth = depth
		self.Z = Z
		self.dummy_filler = dummy_filler
		self.stats = ServerStats()

		# tree[level][idx] is a Bucket
		self.tree: list[list[Bucket]] = []
		for level in range(depth + 1):
			level_nodes = 1 << level
			self.tree.append([self._new_empty_bucket() for _ in range(level_nodes)])

	def _new_empty_bucket(self) -> Bucket:
		b = Bucket(Z=self.Z)
		b.fill_with_dummies(leaf_hint=0, filler=self.dummy_filler)
		return b

	# Returns a copy of buckets along root->leaf (Client will write a fresh path back later)
	def read_path(self, leaf: int) -> list[Bucket]:
		buckets: list[Bucket] = []
		for (level, idx) in path_nodes(leaf, self.depth):
			self.stats.buckets_read += 1
			orig = self.tree[level][idx]
			copied = Bucket(Z=orig.Z, blocks=list(orig.blocks))
			buckets.append(copied)

			# Clear server buckets to model "will be overwritten"
			self.tree[level][idx] = self._new_empty_bucket()

		return buckets

	def write_path(self, leaf: int, buckets: list[Bucket]) -> None:
		nodes = path_nodes(leaf, self.depth)
		if len(buckets) != len(nodes):
			raise ValueError("write_path: buckets length mismatch with path length")

		for (bucket, (level, idx)) in zip(buckets, nodes):
			bucket.enforce_capacity()
			self.stats.buckets_written += 1
			self.tree[level][idx] = bucket

	def reset_stats(self) -> None:
		self.stats = ServerStats()
