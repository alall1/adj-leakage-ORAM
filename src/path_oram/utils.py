import math
import secrets

def is_power_of_two(x: int) -> bool:
	return x > 0 and (x & (x - 1)) == 0

def next_power_of_two(x: int) -> int:
	if x <= 1:
		return 1
	return 1 << (x - 1).bit_length()

# Returns depth where leaves = 2^depth (n=8 -> depth=3)
def tree_depth_from_n(n: int) -> int:
	leaves = next_power_of_two(n)
	return int(math.log2(leaves))

# Random leaf label in [0, 2^depth - 1]
def random_leaf(depth: int) -> int:
	return secrets.randbelow(1 << depth)

# Returns [(level, index), ...] from root to leaf
def path_nodes(leaf: int, depth: int) -> list[tuple[int, int]]:
	nodes = []
	for level in range(depth + 1):
		idx = leaf >> (depth - level)
		nodes.append((level, idx))
	return nodes

# Returns true iff (node_level, node_idx) lies on path root->leaf
def node_on_path_to_leaf(node_level: int, node_idx: int, leaf: int, depth: int) -> bool:
	return node_idx == (leaf >> (depth - node_level))
