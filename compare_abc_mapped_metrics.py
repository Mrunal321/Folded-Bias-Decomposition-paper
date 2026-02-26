#!/usr/bin/env python3
"""
Map folded-vs-baseline majority BLIFs with ABC and compare:
  1) LUT6 mapping (if -K 6): area proxy = LUT count, delay proxy = LUT levels
  2) Std-cell proxy mapping (read_genlib + map): area/delay from ABC stats

Preferred std-cell libraries are those whose filename contains:
  stmg, qca, bioth
If none are found in known local library folders, the script falls back to:
  sky130, asap7, mcnc (if present)
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import final_generator as fg


STAT_RE = re.compile(
    r"nd\s*=\s*(?P<nd>\d+).*?"
    r"(?:area\s*=\s*(?P<area>[0-9]+(?:\.[0-9]+)?)\s*"
    r"delay\s*=\s*(?P<delay>[0-9]+(?:\.[0-9]+)?)\s*)?"
    r"lev\s*=\s*(?P<lev>\d+)",
    re.IGNORECASE,
)


def _resolve_abc_bin(explicit: Optional[str]) -> str:
    if explicit:
        p = Path(explicit)
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
        raise FileNotFoundError(f"ABC binary not executable: {explicit}")

    for c in (
        shutil.which("abc"),
        "/home/mrunal/abc/abc",
    ):
        if c and Path(c).is_file() and os.access(c, os.X_OK):
            return c
    raise FileNotFoundError("Could not find abc binary in PATH or /home/mrunal/abc/abc")


def _known_lib_dirs() -> List[Path]:
    home = Path.home()
    cwd = Path.cwd()
    dirs = [
        cwd / "tools/mockturtle_mig_opt/build/_deps/mockturtle_dep-src/experiments/cell_libraries",
        home / "mockturtle/experiments/cell_libraries",
        home / "Mockturtle-mMIG/experiments/cell_libraries",
        home / "Mockturtle-mMIG-main/experiments/cell_libraries",
    ]
    return [d for d in dirs if d.is_dir()]


def _collect_candidate_genlibs(extra_libs: List[str]) -> List[Path]:
    libs: List[Path] = []
    seen = set()

    for d in _known_lib_dirs():
        for p in d.glob("*.genlib"):
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                libs.append(rp)

    for lib in extra_libs:
        p = Path(lib).expanduser().resolve()
        if not p.is_file():
            raise FileNotFoundError(f"Requested --std-lib not found: {lib}")
        if p.suffix.lower() != ".genlib":
            raise ValueError(f"Only .genlib is supported for std-cell proxy mapping here: {lib}")
        if p not in seen:
            seen.add(p)
            libs.append(p)

    return libs


def _select_std_libs(candidates: List[Path]) -> List[Path]:
    preferred_keys = ("stmg", "qca", "bioth")
    fallbacks = ("sky130", "asap7", "mcnc")

    preferred = [p for p in candidates if any(k in p.name.lower() for k in preferred_keys)]
    if preferred:
        return sorted(preferred, key=lambda p: p.name.lower())

    selected: List[Path] = []
    for k in fallbacks:
        match = [p for p in candidates if k in p.name.lower()]
        if match:
            selected.append(sorted(match, key=lambda p: str(p))[0])
    return selected


def _run_abc(abc_bin: str, script: str) -> str:
    proc = subprocess.run(
        [abc_bin, "-q", script],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "ABC failed:\n"
            f"cmd: {abc_bin} -q \"{script}\"\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}\n"
        )
    return proc.stdout


def _parse_stats(text: str) -> Dict[str, float]:
    lines = text.splitlines()
    for line in reversed(lines):
        m = STAT_RE.search(line)
        if not m:
            continue
        nd = int(m.group("nd"))
        lev = int(m.group("lev"))
        area = float(m.group("area")) if m.group("area") else float(nd)
        delay = float(m.group("delay")) if m.group("delay") else float(lev)
        return {"nd": nd, "lev": lev, "area": area, "delay": delay}
    raise RuntimeError(f"Could not parse ABC stats from output:\n{text}")


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


def _map_lut6(abc_bin: str, blif: str) -> Dict[str, float]:
    out = _run_abc(abc_bin, f"read_blif {blif}; strash; if -K 6; ps")
    return _parse_stats(out)


def _map_stdcell_genlib(abc_bin: str, blif: str, genlib: str) -> Dict[str, float]:
    out = _run_abc(abc_bin, f"read_blif {blif}; strash; read_genlib {genlib}; map; ps")
    return _parse_stats(out)


def _collect_for_n(abc_bin: str, n: int, std_libs: List[Path]) -> List[Dict[str, object]]:
    fb_net = fg.build_folded_bias_full_netlist(n)
    bs_net = fg.build_baseline_strict_netlist(n)

    rows: List[Dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix=f"abc_map_n{n}_") as td:
        fb_blif = os.path.join(td, f"maj_fb_{n}.blif")
        bs_blif = os.path.join(td, f"maj_baseline_strict_{n}.blif")
        _write_blif_for_design(f"maj_fb_{n}", n, fb_net, fb_blif)
        _write_blif_for_design(f"maj_baseline_strict_{n}", n, bs_net, bs_blif)

        fb_lut = _map_lut6(abc_bin, fb_blif)
        bs_lut = _map_lut6(abc_bin, bs_blif)
        rows.append(
            {
                "n": n,
                "target": "lut6",
                "library": "K6",
                "folded_nd": fb_lut["nd"],
                "folded_lev": fb_lut["lev"],
                "folded_area": fb_lut["area"],
                "folded_delay": fb_lut["delay"],
                "baseline_nd": bs_lut["nd"],
                "baseline_lev": bs_lut["lev"],
                "baseline_area": bs_lut["area"],
                "baseline_delay": bs_lut["delay"],
                "delta_nd_baseline_minus_folded": int(bs_lut["nd"] - fb_lut["nd"]),
                "delta_lev_baseline_minus_folded": int(bs_lut["lev"] - fb_lut["lev"]),
                "delta_area_baseline_minus_folded": round(bs_lut["area"] - fb_lut["area"], 4),
                "delta_delay_baseline_minus_folded": round(bs_lut["delay"] - fb_lut["delay"], 4),
            }
        )

        for lib in std_libs:
            fb_sc = _map_stdcell_genlib(abc_bin, fb_blif, str(lib))
            bs_sc = _map_stdcell_genlib(abc_bin, bs_blif, str(lib))
            rows.append(
                {
                    "n": n,
                    "target": "stdcell_proxy",
                    "library": lib.name,
                    "folded_nd": fb_sc["nd"],
                    "folded_lev": fb_sc["lev"],
                    "folded_area": fb_sc["area"],
                    "folded_delay": fb_sc["delay"],
                    "baseline_nd": bs_sc["nd"],
                    "baseline_lev": bs_sc["lev"],
                    "baseline_area": bs_sc["area"],
                    "baseline_delay": bs_sc["delay"],
                    "delta_nd_baseline_minus_folded": int(bs_sc["nd"] - fb_sc["nd"]),
                    "delta_lev_baseline_minus_folded": int(bs_sc["lev"] - fb_sc["lev"]),
                    "delta_area_baseline_minus_folded": round(bs_sc["area"] - fb_sc["area"], 4),
                    "delta_delay_baseline_minus_folded": round(bs_sc["delay"] - fb_sc["delay"], 4),
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ABC LUT6 + std-cell proxy mapped area/delay comparison for folded vs baseline."
    )
    parser.add_argument("--n-start", type=int, default=5, help="Start odd n (default: 5)")
    parser.add_argument("--n-end", type=int, default=51, help="End odd n inclusive (default: 51)")
    parser.add_argument(
        "--output",
        default="results/abc_mapped_compare_5_51.csv",
        help="Output CSV path (default: results/abc_mapped_compare_5_51.csv)",
    )
    parser.add_argument(
        "--abc-bin",
        default=None,
        help="Path to abc binary (default: auto-detect).",
    )
    parser.add_argument(
        "--std-lib",
        action="append",
        default=[],
        help="Extra .genlib path(s) to include. Can be repeated.",
    )
    args = parser.parse_args()

    if args.n_start > args.n_end:
        raise ValueError("--n-start must be <= --n-end")

    ns = [n for n in range(args.n_start, args.n_end + 1) if n >= 3 and n % 2 == 1]
    if not ns:
        raise ValueError("No odd n values in requested range")

    abc_bin = _resolve_abc_bin(args.abc_bin)
    candidates = _collect_candidate_genlibs(args.std_lib)
    std_libs = _select_std_libs(candidates)
    if not std_libs:
        raise RuntimeError(
            "No std-cell proxy .genlib found. Add one with --std-lib or place "
            "sky130/asap7/mcnc in known library folders."
        )

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, object]] = []
    for n in ns:
        rows.extend(_collect_for_n(abc_bin, n, std_libs))

    fieldnames = [
        "n",
        "target",
        "library",
        "folded_nd",
        "folded_lev",
        "folded_area",
        "folded_delay",
        "baseline_nd",
        "baseline_lev",
        "baseline_area",
        "baseline_delay",
        "delta_nd_baseline_minus_folded",
        "delta_lev_baseline_minus_folded",
        "delta_area_baseline_minus_folded",
        "delta_delay_baseline_minus_folded",
    ]
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote CSV: {out_path}")
    print(f"ABC bin: {abc_bin}")
    print("Selected std-cell proxy libs:")
    for lib in std_libs:
        print(f"  - {lib}")
    print(f"Rows: {len(rows)} (n from {ns[0]} to {ns[-1]}; targets per n = {1 + len(std_libs)})")


if __name__ == "__main__":
    main()
