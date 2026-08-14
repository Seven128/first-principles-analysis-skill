#!/usr/bin/env python3
"""Warn about risky absolute or inflated wording in runtime skill documents."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCAN_PATHS = [
    ROOT / "SKILL.md",
    ROOT / "README.md",
    ROOT / "references/core",
    ROOT / "references/writing",
    ROOT / "references/subjects",
    ROOT / "references/conclusions",
]

RISKY = {
    "绝对": "确认是否真的具有无例外范围",
    "完美": "改成可验证的具体结果",
    "降维": "改成实际减少了什么成本或复杂度",
    "跃迁": "改成具体状态变化",
    "物理": "仅在确实讨论物理层或确定性执行边界时使用",
    "所有人": "检查全称命题和反例",
    "任何情况": "说明适用范围",
    "必然": "检查是否只是高概率或条件性结果",
    "唯一": "检查是否存在替代实现或解释",
    "本质上都是": "检查是否过度归纳",
    "彻底解决": "说明残余风险与边界",
}

EXEMPT_HEADINGS = (
    "禁止事项",
    "不能直接假设",
    "常见误用",
    "常见错误",
    "控制绝对化语言",
    "高风险",
)

NEGATION_MARKERS = ("不", "避免", "谨慎", "禁止", "不得", "不能", "并非", "非", "警惕", "误用")


def iter_files() -> list[Path]:
    result: list[Path] = []
    for path in SCAN_PATHS:
        if path.is_file():
            result.append(path)
        elif path.is_dir():
            result.extend(sorted(path.glob("*.md")))
    return result


def lint_file(path: Path) -> list[str]:
    warnings: list[str] = []
    in_fence = False
    exempt_section = False

    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("## ") or stripped.startswith("# "):
            exempt_section = any(name in stripped for name in EXEMPT_HEADINGS)
        if exempt_section or any(marker in stripped for marker in NEGATION_MARKERS):
            continue

        for term, advice in RISKY.items():
            if term == "物理" and any(
                phrase in line
                for phrase in (
                    "物理层",
                    "物理规律",
                    "物理环境",
                    "物理约束",
                    "物理和计算限制",
                    "生物、物理",
                    "生态、物理",
                )
            ):
                continue
            if term in line:
                warnings.append(
                    f"{path.relative_to(ROOT)}:{line_no}: found {term!r}; {advice}: {stripped}"
                )
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="Return non-zero when warnings exist")
    args = parser.parse_args()

    warnings: list[str] = []
    for path in iter_files():
        warnings.extend(lint_file(path))

    if warnings:
        print("Language lint warnings:")
        for warning in warnings:
            print(f"- {warning}")
        return 1 if args.strict else 0

    print(f"OK: no risky unqualified wording in {len(iter_files())} runtime documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
