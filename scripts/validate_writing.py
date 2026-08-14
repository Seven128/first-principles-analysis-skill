#!/usr/bin/env python3
"""Validate the article-composition runtime and writing regressions."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]

WRITING_REFERENCES = [
    "references/writing/01-写作规则卡.md",
    "references/writing/02-文章任务适配.md",
    "references/writing/03-成文检查.md",
]

REQUIRED_PATHS = [
    "references/core/05-输出与表达规则.md",
    "references/core/06-文章成稿与压缩.md",
    *WRITING_REFERENCES,
    "evals/writing-rubric.md",
    "evals/writing-regression-cases.json",
    "evals/writing-style-pairs.json",
    "evals/writing-score-template.json",
]

WRITING_CORE_SECTIONS = [
    "## 1. 成文层的位置",
    "## 2. 有效信息密度",
    "## 3. 先确定文章任务",
    "## 4. 提取最小完整因果主线",
    "## 5. 控制信息层级",
    "## 7. 压缩时保留因果桥梁",
    "## 8. 一条结论只说明一次",
    "## 9. 具体化、例子与比喻",
    "## 11. 四层检查与局部重写",
    "## 12. 详细程度校准",
    "## 13. 成稿检查",
]

WRITING_REFERENCE_SECTIONS = {
    "references/writing/01-写作规则卡.md": [
        "## 1. 一句推进一个主要关系",
        "## 2. 从平铺属性中恢复真实依赖",
        "## 3. 抽象名词还原为主体、动作和状态变化",
        "## 4. 细节在第一次成为必要答案时出现",
        "## 5. 一段闭合一个主要新结论",
        "## 6. 例子必须替正文完成一项工作",
        "## 7. 先具体化，最后才考虑比喻",
        "## 8. 删字不能删掉因果桥",
    ],
    "references/writing/02-文章任务适配.md": [
        "## 1. 原理与机制解释",
        "## 2. 完整方案与系统设计",
        "## 3. 决策备忘录与比较",
        "## 4. 经营、商业与行动分析",
        "## 5. 人的行为与社会机制解释",
        "## 7. 读者水平适配",
        "## 8. 可选语气与作者风味",
    ],
    "references/writing/03-成文检查.md": [
        "## L1：语言与表面负担",
        "## L2：结构与关系",
        "## L3：内容保真与信息选择",
        "## L4：整体阅读检查",
        "## 修复顺序",
        "## 自动检查的边界",
    ],
}

EXPECTED_DIMENSIONS = {
    "reader_focus",
    "causal_completeness",
    "information_selection",
    "structure_and_deduplication",
    "directness_and_flow",
    "supporting_material_control",
}

REQUIRED_CASES = {
    "agent-article-density",
    "fiber-article-density",
    "harness-detailed-without-repetition",
    "human-anger-plain-article",
    "job-offer-decision-memo",
    "api-growth-report-density",
    "http-evolution-readable-density",
    "human-procrastination-readable-density",
}

REQUIRED_PAIRS = {
    "fiber-flat-enumeration",
    "fiber-field-disclosure",
    "agent-nominalization",
    "harness-detail-overload",
    "human-shared-chain",
    "api-growth-result-chain",
    "decision-conclusion-first",
    "metaphor-gate",
}


def fail(message: str) -> None:
    raise ValueError(message)


def load_json(rel: str) -> Any:
    path = ROOT / rel
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"Missing JSON file: {rel}")
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {rel}: {exc}")
    raise AssertionError("unreachable")


def require_sections(rel: str, sections: Iterable[str]) -> None:
    text = (ROOT / rel).read_text(encoding="utf-8")
    missing = [section for section in sections if section not in text]
    if missing:
        fail(f"{rel} missing sections: {', '.join(missing)}")


def require_string_list(item_id: str, field: str, value: Any) -> None:
    if not isinstance(value, list) or not value or not all(
        isinstance(entry, str) and entry.strip() for entry in value
    ):
        fail(f"{item_id} field {field} must be a non-empty string list")


def reasoning_case_ids() -> set[str]:
    data = load_json("evals/regression-cases.json")
    cases = data.get("cases")
    if not isinstance(cases, list):
        fail("evals/regression-cases.json requires cases")
    ids = {case.get("id") for case in cases if isinstance(case, dict)}
    return {item for item in ids if isinstance(item, str)}


def validate_runtime() -> int:
    missing = [rel for rel in REQUIRED_PATHS if not (ROOT / rel).is_file()]
    if missing:
        fail("Missing writing files: " + ", ".join(missing))

    require_sections("references/core/06-文章成稿与压缩.md", WRITING_CORE_SECTIONS)
    for rel, sections in WRITING_REFERENCE_SECTIONS.items():
        require_sections(rel, sections)

    core = (ROOT / "references/core/06-文章成稿与压缩.md").read_text(encoding="utf-8")
    missing_links = [rel for rel in WRITING_REFERENCES if f"`{rel}`" not in core]
    if missing_links:
        fail("Composition core does not load: " + ", ".join(missing_links))

    output_rules = (ROOT / "references/core/05-输出与表达规则.md").read_text(encoding="utf-8")
    for phrase in ("有效信息密度", "一个主要新结论", "具体主体、动作和状态变化"):
        if phrase not in output_rules:
            fail(f"Output rules missing writing invariant: {phrase}")

    rubric = (ROOT / "evals/writing-rubric.md").read_text(encoding="utf-8")
    for phrase in ("局部负担", "并行条件", "比喻"):
        if phrase not in rubric:
            fail(f"Writing rubric missing diagnostic concept: {phrase}")

    return len(WRITING_REFERENCES)


def validate_cases(known_reasoning_ids: set[str]) -> tuple[int, set[str]]:
    data = load_json("evals/writing-regression-cases.json")
    if data.get("version") != 1:
        fail("evals/writing-regression-cases.json version must be 1")

    for field in ("rubric", "reasoning_rubric", "style_pairs"):
        rel = data.get(field)
        if not isinstance(rel, str) or not (ROOT / rel).is_file():
            fail(f"writing-regression-cases.json {field} must reference an existing file")

    dimensions = data.get("rubric_dimensions")
    if not isinstance(dimensions, list) or set(dimensions) != EXPECTED_DIMENSIONS:
        fail("writing rubric_dimensions must contain the expected six dimensions")
    if len(dimensions) != len(set(dimensions)):
        fail("writing rubric_dimensions contains duplicates")

    invariants = data.get("global_invariants")
    if not isinstance(invariants, list) or len(invariants) < 12 or not all(
        isinstance(item, str) and item.strip() for item in invariants
    ):
        fail("writing global_invariants must contain at least twelve strings")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < 8:
        fail("writing-regression-cases.json must contain at least eight cases")

    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            fail("Each writing regression case must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", case_id):
            fail(f"Invalid writing regression case id: {case_id!r}")
        if case_id in ids:
            fail(f"Duplicate writing regression case id: {case_id}")
        ids.add(case_id)

        reasoning_id = case.get("reasoning_case_id")
        if reasoning_id not in known_reasoning_ids:
            fail(f"Writing case {case_id} references unknown reasoning case: {reasoning_id!r}")

        for field in ("type", "prompt", "output_mode"):
            value = case.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"Writing case {case_id} requires {field}")
        for field in ("focus", "rubric_dimensions", "must", "must_not"):
            require_string_list(case_id, field, case.get(field))
        unknown = set(case["rubric_dimensions"]) - EXPECTED_DIMENSIONS
        if unknown:
            fail(f"Writing case {case_id} has unknown dimensions: {sorted(unknown)}")

    missing = sorted(REQUIRED_CASES - ids)
    if missing:
        fail("Missing required writing cases: " + ", ".join(missing))
    return len(cases), ids


def validate_pairs(known_reasoning_ids: set[str]) -> int:
    data = load_json("evals/writing-style-pairs.json")
    if data.get("version") != 1:
        fail("evals/writing-style-pairs.json version must be 1")
    if not isinstance(data.get("purpose"), str) or not data["purpose"].strip():
        fail("writing-style-pairs.json requires purpose")

    pairs = data.get("pairs")
    if not isinstance(pairs, list) or len(pairs) < 8:
        fail("writing-style-pairs.json must contain at least eight pairs")

    ids: set[str] = set()
    for pair in pairs:
        if not isinstance(pair, dict):
            fail("Each writing style pair must be an object")
        pair_id = pair.get("id")
        if not isinstance(pair_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", pair_id):
            fail(f"Invalid writing style pair id: {pair_id!r}")
        if pair_id in ids:
            fail(f"Duplicate writing style pair id: {pair_id}")
        ids.add(pair_id)

        reasoning_id = pair.get("reasoning_case_id")
        if reasoning_id not in known_reasoning_ids:
            fail(f"Writing pair {pair_id} references unknown reasoning case: {reasoning_id!r}")
        for field in ("issue", "before", "after"):
            value = pair.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"Writing pair {pair_id} requires {field}")
        for field in ("transformations", "must_preserve", "must_not_infer"):
            require_string_list(pair_id, field, pair.get(field))
        if pair["before"].strip() == pair["after"].strip():
            fail(f"Writing pair {pair_id} before and after must differ")

    missing = sorted(REQUIRED_PAIRS - ids)
    if missing:
        fail("Missing required writing pairs: " + ", ".join(missing))
    return len(pairs)


def validate_score_template(case_ids: set[str]) -> None:
    data = load_json("evals/writing-score-template.json")
    if data.get("version") != 1:
        fail("evals/writing-score-template.json version must be 1")
    results = data.get("results")
    if not isinstance(results, list) or not results:
        fail("writing-score-template.json requires results")
    for result in results:
        if not isinstance(result, dict) or result.get("id") not in case_ids:
            fail("writing-score-template.json references an unknown writing case")
        scores = result.get("scores")
        if not isinstance(scores, dict) or set(scores) != EXPECTED_DIMENSIONS:
            fail("writing-score-template.json dimensions do not match the writing rubric")


def main() -> int:
    try:
        reference_count = validate_runtime()
        reasoning_ids = reasoning_case_ids()
        case_count, case_ids = validate_cases(reasoning_ids)
        pair_count = validate_pairs(reasoning_ids)
        validate_score_template(case_ids)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK: verified {reference_count} writing runtime references")
    print(f"OK: verified {case_count} writing regression cases")
    print(f"OK: verified {pair_count} paired writing samples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
