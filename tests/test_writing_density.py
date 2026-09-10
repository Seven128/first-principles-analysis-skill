"""Regression tests for fixture validation and generation-input isolation."""

import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_writing_density.py"
spec = importlib.util.spec_from_file_location("writing_density", SCRIPT)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class WritingDensityTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(validator.CASES_PATH.read_text(encoding="utf-8"))

    def case(self, case_id="example-before-abstraction"):
        return next(case for case in self.data["cases"] if case["id"] == case_id)

    def test_current_fixture(self):
        self.assertEqual(validator.validate_cases_and_pairs(self.data), (14, 13))

    def test_runtime_rules_and_entry_consistency(self):
        validator.validate_rule_file()
        validator.validate_skill_link()

    def test_generation_input_allowlist(self):
        case = self.case()
        case["evaluation_secret"] = "NEVER_SEND_TO_GENERATOR"
        case["must"].append("NEVER_SEND_TO_GENERATOR")
        result = validator.writing_density_input(self.data, case["id"])
        self.assertEqual(set(result), {"facts", "request"})
        self.assertEqual(result["facts"], self.data["materials"][case["material"]])
        self.assertEqual(result["request"], case["prompt"])
        self.assertNotIn("NEVER_SEND_TO_GENERATOR", json.dumps(result))

    def test_generation_does_not_mutate_facts(self):
        original = copy.deepcopy(self.data)
        result = validator.writing_density_input(self.data, self.case()["id"])
        result["facts"].append("local-only")
        self.assertEqual(self.data, original)

    def test_unknown_case(self):
        with self.assertRaisesRegex(ValueError, "Unknown writing density case"):
            validator.writing_density_input(self.data, "unknown-case")

    def test_freeform_case_has_no_invented_facts(self):
        result = validator.writing_density_input(self.data, "agent-article-purpose-and-density")
        self.assertEqual(result["facts"], [])

    def test_required_case_cannot_be_renamed(self):
        self.case()["id"] = "unrelated-case"
        with self.assertRaisesRegex(ValueError, "Missing required"):
            validator.validate_cases_and_pairs(self.data)

    def test_required_material_cannot_be_removed(self):
        self.case().pop("material")
        with self.assertRaisesRegex(ValueError, "unknown material"):
            validator.validate_cases_and_pairs(self.data)

    def test_invalid_material_reference(self):
        self.case()["material"] = "not-present"
        with self.assertRaisesRegex(ValueError, "unknown material"):
            validator.validate_cases_and_pairs(self.data)

    def test_invalid_fixture_shapes(self):
        mutations = [
            ("version", True),
            ("materials", []),
            ("rubric_dimensions", ["reader_focus"]),
            ("global_invariants", []),
            ("generation_instructions", []),
        ]
        for field, value in mutations:
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data[field] = value
                with self.assertRaises(ValueError):
                    validator.validate_cases_and_pairs(data)

    def test_blank_material_fact(self):
        self.data["materials"][self.case()["material"]] = [" "]
        with self.assertRaisesRegex(ValueError, "non-empty strings"):
            validator.validate_cases_and_pairs(self.data)

    def test_duplicate_ids(self):
        for field in ("cases", "style_pairs"):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data[field].append(copy.deepcopy(data[field][0]))
                with self.assertRaisesRegex(ValueError, "Duplicate"):
                    validator.validate_cases_and_pairs(data)

    def test_required_pair_cannot_be_renamed(self):
        self.data["style_pairs"][-1]["id"] = "unrelated-pair"
        with self.assertRaisesRegex(ValueError, "Missing required"):
            validator.validate_cases_and_pairs(self.data)

    def test_sufficient_sentence_can_remain_unchanged(self):
        pair = next(p for p in self.data["style_pairs"] if p["id"] == "keep-sufficient-no-example")
        self.assertEqual(pair["before"], pair["after"])
        validator.validate_cases_and_pairs(self.data)

    def test_cli_only_emits_generation_input(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--case", "example-before-abstraction"],
            capture_output=True, text=True, check=True, timeout=10,
        )
        self.assertEqual(set(json.loads(result.stdout)), {"facts", "request"})
        self.assertEqual(result.stderr, "")

    def test_cli_unknown_case_exits_nonzero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--case", "unknown-case"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unknown writing density case", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
