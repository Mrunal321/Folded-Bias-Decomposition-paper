#!/usr/bin/env python3
"""Generate a deterministic suite of baseline and folded-bias netlists."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "scripts" / "final_generator.py"


def parse_n_values(text: str) -> list[int]:
    values: list[int] = []
    for item in text.replace(",", " ").split():
        value = int(item)
        if value < 3 or value % 2 == 0:
            raise argparse.ArgumentTypeError(
                f"all n values must be odd integers >= 3; received {value}"
            )
        if value not in values:
            values.append(value)
    if not values:
        raise argparse.ArgumentTypeError("at least one n value is required")
    return values


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.name


def command_path(path: Path) -> str:
    """Prefer a repository-relative CLI path without changing external targets."""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-values", type=parse_n_values, default=parse_n_values("5,7,9,11,13"))
    parser.add_argument("--output-root", type=Path, default=Path("build/reproduction/netlists"))
    parser.add_argument("--schedule", choices=("serial", "wallace", "dadda"), default="dadda")
    parser.add_argument(
        "--experiment-mode", choices=("default", "k_advantage"), default="default"
    )
    parser.add_argument("--fa-encoding", choices=("majority", "xor"), default="majority")
    parser.add_argument("--mockturtle-scoring", action="store_true")
    parser.add_argument("--mockturtle-bin", default="tools/mockturtle_mig_opt/build/mockturtle_mig_opt")
    parser.add_argument("--self-check-max-n", type=int, default=13)
    args = parser.parse_args()

    output_root = args.output_root
    if not output_root.is_absolute():
        output_root = REPO_ROOT / output_root
    output_root.mkdir(parents=True, exist_ok=True)

    generated: list[dict[str, object]] = []
    for n in args.n_values:
        case_dir = output_root / f"n{n}"
        command = [
            sys.executable,
            str(GENERATOR),
            "--n",
            str(n),
            "--output-dir",
            command_path(case_dir),
            "--schedule",
            args.schedule,
            "--experiment-mode",
            args.experiment_mode,
            "--fa-encoding",
            args.fa_encoding,
            "--self-check-max-n",
            str(args.self_check_max_n),
        ]
        if args.mockturtle_scoring:
            command.extend(["--mockturtle-scoring", "--mockturtle-bin", args.mockturtle_bin])

        print(f"[generate] n={n}", flush=True)
        proc = subprocess.run(command, cwd=REPO_ROOT, text=True, check=False)
        if proc.returncode:
            return proc.returncode

        expected = [
            case_dir / f"maj{n}_generated_canon.v",
            case_dir / "folded_bias" / f"maj_fb_{n}.blif",
            case_dir / "baseline" / f"maj_baseline_strict_{n}.blif",
        ]
        missing = [path for path in expected if not path.is_file()]
        if missing:
            print(
                "missing generated file(s): "
                + ", ".join(relative(path) for path in missing),
                file=sys.stderr,
            )
            return 2
        generated.append(
            {
                "n": n,
                "files": [
                    {
                        "path": relative(path),
                        "bytes": path.stat().st_size,
                        "sha256": sha256(path),
                    }
                    for path in expected
                ],
            }
        )

    manifest = {
        "schema": 1,
        "n_values": args.n_values,
        "schedule": args.schedule,
        "experiment_mode": args.experiment_mode,
        "fa_encoding": args.fa_encoding,
        "mockturtle_scoring": args.mockturtle_scoring,
        "generated": generated,
    }
    manifest_path = output_root.parent / "generation_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[generate] manifest={relative(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
