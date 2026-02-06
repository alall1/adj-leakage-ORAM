# src/eval/master_runner.py
from __future__ import annotations
import json
import os
from dataclasses import asdict
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt

from src.eval.io_utils import ensure_dir, write_json, write_csv
from src.eval.perf_runner import PerfConfig, run_perf_path_oram, run_perf_seal

from src.workload.synthetic import make_zipf_dataset
from src.eval.workloads import WorkloadSpec, make_uniform_distinct, make_zipf_like_distinct, make_hot_set_distinct
from src.eval.phase3_runner import RunConfig, evaluate_over_time
from src.eval.padding_eval import evaluate_padding_sweep
from src.eval.plotting import plot_success_over_time

from src.eval.sessions import SessionPlan, sample_sessions
from src.eval.session_eval import evaluate_sessions
from src.seal.seal_client import SealClient
from src.workload.leakage_oracle import SealLeakageOracle
from src.workload.path_oram_oracle import PathOramLeakageOracle

def _load_config(path: str) -> Dict[str, Any]:
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)

def _make_queries(pattern: str, all_values: List[Any], counts: Dict[Any, int], num_queries: int, seed: int, pattern_params: Dict[str, Any]):
	spec = WorkloadSpec(
		name=pattern,
		num_queries=num_queries,
		seed=seed,
		hot_fraction=pattern_params.get("hot_fraction", 0.10),
		hot_mass=pattern_params.get("hot_mass", 0.90),
		working_set_fraction=pattern_params.get("working_set_fraction", 0.01),
	)
	if pattern == "uniform":
		return make_uniform_distinct(all_values, spec)
	if pattern == "zipf_like":
		return make_zipf_like_distinct(all_values, counts, spec)
	if pattern == "hot_set":
		return make_hot_set_distinct(all_values, counts, spec)
	raise ValueError("unknown pattern")

def _plot_perf(rows, out_png: str, title: str):
	# simple plot: alpha vs avg bandwidth bytes (separate for path/seal)
	plt.figure()
	# path row (single)
	path = [r for r in rows if r["scheme"] == "path_oram"]
	seal = [r for r in rows if r["scheme"] == "seal"]

	if path:
		y = path[0]["avg_bandwidth_bytes"]
		plt.hlines(y, xmin=min([r["alpha"] for r in seal] + [0]), xmax=max([r["alpha"] for r in seal] + [0]),
			label="Path ORAM", linestyles="--")

	seal_sorted = sorted(seal, key=lambda r: r["alpha"])
	xs = [r["alpha"] for r in seal_sorted]
	ys = [r["avg_bandwidth_bytes"] for r in seal_sorted]
	plt.plot(xs, ys, marker="o", label="SEAL")

	plt.xlabel("alpha")
	plt.ylabel("avg bandwidth (bytes)")
	plt.title(title)
	plt.legend()
	plt.tight_layout()
	plt.savefig(out_png)
	plt.close()

def run_all(config_path: str):
	cfg = _load_config(config_path)

	run_name = cfg["run_name"]
	out_root = os.path.join("out", run_name)
	ensure_dir(out_root)
	ensure_dir(os.path.join(out_root, "plots"))
	ensure_dir(os.path.join(out_root, "results"))

	# Save config snapshot
	write_json(os.path.join(out_root, "config_snapshot.json"), cfg)

	# Dataset (single source of truth for all query-based attacks)
	ds_cfg = cfg["dataset"]
	ds = make_zipf_dataset(
		n=ds_cfg["n"],
		vocab=ds_cfg["vocab"],
		a=ds_cfg["zipf_a"],
		seed=ds_cfg["seed"],
	)
	counts = ds.value_counts()
	all_values = list(ds.index.keys())

	# ------------------------------------------------------------
	# 1) Performance experiments (actual ORAM accesses)
	# ------------------------------------------------------------
	if cfg["toggles"].get("perf", True):
		perf_cfg = cfg["perf"]
		patterns = perf_cfg["patterns"]
		alphas = perf_cfg["alphas"]

		for pattern in patterns:
			pc = PerfConfig(
				n=perf_cfg["n"],
				Z=perf_cfg["Z"],
				alphas=alphas,
				num_ops=perf_cfg["num_ops"],
				read_fraction=perf_cfg["read_fraction"],
				block_size_bytes=perf_cfg["block_size_bytes"],
				seed=perf_cfg["seed"],
				pattern=pattern,
				hot_fraction=perf_cfg.get("hot_fraction", 0.10),
				hot_mass=perf_cfg.get("hot_mass", 0.90),
				working_set_fraction=perf_cfg.get("working_set_fraction", 0.01),
			)

			rows = []
			r_path = run_perf_path_oram(pc)
			rows.append(asdict(r_path))
			for a in alphas:
				r_seal = run_perf_seal(pc, alpha=a)
				rows.append(asdict(r_seal))

			csv_path = os.path.join(out_root, "results", f"perf_{pattern}.csv")
			write_csv(csv_path, rows)

			png_path = os.path.join(out_root, "plots", f"perf_bandwidth_{pattern}.png")
			_plot_perf(rows, png_path, title=f"Avg bandwidth vs alpha ({pattern})")

	# ------------------------------------------------------------
	# 2) Attack over time (checkpoints) across patterns
	# ------------------------------------------------------------
	if cfg["toggles"].get("over_time", True):
		ot = cfg["over_time"]
		alphas = ot["alphas"]
		checkpoints = ot["checkpoints"]
		patterns = ot["patterns"]
		padding_x = ot.get("padding_x", None)

		for pattern in patterns:
			qvals = _make_queries(
				pattern, all_values, counts,
				num_queries=ot["num_queries"],
				seed=ot["seed"],
				pattern_params=ot,
			)
			rc = RunConfig(
				n=ds_cfg["n"],
				Z=ot["Z"],
				alphas=alphas,
				padding_x=padding_x,
				rng_seed=ot["seed"],
				checkpoints=type("C", (), {"points": checkpoints})(),  # tiny adapter
			)
			ts = evaluate_over_time(ds.index, counts, qvals, rc)

			# save series as json
			write_json(os.path.join(out_root, "results", f"over_time_{pattern}.json"), ts.series)

			# plots
			plot_success_over_time(
				ts.series,
				title=f"{pattern}: QRSR vs queries (padding_x={padding_x})",
				out_path=os.path.join(out_root, "plots", f"qrsr_over_time_{pattern}.png"),
				metric="qrsr",
			)
			plot_success_over_time(
				ts.series,
				title=f"{pattern}: DRSR vs queries (padding_x={padding_x})",
				out_path=os.path.join(out_root, "plots", f"drsr_over_time_{pattern}.png"),
				metric="drsr",
			)

	# ------------------------------------------------------------
	# 3) Padding sweep (security + overhead)
	# ------------------------------------------------------------
	if cfg["toggles"].get("padding_sweep", True):
		ps = cfg["padding_sweep"]
		alphas = ps["alphas"]
		xs = [None if x == "None" else int(x) for x in ps["xs"]]
		pattern = ps["pattern"]

		qvals = _make_queries(
			pattern, all_values, counts,
			num_queries=ps["num_queries"],
			seed=ps["seed"],
			pattern_params=ps,
		)
		rows = evaluate_padding_sweep(
			dataset_index=ds.index,
			value_counts=counts,
			query_values_in_order=qvals,
			n=ds_cfg["n"],
			Z=ps["Z"],
			alphas=alphas,
			xs=xs,
			rng_seed=ps["seed"],
		)
		write_json(os.path.join(out_root, "results", "padding_sweep.json"), rows)

	# ------------------------------------------------------------
	# 4) Session-length reset experiment
	# ------------------------------------------------------------
	if cfg["toggles"].get("sessions", True):
		sc = cfg["sessions"]
		alphas = sc["alphas"]
		lengths = sc["session_lengths"]
		num_sessions = sc["num_sessions"]
		pattern = sc["pattern"]
		padding_x = sc.get("padding_x", None)

		baseline_oracle = PathOramLeakageOracle(dataset_index=ds.index, constant_volume=1, padding_x=padding_x)

		out_rows = []
		for L in lengths:
			plan = SessionPlan(
				num_sessions=num_sessions,
				session_length=L,
				pattern=pattern,
				seed=sc["seed"],
				hot_fraction=sc.get("hot_fraction", 0.10),
				hot_mass=sc.get("hot_mass", 0.90),
				working_set_fraction=sc.get("working_set_fraction", 0.01),
			)
			sessions = sample_sessions(all_values, counts, plan)

			# baseline stats
			bstats = evaluate_sessions(
				oracle=baseline_oracle,
				value_counts=counts,
				encrypted_tuples=None,
				sessions=sessions,
				padding_x=padding_x,
				base_seed=sc["seed"],
			)
			out_rows.append({"scheme": "path_oram_baseline", "alpha": 0, "L": L, **asdict(bstats)})

			# seal stats per alpha
			for a in alphas:
				seal = SealClient(n=ds_cfg["n"], Z=sc["Z"], alpha=a, default_value=0)
				oracle = SealLeakageOracle(seal=seal, dataset_index=ds.index, padding_x=padding_x, rng_seed=sc["seed"])
				encT = oracle.build_encrypted_tuples()
				sstats = evaluate_sessions(
					oracle=oracle,
					value_counts=counts,
					encrypted_tuples=encT,
					sessions=sessions,
					padding_x=padding_x,
					base_seed=sc["seed"],
				)
				out_rows.append({"scheme": "seal", "alpha": a, "L": L, **asdict(sstats)})

			print(f"Sessions done for L={L}")

		write_csv(os.path.join(out_root, "results", "sessions.csv"), out_rows)

	# Summary marker
	with open(os.path.join(out_root, "summary.txt"), "w", encoding="utf-8") as f:
		f.write("Run complete.\n")
		f.write("See results/ and plots/.\n")

	print(f"\nAll done. Outputs in: {out_root}")

if __name__ == "__main__":
	run_all("configs/master.json")
