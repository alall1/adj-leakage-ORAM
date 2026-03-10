# src/eval/replot_padding_overhead.py
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt


def _load_rows(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("padding_sweep.json expected to be a list of rows")
    return data


def _normalize_x(x_val: Any) -> Optional[int]:
    if x_val is None:
        return None
    return int(x_val)


def _x_sort_key(x: Optional[int]) -> int:
    # Put None (no padding) first, then ascending numeric x
    return -1 if x is None else x


def _categorical_axis(xs: List[Optional[int]]) -> Tuple[List[int], List[str]]:
    positions = list(range(len(xs)))
    labels = ["None" if x is None else str(x) for x in xs]
    return positions, labels


def plot_overhead_vs_x_avg(rows: List[Dict[str, Any]], out_path: str, title: str) -> None:
    """
    Plot overhead_factor vs x, averaged over alpha.
    """
    xs = sorted({_normalize_x(r["x"]) for r in rows}, key=_x_sort_key)
    alphas = sorted({int(r["alpha"]) for r in rows})

    # Lookup (alpha, x) -> overhead
    lookup: Dict[Tuple[int, Optional[int]], float] = {}
    for r in rows:
        a = int(r["alpha"])
        x = _normalize_x(r["x"])
        lookup[(a, x)] = float(r["overhead_factor"])

    # Average over alphas for each x
    avg_overhead = []
    for x in xs:
        vals = [lookup[(a, x)] for a in alphas if (a, x) in lookup]
        avg_overhead.append(sum(vals) / len(vals) if vals else float("nan"))

    xpos, xlabels = _categorical_axis(xs)

    plt.figure()
    plt.plot(xpos, avg_overhead, marker="o")
    plt.xticks(xpos, xlabels)
    plt.xlabel("padding base x (None = no padding)")
    plt.ylabel("avg overhead factor (padded/real)")
    plt.title(title)

    # dynamic y-scale (overhead is >=1, not clamped)
    finite = [v for v in avg_overhead if v == v]
    if finite:
        y_min = min(finite)
        y_max = max(finite)
        if abs(y_max - y_min) < 1e-9:
            pad = max(0.1, 0.05 * y_max)
        else:
            pad = max(0.1, 0.1 * (y_max - y_min))
        lower = max(0.0, y_min - pad)
        upper = y_max + pad
        if upper <= lower:
            upper = lower + 0.2
        plt.ylim(lower, upper)

    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def plot_overhead_vs_x_by_alpha(rows: List[Dict[str, Any]], out_path: str, title: str) -> None:
    """
    Plot overhead_factor vs x with one curve per alpha.
    """
    xs = sorted({_normalize_x(r["x"]) for r in rows}, key=_x_sort_key)
    alphas = sorted({int(r["alpha"]) for r in rows})

    lookup: Dict[Tuple[int, Optional[int]], float] = {}
    for r in rows:
        a = int(r["alpha"])
        x = _normalize_x(r["x"])
        lookup[(a, x)] = float(r["overhead_factor"])

    xpos, xlabels = _categorical_axis(xs)

    plt.figure()
    all_y: List[float] = []

    for a in alphas:
        ys = []
        for x in xs:
            val = lookup.get((a, x), float("nan"))
            ys.append(val)
            if val == val:
                all_y.append(val)
        plt.plot(xpos, ys, marker="o", label=f"alpha={a}")

    plt.xticks(xpos, xlabels)
    plt.xlabel("padding base x (None = no padding)")
    plt.ylabel("overhead factor (padded/real)")
    plt.title(title)
    plt.legend()

    # dynamic y-scale (not clamped)
    if all_y:
        y_min = min(all_y)
        y_max = max(all_y)
        if abs(y_max - y_min) < 1e-9:
            pad = max(0.1, 0.05 * y_max)
        else:
            pad = max(0.1, 0.1 * (y_max - y_min))
        lower = max(0.0, y_min - pad)
        upper = y_max + pad
        if upper <= lower:
            upper = lower + 0.2
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

    rows = _load_rows(padding_json)

    out_avg = os.path.join(plots_dir, "padding_overhead_vs_x.png")
    out_by_alpha = os.path.join(plots_dir, "padding_overhead_vs_x_by_alpha.png")

    plot_overhead_vs_x_avg(
        rows,
        out_path=out_avg,
        title="Padding overhead vs x (avg over alpha)",
    )
    plot_overhead_vs_x_by_alpha(
        rows,
        out_path=out_by_alpha,
        title="Padding overhead vs x (by alpha)",
    )

    print(f"Wrote {out_avg}")
    print(f"Wrote {out_by_alpha}")


def main() -> None:
    # Update these to match your actual run directories if needed.
    run_dirs = [
        os.path.join("out", "light_seed1"),
        os.path.join("out", "light_seed2"),
        os.path.join("out", "light_seed3"),
    ]

    for rd in run_dirs:
        replot_one_run(rd)

    print("\nDone. Added padding overhead plots to each run's plots/ folder.")


if __name__ == "__main__":
    main()
