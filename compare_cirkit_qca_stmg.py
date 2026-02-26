#!/usr/bin/env python3
"""
Compare folded-vs-baseline majority designs using CirKit device proxies:
  - QCA: area/delay/energy
  - STMG: area/delay/energy

Flow per design:
  netlist (from final_generator) -> BLIF -> AIGER (ABC) -> MIG store (CirKit) -> migcost
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Tuple

import final_generator as fg


def _resolve_abc_bin(explicit: str | None) -> str:
    if explicit:
        p = Path(explicit)
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
        raise FileNotFoundError(f"ABC binary not executable: {explicit}")
    for c in (shutil.which("abc"), "/home/mrunal/abc/abc"):
        if c and Path(c).is_file() and os.access(c, os.X_OK):
            return c
    raise FileNotFoundError("Could not find abc binary")


def _write_blif_for_design(model_name: str, n: int, net_data, blif_path: str) -> None:
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


def _blif_to_aiger(abc_bin: str, blif_path: str, aig_path: str) -> None:
    script = f"read_blif {blif_path}; strash; write_aiger {aig_path}"
    proc = subprocess.run([abc_bin, "-q", script], check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ABC failed for {blif_path}:\n{proc.stdout}\n{proc.stderr}")
    if not os.path.exists(aig_path):
        raise RuntimeError(f"ABC did not create AIGER file: {aig_path}")


def _cirkit_eval(aig_path: str) -> Dict[str, float]:
    # Imported lazily so script can still show a clean error if cirkit is missing.
    import cirkit  # type: ignore

    cirkit.store(clear=True, mig=True)
    cirkit.read_aiger(filename=aig_path, mig=True)
    ntk = cirkit.ps(mig=True, silent=True).dict()
    cost = cirkit.migcost(mig=True).dict()
    return {
        "gates": int(ntk.get("gates", 0)),
        "depth": int(ntk.get("depth", 0)),
        "inverters": int(cost.get("num_inverters", 0)),
        "qca_area": float(cost.get("qca_area", 0.0)),
        "qca_delay": float(cost.get("qca_delay", 0.0)),
        "qca_energy": float(cost.get("qca_energy", 0.0)),
        "stmg_area": float(cost.get("stmg_area", 0.0)),
        "stmg_delay": float(cost.get("stmg_delay", 0.0)),
        "stmg_energy": float(cost.get("stmg_energy", 0.0)),
    }


def _collect_for_n(n: int, abc_bin: str) -> Dict[str, object]:
    fb_net = fg.build_folded_bias_full_netlist(n)
    bs_net = fg.build_baseline_strict_netlist(n)

    with tempfile.TemporaryDirectory(prefix=f"cirkit_n{n}_") as td:
        fb_blif = os.path.join(td, f"maj_fb_{n}.blif")
        bs_blif = os.path.join(td, f"maj_baseline_strict_{n}.blif")
        fb_aig = os.path.join(td, f"maj_fb_{n}.aig")
        bs_aig = os.path.join(td, f"maj_baseline_strict_{n}.aig")

        _write_blif_for_design(f"maj_fb_{n}", n, fb_net, fb_blif)
        _write_blif_for_design(f"maj_baseline_strict_{n}", n, bs_net, bs_blif)

        t_fb = time.perf_counter()
        _blif_to_aiger(abc_bin, fb_blif, fb_aig)
        fb = _cirkit_eval(fb_aig)
        t_fb = time.perf_counter() - t_fb

        t_bs = time.perf_counter()
        _blif_to_aiger(abc_bin, bs_blif, bs_aig)
        bs = _cirkit_eval(bs_aig)
        t_bs = time.perf_counter() - t_bs

    return {
        "n": n,
        "folded_gates": fb["gates"],
        "folded_depth": fb["depth"],
        "folded_inverters": fb["inverters"],
        "folded_runtime_s": round(t_fb, 6),
        "folded_qca_area": fb["qca_area"],
        "folded_qca_delay": fb["qca_delay"],
        "folded_qca_energy": fb["qca_energy"],
        "folded_stmg_area": fb["stmg_area"],
        "folded_stmg_delay": fb["stmg_delay"],
        "folded_stmg_energy": fb["stmg_energy"],
        "baseline_gates": bs["gates"],
        "baseline_depth": bs["depth"],
        "baseline_inverters": bs["inverters"],
        "baseline_runtime_s": round(t_bs, 6),
        "baseline_qca_area": bs["qca_area"],
        "baseline_qca_delay": bs["qca_delay"],
        "baseline_qca_energy": bs["qca_energy"],
        "baseline_stmg_area": bs["stmg_area"],
        "baseline_stmg_delay": bs["stmg_delay"],
        "baseline_stmg_energy": bs["stmg_energy"],
        "delta_gates_baseline_minus_folded": int(bs["gates"] - fb["gates"]),
        "delta_depth_baseline_minus_folded": int(bs["depth"] - fb["depth"]),
        "delta_inverters_baseline_minus_folded": int(bs["inverters"] - fb["inverters"]),
        "delta_runtime_s_baseline_minus_folded": round(t_bs - t_fb, 6),
        "delta_qca_area_baseline_minus_folded": round(bs["qca_area"] - fb["qca_area"], 6),
        "delta_qca_delay_baseline_minus_folded": round(bs["qca_delay"] - fb["qca_delay"], 6),
        "delta_qca_energy_baseline_minus_folded": round(bs["qca_energy"] - fb["qca_energy"], 6),
        "delta_stmg_area_baseline_minus_folded": round(bs["stmg_area"] - fb["stmg_area"], 6),
        "delta_stmg_delay_baseline_minus_folded": round(bs["stmg_delay"] - fb["stmg_delay"], 6),
        "delta_stmg_energy_baseline_minus_folded": round(bs["stmg_energy"] - fb["stmg_energy"], 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CirKit QCA/STMG comparison for folded vs baseline.")
    parser.add_argument("--n-start", type=int, default=5)
    parser.add_argument("--n-end", type=int, default=51)
    parser.add_argument("--abc-bin", default=None, help="Path to abc binary")
    parser.add_argument("--output", default="results/cirkit_qca_stmg_compare_5_51.csv")
    args = parser.parse_args()

    if args.n_start > args.n_end:
        raise ValueError("--n-start must be <= --n-end")
    ns = [n for n in range(args.n_start, args.n_end + 1) if n >= 3 and n % 2 == 1]
    if not ns:
        raise ValueError("No odd n values in requested range")

    abc_bin = _resolve_abc_bin(args.abc_bin)

    rows: List[Dict[str, object]] = []
    for n in ns:
        rows.append(_collect_for_n(n, abc_bin))

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote CSV: {out_path}")
    print(f"Rows: {len(rows)} (n from {ns[0]} to {ns[-1]})")


if __name__ == "__main__":
    main()
