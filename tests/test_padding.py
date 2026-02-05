# tests/test_padding.py
from src.attacks.padding import next_power_of_x

def is_power_of_x(val: int, x: int) -> bool:
	if val <= 0:
		return False
	p = 1
	while p < val:
		p *= x
	return p == val

def test_padding_rules():
	# No padding
	for s in [0, 1, 2, 3, 7, 13, 64]:
		assert next_power_of_x(s, None) == s

	# Power-of-x padding checks
	for x in [2, 4, 8]:
		for s in [1, 2, 3, 5, 7, 9, 13, 17, 63, 64, 65]:
			p = next_power_of_x(s, x)
			assert p >= s
			assert is_power_of_x(p, x) or p == 1  # 1 is x^0

	print("OK: padding tests passed")

if __name__ == "__main__":
	test_padding_rules()
