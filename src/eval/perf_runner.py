# src/eval/perf_runner.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import time
import random

from src.path_oram.client import PathOramClient
from src.seal.seal_client import SealClient

from src.path_oram.metrics import estimate_bandwidth_bytes

@dataclass(frozen=True)
class PerfConfig:
	n: int
	Z: int
	alphas: List[int]
	num_ops: int
	read_fraction: float  # e.g., 0.5
	block_size_bytes: int
	seed: int

	# access pattern on BLOCK IDs
	pattern: str  # "uniform" | "zipf_like" | "hot_set"
	hot_fraction: float = 0.10
	hot_mass: float = 0.90
	working_set_fraction: float = 0.01

@dataclass(frozen=True)
class PerfRow:
	scheme: str        # "path_oram" or "seal"
	alpha: int         # 0 for path_oram
	pattern: str
	num_ops: int
	seconds: float
	avg_bandwidth_bytes: float
	avg_buckets_read: float
	avg_buckets_written: float

def _make_block_trace(cfg: PerfConfig) -> List[int]:
	rng = random.Random(cfg.seed)
	n = cfg.n
	ops = cfg.num_ops

	if cfg.pattern == "uniform":
		return [rng.randrange(n) for _ in range(ops)]

	# Define hot blocks as top hot_fraction of IDs (simple; reproducible)
	hot_k = max(1, int(n * cfg.hot_fraction))
	hot_ids = list(range(hot_k))

	if cfg.pattern == "hot_set":
		ws_k = max(1, int(n * cfg.working_set_fraction))
		ws_ids = list(range(ws_k))
		return [ws_ids[rng.randrange(ws_k)] for _ in range(ops)]

	if cfg.pattern == "zipf_like":
		# With probability hot_mass, pick from hot set; else from full range
		trace = []
		for _ in range(ops):
			if rng.random() < cfg.hot_mass:
				trace.append(hot_ids[rng.randrange(hot_k)])
			else:
				trace.append(rng.randrange(n))
		return trace

	raise ValueError("unknown pattern")

def run_perf_path_oram(cfg: PerfConfig) -> PerfRow:
	rng = random.Random(cfg.seed + 1)
	
	oram = PathOramClient.setup(n=cfg.n, Z=cfg.Z, default_value=0)
	trace = _make_block_trace(cfg)

	total_br = total_bw = total_bytes = 0
	t0 = time.perf_counter()

	for bid in trace:
		op_is_read = (rng.random() < cfg.read_fraction)

		oram.server.reset_stats()
		if op_is_read:
			_ = oram.access("read", bid)
		else:
			oram.access("write", bid, rng.randrange(1_000_000))

		br = oram.server.stats.buckets_read
		bw = oram.server.stats.buckets_written

		total_br += br
		total_bw += bw
		total_bytes += estimate_bandwidth_bytes(br, bw, cfg.Z, cfg.block_size_bytes)

	t1 = time.perf_counter()

	return PerfRow(
		scheme="path_oram",
		alpha=0,
		pattern=cfg.pattern,
		num_ops=cfg.num_ops,
		seconds=(t1 - t0),
		avg_bandwidth_bytes=total_bytes / cfg.num_ops,
		avg_buckets_read=total_br / cfg.num_ops,
		avg_buckets_written=total_bw / cfg.num_ops,
	)

def run_perf_seal(cfg: PerfConfig, alpha: int) -> PerfRow:
	rng = random.Random(cfg.seed + 2 + alpha)

	seal = SealClient(n=cfg.n, Z=cfg.Z, alpha=alpha, default_value=0, block_size_bytes=cfg.block_size_bytes)
	trace = _make_block_trace(cfg)

	total_br = total_bw = total_bytes = 0
	t0 = time.perf_counter()

	for bid in trace:
		op_is_read = (rng.random() < cfg.read_fraction)

		# SealClient already resets sub.server stats inside access()
		if op_is_read:
			_ = seal.access("read", bid)
		else:
			seal.access("write", bid, rng.randrange(1_000_000))

		log = seal.last_access
		total_br += log.buckets_read
		total_bw += log.buckets_written
		total_bytes += log.approx_bandwidth_bytes

	t1 = time.perf_counter()

	return PerfRow(
		scheme="seal",
		alpha=alpha,
		pattern=cfg.pattern,
		num_ops=cfg.num_ops,
		seconds=(t1 - t0),
		avg_bandwidth_bytes=total_bytes / cfg.num_ops,
		avg_buckets_read=total_br / cfg.num_ops,
		avg_buckets_written=total_bw / cfg.num_ops,
	)
