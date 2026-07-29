#!/usr/bin/env python3
"""Validate the standalone first-principles-analysis skill repository."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "SKILL.md",
    "README.md",
    "AGENTS.md",
    "agents/openai.yaml",
    "references/第一性原理分析逻辑.md",
    "references/第一性原理分析提示词.md",
    "references/source-manifest.json",
    "evals/README.md",
    "evals/regression-cases.json",
]


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


def validate_source_manifest() -> int:
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
            fail(f"Source manifest path does not exist: {rel}")
        actual = sha256(path)
        if actual != expected:
            fail(f"Source hash mismatch for {rel}: expected {expected}, got {actual}")

    return len(files)


def validate_regression_cases() -> int:
    data = load_json(ROOT / "evals/regression-cases.json")
    if data.get("version") != 1:
        fail("evals/regression-cases.json version must be 1")

    invariants = data.get("global_invariants")
    if not isinstance(invariants, list) or len(invariants) < 5 or not all(isinstance(item, str) and item.strip() for item in invariants):
        fail("global_invariants must contain at least five non-empty strings")

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        fail("regression-cases.json must contain a non-empty cases list")

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
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            fail(f"Regression case {case_id} requires a prompt")
        for field in ("focus", "must", "must_not"):
            value = case.get(field)
            if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
                fail(f"Regression case {case_id} field {field} must be a list of non-empty strings")
        reference = case.get("reference")
        if reference is not None:
            if not isinstance(reference, str) or not (ROOT / reference).is_file():
                fail(f"Regression case {case_id} references missing file: {reference}")

    return len(cases)


def main() -> int:
    try:
        validate_required_paths()
        metadata = parse_skill_frontmatter(ROOT / "SKILL.md")
        validate_utf8_text()
        source_count = validate_source_manifest()
        case_count = validate_regression_cases()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK: skill={metadata['name']}")
    print(f"OK: verified {source_count} source-controlled reference files")
    print(f"OK: verified {case_count} regression cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
