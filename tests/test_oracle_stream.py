# tests/test_oracle_stream.py
from src.seal.seal_client import SealClient
from src.workload.synthetic import make_zipf_dataset
from src.workload.leakage_oracle import SealLeakageOracle

def test_oracle_stream():
	n = 1 << 10
	Z = 4
	alpha = 3

	ds = make_zipf_dataset(n=n, vocab=128, a=1.2, seed=3)
	seal = SealClient(n=n, Z=Z, alpha=alpha, default_value=0)
	oracle = SealLeakageOracle(seal=seal, dataset_index=ds.index, padding_x=None, rng_seed=5)

	values = list(ds.index.keys())[:25]
	obs = oracle.observe_query_stream(values)

	assert len(obs) == len(values)

	for (v, qobs) in obs:
		# volume should match index size when no padding
		assert qobs.observed_volume == len(ds.index[v])
		assert len(qobs.returned_prefixes) == qobs.observed_volume

	print("OK: oracle stream test passed")

if __name__ == "__main__":
	test_oracle_stream()
