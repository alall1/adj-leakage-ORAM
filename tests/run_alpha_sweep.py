# tests/run_alpha_sweep.py
from src.seal.seal_client import SealClient
from src.workload.synthetic import make_zipf_dataset
from src.workload.leakage_oracle import SealLeakageOracle
from src.attacks.query_recovery import query_recovery_attack
from src.attacks.database_recovery import database_recovery_attack

def main():
	n = 1 << 12
	Z = 4
	ds = make_zipf_dataset(n=n, vocab=512, a=1.2, seed=2)
	counts = ds.value_counts()

	for alpha in [0, 1, 2, 3, 4, 5]:
		seal = SealClient(n=n, Z=Z, alpha=alpha, default_value=0)
		oracle = SealLeakageOracle(seal=seal, dataset_index=ds.index, padding_x=None, rng_seed=123)

		obs = oracle.observe_all_queries()
		encT = oracle.build_encrypted_tuples()

		qrsr = query_recovery_attack(counts, obs, x=None, rng_seed=123)
		drsr = database_recovery_attack(counts, encT, obs, x=None, rng_seed=123)

		print(f"alpha={alpha:2d}  QRSR={qrsr:0.3f}  DRSR={drsr:0.3f}")

if __name__ == "__main__":
	main()
