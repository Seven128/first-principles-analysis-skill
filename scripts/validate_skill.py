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
    "references/source-manifest.json",
    "references/examples/旧案例使用说明.md",
    "evals/README.md",
    "evals/rubric.md",
    "evals/regression-cases.json",
    "scripts/lint_language.py",
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


def validate_regression_cases() -> int:
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
            value = case.get(field)
            if not isinstance(value, list) or not value or not all(
                isinstance(item, str) and item.strip() for item in value
            ):
                fail(f"Regression case {case_id} field {field} must be a non-empty string list")

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

    return len(cases)


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
        case_count = validate_regression_cases()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK: skill={metadata['name']}")
    print(f"OK: verified {source_count} source-controlled reference entries")
    print(f"OK: verified {subject_count} subject guides")
    print(f"OK: verified {conclusion_count} conclusion cards")
    print(f"OK: verified {case_count} regression cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
