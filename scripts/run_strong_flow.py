#!/usr/bin/env python3
"""Run optional ABC and Mockturtle checks on a generated netlist suite."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MOCKTURTLE_COMMIT = "420f0271ab9f63a1644bf465ab47c970c173bd7b"
MOCKTURTLE_MAX_PIS = 8
MOCKTURTLE_MAX_INSERTS = 1
ABC_LUT_INPUTS = 6
PAPER_N_COUNT = 29
METHOD_COUNT = 2
POST_OPTIMIZATION_STAGE_COUNT = 3
ABC_ROUND = [
    "balance",
    "rewrite",
    "refactor",
    "balance",
    "rewrite",
    "rewrite -z",
    "balance",
    "refactor -z",
    "rewrite -z",
    "balance",
]
STAT_RE = re.compile(
    r"i/o\s*=\s*(?P<inputs>\d+)\s*/\s*(?P<outputs>\d+).*?"
    r"(?:and|nd)\s*=\s*(?P<nodes>\d+).*?lev\s*=\s*(?P<levels>\d+)",
    re.IGNORECASE,
)


def parse_n_values(text: str) -> list[int]:
    values = [int(item) for item in text.replace(",", " ").split()]
    if not values or any(value < 3 or value % 2 == 0 for value in values):
        raise argparse.ArgumentTypeError("n values must be odd integers >= 3")
    return list(dict.fromkeys(values))


def resolve_executable(value: str) -> Path | None:
    if not value:
        return None
    candidate = Path(value)
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return candidate.resolve()
    found = shutil.which(value)
    return Path(found).resolve() if found else None


def abc_path(path: Path) -> str:
    return '"' + str(path.resolve()).replace('"', '\\"') + '"'


def report_path(path: Path) -> str:
    """Return a portable artifact path without exposing an external filesystem."""

    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return f"<external-output>/{path.name}"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def abc_version(abc: Path) -> str:
    """Return ABC's canonical version line without recording a local path."""

    process = run([str(abc), "-q", "version"])
    for raw_line in (process.stdout + "\n" + process.stderr).splitlines():
        line = " ".join(raw_line.split())
        if re.match(r"^UC Berkeley, ABC\b", line) and not any(
            marker in line for marker in ("/", "\\", "@")
        ):
            return line
    return "unreported"


def parse_stats(stdout: str) -> list[dict[str, int]]:
    return [
        {key: int(value) for key, value in match.groupdict().items()}
        for match in STAT_RE.finditer(stdout)
    ]


def prepare_output(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()


def require_output(path: Path, label: str) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"{label} did not produce an optimized BLIF")


def run_abc(
    abc: Path,
    source: Path,
    strong_output: Path | None = None,
    lut6_output: Path | None = None,
) -> dict[str, object]:
    if (strong_output is None) != (lut6_output is None):
        raise ValueError("strong_output and lut6_output must be provided together")
    write_outputs = strong_output is not None and lut6_output is not None
    if write_outputs:
        assert strong_output is not None and lut6_output is not None
        prepare_output(strong_output)
        prepare_output(lut6_output)
    script = [f"read_blif {abc_path(source)}", "strash", "ps"]
    script.extend(ABC_ROUND * 3)
    script.append("ps")
    if write_outputs:
        assert strong_output is not None and lut6_output is not None
        script.extend(
            [
                f"write_blif {abc_path(strong_output)}",
                f"read_blif {abc_path(strong_output)}",
                "strash",
            ]
        )
    script.extend([f"if -K {ABC_LUT_INPUTS}", "ps"])
    if write_outputs:
        assert lut6_output is not None
        script.append(f"write_blif {abc_path(lut6_output)}")
    started = time.perf_counter()
    process = run([str(abc), "-q", "; ".join(script)])
    elapsed = time.perf_counter() - started
    if process.returncode:
        raise RuntimeError(process.stderr.strip() or process.stdout.strip())
    stats = parse_stats(process.stdout)
    if len(stats) < 3:
        raise RuntimeError("could not parse the raw, strong-AIG, and LUT6 ABC checkpoints")
    if write_outputs:
        assert strong_output is not None and lut6_output is not None
        require_output(strong_output, "ABC strong flow")
        require_output(lut6_output, "ABC LUT6 flow")
    return {
        "raw_aig": stats[-3],
        "strong_aig": stats[-2],
        "lut6": stats[-1],
        "elapsed_s": round(elapsed, 6),
    }


def run_cec(abc: Path, baseline: Path, folded: Path) -> dict[str, object]:
    # ABC's plain `cec` otherwise applies a 20-second default limit.  `-T 0`
    # disables that runtime bound for the FRAIG+SAT flow.  Optimizers may
    # rename ports, so `-n` deliberately matches combinational I/O by order.
    script = f"cec -n -T 0 {abc_path(baseline)} {abc_path(folded)}"
    started = time.perf_counter()
    process = run([str(abc), "-q", script])
    elapsed = time.perf_counter() - started
    text = process.stdout + "\n" + process.stderr
    # A recognized verdict is authoritative even if a checker uses a nonzero
    # exit code for inequivalence.  A nonzero run without a verdict is a tool
    # failure, while a zero/no-verdict run is genuinely undecided.
    if "Networks are equivalent" in text:
        status = "equivalent"
    elif "Networks are NOT EQUIVALENT" in text:
        status = "not_equivalent"
    elif process.returncode != 0:
        status = "tool_error"
    else:
        status = "undecided"
    return {"status": status, "returncode": process.returncode, "elapsed_s": round(elapsed, 6)}


def parse_mockturtle(stdout: str) -> dict[str, object]:
    for line in stdout.splitlines():
        if not line.startswith("RESULT "):
            continue
        result: dict[str, object] = {}
        for token in line.split()[1:]:
            key, value = token.split("=", 1)
            try:
                result[key] = int(value)
            except ValueError:
                result[key] = value
        return result
    raise RuntimeError("Mockturtle output did not contain a RESULT line")


def run_mockturtle(
    binary: Path,
    source: Path,
    output: Path,
    recipe: str,
    rounds: int,
) -> dict[str, object]:
    prepare_output(output)
    started = time.perf_counter()
    process = run(
        [
            str(binary),
            "--input",
            str(source),
            "--output",
            str(output),
            "--recipe",
            recipe,
            "--rounds",
            str(rounds),
            "--max-pis",
            str(MOCKTURTLE_MAX_PIS),
            "--max-inserts",
            str(MOCKTURTLE_MAX_INSERTS),
        ]
    )
    elapsed = time.perf_counter() - started
    if process.returncode:
        raise RuntimeError(process.stderr.strip() or process.stdout.strip())
    require_output(output, "Mockturtle strong flow")
    return {**parse_mockturtle(process.stdout), "elapsed_s": round(elapsed, 6)}


def run_mockturtle_cec(binary: Path, baseline: Path, folded: Path) -> dict[str, object]:
    started = time.perf_counter()
    process = run([str(binary), str(baseline), str(folded)])
    elapsed = time.perf_counter() - started
    output = process.stdout + "\n" + process.stderr
    # The helper intentionally returns one for a valid NOT_EQUIVALENT verdict.
    if "RESULT=EQUIVALENT" in output:
        status = "equivalent"
    elif "RESULT=NOT_EQUIVALENT" in output:
        status = "not_equivalent"
    elif process.returncode != 0:
        status = "tool_error"
    else:
        status = "undecided"
    return {
        "status": status,
        "returncode": process.returncode,
        "elapsed_s": round(elapsed, 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-values", type=parse_n_values, default=parse_n_values("5,7,9,11,13"))
    parser.add_argument("--input-root", type=Path, default=Path("build/reproduction/netlists"))
    parser.add_argument("--output", type=Path, default=Path("build/reproduction/strong_flow.json"))
    parser.add_argument(
        "--optimized-root",
        type=Path,
        default=Path("build/reproduction/strong_flow/optimized"),
        help="directory for regenerated optimized BLIFs",
    )
    parser.add_argument("--abc-bin", default=os.environ.get("ABC_BIN", "abc"))
    parser.add_argument(
        "--mockturtle-bin",
        default=os.environ.get(
            "MOCKTURTLE_BIN", "tools/mockturtle_mig_opt/build/mockturtle_mig_opt"
        ),
    )
    parser.add_argument(
        "--mockturtle-cec-bin",
        default=os.environ.get(
            "MOCKTURTLE_CEC_BIN",
            "tools/mockturtle_mig_opt/build/mockturtle_blif_cec",
        ),
    )
    parser.add_argument("--mockturtle-recipe", default="resub_depth_resub2")
    parser.add_argument("--mockturtle-rounds", type=int, default=6)
    parser.add_argument("--require-abc", action="store_true")
    parser.add_argument("--require-mockturtle", action="store_true")
    parser.add_argument("--require-mockturtle-cec", action="store_true")
    args = parser.parse_args()

    abc = resolve_executable(args.abc_bin)
    mockturtle = resolve_executable(args.mockturtle_bin)
    mockturtle_cec = resolve_executable(args.mockturtle_cec_bin)
    if args.require_abc and abc is None:
        print("ABC was requested but could not be found; set ABC_BIN.", file=sys.stderr)
        return 2
    if args.require_mockturtle and mockturtle is None:
        print("Mockturtle was requested but could not be found; set MOCKTURTLE_BIN.", file=sys.stderr)
        return 2
    if args.require_mockturtle_cec and mockturtle_cec is None:
        print(
            "Mockturtle CEC was requested but could not be found; set MOCKTURTLE_CEC_BIN.",
            file=sys.stderr,
        )
        return 2
    print(f"[strong] ABC={'enabled' if abc else 'not found; skipped'}")
    print(f"[strong] Mockturtle={'enabled' if mockturtle else 'not found; skipped'}")
    print(
        f"[strong] Mockturtle CEC="
        f"{'enabled' if mockturtle_cec else 'not found; skipped'}"
    )
    abc_version_text = abc_version(abc) if abc else None

    input_root = args.input_root if args.input_root.is_absolute() else REPO_ROOT / args.input_root
    optimized_root = (
        args.optimized_root
        if args.optimized_root.is_absolute()
        else REPO_ROOT / args.optimized_root
    )
    cases: list[dict[str, object]] = []
    post_cec_summary = {
        "expected": 0,
        "executed": 0,
        "equivalent": 0,
        "undecided": 0,
        "not_equivalent": 0,
        "tool_error": 0,
    }
    post_cec_checkers: set[str] = set()
    failed = False
    for n in args.n_values:
        case_dir = input_root / f"n{n}"
        paths = {
            "folded_bias": case_dir / "folded_bias" / f"maj_fb_{n}.blif",
            "baseline": case_dir / "baseline" / f"maj_baseline_strict_{n}.blif",
        }
        if any(not path.is_file() for path in paths.values()):
            print(f"missing generated inputs for n={n}", file=sys.stderr)
            return 2
        record: dict[str, object] = {"n": n, "designs": {}}
        designs = record["designs"]
        assert isinstance(designs, dict)
        for label, path in paths.items():
            result: dict[str, object] = {}
            artifact_dir = optimized_root / f"n{n}" / label
            optimized = {
                "mockturtle_strong": artifact_dir / "mockturtle_strong.blif",
                "abc_strong": artifact_dir / "abc_strong.blif",
                "abc_lut6": artifact_dir / "abc_lut6.blif",
            }
            if abc:
                result["abc"] = run_abc(
                    abc,
                    path,
                    optimized["abc_strong"],
                    optimized["abc_lut6"],
                )
            if mockturtle:
                result["mockturtle"] = run_mockturtle(
                    mockturtle,
                    path,
                    optimized["mockturtle_strong"],
                    args.mockturtle_recipe,
                    args.mockturtle_rounds,
                )
            generated_stages: list[str] = []
            if mockturtle:
                generated_stages.append("mockturtle_strong")
            if abc:
                generated_stages.extend(("abc_strong", "abc_lut6"))
            result["optimized_blifs"] = {
                stage: report_path(optimized[stage])
                for stage in generated_stages
            }
            post_cec_summary["expected"] += len(generated_stages)
            post_cec: dict[str, object] = {}
            if abc:
                cec_stages = ["abc_strong", "abc_lut6"]
                if mockturtle:
                    cec_stages.insert(0, "mockturtle_strong")
                for stage in cec_stages:
                    cec = {
                        **run_cec(abc, path, optimized[stage]),
                        "checker": "abc",
                    }
                    post_cec[stage] = cec
                    post_cec_checkers.add("ABC cec -n -T 0")
                    post_cec_summary["executed"] += 1
                    status = str(cec["status"])
                    post_cec_summary[status] += 1
                    failed |= status != "equivalent"
                    print(
                        f"[strong] n={n} {label} {stage} source-CEC={status}"
                    )
            elif mockturtle and mockturtle_cec:
                cec = {
                    **run_mockturtle_cec(
                        mockturtle_cec,
                        path,
                        optimized["mockturtle_strong"],
                    ),
                    "checker": "mockturtle",
                }
                post_cec["mockturtle_strong"] = cec
                post_cec_checkers.add("Mockturtle equivalence_checking conflict_limit=0")
                post_cec_summary["executed"] += 1
                status = str(cec["status"])
                post_cec_summary[status] += 1
                failed |= status != "equivalent"
                print(
                    f"[strong] n={n} {label} mockturtle_strong "
                    f"source-CEC={status}"
                )
            result["source_vs_optimized_cec"] = post_cec
            designs[label] = result
        if abc:
            cec = run_cec(abc, paths["baseline"], paths["folded_bias"])
            record["baseline_vs_folded_cec"] = cec
            failed |= cec["status"] != "equivalent"
            print(f"[strong] n={n} ABC-CEC={cec['status']}")
        if mockturtle_cec:
            cec = run_mockturtle_cec(
                mockturtle_cec, paths["baseline"], paths["folded_bias"]
            )
            record["mockturtle_baseline_vs_folded_cec"] = cec
            failed |= cec["status"] != "equivalent"
            print(f"[strong] n={n} Mockturtle-CEC={cec['status']}")
        cases.append(record)

    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    post_cec_applicable = post_cec_summary["expected"] > 0
    if not post_cec_applicable:
        post_cec_status = "not_run"
    elif post_cec_summary["executed"] != post_cec_summary["expected"]:
        post_cec_status = "incomplete"
    elif (
        post_cec_summary["undecided"]
        or post_cec_summary["not_equivalent"]
        or post_cec_summary["tool_error"]
    ):
        post_cec_status = "failed"
    else:
        post_cec_status = "complete"
    output.write_text(
        json.dumps(
            {
                "schema": 2,
                "tools": {
                    "abc": bool(abc),
                    "mockturtle": bool(mockturtle),
                    "mockturtle_cec": bool(mockturtle_cec),
                },
                "provenance": {
                    "abc": {
                        "enabled": bool(abc),
                        "version": abc_version_text,
                        "input_format": "BLIF",
                        "strong_aig_recipe": {
                            "preprocess": ["strash"],
                            "rounds": 3,
                            "commands_per_round": ABC_ROUND,
                        },
                        "lut6_mapping": {
                            "command": f"if -K {ABC_LUT_INPUTS}",
                            "lut_inputs": ABC_LUT_INPUTS,
                        },
                        "cec": {
                            "command": "cec -n -T 0 <reference> <candidate>",
                            "io_matching": "order",
                            "runtime_limit_seconds": None,
                            "runtime_limit_disabled": True,
                        },
                    },
                    "mockturtle": {
                        "source_commit": MOCKTURTLE_COMMIT,
                        "optimizer": {
                            "enabled": bool(mockturtle),
                            "recipe": args.mockturtle_recipe,
                            "rounds": args.mockturtle_rounds,
                            "max_pis": MOCKTURTLE_MAX_PIS,
                            "max_inserts": MOCKTURTLE_MAX_INSERTS,
                        },
                        "cec": {
                            "enabled": bool(mockturtle_cec),
                            "conflict_limit": 0,
                        },
                    },
                },
                "post_optimization_cec_summary": {
                    **post_cec_summary,
                    "artifact_root": report_path(optimized_root),
                    "checker_enabled": bool(
                        abc or (mockturtle and mockturtle_cec)
                    ),
                    "applicable": post_cec_applicable,
                    "complete": post_cec_status == "complete",
                    "checkers": sorted(post_cec_checkers),
                    "scope": "generated source BLIF versus each optimized BLIF",
                    "status": post_cec_status,
                    "paper_profile_expected_with_both_tools": (
                        PAPER_N_COUNT * METHOD_COUNT * POST_OPTIMIZATION_STAGE_COUNT
                    ),
                },
                "cases": cases,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"[strong] report={output.relative_to(REPO_ROOT) if output.is_relative_to(REPO_ROOT) else output.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
