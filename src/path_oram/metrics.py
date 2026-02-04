# src/path_oram/metrics.py
from dataclasses import dataclass

@dataclass
class OramMetrics:
	buckets_read: int
	buckets_written: int
	stash_size: int
	approx_bandwidth_bytes: int

# Rough bandwidth estimate: each bucket contains Z blocks with block_size_bytes, counting read/write buckets
def estimate_bandwidth_bytes(
	buckets_read: int,
	buckets_written: int,
	Z: int,
	block_size_bytes: int
) -> int:
	return (buckets_read + buckets_written) * Z * block_size_bytes
