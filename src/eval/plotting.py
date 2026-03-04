# src/eval/plotting.py
from __future__ import annotations
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt

def plot_success_over_time(
    series: Dict[int, List[Tuple[int, float, float]]],
    title: str,
    out_path: str,
    metric: str = "qrsr",   # or "drsr"
    zoom: bool = True,
    margin: float = 0.01,
) -> None:
    """
    series: alpha -> [(t, qrsr, drsr), ...]
    If zoom=True, y-axis is tightened around the plotted values.
    """
    plt.figure()

    all_y = []

    for alpha, points in series.items():
        xs = [p[0] for p in points]
        ys = [p[1] for p in points] if metric == "qrsr" else [p[2] for p in points]
        all_y.extend(ys)
        plt.plot(xs, ys, marker="o", label=f"alpha={alpha}")

    plt.xscale("log")
    plt.xlabel("number of (distinct) queries observed")
    plt.ylabel(metric.upper())
    plt.title(title)
    plt.legend()

    if all_y:
        if zoom:
            y_min = min(all_y)
            y_max = max(all_y)

            # If values are nearly constant, still give a visible window
            if abs(y_max - y_min) < 1e-6:
                pad = 0.01
            else:
                pad = max(margin, 0.1 * (y_max - y_min))

            lower = max(0.0, y_min - pad)
            upper = min(1.0, y_max + pad)

            # Prevent identical bounds
            if upper <= lower:
                upper = min(1.0, lower + 0.02)

            plt.ylim(lower, upper)
        else:
            plt.ylim(0.0, 1.0)

    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
