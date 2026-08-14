#!/usr/bin/env python3
"""Validate subject-guide and conclusion-card section contracts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SUBJECT_SECTIONS = [
    "## 适用问题",
    "## 优先检查",
    "## 不能直接假设",
    "## 证据与验证",
    "## 常见错误",
]
CONCLUSION_SECTIONS = [
    "## 更准确的表述",
    "## 为什么可能成立",
    "## 适用范围",
    "## 成立条件",
    "## 失效或弱化",
    "## 证据",
    "## 常见误用",
]


def check(directory: Path, sections: list[str]) -> list[str]:
    errors: list[str] = []
    for path in sorted(directory.glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        missing = [section for section in sections if section not in text]
        if missing:
            errors.append(f"{path.relative_to(ROOT)} missing: {', '.join(missing)}")
    return errors


def main() -> int:
    errors = [
        *check(ROOT / "references/subjects", SUBJECT_SECTIONS),
        *check(ROOT / "references/conclusions", CONCLUSION_SECTIONS),
    ]
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: subject guides and conclusion cards satisfy section contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
