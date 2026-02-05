# src/eval/plotting.py
from __future__ import annotations
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt

def plot_success_over_time(
	series: Dict[int, List[Tuple[int, float, float]]],
	title: str,
	out_path: str,
	metric: str = "qrsr",  # or "drsr"
) -> None:
	plt.figure()
	for alpha, points in series.items():
		xs = [p[0] for p in points]
		ys = [p[1] for p in points] if metric == "qrsr" else [p[2] for p in points]
		plt.plot(xs, ys, marker="o", label=f"alpha={alpha}")
	plt.xscale("log")
	plt.ylim(0.0, 1.0)
	plt.xlabel("number of (distinct) queries observed")
	plt.ylabel(metric.upper())
	plt.title(title)
	plt.legend()
	plt.tight_layout()
	plt.savefig(out_path)
	plt.close()
