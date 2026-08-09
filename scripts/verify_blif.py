#!/usr/bin/env python3
"""Independently check generated BLIFs against the majority specification."""

from __future__ import annotations

import argparse
import functools
import itertools
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Node:
    inputs: tuple[str, ...]
    output: str
    rows: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class Blif:
    inputs: tuple[str, ...]
    output: str
    nodes: tuple[Node, ...]


def parse_n_values(text: str) -> list[int]:
    values = [int(item) for item in text.replace(",", " ").split()]
    if not values or any(value < 3 or value % 2 == 0 for value in values):
        raise argparse.ArgumentTypeError("n values must be odd integers >= 3")
    return list(dict.fromkeys(values))


def logical_lines(path: Path) -> list[str]:
    lines: list[str] = []
    pending = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.endswith("\\"):
            pending += line[:-1].strip() + " "
            continue
        lines.append((pending + line).strip())
        pending = ""
    if pending:
        lines.append(pending.strip())
    return lines


def read_blif(path: Path) -> Blif:
    lines = logical_lines(path)
    inputs: list[str] = []
    outputs: list[str] = []
    nodes: list[Node] = []
    index = 0
    while index < len(lines):
        fields = lines[index].split()
        if fields[0] == ".inputs":
            inputs.extend(fields[1:])
        elif fields[0] == ".outputs":
            outputs.extend(fields[1:])
        elif fields[0] == ".names":
            fanins = tuple(fields[1:-1])
            output = fields[-1]
            rows: list[tuple[str, int]] = []
            index += 1
            while index < len(lines) and not lines[index].startswith("."):
                row = lines[index].split()
                if fanins:
                    pattern = row[0]
                    value = int(row[1]) if len(row) == 2 else 1
                    if len(pattern) != len(fanins):
                        raise ValueError(f"invalid cube in {path}: {lines[index]}")
                else:
                    pattern = ""
                    value = int(row[0])
                rows.append((pattern, value))
                index += 1
            nodes.append(Node(fanins, output, tuple(rows)))
            continue
        index += 1
    if not inputs or len(outputs) != 1:
        raise ValueError(f"expected one-output combinational BLIF: {path}")
    return Blif(tuple(inputs), outputs[0], tuple(nodes))


def node_value(node: Node, values: dict[str, int]) -> int:
    phases = {value for _, value in node.rows}
    if len(phases) > 1:
        raise ValueError(f"mixed ON/OFF-set table at {node.output}")
    default = 1 - next(iter(phases)) if phases else 0
    result = default
    for pattern, row_value in node.rows:
        if all(symbol == "-" or int(symbol) == values[name] for symbol, name in zip(pattern, node.inputs)):
            result = row_value
    return result


@functools.lru_cache(maxsize=512)
def topological_nodes(network: Blif) -> tuple[Node, ...]:
    available = set(network.inputs)
    pending = list(network.nodes)
    ordered: list[Node] = []
    while pending:
        next_pending: list[Node] = []
        for node in pending:
            if all(name in available for name in node.inputs):
                ordered.append(node)
                available.add(node.output)
            else:
                next_pending.append(node)
        if len(next_pending) == len(pending):
            missing = sorted(
                {name for node in next_pending for name in node.inputs if name not in available}
            )
            raise ValueError("unresolved BLIF signal(s): " + ", ".join(missing[:8]))
        pending = next_pending
    return tuple(ordered)


def simulate(network: Blif, bits: tuple[int, ...]) -> int:
    values = dict(zip(network.inputs, bits))
    for node in topological_nodes(network):
        values[node.output] = node_value(node, values)
    return values[network.output]


def simulate_many(network: Blif, vectors: list[tuple[int, ...]]) -> list[int]:
    """Evaluate many vectors exactly using one Python integer per BLIF signal."""
    if not vectors:
        return []
    if any(len(bits) != len(network.inputs) for bits in vectors):
        raise ValueError("input-vector width does not match the BLIF primary-input count")

    width_mask = (1 << len(vectors)) - 1
    values: dict[str, int] = {}
    for input_index, name in enumerate(network.inputs):
        packed = 0
        for vector_index, bits in enumerate(vectors):
            packed |= int(bits[input_index]) << vector_index
        values[name] = packed

    for node in topological_nodes(network):
        phases = {value for _, value in node.rows}
        if len(phases) > 1:
            raise ValueError(f"mixed ON/OFF-set table at {node.output}")
        default = 1 - next(iter(phases)) if phases else 0
        result = width_mask if default else 0
        for pattern, row_value in node.rows:
            matches = width_mask
            for symbol, name in zip(pattern, node.inputs):
                if symbol == "1":
                    matches &= values[name]
                elif symbol == "0":
                    matches &= width_mask ^ values[name]
                elif symbol != "-":
                    raise ValueError(f"invalid BLIF cube symbol {symbol!r}")
            if row_value:
                result |= matches
            else:
                result &= width_mask ^ matches
        values[node.output] = result

    packed_output = values[network.output]
    return [(packed_output >> index) & 1 for index in range(len(vectors))]


def validation_vectors(n: int, exhaustive_max_n: int, random_vectors: int) -> list[tuple[int, ...]]:
    if n <= exhaustive_max_n:
        return list(itertools.product((0, 1), repeat=n))

    rng = random.Random(0x7CAD + n)
    threshold = (n + 1) // 2
    vectors: list[tuple[int, ...]] = []
    for weight in sorted({0, 1, threshold - 1, threshold, threshold + 1, n - 1, n}):
        for _ in range(12):
            bits = [1] * weight + [0] * (n - weight)
            rng.shuffle(bits)
            vectors.append(tuple(bits))
    for _ in range(random_vectors):
        vectors.append(tuple(rng.getrandbits(1) for _ in range(n)))
    return vectors


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-values", type=parse_n_values, default=parse_n_values("5,7,9,11,13"))
    parser.add_argument("--input-root", type=Path, default=Path("build/reproduction/netlists"))
    parser.add_argument("--exhaustive-max-n", type=int, default=13)
    parser.add_argument("--random-vectors", type=int, default=1024)
    parser.add_argument("--report", type=Path, default=Path("build/reproduction/verification.json"))
    args = parser.parse_args()

    input_root = args.input_root if args.input_root.is_absolute() else REPO_ROOT / args.input_root
    report: list[dict[str, object]] = []
    for n in args.n_values:
        case_dir = input_root / f"n{n}"
        folded_path = case_dir / "folded_bias" / f"maj_fb_{n}.blif"
        baseline_path = case_dir / "baseline" / f"maj_baseline_strict_{n}.blif"
        folded = read_blif(folded_path)
        baseline = read_blif(baseline_path)
        if len(folded.inputs) != n or len(baseline.inputs) != n:
            raise ValueError(f"primary-input count mismatch for n={n}")

        vectors = validation_vectors(n, args.exhaustive_max_n, args.random_vectors)
        threshold = (n + 1) // 2
        folded_values = simulate_many(folded, vectors)
        baseline_values = simulate_many(baseline, vectors)
        for index, (bits, folded_value, baseline_value) in enumerate(
            zip(vectors, folded_values, baseline_values)
        ):
            expected = int(sum(bits) >= threshold)
            if (folded_value, baseline_value) != (expected, expected):
                print(
                    f"FAIL n={n} vector={index} weight={sum(bits)} "
                    f"expected={expected} folded={folded_value} baseline={baseline_value}",
                    file=sys.stderr,
                )
                return 1
        mode = "exhaustive" if n <= args.exhaustive_max_n else "boundary_plus_seeded"
        print(f"[verify] PASS n={n} vectors={len(vectors)} mode={mode}")
        report.append(
            {
                "n": n,
                "mode": mode,
                "vectors": len(vectors),
                "mismatches": 0,
                "folded_blif": relative(folded_path),
                "baseline_blif": relative(baseline_path),
            }
        )

    report_path = args.report if args.report.is_absolute() else REPO_ROOT / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps({"schema": 1, "checks": report}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[verify] report={relative(report_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
