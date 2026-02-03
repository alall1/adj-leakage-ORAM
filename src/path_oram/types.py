from dataclasses import dataclass, field
from typing import Any

DUMMY_ID = -1

@dataclass
class Block:
	block_id: int
	data: Any
	leaf: int
	is_dummy: bool = False

	@staticmethod
	def dummy(leaf: int, filler: Any = None) -> "Block":
		return Block(block_id=DUMMY_ID, data=filler, leaf=leaf, is_dummy=True)

@dataclass
class Bucket:
	Z: int
	blocks: list[Block] = field(default_factory=list)
	
	def real_blocks(self) -> list[Block]:
		return [b for b in self.blocks if not b.is_dummy]
	
	def clear(self) -> None:
		self.blocks = []

	# Padding bucket up to Z blocks with dummy blocks
	def fill_with_dummies(self, leaf_hint: int = 0, filler: Any = None) -> None:
		while len(self.blocks) < self.Z:
			self.blocks.append(Block.dummy(leaf=leaf_hint, filler=filler))

	def enforce_capacity(self) -> None:
		if len(self.blocks) > self.Z:
			raise ValueError(f"Bucket overflow: has {len(self.blocks)} > Z={self.Z}")
