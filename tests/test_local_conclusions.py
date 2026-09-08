"""Test fixture coverage and generation-input isolation, not prose quality."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_writing as writing


STATEMENT_CASES = {
    "screenshot-completion-statement",
    "screenshot-operation-conclusion",
    "screenshot-feedback-conclusion",
    "screenshot-enforcement-difference",
    "screenshot-verification-boundary",
    "screenshot-stop-classification",
    "transfer-concrete-comparison",
    "transfer-concrete-duties",
    "statement-format-invariance",
    "statement-structure-no-bold",
}
STYLE_CASES = {
    "style-drop-fillers",
    "style-unpack-label",
    "style-direct-status",
    "style-keep-real-comparison",
    "style-keep-terms-and-quote",
    "style-no-invented-action",
    "style-no-ceremony-article",
    "style-preserve-negative-boundary",
}


class LocalConclusionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = ROOT / "evals/local-conclusion-regression-cases.json"
        cls.data = json.loads(path.read_text(encoding="utf-8"))

    def test_old_and_new_case_coverage(self) -> None:
        count = writing.validate_local_cases(self.data)
        ids = {case["id"] for case in self.data["cases"]}
        self.assertTrue(writing.REQUIRED_LOCAL_CASES <= ids)
        self.assertTrue(STATEMENT_CASES <= ids, STATEMENT_CASES - ids)
        self.assertTrue(STYLE_CASES <= ids, STYLE_CASES - ids)
        self.assertGreaterEqual(count, 32)

    def test_generation_input_excludes_review_fields(self) -> None:
        for case in self.data["cases"]:
            with self.subTest(case=case["id"]):
                payload = writing.local_conclusion_input(self.data, case["id"])
                self.assertEqual(set(payload), {"facts", "request"})
                self.assertEqual(payload["request"], case["input"]["request"])
                self.assertEqual(
                    payload["facts"],
                    self.data["materials"][case["input"]["material"]],
                )
                self.assertIsNot(
                    payload["facts"],
                    self.data["materials"][case["input"]["material"]],
                )

    def test_payload_mutation_does_not_change_fixture(self) -> None:
        before = copy.deepcopy(self.data)
        payload = writing.local_conclusion_input(
            self.data, "screenshot-operation-conclusion"
        )
        payload["facts"].append("This belongs only to the caller.")
        payload["request"] = "Changed request"
        self.assertEqual(self.data, before)

    def test_unknown_case_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown local conclusion case"):
            writing.local_conclusion_input(self.data, "missing-case")

    def test_malformed_fixtures_are_rejected(self) -> None:
        mutations = {
            "duplicate_case": lambda d: d["cases"].append(copy.deepcopy(d["cases"][0])),
            "unknown_material": lambda d: d["cases"][-1]["input"].update(material="missing"),
            "review_in_input": lambda d: d["cases"][-1]["input"].update(evaluation={}),
            "invalid_role": lambda d: d["cases"][-1]["evaluation"].update(role="invalid"),
            "empty_expectations": lambda d: d["cases"][-1]["evaluation"].update(must=[]),
            "missing_original_case": lambda d: d["cases"].pop(0),
        }
        for name, mutate in mutations.items():
            with self.subTest(mutation=name):
                data = copy.deepcopy(self.data)
                mutate(data)
                with self.assertRaises(ValueError):
                    writing.validate_local_cases(data)


if __name__ == "__main__":
    unittest.main()
