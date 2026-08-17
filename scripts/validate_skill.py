#!/usr/bin/env python3
"""Validate the standalone first-principles-analysis skill repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]

CORE_PATHS = [
    "references/core/00-第一性原理核心原则.md",
    "references/core/01-问题识别与分类.md",
    "references/core/02-为什么类问题推理.md",
    "references/core/03-怎么做类问题推理.md",
    "references/core/04-客观性与证据规则.md",
    "references/core/05-输出与表达规则.md",
    "references/core/06-文章成稿与压缩.md",
]

SUBJECT_PATHS = [
    "references/subjects/人的行为与情绪.md",
    "references/subjects/群体与组织.md",
    "references/subjects/技术系统与产品.md",
    "references/subjects/行业市场与资源流动.md",
    "references/subjects/商业与赚钱.md",
    "references/subjects/制度与政策.md",
    "references/subjects/自然与生物系统.md",
]

CONCLUSION_PATHS = [
    "references/conclusions/利益关系链.md",
    "references/conclusions/资源分配.md",
    "references/conclusions/反馈延迟与周期.md",
    "references/conclusions/人的行为与情绪.md",
    "references/conclusions/信息能力与时间差.md",
    "references/conclusions/资金流向.md",
]

REQUIRED_PATHS = [
    "SKILL.md",
    "README.md",
    "AGENTS.md",
    "agents/openai.yaml",
    "references/README.md",
    "references/第一性原理分析逻辑.md",
    "references/第一性原理分析提示词.md",
    "references/writing/00-分析定稿与文章契约.md",
    "references/source-manifest.json",
    "references/examples/旧案例使用说明.md",
    "evals/README.md",
    "evals/rubric.md",
    "evals/regression-cases.json",
    "evals/score-template.json",
    "evals/writing-rubric.md",
    "evals/writing-regression-cases.json",
    "evals/writing-score-template.json",
    "scripts/eval_report.py",
    "scripts/lint_language.py",
    "scripts/validate_conclusions.py",
    *CORE_PATHS,
    *SUBJECT_PATHS,
    *CONCLUSION_PATHS,
]

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

WRITING_SECTIONS = [
    "## 1. 成文层的位置",
    "## 3. 先确定文章任务",
    "## 4. 提取最小完整因果主线",
    "## 5. 控制信息层级",
    "## 7. 压缩时保留因果桥梁",
    "## 8. 一条结论只说明一次",
    "## 12. 详细程度校准",
    "## 13. 成稿检查",
]

EXPECTED_RUBRIC_DIMENSIONS = {
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

EXPECTED_WRITING_RUBRIC_DIMENSIONS = {
    "reader_focus",
    "causal_completeness",
    "information_selection",
    "structure_and_deduplication",
    "directness_and_flow",
    "supporting_material_control",
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


def parse_skill_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail("SKILL.md must start with YAML frontmatter")

    end = text.find("\n---\n", 4)
    if end == -1:
        fail("SKILL.md frontmatter is not closed")

    values: dict[str, str] = {}
    for raw_line in text[4:end].splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.+)$", line)
        if match:
            key, value = match.groups()
            values[key] = value.strip().strip('"\'')

    for key in ("name", "description"):
        if not values.get(key):
            fail(f"SKILL.md frontmatter requires non-empty {key}")

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", values["name"]):
        fail("SKILL.md name must use lowercase letters, digits, and hyphens")

    return values


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_required_paths() -> None:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).is_file()]
    if missing:
        fail("Missing required files: " + ", ".join(missing))


def validate_utf8_text() -> None:
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json", ".yaml", ".yml", ".py"}:
            try:
                path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                fail(f"File is not valid UTF-8: {path.relative_to(ROOT)} ({exc})")


def validate_source_manifest(skip_hashes: bool = False) -> int:
    manifest = load_json(ROOT / "references/source-manifest.json")
    if manifest.get("version") != 1:
        fail("references/source-manifest.json version must be 1")

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        fail("references/source-manifest.json must contain a non-empty files list")

    seen: set[str] = set()
    for entry in files:
        if not isinstance(entry, dict):
            fail("Each source manifest entry must be an object")
        rel = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(rel, str) or not rel:
            fail("Each source manifest entry requires path")
        if rel in seen:
            fail(f"Duplicate source manifest path: {rel}")
        seen.add(rel)
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            fail(f"Invalid sha256 for {rel}")
        path = ROOT / rel
        if not path.is_file():
            if skip_hashes:
                continue
            fail(f"Source manifest path does not exist: {rel}")
        if skip_hashes:
            continue
        actual = sha256(path)
        if actual != expected:
            fail(f"Source hash mismatch for {rel}: expected {expected}, got {actual}")

    return len(files)


def require_sections(path: Path, sections: Iterable[str]) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [section for section in sections if section not in text]
    if missing:
        fail(f"{path.relative_to(ROOT)} missing sections: {', '.join(missing)}")


def validate_guides() -> tuple[int, int]:
    for rel in SUBJECT_PATHS:
        require_sections(ROOT / rel, SUBJECT_SECTIONS)
    for rel in CONCLUSION_PATHS:
        require_sections(ROOT / rel, CONCLUSION_SECTIONS)
    require_sections(ROOT / "references/core/06-文章成稿与压缩.md", WRITING_SECTIONS)
    return len(SUBJECT_PATHS), len(CONCLUSION_PATHS)


def validate_runtime_links() -> None:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    referenced = set(re.findall(r"`([^`]+\.(?:md|json|txt))`", text))
    missing = sorted(
        rel for rel in referenced
        if rel.startswith(("references/", "evals/", "scripts/")) and not (ROOT / rel).exists()
    )
    if missing:
        fail("SKILL.md references missing paths: " + ", ".join(missing))


def validate_string_list(case_id: str, field: str, value: Any) -> None:
    if not isinstance(value, list) or not value or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        fail(f"Regression case {case_id} field {field} must be a non-empty string list")


def validate_regression_cases() -> tuple[int, set[str]]:
    data = load_json(ROOT / "evals/regression-cases.json")
    if data.get("version") != 2:
        fail("evals/regression-cases.json version must be 2")

    rubric = data.get("rubric")
    if not isinstance(rubric, str) or not (ROOT / rubric).is_file():
        fail("regression-cases.json rubric must reference an existing file")

    global_dims = data.get("rubric_dimensions")
    if not isinstance(global_dims, list) or set(global_dims) != EXPECTED_RUBRIC_DIMENSIONS:
        fail("rubric_dimensions must contain the expected ten dimensions exactly once")
    if len(global_dims) != len(set(global_dims)):
        fail("rubric_dimensions contains duplicates")

    invariants = data.get("global_invariants")
    if not isinstance(invariants, list) or len(invariants) < 10 or not all(
        isinstance(item, str) and item.strip() for item in invariants
    ):
        fail("global_invariants must contain at least ten non-empty strings")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < 20:
        fail("regression-cases.json must contain at least twenty cases")

    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            fail("Each regression case must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", case_id):
            fail(f"Invalid regression case id: {case_id!r}")
        if case_id in ids:
            fail(f"Duplicate regression case id: {case_id}")
        ids.add(case_id)

        if not isinstance(case.get("type"), str) or not case["type"].strip():
            fail(f"Regression case {case_id} requires a type")
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            fail(f"Regression case {case_id} requires a prompt")

        for field in ("subjects", "focus", "rubric_dimensions", "must", "must_not"):
            validate_string_list(case_id, field, case.get(field))

        unknown_dims = set(case["rubric_dimensions"]) - EXPECTED_RUBRIC_DIMENSIONS
        if unknown_dims:
            fail(f"Regression case {case_id} has unknown rubric dimensions: {sorted(unknown_dims)}")

        reference = case.get("reference")
        if reference is not None:
            if not isinstance(reference, str) or not (ROOT / reference).is_file():
                fail(f"Regression case {case_id} references missing file: {reference}")

    required_new_cases = {
        "human-anger",
        "human-procrastination",
        "leader-project-allocation",
        "team-core-projects",
        "pork-cycle",
        "ai-money",
        "pure-definition-prime",
        "agent-what-routing",
        "ant-trail-migration",
        "job-offer-choice",
        "false-premise-interest-only",
        "mixed-growth-stagnation",
    }
    missing_new = sorted(required_new_cases - ids)
    if missing_new:
        fail("Missing required v2 regression cases: " + ", ".join(missing_new))

    return len(cases), ids


def validate_writing_regression_cases(reasoning_ids: set[str]) -> tuple[int, set[str]]:
    data = load_json(ROOT / "evals/writing-regression-cases.json")
    if data.get("version") != 1:
        fail("evals/writing-regression-cases.json version must be 1")

    for field in ("rubric", "reasoning_rubric"):
        rel = data.get(field)
        if not isinstance(rel, str) or not (ROOT / rel).is_file():
            fail(f"writing-regression-cases.json {field} must reference an existing file")

    global_dims = data.get("rubric_dimensions")
    if not isinstance(global_dims, list) or set(global_dims) != EXPECTED_WRITING_RUBRIC_DIMENSIONS:
        fail("writing rubric_dimensions must contain the expected six dimensions exactly once")
    if len(global_dims) != len(set(global_dims)):
        fail("writing rubric_dimensions contains duplicates")

    invariants = data.get("global_invariants")
    if not isinstance(invariants, list) or len(invariants) < 8 or not all(
        isinstance(item, str) and item.strip() for item in invariants
    ):
        fail("writing global_invariants must contain at least eight non-empty strings")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < 5:
        fail("writing-regression-cases.json must contain at least five cases")

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

        reasoning_case_id = case.get("reasoning_case_id")
        if not isinstance(reasoning_case_id, str) or reasoning_case_id not in reasoning_ids:
            fail(
                f"Writing regression case {case_id} references unknown reasoning case: "
                f"{reasoning_case_id!r}"
            )

        for field in ("type", "prompt", "output_mode"):
            value = case.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"Writing regression case {case_id} requires {field}")

        for field in ("focus", "rubric_dimensions", "must", "must_not"):
            validate_string_list(case_id, field, case.get(field))

        unknown_dims = set(case["rubric_dimensions"]) - EXPECTED_WRITING_RUBRIC_DIMENSIONS
        if unknown_dims:
            fail(f"Writing regression case {case_id} has unknown dimensions: {sorted(unknown_dims)}")

    required_cases = {
        "agent-article-density",
        "fiber-article-density",
        "harness-detailed-without-repetition",
        "human-anger-plain-article",
        "job-offer-decision-memo",
        "api-growth-report-density",
        "agent-article-handoff-and-reader-contract",
    }
    missing = sorted(required_cases - ids)
    if missing:
        fail("Missing required writing regression cases: " + ", ".join(missing))

    return len(cases), ids


def validate_score_template(
    rel: str,
    known_case_ids: set[str],
    expected_dimensions: set[str],
) -> None:
    data = load_json(ROOT / rel)
    if data.get("version") != 1:
        fail(f"{rel} version must be 1")
    results = data.get("results")
    if not isinstance(results, list) or not results:
        fail(f"{rel} requires a non-empty results list")
    for item in results:
        if not isinstance(item, dict):
            fail(f"{rel} results must contain objects")
        case_id = item.get("id")
        if case_id not in known_case_ids:
            fail(f"{rel} references unknown case id: {case_id!r}")
        scores = item.get("scores")
        if not isinstance(scores, dict) or set(scores) != expected_dimensions:
            fail(f"{rel} score dimensions do not match expected dimensions")
        if not all(isinstance(value, int) and 0 <= value <= 2 for value in scores.values()):
            fail(f"{rel} scores must be integers from 0 to 2")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-source-hashes",
        action="store_true",
        help="Skip source file existence/hash checks for partial local staging only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        validate_required_paths()
        metadata = parse_skill_frontmatter(ROOT / "SKILL.md")
        validate_utf8_text()
        source_count = validate_source_manifest(skip_hashes=args.skip_source_hashes)
        subject_count, conclusion_count = validate_guides()
        validate_runtime_links()
        reasoning_case_count, reasoning_ids = validate_regression_cases()
        writing_case_count, writing_ids = validate_writing_regression_cases(reasoning_ids)
        validate_score_template(
            "evals/score-template.json",
            reasoning_ids,
            EXPECTED_RUBRIC_DIMENSIONS,
        )
        validate_score_template(
            "evals/writing-score-template.json",
            writing_ids,
            EXPECTED_WRITING_RUBRIC_DIMENSIONS,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK: skill={metadata['name']}")
    print(f"OK: verified {source_count} source-controlled reference entries")
    print(f"OK: verified {subject_count} subject guides")
    print(f"OK: verified {conclusion_count} conclusion cards")
    print(f"OK: verified {reasoning_case_count} reasoning regression cases")
    print(f"OK: verified {writing_case_count} writing regression cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
