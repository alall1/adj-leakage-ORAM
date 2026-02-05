# src/eval/checkpoints.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class CheckpointSpec:
	points: List[int]

DEFAULT_CHECKPOINTS = CheckpointSpec(points=[10, 100, 1_000, 10_000])
