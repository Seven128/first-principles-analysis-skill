#!/usr/bin/env python3
"""Validate and summarize manually scored model-output regression results."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals/regression-cases.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("scores", type=Path, help="JSON mapping case id to dimension scores and notes")
    parser.add_argument("--minimum", type=int, default=16)
    args = parser.parse_args()

    cases_data = load(CASES_PATH)
    known = {case["id"]: case for case in cases_data["cases"]}
    scores_data = load(args.scores)
    results = scores_data.get("results")
    if not isinstance(results, list):
        print("ERROR: score file requires a results list", file=sys.stderr)
        return 1

    failed = 0
    seen: set[str] = set()
    for item in results:
        case_id = item.get("id")
        if case_id not in known:
            print(f"ERROR: unknown case id: {case_id}", file=sys.stderr)
            return 1
        if case_id in seen:
            print(f"ERROR: duplicate case id: {case_id}", file=sys.stderr)
            return 1
        seen.add(case_id)

        required_dims = known[case_id]["rubric_dimensions"]
        scores = item.get("scores")
        if not isinstance(scores, dict):
            print(f"ERROR: {case_id} requires scores object", file=sys.stderr)
            return 1
        if set(scores) != set(required_dims):
            print(f"ERROR: {case_id} score dimensions do not match case rubric", file=sys.stderr)
            return 1
        if not all(isinstance(value, int) and 0 <= value <= 2 for value in scores.values()):
            print(f"ERROR: {case_id} scores must be integers from 0 to 2", file=sys.stderr)
            return 1

        total = sum(scores.values())
        maximum = 2 * len(required_dims)
        severe = bool(item.get("severe_error", False))
        threshold = min(args.minimum, maximum)
        passed = total >= threshold and not severe
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {case_id} {total}/{maximum}")
        if not passed:
            failed += 1

    print(f"Scored {len(results)} cases; failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
