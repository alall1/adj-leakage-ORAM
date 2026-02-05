# tests/test_over_time_eval.py
from src.workload.synthetic import make_zipf_dataset
from src.eval.workloads import WorkloadSpec, make_uniform_distinct
from src.eval.phase3_runner import RunConfig, evaluate_over_time

def test_over_time_eval():
	n = 1 << 12
	Z = 4
	ds = make_zipf_dataset(n=n, vocab=512, a=1.2, seed=7)
	counts = ds.value_counts()
	values = list(ds.index.keys())

	spec = WorkloadSpec(name="uniform", num_queries=500, seed=0)
	qvals = make_uniform_distinct(values, spec)

	cfg = RunConfig(n=n, Z=Z, alphas=[0, 2, 4], padding_x=None, rng_seed=42)
	ts = evaluate_over_time(ds.index, counts, qvals, cfg)

	assert set(ts.series.keys()) == {0, 2, 4}
	for alpha, points in ts.series.items():
		assert len(points) > 0
		for t, qrsr, drsr in points:
			assert 1 <= t <= len(qvals)
			assert 0.0 <= qrsr <= 1.0
			assert 0.0 <= drsr <= 1.0

	print("OK: over-time eval test passed")

if __name__ == "__main__":
	test_over_time_eval()
