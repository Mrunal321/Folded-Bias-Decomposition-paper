#!/usr/bin/env python3
"""Fail if the public tree contains private, bulky, or generated material."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 5 * 1024 * 1024
FORBIDDEN_PARTS = {
    "build",
    "out",
    "results",
    "proposed_insertions",
    "original paper",
    ".vscode",
    ".idea",
    "__pycache__",
}
FORBIDDEN_WORDS = ("manuscript", "rebuttal", "supplementary")
FORBIDDEN_SUFFIXES = {
    ".aux",
    ".bbl",
    ".bib",
    ".blg",
    ".cnf",
    ".csv",
    ".dcp",
    ".doc",
    ".docx",
    ".fdb_latexmk",
    ".fls",
    ".jpg",
    ".jpeg",
    ".log",
    ".pdf",
    ".png",
    ".qca",
    ".rpt",
    ".saif",
    ".synctex.gz",
    ".tex",
    ".toc",
    ".vcd",
    ".vvp",
    ".wdb",
    ".zip",
}
ARCHIVE_GENERATED_DIRS = {
    ".Xil",
    ".git",
    ".idea",
    ".venv",
    ".vscode",
    "CMakeFiles",
    "__pycache__",
    "build",
    "out",
    "results",
}
ARCHIVE_GENERATED_FILES = {"CMakeCache.txt", "abc.history"}


def archive_generated(path: Path) -> bool:
    """Identify ignored by-products that may be created after ZIP extraction."""

    relative = path.relative_to(REPO_ROOT)
    directories = relative.parts[:-1]
    if any(
        part in ARCHIVE_GENERATED_DIRS or part.startswith("build_")
        for part in directories
    ):
        return True
    if relative.parts[:2] == ("artifacts", "generated"):
        return True
    return relative.name in ARCHIVE_GENERATED_FILES or relative.suffix in {".pyc", ".pyo"}


def archived_raw_data(path: Path) -> bool:
    """Allow only the curated, checksummed public numerical archive."""

    relative = path.relative_to(REPO_ROOT)
    return (
        relative.parts[:2] == ("archive", "paper-results-v5.61")
        and len(relative.parts) == 4
        and relative.parts[2] == "raw-data"
        and relative.suffix == ".csv"
    )


def release_files() -> list[Path]:
    # A Git checkout needs Git-aware enumeration so ignored build products do not
    # make an otherwise clean working tree fail the release gate.  GitHub source
    # archives do not contain `.git`, so scan every archived file in that case.
    # Do not fall back after a Git error: a damaged checkout must fail loudly
    # rather than silently weakening the audit.
    if not (REPO_ROOT / ".git").exists():
        return sorted(
            path
            for path in REPO_ROOT.rglob("*")
            if path.is_file() and not archive_generated(path)
        )
    process = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [REPO_ROOT / line for line in process.stdout.splitlines() if line and (REPO_ROOT / line).is_file()]


def sensitive_text(path: Path) -> list[str]:
    data = path.read_bytes()
    if b"\0" in data:
        return []
    text = data.decode("utf-8", errors="replace")
    findings: list[str] = []
    markers = {
        "Unix home path": "/" + "home" + "/",
        "macOS home path": "/" + "Users" + "/",
        "Codex state path": "." + "codex" + "/",
    }
    for label, marker in markers.items():
        if marker in text:
            findings.append(label)
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
        findings.append("email address")
    if re.search(r"(?i)(?<![A-Za-z0-9_])[A-Z]:[\\/]", text):
        findings.append("Windows absolute path")
    if re.search(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----", text):
        findings.append("private key")
    if re.search(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})", text):
        findings.append("GitHub token-like string")
    return findings


def verify_example_checksums() -> list[str]:
    manifest = REPO_ROOT / "artifacts" / "examples" / "SHA256SUMS"
    if not manifest.is_file():
        return ["missing example checksum manifest"]
    problems: list[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split(maxsplit=1)
        path = manifest.parent / relative.strip()
        if not path.is_file():
            problems.append(f"missing example: {path.relative_to(REPO_ROOT)}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            problems.append(f"example checksum mismatch: {path.relative_to(REPO_ROOT)}")
    return problems


def main() -> int:
    problems: list[str] = verify_example_checksums()
    files = release_files()
    for path in files:
        relative = path.relative_to(REPO_ROOT)
        lowered_parts = {part.lower() for part in relative.parts}
        lowered_name = relative.as_posix().lower()
        if lowered_parts & FORBIDDEN_PARTS:
            problems.append(f"forbidden directory: {relative}")
        if any(word in lowered_name for word in FORBIDDEN_WORDS):
            problems.append(f"paper-writing material: {relative}")
        if (
            any(lowered_name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES)
            and not archived_raw_data(path)
        ):
            problems.append(f"forbidden generated/document format: {relative}")
        if path.stat().st_size > MAX_FILE_BYTES:
            problems.append(f"file exceeds 5 MiB: {relative}")
        for finding in sensitive_text(path):
            problems.append(f"{finding}: {relative}")

    if problems:
        print("Release audit failed:", file=sys.stderr)
        for problem in sorted(set(problems)):
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print(f"[audit] PASS files={len(files)} max_file_bytes={MAX_FILE_BYTES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
