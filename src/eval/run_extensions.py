# src/eval/run_extensions.py
from __future__ import annotations
from typing import Dict, List

from src.workload.synthetic import make_zipf_dataset
from src.eval.workloads import WorkloadSpec, make_uniform_distinct, make_zipf_like_distinct, make_hot_set_distinct
from src.eval.phase3_runner import RunConfig, evaluate_over_time
from src.eval.plotting import plot_success_over_time

def main():
	n = 1 << 14
	Z = 4
	alphas = [0, 1, 2, 3, 4, 5]
	padding_x = None

	# Synthetic dataset (skewed is useful for volume attacks)
	ds = make_zipf_dataset(n=n, vocab=2048, a=1.2, seed=1)
	value_counts = ds.value_counts()
	all_values = list(ds.index.keys())

	# ---- Extension 1: access patterns ----
	patterns = [
		("uniform", WorkloadSpec(name="uniform", num_queries=10_000, seed=10)),
		("zipf_like", WorkloadSpec(name="zipf_like", num_queries=10_000, seed=11, hot_fraction=0.10, hot_mass=0.90)),
		("hot_set", WorkloadSpec(name="hot_set", num_queries=10_000, seed=12, working_set_fraction=0.01)),
	]

	cfg = RunConfig(n=n, Z=Z, alphas=alphas, padding_x=padding_x, rng_seed=42)

	for name, spec in patterns:
		if name == "uniform":
			qvals = make_uniform_distinct(all_values, spec)
		elif name == "zipf_like":
			qvals = make_zipf_like_distinct(all_values, value_counts, spec)
		else:
			qvals = make_hot_set_distinct(all_values, value_counts, spec)

		ts = evaluate_over_time(ds.index, value_counts, qvals, cfg)

		# print last checkpoint summary (end-of-experiment success)
		print(f"\n=== Pattern: {name} ===")
		for alpha in alphas:
			points = ts.series[alpha]
			t, qrsr, drsr = points[-1]
			print(f"alpha={alpha:2d}  t={t:5d}  QRSR={qrsr:.3f}  DRSR={drsr:.3f}")

		# ---- Extension 2: confidence over time (plots) ----
		plot_success_over_time(
			ts.series,
			title=f"{name}: QRSR vs queries (padding_x={padding_x})",
			out_path=f"qrsr_{name}.png",
			metric="qrsr",
		)
		plot_success_over_time(
			ts.series,
			title=f"{name}: DRSR vs queries (padding_x={padding_x})",
			out_path=f"drsr_{name}.png",
			metric="drsr",
		)

	print("\nSaved plots: qrsr_*.png and drsr_*.png")

if __name__ == "__main__":
	main()
