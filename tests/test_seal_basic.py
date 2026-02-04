# tests/test_seal_basic.py
import random
from src.seal.seal_client import SealClient

def test_seal_basic():
	n = 64
	Z = 4
	alpha = 2

	seal = SealClient(n=n, Z=Z, alpha=alpha, default_value=0)

	truth = {i: 0 for i in range(n)}

	# Prime: write all blocks once
	for i in range(n):
		v = random.randrange(1_000_000)
		seal.access("write", i, v)
		truth[i] = v

	# Random ops
	for _ in range(500):
		i = random.randrange(n)
		if random.random() < 0.5:
			v = random.randrange(1_000_000)
			seal.access("write", i, v)
			truth[i] = v
		else:
			got = seal.access("read", i)
			assert got == truth[i]

		# leakage signal is: which oram_index was touched
		assert seal.last_access is not None
		assert 0 <= seal.last_access.oram_index < (1 << alpha)

	print("OK: SEAL basic test passed")

if __name__ == "__main__":
	test_seal_basic()
