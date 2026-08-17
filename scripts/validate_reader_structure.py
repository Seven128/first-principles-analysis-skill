#!/usr/bin/env python3
"""Validate reader-facing questions, purpose layering, and heading hierarchy."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RULE_PATH = ROOT / "references/writing/05-结构节点、信息层级与标题.md"
CASES_PATH = ROOT / "evals/reader-structure-regression-cases.json"
SKILL_PATH = ROOT / "SKILL.md"
CONTRACT_PATH = ROOT / "references/writing/00-分析定稿与文章契约.md"
PURPOSE_PATH = ROOT / "references/core/01a-目的、现状、问题与方案.md"

EXPECTED_DIMENSIONS = {
    "reader_focus",
    "causal_completeness",
    "information_selection",
    "structure_and_deduplication",
    "directness_and_flow",
    "supporting_material_control",
}

REQUIRED_CASES = {
    "agent-reader-question-not-answer-catalog",
    "designed-system-purpose-target-state",
    "goal-solving-purpose-keeps-outcome",
    "informative-heading-names-capabilities",
    "heading-depth-by-semantic-independence",
    "parent-child-no-full-repetition",
}

REQUIRED_PAIRS = {
    "compress-internal-task-to-reader-question",
    "purpose-target-state-before-criteria",
    "replace-suspense-heading-with-information",
    "use-bold-lead-for-compact-aspect",
}

REQUIRED_RULE_SECTIONS = [
    "## 2. 三类交接信息必须分开",
    "## 3. 每个结构节点只承担一种主要职责",
    "## 4. 原理还原型最终目的先锁定对象角色",
    "## 5. 信息在第一次成为必要答案时出现",
    "## 6. 标题必须直接提供信息",
    "## 7. 何时建立小标题",
    "## 8. 标题层级",
    "## 9. 父章节与子章节分工",
    "## 10. 成文检查",
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


def validate_runtime() -> None:
    for path in (RULE_PATH, CASES_PATH, SKILL_PATH, CONTRACT_PATH, PURPOSE_PATH):
        if not path.is_file():
            fail(f"Missing runtime file: {path.relative_to(ROOT)}")

    rule = RULE_PATH.read_text(encoding="utf-8")
    missing = [section for section in REQUIRED_RULE_SECTIONS if section not in rule]
    if missing:
        fail("Reader structure rule missing sections: " + ", ".join(missing))
    for phrase in (
        "完整分析任务",
        "读者可见问题",
        "必须覆盖项与证据边界",
        "稳定角色与目标状态",
        "标题必须直接提供信息",
        "段首粗体",
        "父章节只建立总关系",
    ):
        if phrase not in rule:
            fail(f"Reader structure rule missing phrase: {phrase}")

    skill = SKILL_PATH.read_text(encoding="utf-8")
    for phrase in (
        "references/writing/05-结构节点、信息层级与标题.md",
        "内部完整分析任务",
        "读者可见问题",
        "validate_reader_structure.py",
    ):
        if phrase not in skill:
            fail(f"SKILL.md missing reader-structure invariant: {phrase}")

    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    for phrase in ("完整分析任务", "读者可见问题", "必须覆盖项"):
        if phrase not in contract:
            fail(f"Article contract missing field: {phrase}")

    purpose = PURPOSE_PATH.read_text(encoding="utf-8")
    for phrase in ("稳定角色与目标状态", "完成标准单独保存", "接口调用的大模型"):
        if phrase not in purpose:
            fail(f"Purpose rule missing concept: {phrase}")

    legacy_paths = [
        ROOT / "AGENTS.md",
        SKILL_PATH,
        ROOT / "agents/openai.yaml",
        ROOT / "references/core/05-输出与表达规则.md",
        ROOT / "references/core/06-文章成稿与压缩.md",
        ROOT / "references/writing/01-写作规则卡.md",
        ROOT / "references/writing/02-文章任务适配.md",
        ROOT / "references/writing/03-成文检查.md",
        ROOT / "references/writing/04-信息密度、段落与例子控制.md",
        ROOT / "evals/writing-rubric.md",
        ROOT / "evals/writing-style-pairs.json",
        ROOT / "evals/writing-regression-cases.json",
        ROOT / "evals/writing-density-regression-cases.json",
    ]
    legacy_phrases = (
        "文章开头写出补全后的实际分析问题",
        "标题之后尽快写出补全后的实际分析问题",
        "标题之后默认先写出补全后的实际分析问题",
        "标题之后先写出实际分析问题",
        "标题后先写补全后的实际分析问题",
        "标题后先写出补全后的实际分析问题",
        "文章标题后是否尽快呈现同一个问题",
        "最终目的是否描述外部结果和完成标准",
        "把分析阶段补全的问题放在文章开头",
    )
    for path in legacy_paths:
        text = path.read_text(encoding="utf-8")
        for phrase in legacy_phrases:
            if phrase in text:
                fail(f"Legacy reader-structure wording remains in {path.relative_to(ROOT)}: {phrase}")

def validate_cases() -> tuple[int, int]:
    data = load_json(CASES_PATH)
    if data.get("version") != 1:
        fail("reader-structure-regression-cases.json version must be 1")

    dimensions = data.get("rubric_dimensions")
    if not isinstance(dimensions, list) or set(dimensions) != EXPECTED_DIMENSIONS:
        fail("Reader structure rubric_dimensions must contain the six writing dimensions")
    if len(dimensions) != len(set(dimensions)):
        fail("Reader structure rubric_dimensions contains duplicates")

    invariants = data.get("global_invariants")
    require_string_list("global", "global_invariants", invariants)
    if len(invariants) < 8:
        fail("Reader structure regressions require at least eight global invariants")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < len(REQUIRED_CASES):
        fail("Reader structure regressions do not contain enough cases")

    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            fail("Each reader structure case must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", case_id):
            fail(f"Invalid reader structure case id: {case_id!r}")
        if case_id in ids:
            fail(f"Duplicate reader structure case id: {case_id}")
        ids.add(case_id)
        for field in ("type", "prompt"):
            value = case.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"Case {case_id} requires {field}")
        for field in ("focus", "must", "must_not"):
            require_string_list(case_id, field, case.get(field))

    missing_cases = sorted(REQUIRED_CASES - ids)
    if missing_cases:
        fail("Missing reader structure cases: " + ", ".join(missing_cases))

    pairs = data.get("style_pairs")
    if not isinstance(pairs, list) or len(pairs) < len(REQUIRED_PAIRS):
        fail("Reader structure regressions do not contain enough style pairs")
    pair_ids: set[str] = set()
    for pair in pairs:
        if not isinstance(pair, dict):
            fail("Each reader structure style pair must be an object")
        pair_id = pair.get("id")
        if not isinstance(pair_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", pair_id):
            fail(f"Invalid reader structure pair id: {pair_id!r}")
        if pair_id in pair_ids:
            fail(f"Duplicate reader structure pair id: {pair_id}")
        pair_ids.add(pair_id)
        for field in ("before", "after", "transformation"):
            value = pair.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"Style pair {pair_id} requires {field}")
        for field in ("must_preserve", "must_not_infer"):
            require_string_list(pair_id, field, pair.get(field))

    missing_pairs = sorted(REQUIRED_PAIRS - pair_ids)
    if missing_pairs:
        fail("Missing reader structure pairs: " + ", ".join(missing_pairs))
    return len(cases), len(pairs)


def main() -> int:
    try:
        validate_runtime()
        case_count, pair_count = validate_cases()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("OK: reader-facing question, purpose layering, and heading hierarchy rules")
    print(f"OK: verified {case_count} reader-structure regression cases")
    print(f"OK: verified {pair_count} reader-structure style pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
