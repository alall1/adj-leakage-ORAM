# tests/bench_seal_alpha.py
import random
from src.seal.seal_client import SealClient

def bench():
	n = 1 << 12  # keep small for quick runs
	Z = 4
	ops = 2000

	for alpha in [0, 1, 2, 3, 4]:
		seal = SealClient(n=n, Z=Z, alpha=alpha, default_value=0, block_size_bytes=64)

		# Prime a subset (enough for meaningful reads)
		for i in range(min(n, 512)):
			seal.access("write", i, i)

		total_br = total_bw = total_bytes = 0

		for _ in range(ops):
			i = random.randrange(n)
			if random.random() < 0.5:
				seal.access("write", i, random.randrange(1_000_000))
			else:
				seal.access("read", i)

			log = seal.last_access
			total_br += log.buckets_read
			total_bw += log.buckets_written
			total_bytes += log.approx_bandwidth_bytes

		print(
			f"alpha={alpha:2d}  "
			f"avg_read_buckets={total_br/ops:6.2f}  "
			f"avg_write_buckets={total_bw/ops:6.2f}  "
			f"avg_bandwidth_bytes={total_bytes/ops:10.1f}"
		)

if __name__ == "__main__":
	bench()
