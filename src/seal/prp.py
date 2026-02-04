# src/seal/prp.py
import hashlib
from dataclasses import dataclass

def _hash_to_int(key: bytes, label: bytes, out_bytes: int = 8) -> int:
	h = hashlib.blake2s(digest_size=out_bytes)
	h.update(key)
	h.update(label)
	return int.from_bytes(h.digest(), "big")

# Returns (g, x, y) s.t. ax + by = g = gcd(a,b)
def _egcd(a: int, b: int) -> tuple[int, int, int]:
	if b == 0:
		return (a, 1, 0)
	g, x1, y1 = _egcd(b, a % b)
	return (g, y1, x1 - (a // b) * y1)

def _modinv(a: int, m: int) -> int:
	g, x, _ = _egcd(a, m)
	if g != 1:
		raise ValueError("no modular inverse")
	return x % m

# Conceptual PRP over k-bit integers using affline permutation mod 2^k
@dataclass(frozen=True)
class AffinePRP:
	key: bytes
	k: int

	def __post_init__(self):
		if self.k <= 0:
			raise ValueError("k must be positive")
		
		mod = 1 << self.k

		# Derive 'a' and 'b' from the key deterministically.
		a = _hash_to_int(self.key, b"SEAL_A") % mod
		b = _hash_to_int(self.key, b"SEAL_B") % mod

		# Force a to be odd so inverse exists mod 2^k.
		a |= 1

		object.__setattr__(self, "a", a)
		object.__setattr__(self, "b", b)
		object.__setattr__(self, "mod", mod)
		object.__setattr__(self, "a_inv", _modinv(a, mod))

	def permute(self, x: int) -> int:
		if x < 0 or x >= self.mod:
			raise ValueError("x out of range for k-bit PRP")
		return (self.a * x + self.b) % self.mod

	def inverse(self, y: int) -> int:
		if y < 0 or y >= self.mod:
			raise ValueError("y out of range for k-bit PRP")
		return (self.a_inv * (y - self.b)) % self.mod
