#!/usr/bin/env python3
"""
Collect folded-vs-baseline metrics in two modes:
  1) raw       : no optimization rounds (rounds=0)
  2) light_opt : recipe=resub, rounds=1

Outputs a CSV with:
  - raw architecture stats: FA count, FA levels
  - raw structural size: klut_gates
  - raw/light runtime: runtime_s
  - light optimization result: mig_before/mig_after, depth_before/depth_after
"""

import argparse
import csv
import os
import subprocess
import tempfile
import time

import final_generator as fg


def _run_mockturtle_once(mock_bin, blif_path, rounds, recipe="resub"):
    cmd = [
        mock_bin,
        "--input",
        blif_path,
        "--recipe",
        recipe,
        "--rounds",
        str(rounds),
        "--max-pis",
        str(fg.MOCKTURTLE_MAX_PIS),
        "--max-inserts",
        str(fg.MOCKTURTLE_MAX_INSERTS),
    ]
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    elapsed_s = time.perf_counter() - t0
    if proc.returncode != 0:
        raise RuntimeError(
            f"mockturtle failed (rounds={rounds}, recipe={recipe}):\n"
            f"cmd={' '.join(cmd)}\n"
            f"stdout={proc.stdout}\n"
            f"stderr={proc.stderr}"
        )
    parsed = fg._parse_mockturtle_result(proc.stdout)
    if not parsed:
        raise RuntimeError(f"Could not parse RESULT line from mockturtle output:\n{proc.stdout}")
    parsed = dict(parsed)
    parsed["runtime_s"] = elapsed_s
    return parsed


def _write_blif_for_design(model_name, n, net_data, blif_path):
    if len(net_data) == 3:
        fa_ops, const1_names, maj_signal = net_data
        maj_ops = []
    elif len(net_data) == 4:
        fa_ops, maj_ops, const1_names, maj_signal = net_data
    else:
        raise AssertionError(f"Unsupported net_data tuple size: {len(net_data)}")

    fg._write_blif_from_fas_canonical(
        model_name=model_name,
        n=n,
        fa_ops=fa_ops,
        maj_signal=maj_signal,
        const1_names=const1_names,
        path=blif_path,
        maj_only=fg.MAJ_ONLY_FA,
        maj_ops=maj_ops,
    )


def _collect_for_n(n, mock_bin):
    _, _, _, _, _, fb_stats = fg.emit_folded_bias(n)
    _, _, _, _, _, bs_stats = fg.emit_baseline_strict(n)

    fb_net = fg.build_folded_bias_full_netlist(n)
    bs_net = fg.build_baseline_strict_netlist(n)

    with tempfile.TemporaryDirectory(prefix=f"raw_light_n{n}_") as td:
        fb_blif = os.path.join(td, f"fb_{n}.blif")
        bs_blif = os.path.join(td, f"bs_{n}.blif")
        _write_blif_for_design(f"maj_fb_{n}", n, fb_net, fb_blif)
        _write_blif_for_design(f"maj_baseline_strict_{n}", n, bs_net, bs_blif)

        fb_raw = _run_mockturtle_once(mock_bin, fb_blif, rounds=0, recipe="resub")
        bs_raw = _run_mockturtle_once(mock_bin, bs_blif, rounds=0, recipe="resub")

        fb_light = _run_mockturtle_once(mock_bin, fb_blif, rounds=1, recipe="resub")
        bs_light = _run_mockturtle_once(mock_bin, bs_blif, rounds=1, recipe="resub")

    return {
        "n": n,
        "folded_fa_count": fb_stats.get("fa_count"),
        "folded_fa_levels": fb_stats.get("fa_levels"),
        "folded_raw_klut_gates": fb_raw.get("klut_gates"),
        "folded_raw_runtime_s": round(fb_raw.get("runtime_s", 0.0), 6),
        "folded_light_mig_before": fb_light.get("mig_before"),
        "folded_light_mig_after": fb_light.get("mig_after"),
        "folded_light_depth_before": fb_light.get("depth_before"),
        "folded_light_depth_after": fb_light.get("depth_after"),
        "folded_light_runtime_s": round(fb_light.get("runtime_s", 0.0), 6),
        "baseline_fa_count": bs_stats.get("total_fa_count"),
        "baseline_fa_levels": bs_stats.get("total_levels"),
        "baseline_raw_klut_gates": bs_raw.get("klut_gates"),
        "baseline_raw_runtime_s": round(bs_raw.get("runtime_s", 0.0), 6),
        "baseline_light_mig_before": bs_light.get("mig_before"),
        "baseline_light_mig_after": bs_light.get("mig_after"),
        "baseline_light_depth_before": bs_light.get("depth_before"),
        "baseline_light_depth_after": bs_light.get("depth_after"),
        "baseline_light_runtime_s": round(bs_light.get("runtime_s", 0.0), 6),
        "delta_raw_klut_baseline_minus_folded": bs_raw.get("klut_gates") - fb_raw.get("klut_gates"),
        "delta_light_mig_before_baseline_minus_folded": bs_light.get("mig_before") - fb_light.get("mig_before"),
        "delta_light_mig_baseline_minus_folded": bs_light.get("mig_after") - fb_light.get("mig_after"),
        "delta_light_depth_before_baseline_minus_folded": bs_light.get("depth_before") - fb_light.get("depth_before"),
        "delta_light_depth_baseline_minus_folded": bs_light.get("depth_after") - fb_light.get("depth_after"),
        "delta_raw_runtime_s_baseline_minus_folded": round(
            bs_raw.get("runtime_s", 0.0) - fb_raw.get("runtime_s", 0.0), 6
        ),
        "delta_light_runtime_s_baseline_minus_folded": round(
            bs_light.get("runtime_s", 0.0) - fb_light.get("runtime_s", 0.0), 6
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compare folded vs baseline in raw and light optimization modes."
    )
    parser.add_argument("--n-start", type=int, default=5, help="Start odd n (default: 5)")
    parser.add_argument("--n-end", type=int, default=51, help="End odd n inclusive (default: 51)")
    parser.add_argument(
        "--output",
        default="results/raw_light_metrics_5_51.csv",
        help="CSV output path (default: results/raw_light_metrics_5_51.csv)",
    )
    args = parser.parse_args()

    if args.n_start > args.n_end:
        raise ValueError("--n-start must be <= --n-end")

    ns = [n for n in range(args.n_start, args.n_end + 1) if n % 2 == 1 and n >= 3]
    if not ns:
        raise ValueError("No odd n values to evaluate in the requested range")

    mock_bin = fg._resolve_mockturtle_bin()
    if not mock_bin:
        raise RuntimeError("mockturtle binary not found. Build tools/mockturtle_mig_opt first.")

    rows = []
    for n in ns:
        rows.append(_collect_for_n(n, mock_bin))

    out_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote CSV: {out_path}")
    print(f"Rows: {len(rows)} (n from {ns[0]} to {ns[-1]})")


if __name__ == "__main__":
    main()
