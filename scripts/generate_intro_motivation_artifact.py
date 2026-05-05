#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _find_row_by_n(rows: list[dict[str, str]], n: int) -> dict[str, str]:
    for r in rows:
        if int(r["n"]) == n:
            return r
    raise ValueError(f"n={n} not found in CSV.")


def _box(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    face: str,
    edge: str = "#303030",
    linestyle: str = "-",
) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            linewidth=1.4,
            edgecolor=edge,
            linestyle=linestyle,
            facecolor=face,
        )
    )
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=13.0,
        fontweight="semibold",
        color="#111111",
    )


def _arrow(ax, x0: float, y0: float, x1: float, y1: float) -> None:
    ax.add_patch(
        FancyArrowPatch(
            (x0, y0),
            (x1, y1),
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=1.0,
            color="#404040",
        )
    )


def _panel_architecture(ax) -> None:
    ax.set_title("(a) Architectural idea", fontsize=16)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    y_baseline = 0.62
    y_folded = 0.22
    h = 0.145
    w = 0.15
    x0 = 0.095
    gap = 0.03
    xs = [x0 + i * (w + gap) for i in range(5)]

    top_labels = [
        "Inputs",
        "CSA for HW",
        "Comparator\nadder (-Th)",
        "Final carry\n(decision bit)",
        "Output",
    ]
    top_colors = ["#eef2ff", "#dbeafe", "#fde68a", "#c7f9cc", "#ecfccb"]
    for i in range(5):
        _box(ax, xs[i], y_baseline, w, h, top_labels[i], top_colors[i])
    for i in range(4):
        _arrow(ax, xs[i] + w, y_baseline + h / 2, xs[i + 1], y_baseline + h / 2)
    ax.text(x0 - 0.02, y_baseline + h / 2, "Baseline", ha="right", va="center", fontsize=13, fontweight="bold")

    bottom_labels = {
        0: "Inputs + K\n($|K| \\less Th$)",
        1: "Folded-bias\nCSA",
        2: "No explicit\ncomparator",
        3: "Final carry\n(decision bit)",
        4: "Output",
    }
    bottom_colors = {
        0: "#eef2ff",
        1: "#d1fae5",
        2: "#f8fafc",
        3: "#a7f3d0",
        4: "#ecfccb",
    }
    for i in (0, 1, 3, 4):
        _box(ax, xs[i], y_folded, w, h, bottom_labels[i], bottom_colors[i])
    _box(
        ax,
        xs[2],
        y_folded,
        w,
        h,
        bottom_labels[2],
        bottom_colors[2],
        edge="#b91c1c",
        linestyle="--",
    )

    _arrow(ax, xs[0] + w, y_folded + h / 2, xs[1], y_folded + h / 2)
    _arrow(ax, xs[1] + w, y_folded + h / 2, xs[3], y_folded + h / 2)
    _arrow(ax, xs[3] + w, y_folded + h / 2, xs[4], y_folded + h / 2)
    ax.text(x0 - 0.02, y_folded + h / 2, "Folded-bias", ha="right", va="center", fontsize=13, fontweight="bold")

    xc = xs[2] + w / 2
    y0 = y_baseline - 0.005
    y1 = y_folded + h + 0.005
    ax.add_patch(
        FancyArrowPatch(
            (xc, y0),
            (xc, y1),
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=1.3,
            linestyle="--",
            color="#b91c1c",
        )
    )
    ax.text(
        xc + 0.01,
        (y0 + y1) / 2,
        "Eliminated\nin Folded-bias",
        color="#b91c1c",
        fontsize=10.5,
        ha="left",
        va="center",
    )
    ax.text(
        0.44,
        0.08,
        "K is injected in CSA columns ($|K| \\less Th$);\nexplicit -Th comparator add is removed.",
        fontsize=13.5,
        fontweight="semibold",
        color="#14532d",
        ha="center",
        va="center",
        bbox=dict(facecolor="white", edgecolor="#14532d", boxstyle="round,pad=0.2", alpha=0.95),
    )


def _panel_example(ax, row: dict[str, str]) -> tuple[int, int, float, float, int]:
    n = int(row["n"])
    b_fa = int(row["baseline_fa_count"])
    f_fa = int(row["folded_fa_count"])
    b_kl = int(row["baseline_raw_klut_gates"])
    f_kl = int(row["folded_raw_klut_gates"])

    d_fa = b_fa - f_fa
    d_kl = b_kl - f_kl
    p_fa = 100.0 * d_fa / b_fa
    p_kl = 100.0 * d_kl / b_kl

    labels = ["FA count", "Raw k-LUT"]
    # Keep bars thin, but explicitly control intra-pair and inter-group spacing.
    bar_w = 0.08
    pair_gap = 0.01
    group_step = 0.32
    group_centers = [0.0, group_step]
    x_margin = 0.16

    baseline = [b_fa, b_kl]
    folded = [f_fa, f_kl]

    offset = bar_w / 2 + pair_gap / 2
    baseline_x = [c - offset for c in group_centers]
    folded_x = [c + offset for c in group_centers]

    ax.bar(baseline_x, baseline, width=bar_w, color="#ff7f0e", label="Baseline")
    ax.bar(folded_x, folded, width=bar_w, color="#1f77b4", label="Folded-bias")

    ax.set_xticks(group_centers)
    ax.set_xticklabels(labels, fontsize=11.5)
    ax.set_ylabel("Count", fontsize=13)
    ax.set_title(f"(b) Case Study (n={n})", fontsize=14)
    ax.tick_params(axis="y", labelsize=11.5)
    ax.set_xlim(group_centers[0] - x_margin, group_centers[-1] + x_margin)
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(frameon=False, fontsize=11.5, loc="upper left")

    for i, v in enumerate(baseline):
        ax.text(baseline_x[i], v + max(baseline) * 0.02, f"{v}", ha="center", va="bottom", fontsize=11.5)
    for i, v in enumerate(folded):
        ax.text(folded_x[i], v + max(baseline) * 0.02, f"{v}", ha="center", va="bottom", fontsize=11.5)

    # Keep savings in caption/body text; avoid overlay text inside the bar plot.
    return d_fa, d_kl, p_fa, p_kl, n


def _write_latex_figure(path: Path, fig_rel_path: str, n: int, d_fa: int, d_kl: int, p_fa: float, p_kl: float) -> None:
    text = rf"""\begin{{figure*}}[t]
\centering
\includegraphics[width=\textwidth]{{{fig_rel_path}}}
\caption{{Introduction-level motivation for folded-bias decomposition. (a) Baseline computes HW with CSA, performs an explicit comparator add with $-Th$, and then derives the final carry decision bit. Folded-bias injects $K$ directly into CSA columns and derives the same decision bit without a separate comparator stage. (b) Example at $n={n}$: FA count reduces by $\Delta$FA={d_fa} ({p_fa:.1f}\%), and raw $k$-LUT structural size reduces by $\Delta$raw-$k$-LUT={d_kl} ({p_kl:.1f}\%) versus baseline.}}
\label{{fig:intro_motivation}}
\end{{figure*}}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _write_intro_paragraph(path: Path, n: int, d_fa: int, d_kl: int, p_fa: float, p_kl: float) -> None:
    text = (
        "The motivation for folded-bias decomposition is architectural.\n"
        "In the baseline flow, CSA-based accumulation is followed by an explicit comparator add with $-Th$, whose carry-out\n"
        "gives the final decision bit.\n"
        "Folded-bias instead injects $K$ directly in CSA columns and obtains the same decision bit without a separate\n"
        "comparator stage.\n"
        f"A small example at $n={n}$ illustrates the effect: FA count decreases by $\\Delta\\mathrm{{FA}}={d_fa}$ ({p_fa:.1f}\\%),\n"
        f"and raw $k$-LUT structural size decreases by $\\Delta\\mathrm{{raw\\text{{-}}}}k\\mathrm{{\\text{{-}}LUT}}={d_kl}$ ({p_kl:.1f}\\%) versus baseline.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate introduction motivation figure + short LaTeX text.")
    parser.add_argument("--raw-csv", default="results/paper_package_5_61/data/raw_light_metrics_5_61.csv")
    parser.add_argument("--example-n", type=int, default=13, help="Single n-value used in the intro example.")
    parser.add_argument("--out-fig-prefix", default="results/paper_package_5_61/figures/fig_intro_motivation")
    parser.add_argument("--out-tex", default="results/paper_package_5_61/tables/fig_intro_motivation.tex")
    parser.add_argument(
        "--out-intro-paragraph",
        default="results/paper_package_5_61/tables/intro_motivation_paragraph.tex",
    )
    parser.add_argument(
        "--fig-rel-path-for-latex",
        default="results/paper_package_5_61/figures/fig_intro_motivation.pdf",
    )
    args = parser.parse_args()

    rows = _read_csv(Path(args.raw_csv))
    example = _find_row_by_n(rows, args.example_n)

    plt.style.use("default")
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig = plt.figure(figsize=(14.2, 5.2), facecolor="white")
    gs = fig.add_gridspec(1, 2, width_ratios=[1.8, 0.8])
    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[0, 1])
    ax0.set_facecolor("white")
    ax1.set_facecolor("white")

    _panel_architecture(ax0)
    d_fa, d_kl, p_fa, p_kl, n = _panel_example(ax1, example)

    fig.tight_layout()

    out_prefix = Path(args.out_fig_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_prefix.with_suffix(".png"), dpi=450, bbox_inches="tight")
    fig.savefig(out_prefix.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)

    _write_latex_figure(Path(args.out_tex), args.fig_rel_path_for_latex, n, d_fa, d_kl, p_fa, p_kl)
    _write_intro_paragraph(Path(args.out_intro_paragraph), n, d_fa, d_kl, p_fa, p_kl)

    print(f"Wrote figure: {out_prefix.with_suffix('.png')}")
    print(f"Wrote figure: {out_prefix.with_suffix('.pdf')}")
    print(f"Wrote LaTeX figure block: {args.out_tex}")
    print(f"Wrote intro paragraph: {args.out_intro_paragraph}")


if __name__ == "__main__":
    main()
