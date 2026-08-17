#!/usr/bin/env python3
"""Validate paragraph, example, code-block, and repetition controls."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RULE_PATH = ROOT / "references/writing/04-信息密度、段落与例子控制.md"
CASES_PATH = ROOT / "evals/writing-density-regression-cases.json"
SKILL_PATH = ROOT / "SKILL.md"

EXPECTED_DIMENSIONS = {
    "reader_focus",
    "causal_completeness",
    "information_selection",
    "structure_and_deduplication",
    "directness_and_flow",
    "supporting_material_control",
}

REQUIRED_CASES = {
    "agent-article-purpose-and-density",
    "fiber-detailed-without-micro-examples",
    "human-anger-short-without-example-padding",
    "decision-memo-no-display-padding",
    "harness-detailed-purpose-dense",
}

REQUIRED_PAIRS = {
    "merge-fragmented-paragraphs",
    "remove-micro-example-chain",
    "remove-plain-text-code-fence",
    "lift-solution-out-of-purpose",
    "compress-repetitive-summary",
    "state-question-before-purpose",
    "remove-generation-context",
}

REQUIRED_RULE_SECTIONS = [
    "## 2. 段落由主要结论闭合决定",
    "## 3. 默认先不用例子",
    "## 4. 优先使用整体例子，不制造微型例子串",
    "## 5. 代码块只承载需要精确保真的内容",
    "## 6. 列表只用于真实并列与步骤",
    "## 7. 一项核心结论只完整说明一次",
    "## 8. 详细程度来自关键关系，不来自篇幅填充",
    "## 9. 成文检查",
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


def require_string_list(item_id: str, field: str, value: Any) -> None:
    if not isinstance(value, list) or not value:
        fail(f"Item {item_id} field {field} must be a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        fail(f"Item {item_id} field {field} must contain non-empty strings")


def validate_rule_file() -> None:
    if not RULE_PATH.is_file():
        fail(f"Missing rule file: {RULE_PATH.relative_to(ROOT)}")
    text = RULE_PATH.read_text(encoding="utf-8")
    missing = [section for section in REQUIRED_RULE_SECTIONS if section not in text]
    if missing:
        fail("Writing density rule file missing sections: " + ", ".join(missing))

    required_phrases = [
        "不能把“一句推进一个主要关系”误解成“一句话一个段落”",
        "默认先不用例子",
        "优先在主要原理已经讲清后，使用一个能够贯穿主链的代表性例子",
        "普通中文句子",
        "总结不重新枚举正文中的全部模块",
        "实际分析问题",
        "用户当前材料",
    ]
    for phrase in required_phrases:
        if phrase not in text:
            fail(f"Writing density rule file missing required phrase: {phrase}")


def validate_skill_link() -> None:
    if not SKILL_PATH.is_file():
        fail("Missing SKILL.md")
    text = SKILL_PATH.read_text(encoding="utf-8")
    rel = "references/writing/04-信息密度、段落与例子控制.md"
    if rel not in text:
        fail(f"SKILL.md must load {rel}")
    for phrase in ("默认先不用例子", "一句话一个段落", "普通文字放进代码块", "实际分析问题", "分析定稿"):
        if phrase not in text:
            fail(f"SKILL.md missing writing-density control: {phrase}")


def validate_cases_and_pairs() -> tuple[int, int]:
    data = load_json(CASES_PATH)
    if data.get("version") != 1:
        fail("writing-density-regression-cases.json version must be 1")
    if data.get("rubric") != "evals/writing-rubric.md":
        fail("Writing density regressions must use evals/writing-rubric.md")

    dimensions = data.get("rubric_dimensions")
    if not isinstance(dimensions, list) or set(dimensions) != EXPECTED_DIMENSIONS:
        fail("Writing density rubric_dimensions must contain the six writing dimensions")
    if len(dimensions) != len(set(dimensions)):
        fail("Writing density rubric_dimensions contains duplicates")

    invariants = data.get("global_invariants")
    if not isinstance(invariants, list) or len(invariants) < 10:
        fail("Writing density regressions require at least ten global invariants")
    if not all(isinstance(item, str) and item.strip() for item in invariants):
        fail("Writing density global invariants must be non-empty strings")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < len(REQUIRED_CASES):
        fail("Writing density regressions do not contain enough cases")

    case_ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            fail("Each writing density case must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", case_id):
            fail(f"Invalid writing density case id: {case_id!r}")
        if case_id in case_ids:
            fail(f"Duplicate writing density case id: {case_id}")
        case_ids.add(case_id)

        for field in ("type", "prompt"):
            value = case.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"Case {case_id} requires {field}")
        for field in ("focus", "rubric_dimensions", "must", "must_not"):
            require_string_list(case_id, field, case.get(field))
        unknown = set(case["rubric_dimensions"]) - EXPECTED_DIMENSIONS
        if unknown:
            fail(f"Case {case_id} has unknown rubric dimensions: {sorted(unknown)}")

    missing_cases = sorted(REQUIRED_CASES - case_ids)
    if missing_cases:
        fail("Missing required writing density cases: " + ", ".join(missing_cases))

    pairs = data.get("style_pairs")
    if not isinstance(pairs, list) or len(pairs) < len(REQUIRED_PAIRS):
        fail("Writing density regressions do not contain enough style pairs")

    pair_ids: set[str] = set()
    for pair in pairs:
        if not isinstance(pair, dict):
            fail("Each writing density style pair must be an object")
        pair_id = pair.get("id")
        if not isinstance(pair_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", pair_id):
            fail(f"Invalid writing density pair id: {pair_id!r}")
        if pair_id in pair_ids:
            fail(f"Duplicate writing density pair id: {pair_id}")
        pair_ids.add(pair_id)

        for field in ("before", "after", "transformation"):
            value = pair.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"Style pair {pair_id} requires {field}")
        for field in ("must_preserve", "must_not_infer"):
            require_string_list(pair_id, field, pair.get(field))

    missing_pairs = sorted(REQUIRED_PAIRS - pair_ids)
    if missing_pairs:
        fail("Missing required writing density style pairs: " + ", ".join(missing_pairs))

    return len(cases), len(pairs)


def main() -> int:
    try:
        validate_rule_file()
        validate_skill_link()
        case_count, pair_count = validate_cases_and_pairs()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("OK: writing density runtime rule")
    print(f"OK: verified {case_count} writing density regression cases")
    print(f"OK: verified {pair_count} writing density style pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
