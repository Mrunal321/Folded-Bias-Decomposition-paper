#!/usr/bin/env python3
"""
Vivado folded-vs-baseline comparison.

For each odd n in range:
  1) Generate Verilog for folded and baseline (plus FA primitive)
  2) Run Vivado in batch mode (synth only or synth+impl)
  3) Collect utilization, timing, power, runtime
  4) Write detailed CSV + paired comparison CSV (baseline - folded deltas)
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Tuple

import final_generator as fg


FA_PRIMITIVE = """module fa(input a,b,cin, output sum,cout);
  assign {cout,sum} = a + b + cin;
endmodule
"""


VIVADO_TCL = r"""
set verilog_file [lindex $argv 0]
set top_name     [lindex $argv 1]
set part_name    [lindex $argv 2]
set xdc_file     [lindex $argv 3]
set out_dir      [lindex $argv 4]
set run_impl     [lindex $argv 5]

file mkdir $out_dir

read_verilog $verilog_file
if {[file exists $xdc_file]} {
  read_xdc $xdc_file
}

synth_design -top $top_name -part $part_name
report_utilization -file [file join $out_dir utilization_synth.rpt]
report_timing_summary -delay_type max -max_paths 10 -file [file join $out_dir timing_synth.rpt]

set stage "synth"
if {$run_impl == 1} {
  opt_design
  place_design
  phys_opt_design
  route_design
  set stage "impl"
  report_utilization -file [file join $out_dir utilization_impl.rpt]
  report_timing_summary -delay_type max -max_paths 10 -file [file join $out_dir timing_impl.rpt]
}

report_power -file [file join $out_dir power_${stage}.rpt]

set lut_count [llength [get_cells -hier -filter {REF_NAME =~ LUT*}]]
set ff_count [llength [get_cells -hier -filter {REF_NAME =~ FD*}]]
set carry4_count [llength [get_cells -hier -filter {REF_NAME == CARRY4}]]
set dsp_count [llength [get_cells -hier -filter {REF_NAME =~ DSP48*}]]
set ramb18_count [llength [get_cells -hier -filter {REF_NAME == RAMB18E1 || REF_NAME == RAMB18E2}]]
set ramb36_count [llength [get_cells -hier -filter {REF_NAME == RAMB36E1 || REF_NAME == RAMB36E2}]]

set wns "NA"
set datapath_delay "NA"
set logic_levels "NA"
set paths [get_timing_paths -max_paths 1 -delay_type max]
if {[llength $paths] > 0} {
  set p [lindex $paths 0]
  set wns [get_property SLACK $p]
  set datapath_delay [get_property DATAPATH_DELAY $p]
  set logic_levels [get_property LOGIC_LEVELS $p]
}

set fp [open [file join $out_dir metrics_kv.txt] "w"]
puts $fp "stage $stage"
puts $fp "lut_cells $lut_count"
puts $fp "ff_cells $ff_count"
puts $fp "carry4_cells $carry4_count"
puts $fp "dsp_cells $dsp_count"
puts $fp "ramb18_cells $ramb18_count"
puts $fp "ramb36_cells $ramb36_count"
puts $fp "wns_ns $wns"
puts $fp "datapath_delay_ns $datapath_delay"
puts $fp "logic_levels $logic_levels"
close $fp

exit
"""


def _write_design_verilog(n: int, design: str, out_path: Path) -> str:
    if design == "folded":
        src, *_ = fg.emit_folded_bias(n)
        top = f"maj_fb_{n}"
    elif design == "baseline":
        src, *_ = fg.emit_baseline_strict(n)
        top = f"maj_baseline_strict_{n}"
    else:
        raise ValueError(f"Unsupported design: {design}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(FA_PRIMITIVE + "\n" + src + "\n")
    return top


def _write_xdc(n: int, out_path: Path) -> None:
    # Virtual-clock style constraints for combinational in->out timing extraction.
    xdc = (
        "create_clock -name vclk -period 10.000\n"
        "set_input_delay -clock [get_clocks vclk] 0 [get_ports {x[*]}]\n"
        "set_output_delay -clock [get_clocks vclk] 0 [get_ports {maj}]\n"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(xdc)


def _parse_kv(path: Path) -> Dict[str, str]:
    d: Dict[str, str] = {}
    if not path.exists():
        return d
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if " " not in line:
            continue
        k, v = line.split(" ", 1)
        d[k.strip()] = v.strip()
    return d


def _parse_utilization(path: Path) -> Dict[str, float]:
    out = {
        "clb_luts": float("nan"),
        "clb_regs": float("nan"),
        "carry4": float("nan"),
        "dsp": float("nan"),
        "ramb18": float("nan"),
        "ramb36": float("nan"),
    }
    if not path.exists():
        return out

    for line in path.read_text().splitlines():
        if "|" not in line:
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) < 2:
            continue
        key = cols[0]
        val_s = cols[1].replace(",", "")
        try:
            val = float(val_s)
        except ValueError:
            continue
        # Vivado 2024.2 synthesis report uses "Slice LUTs"/"Slice Registers".
        if key.startswith("CLB LUTs") or key.startswith("Slice LUTs"):
            out["clb_luts"] = val
        elif key.startswith("CLB Registers") or key.startswith("Slice Registers"):
            out["clb_regs"] = val
        elif key == "CARRY4":
            out["carry4"] = val
        elif key.startswith("DSPs") or key.startswith("DSP48"):
            out["dsp"] = val
        elif key.startswith("RAMB18"):
            out["ramb18"] = val
        elif key.startswith("RAMB36"):
            out["ramb36"] = val
    return out


def _parse_power(path: Path) -> Dict[str, float]:
    out = {
        "total_power_w": float("nan"),
        "dynamic_power_w": float("nan"),
        "static_power_w": float("nan"),
    }
    if not path.exists():
        return out

    txt = path.read_text()
    patterns = {
        "total_power_w": [
            r"Total On-Chip Power \(W\)\s*\|\s*([0-9eE+\-.]+)",
            r"Total On-Chip Power \(W\)\s*[:]\s*([0-9eE+\-.]+)",
        ],
        "dynamic_power_w": [
            r"Dynamic \(W\)\s*\|\s*([0-9eE+\-.]+)",
            r"Total Dynamic Power \(W\)\s*\|\s*([0-9eE+\-.]+)",
        ],
        "static_power_w": [
            r"Device Static \(W\)\s*\|\s*([0-9eE+\-.]+)",
            r"Static Power \(W\)\s*\|\s*([0-9eE+\-.]+)",
        ],
    }

    for k, regs in patterns.items():
        for rg in regs:
            m = re.search(rg, txt)
            if m:
                out[k] = float(m.group(1))
                break
    return out


def _to_float(v: str, default=float("nan")) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _run_single(
    vivado_bin: str,
    n: int,
    design: str,
    part: str,
    run_impl: bool,
    work_dir: Path,
) -> Dict[str, float]:
    run_dir = work_dir / f"n{n}" / design
    run_dir.mkdir(parents=True, exist_ok=True)
    v_path = run_dir / f"{design}_{n}.v"
    xdc_path = run_dir / f"{design}_{n}.xdc"
    tcl_path = run_dir / "run_vivado.tcl"

    top = _write_design_verilog(n, design, v_path)
    _write_xdc(n, xdc_path)
    tcl_path.write_text(VIVADO_TCL)

    cmd = [
        vivado_bin,
        "-mode",
        "batch",
        "-nojournal",
        "-nolog",
        "-notrace",
        "-source",
        str(tcl_path),
        "-tclargs",
        str(v_path),
        top,
        part,
        str(xdc_path),
        str(run_dir),
        "1" if run_impl else "0",
    ]

    t0 = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    runtime_s = time.perf_counter() - t0
    (run_dir / "vivado_stdout.log").write_text(proc.stdout or "")
    (run_dir / "vivado_stderr.log").write_text(proc.stderr or "")
    if proc.returncode != 0:
        raise RuntimeError(
            f"Vivado failed for n={n}, design={design}, rc={proc.returncode}\n"
            f"See logs: {run_dir / 'vivado_stdout.log'} and {run_dir / 'vivado_stderr.log'}"
        )

    kv = _parse_kv(run_dir / "metrics_kv.txt")
    stage = kv.get("stage", "impl" if run_impl else "synth")
    util = _parse_utilization(run_dir / f"utilization_{stage}.rpt")
    power = _parse_power(run_dir / f"power_{stage}.rpt")

    row = {
        "n": n,
        "design": design,
        "part": part,
        "stage": stage,
        "runtime_s": round(runtime_s, 6),
        "lut_cells": _to_float(kv.get("lut_cells", "nan")),
        "ff_cells": _to_float(kv.get("ff_cells", "nan")),
        "carry4_cells": _to_float(kv.get("carry4_cells", "nan")),
        "dsp_cells": _to_float(kv.get("dsp_cells", "nan")),
        "ramb18_cells": _to_float(kv.get("ramb18_cells", "nan")),
        "ramb36_cells": _to_float(kv.get("ramb36_cells", "nan")),
        "wns_ns": _to_float(kv.get("wns_ns", "nan")),
        "datapath_delay_ns": _to_float(kv.get("datapath_delay_ns", "nan")),
        "logic_levels": _to_float(kv.get("logic_levels", "nan")),
        "clb_luts": util["clb_luts"],
        "clb_regs": util["clb_regs"],
        "carry4": util["carry4"],
        "dsp": util["dsp"],
        "ramb18": util["ramb18"],
        "ramb36": util["ramb36"],
        "total_power_w": power["total_power_w"],
        "dynamic_power_w": power["dynamic_power_w"],
        "static_power_w": power["static_power_w"],
    }
    return row


def _pair_rows(rows: List[Dict[str, float]]) -> List[Dict[str, float]]:
    by_n: Dict[int, Dict[str, Dict[str, float]]] = {}
    for r in rows:
        n = int(r["n"])
        by_n.setdefault(n, {})[str(r["design"])] = r

    out: List[Dict[str, float]] = []
    metrics = [
        "runtime_s",
        "lut_cells",
        "ff_cells",
        "carry4_cells",
        "wns_ns",
        "datapath_delay_ns",
        "logic_levels",
        "clb_luts",
        "clb_regs",
        "carry4",
        "dsp",
        "ramb18",
        "ramb36",
        "total_power_w",
        "dynamic_power_w",
        "static_power_w",
    ]

    for n in sorted(by_n):
        pair = by_n[n]
        if "folded" not in pair or "baseline" not in pair:
            continue
        fb = pair["folded"]
        bs = pair["baseline"]
        row: Dict[str, float] = {
            "n": n,
            "part": fb["part"],
            "stage": fb["stage"],
        }
        for m in metrics:
            row[f"folded_{m}"] = fb[m]
            row[f"baseline_{m}"] = bs[m]
            # delta = baseline - folded (except WNS where larger is better; keep same sign convention anyway)
            row[f"delta_{m}_baseline_minus_folded"] = bs[m] - fb[m]
        out.append(row)
    return out


def _resolve_vivado(explicit: str | None) -> str:
    if explicit and Path(explicit).is_file():
        return explicit
    env = os.environ.get("VIVADO_BIN")
    if env and Path(env).is_file():
        return env
    for c in (
        "/tools/Xilinx/Vivado/2024.2/bin/vivado",
        "/home/mrunal/Desktop/Xilinx/Vivado/2024.2/bin/vivado",
    ):
        if Path(c).is_file():
            return c
    from shutil import which

    w = which("vivado")
    if w:
        return w
    raise FileNotFoundError("Vivado binary not found. Pass --vivado-bin or set VIVADO_BIN.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Vivado comparison for folded vs baseline majority designs.")
    parser.add_argument("--n-start", type=int, default=5)
    parser.add_argument("--n-end", type=int, default=61)
    parser.add_argument("--part", default="xc7a100tcsg324-1")
    parser.add_argument("--vivado-bin", default=None)
    parser.add_argument("--synth-only", action="store_true", help="Run only synthesis (skip place/route).")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: results/vivado_compare_<start>_<end>).",
    )
    args = parser.parse_args()

    if args.n_start > args.n_end:
        raise ValueError("--n-start must be <= --n-end")
    ns = [n for n in range(args.n_start, args.n_end + 1) if n >= 3 and (n % 2 == 1)]
    if not ns:
        raise ValueError("No odd n values in requested range.")

    vivado = _resolve_vivado(args.vivado_bin)
    run_impl = not args.synth_only

    root = Path(__file__).resolve().parent
    out_dir = Path(args.output_dir) if args.output_dir else (root / "results" / f"vivado_compare_{args.n_start}_{args.n_end}")
    out_dir.mkdir(parents=True, exist_ok=True)

    detailed_rows: List[Dict[str, float]] = []
    for n in ns:
        for design in ("folded", "baseline"):
            row = _run_single(
                vivado_bin=vivado,
                n=n,
                design=design,
                part=args.part,
                run_impl=run_impl,
                work_dir=out_dir / "runs",
            )
            detailed_rows.append(row)
            print(
                f"[Vivado] n={n:>3} design={design:<8} stage={row['stage']:<5} "
                f"CLB_LUTs={row['clb_luts']} delay_ns={row['datapath_delay_ns']} power_w={row['total_power_w']}"
            )

    detail_csv = out_dir / "vivado_detailed.csv"
    with detail_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(detailed_rows[0].keys()))
        writer.writeheader()
        writer.writerows(detailed_rows)

    paired_rows = _pair_rows(detailed_rows)
    pair_csv = out_dir / "vivado_comparison.csv"
    with pair_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(paired_rows[0].keys()))
        writer.writeheader()
        writer.writerows(paired_rows)

    print(f"Wrote detailed CSV: {detail_csv}")
    print(f"Wrote comparison CSV: {pair_csv}")
    print(f"Run directory: {out_dir / 'runs'}")


if __name__ == "__main__":
    main()
