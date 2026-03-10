# src/eval/replot_sessions_length.py
from __future__ import annotations

import csv
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt


def _load_sessions_rows(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _dynamic_ylim_01(vals: List[float]) -> None:
    """Zoom y-axis around values but clamp to [0,1]."""
    vals = [v for v in vals if v == v]  # drop NaNs
    if not vals:
        plt.ylim(0.0, 1.0)
        return
    y_min = min(vals)
    y_max = max(vals)
    if abs(y_max - y_min) < 1e-9:
        pad = 0.01
    else:
        pad = max(0.01, 0.15 * (y_max - y_min))
    lower = max(0.0, y_min - pad)
    upper = min(1.0, y_max + pad)
    if upper <= lower:
        upper = min(1.0, lower + 0.02)
    plt.ylim(lower, upper)


def plot_sessions_metric(
    rows: List[Dict[str, Any]],
    metric: str,        # "qrsr_mean" or "drsr_mean"
    out_path: str,
    title: str
) -> None:
    """
    rows expected columns:
      scheme, alpha, L, qrsr_mean, qrsr_std, drsr_mean, drsr_std
    """
    # Parse and group: scheme -> alpha -> {L: metric}
    seal_map: Dict[int, Dict[int, float]] = defaultdict(dict)
    baseline_map: Dict[int, float] = {}

    all_L = set()
    all_y = []

    for r in rows:
        scheme = r["scheme"]
        alpha = int(r["alpha"])
        L = int(r["L"])
        val = float(r[metric])

        all_L.add(L)

        if scheme == "seal":
            seal_map[alpha][L] = val
            all_y.append(val)
        else:
            # path_oram_baseline (or any non-seal scheme)
            baseline_map[L] = val
            all_y.append(val)

    lengths = sorted(all_L)

    plt.figure()

    # Plot SEAL curves
    for alpha in sorted(seal_map.keys()):
        ys = [seal_map[alpha].get(L, float("nan")) for L in lengths]
        plt.plot(lengths, ys, marker="o", label=f"alpha={alpha}")

    # Plot baseline if present
    if baseline_map:
        ys = [baseline_map.get(L, float("nan")) for L in lengths]
        plt.plot(lengths, ys, marker="o", linestyle="--", label="Path ORAM baseline")

    plt.xscale("log")
    plt.xlabel("session length L (distinct queries)")
    plt.ylabel(metric.upper())
    plt.title(title)
    plt.legend()
    _dynamic_ylim_01(all_y)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def replot_one_run(run_dir: str) -> None:
    results_dir = os.path.join(run_dir, "results")
    plots_dir = os.path.join(run_dir, "plots")
    sessions_csv = os.path.join(results_dir, "sessions.csv")

    if not os.path.exists(sessions_csv):
        print(f"Skipping {run_dir}: missing results/sessions.csv")
        return
    if not os.path.isdir(plots_dir):
        print(f"Skipping {run_dir}: missing plots/ directory")
        return

    rows = _load_sessions_rows(sessions_csv)

    out_q = os.path.join(plots_dir, "sessions_qrsr_vs_L.png")
    out_d = os.path.join(plots_dir, "sessions_drsr_vs_L.png")

    plot_sessions_metric(
        rows,
        metric="qrsr_mean",
        out_path=out_q,
        title="Session-reset: QRSR vs session length L"
    )
    plot_sessions_metric(
        rows,
        metric="drsr_mean",
        out_path=out_d,
        title="Session-reset: DRSR vs session length L"
    )

    print(f"Wrote {out_q}")
    print(f"Wrote {out_d}")


def main() -> None:
    # Update these if your folder names differ.
    run_dirs = [
        os.path.join("out", "light_seed1"),
        os.path.join("out", "light_seed2"),
        os.path.join("out", "light_seed3"),
    ]

    for rd in run_dirs:
        replot_one_run(rd)

    print("\nDone. Added session-length plots to each run's plots/ folder.")


if __name__ == "__main__":
    main()
