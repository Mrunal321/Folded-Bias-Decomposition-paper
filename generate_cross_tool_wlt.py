#!/usr/bin/env python3
"""
Generate a cross-tool Win/Loss/Tie (WLT) summary figure + LaTeX table.

Inputs:
  - raw/light metrics CSV
  - ABC mapped CSV
  - CirKit CSV
  - Vivado comparison CSV

Outputs:
  - one multi-panel figure (.png + .pdf)
  - one LaTeX table with aggregated counts
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


EPS = 1e-12


def _read_csv(path: Path):
    with path.open() as f:
        return list(csv.DictReader(f))


def _to_float(v):
    s = str(v).strip()
    if not s or s.lower() == "nan":
        return float("nan")
    return float(s)


def _is_nan(v):
    return math.isnan(v)


def _wlt_from_deltas(deltas, better="min"):
    fw = ties = bw = 0
    for d in deltas:
        if _is_nan(d):
            continue
        if better == "min":
            # delta = baseline - folded
            # positive => folded better
            if d > EPS:
                fw += 1
            elif d < -EPS:
                bw += 1
            else:
                ties += 1
        elif better == "max":
            # for max-better metrics like WNS:
            # delta = baseline - folded; negative => folded better
            if d < -EPS:
                fw += 1
            elif d > EPS:
                bw += 1
            else:
                ties += 1
        else:
            raise ValueError(f"Unsupported better={better}")
    return fw, ties, bw


def _pareto_counts(vivado_rows):
    f_dom = b_dom = exact_tie = tradeoff = 0
    for r in vivado_rows:
        fl = _to_float(r["folded_clb_luts"])
        bl = _to_float(r["baseline_clb_luts"])
        fd = _to_float(r["folded_datapath_delay_ns"])
        bd = _to_float(r["baseline_datapath_delay_ns"])
        if any(_is_nan(v) for v in (fl, bl, fd, bd)):
            continue

        folded_dom = (fl <= bl + EPS and fd <= bd + EPS) and (fl < bl - EPS or fd < bd - EPS)
        baseline_dom = (bl <= fl + EPS and bd <= fd + EPS) and (bl < fl - EPS or bd < fd - EPS)
        tie = abs(fl - bl) <= EPS and abs(fd - bd) <= EPS

        if folded_dom and not baseline_dom:
            f_dom += 1
        elif baseline_dom and not folded_dom:
            b_dom += 1
        elif tie:
            exact_tie += 1
        else:
            tradeoff += 1
    return f_dom, b_dom, exact_tie, tradeoff


def _asic_single_lib_stats(abc_rows, lib_name):
    rows = [
        r
        for r in abc_rows
        if r.get("target") == "stdcell_proxy" and r.get("library") == lib_name
    ]
    rows = sorted(rows, key=lambda x: int(x["n"]))
    if not rows:
        return None

    area = _wlt_from_deltas([_to_float(r["delta_area_baseline_minus_folded"]) for r in rows], better="min")
    delay = _wlt_from_deltas([_to_float(r["delta_delay_baseline_minus_folded"]) for r in rows], better="min")
    adp = _wlt_from_deltas(
        [
            (_to_float(r["baseline_area"]) * _to_float(r["baseline_delay"]))
            - (_to_float(r["folded_area"]) * _to_float(r["folded_delay"]))
            for r in rows
        ],
        better="min",
    )
    return {"library": lib_name, "n": len(rows), "area": area, "delay": delay, "adp": adp}


def _stacked_wlt(ax, entries, title, n_label):
    """
    entries: list[(label, fw, ties, bw)]
    """
    labels = [e[0] for e in entries]
    fw = [e[1] for e in entries]
    ties = [e[2] for e in entries]
    bw = [e[3] for e in entries]
    x = list(range(len(entries)))

    b1 = ax.bar(x, fw, color="#1f77b4", label="Folded wins")
    b2 = ax.bar(x, bw, bottom=fw, color="#ff7f0e", label="Baseline wins")
    b3 = ax.bar(x, ties, bottom=[a + b for a, b in zip(fw, bw)], color="#2ca02c", label="Ties")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_title(title)
    ax.set_ylabel("Count (n-values)")
    ax.grid(True, axis="y", alpha=0.25)
    for xi, top in enumerate([a + b + c for a, b, c in zip(fw, bw, ties)]):
        ax.text(xi, top + 0.2, f"n={n_label}", ha="center", va="bottom", fontsize=10)
    return b1[0], b2[0], b3[0]


def _latex_table(rows, caption, label):
    lines = []
    lines.append("\\begin{table*}[t]")
    lines.append("\\centering")
    lines.append("\\scriptsize")
    lines.append("\\setlength{\\tabcolsep}{3.2pt}")
    lines.append("\\renewcommand{\\arraystretch}{1.05}")
    lines.append(f"\\caption{{{caption}}}")
    lines.append(f"\\label{{{label}}}")
    lines.append("\\begin{tabular}{l l r r r r r}")
    lines.append("\\hline")
    lines.append("Group & Metric & Folded wins & Ties & Baseline wins & Tradeoff & n \\\\")
    lines.append("\\hline")
    for r in rows:
        lines.append(
            f"{r['group']} & {r['metric']} & {r['fw']} & {r['ties']} & {r['bw']} & {r['tradeoff']} & {r['n']} \\\\"
        )
    lines.append("\\hline")
    lines.append("\\end{tabular}")
    lines.append("\\end{table*}")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Cross-tool WLT summary plot + table.")
    parser.add_argument("--raw-csv", default="results/paper_package_5_61/data/raw_light_metrics_5_61.csv")
    parser.add_argument("--abc-csv", default="results/paper_package_5_61/data/abc_mapped_compare_5_61.csv")
    parser.add_argument("--cirkit-csv", default="results/paper_package_5_61/data/cirkit_qca_stmg_compare_5_61.csv")
    parser.add_argument("--vivado-csv", default="results/vivado_paper_package_5_61/data/vivado_comparison.csv")
    parser.add_argument(
        "--asic-lib",
        default="mcnc.genlib",
        help="Standard-cell library to use in ASIC panel/table (default: mcnc.genlib)",
    )
    parser.add_argument("--out-fig-prefix", default="results/paper_package_5_61/figures/fig_cross_tool_wlt_summary")
    parser.add_argument("--out-tex", default="results/paper_package_5_61/tables/table_cross_tool_wlt_summary.tex")
    args = parser.parse_args()

    raw_rows = _read_csv(Path(args.raw_csv))
    abc_rows = _read_csv(Path(args.abc_csv))
    cir_rows = _read_csv(Path(args.cirkit_csv))
    viv_rows = [r for r in _read_csv(Path(args.vivado_csv)) if r.get("stage", "synth") == "synth"]

    n_raw = len(raw_rows)
    n_lut = len([r for r in abc_rows if r.get("target") == "lut6"])
    n_cir = len(cir_rows)
    n_viv = len(viv_rows)

    # ABC / logic-level entries
    light_mig = _wlt_from_deltas([_to_float(r["delta_light_mig_baseline_minus_folded"]) for r in raw_rows], "min")
    light_rt = _wlt_from_deltas([_to_float(r["delta_light_runtime_s_baseline_minus_folded"]) for r in raw_rows], "min")
    lut_rows = [r for r in abc_rows if r.get("target") == "lut6"]
    lut_area = _wlt_from_deltas([_to_float(r["delta_area_baseline_minus_folded"]) for r in lut_rows], "min")
    lut_delay = _wlt_from_deltas([_to_float(r["delta_delay_baseline_minus_folded"]) for r in lut_rows], "min")

    # CirKit entries
    qca_area = _wlt_from_deltas([_to_float(r["delta_qca_area_baseline_minus_folded"]) for r in cir_rows], "min")
    qca_delay = _wlt_from_deltas([_to_float(r["delta_qca_delay_baseline_minus_folded"]) for r in cir_rows], "min")
    stmg_area = _wlt_from_deltas([_to_float(r["delta_stmg_area_baseline_minus_folded"]) for r in cir_rows], "min")
    stmg_delay = _wlt_from_deltas([_to_float(r["delta_stmg_delay_baseline_minus_folded"]) for r in cir_rows], "min")

    # Vivado entries
    viv_lut = _wlt_from_deltas([_to_float(r["delta_clb_luts_baseline_minus_folded"]) for r in viv_rows], "min")
    viv_delay = _wlt_from_deltas([_to_float(r["delta_datapath_delay_ns_baseline_minus_folded"]) for r in viv_rows], "min")
    viv_adp = _wlt_from_deltas(
        [
            (_to_float(r["baseline_clb_luts"]) * _to_float(r["baseline_datapath_delay_ns"]))
            - (_to_float(r["folded_clb_luts"]) * _to_float(r["folded_datapath_delay_ns"]))
            for r in viv_rows
        ],
        "min",
    )
    pareto = _pareto_counts(viv_rows)

    # ASIC proxy: single selected std-cell library (e.g., mcnc.genlib)
    asic_stats = _asic_single_lib_stats(abc_rows, args.asic_lib)

    # Build summary rows for LaTeX
    summary_rows = []

    def add(group, metric, triple, n, tradeoff=0):
        fw, ties, bw = triple
        summary_rows.append(
            {
                "group": group,
                "metric": metric,
                "fw": fw,
                "ties": ties,
                "bw": bw,
                "tradeoff": tradeoff,
                "n": n,
            }
        )

    add("ABC/Logic", "Light MIG", light_mig, n_raw)
    add("ABC/Logic", "Light Runtime", light_rt, n_raw)
    add("ABC/Logic", "LUT6 Area", lut_area, n_lut)
    add("ABC/Logic", "LUT6 Delay", lut_delay, n_lut)

    add("CirKit", "QCA Area", qca_area, n_cir)
    add("CirKit", "QCA Delay", qca_delay, n_cir)
    add("CirKit", "STMG Area", stmg_area, n_cir)
    add("CirKit", "STMG Delay", stmg_delay, n_cir)

    add("Vivado", "CLB LUTs", viv_lut, n_viv)
    add("Vivado", "Delay", viv_delay, n_viv)
    add("Vivado", "ADP", viv_adp, n_viv)
    summary_rows.append(
        {
            "group": "Vivado Pareto",
            "metric": "(LUT,Delay)",
            "fw": pareto[0],
            "ties": pareto[2],
            "bw": pareto[1],
            "tradeoff": pareto[3],
            "n": n_viv,
        }
    )

    if asic_stats:
        add(f"ASIC ({asic_stats['library']})", "Area", asic_stats["area"], asic_stats["n"])
        add(f"ASIC ({asic_stats['library']})", "Delay", asic_stats["delay"], asic_stats["n"])
        add(f"ASIC ({asic_stats['library']})", "ADP", asic_stats["adp"], asic_stats["n"])

    # Write LaTeX table
    out_tex = Path(args.out_tex)
    out_tex.parent.mkdir(parents=True, exist_ok=True)
    out_tex.write_text(
        _latex_table(
            summary_rows,
            "Win/Loss/Tie (WLT) summary for folded-bias vs baseline. "
            f"All counts are computed from existing CSVs; ASIC rows use \\texttt{{{args.asic_lib}}}.",
            "tab:cross_tool_wlt",
        )
    )

    # Plot figure
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(19, 8))
    gs = fig.add_gridspec(1, 5, width_ratios=[1.2, 1.2, 1.2, 0.9, 1.1])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])
    ax4 = fig.add_subplot(gs[0, 3])
    ax5 = fig.add_subplot(gs[0, 4])

    h_wlt = _stacked_wlt(
        ax1,
        [
            ("Light MIG", *light_mig),
            ("Light Runtime", *light_rt),
            ("LUT6 Area", *lut_area),
            ("LUT6 Delay", *lut_delay),
        ],
        "ABC / Logic-level",
        n_raw,
    )
    _stacked_wlt(
        ax2,
        [
            ("QCA Area", *qca_area),
            ("QCA Delay", *qca_delay),
            ("STMG Area", *stmg_area),
            ("STMG Delay", *stmg_delay),
        ],
        "CirKit / Emerging fabrics",
        n_cir,
    )
    _stacked_wlt(
        ax3,
        [
            ("CLB LUTs", *viv_lut),
            ("Delay", *viv_delay),
            ("ADP", *viv_adp),
        ],
        "Vivado / FPGA",
        n_viv,
    )

    # Vivado Pareto panel
    f_dom, b_dom, exact_tie, tradeoff = pareto
    b1 = ax4.bar([0], [f_dom], color="#1f77b4", label="Folded dominates")
    b2 = ax4.bar([0], [b_dom], bottom=[f_dom], color="#ff7f0e", label="Baseline dominates")
    b3 = ax4.bar([0], [exact_tie], bottom=[f_dom + b_dom], color="#2ca02c", label="Exact tie")
    b4 = ax4.bar([0], [tradeoff], bottom=[f_dom + b_dom + exact_tie], color="#d62728", label="Tradeoff")
    ax4.set_xticks([0])
    ax4.set_xticklabels(["Pareto (LUT,Delay)"])
    ax4.set_title("Vivado Pareto")
    ax4.set_ylabel("Count (n-values)")
    ax4.grid(True, axis="y", alpha=0.25)
    ax4.text(0, f_dom + b_dom + exact_tie + tradeoff + 0.2, f"n={n_viv}", ha="center", va="bottom", fontsize=10)

    # ASIC proxy panel
    if asic_stats:
        _stacked_wlt(
            ax5,
            [
                ("Area", *asic_stats["area"]),
                ("Delay", *asic_stats["delay"]),
                ("ADP", *asic_stats["adp"]),
            ],
            f"ASIC / {asic_stats['library']}",
            asic_stats["n"],
        )
    else:
        ax5.axis("off")
        ax5.text(0.5, 0.5, f"ASIC proxy\n{args.asic_lib}\nnot available", ha="center", va="center")

    # Shared y scaling for first 4 panels
    ymax = max(n_raw, n_cir, n_viv)
    for ax in (ax1, ax2, ax3, ax4):
        ax.set_ylim(0, ymax + 1)

    fig.suptitle("Cross-Tool Win-Loss-Tie (WLT) Summary: Folded-bias vs Baseline", fontsize=22, y=0.98)

    # Global legend
    fig.legend(
        [h_wlt[0], h_wlt[1], h_wlt[2], b1[0], b2[0], b3[0], b4[0]],
        ["Folded wins", "Baseline wins", "Ties", "Folded dominates", "Baseline dominates", "Exact tie", "Tradeoff"],
        loc="upper center",
        ncol=7,
        frameon=False,
        bbox_to_anchor=(0.5, 0.93),
        fontsize=17,
        handlelength=1.6,
    )

    fig.tight_layout(rect=[0, 0, 1, 0.90])
    out_prefix = Path(args.out_fig_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_prefix.with_suffix(".png"), dpi=300)
    fig.savefig(out_prefix.with_suffix(".pdf"))
    plt.close(fig)

    print(f"Wrote figure: {out_prefix.with_suffix('.png')}")
    print(f"Wrote figure: {out_prefix.with_suffix('.pdf')}")
    print(f"Wrote table:  {out_tex}")


if __name__ == "__main__":
    main()
