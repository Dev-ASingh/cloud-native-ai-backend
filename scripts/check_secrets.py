"""Fail CI when high-signal credential material appears in tracked files."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

PATTERNS = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH|DSA) PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
)
EXCLUDED_SUFFIXES = (".pyc", ".db", ".sqlite", ".sqlite3")


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [Path(item) for item in result.stdout.decode().split("\0") if item]


def main() -> int:
    findings: list[str] = []
    for path in tracked_files():
        if path.name == "check_secrets.py" or path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in PATTERNS:
            if pattern.search(content):
                findings.append(f"{path}: matched {pattern.pattern}")

    if findings:
        print("Potential credential material found:")
        print("\n".join(findings))
        return 1
    print("Tracked-file credential scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
