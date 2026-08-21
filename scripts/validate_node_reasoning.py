#!/usr/bin/env python3
"""Validate key-node reasoning and optional supplementary-analysis regressions."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODE_CASES_PATH = ROOT / "evals/node-validation-regression-cases.json"
SUPPLEMENTARY_CASES_PATH = ROOT / "evals/supplementary-analysis-regression-cases.json"
WHY_RULE_PATH = ROOT / "references/core/02-为什么类问题推理.md"
HOW_RULE_PATH = ROOT / "references/core/03-怎么做类问题推理.md"
EVIDENCE_RULE_PATH = ROOT / "references/core/04-客观性与证据规则.md"
NODE_RULE_PATH = ROOT / "references/core/04a-关键推理节点反向校验.md"

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

REQUIRED_NODE_CASE_IDS = {
    "commute-inverse-not-contrapositive",
    "cache-missing-sufficient-conditions",
    "replication-not-unique-necessity",
    "exercise-probability-counterexample",
    "core-project-common-cause",
}

REQUIRED_SUPPLEMENTARY_CASE_IDS = {
    "mechanism-explanation-skips-forced-history",
    "historical-axis-when-evolution-is-unknown",
    "horizontal-comparison-tests-necessity",
    "horizontal-comparison-tests-sufficiency",
    "action-route-skips-history-detour",
    "double-derivation-without-rebuild-bias",
    "cross-domain-transfer-requires-structural-map",
    "multi-perspective-without-fake-experts",
    "future-paths-are-conditional-not-fixed",
    "minimum-experiment-maximizes-information-value",
    "simple-definition-skips-supplementary-methods",
    "single-emotion-skips-forced-history-and-comparison",
}


def fail(message: str) -> None:
    raise ValueError(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        fail(f"Missing JSON file: {path.relative_to(ROOT)}")
        raise exc
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}")
        raise exc


def require_string_list(item_id: str, field: str, value: Any) -> None:
    if not isinstance(value, list) or not value:
        fail(f"Item {item_id} field {field} must be a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        fail(f"Item {item_id} field {field} must contain non-empty strings")


def validate_runtime_rules() -> None:
    requirements = {
        WHY_RULE_PATH: (
            "补充分析轴不能替代主因果链",
            "历史纵轴",
            "横向对照",
            "多视角交叉审查",
            "路径数量由真实分支决定",
        ),
        HOW_RULE_PATH: (
            "双遍推导",
            "不默认推倒重来",
            "跨领域借解",
            "多视角交叉审查",
            "信息价值最高的最小实验",
            "不固定为三项或七天",
        ),
        NODE_RULE_PATH: (
            "使用真实对照增强反向校验",
            "相同目标、不同实现",
            "相同机制、不同结果",
            "同一对象、不同时间",
            "历史可见选项",
        ),
        EVIDENCE_RULE_PATH: (
            "历史演化证据",
            "横向比较证据",
            "跨领域类比证据",
            "未来场景证据",
        ),
    }

    for path, phrases in requirements.items():
        if not path.is_file():
            fail(f"Missing runtime rule file: {path.relative_to(ROOT)}")
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                fail(f"{path.relative_to(ROOT)} missing required phrase: {phrase}")

    why_text = WHY_RULE_PATH.read_text(encoding="utf-8")
    how_text = HOW_RULE_PATH.read_text(encoding="utf-8")
    for phrase in (
        "简单定义、当前机制说明、一次具体情绪、普通事实确认",
        "不因为存在这些方法就自动变成历史研究或竞品分析",
    ):
        if phrase not in why_text:
            fail(f"Why reasoning rule missing anti-overgeneralization boundary: {phrase}")
    for phrase in (
        "不能跳过主链直接给热门方案",
        "用户只需要从零设计一条路径时，不先写一段对象发展史",
    ):
        if phrase not in how_text:
            fail(f"How reasoning rule missing anti-overgeneralization boundary: {phrase}")


def validate_case_suite(path: Path, required_ids: set[str], *, minimum_cases: int, minimum_invariants: int) -> tuple[int, int]:
    data = load_json(path)

    if data.get("version") != 1:
        fail(f"{path.name} version must be 1")

    purpose = data.get("purpose")
    if not isinstance(purpose, str) or not purpose.strip():
        fail(f"{path.name} requires purpose")

    rubric = data.get("rubric")
    if not isinstance(rubric, str) or not (ROOT / rubric).is_file():
        fail(f"{path.name} rubric must reference an existing file")

    dimensions = data.get("rubric_dimensions")
    require_string_list("global", "rubric_dimensions", dimensions)
    unknown_global_dimensions = set(dimensions) - EXPECTED_DIMENSIONS
    if unknown_global_dimensions:
        fail(f"Unknown global rubric dimensions in {path.name}: {sorted(unknown_global_dimensions)}")
    if len(dimensions) != len(set(dimensions)):
        fail(f"{path.name} global rubric_dimensions contains duplicates")

    invariants = data.get("global_invariants")
    require_string_list("global", "global_invariants", invariants)
    if len(invariants) < minimum_invariants:
        fail(f"{path.name} global_invariants must contain at least {minimum_invariants} items")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < minimum_cases:
        fail(f"{path.name} must contain at least {minimum_cases} cases")

    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            fail(f"Each case in {path.name} must be an object")

        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", case_id):
            fail(f"Invalid case id in {path.name}: {case_id!r}")
        if case_id in ids:
            fail(f"Duplicate case id in {path.name}: {case_id}")
        ids.add(case_id)

        for field in ("type", "prompt"):
            value = case.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"Case {case_id} in {path.name} requires {field}")

        for field in ("focus", "rubric_dimensions", "must", "must_not"):
            require_string_list(case_id, field, case.get(field))

        unknown_dimensions = set(case["rubric_dimensions"]) - EXPECTED_DIMENSIONS
        if unknown_dimensions:
            fail(f"Case {case_id} in {path.name} has unknown rubric dimensions: {sorted(unknown_dimensions)}")
        if len(case["rubric_dimensions"]) != len(set(case["rubric_dimensions"])):
            fail(f"Case {case_id} in {path.name} rubric_dimensions contains duplicates")

    missing = sorted(required_ids - ids)
    if missing:
        fail(f"Missing required cases in {path.name}: " + ", ".join(missing))

    return len(cases), len(invariants)


def main() -> int:
    validate_runtime_rules()
    node_cases, node_invariants = validate_case_suite(
        NODE_CASES_PATH,
        REQUIRED_NODE_CASE_IDS,
        minimum_cases=5,
        minimum_invariants=6,
    )
    supplementary_cases, supplementary_invariants = validate_case_suite(
        SUPPLEMENTARY_CASES_PATH,
        REQUIRED_SUPPLEMENTARY_CASE_IDS,
        minimum_cases=12,
        minimum_invariants=10,
    )

    print("Validated node reasoning suite: " f"{node_cases} cases, {node_invariants} global invariants")
    print("Validated supplementary analysis suite: " f"{supplementary_cases} cases, {supplementary_invariants} global invariants")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
