# tests/test_attacks_small.py
from src.seal.seal_client import SealClient
from src.workload.synthetic import make_zipf_dataset
from src.workload.leakage_oracle import SealLeakageOracle
from src.attacks.query_recovery import query_recovery_attack
from src.attacks.database_recovery import database_recovery_attack

def test_attacks_small():
	n = 1 << 10
	Z = 4
	alpha = 3

	ds = make_zipf_dataset(n=n, vocab=256, a=1.2, seed=1)

	seal = SealClient(n=n, Z=Z, alpha=alpha, default_value=0)
	oracle = SealLeakageOracle(seal=seal, dataset_index=ds.index, padding_x=None)

	observations = oracle.observe_all_queries()
	counts = ds.value_counts()
	encT = oracle.build_encrypted_tuples()

	qrsr = query_recovery_attack(counts, observations, x=None, rng_seed=7)
	drsr = database_recovery_attack(counts, encT, observations, x=None, rng_seed=7)

	assert 0.0 <= qrsr <= 1.0
	assert 0.0 <= drsr <= 1.0

	print(f"OK: QRSR={qrsr:.3f}, DRSR={drsr:.3f}")

if __name__ == "__main__":
	test_attacks_small()
