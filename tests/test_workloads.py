# tests/test_workloads.py
from src.workload.synthetic import make_zipf_dataset
from src.eval.workloads import (
	WorkloadSpec,
	make_uniform_distinct,
	make_zipf_like_distinct,
	make_hot_set_distinct,
)

def test_workload_generators():
	n = 1 << 12
	ds = make_zipf_dataset(n=n, vocab=512, a=1.2, seed=1)
	counts = ds.value_counts()
	values = list(ds.index.keys())

	# Uniform
	spec_u = WorkloadSpec(name="uniform", num_queries=100, seed=0)
	w_u = make_uniform_distinct(values, spec_u)
	assert len(w_u) == len(set(w_u)) == 100

	# Zipf-like should bias toward hot values
	spec_z = WorkloadSpec(name="zipf_like", num_queries=200, seed=1, hot_fraction=0.10, hot_mass=0.90)
	w_z = make_zipf_like_distinct(values, counts, spec_z)
	assert len(w_z) == len(set(w_z))  # distinct by construction

	sorted_vals = sorted(values, key=lambda v: counts.get(v, 0), reverse=True)
	hot_k = max(1, int(len(sorted_vals) * spec_z.hot_fraction))
	hot = set(sorted_vals[:hot_k])

	hot_hits = sum(1 for v in w_z if v in hot)
	# Not exact, but should be noticeably > uniform expectation
	assert hot_hits > 0.5 * len(w_z)

	# Hot-set should only draw from working set
	spec_h = WorkloadSpec(name="hot_set", num_queries=50, seed=2, working_set_fraction=0.05)
	w_h = make_hot_set_distinct(values, counts, spec_h)

	ws_k = max(1, int(len(sorted_vals) * spec_h.working_set_fraction))
	ws = set(sorted_vals[:ws_k])
	assert all(v in ws for v in w_h)

	print("OK: workload generator tests passed")

if __name__ == "__main__":
	test_workload_generators()
