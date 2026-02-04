# src/seal/partitioning.py
from dataclasses import dataclass

def is_power_of_two(x: int) -> bool:
	return x > 0 and (x & (x - 1)) == 0

@dataclass(frozen=True)
class SealParams:
	n: int         	# total logical blocks, must be power of two
	alpha: int      # leakage parameter
	m: int          # number of sub-ORAMs = 2^alpha
	k: int          # log2(n)
	local_k: int    # k - alpha
	local_n: int    # n / m

# SEAL expects n = 2^k, then m = 2^alpha sub-ORAMs, each local_n = 2^(k-alpha).
def make_seal_params(n: int, alpha: int) -> SealParams:
	if not is_power_of_two(n):
		raise ValueError("SEAL requires n to be a power of two (e.g., 2^20).")
	k = n.bit_length() - 1
	if not (0 <= alpha <= k):
		raise ValueError(f"alpha must be in [0, {k}] for n=2^{k}.")
	m = 1 << alpha
	local_k = k - alpha
	local_n = 1 << local_k
	return SealParams(n=n, alpha=alpha, m=m, k=k, local_k=local_k, local_n=local_n)
