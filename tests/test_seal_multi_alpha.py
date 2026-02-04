# tests/test_seal_multi_alpha.py
import random
from src.seal.seal_client import SealClient

def run_one(alpha: int):
	n = 128
	Z = 4
	seal = SealClient(n=n, Z=Z, alpha=alpha, default_value=0)

	truth = {i: 0 for i in range(n)}

	# Prime
	for i in range(n):
		v = random.randrange(1_000_000)
		seal.access("write", i, v)
		truth[i] = v

	# Random ops
	for _ in range(600):
		i = random.randrange(n)
		if random.random() < 0.5:
			v = random.randrange(1_000_000)
			seal.access("write", i, v)
			truth[i] = v
		else:
			got = seal.access("read", i)
			assert got == truth[i]

	return True

def test_multi_alpha():
	for alpha in [0, 1, 2, 3, 4]:
		assert run_one(alpha)
		print(f"OK: alpha={alpha} passed")

if __name__ == "__main__":
	test_multi_alpha()
