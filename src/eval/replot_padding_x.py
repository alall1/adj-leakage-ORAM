# src/eval/replot_padding_x.py
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt


def _load_padding_rows(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # data is expected to be a list of dicts:
    # {alpha, x, qrsr, drsr, overhead_factor, ...}
    if not isinstance(data, list):
        raise ValueError("padding_sweep.json expected to be a list")
    return data


def _normalize_x(x_val: Any) -> Optional[int]:
    # JSON uses null for None, numbers for ints
    if x_val is None:
        return None
    return int(x_val)


def _x_sort_key(x: Optional[int]) -> int:
    # Put None first (no padding), then numeric ascending
    return -1 if x is None else x


def plot_metric_vs_padding_x(
    rows: List[Dict[str, Any]],
    metric: str,  # "drsr" or "qrsr"
    out_path: str,
    title: str,
) -> None:
    """
    Plots metric vs padding parameter x.
    One line per alpha.
    X-axis is categorical: None, 2, 4, 8, 16, ...
    """
    # Collect unique alphas and x values
    alphas = sorted({int(r["alpha"]) for r in rows})
    xs = sorted({_normalize_x(r["x"]) for r in rows}, key=_x_sort_key)

    # Build a lookup: (alpha, x) -> metric value
    lookup: Dict[Tuple[int, Optional[int]], float] = {}
    for r in rows:
        a = int(r["alpha"])
        x = _normalize_x(r["x"])
        lookup[(a, x)] = float(r[metric])

    # X positions for categorical axis
    x_positions = list(range(len(xs)))
    x_labels = ["None" if x is None else str(x) for x in xs]

    plt.figure()
    all_y: List[float] = []

    for a in alphas:
        ys = []
        for x in xs:
            val = lookup.get((a, x), None)
            if val is None:
                ys.append(float("nan"))
            else:
                ys.append(val)
                all_y.append(val)
        plt.plot(x_positions, ys, marker="o", label=f"alpha={a}")

    plt.xticks(x_positions, x_labels)
    plt.xlabel("padding base x (None = no padding)")
    plt.ylabel(metric.upper())
    plt.title(title)
    plt.legend()

    # Dynamic y zoom (clamped to [0,1])
    if all_y:
        y_min = min(all_y)
        y_max = max(all_y)
        if abs(y_max - y_min) < 1e-9:
            pad = 0.01
        else:
            pad = max(0.01, 0.15 * (y_max - y_min))
        lower = max(0.0, y_min - pad)
        upper = min(1.0, y_max + pad)
        if upper <= lower:
            upper = min(1.0, lower + 0.02)
        plt.ylim(lower, upper)

    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def replot_one_run(run_dir: str) -> None:
    results_dir = os.path.join(run_dir, "results")
    plots_dir = os.path.join(run_dir, "plots")
    padding_json = os.path.join(results_dir, "padding_sweep.json")

    if not os.path.exists(padding_json):
        print(f"Skipping {run_dir}: missing results/padding_sweep.json")
        return
    if not os.path.isdir(plots_dir):
        print(f"Skipping {run_dir}: missing plots/ directory")
        return

    rows = _load_padding_rows(padding_json)

    out_drsr = os.path.join(plots_dir, "drsr_vs_padding_x.png")
    plot_metric_vs_padding_x(
        rows,
        metric="drsr",
        out_path=out_drsr,
        title="DRSR vs padding base x (one curve per alpha)",
    )
    print(f"Wrote {out_drsr}")

    out_qrsr = os.path.join(plots_dir, "qrsr_vs_padding_x.png")
    plot_metric_vs_padding_x(
        rows,
        metric="qrsr",
        out_path=out_qrsr,
        title="QRSR vs padding base x (one curve per alpha)",
    )
    print(f"Wrote {out_qrsr}")


def main() -> None:
    # Update these names to match your run folders exactly.
    run_dirs = [
        os.path.join("out", "light_seed1"),
        os.path.join("out", "light_seed2"),
        os.path.join("out", "light_seed3"),
    ]

    for rd in run_dirs:
        replot_one_run(rd)

    print("\nDone. Added drsr_vs_padding_x.png (and qrsr_vs_padding_x.png) to each run's plots/ folder.")


if __name__ == "__main__":
    main()
