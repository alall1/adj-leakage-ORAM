# tests/test_small_oram.py
import random
from src.path_oram.client import PathOramClient

def test_small_correctness():
	n = 16
	Z = 4
	oram = PathOramClient.setup(n=n, Z=Z, default_value=0)

	truth = {i: 0 for i in range(n)}

	# Do random ops
	for _ in range(200):
		block_id = random.randrange(n)
		if random.random() < 0.5:
			# write
			v = random.randrange(10_000)
			oram.access("write", block_id, v)
			truth[block_id] = v
		else:
			# read
			got = oram.access("read", block_id)
			assert got == truth[block_id]
	
		# Path length sanity: depth+1 reads and depth+1 writes per access
		d = oram.cfg.depth
		assert oram.server.stats.buckets_read % (d + 1) == 0
		assert oram.server.stats.buckets_written % (d + 1) == 0

	print("OK: small correctness test passed")

if __name__ == "__main__":
	test_small_correctness()
