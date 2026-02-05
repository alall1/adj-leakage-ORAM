# src/attacks/padding.py
from typing import Optional

# Pads s to the next power of x, if x is None, no padding
# Example: s = 13, x = 4 -> 16
def next_power_of_x(s: int, x: Optional[int]) -> int:
	if x is None:
		return s
	if x < 2:
		raise ValueError("x must be >= 2")
	if s <= 1:
		return s
	p = 1
	while p < s:
		p *= x
	return p
