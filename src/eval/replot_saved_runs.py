# src/eval/replot_saved_runs.py
from __future__ import annotations

import csv
import json
import os
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _load_csv_rows(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def _apply_dynamic_ylim(all_y: List[float], margin: float = 0.01) -> None:
    """
    Tighten y-axis around the data while staying inside [0,1].
    """
    if not all_y:
        plt.ylim(0.0, 1.0)
        return

    y_min = min(all_y)
    y_max = max(all_y)

    if abs(y_max - y_min) < 1e-9:
        pad = 0.01
    else:
        pad = max(margin, 0.1 * (y_max - y_min))

    lower = max(0.0, y_min - pad)
    upper = min(1.0, y_max + pad)

    if upper <= lower:
        upper = min(1.0, lower + 0.02)

    plt.ylim(lower, upper)


# ---------------------------------------------------------------------
# Over-time plots (QRSR / DRSR)
# ---------------------------------------------------------------------

def replot_over_time(json_path: str, out_path: str, metric: str, title: str) -> None:
    """
    Recreate QRSR/DRSR-over-time plots from saved over_time_*.json.
    Expected JSON format:
      {
        "0": [[10, qrsr, drsr], [100, qrsr, drsr], ...],
        "1": [[10, qrsr, drsr], ...],
        ...
      }
    """
    series = _load_json(json_path)

    plt.figure()
    all_y: List[float] = []

    # sort alpha numerically, even though JSON keys are strings
    for alpha_str in sorted(series.keys(), key=lambda x: int(x)):
        points = series[alpha_str]
        xs = [int(p[0]) for p in points]
        ys = [float(p[1]) for p in points] if metric == "qrsr" else [float(p[2]) for p in points]

        all_y.extend(ys)
        plt.plot(xs, ys, marker="o", label=f"alpha={alpha_str}")

    plt.xscale("log")
    plt.xlabel("number of (distinct) queries observed")
    plt.ylabel(metric.upper())
    plt.title(title)
    plt.legend()
    _apply_dynamic_ylim(all_y)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


# ---------------------------------------------------------------------
# Performance bandwidth plots
# ---------------------------------------------------------------------

def replot_perf_bandwidth(csv_path: str, out_path: str, title: str) -> None:
    """
    Recreate perf_bandwidth_*.png from saved perf_*.csv.
    Expected CSV columns include:
      scheme, alpha, avg_bandwidth_bytes
    """
    rows = _load_csv_rows(csv_path)

    path_rows = [r for r in rows if r["scheme"] == "path_oram"]
    seal_rows = [r for r in rows if r["scheme"] == "seal"]

    plt.figure()
    all_y: List[float] = []

    # Path ORAM baseline (horizontal line)
    if path_rows:
        path_bw = float(path_rows[0]["avg_bandwidth_bytes"])
        all_y.append(path_bw)

        alphas_for_bounds = [int(r["alpha"]) for r in seal_rows] if seal_rows else [0]
        xmin = min(alphas_for_bounds)
        xmax = max(alphas_for_bounds)

        plt.hlines(
            path_bw,
            xmin=xmin,
            xmax=xmax,
            linestyles="--",
            label="Path ORAM"
        )

    # SEAL curve
    seal_sorted = sorted(seal_rows, key=lambda r: int(r["alpha"]))
    xs = [int(r["alpha"]) for r in seal_sorted]
    ys = [float(r["avg_bandwidth_bytes"]) for r in seal_sorted]

    if xs and ys:
        all_y.extend(ys)
        plt.plot(xs, ys, marker="o", label="SEAL")

    plt.xlabel("alpha")
    plt.ylabel("avg bandwidth (bytes)")
    plt.title(title)
    plt.legend()

    # Dynamic y scaling for perf too (not clamped to [0,1])
    if all_y:
        y_min = min(all_y)
        y_max = max(all_y)
        if abs(y_max - y_min) < 1e-9:
            pad = max(1.0, 0.05 * y_max if y_max > 0 else 1.0)
        else:
            pad = max(1.0, 0.1 * (y_max - y_min))
        lower = max(0.0, y_min - pad)
        upper = y_max + pad
        if upper <= lower:
            upper = lower + 1.0
        plt.ylim(lower, upper)

    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


# ---------------------------------------------------------------------
# Run-folder driver
# ---------------------------------------------------------------------

def replot_run(run_dir: str) -> None:
    results_dir = os.path.join(run_dir, "results")
    plots_dir = os.path.join(run_dir, "plots")

    if not os.path.isdir(results_dir):
        print(f"Skipping {run_dir}: no results/ directory")
        return
    if not os.path.isdir(plots_dir):
        print(f"Skipping {run_dir}: no plots/ directory")
        return

    patterns = ["uniform", "zipf_like", "hot_set"]

    for pattern in patterns:
        # over_time JSON -> qrsr/drsr plots
        json_path = os.path.join(results_dir, f"over_time_{pattern}.json")
        if os.path.exists(json_path):
            qrsr_out = os.path.join(plots_dir, f"qrsr_over_time_{pattern}.png")
            drsr_out = os.path.join(plots_dir, f"drsr_over_time_{pattern}.png")

            replot_over_time(
                json_path=json_path,
                out_path=qrsr_out,
                metric="qrsr",
                title=f"{pattern}: QRSR vs queries (zoomed)"
            )
            replot_over_time(
                json_path=json_path,
                out_path=drsr_out,
                metric="drsr",
                title=f"{pattern}: DRSR vs queries (zoomed)"
            )
            print(f"Replotted over-time plots for {run_dir} / {pattern}")
        else:
            print(f"Missing {json_path}")

        # perf CSV -> perf bandwidth plot
        csv_path = os.path.join(results_dir, f"perf_{pattern}.csv")
        perf_out = os.path.join(plots_dir, f"perf_bandwidth_{pattern}.png")
        if os.path.exists(csv_path):
            replot_perf_bandwidth(
                csv_path=csv_path,
                out_path=perf_out,
                title=f"Avg bandwidth vs alpha ({pattern}, zoomed)"
            )
            print(f"Replotted perf plot for {run_dir} / {pattern}")
        else:
            print(f"Missing {csv_path}")


def main() -> None:
    # Change these if your run folder names differ.
    run_dirs = [
        os.path.join("out", "light_seed1"),
        os.path.join("out", "light_seed2"),
        os.path.join("out", "light_seed3"),
    ]

    for run_dir in run_dirs:
        replot_run(run_dir)

    print("\nDone. Existing plot PNGs have been replaced with zoomed versions.")


if __name__ == "__main__":
    main()
