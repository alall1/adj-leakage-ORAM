# src/seal/seal_client.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

import secrets

from src.path_oram.client import PathOramClient
from src.path_oram.metrics import OramMetrics, estimate_bandwidth_bytes
from src.seal.partitioning import make_seal_params, SealParams
from src.seal.prp import AffinePRP

@dataclass
class SealAccessLog:
	oram_index: int
	local_id: int
	buckets_read: int
	buckets_written: int
	stash_size: int
	approx_bandwidth_bytes: int

# SEAL wrapper, maintains m = 2^alpha Path ORAMs, of size local_n
# Routes each global block_id using j = PRP_k(block_id), oram_index = top alpha bits of j, local_id = remaining bits of j 
class SealClient:
	def __init__(
		self,
		n: int,
		Z: int,
		alpha: int,
		block_size_bytes: int = 64,
		prp_key: Optional[bytes] = None,
		default_value: Any = 0,
	):
		self.params: SealParams = make_seal_params(n, alpha)
		self.Z = Z
		self.block_size_bytes = block_size_bytes
		self.default_value = default_value

		if prp_key is None:
			prp_key = secrets.token_bytes(16)
		self.prp = AffinePRP(key=prp_key, k=self.params.k)

		# Create sub-ORAMs
		self.sub_orams: list[PathOramClient] = []
		for _ in range(self.params.m):
			self.sub_orams.append(PathOramClient.setup(n=self.params.local_n, Z=Z, default_value=default_value))
		
		# Optional: keep an access log if you want (useful for Phase 3 attacker)
		self.last_access: Optional[SealAccessLog] = None
		self.access_log: list[SealAccessLog] = []
		
	# Returns (oram_index, local_id) based on PRP(global_id)
	def route(self, global_id: int) -> tuple[int, int]:
		if not (0 <= global_id < self.params.n):
			raise ValueError("global_id out of range")
		j = self.prp.permute(global_id)  # k-bit value

		# top alpha bits decide the ORAM index
		if self.params.alpha == 0:
			oram_index = 0
			local_id = j  # all bits used as local id
			return oram_index, local_id

		shift = self.params.local_k
		oram_index = j >> shift
		local_mask = (1 << shift) - 1
		local_id = j & local_mask
		return oram_index, local_id

	# Same interface style as Path ORAM, but with global IDs
	def access(self, op: str, global_id: int, new_data: Any = None) -> Optional[Any]:
		oram_index, local_id = self.route(global_id)
		
		# Reset stats so per-access counters are clean
		sub = self.sub_orams[oram_index]
		sub.server.reset_stats()
		
		result = sub.access(op, local_id, new_data)

		# Capture per-access metrics (this is your leakage signal too)
		br = sub.server.stats.buckets_read
		bw = sub.server.stats.buckets_written
		stash_size = len(sub.stash)
		approx_bw = estimate_bandwidth_bytes(br, bw, self.Z, self.block_size_bytes)

		self.last_access = SealAccessLog(
			oram_index=oram_index,
			local_id=local_id,
			buckets_read=br,
			buckets_written=bw,
			stash_size=stash_size,
			approx_bandwidth_bytes=approx_bw,
		)

		self.access_log.append(self.last_access)
		return result

	def reset_log(self) -> None:
		self.access_log = []
		self.last_access = None
