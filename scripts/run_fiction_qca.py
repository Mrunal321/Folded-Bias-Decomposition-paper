#!/usr/bin/env python3
"""Run the pinned Fiction QCA-ONE physical-design flow on generated B/FB BLIFs."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from run_strong_flow import ABC_ROUND, abc_path, resolve_executable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = (
    "mawalter/fiction@sha256:"
    "c93abd35f49078d637414ce58bc03834298911ed704ec8edd960f1f76214c396"
)
FICTION_ENTRYPOINT = "/app/fiction/build/cli/fiction"

ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
PROGRESS = re.compile(r"\x1b\[G\[i\][^\x1b\r\n]*?: \|[. ]{5}\|")
NETWORK = re.compile(
    r"\[i\] (?P<name>.+) \(TEC\) - I/O: (?P<pis>\d+)/(?P<pos>\d+), "
    r"gates: (?P<gates>\d+), level: (?P<level>\d+)"
)
GATE_LAYOUT = re.compile(
    r"\[i\] (?P<name>.+) \(2DDWAVE\) - (?P<x>\d+) × (?P<y>\d+), "
    r"I/O: (?P<pis>\d+)/(?P<pos>\d+), gates: (?P<gates>\d+), "
    r"wires: (?P<wires>\d+), crossings: (?P<crossings>\d+), CP: (?P<cp>\d+), "
    r"TP: (?P<tp>[^,]+), sync\. elems\.: (?P<sync>\d+)"
)
CELL_LAYOUT = re.compile(
    r"\[i\] (?P<name>.+) \(QCA\) - (?P<x>\d+) × (?P<y>\d+), "
    r"I/O: (?P<pis>\d+)/(?P<pos>\d+), cells: (?P<cells>\d+)"
)
AREA = re.compile(r"\[i\] (?P<area>\d+) nm²")
EQUIV = re.compile(
    r"are (?P<kind>NOT|WEAKLY|STRONGLY) equivalent"
    r"(?: with a delay difference of (?P<delay>\d+) clock cycles)?"
)
DRVS = re.compile(r"DRVs: (?P<drvs>\d+), Warnings: (?P<warnings>\d+)")


def parse_values(text: str) -> list[int]:
    values = [int(item) for item in text.replace(",", " ").split()]
    if not values or any(value < 3 or value % 2 == 0 for value in values):
        raise argparse.ArgumentTypeError("n values must be odd integers >= 3")
    return list(dict.fromkeys(values))


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.name


def clean_output(text: str) -> str:
    compact = ANSI.sub("", PROGRESS.sub("", text)).replace("\r", "\n")
    return re.sub(r"\n{3,}", "\n\n", compact)


def run(
    command: list[str], timeout: int | None
) -> tuple[subprocess.CompletedProcess[str], float]:
    started = time.perf_counter()
    try:
        process = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout if isinstance(error.stdout, str) else ""
        stderr = error.stderr if isinstance(error.stderr, str) else ""
        process = subprocess.CompletedProcess(command, 124, stdout, stderr + "\nTIMEOUT\n")
    return process, time.perf_counter() - started


def last_match(pattern: re.Pattern[str], text: str) -> dict[str, str] | None:
    matches = list(pattern.finditer(text))
    return matches[-1].groupdict() if matches else None


def normalize_with_abc(abc: Path, source: Path, output: Path) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    commands = [f"read_blif {abc_path(source)}", "strash"]
    commands.extend(ABC_ROUND * 3)
    commands.extend(
        [
            f"write_blif {abc_path(output)}",
            f"cec -T 0 {abc_path(source)} {abc_path(output)}",
        ]
    )
    # ABC's CEC limit is disabled with -T 0, and this subprocess deliberately has
    # no outer wall-clock watchdog.  Physical-layout commands retain their own
    # configurable timeout below.
    process, elapsed = run([str(abc), "-q", "; ".join(commands)], None)
    text = process.stdout + "\n" + process.stderr
    if "Networks are equivalent" in text:
        status = "equivalent"
    elif "Networks are NOT EQUIVALENT" in text:
        status = "not_equivalent"
    else:
        status = "undecided"
    if process.returncode or status != "equivalent" or not output.is_file():
        raise RuntimeError(
            f"ABC normalization/CEC failed for {relative(source)}: "
            f"returncode={process.returncode}, status={status}"
        )
    return {"status": status, "elapsed_s": round(elapsed, 6)}


def parse_fiction(text: str) -> dict[str, object]:
    result: dict[str, object] = {}
    networks = list(NETWORK.finditer(text))
    if networks:
        normalized = networks[0].groupdict()
        mapped = networks[-1].groupdict()
        result["normalized_network"] = {
            key: int(value) for key, value in normalized.items() if key != "name"
        }
        result["mapped_network"] = {
            key: int(value) for key, value in mapped.items() if key != "name"
        }
    gate = last_match(GATE_LAYOUT, text)
    if gate:
        result["gate_layout"] = {
            key: (value if key == "tp" else int(value))
            for key, value in gate.items()
            if key != "name"
        }
    drv = last_match(DRVS, text)
    if drv:
        result["design_rule_check"] = {
            "drvs": int(drv["drvs"]),
            "warnings": int(drv["warnings"]),
        }
    equivalence = last_match(EQUIV, text)
    if equivalence:
        result["layout_equivalence"] = {
            "kind": equivalence["kind"].lower(),
            "delay_difference_cycles": int(equivalence["delay"] or 0),
        }
    cell = last_match(CELL_LAYOUT, text)
    if cell:
        result["cell_layout"] = {
            key: int(value) for key, value in cell.items() if key != "name"
        }
    area = last_match(AREA, text)
    if area:
        area_nm2 = int(area["area"])
        result["cell_area_nm2"] = area_nm2
        result["cell_area_um2"] = area_nm2 / 1_000_000
    return result


def validate_case(record: dict[str, object]) -> None:
    parsed = record["fiction"]
    assert isinstance(parsed, dict)
    required = ("gate_layout", "design_rule_check", "layout_equivalence", "cell_layout", "cell_area_nm2")
    missing = [key for key in required if key not in parsed]
    if missing:
        raise RuntimeError(
            f"Fiction output is missing {', '.join(missing)} for n={record['n']} {record['method']}"
        )
    drv = parsed["design_rule_check"]
    equivalence = parsed["layout_equivalence"]
    assert isinstance(drv, dict) and isinstance(equivalence, dict)
    if drv["drvs"] != 0 or drv["warnings"] != 0:
        raise RuntimeError(f"Fiction design-rule check was not clean for n={record['n']} {record['method']}")
    if equivalence["kind"] not in ("weakly", "strongly"):
        raise RuntimeError(f"Fiction reported non-equivalence for n={record['n']} {record['method']}")
    if record["layout_export_requested"] and not record["layout_exported"]:
        raise RuntimeError(f"Fiction did not export the requested layout for n={record['n']} {record['method']}")


def summarize(records: list[dict[str, object]]) -> dict[str, object]:
    pairs: dict[int, dict[str, dict[str, object]]] = {}
    for record in records:
        pairs.setdefault(int(record["n"]), {})[str(record["method"])] = record
    metrics = {
        "cell_area_um2": ("fiction", "cell_area_um2"),
        "qca_cells": ("fiction", "cell_layout", "cells"),
        "critical_path_clock_zones": ("fiction", "gate_layout", "cp"),
        "gate_wires": ("fiction", "gate_layout", "wires"),
        "gate_crossings": ("fiction", "gate_layout", "crossings"),
    }
    aggregate: dict[str, object] = {}
    for metric, keys in metrics.items():
        deltas: list[float] = []
        for methods in pairs.values():
            if set(methods) != {"B", "FB"}:
                continue
            values: dict[str, float] = {}
            for method in ("B", "FB"):
                value: object = methods[method]
                for key in keys:
                    assert isinstance(value, dict)
                    value = value[key]
                values[method] = float(value)
            deltas.append(values["B"] - values["FB"])
        aggregate[metric] = {
            "cases": len(deltas),
            "mean_baseline_minus_folded": sum(deltas) / len(deltas),
            "folded_wins": sum(delta > 0 for delta in deltas),
            "ties": sum(delta == 0 for delta in deltas),
            "folded_losses": sum(delta < 0 for delta in deltas),
        }
    return {
        "case_count": len(records),
        "paired_n_count": len(pairs),
        "abc_cec_equivalent": sum(
            record["abc_source_vs_normalized_cec"]["status"] == "equivalent"  # type: ignore[index]
            for record in records
        ),
        "clean_design_rule_checks": len(records),
        "layout_equivalence_reports": len(records),
        "paired_deltas": aggregate,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--n-values",
        type=parse_values,
        default=parse_values("5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,43,45,47,49,51,53,55,57,59,61"),
    )
    parser.add_argument("--input-root", type=Path, default=Path("build/reproduction/netlists"))
    parser.add_argument("--output-root", type=Path, default=Path("build/reproduction/fiction_qca"))
    parser.add_argument("--abc-bin", default=os.environ.get("ABC_BIN", "abc"))
    parser.add_argument("--docker-bin", default=os.environ.get("DOCKER_BIN", "docker"))
    parser.add_argument("--image", default=os.environ.get("FICTION_IMAGE", DEFAULT_IMAGE))
    parser.add_argument("--export-layout-n", type=parse_values, default=parse_values("5,31,61"))
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    if "@sha256:" not in args.image:
        raise SystemExit("--image must use an immutable Docker digest, not a floating tag")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")

    abc = resolve_executable(args.abc_bin)
    docker = resolve_executable(args.docker_bin)
    if abc is None:
        raise SystemExit("ABC is required; set --abc-bin or ABC_BIN")
    if docker is None:
        raise SystemExit("Docker is required; set --docker-bin or DOCKER_BIN")

    input_root = args.input_root if args.input_root.is_absolute() else REPO_ROOT / args.input_root
    output_root = args.output_root if args.output_root.is_absolute() else REPO_ROOT / args.output_root
    normalized_root = output_root / "normalized"
    layouts_root = output_root / "layouts"
    logs_root = output_root / "logs"
    for directory in (normalized_root, layouts_root, logs_root):
        directory.mkdir(parents=True, exist_ok=True)

    version_process, _ = run(
        [
            str(docker),
            "run",
            "--rm",
            "--entrypoint",
            FICTION_ENTRYPOINT,
            args.image,
            "-c",
            "version",
        ],
        120,
    )
    version_text = clean_output(version_process.stdout + "\n" + version_process.stderr).strip()
    if version_process.returncode or "fiction v0.6.5" not in version_text:
        raise RuntimeError(
            "the pinned Fiction image did not report the expected v0.6.5 version"
        )

    records: list[dict[str, object]] = []
    for n in args.n_values:
        paths = {
            "B": input_root / f"n{n}" / "baseline" / f"maj_baseline_strict_{n}.blif",
            "FB": input_root / f"n{n}" / "folded_bias" / f"maj_fb_{n}.blif",
        }
        for method, source in paths.items():
            if not source.is_file():
                raise SystemExit(
                    f"missing {relative(source)}; generate the requested n values before running Fiction"
                )
            normalized = normalized_root / f"n{n}_{method}.blif"
            cec = normalize_with_abc(abc, source, normalized)
            export = n in set(args.export_layout_n)
            layout = layouts_root / f"n{n}_{method}.qca"
            if layout.exists():
                layout.unlink()
            export_command = f"; qca /work/layouts/{layout.name}" if export else ""
            fiction_commands = (
                f"read -t /work/inputs/{normalized.name}; ps -n; "
                "map -a -o -i; ps -n; ortho -n 4; ps -g; check; "
                "equiv -n -g; cell -l QCA-ONE; ps -c; area"
                f"{export_command}"
            )
            command = [
                str(docker),
                "run",
                "--rm",
                "--entrypoint",
                FICTION_ENTRYPOINT,
                "-v",
                f"{normalized_root.resolve()}:/work/inputs:ro",
                "-v",
                f"{layouts_root.resolve()}:/work/layouts",
                args.image,
                "-c",
                fiction_commands,
            ]
            process, elapsed = run(command, args.timeout)
            output = clean_output(process.stdout + "\n" + process.stderr)
            (logs_root / f"n{n}_{method}.txt").write_text(output + "\n", encoding="utf-8")
            if process.returncode:
                raise RuntimeError(
                    f"Fiction failed for n={n} {method}: returncode={process.returncode}"
                )
            record: dict[str, object] = {
                "n": n,
                "method": method,
                "source_blif": relative(source),
                "normalized_blif": relative(normalized),
                "abc_source_vs_normalized_cec": cec,
                "fiction_elapsed_s": round(elapsed, 6),
                "layout_export_requested": export,
                "layout_exported": layout.is_file(),
                "fiction": parse_fiction(output),
            }
            validate_case(record)
            records.append(record)
            print(f"[fiction] PASS n={n} method={method}", flush=True)

    report = {
        "schema": 1,
        "image": args.image,
        "expected_fiction_version": "v0.6.5",
        "reported_version_output": version_text,
        "cell_library": "QCA-ONE",
        "clocking": "2DDWave",
        "abc_normalization": "strash plus three fixed resyn2-style rounds",
        "abc_cec": "cec -T 0 (ABC-internal limit disabled; no outer process timeout)",
        "fiction_commands": "read -t; map -a -o -i; ortho -n 4; check; equiv -n -g; cell -l QCA-ONE; area",
        "summary": summarize(records),
        "cases": records,
    }
    report_path = output_root / "fiction_qca.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[fiction] report={relative(report_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
