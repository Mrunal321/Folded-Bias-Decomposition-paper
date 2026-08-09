#!/usr/bin/env python3
"""Generate and verify direct and folded implementations of general thresholds."""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import final_generator as fg
from verify_blif import read_blif, simulate_many
from run_strong_flow import resolve_executable, run_abc, run_cec


REPO_ROOT = Path(__file__).resolve().parents[1]
SEED = 20260710


@dataclass
class Netlist:
    n: int
    threshold: int
    method: str
    fa_ops: list[tuple[str, str, str, str, str]]
    const1: list[str]
    output: str
    logic_ops: list[tuple[str, tuple[str, ...], str]]
    diagnostics: dict[str, object]


def parse_n_values(text: str) -> list[int]:
    values = [int(item) for item in text.replace(",", " ").split()]
    if not values or any(value < 3 for value in values):
        raise argparse.ArgumentTypeError("n values must be integers >= 3")
    return list(dict.fromkeys(values))


def compress(inputs: list[str], bias: int) -> tuple[list[tuple[str, str, str, str, str]], dict[int, str], list[str]]:
    constants: defaultdict[int, list[str]] = defaultdict(list)
    const1: list[str] = []
    for bit in range(max(1, bias.bit_length())):
        if (bias >> bit) & 1:
            name = f"K{bit}"
            constants[bit].append(name)
            const1.append(name)
    scheduled, _, residual, _ = fg.csa_macro_schedule_all_columns(inputs, constants)
    fa_ops = [(a, b, c, s, carry) for _, _, a, b, c, s, carry in scheduled]
    return fa_ops, dict(residual), const1


def high_bit_or(residual: dict[int, str], first: int) -> tuple[str, list[tuple[str, tuple[str, ...], str]]]:
    signals = [residual[index] for index in sorted(residual) if index >= first and residual[index] != "1'b0"]
    if not signals:
        return "1'b0", []
    if len(signals) == 1:
        return signals[0], []
    operations: list[tuple[str, tuple[str, ...], str]] = []
    current = signals[0]
    for index, signal in enumerate(signals[1:]):
        output = f"decision_or_{index}"
        operations.append(("or2", (current, signal), output))
        current = output
    return current, operations


def build_folded(n: int, threshold: int) -> Netlist:
    width = math.ceil(math.log2(threshold))
    bias = (1 << width) - threshold
    fa_ops, residual, const1 = compress([f"x[{i}]" for i in range(n)], bias)
    output, logic = high_bit_or(residual, width)
    return Netlist(
        n,
        threshold,
        "folded_bias",
        fa_ops,
        const1,
        output,
        logic,
        {
            "w": width,
            "K": bias,
            "popcount_K": bias.bit_count(),
            "carry_only_valid": n + bias < (1 << (width + 1)),
            "decision_high_bits": sum(1 for index in residual if index >= width),
        },
    )


def build_direct(n: int, threshold: int) -> Netlist:
    fa_ops, residual, const1 = compress([f"x[{i}]" for i in range(n)], 0)
    width = math.ceil(math.log2(n + 1))
    compare_constant = (1 << width) - threshold
    carry = "1'b0"
    for bit in range(width):
        a = residual.get(bit, "1'b0")
        b = f"C{bit}" if (compare_constant >> bit) & 1 else "1'b0"
        if b != "1'b0":
            const1.append(b)
        sum_signal = f"cmp_s{bit}"
        next_carry = f"cmp_c{bit + 1}"
        fa_ops.append((a, b, carry, sum_signal, next_carry))
        carry = next_carry
    return Netlist(
        n,
        threshold,
        "direct_csa_threshold",
        fa_ops,
        const1,
        carry,
        [],
        {"comparison_width": width, "comparison_constant": compare_constant},
    )


def sanitize(signal: str) -> str:
    if signal.startswith("x[") and signal.endswith("]"):
        return "x" + signal[2:-1]
    return re.sub(r"[^A-Za-z0-9_$]", "_", signal)


def write_blif(netlist: Netlist, path: Path) -> None:
    lines = [
        f".model {netlist.method}_n{netlist.n}_T{netlist.threshold}",
        ".inputs " + " ".join(f"x{i}" for i in range(netlist.n)),
        ".outputs threshold_out",
    ]
    for name in sorted(set(netlist.const1)):
        lines.extend([f".names {sanitize(name)}", "1"])

    logic_inputs = [signal for _, inputs, _ in netlist.logic_ops for signal in inputs]
    need_zero = any(signal == "1'b0" for operation in netlist.fa_ops for signal in operation[:3]) or "1'b0" in logic_inputs or netlist.output == "1'b0"
    need_one = any(signal == "1'b1" for operation in netlist.fa_ops for signal in operation[:3]) or "1'b1" in logic_inputs or netlist.output == "1'b1"
    if need_zero:
        lines.append(".names CONST0")
    if need_one:
        lines.extend([".names CONST1", "1"])

    def mapped(signal: str) -> str:
        return {"1'b0": "CONST0", "1'b1": "CONST1"}.get(signal, sanitize(signal))

    def maj3(a: str, b: str, c: str, output: str, invert: tuple[bool, bool, bool] = (False, False, False)) -> None:
        inputs = [mapped(a), mapped(b), mapped(c)]
        order = sorted(range(3), key=inputs.__getitem__)
        lines.append(".names " + " ".join([inputs[index] for index in order] + [sanitize(output)]))
        for values in ((0,0,0),(0,0,1),(0,1,0),(0,1,1),(1,0,0),(1,0,1),(1,1,0),(1,1,1)):
            original = [0, 0, 0]
            for sorted_index, original_index in enumerate(order):
                original[original_index] = values[sorted_index]
            if sum(original[index] ^ int(invert[index]) for index in range(3)) >= 2:
                lines.append("".join(map(str, values)) + " 1")

    for index, (a, b, carry_in, sum_signal, carry_out) in enumerate(netlist.fa_ops):
        maj3(a, b, carry_in, carry_out)
        helper = f"fa{index}_op1"
        maj3(a, b, carry_in, helper, (True, False, False))
        maj3(helper, a, carry_out, sum_signal, (False, False, True))
    for gate, inputs, output in netlist.logic_ops:
        if gate != "or2":
            raise ValueError(f"unsupported decision gate: {gate}")
        lines.extend([f".names {mapped(inputs[0])} {mapped(inputs[1])} {sanitize(output)}", "1- 1", "-1 1"])
    lines.extend([f".names {mapped(netlist.output)} threshold_out", "1 1", ".end", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def depth(netlist: Netlist) -> int:
    levels: dict[str, int] = {}

    def level(signal: str) -> int:
        return 0 if signal in ("1'b0", "1'b1") else levels.get(signal, 0)

    for a, b, carry_in, sum_signal, carry_out in netlist.fa_ops:
        current = max(level(a), level(b), level(carry_in)) + 1
        levels[sum_signal] = current
        levels[carry_out] = current
    for _, inputs, output in netlist.logic_ops:
        levels[output] = max(level(signal) for signal in inputs) + 1
    return level(netlist.output)


def paper_vector_count(n: int) -> int:
    return 4096 if n == 127 else 2048


def vectors(n: int, threshold: int, count: int) -> list[tuple[int, ...]]:
    if n <= 12:
        return [tuple((word >> bit) & 1 for bit in range(n)) for word in range(1 << n)]
    rng = random.Random(SEED + n * 1009 + threshold)
    words = {0, (1 << n) - 1}
    for weight in sorted({0, 1, threshold - 1, threshold, min(n, threshold + 1), n - 1, n}):
        if 0 <= weight <= n:
            words.add((1 << weight) - 1 if weight else 0)
            positions = rng.sample(range(n), weight)
            words.add(sum(1 << position for position in positions))
    while len(words) < count:
        words.add(rng.getrandbits(n))
    return [tuple((word >> bit) & 1 for bit in range(n)) for word in sorted(words)]


def delta_summary(records: list[dict[str, object]], metric: str) -> dict[str, object]:
    deltas = [float(record[f"direct_{metric}"]) - float(record[f"folded_{metric}"]) for record in records]
    return {
        "count": len(deltas),
        "mean_baseline_minus_folded": statistics.mean(deltas),
        "median_baseline_minus_folded": statistics.median(deltas),
        "minimum": min(deltas),
        "maximum": max(deltas),
        "folded_wins": sum(delta > 0 for delta in deltas),
        "ties": sum(delta == 0 for delta in deltas),
        "folded_losses": sum(delta < 0 for delta in deltas),
    }


def near_power_of_two(threshold: int, width: int) -> bool:
    """Match the manuscript category: within one of either adjacent power."""
    lower = 1 << max(0, width - 1)
    upper = 1 << width
    return min(abs(threshold - lower), abs(upper - threshold)) <= 1


def summarize(records: list[dict[str, object]], abc_enabled: bool) -> dict[str, object]:
    regions = {
        "all": records,
        "low_T_le_n_over_3": [record for record in records if 3 * int(record["T"]) <= int(record["n"])],
        "middle": [
            record
            for record in records
            if 3 * int(record["T"]) > int(record["n"])
            and 3 * int(record["T"]) < 2 * int(record["n"])
        ],
        "high_T_ge_2n_over_3": [record for record in records if 3 * int(record["T"]) >= 2 * int(record["n"])],
        "carry_only_valid": [record for record in records if bool(record["carry_only_valid"])],
        "high_bit_or_required": [record for record in records if not bool(record["carry_only_valid"])],
        "near_power_of_two": [record for record in records if bool(record["near_power_of_two"])],
    }
    metrics = ["fa_count", "depth"]
    if abc_enabled:
        metrics.extend(("abc_aig_nodes", "abc_aig_levels", "lut6_nodes", "lut6_levels"))
    region_summaries = {
        region: {
            "cases": len(items),
            "metrics": {metric: delta_summary(items, metric) for metric in metrics},
        }
        for region, items in regions.items()
        if items
    }
    cec_counts: dict[str, int] = {}
    if abc_enabled:
        for record in records:
            status = str(record["abc_cec_status"])
            cec_counts[status] = cec_counts.get(status, 0) + 1
    return {
        "cases": len(records),
        "deterministic_passes": sum(int(record["mismatches"]) == 0 for record in records),
        "abc_cec": cec_counts,
        "regions": region_summaries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-values", type=parse_n_values, default=parse_n_values("31,63,127"))
    parser.add_argument(
        "--vectors",
        default="paper",
        help="Vectors per case, or 'paper' for 2,048 (n=31/63) and 4,096 (n=127).",
    )
    parser.add_argument("--output-root", type=Path, default=Path("build/reproduction/thresholds"))
    parser.add_argument("--report", type=Path, default=Path("build/reproduction/threshold_sweep.json"))
    parser.add_argument("--abc-bin", default="")
    parser.add_argument("--require-abc", action="store_true")
    args = parser.parse_args()

    if args.vectors == "paper":
        vector_override = None
    else:
        try:
            vector_override = int(args.vectors)
        except ValueError as error:
            raise SystemExit("--vectors must be a positive integer or 'paper'") from error
        if vector_override <= 0:
            raise SystemExit("--vectors must be positive")

    abc = resolve_executable(args.abc_bin)
    if args.require_abc and abc is None:
        raise SystemExit("ABC was requested but could not be found; set --abc-bin or ABC_BIN")
    print(f"[threshold] ABC={'enabled' if abc else 'not found; mapped metrics and CEC skipped'}")

    fg.SCHEDULE_MODE = "dadda"
    output_root = args.output_root if args.output_root.is_absolute() else REPO_ROOT / args.output_root
    records: list[dict[str, object]] = []
    for n in args.n_values:
        for threshold in range(2, n + 1):
            started = time.perf_counter()
            folded = build_folded(n, threshold)
            direct = build_direct(n, threshold)
            case_dir = output_root / f"n{n}" / f"T{threshold}"
            folded_path = case_dir / "folded_bias.blif"
            direct_path = case_dir / "direct_csa_threshold.blif"
            write_blif(folded, folded_path)
            write_blif(direct, direct_path)
            folded_blif = read_blif(folded_path)
            direct_blif = read_blif(direct_path)
            vector_count = vector_override if vector_override is not None else paper_vector_count(n)
            applied = vectors(n, threshold, vector_count)
            folded_values = simulate_many(folded_blif, applied)
            direct_values = simulate_many(direct_blif, applied)
            for index, (bits, folded_value, direct_value) in enumerate(
                zip(applied, folded_values, direct_values)
            ):
                expected = int(sum(bits) >= threshold)
                observed = (folded_value, direct_value)
                if observed != (expected, expected):
                    raise RuntimeError(
                        f"threshold mismatch n={n} T={threshold} vector={index} "
                        f"expected={expected} folded={observed[0]} direct={observed[1]}"
                    )
            record: dict[str, object] = {
                    "n": n,
                    "T": threshold,
                    "w": folded.diagnostics["w"],
                    "K": folded.diagnostics["K"],
                    "popcount_K": folded.diagnostics["popcount_K"],
                    "near_power_of_two": near_power_of_two(
                        threshold, int(folded.diagnostics["w"])
                    ),
                    "carry_only_valid": folded.diagnostics["carry_only_valid"],
                    "decision_high_bits": folded.diagnostics["decision_high_bits"],
                    "folded_fa_count": len(folded.fa_ops),
                    "direct_fa_count": len(direct.fa_ops),
                    "folded_depth": depth(folded),
                    "direct_depth": depth(direct),
                    "vectors": len(applied),
                    "mismatches": 0,
                    "elapsed_s": round(time.perf_counter() - started, 6),
                }
            if abc:
                folded_abc = run_abc(abc, folded_path)
                direct_abc = run_abc(abc, direct_path)
                cec = run_cec(abc, direct_path, folded_path)
                if cec["status"] == "not_equivalent":
                    raise RuntimeError(f"ABC disproved equivalence for n={n}, T={threshold}")
                if cec["status"] == "tool_error":
                    raise RuntimeError(f"ABC CEC failed for n={n}, T={threshold}")
                for prefix, metrics in (("folded", folded_abc), ("direct", direct_abc)):
                    for checkpoint in ("strong_aig", "lut6"):
                        values = metrics[checkpoint]
                        assert isinstance(values, dict)
                        metric_prefix = "abc_aig" if checkpoint == "strong_aig" else "lut6"
                        record[f"{prefix}_{metric_prefix}_nodes"] = values["nodes"]
                        record[f"{prefix}_{metric_prefix}_levels"] = values["levels"]
                record["abc_cec_status"] = cec["status"]
                record["abc_cec_elapsed_s"] = cec["elapsed_s"]
            records.append(record)
        print(f"[threshold] PASS n={n} cases={n - 1}")

    report = args.report if args.report.is_absolute() else REPO_ROOT / args.report
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "schema": 2,
                "seed": SEED,
                "vector_policy": (
                    "paper:2048_for_n31_n63;4096_for_n127"
                    if vector_override is None
                    else f"fixed:{vector_override}"
                ),
                "abc_enabled": bool(abc),
                "summary": summarize(records, bool(abc)),
                "cases": records,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"[threshold] report={report.relative_to(REPO_ROOT) if report.is_relative_to(REPO_ROOT) else report.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
