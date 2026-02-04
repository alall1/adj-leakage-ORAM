# tests/test_prp.py
from src.seal.prp import AffinePRP
import secrets

def test_prp_small():
	n = 1024
	k = n.bit_length() - 1
	prp = AffinePRP(key=secrets.token_bytes(16), k=k)
	
	seen = set()
	for i in range(n):
		j = prp.permute(i)
		assert 0 <= j < n
		assert j not in seen
		seen.add(j)
		assert prp.inverse(j) == i

	print("OK: PRP permutation + inverse test passed")

if __name__ == "__main__":
	test_prp_small()
