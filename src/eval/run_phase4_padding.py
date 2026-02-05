# src/eval/run_phase4_padding.py
from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from src.workload.synthetic import make_zipf_dataset
from src.eval.workloads import WorkloadSpec, make_uniform_distinct
from src.eval.padding_eval import evaluate_padding_sweep
from src.eval.phase3_runner import RunConfig, evaluate_over_time
from src.eval.plotting import plot_success_over_time

import matplotlib.pyplot as plt

def plot_success_vs_alpha(rows, metric: str, out_path: str, title: str):
	# rows: list of PaddingEvalRow
	# build x -> [(alpha, metric)]
	by_x: Dict[Optional[int], List[Tuple[int, float]]] = defaultdict(list)
	for r in rows:
		val = r.qrsr if metric == "qrsr" else r.drsr
		by_x[r.x].append((r.alpha, val))

	plt.figure()
	for x, pts in sorted(by_x.items(), key=lambda kv: (-1 if kv[0] is None else kv[0])):
		pts_sorted = sorted(pts, key=lambda p: p[0])
		xs = [p[0] for p in pts_sorted]
		ys = [p[1] for p in pts_sorted]
		label = "x=None" if x is None else f"x={x}"
		plt.plot(xs, ys, marker="o", label=label)

	plt.ylim(0.0, 1.0)
	plt.xlabel("alpha")
	plt.ylabel(metric.upper())
	plt.title(title)
	plt.legend()
	plt.tight_layout()
	plt.savefig(out_path)
	plt.close()

def plot_overhead(rows, out_path: str, title: str):
	# overhead vs x (averaged over alpha)
	from statistics import mean

	by_x: Dict[Optional[int], List[float]] = defaultdict(list)
	for r in rows:
		by_x[r.x].append(r.overhead_factor)

	xs = []
	ys = []
	for x in sorted(by_x.keys(), key=lambda v: -1 if v is None else v):
		xs.append(-1 if x is None else x)
		ys.append(mean(by_x[x]))

	plt.figure()
	plt.plot(xs, ys, marker="o")
	plt.xlabel("padding x (None shown as -1)")
	plt.ylabel("avg overhead factor (padded/real)")
	plt.title(title)
	plt.tight_layout()
	plt.savefig(out_path)
	plt.close()

def main():
	n = 1 << 14
	Z = 4

	# Dataset
	ds = make_zipf_dataset(n=n, vocab=2048, a=1.2, seed=1)
	counts = ds.value_counts()
	all_values = list(ds.index.keys())

	# Workload: uniform distinct queries (baseline)
	spec = WorkloadSpec(name="uniform", num_queries=10_000, seed=0)
	qvals = make_uniform_distinct(all_values, spec)

	# Sweep settings
	alphas = [0, 1, 2, 3, 4, 5]
	xs: List[Optional[int]] = [None, 2, 4, 8, 16]

	# 1) End-of-run metrics vs (alpha, x)
	rows = evaluate_padding_sweep(
		dataset_index=ds.index,
		value_counts=counts,
		query_values_in_order=qvals,
		n=n,
		Z=Z,
		alphas=alphas,
		xs=xs,
		rng_seed=42,
	)

	# Print a readable table
	print("\n=== Phase 4: Padding Sweep (uniform distinct queries) ===")
	for r in sorted(rows, key=lambda rr: (rr.x is None, rr.x if rr.x is not None else -1, rr.alpha)):
		xlab = "None" if r.x is None else str(r.x)
		print(
			f"x={xlab:>4}  alpha={r.alpha:2d}  "
			f"QRSR={r.qrsr:.3f}  DRSR={r.drsr:.3f}  "
			f"avg_real={r.avg_real_vol:7.2f}  avg_padded={r.avg_padded_vol:7.2f}  "
			f"overhead={r.overhead_factor:6.2f}x"
		)

	# Plots: success vs alpha for each padding x
	plot_success_vs_alpha(
		rows, metric="qrsr",
		out_path="phase4_qrsr_vs_alpha.png",
		title="Phase 4: QRSR vs alpha for different padding x"
	)
	plot_success_vs_alpha(
		rows, metric="drsr",
		out_path="phase4_drsr_vs_alpha.png",
		title="Phase 4: DRSR vs alpha for different padding x"
	)
	plot_overhead(
		rows,
		out_path="phase4_overhead_vs_x.png",
		title="Phase 4: Padding overhead vs x (avg over alpha)"
	)

	# 2) Extension 2 style: “confidence over time” WITH padding (optional but valuable)
	#    Pick a single x to show attacker success vs query count at multiple alphas.
	x_focus = 4
	cfg = RunConfig(n=n, Z=Z, alphas=alphas, padding_x=x_focus, rng_seed=42)
	ts = evaluate_over_time(ds.index, counts, qvals, cfg)

	plot_success_over_time(
		ts.series,
		title=f"Phase 4: QRSR over time (padding x={x_focus})",
		out_path="phase4_qrsr_over_time_x4.png",
		metric="qrsr",
	)
	plot_success_over_time(
		ts.series,
		title=f"Phase 4: DRSR over time (padding x={x_focus})",
		out_path="phase4_drsr_over_time_x4.png",
		metric="drsr",
	)

	print("\nSaved plots:")
	print("  phase4_qrsr_vs_alpha.png")
	print("  phase4_drsr_vs_alpha.png")
	print("  phase4_overhead_vs_x.png")
	print("  phase4_qrsr_over_time_x4.png")
	print("  phase4_drsr_over_time_x4.png")

if __name__ == "__main__":
	main()
