# src/eval/run_session_length.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt

from src.workload.synthetic import make_zipf_dataset
from src.seal.seal_client import SealClient
from src.workload.leakage_oracle import SealLeakageOracle
from src.workload.path_oram_oracle import PathOramLeakageOracle

from src.eval.sessions import SessionPlan, sample_sessions
from src.eval.session_eval import evaluate_sessions

@dataclass(frozen=True)
class SessionExperimentConfig:
	n: int
	Z: int
	alphas: List[int]
	session_lengths: List[int]
	num_sessions: int
	pattern: str                 # "uniform" | "zipf_like" | "hot_set"
	padding_x: Optional[int] = None
	seed: int = 0

def plot_metric_vs_length(results_by_alpha, lengths, metric: str, title: str, out_path: str, include_baseline=None):
	plt.figure()
	for alpha, stats in results_by_alpha.items():
		ys = [getattr(stats[L], metric) for L in lengths]
		plt.plot(lengths, ys, marker="o", label=f"alpha={alpha}")

	if include_baseline is not None:
		ys = [getattr(include_baseline[L], metric) for L in lengths]
		plt.plot(lengths, ys, marker="o", linestyle="--", label="Path ORAM baseline")

	plt.xscale("log")
	plt.ylim(0.0, 1.0)
	plt.xlabel("session length (distinct queries)")
	plt.ylabel(metric.upper())
	plt.title(title)
	plt.legend()
	plt.tight_layout()
	plt.savefig(out_path)
	plt.close()

def main():
	cfg = SessionExperimentConfig(
		n=1 << 14,
		Z=4,
		alphas=[0, 1, 2, 3, 4, 5],
		session_lengths=[10, 50, 100, 500, 1000],
		num_sessions=200,
		pattern="zipf_like",   # change to "uniform" or "hot_set"
		padding_x=None,
		seed=7,
	)

	ds = make_zipf_dataset(n=cfg.n, vocab=2048, a=1.2, seed=1)
	counts = ds.value_counts()
	all_values = list(ds.index.keys())

	# Baseline oracle (Path ORAM leakage-free model)
	baseline_oracle = PathOramLeakageOracle(dataset_index=ds.index, constant_volume=1, padding_x=cfg.padding_x)

	baseline_stats_by_L = {}

	# SEAL results: alpha -> L -> SessionStats
	results = {}

	for L in cfg.session_lengths:
		plan = SessionPlan(
			num_sessions=cfg.num_sessions,
			session_length=L,
			pattern=cfg.pattern,
			seed=cfg.seed,
			hot_fraction=0.10,
			hot_mass=0.90,
			working_set_fraction=0.01,
		)
		sessions = sample_sessions(all_values, counts, plan)

		# Evaluate baseline once per L (doesn't depend on alpha)
		bstats = evaluate_sessions(
			oracle=baseline_oracle,
			value_counts=counts,
			encrypted_tuples=None,
			sessions=sessions,
			padding_x=cfg.padding_x,
			base_seed=cfg.seed,
		)
		baseline_stats_by_L[L] = bstats

		for alpha in cfg.alphas:
			seal = SealClient(n=cfg.n, Z=cfg.Z, alpha=alpha, default_value=0)
			oracle = SealLeakageOracle(seal=seal, dataset_index=ds.index, padding_x=cfg.padding_x, rng_seed=cfg.seed)
			
			encT = oracle.build_encrypted_tuples()

			stats = evaluate_sessions(
				oracle=oracle,
				value_counts=counts,
				encrypted_tuples=encT,
				sessions=sessions,
				padding_x=cfg.padding_x,
				base_seed=cfg.seed,
			)

			results.setdefault(alpha, {})[L] = stats

		print(f"Done L={L}")

	# Print a readable summary
	print("\n=== Session-length summary (means) ===")
	for alpha in cfg.alphas:
		print(f"\nalpha={alpha}")
		for L in cfg.session_lengths:
			s = results[alpha][L]
			print(f"  L={L:5d}  QRSR={s.qrsr_mean:.3f}  DRSR={s.drsr_mean:.3f}")

	# Plots
	plot_metric_vs_length(
		results_by_alpha=results,
		lengths=cfg.session_lengths,
		metric="qrsr_mean",
		title=f"QRSR vs session length ({cfg.pattern}, padding_x={cfg.padding_x})",
		out_path="session_qrsr_vs_length.png",
		include_baseline=baseline_stats_by_L,
	)
	plot_metric_vs_length(
		results_by_alpha=results,
		lengths=cfg.session_lengths,
		metric="drsr_mean",
		title=f"DRSR vs session length ({cfg.pattern}, padding_x={cfg.padding_x})",
		out_path="session_drsr_vs_length.png",
		include_baseline=baseline_stats_by_L,
	)

	print("\nSaved plots:")
	print("  session_qrsr_vs_length.png")
	print("  session_drsr_vs_length.png")

if __name__ == "__main__":
	main()
