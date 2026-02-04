# tests/test_invariants.py
import random
from src.path_oram.client import PathOramClient

def test_invariants_small():
	n = 16
	Z = 4
	oram = PathOramClient.setup(n=n, Z=Z, default_value=0)

	# Truth store
	truth = {i: 0 for i in range(n)}

	# --- Prime the ORAM so every block definitely exists somewhere ---
	for i in range(n):
		oram.server.reset_stats()
		v = random.randrange(1_000_000)
		oram.access("write", i, v)
		truth[i] = v
		
		# path-touch sanity
		d = oram.cfg.depth
		assert oram.server.stats.buckets_read == d + 1
		assert oram.server.stats.buckets_written == d + 1
		
		# invariants (don't require all blocks present yet)
		oram.assert_invariants(require_all_blocks_present=False)

	# Priming is done, check that all blocks are present
	oram.assert_invariants(require_all_blocks_present=True)
	
	# --- Random operations ---
	max_stash = 0
	for _ in range(300):
		block_id = random.randrange(n)
		oram.server.reset_stats()
		
		if random.random() < 0.5:
			v = random.randrange(1_000_000)
			oram.access("write", block_id, v)
			truth[block_id] = v
		else:
			got = oram.access("read", block_id)
			assert got == truth[block_id]

		# path-touch sanity: exactly one full path read + written
		d = oram.cfg.depth
		assert oram.server.stats.buckets_read == d + 1
		assert oram.server.stats.buckets_written == d + 1

		# invariants: after priming, all blocks should remain present exactly once
		oram.assert_invariants(require_all_blocks_present=True)

		# stash tracking (not a strict assertion; just visibility)
		max_stash = max(max_stash, len(oram.stash))

	print("OK: invariant test passed")
	print(f"Max stash size observed: {max_stash}")

if __name__ == "__main__":
	test_invariants_small()
