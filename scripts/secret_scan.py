"""Fail if likely secrets appear in tracked files. Run before any public push."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    re.compile(r"postgres(ql)?://[^:]+:[^@]+@"),
    re.compile(r"PASSWORD\s*=\s*['\"][^'\"]{8,}['\"]", re.I),
]

SKIP_PARTS = {".env.example", "secret_scan.py", "catalog_data.py"}


def tracked_files() -> list[str]:
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        EXCLUDE = {".venv", "venv", "env", "node_modules", "__pycache__", ".git", ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build", "frontend/dist", "frontend/coverage"}
        return [
            str(p) for p in ROOT.rglob("*")
            if p.is_file()
            and not any(part in p.parts for part in EXCLUDE)
            and "node_modules" not in str(p)
            and ".git" not in str(p)
        ]
    return result.stdout.splitlines()


def main() -> int:
    findings = 0
    for rel in tracked_files():
        path = ROOT / rel
        if any(part in rel.replace("\\", "/") for part in SKIP_PARTS):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".webp", ".ico", ".pdf"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in PATTERNS:
            if pattern.search(text):
                print(f"Possible secret in {rel}")
                findings += 1
                break
    if findings:
        print("Secret scan failed. Rotate any real credential immediately. Do not push.")
        return 1
    print("Secret scan: no high-confidence matches in scanned files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
