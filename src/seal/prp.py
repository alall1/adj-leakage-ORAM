# src/seal/prp.py
import hashlib
from dataclasses import dataclass

def _u32(x: int) -> int:
	return x & 0xFFFFFFFF

# Conceptual PRF for Feistel: returns 32-bit int from (key, round, half)
def _round_f(key: bytes, r: int, half: int) -> int:
	h = hashlib.blake2s(digest_size=4)
	h.update(key)
	h.update(r.to_bytes(4, "big"))
	h.update(_u32(half).to_bytes(4, "big"))
	return int.from_bytes(h.digest(), "big")

# Conceptual PRP over k-bit integers using a Feistel network (if k is odd, pad the split by 1 bit
@dataclass(frozen=True)
class FeistelPRP:
	key: bytes
	k: int
	rounds: int = 6

	def permute(self, x: int) -> int:
		if x < 0 or x >= (1 << self.k):
			raise ValueError("x out of range for k-bit PRP")

		# Split bits
		left_bits = self.k // 2
		right_bits = self.k - left_bits
		L_mask = (1 << left_bits) - 1
		R_mask = (1 << right_bits) - 1

		L = (x >> right_bits) & L_mask
		R = x & R_mask

		for r in range(self.rounds):
			f = _round_f(self.key, r, R) & L_mask  # match L size
			L, R = R, (L ^ f) & L_mask if left_bits == right_bits else (L ^ f) & L_mask

		y = ((L & L_mask) << right_bits) | (R & R_mask)
		return y

	def inverse(self, y: int) -> int:
		if y < 0 or y >= (1 << self.k):
			raise ValueError("y out of range for k-bit PRP")

		left_bits = self.k // 2
		right_bits = self.k - left_bits
		L_mask = (1 << left_bits) - 1
		R_mask = (1 << right_bits) - 1

		L = (y >> right_bits) & L_mask
		R = y & R_mask

		for r in reversed(range(self.rounds)):
			f = _round_f(self.key, r, L) & L_mask
			L, R = (R ^ f) & L_mask, L
		
		x = ((L & L_mask) << right_bits) | (R & R_mask)
		return x
