#!/usr/bin/env python3
"""
Generate paper-ready tables/figures from Vivado folded-vs-baseline CSV data.

Inputs:
  - vivado_comparison.csv (required)
  - vivado_detailed.csv   (optional, copied for completeness)

Outputs:
  - data/*.csv
  - tables/*.tex
  - figures/*.png + *.pdf
  - SUMMARY.md
"""

from __future__ import annotations

import argparse
import csv
import math
import shutil
from pathlib import Path
from statistics import mean, median


EPS = 1e-12


def _read_csv(path: Path):
    with path.open() as f:
        return list(csv.DictReader(f))


def _to_float(v: str) -> float:
    if v is None:
        return float("nan")
    s = str(v).strip()
    if not s:
        return float("nan")
    if s.lower() == "nan":
        return float("nan")
    return float(s)


def _is_nan(v: float) -> bool:
    return math.isnan(v)


def _fmt_num(v: float, nd: int = 3) -> str:
    if _is_nan(v):
        return "--"
    if nd == 0:
        return str(int(round(v)))
    return f"{v:.{nd}f}"


def _latex_table(headers, rows, caption, label):
    colspec = "c" * len(headers)
    out = []
    out.append("\\begin{table*}[t]")
    out.append("\\centering")
    out.append("\\scriptsize")
    out.append("\\setlength{\\tabcolsep}{3.6pt}")
    out.append("\\renewcommand{\\arraystretch}{1.05}")
    out.append(f"\\caption{{{caption}}}")
    out.append(f"\\label{{{label}}}")
    out.append(f"\\begin{{tabular}}{{{colspec}}}")
    out.append("\\hline")
    out.append(" & ".join(headers) + " \\\\")
    out.append("\\hline")
    for row in rows:
        out.append(" & ".join(row) + " \\\\")
    out.append("\\hline")
    out.append("\\end{tabular}")
    out.append("\\end{table*}")
    out.append("")
    return "\n".join(out)


def _metric_wtl(rows, metric_key: str, better: str):
    dkey = f"delta_{metric_key}_baseline_minus_folded"
    vals = [_to_float(r[dkey]) for r in rows]
    vals = [v for v in vals if not _is_nan(v)]
    if better == "min":
        fw = sum(1 for v in vals if v > EPS)  # baseline larger => folded better
        bw = sum(1 for v in vals if v < -EPS)
    elif better == "max":
        fw = sum(1 for v in vals if v < -EPS)  # baseline lower => folded better
        bw = sum(1 for v in vals if v > EPS)
    else:
        raise ValueError(f"Unsupported better='{better}'")
    ties = len(vals) - fw - bw
    return fw, ties, bw, vals


def _wtl_gain_from_pairs(f_vals, b_vals, better: str):
    fw = ties = bw = 0
    gains = []
    rel_gains = []
    for f, b in zip(f_vals, b_vals):
        if _is_nan(f) or _is_nan(b):
            continue
        if better == "min":
            gain = b - f
            rel = (gain / b * 100.0) if abs(b) > EPS else float("nan")
        elif better == "max":
            gain = f - b
            # Relative percentages are unstable around zero for WNS.
            rel = float("nan")
        else:
            raise ValueError(f"Unsupported better='{better}'")

        gains.append(gain)
        rel_gains.append(rel)
        if gain > EPS:
            fw += 1
        elif gain < -EPS:
            bw += 1
        else:
            ties += 1

    return fw, ties, bw, gains, rel_gains


def _build_vivado_area_delay_table(rows):
    headers = [
        "$n$",
        "LUT$_F$",
        "LUT$_B$",
        "$\\Delta$LUT",
        "Delay$_F$ (ns)",
        "Delay$_B$ (ns)",
        "$\\Delta$Delay",
        "Lvl$_F$",
        "Lvl$_B$",
        "$\\Delta$Lvl",
    ]
    out_rows = []
    for r in rows:
        out_rows.append(
            [
                r["n"],
                _fmt_num(_to_float(r["folded_clb_luts"]), 0),
                _fmt_num(_to_float(r["baseline_clb_luts"]), 0),
                _fmt_num(_to_float(r["delta_clb_luts_baseline_minus_folded"]), 0),
                _fmt_num(_to_float(r["folded_datapath_delay_ns"]), 3),
                _fmt_num(_to_float(r["baseline_datapath_delay_ns"]), 3),
                _fmt_num(_to_float(r["delta_datapath_delay_ns_baseline_minus_folded"]), 3),
                _fmt_num(_to_float(r["folded_logic_levels"]), 0),
                _fmt_num(_to_float(r["baseline_logic_levels"]), 0),
                _fmt_num(_to_float(r["delta_logic_levels_baseline_minus_folded"]), 0),
            ]
        )
    return _latex_table(
        headers,
        out_rows,
        "Vivado synthesis comparison (resource and delay). "
        "All deltas are baseline minus folded; positive delta implies folded is better for these min-cost metrics.",
        "tab:vivado_area_delay",
    )


def _build_vivado_timing_runtime_table(rows):
    headers = [
        "$n$",
        "WNS$_F$ (ns)",
        "WNS$_B$ (ns)",
        "$\\Delta$WNS",
        "Power$_F$ (mW)",
        "Power$_B$ (mW)",
        "$\\Delta$Power",
        "$t_F$ (s)",
        "$t_B$ (s)",
        "$\\Delta t$",
    ]
    out_rows = []
    for r in rows:
        pf = _to_float(r["folded_total_power_w"]) * 1e3
        pb = _to_float(r["baseline_total_power_w"]) * 1e3
        pd = _to_float(r["delta_total_power_w_baseline_minus_folded"]) * 1e3
        out_rows.append(
            [
                r["n"],
                _fmt_num(_to_float(r["folded_wns_ns"]), 3),
                _fmt_num(_to_float(r["baseline_wns_ns"]), 3),
                _fmt_num(_to_float(r["delta_wns_ns_baseline_minus_folded"]), 3),
                _fmt_num(pf, 3),
                _fmt_num(pb, 3),
                _fmt_num(pd, 3),
                _fmt_num(_to_float(r["folded_runtime_s"]), 3),
                _fmt_num(_to_float(r["baseline_runtime_s"]), 3),
                _fmt_num(_to_float(r["delta_runtime_s_baseline_minus_folded"]), 3),
            ]
        )
    return _latex_table(
        headers,
        out_rows,
        "Vivado synthesis timing/power/runtime comparison. "
        "Deltas are baseline minus folded. For WNS, negative delta means folded has higher slack (better).",
        "tab:vivado_timing_runtime",
    )


def _build_vivado_summary_table(rows):
    metric_defs = [
        ("CLB LUTs", "clb_luts", "min"),
        ("Datapath delay (ns)", "datapath_delay_ns", "min"),
        ("Logic levels", "logic_levels", "min"),
        ("WNS (ns)", "wns_ns", "max"),
        ("Total power (W)", "total_power_w", "min"),
        ("Runtime (s)", "runtime_s", "min"),
    ]
    headers = [
        "Metric",
        "Better",
        "Folded wins",
        "Ties",
        "Baseline wins",
        "Mean $\\Delta$ (B-F)",
        "Median $\\Delta$ (B-F)",
    ]
    out_rows = []
    for title, key, better in metric_defs:
        fw, ties, bw, vals = _metric_wtl(rows, key, better)
        out_rows.append(
            [
                title,
                "\\downarrow" if better == "min" else "\\uparrow",
                str(fw),
                str(ties),
                str(bw),
                _fmt_num(mean(vals), 4),
                _fmt_num(median(vals), 4),
            ]
        )
    return _latex_table(
        headers,
        out_rows,
        "Vivado aggregate win/tie/loss summary over all $n$ points. "
        "$\\Delta$ is baseline minus folded.",
        "tab:vivado_summary",
    )


def _build_vivado_composite_table(rows):
    headers = [
        "$n$",
        "ADP$_F$",
        "ADP$_B$",
        "$\\Delta$ADP (B-F)",
        "Improvement (\\%)",
    ]
    out_rows = []
    for r in rows:
        fl = _to_float(r["folded_clb_luts"])
        bl = _to_float(r["baseline_clb_luts"])
        fd = _to_float(r["folded_datapath_delay_ns"])
        bd = _to_float(r["baseline_datapath_delay_ns"])
        fadp = fl * fd
        badp = bl * bd
        delta = badp - fadp
        imp = (delta / badp * 100.0) if badp != 0 else float("nan")
        out_rows.append(
            [
                r["n"],
                _fmt_num(fadp, 3),
                _fmt_num(badp, 3),
                _fmt_num(delta, 3),
                _fmt_num(imp, 3),
            ]
        )
    return _latex_table(
        headers,
        out_rows,
        "Vivado composite metric: area-delay product (ADP = CLB LUTs $\\times$ datapath delay). "
        "Positive $\\Delta$ADP and positive improvement indicate folded is better.",
        "tab:vivado_composite_adp",
    )


def _build_vivado_aggregate_wins_table(rows):
    headers = [
        "Objective",
        "Folded wins",
        "Ties",
        "Baseline wins",
        "Tradeoff",
        "Folded win rate (\\%)",
        "Mean gain",
        "Mean gain (\\%)",
    ]

    out_rows = []
    metric_defs = [
        ("CLB LUTs (min)", "folded_clb_luts", "baseline_clb_luts", "min"),
        ("Datapath delay (min)", "folded_datapath_delay_ns", "baseline_datapath_delay_ns", "min"),
        ("WNS (max)", "folded_wns_ns", "baseline_wns_ns", "max"),
        ("Total power (min)", "folded_total_power_w", "baseline_total_power_w", "min"),
    ]

    for title, fcol, bcol, better in metric_defs:
        f_vals = [_to_float(r[fcol]) for r in rows]
        b_vals = [_to_float(r[bcol]) for r in rows]
        fw, ties, bw, gains, rels = _wtl_gain_from_pairs(f_vals, b_vals, better)
        total = fw + ties + bw
        rel_clean = [x for x in rels if not _is_nan(x)]
        out_rows.append(
            [
                title,
                str(fw),
                str(ties),
                str(bw),
                "0",
                _fmt_num((fw / total * 100.0) if total else float("nan"), 2),
                _fmt_num(mean(gains) if gains else float("nan"), 4),
                _fmt_num(mean(rel_clean) if rel_clean else float("nan"), 3),
            ]
        )

    # ADP row
    f_adp = [
        _to_float(r["folded_clb_luts"]) * _to_float(r["folded_datapath_delay_ns"])
        for r in rows
    ]
    b_adp = [
        _to_float(r["baseline_clb_luts"]) * _to_float(r["baseline_datapath_delay_ns"])
        for r in rows
    ]
    fw, ties, bw, gains, rels = _wtl_gain_from_pairs(f_adp, b_adp, "min")
    total = fw + ties + bw
    rel_clean = [x for x in rels if not _is_nan(x)]
    out_rows.append(
        [
            "ADP = LUTs x delay (min)",
            str(fw),
            str(ties),
            str(bw),
            "0",
            _fmt_num((fw / total * 100.0) if total else float("nan"), 2),
            _fmt_num(mean(gains) if gains else float("nan"), 4),
            _fmt_num(mean(rel_clean) if rel_clean else float("nan"), 3),
        ]
    )

    # Pareto row for joint (LUT, delay)
    fw = ties = bw = trade = 0
    for r in rows:
        fl = _to_float(r["folded_clb_luts"])
        bl = _to_float(r["baseline_clb_luts"])
        fd = _to_float(r["folded_datapath_delay_ns"])
        bd = _to_float(r["baseline_datapath_delay_ns"])
        if any(_is_nan(v) for v in (fl, bl, fd, bd)):
            continue

        folded_dom = (fl <= bl + EPS and fd <= bd + EPS) and (fl < bl - EPS or fd < bd - EPS)
        base_dom = (bl <= fl + EPS and bd <= fd + EPS) and (bl < fl - EPS or bd < fd - EPS)
        exact_tie = abs(fl - bl) <= EPS and abs(fd - bd) <= EPS

        if folded_dom and not base_dom:
            fw += 1
        elif base_dom and not folded_dom:
            bw += 1
        elif exact_tie:
            ties += 1
        else:
            trade += 1

    total = fw + ties + bw + trade
    out_rows.append(
        [
            "Pareto on (LUT, delay)",
            str(fw),
            str(ties),
            str(bw),
            str(trade),
            _fmt_num((fw / total * 100.0) if total else float("nan"), 2),
            "--",
            "--",
        ]
    )

    return _latex_table(
        headers,
        out_rows,
        "Aggregate Vivado tradeoff summary. "
        "ADP and Pareto rows provide a joint area-delay view; higher Folded win-rate indicates stronger overall tradeoff.",
        "tab:vivado_aggregate_wins",
    )


def _make_figures(rows, fig_dir: Path):
    import matplotlib.pyplot as plt

    fig_dir.mkdir(parents=True, exist_ok=True)
    ns = [int(r["n"]) for r in rows]

    def s(col):
        return [_to_float(r[col]) for r in rows]

    # Figure 1: direct curves (resource + delay)
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))
    axs[0].plot(ns, s("folded_clb_luts"), marker="o", label="Folded")
    axs[0].plot(ns, s("baseline_clb_luts"), marker="s", label="Baseline")
    axs[0].set_title("Vivado CLB LUT Count")
    axs[0].set_xlabel("n")
    axs[0].set_ylabel("CLB LUTs")
    axs[0].grid(True, alpha=0.25)
    axs[0].legend()

    axs[1].plot(ns, s("folded_datapath_delay_ns"), marker="o", label="Folded")
    axs[1].plot(ns, s("baseline_datapath_delay_ns"), marker="s", label="Baseline")
    axs[1].set_title("Vivado Datapath Delay")
    axs[1].set_xlabel("n")
    axs[1].set_ylabel("Delay (ns)")
    axs[1].grid(True, alpha=0.25)
    axs[1].legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "fig_vivado_area_delay_curves.png", dpi=300)
    fig.savefig(fig_dir / "fig_vivado_area_delay_curves.pdf")
    plt.close(fig)

    # Figure 2: timing/power/runtime curves
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2))
    axs[0].plot(ns, s("folded_wns_ns"), marker="o", label="Folded")
    axs[0].plot(ns, s("baseline_wns_ns"), marker="s", label="Baseline")
    axs[0].set_title("Worst Negative Slack")
    axs[0].set_xlabel("n")
    axs[0].set_ylabel("WNS (ns)")
    axs[0].grid(True, alpha=0.25)
    axs[0].legend()

    axs[1].plot(ns, [x * 1e3 for x in s("folded_total_power_w")], marker="o", label="Folded")
    axs[1].plot(ns, [x * 1e3 for x in s("baseline_total_power_w")], marker="s", label="Baseline")
    axs[1].set_title("Total Power")
    axs[1].set_xlabel("n")
    axs[1].set_ylabel("Power (mW)")
    axs[1].grid(True, alpha=0.25)
    axs[1].legend()

    axs[2].plot(ns, s("folded_runtime_s"), marker="o", label="Folded")
    axs[2].plot(ns, s("baseline_runtime_s"), marker="s", label="Baseline")
    axs[2].set_title("Vivado Runtime")
    axs[2].set_xlabel("n")
    axs[2].set_ylabel("Runtime (s)")
    axs[2].grid(True, alpha=0.25)
    axs[2].legend()

    fig.tight_layout()
    fig.savefig(fig_dir / "fig_vivado_timing_power_runtime_curves.png", dpi=300)
    fig.savefig(fig_dir / "fig_vivado_timing_power_runtime_curves.pdf")
    plt.close(fig)

    # Figure 3: delta trends
    fig, axs = plt.subplots(2, 2, figsize=(12, 7.2))
    delta_specs = [
        ("delta_clb_luts_baseline_minus_folded", "CLB LUT Delta (B-F)", "LUT"),
        ("delta_datapath_delay_ns_baseline_minus_folded", "Delay Delta (B-F)", "ns"),
        ("delta_wns_ns_baseline_minus_folded", "WNS Delta (B-F)", "ns"),
        ("delta_runtime_s_baseline_minus_folded", "Runtime Delta (B-F)", "s"),
    ]
    for ax, (key, title, ylab) in zip(axs.flat, delta_specs):
        ax.axhline(0.0, color="black", linewidth=1)
        ax.plot(ns, s(key), marker="o")
        ax.set_title(title)
        ax.set_xlabel("n")
        ax.set_ylabel(ylab)
        ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig_vivado_delta_trends.png", dpi=300)
    fig.savefig(fig_dir / "fig_vivado_delta_trends.pdf")
    plt.close(fig)

    # Figure 4: aggregate win/tie/loss counts
    metric_defs = [
        ("LUTs", "clb_luts", "min"),
        ("Delay", "datapath_delay_ns", "min"),
        ("Levels", "logic_levels", "min"),
        ("WNS", "wns_ns", "max"),
        ("Power", "total_power_w", "min"),
        ("Runtime", "runtime_s", "min"),
    ]
    folded_wins = []
    ties = []
    baseline_wins = []
    labels = []
    for name, key, better in metric_defs:
        fw, t, bw, _ = _metric_wtl(rows, key, better)
        labels.append(name)
        folded_wins.append(fw)
        ties.append(t)
        baseline_wins.append(bw)

    x = list(range(len(labels)))
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.bar(x, folded_wins, label="Folded wins")
    ax.bar(x, ties, bottom=folded_wins, label="Ties")
    ax.bar(x, baseline_wins, bottom=[a + b for a, b in zip(folded_wins, ties)], label="Baseline wins")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Count over n")
    ax.set_title("Vivado Win/Tie/Loss Summary")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "fig_vivado_win_tie_loss.png", dpi=300)
    fig.savefig(fig_dir / "fig_vivado_win_tie_loss.pdf")
    plt.close(fig)

    # Figure 5: ADP curves + ADP percent delta
    fadp = [(_to_float(r["folded_clb_luts"]) * _to_float(r["folded_datapath_delay_ns"])) for r in rows]
    badp = [(_to_float(r["baseline_clb_luts"]) * _to_float(r["baseline_datapath_delay_ns"])) for r in rows]
    delta_pct = []
    for b, f in zip(badp, fadp):
        if abs(b) < EPS:
            delta_pct.append(float("nan"))
        else:
            delta_pct.append((b - f) / b * 100.0)

    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))
    axs[0].plot(ns, fadp, marker="o", label="Folded")
    axs[0].plot(ns, badp, marker="s", label="Baseline")
    axs[0].set_title("Area-Delay Product (ADP)")
    axs[0].set_xlabel("n")
    axs[0].set_ylabel("CLB LUTs x ns")
    axs[0].grid(True, alpha=0.25)
    axs[0].legend()

    axs[1].axhline(0.0, color="black", linewidth=1)
    axs[1].plot(ns, delta_pct, marker="o")
    axs[1].set_title("ADP Improvement (%)")
    axs[1].set_xlabel("n")
    axs[1].set_ylabel("(B-F)/B * 100")
    axs[1].grid(True, alpha=0.25)

    fig.tight_layout()
    fig.savefig(fig_dir / "fig_vivado_adp.png", dpi=300)
    fig.savefig(fig_dir / "fig_vivado_adp.pdf")
    plt.close(fig)


def _build_summary_md(rows):
    metric_defs = [
        ("CLB LUTs", "clb_luts", "min"),
        ("Datapath delay (ns)", "datapath_delay_ns", "min"),
        ("Logic levels", "logic_levels", "min"),
        ("WNS (ns)", "wns_ns", "max"),
        ("Total power (W)", "total_power_w", "min"),
        ("Runtime (s)", "runtime_s", "min"),
    ]

    out = []
    out.append("# Vivado Paper Package Summary")
    out.append("")
    out.append("Interpretation:")
    out.append("- Every delta column is `baseline - folded`.")
    out.append("- For min-cost metrics (LUT/delay/levels/power/runtime), positive delta means folded is better.")
    out.append("- For WNS (max-better), negative delta means folded is better.")
    out.append("")
    out.append("## Win/Tie/Loss")
    out.append("")
    out.append("| Metric | Better | Folded wins | Ties | Baseline wins | Mean delta (B-F) |")
    out.append("|---|---:|---:|---:|---:|---:|")
    for name, key, better in metric_defs:
        fw, ties, bw, vals = _metric_wtl(rows, key, better)
        arrow = "min" if better == "min" else "max"
        out.append(f"| {name} | {arrow} | {fw} | {ties} | {bw} | {mean(vals):.6f} |")
    out.append("")
    # ADP summary
    adp_vals = []
    for r in rows:
        fl = _to_float(r["folded_clb_luts"])
        bl = _to_float(r["baseline_clb_luts"])
        fd = _to_float(r["folded_datapath_delay_ns"])
        bd = _to_float(r["baseline_datapath_delay_ns"])
        f = fl * fd
        b = bl * bd
        if abs(b) > EPS:
            adp_vals.append((b - f) / b * 100.0)
    fw = sum(1 for v in adp_vals if v > EPS)
    ties = sum(1 for v in adp_vals if abs(v) <= EPS)
    bw = sum(1 for v in adp_vals if v < -EPS)
    out.append("## Composite (ADP)")
    out.append("")
    out.append(f"- Folded wins: {fw}")
    out.append(f"- Ties: {ties}")
    out.append(f"- Baseline wins: {bw}")
    out.append(f"- Mean ADP improvement: {mean(adp_vals):.4f}%")
    out.append(f"- Median ADP improvement: {median(adp_vals):.4f}%")
    out.append("")

    # Pareto summary on (LUT, delay)
    f_dom = b_dom = ties2 = trade = 0
    for r in rows:
        fl = _to_float(r["folded_clb_luts"])
        bl = _to_float(r["baseline_clb_luts"])
        fd = _to_float(r["folded_datapath_delay_ns"])
        bd = _to_float(r["baseline_datapath_delay_ns"])
        if any(_is_nan(v) for v in (fl, bl, fd, bd)):
            continue

        folded_dom = (fl <= bl + EPS and fd <= bd + EPS) and (fl < bl - EPS or fd < bd - EPS)
        base_dom = (bl <= fl + EPS and bd <= fd + EPS) and (bl < fl - EPS or bd < fd - EPS)
        exact_tie = abs(fl - bl) <= EPS and abs(fd - bd) <= EPS

        if folded_dom and not base_dom:
            f_dom += 1
        elif base_dom and not folded_dom:
            b_dom += 1
        elif exact_tie:
            ties2 += 1
        else:
            trade += 1

    out.append("## Pareto (LUT, Delay)")
    out.append("")
    out.append(f"- Folded dominates: {f_dom}")
    out.append(f"- Baseline dominates: {b_dom}")
    out.append(f"- Exact ties: {ties2}")
    out.append(f"- Tradeoff points: {trade}")
    out.append("")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Generate Vivado-only paper-ready tables and figures.")
    parser.add_argument(
        "--comparison-csv",
        default="results/vivado_compare_5_61_synth/vivado_comparison.csv",
        help="Path to vivado_comparison.csv",
    )
    parser.add_argument(
        "--detailed-csv",
        default="results/vivado_compare_5_61_synth/vivado_detailed.csv",
        help="Path to vivado_detailed.csv (optional copy source)",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory (default: results/vivado_paper_package_<start>_<end>)",
    )
    args = parser.parse_args()

    comp_csv = Path(args.comparison_csv).resolve()
    if not comp_csv.is_file():
        raise FileNotFoundError(f"Missing comparison CSV: {comp_csv}")

    rows = sorted(_read_csv(comp_csv), key=lambda r: int(r["n"]))
    if not rows:
        raise RuntimeError(f"No rows found in {comp_csv}")

    n_start = int(rows[0]["n"])
    n_end = int(rows[-1]["n"])

    root = Path(__file__).resolve().parent
    out_dir = Path(args.out_dir) if args.out_dir else (root / "results" / f"vivado_paper_package_{n_start}_{n_end}")
    data_dir = out_dir / "data"
    tab_dir = out_dir / "tables"
    fig_dir = out_dir / "figures"
    data_dir.mkdir(parents=True, exist_ok=True)
    tab_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Copy source CSVs into package.
    shutil.copy2(comp_csv, data_dir / "vivado_comparison.csv")
    det_csv = Path(args.detailed_csv).resolve()
    if det_csv.is_file():
        shutil.copy2(det_csv, data_dir / "vivado_detailed.csv")

    (tab_dir / "table_vivado_area_delay.tex").write_text(_build_vivado_area_delay_table(rows))
    (tab_dir / "table_vivado_timing_runtime.tex").write_text(_build_vivado_timing_runtime_table(rows))
    (tab_dir / "table_vivado_summary.tex").write_text(_build_vivado_summary_table(rows))
    (tab_dir / "table_vivado_composite_adp.tex").write_text(_build_vivado_composite_table(rows))
    (tab_dir / "table_vivado_aggregate_wins.tex").write_text(_build_vivado_aggregate_wins_table(rows))

    _make_figures(rows, fig_dir)
    (out_dir / "SUMMARY.md").write_text(_build_summary_md(rows))

    print(f"Vivado paper package generated at: {out_dir}")
    print(f"Data:    {data_dir}")
    print(f"Tables:  {tab_dir}")
    print(f"Figures: {fig_dir}")


if __name__ == "__main__":
    main()
