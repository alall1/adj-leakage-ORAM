# tests/test_medium_smoke.py
import random
from src.path_oram.client import PathOramClient

def test_medium_smoke():
	n = 1 << 12   # 4096
	Z = 4
	oram = PathOramClient.setup(n=n, Z=Z, default_value=0)

	# Just do writes/reads on random subset (fast)
	truth = {}
	for _ in range(2000):
		i = random.randrange(n)
		if random.random() < 0.6:
			v = random.randrange(1_000_000)
			oram.access("write", i, v)
			truth[i] = v
		else:
			# only check if wrote before (since default_value is 0)
			got = oram.access("read", i)
			if i in truth:
				assert got == truth[i]
	
	print("OK: medium smoke test passed")

if __name__ == "__main__":
	test_medium_smoke()
