#!/usr/bin/env python3
"""Reproduce the scoped EPFL ``voter`` comparison without tracking results.

The benchmark is downloaded from an immutable EPFL benchmark revision (or
accepted through a hash-checked local override).  The paper baseline and the
folded-bias construction are regenerated with ``final_generator.py``.  All
three networks are then checked against the 1001-input majority specification
on the deterministic vector set used for the revised voter experiment.

ABC metrics and pairwise CEC are optional.  When enabled, CEC matches primary
inputs by order and uses ``-T 0`` so ABC applies no CEC runtime limit.  An
undecided CEC result is reported as undecided; deterministic testing is never
presented as a formal proof.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from run_strong_flow import ABC_ROUND, abc_path, abc_version, resolve_executable, run_abc
from verify_blif import read_blif, simulate_many


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "scripts/final_generator.py"

N = 1001
THRESHOLD = 501
SEED = 0x7CAD
BOUNDARY_WEIGHTS = (0, 1, 2, 499, 500, 501, 502, 999, 1000, 1001)
PERMUTATIONS_PER_WEIGHT = 12
RANDOM_VECTOR_COUNT = 1024
EXPECTED_VECTOR_COUNT = len(BOUNDARY_WEIGHTS) * PERMUTATIONS_PER_WEIGHT + RANDOM_VECTOR_COUNT
VALIDATION_VECTOR_SHA256 = "bed2c8b9d1648ea1632350155e8894801aa8210d7d4f2ae3c97a2f10919cb35e"

EPFL_REPOSITORY = "https://github.com/lsils/benchmarks"
EPFL_COMMIT = "0060e156826e733d69bf5b3322d1bdd0d03a1f9a"
EPFL_PATH = "random_control/voter.blif"
EPFL_SHA256 = "542214e933efbcd563aebf9a3a7487dfb596c823af2e62f72b105b2dae1ed597"
EPFL_URL = f"https://raw.githubusercontent.com/lsils/benchmarks/{EPFL_COMMIT}/{EPFL_PATH}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    """Return a report-safe path without exposing a user or machine prefix."""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.name


def command_path(path: Path) -> str:
    """Prefer a repository-relative CLI path while preserving external output roots."""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def prepare_epfl_source(local_source: Path | None, destination: Path, timeout: int) -> str:
    if local_source is None:
        request = urllib.request.Request(
            EPFL_URL,
            headers={"User-Agent": "folded-bias-reproducibility"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read()
        source_mode = "pinned_download"
    else:
        if not local_source.is_file():
            raise FileNotFoundError(f"EPFL source override is not a file: {local_source}")
        data = local_source.read_bytes()
        source_mode = "hash_checked_local_override"

    observed = sha256_bytes(data)
    if observed != EPFL_SHA256:
        raise RuntimeError(
            "EPFL voter SHA-256 mismatch: "
            f"expected {EPFL_SHA256}, observed {observed}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return source_mode


def generate_constructions(output_root: Path) -> dict[str, Path]:
    command = [
        sys.executable,
        str(GENERATOR),
        "--n",
        str(N),
        "--output-dir",
        command_path(output_root),
        "--schedule",
        "dadda",
        "--experiment-mode",
        "k_advantage",
        "--fa-encoding",
        "majority",
        "--skip-self-check",
    ]
    process = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode:
        details = (process.stderr or process.stdout).strip()
        raise RuntimeError(f"majority generator failed: {details}")

    paths = {
        "baseline_strict": output_root / "baseline" / f"maj_baseline_strict_{N}.blif",
        "folded_bias": output_root / "folded_bias" / f"maj_fb_{N}.blif",
    }
    missing = [relative(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise RuntimeError("generator did not create: " + ", ".join(missing))
    return paths


def deterministic_vectors() -> list[tuple[int, ...]]:
    """Recreate the documented 1,144-vector protocol byte-for-byte in order."""
    rng = random.Random(SEED)
    vectors: list[tuple[int, ...]] = []
    for weight in BOUNDARY_WEIGHTS:
        for _ in range(PERMUTATIONS_PER_WEIGHT):
            bits = [1] * weight + [0] * (N - weight)
            rng.shuffle(bits)
            vectors.append(tuple(bits))
    for _ in range(RANDOM_VECTOR_COUNT):
        vectors.append(tuple(int(bit) for bit in (rng.choice("01") for _ in range(N))))
    if len(vectors) != EXPECTED_VECTOR_COUNT:
        raise AssertionError("internal deterministic-vector count error")
    return vectors


def vector_stream_sha256(vectors: list[tuple[int, ...]]) -> str:
    digest = hashlib.sha256()
    for vector in vectors:
        digest.update(bytes(48 + bit for bit in vector))
        digest.update(b"\n")
    return digest.hexdigest()


def specification_checks(
    paths: dict[str, Path], vectors: list[tuple[int, ...]]
) -> dict[str, object]:
    networks = {label: read_blif(path) for label, path in paths.items()}
    for label, network in networks.items():
        if len(network.inputs) != N:
            raise RuntimeError(
                f"{label} has {len(network.inputs)} primary inputs; expected {N}"
            )

    expected = [int(sum(bits) >= THRESHOLD) for bits in vectors]
    observed = {
        label: simulate_many(network, vectors) for label, network in networks.items()
    }
    checks: dict[str, object] = {}
    for label, values in observed.items():
        mismatches = sum(value != reference for value, reference in zip(values, expected))
        checks[label] = {
            "tested_vectors": len(vectors),
            "passed_vectors": len(vectors) - mismatches,
            "mismatches": mismatches,
            "status": "pass" if mismatches == 0 else "fail",
        }

    pairs: dict[str, object] = {}
    pair_labels = (
        ("epfl_original", "baseline_strict"),
        ("epfl_original", "folded_bias"),
        ("baseline_strict", "folded_bias"),
    )
    for left, right in pair_labels:
        mismatches = sum(a != b for a, b in zip(observed[left], observed[right]))
        pairs[f"{left}_vs_{right}"] = {
            "tested_vectors": len(vectors),
            "passed_vectors": len(vectors) - mismatches,
            "mismatches": mismatches,
            "status": "pass" if mismatches == 0 else "fail",
        }

    any_mismatch = any(int(item["mismatches"]) for item in checks.values())
    if any_mismatch:
        raise RuntimeError("at least one voter implementation failed the majority specification")
    return {"designs_vs_specification": checks, "pairwise": pairs}


def run_pairwise_cec(abc: Path, left: Path, right: Path) -> dict[str, object]:
    # -n selects PI/PO matching by order, because EPFL and generated netlists
    # use different signal names. -T 0 removes ABC's default 20-second limit.
    script = f"cec -n -T 0 {abc_path(left)} {abc_path(right)}"
    started = time.perf_counter()
    process = subprocess.run(
        [str(abc), "-q", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - started
    output = process.stdout + "\n" + process.stderr
    # Preserve a recognized formal verdict; otherwise distinguish a checker
    # failure from a successful run that reached no conclusion.
    if "Networks are equivalent" in output:
        status = "equivalent"
    elif "Networks are NOT EQUIVALENT" in output:
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


def abc_checks(
    abc: Path,
    paths: dict[str, Path],
    *,
    skip_metrics: bool,
    skip_formal: bool,
) -> dict[str, object]:
    result: dict[str, object] = {
        "enabled": True,
        "version": abc_version(abc),
        "metric_flow": {
            "representation": "AIG followed by LUT6 mapping",
            "abc_resyn2_style_rounds": 3,
            "expanded_round": ABC_ROUND,
        },
        "cec": {
            "command_options": "-n -T 0",
            "input_matching": "primary-input order",
            "runtime_limit_seconds": None,
            "runtime_limit_disabled": True,
            "interpretation": (
                "equivalent is a formal proof; not_equivalent is a disproof; "
                "undecided is not a proof; tool_error means the checker failed"
            ),
        },
    }
    if not skip_metrics:
        result["metrics"] = {label: run_abc(abc, path) for label, path in paths.items()}

    if not skip_formal:
        pairs: dict[str, object] = {}
        for left, right in (
            ("epfl_original", "baseline_strict"),
            ("epfl_original", "folded_bias"),
            ("baseline_strict", "folded_bias"),
        ):
            label = f"{left}_vs_{right}"
            cec = run_pairwise_cec(abc, paths[left], paths[right])
            pairs[label] = cec
            print(f"[epfl-voter] ABC-CEC {label}={cec['status']}")
            if cec["status"] == "not_equivalent":
                raise RuntimeError(f"ABC disproved equivalence for {label}")
            if cec["status"] == "tool_error":
                raise RuntimeError(f"ABC CEC failed for {label}")
        result["cec"]["pairs"] = pairs
        result["cec"]["all_pairs_formally_proved"] = all(
            item["status"] == "equivalent" for item in pairs.values()
        )
    else:
        result["cec"]["status"] = "not_run"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--epfl-source",
        type=Path,
        help="Optional local voter.blif; it must match the pinned SHA-256.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("build/reproduction/epfl_voter"),
        help="Generated netlists and JSON report (default: ignored build directory).",
    )
    parser.add_argument(
        "--abc-bin",
        default=os.environ.get("ABC_BIN", ""),
        help="ABC executable; setting this enables optional metrics and CEC.",
    )
    parser.add_argument("--skip-metrics", action="store_true")
    parser.add_argument("--skip-formal", action="store_true")
    parser.add_argument("--download-timeout", type=int, default=60)
    args = parser.parse_args()

    if args.download_timeout <= 0:
        raise SystemExit("--download-timeout must be positive")
    output_root = (
        args.output_root
        if args.output_root.is_absolute()
        else REPO_ROOT / args.output_root
    )
    output_root.mkdir(parents=True, exist_ok=True)

    epfl_path = output_root / "inputs" / "epfl_voter.blif"
    source_mode = prepare_epfl_source(args.epfl_source, epfl_path, args.download_timeout)
    generated = generate_constructions(output_root / "generated")
    paths = {"epfl_original": epfl_path, **generated}

    vectors = deterministic_vectors()
    observed_vector_hash = vector_stream_sha256(vectors)
    if observed_vector_hash != VALIDATION_VECTOR_SHA256:
        raise AssertionError("internal deterministic-vector stream changed")
    checks = specification_checks(paths, vectors)
    print(
        f"[epfl-voter] PASS deterministic specification tests: "
        f"{len(vectors)}/{len(vectors)} vectors for each of {len(paths)} designs"
    )

    abc = None
    if args.abc_bin:
        abc = resolve_executable(args.abc_bin)
        if abc is None:
            raise SystemExit("ABC was requested but could not be found; set --abc-bin or ABC_BIN")

    report: dict[str, object] = {
        "schema": 1,
        "scope": (
            "EPFL voter only; this is not an evaluation of unrelated EPFL benchmarks"
        ),
        "benchmark": {
            "name": "voter",
            "function": "1001-input majority",
            "repository": EPFL_REPOSITORY,
            "commit": EPFL_COMMIT,
            "path": EPFL_PATH,
            "sha256": EPFL_SHA256,
            "source_mode": source_mode,
        },
        "construction": {
            "n": N,
            "threshold": THRESHOLD,
            "generator": "scripts/final_generator.py",
            "generator_sha256": sha256_file(GENERATOR),
            "schedule": "dadda",
            "experiment_mode": "k_advantage",
            "fa_encoding": "majority",
            "generated_blifs": {
                label: relative(path) for label, path in generated.items()
            },
        },
        "deterministic_specification_tests": {
            "status": "pass",
            "seed": "0x7CAD",
            "total_vectors": len(vectors),
            "vector_stream_sha256": observed_vector_hash,
            "boundary_weight_permutations": {
                "weights": list(BOUNDARY_WEIGHTS),
                "vectors_per_weight": PERMUTATIONS_PER_WEIGHT,
                "vectors": len(BOUNDARY_WEIGHTS) * PERMUTATIONS_PER_WEIGHT,
            },
            "seeded_uniform_random_vectors": RANDOM_VECTOR_COUNT,
            **checks,
            "pairwise_aggregate": {
                "miter_evaluations": 3 * len(vectors),
                "passed_miter_evaluations": 3 * len(vectors),
                "mismatches": 0,
                "observed_pass_rate_percent": 100.0,
            },
            "meaning": (
                "pass means zero observed mismatches against majority on all listed "
                "vectors; it is quantitative testing, not exhaustive or formal proof"
            ),
        },
        "abc": {"enabled": False},
    }
    if abc is not None:
        report["abc"] = abc_checks(
            abc,
            paths,
            skip_metrics=args.skip_metrics,
            skip_formal=args.skip_formal,
        )

    report_path = output_root / "voter.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[epfl-voter] report={relative(report_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
