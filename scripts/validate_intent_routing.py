#!/usr/bin/env python3
"""Validate the focused complex-input and intent-routing regression suite."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals/intent-routing-regression-cases.json"

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

REQUIRED_CASE_IDS = {
    "existing-system-how-made",
    "user-builds-system-how-to",
    "mixed-explain-then-build",
    "many-questions-one-problem-tree",
    "multiple-independent-questions",
    "surface-what-goal-solving",
    "current-intent-overrides-history",
    "ambiguous-how-minimal-clarification",
    "dynamic-reroute-with-new-evidence",
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


def require_string_list(case_id: str, field: str, value: Any) -> None:
    if not isinstance(value, list) or not value:
        fail(f"Case {case_id} field {field} must be a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        fail(f"Case {case_id} field {field} must contain non-empty strings")


def main() -> int:
    data = load_json(CASES_PATH)

    if data.get("version") != 1:
        fail("intent-routing-regression-cases.json version must be 1")

    purpose = data.get("purpose")
    if not isinstance(purpose, str) or not purpose.strip():
        fail("intent-routing-regression-cases.json requires purpose")

    rubric = data.get("rubric")
    if not isinstance(rubric, str) or not (ROOT / rubric).is_file():
        fail("intent-routing-regression-cases.json rubric must reference an existing file")

    dimensions = data.get("rubric_dimensions")
    require_string_list("global", "rubric_dimensions", dimensions)
    unknown_global_dimensions = set(dimensions) - EXPECTED_DIMENSIONS
    if unknown_global_dimensions:
        fail(f"Unknown global rubric dimensions: {sorted(unknown_global_dimensions)}")
    if len(dimensions) != len(set(dimensions)):
        fail("Global rubric_dimensions contains duplicates")

    invariants = data.get("global_invariants")
    require_string_list("global", "global_invariants", invariants)
    if len(invariants) < 8:
        fail("global_invariants must contain at least eight items")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < 9:
        fail("intent-routing-regression-cases.json must contain at least nine cases")

    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            fail("Each intent-routing case must be an object")

        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", case_id):
            fail(f"Invalid intent-routing case id: {case_id!r}")
        if case_id in ids:
            fail(f"Duplicate intent-routing case id: {case_id}")
        ids.add(case_id)

        for field in ("type", "prompt"):
            value = case.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"Case {case_id} requires {field}")

        for field in ("focus", "rubric_dimensions", "must", "must_not"):
            require_string_list(case_id, field, case.get(field))

        unknown_dimensions = set(case["rubric_dimensions"]) - EXPECTED_DIMENSIONS
        if unknown_dimensions:
            fail(f"Case {case_id} has unknown rubric dimensions: {sorted(unknown_dimensions)}")
        if len(case["rubric_dimensions"]) != len(set(case["rubric_dimensions"])):
            fail(f"Case {case_id} rubric_dimensions contains duplicates")

    missing = sorted(REQUIRED_CASE_IDS - ids)
    if missing:
        fail("Missing required intent-routing cases: " + ", ".join(missing))

    print(
        "Validated intent routing suite: "
        f"{len(cases)} cases, {len(invariants)} global invariants"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
