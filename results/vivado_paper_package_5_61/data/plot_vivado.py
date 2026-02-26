#!/usr/bin/env python3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


plt.rcParams.update(
    {
        "font.size": 11,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "-",
        "axes.spines.top": True,
        "axes.spines.right": True,
        "legend.frameon": True,
    }
)

HERE = Path(__file__).resolve().parent
COMP_PATH = HERE / "vivado_comparison.csv"
FIG_DIR = HERE.parent / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

if not COMP_PATH.is_file():
    raise FileNotFoundError(f"Missing comparison CSV: {COMP_PATH}")

comp = pd.read_csv(COMP_PATH)
comp_s = comp.copy()
if "stage" in comp_s.columns:
    comp_s = comp_s[comp_s["stage"] == "synth"].copy()

comp_s = comp_s.sort_values("n")

# Normalize key numeric columns to avoid dtype surprises.
numeric_cols = [
    "n",
    "folded_clb_luts",
    "baseline_clb_luts",
    "folded_datapath_delay_ns",
    "baseline_datapath_delay_ns",
    "delta_clb_luts_baseline_minus_folded",
    "delta_datapath_delay_ns_baseline_minus_folded",
    "delta_wns_ns_baseline_minus_folded",
    "delta_runtime_s_baseline_minus_folded",
    "folded_wns_ns",
    "baseline_wns_ns",
    "folded_total_power_w",
    "baseline_total_power_w",
    "folded_runtime_s",
    "baseline_runtime_s",
    "baseline_logic_levels",
    "folded_logic_levels",
]
for c in numeric_cols:
    if c in comp_s.columns:
        comp_s[c] = pd.to_numeric(comp_s[c], errors="coerce")

out_paths = []


def savefig(base: str):
    pdf = FIG_DIR / f"{base}.pdf"
    png = FIG_DIR / f"{base}.png"
    plt.savefig(pdf, bbox_inches="tight")
    plt.savefig(png, bbox_inches="tight", dpi=300)
    plt.close()
    out_paths.extend([str(pdf), str(png)])


# 1) Area (CLB LUT) + Delay (Datapath), 1x2
fig, ax = plt.subplots(1, 2, figsize=(12, 3.8))
ax[0].plot(comp_s["n"], comp_s["folded_clb_luts"], marker="o", label="Folded-bias")
ax[0].plot(comp_s["n"], comp_s["baseline_clb_luts"], marker="s", label="Baseline")
ax[0].set_title("Vivado CLB LUT Count")
ax[0].set_xlabel("n")
ax[0].set_ylabel("CLB LUTs")
ax[0].legend()

ax[1].plot(comp_s["n"], comp_s["folded_datapath_delay_ns"], marker="o", label="Folded-bias")
ax[1].plot(comp_s["n"], comp_s["baseline_datapath_delay_ns"], marker="s", label="Baseline")
ax[1].set_title("Vivado Datapath Delay")
ax[1].set_xlabel("n")
ax[1].set_ylabel("Delay (ns)")
ax[1].legend()
fig.tight_layout()
savefig("fig_vivado_area_delay_curves")

# 2) Delta trends 2x2
fig, ax = plt.subplots(2, 2, figsize=(12, 6))
ax = ax.flatten()

ax[0].plot(comp_s["n"], comp_s["delta_clb_luts_baseline_minus_folded"], marker="o")
ax[0].axhline(0)
ax[0].set_title("CLB LUT Delta (B-F)")
ax[0].set_xlabel("n")
ax[0].set_ylabel("LUTs")

ax[1].plot(comp_s["n"], comp_s["delta_datapath_delay_ns_baseline_minus_folded"], marker="o")
ax[1].axhline(0)
ax[1].set_title("Delay Delta (B-F)")
ax[1].set_xlabel("n")
ax[1].set_ylabel("ns")

ax[2].plot(comp_s["n"], comp_s["delta_wns_ns_baseline_minus_folded"], marker="o")
ax[2].axhline(0)
ax[2].set_title("WNS Delta (B-F)")
ax[2].set_xlabel("n")
ax[2].set_ylabel("ns")

ax[3].plot(comp_s["n"], comp_s["delta_runtime_s_baseline_minus_folded"], marker="o")
ax[3].axhline(0)
ax[3].set_title("Runtime Delta (B-F)")
ax[3].set_xlabel("n")
ax[3].set_ylabel("s")

fig.tight_layout()
savefig("fig_vivado_delta_trends")

# 3) Timing/Power/Runtime curves
fig, ax = plt.subplots(1, 3, figsize=(14, 3.8))

ax[0].plot(comp_s["n"], comp_s["folded_wns_ns"], marker="o", label="Folded-bias")
ax[0].plot(comp_s["n"], comp_s["baseline_wns_ns"], marker="s", label="Baseline")
ax[0].set_title("Worst Negative Slack")
ax[0].set_xlabel("n")
ax[0].set_ylabel("WNS (ns)")
ax[0].legend()

ax[1].plot(comp_s["n"], comp_s["folded_total_power_w"] * 1000.0, marker="o", label="Folded-bias")
ax[1].plot(comp_s["n"], comp_s["baseline_total_power_w"] * 1000.0, marker="s", label="Baseline")
ax[1].set_title("Total Power")
ax[1].set_xlabel("n")
ax[1].set_ylabel("Power (mW)")
ax[1].legend()

ax[2].plot(comp_s["n"], comp_s["folded_runtime_s"], marker="o", label="Folded-bias")
ax[2].plot(comp_s["n"], comp_s["baseline_runtime_s"], marker="s", label="Baseline")
ax[2].set_title("Vivado Runtime")
ax[2].set_xlabel("n")
ax[2].set_ylabel("Runtime (s)")
ax[2].legend()

fig.tight_layout()
savefig("fig_vivado_timing_power_runtime_curves")

# 4) Win/Tie/Loss summary
metrics = [
    ("LUTs", "baseline_clb_luts", "folded_clb_luts", "lower"),
    ("Delay", "baseline_datapath_delay_ns", "folded_datapath_delay_ns", "lower"),
    ("Levels", "baseline_logic_levels", "folded_logic_levels", "lower"),
    ("WNS", "baseline_wns_ns", "folded_wns_ns", "higher"),
    ("Power", "baseline_total_power_w", "folded_total_power_w", "lower"),
    ("Runtime", "baseline_runtime_s", "folded_runtime_s", "lower"),
]

fold_wins = []
ties = []
base_wins = []
labels = []

for name, bcol, fcol, direction in metrics:
    b = comp_s[bcol].to_numpy(dtype=float)
    f = comp_s[fcol].to_numpy(dtype=float)
    if direction == "lower":
        fw = np.sum(f < b)
        tw = np.sum(np.isclose(f, b))
        bw = np.sum(f > b)
    else:
        fw = np.sum(f > b)
        tw = np.sum(np.isclose(f, b))
        bw = np.sum(f < b)
    labels.append(name)
    fold_wins.append(int(fw))
    ties.append(int(tw))
    base_wins.append(int(bw))

x = np.arange(len(labels))
fig, ax = plt.subplots(1, 1, figsize=(10.5, 4.2))
ax.bar(x, fold_wins, label="Folded wins")
ax.bar(x, ties, bottom=fold_wins, label="Ties")
ax.bar(x, base_wins, bottom=np.array(fold_wins) + np.array(ties), label="Baseline wins")
ax.set_xticks(x, labels)
ax.set_ylabel("Count over n")
ax.set_title("Vivado Win/Tie/Loss Summary")
ax.legend()
fig.tight_layout()
savefig("fig_vivado_win_tie_loss")

print("Generated figures:")
for p in out_paths:
    print(p)
print("Win/Tie/Loss arrays:", (fold_wins, ties, base_wins))
