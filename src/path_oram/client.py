from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

from .types import Block, Bucket
from .server import ServerTree
from .utils import random_leaf, path_nodes, node_on_path_to_leaf, tree_depth_from_n

@dataclass
class ClientConfig:
	n: int
	Z: int
	depth: int
	default_value: Any = 0

# Client owns: position map, stash (both secret)
# Server owns: bucket tree (dumb storage)
class PathOramClient:
	def __init__(self, server: ServerTree, cfg: ClientConfig):
		self.server = server
		self.cfg = cfg
		self.position_map: list[int] = [0] * cfg.n
		self.stash: list[Block] = []
	
	@classmethod
	def setup(cls, n: int, Z: int, default_value: Any = 0) -> "PathOramClient":
		depth = tree_depth_from_n(n)
		server = ServerTree(depth=depth, Z=Z, dummy_filler=None)
		cfg = ClientConfig(n=n, Z=Z, depth=depth, default_value=default_value)
		client = cls(server=server, cfg=cfg)

		for i in range(n):
			client.position_map[i] = random_leaf(depth)

		return client

	# Always reads/writes full path, uses stash + eviction
	def access(self, op: str, block_id: int, new_data: Any = None) -> Optional[Any]:
		if not (0 <= block_id < self.cfg.n):
			raise ValueError("block_id out of range")
		if op not in ("read", "write"):
			raise ValueError("op must be 'read' or 'write'")

		# 1) old leaf from pos map
		old_leaf = self.position_map[block_id]

		# 2) immediately assign new leaf to logical block
		new_leaf = random_leaf(self.cfg.depth)
		self.position_map[block_id] = new_leaf

		# 3) read full path into stash
		path = self.server.read_path(old_leaf)
		for bucket in path:
			for b in bucket.real_blocks():
				self._stash_put_or_replace(b)

		# 4) get target block from stash
		target = self._stash_get(block_id)
		if target is None:
			target = Block(block_id=block_id, data=self.cfg.default_value, leaf=new_leaf, is_dummy=False)
			self.stash.append(target)

		# Keeping leaf consistent with position map
		target.leaf = new_leaf

		# 5) perform operation
		result: Optional[Any] = None
		if op == "read":
			result = target.data
		else:
			target.data = new_data

		# 6) eviction/write-back along accessed path
		new_path = self._evict_path(old_leaf)
		self.server.write_path(old_leaf, new_path)
		
		return result

	# ---------- stash helpers ----------

	def _stash_get(self, block_id: int) -> Optional[Block]:
		for b in self.stash:
			if (not b.is_dummy) and b.block_id == block_id:
				return b
		return None

	# Ensure no duplicate blocks
	def _stash_put_or_replace(self, block: Block) -> None:
		for i, b in enumerate(self.stash):
			if (not b.is_dummy) and b.block_id == block.block_id:
				self.stash[i] = block
				return
		self.stash.append(block)

	# ---------- eviction ----------

	# Rewrite path root->accessed_leaf using stash blocks; fill buckets from bottom->top so blocks are deep
	def _evict_path(self, accessed_leaf: int) -> list[Bucket]:
		nodes = path_nodes(accessed_leaf, self.cfg.depth)  # root..leaf
		new_buckets: list[Bucket] = [Bucket(Z=self.cfg.Z) for _ in nodes]
		
		# Process from leaf up to root (deepest first)
		for pos in range(len(nodes) - 1, -1, -1):
			level, idx = nodes[pos]
			bucket = Bucket(Z=self.cfg.Z)

			# Pick up to Z eligible blocks from stash
			eligible_indices = []
			for si, blk in enumerate(self.stash):
				if blk.is_dummy:
					continue
				if node_on_path_to_leaf(level, idx, blk.leaf, self.cfg.depth):
					eligible_indices.append(si)
				if len(eligible_indices) >= self.cfg.Z:
					break

			# Place chosen blocks into bucket and remove from stash
			chosen = [self.stash[i] for i in eligible_indices]
			for i in sorted(eligible_indices, reverse=True):
				self.stash.pop(i)
			
			bucket.blocks.extend(chosen)
			bucket.fill_with_dummies(leaf_hint=accessed_leaf, filler=None)
			bucket.enforce_capacity()

			new_buckets[pos] = bucket

		return new_buckets	

	# ---------- debugging / invariants ----------
	
	# Counts real blocks in stash + server
	def count_real_blocks_everywhere(self) -> int:
		count = 0
		count += sum(1 for b in self.stash if not b.is_dummy)
		for level in range(self.cfg.depth + 1):
			for bucket in self.server.tree[level]:
				count += sum(1 for b in bucket.blocks if not b.is_dummy)
		return count
