#!/usr/bin/env python3
"""Validate purpose/current-state/problem/solution runtime rules and regressions."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RULE_PATH = ROOT / "references/core/01a-目的、现状、问题与方案.md"
CASES_PATH = ROOT / "evals/purpose-structure-regression-cases.json"
SKILL_PATH = ROOT / "SKILL.md"

EXPECTED_DIMENSIONS = {
    "problem_definition",
    "route_choice",
    "subject_reasoning",
    "causal_chain",
    "alternative_explanations",
    "evidence_discipline",
    "neutrality",
    "flexibility",
    "actionability_or_explanatory_value",
    "language",
}

REQUIRED_CASES = {
    "designed-system-purpose-chain",
    "goal-solving-purpose-chain",
    "historical-intent-boundary",
    "solution-leakage-in-purpose",
    "definition-skips-purpose-template",
    "emotion-skips-forced-purpose",
    "natural-result-skips-purpose",
    "market-result-skips-unified-purpose",
    "decision-adapts-purpose-structure",
}

REQUIRED_RULE_SECTIONS = [
    "## 2. 先判断对象是否承载明确目的",
    "## 3. 最终目的与完成标准",
    "## 4. 当前状态、已有能力与客观限制",
    "## 5. 要解决的问题",
    "## 6. 设计原则与具体方案",
    "## 7. 新状态、新问题与后续方案",
    "## 8. 逻辑重建与真实历史分开",
    "## 9. 不同问题的结构变体",
    "## 10. 推理层与表达层的关系",
    "## 11. 输出前检查",
]


def fail(message: str) -> None:
    raise ValueError(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"Missing file: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}")
    raise AssertionError("unreachable")


def require_string_list(case_id: str, field: str, value: Any) -> None:
    if not isinstance(value, list) or not value:
        fail(f"Case {case_id} field {field} must be a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        fail(f"Case {case_id} field {field} must contain non-empty strings")


def validate_rule_file() -> None:
    if not RULE_PATH.is_file():
        fail(f"Missing rule file: {RULE_PATH.relative_to(ROOT)}")
    text = RULE_PATH.read_text(encoding="utf-8")
    missing = [section for section in REQUIRED_RULE_SECTIONS if section not in text]
    if missing:
        fail("Purpose rule file missing sections: " + ", ".join(missing))

    required_phrases = [
        "这是一组稳定的语义节点，不是所有问题都必须使用的标题模板",
        "不提前写入具体模块、协议、算法和实现属性",
        "当前状态”和“要解决的问题",
        "每项方案必须能够指出自己处理的是哪个已经证明的问题",
        "逻辑重建与真实历史分开",
    ]
    for phrase in required_phrases:
        if phrase not in text:
            fail(f"Purpose rule file missing required phrase: {phrase}")


def validate_skill_link() -> None:
    if not SKILL_PATH.is_file():
        fail("Missing SKILL.md")
    text = SKILL_PATH.read_text(encoding="utf-8")
    rel = "references/core/01a-目的、现状、问题与方案.md"
    if rel not in text:
        fail(f"SKILL.md must load {rel}")
    if "最终目的—当前状态与要解决的问题—采用的方案" not in text:
        fail("SKILL.md must describe the visible purpose structure")
    if "不应强行启用" not in text and "不能强行" not in text:
        fail("SKILL.md must preserve the applicability boundary")


def validate_cases() -> int:
    data = load_json(CASES_PATH)
    if data.get("version") != 1:
        fail("purpose-structure-regression-cases.json version must be 1")
    if data.get("rubric") != "evals/rubric.md":
        fail("Purpose regressions must use evals/rubric.md")

    dimensions = data.get("rubric_dimensions")
    if not isinstance(dimensions, list) or set(dimensions) != EXPECTED_DIMENSIONS:
        fail("Purpose regression rubric_dimensions must contain the ten reasoning dimensions")
    if len(dimensions) != len(set(dimensions)):
        fail("Purpose regression rubric_dimensions contains duplicates")

    invariants = data.get("global_invariants")
    if not isinstance(invariants, list) or len(invariants) < 10:
        fail("Purpose regressions require at least ten global invariants")
    if not all(isinstance(item, str) and item.strip() for item in invariants):
        fail("Purpose regression global invariants must be non-empty strings")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < len(REQUIRED_CASES):
        fail("Purpose regressions do not contain enough cases")

    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            fail("Each purpose regression case must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", case_id):
            fail(f"Invalid purpose regression case id: {case_id!r}")
        if case_id in ids:
            fail(f"Duplicate purpose regression case id: {case_id}")
        ids.add(case_id)

        for field in ("type", "prompt"):
            value = case.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"Case {case_id} requires {field}")
        for field in ("focus", "rubric_dimensions", "must", "must_not"):
            require_string_list(case_id, field, case.get(field))

        unknown = set(case["rubric_dimensions"]) - EXPECTED_DIMENSIONS
        if unknown:
            fail(f"Case {case_id} has unknown rubric dimensions: {sorted(unknown)}")

    missing = sorted(REQUIRED_CASES - ids)
    if missing:
        fail("Missing required purpose regression cases: " + ", ".join(missing))
    return len(cases)


def main() -> int:
    try:
        validate_rule_file()
        validate_skill_link()
        count = validate_cases()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("OK: purpose/current-state/problem/solution runtime rule")
    print(f"OK: verified {count} purpose-structure regression cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
