#!/usr/bin/env python3
"""Validate writing-density rules and fixtures, not generated prose quality."""

from __future__ import annotations

import argparse
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

MATERIAL_CASES = {
    "feedback-reading-group",
    "example-before-abstraction",
    "incremental-scenario-and-recap",
    "demo-evidence-boundary",
    "text-table-complement",
    "markdown-without-forced-layout",
    "keep-short-without-example",
    "non-purpose-without-padding",
    "parallel-without-false-transition",
}
REQUIRED_CASES = {
    "agent-article-purpose-and-density",
    "fiber-detailed-without-micro-examples",
    "human-anger-short-without-example-padding",
    "decision-memo-no-display-padding",
    "harness-detailed-purpose-dense",
} | MATERIAL_CASES

REQUIRED_PAIRS = {
    "merge-fragmented-paragraphs",
    "remove-micro-example-chain",
    "remove-plain-text-code-fence",
    "lift-solution-out-of-purpose",
    "compress-repetitive-summary",
    "state-question-before-purpose",
    "remove-generation-context",
    "split-proof-by-reading-task",
    "example-at-first-need",
    "incremental-scenario-with-recap",
    "demo-support-near-claim",
    "keep-complementary-table-and-text",
    "keep-sufficient-no-example",
}

REQUIRED_RULE_SECTIONS = [
    "## 2. 段落按阅读任务分组，论点保持完整",
    "## 3. 例子在第一次帮助理解时出现",
    "## 4. 复用场景，按当前问题展示必要部分",
    "## 5. 代码块只承载需要精确保真的内容",
    "## 6. 列表只用于真实并列与步骤",
    "## 7. 一项核心结论只完整说明一次",
    "## 8. 详细程度来自关键关系，不来自篇幅填充",
    "## 8.2 连续阅读中的理解负担",
    "## 8.3 判断、证据与展示相互对应",
    "## 9. 成文检查",
]

# These are stale runtime instructions, not semantic quality metrics for articles.
STALE_DIRECTIVES = (
    "默认先不用例子",
    "优先在主要原理已经讲清后，使用一个能够贯穿主链的代表性例子",
    "支撑同一结论的相邻句留在本段",
    "多句话共同证明同一结论时放在同一段",
    "段落由一个主要新结论是否闭合决定",
)


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
        "多个相邻段落共同完成",
        "直接语言已经足够时",
        "说明性例子、真实演示与证据分开",
        "简短回指",
        "普通中文句子",
        "总结不重新枚举正文中的全部模块",
        "完整分析任务",
        "读者可见问题",
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
    for phrase in ("例子在第一次帮助理解时出现", "相邻段落", "一句话一个段落", "普通文字放进代码块", "完整分析任务", "读者可见问题", "分析定稿"):
        if phrase not in text:
            fail(f"SKILL.md missing writing-density control: {phrase}")

    runtime_paths = [
        SKILL_PATH, ROOT / "AGENTS.md", ROOT / "agents/openai.yaml",
        ROOT / "references/core/05-输出与表达规则.md",
        ROOT / "references/core/06-文章成稿与压缩.md",
        *sorted((ROOT / "references/writing").glob("*.md")),
    ]
    for path in runtime_paths:
        if not path.is_file():
            fail(f"Missing runtime file: {path.relative_to(ROOT)}")
        content = path.read_text(encoding="utf-8")
        for phrase in STALE_DIRECTIVES:
            if phrase in content:
                fail(f"Stale writing instruction in {path.relative_to(ROOT)}: {phrase}")


def validate_cases_and_pairs(data: Any = None) -> tuple[int, int]:
    if data is None:
        data = load_json(CASES_PATH)
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
        fail("writing-density-regression-cases.json version must be 1")
    if data.get("rubric") != "evals/writing-rubric.md":
        fail("Writing density regressions must use evals/writing-rubric.md")

    dimensions = data.get("rubric_dimensions")
    require_string_list("writing density", "rubric_dimensions", dimensions)
    if set(dimensions) != EXPECTED_DIMENSIONS:
        fail("Writing density rubric_dimensions must contain the six writing dimensions")
    if len(dimensions) != len(set(dimensions)):
        fail("Writing density rubric_dimensions contains duplicates")

    invariants = data.get("global_invariants")
    require_string_list("writing density", "global_invariants", invariants)
    if len(invariants) < 10:
        fail("Writing density regressions require at least ten global invariants")
    require_string_list("writing density", "generation_instructions", data.get("generation_instructions"))

    materials = data.get("materials")
    if not isinstance(materials, dict) or not materials:
        fail("Writing density regressions require locked materials")
    for material_id, facts in materials.items():
        if not isinstance(material_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", material_id):
            fail(f"Invalid writing density material id: {material_id!r}")
        require_string_list(material_id, "facts", facts)

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

        if case_id in MATERIAL_CASES or "material" in case:
            material_id = case.get("material")
            if not isinstance(material_id, str) or material_id not in materials:
                fail(f"Case {case_id} references unknown material: {material_id!r}")

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
        # A sufficient original sentence may deliberately remain unchanged.

    missing_pairs = sorted(REQUIRED_PAIRS - pair_ids)
    if missing_pairs:
        fail("Missing required writing density style pairs: " + ", ".join(missing_pairs))

    return len(cases), len(pairs)


def writing_density_input(data: Any, case_id: str) -> dict[str, Any]:
    """Allowlist only locked facts and the request; never pass reviewer fields."""
    validate_cases_and_pairs(data)
    for case in data["cases"]:
        if case["id"] == case_id:
            material_id = case.get("material")
            facts = list(data["materials"][material_id]) if material_id else []
            return {"facts": facts, "request": case["prompt"]}
    fail(f"Unknown writing density case: {case_id}")
    raise AssertionError("unreachable")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", help="Print generation input only for an existing case ID")
    args = parser.parse_args()
    try:
        if args.case:
            print(json.dumps(writing_density_input(load_json(CASES_PATH), args.case), ensure_ascii=False, indent=2))
            return 0
        validate_rule_file()
        validate_skill_link()
        case_count, pair_count = validate_cases_and_pairs()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("OK: writing density runtime rules and entry consistency (structure only)")
    print(f"OK: verified {case_count} writing density regression cases")
    print(f"OK: verified {pair_count} writing density style pairs")
    print("NOTE: structure checks do not establish generated prose quality or reading improvement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
