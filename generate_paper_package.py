#!/usr/bin/env python3
"""
Generate a research-report package for folded vs baseline majority circuits.

It runs all measurement pipelines, merges results, and emits:
  - CSV data files
  - LaTeX tables (ready for Overleaf)
  - Publication-style figures (PNG + PDF)
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
from collections import defaultdict
from pathlib import Path
from statistics import mean


def _run(cmd, cwd: Path) -> None:
    print("[run]", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(cwd), check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(cmd)}")


def _read_csv(path: Path):
    with path.open() as f:
        return list(csv.DictReader(f))


def _to_float(v):
    return float(v)


def _to_int(v):
    return int(float(v))


def _fmt(v, nd=3):
    if isinstance(v, int):
        return str(v)
    return f"{float(v):.{nd}f}"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _latex_table(headers, rows, caption, label):
    colspec = "c" * len(headers)
    lines = []
    lines.append("\\begin{table*}[t]")
    lines.append("\\centering")
    lines.append(f"\\caption{{{caption}}}")
    lines.append(f"\\label{{{label}}}")
    lines.append(f"\\begin{{tabular}}{{{colspec}}}")
    lines.append("\\hline")
    lines.append(" & ".join(headers) + " \\\\")
    lines.append("\\hline")
    for r in rows:
        lines.append(" & ".join(r) + " \\\\")
    lines.append("\\hline")
    lines.append("\\end{tabular}")
    lines.append("\\end{table*}")
    lines.append("")
    return "\n".join(lines)


def _build_core_table(raw_rows):
    headers = [
        "$n$",
        "FA$_{fold}$",
        "FA$_{base}$",
        "$\\Delta$FA",
        "MIG$_{fold}^{light}$",
        "MIG$_{base}^{light}$",
        "$\\Delta$MIG",
        "$t_{fold}^{light}$ (s)",
        "$t_{base}^{light}$ (s)",
        "$\\Delta t^{light}$ (s)",
    ]
    rows = []
    for r in raw_rows:
        rows.append([
            r["n"],
            r["folded_fa_count"],
            r["baseline_fa_count"],
            str(_to_int(r["baseline_fa_count"]) - _to_int(r["folded_fa_count"])),
            r["folded_light_mig_after"],
            r["baseline_light_mig_after"],
            r["delta_light_mig_baseline_minus_folded"],
            _fmt(r["folded_light_runtime_s"], 4),
            _fmt(r["baseline_light_runtime_s"], 4),
            _fmt(r["delta_light_runtime_s_baseline_minus_folded"], 4),
        ])
    return _latex_table(
        headers,
        rows,
        "Core implementation comparison (raw structure and light optimization). "
        "All deltas are baseline minus folded.",
        "tab:core_impl",
    )


def _build_lut6_table(abc_rows):
    lut = [r for r in abc_rows if r["target"] == "lut6"]
    headers = ["$n$", "LUT6$_{fold}$", "LUT6$_{base}$", "$\\Delta$LUT6", "Lev$_{fold}$", "Lev$_{base}$", "$\\Delta$Lev"]
    rows = []
    for r in lut:
        rows.append([
            r["n"],
            _fmt(r["folded_area"], 0),
            _fmt(r["baseline_area"], 0),
            _fmt(r["delta_area_baseline_minus_folded"], 0),
            r["folded_lev"],
            r["baseline_lev"],
            r["delta_lev_baseline_minus_folded"],
        ])
    return _latex_table(
        headers,
        rows,
        "ABC LUT6 mapping comparison. Deltas are baseline minus folded.",
        "tab:lut6_map",
    )


def _build_stdcell_tables(abc_rows):
    by_lib = defaultdict(list)
    for r in abc_rows:
        if r["target"] == "stdcell_proxy":
            by_lib[r["library"]].append(r)

    outs = {}
    for lib, rows_lib in sorted(by_lib.items()):
        rows_lib = sorted(rows_lib, key=lambda x: int(x["n"]))
        headers = ["$n$", "Area$_{fold}$", "Area$_{base}$", "$\\Delta$Area", "Delay$_{fold}$", "Delay$_{base}$", "$\\Delta$Delay"]
        rows = []
        for r in rows_lib:
            rows.append([
                r["n"],
                _fmt(r["folded_area"], 3),
                _fmt(r["baseline_area"], 3),
                _fmt(r["delta_area_baseline_minus_folded"], 3),
                _fmt(r["folded_delay"], 3),
                _fmt(r["baseline_delay"], 3),
                _fmt(r["delta_delay_baseline_minus_folded"], 3),
            ])
        lib_tag = lib.replace(".", "_")
        outs[lib] = _latex_table(
            headers,
            rows,
            f"ABC std-cell proxy mapping using \\texttt{{{lib}}}. Deltas are baseline minus folded.",
            f"tab:stdcell_{lib_tag}",
        )
    return outs


def _build_cirkit_table(cir_rows):
    headers = [
        "$n$",
        "Inv$_{fold}$",
        "Inv$_{base}$",
        "$\\Delta$Inv",
        "QCA Area$_{\\Delta}$",
        "QCA Delay$_{\\Delta}$",
        "STMG Area$_{\\Delta}$",
        "STMG Delay$_{\\Delta}$",
        "$\\Delta t$ (s)",
    ]
    rows = []
    for r in cir_rows:
        rows.append([
            r["n"],
            r["folded_inverters"],
            r["baseline_inverters"],
            r["delta_inverters_baseline_minus_folded"],
            _fmt(r["delta_qca_area_baseline_minus_folded"], 4),
            _fmt(r["delta_qca_delay_baseline_minus_folded"], 4),
            _fmt(r["delta_stmg_area_baseline_minus_folded"], 4),
            _fmt(r["delta_stmg_delay_baseline_minus_folded"], 4),
            _fmt(r["delta_runtime_s_baseline_minus_folded"], 4),
        ])
    return _latex_table(
        headers,
        rows,
        "CirKit device-level comparison (QCA/STMG) including inverter counts. "
        "Deltas are baseline minus folded.",
        "tab:cirkit_qca_stmg",
    )


def _make_figures(raw_rows, abc_rows, cir_rows, fig_dir: Path):
    import matplotlib.pyplot as plt

    fig_dir.mkdir(parents=True, exist_ok=True)
    ns = [int(r["n"]) for r in raw_rows]

    # Figure 1: light MIG and runtime
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))
    axs[0].plot(ns, [int(r["folded_light_mig_after"]) for r in raw_rows], marker="o", label="Folded")
    axs[0].plot(ns, [int(r["baseline_light_mig_after"]) for r in raw_rows], marker="s", label="Baseline")
    axs[0].set_title("Light Optimization MIG Node Count")
    axs[0].set_xlabel("n")
    axs[0].set_ylabel("MIG nodes (after)")
    axs[0].grid(True, alpha=0.25)
    axs[0].legend()

    axs[1].plot(ns, [float(r["folded_light_runtime_s"]) * 1e3 for r in raw_rows], marker="o", label="Folded")
    axs[1].plot(ns, [float(r["baseline_light_runtime_s"]) * 1e3 for r in raw_rows], marker="s", label="Baseline")
    axs[1].set_title("Light Optimization Runtime")
    axs[1].set_xlabel("n")
    axs[1].set_ylabel("Runtime (ms)")
    axs[1].grid(True, alpha=0.25)
    axs[1].legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "fig_core_light.png", dpi=300)
    fig.savefig(fig_dir / "fig_core_light.pdf")
    plt.close(fig)

    # Figure 2: LUT6 deltas
    lut = sorted([r for r in abc_rows if r["target"] == "lut6"], key=lambda x: int(x["n"]))
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))
    axs[0].axhline(0.0, color="black", linewidth=1)
    axs[0].plot([int(r["n"]) for r in lut], [float(r["delta_area_baseline_minus_folded"]) for r in lut], marker="o")
    axs[0].set_title("LUT6 Area Delta (baseline - folded)")
    axs[0].set_xlabel("n")
    axs[0].set_ylabel("LUT count delta")
    axs[0].grid(True, alpha=0.25)

    axs[1].axhline(0.0, color="black", linewidth=1)
    axs[1].plot([int(r["n"]) for r in lut], [float(r["delta_delay_baseline_minus_folded"]) for r in lut], marker="o")
    axs[1].set_title("LUT6 Delay Delta (baseline - folded)")
    axs[1].set_xlabel("n")
    axs[1].set_ylabel("Level delta")
    axs[1].grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig_lut6_deltas.png", dpi=300)
    fig.savefig(fig_dir / "fig_lut6_deltas.pdf")
    plt.close(fig)

    # Figure 3: CirKit QCA/STMG deltas
    fig, axs = plt.subplots(2, 2, figsize=(12, 7.5))
    nsc = [int(r["n"]) for r in cir_rows]
    axs[0, 0].axhline(0.0, color="black", linewidth=1)
    axs[0, 0].plot(nsc, [float(r["delta_qca_area_baseline_minus_folded"]) for r in cir_rows], marker="o")
    axs[0, 0].set_title("QCA Area Delta")
    axs[0, 0].set_ylabel("baseline - folded")
    axs[0, 0].grid(True, alpha=0.25)

    axs[0, 1].axhline(0.0, color="black", linewidth=1)
    axs[0, 1].plot(nsc, [float(r["delta_qca_delay_baseline_minus_folded"]) for r in cir_rows], marker="o")
    axs[0, 1].set_title("QCA Delay Delta")
    axs[0, 1].grid(True, alpha=0.25)

    axs[1, 0].axhline(0.0, color="black", linewidth=1)
    axs[1, 0].plot(nsc, [float(r["delta_stmg_area_baseline_minus_folded"]) for r in cir_rows], marker="o")
    axs[1, 0].set_title("STMG Area Delta")
    axs[1, 0].set_xlabel("n")
    axs[1, 0].set_ylabel("baseline - folded")
    axs[1, 0].grid(True, alpha=0.25)

    axs[1, 1].axhline(0.0, color="black", linewidth=1)
    axs[1, 1].plot(nsc, [float(r["delta_stmg_delay_baseline_minus_folded"]) for r in cir_rows], marker="o")
    axs[1, 1].set_title("STMG Delay Delta")
    axs[1, 1].set_xlabel("n")
    axs[1, 1].grid(True, alpha=0.25)

    fig.tight_layout()
    fig.savefig(fig_dir / "fig_cirkit_deltas.png", dpi=300)
    fig.savefig(fig_dir / "fig_cirkit_deltas.pdf")
    plt.close(fig)

    # Figure 4: win counts
    def wins(rows, col):
        vals = [float(r[col]) for r in rows]
        return sum(1 for v in vals if v > 0), sum(1 for v in vals if v == 0), sum(1 for v in vals if v < 0)

    labels = [
        "Light MIG",
        "Light Runtime",
        "LUT6 Area",
        "LUT6 Delay",
        "QCA Area",
        "QCA Delay",
        "STMG Area",
        "STMG Delay",
    ]
    metrics = [
        (raw_rows, "delta_light_mig_baseline_minus_folded"),
        (raw_rows, "delta_light_runtime_s_baseline_minus_folded"),
        (lut, "delta_area_baseline_minus_folded"),
        (lut, "delta_delay_baseline_minus_folded"),
        (cir_rows, "delta_qca_area_baseline_minus_folded"),
        (cir_rows, "delta_qca_delay_baseline_minus_folded"),
        (cir_rows, "delta_stmg_area_baseline_minus_folded"),
        (cir_rows, "delta_stmg_delay_baseline_minus_folded"),
    ]
    wvals = [wins(rs, c)[0] for rs, c in metrics]
    lvals = [wins(rs, c)[2] for rs, c in metrics]

    fig, ax = plt.subplots(figsize=(12, 4.2))
    x = range(len(labels))
    ax.bar(x, wvals, label="Folded wins", alpha=0.9)
    ax.bar(x, lvals, bottom=wvals, label="Baseline wins", alpha=0.75)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylabel("Count over n")
    ax.set_title("Win/Loss Counts Across Metrics")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig_win_counts.png", dpi=300)
    fig.savefig(fig_dir / "fig_win_counts.pdf")
    plt.close(fig)


def _summary_md(raw_rows, abc_rows, cir_rows):
    lut = [r for r in abc_rows if r["target"] == "lut6"]

    def win_stats(rows, col):
        vals = [float(r[col]) for r in rows]
        w = sum(1 for v in vals if v > 0)
        t = sum(1 for v in vals if v == 0)
        l = sum(1 for v in vals if v < 0)
        return w, t, l

    items = [
        ("Light MIG", raw_rows, "delta_light_mig_baseline_minus_folded"),
        ("Light Runtime", raw_rows, "delta_light_runtime_s_baseline_minus_folded"),
        ("LUT6 Area", lut, "delta_area_baseline_minus_folded"),
        ("LUT6 Delay", lut, "delta_delay_baseline_minus_folded"),
        ("QCA Area", cir_rows, "delta_qca_area_baseline_minus_folded"),
        ("QCA Delay", cir_rows, "delta_qca_delay_baseline_minus_folded"),
        ("STMG Area", cir_rows, "delta_stmg_area_baseline_minus_folded"),
        ("STMG Delay", cir_rows, "delta_stmg_delay_baseline_minus_folded"),
        ("Inverters", cir_rows, "delta_inverters_baseline_minus_folded"),
    ]

    out = []
    out.append("# Paper-Ready Comparison Summary")
    out.append("")
    out.append("Interpretation: all deltas are `baseline - folded`.")
    out.append("- Positive delta: folded is better")
    out.append("- Negative delta: baseline is better")
    out.append("")
    out.append("## Win/Loss Counts")
    out.append("")
    out.append("| Metric | Folded Wins | Ties | Baseline Wins |")
    out.append("|---|---:|---:|---:|")
    for name, rows, col in items:
        w, t, l = win_stats(rows, col)
        out.append(f"| {name} | {w} | {t} | {l} |")
    out.append("")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Generate full paper-ready stats/tables/figures package.")
    parser.add_argument("--n-start", type=int, default=5)
    parser.add_argument("--n-end", type=int, default=61)
    parser.add_argument("--abc-bin", default="/home/mrunal/abc/abc")
    parser.add_argument(
        "--cirkit-python",
        default="/home/mrunal/Mockturtle-mMIG-main/experiments-dac19-flow/.venv/bin/python",
        help="Python executable with CirKit installed for QCA/STMG metrics.",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory (default: results/paper_package_<start>_<end>)",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    out_dir = Path(args.out_dir) if args.out_dir else root / "results" / f"paper_package_{args.n_start}_{args.n_end}"
    data_dir = out_dir / "data"
    fig_dir = out_dir / "figures"
    tab_dir = out_dir / "tables"
    data_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    tab_dir.mkdir(parents=True, exist_ok=True)

    raw_csv = data_dir / f"raw_light_metrics_{args.n_start}_{args.n_end}.csv"
    abc_csv = data_dir / f"abc_mapped_compare_{args.n_start}_{args.n_end}.csv"
    cir_csv = data_dir / f"cirkit_qca_stmg_compare_{args.n_start}_{args.n_end}.csv"

    _run(
        [
            "/usr/bin/python3",
            str(root / "compare_raw_light_metrics.py"),
            "--n-start",
            str(args.n_start),
            "--n-end",
            str(args.n_end),
            "--output",
            str(raw_csv),
        ],
        cwd=root,
    )
    _run(
        [
            "/usr/bin/python3",
            str(root / "compare_abc_mapped_metrics.py"),
            "--n-start",
            str(args.n_start),
            "--n-end",
            str(args.n_end),
            "--abc-bin",
            args.abc_bin,
            "--output",
            str(abc_csv),
        ],
        cwd=root,
    )
    _run(
        [
            args.cirkit_python,
            str(root / "compare_cirkit_qca_stmg.py"),
            "--n-start",
            str(args.n_start),
            "--n-end",
            str(args.n_end),
            "--abc-bin",
            args.abc_bin,
            "--output",
            str(cir_csv),
        ],
        cwd=root,
    )

    raw_rows = sorted(_read_csv(raw_csv), key=lambda x: int(x["n"]))
    abc_rows = sorted(_read_csv(abc_csv), key=lambda x: (int(x["n"]), x["target"], x["library"]))
    cir_rows = sorted(_read_csv(cir_csv), key=lambda x: int(x["n"]))

    _write_text(tab_dir / "table_core_impl.tex", _build_core_table(raw_rows))
    _write_text(tab_dir / "table_lut6.tex", _build_lut6_table(abc_rows))
    for lib, tex in _build_stdcell_tables(abc_rows).items():
        _write_text(tab_dir / f"table_stdcell_{lib}.tex", tex)
    _write_text(tab_dir / "table_cirkit_qca_stmg.tex", _build_cirkit_table(cir_rows))

    _make_figures(raw_rows, abc_rows, cir_rows, fig_dir)
    _write_text(out_dir / "SUMMARY.md", _summary_md(raw_rows, abc_rows, cir_rows))

    print(f"Paper package generated at: {out_dir}")
    print(f"Data:    {data_dir}")
    print(f"Tables:  {tab_dir}")
    print(f"Figures: {fig_dir}")


if __name__ == "__main__":
    main()
