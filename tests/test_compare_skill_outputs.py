"""Synthetic protocol tests; these do not run or evaluate a language model."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import compare_skill_outputs as c


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.before, self.after, self.run = self.root / "before.json", self.root / "after.json", self.root / "run"
        for path, letter in ((self.before, "a"), (self.after, "b")):
            c.write_json(path, {"revision": letter * 40, "files": {p: f"synthetic policy {letter}" for p in c.WRITING}})

    def prepare(self, repeats=1):
        c.prepare(self.before, self.after, "tool-heading", self.run, repeats)
        return c.read_json(self.run / "private/manifest.json")

    def outputs(self, origin="synthetic", repeats=1):
        manifest = self.prepare(repeats)
        for job in manifest["jobs"]:
            out = self.run / "outputs"
            out.mkdir(exist_ok=True)
            (out / f"{job['id']}.md").write_text(f"实际操作由工具执行；执行结果供下一轮使用。样本 {job['id']}。", encoding="utf-8")
            c.write_json(out / f"{job['id']}.json", {
                "actor": "test fixture", "model": "synthetic-model", "settings": {"mode": "test"},
                "origin": origin, "context_id": job["id"], "run_id": job["id"], "isolation": "fresh",
                "packet_sha256": job["packet_sha256"],
            })
        return manifest

    def judgments(self, origin="synthetic", saw_mapping=False):
        b = c.read_json(self.run / "private/blind.json")
        for r in b["reviews"]:
            packet = c.read_json(self.run / "review" / f"{r['id']}.json")
            c.write_json(self.run / "judgments" / f"{r['id']}.json", {
                "packet_sha256": r["packet_sha256"], "saw_mapping": saw_mapping,
                "verdict": "tie", "reason": "Synthetic fixture for transport and validation only.",
                "evidence": {k: v[:8] for k, v in packet["candidates"].items()},
                "answers": ["synthetic answer" for _ in packet["criteria"]["questions"]],
                "metadata": {"actor": "test fixture", "model": "synthetic-judge", "settings": {},
                             "origin": origin, "context_id": r["id"], "run_id": r["id"], "isolation": "fresh"},
            })

    def replace_json(self, path, transform):
        value = c.read_json(path)
        transform(value)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def test_case_inputs_exclude_review_fields(self):
        suite = c.read_json(c.SUITE)
        self.assertGreaterEqual(len(suite["cases"]), 12)
        stages = set()
        for case in suite["cases"]:
            loaded = c.get_case(case["id"])
            stages.add(loaded["stage"])
            self.assertEqual(set(loaded["input"]), {"request", "material"})
            self.assertNotIn("evaluation", loaded["input"])
        self.assertEqual(stages, {"analysis", "writing"})

    def test_preparation_is_not_model_evaluation(self):
        manifest = self.prepare(2)
        self.assertEqual(len(manifest["jobs"]), 4)
        self.assertEqual(c.report(self.run)["completed"], 0)
        for job in manifest["jobs"]:
            packet = c.read_json(self.run / "generation" / f"{job['id']}.json")
            self.assertEqual(set(packet), {"job_id", "instruction", "stage", "policy", "task"})
            self.assertEqual(packet["task"], manifest["case"]["input"])

    def test_blind_packets_hide_mapping_and_generator_metadata(self):
        self.outputs()
        c.blind(self.run)
        packet = c.read_json(next((self.run / "review").glob("*.json")))
        self.assertEqual(set(packet), {"review_id", "task", "criteria", "instruction", "candidates"})
        self.assertEqual(set(packet["candidates"]), {"A", "B"})
        self.assertEqual(c.report(self.run)["status"], "awaiting_judgments")

    def test_synthetic_pipeline_cannot_claim_independent_model_evaluation(self):
        self.outputs(repeats=2)
        c.blind(self.run)
        self.judgments()
        report = c.report(self.run)
        self.assertEqual(report["completed"], 2)
        self.assertEqual(report["preferences"]["tie"], 2)
        self.assertFalse(report["declared_independent_comparison_complete"])

    def test_external_isolation_is_only_an_operator_declaration(self):
        self.outputs(origin="external")
        c.blind(self.run)
        self.judgments(origin="external")
        report = c.report(self.run)
        self.assertEqual(report["evidence_level"], "operator-declared-isolated-blind")
        self.assertIn("operator declarations", report["limitation"])

    def test_judge_who_saw_mapping_is_not_blind(self):
        self.outputs(origin="external")
        c.blind(self.run)
        self.judgments(origin="external", saw_mapping=True)
        self.assertFalse(c.report(self.run)["declared_independent_comparison_complete"])

    def test_shared_context_or_different_settings_is_not_controlled(self):
        manifest = self.outputs(origin="external")
        jobs = manifest["jobs"]
        path = self.run / "outputs" / f"{jobs[1]['id']}.json"
        self.replace_json(path, lambda m: m.update(context_id=jobs[0]["id"], settings={"different": True}))
        c.blind(self.run)
        self.judgments(origin="external")
        report = c.report(self.run)
        self.assertFalse(report["same_model_and_settings"])
        self.assertFalse(report["declared_independent_comparison_complete"])

    def test_missing_outputs_does_not_create_blind_records(self):
        self.prepare()
        with self.assertRaises(OSError):
            c.blind(self.run)
        self.assertFalse((self.run / "review").exists())

    def test_policy_file_set_mismatch_is_rejected(self):
        self.replace_json(self.after, lambda v: v["files"].pop(c.WRITING[0]))
        with self.assertRaises(ValueError):
            self.prepare()

    def test_missing_runtime_material_is_rejected(self):
        for path in (self.before, self.after):
            self.replace_json(path, lambda v: v["files"].pop(c.WRITING[0]))
        with self.assertRaises(ValueError):
            self.prepare()

    def test_reviewer_files_and_mutable_revisions_are_rejected(self):
        for mutation in (lambda v: v["files"].update({"evals/answers.md": "answer"}), lambda v: v.update(revision="main")):
            data = c.read_json(self.before)
            mutation(data)
            path = self.root / "bad.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                c.bundle(path)

    def test_existing_run_is_not_overwritten(self):
        self.prepare()
        with self.assertRaises(FileExistsError):
            self.prepare()

    def test_generation_packet_mutation_is_rejected(self):
        manifest = self.outputs()
        path = self.run / "generation" / f"{manifest['jobs'][0]['id']}.json"
        path.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "packet changed"):
            c.blind(self.run)

    def test_output_mutation_after_blinding_is_rejected(self):
        manifest = self.outputs()
        c.blind(self.run)
        (self.run / "outputs" / f"{manifest['jobs'][0]['id']}.md").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed after blinding"):
            c.report(self.run)

    def test_manifest_mutation_after_blinding_is_rejected(self):
        self.outputs()
        c.blind(self.run)
        self.replace_json(self.run / "private/manifest.json", lambda m: m["revisions"].update(after="c" * 40))
        with self.assertRaisesRegex(ValueError, "Manifest changed"):
            c.report(self.run)

    def test_review_requires_actual_output_evidence(self):
        self.outputs()
        c.blind(self.run)
        self.judgments()
        path = next((self.run / "judgments").glob("*.json"))
        self.replace_json(path, lambda j: j["evidence"].update(A="This never appeared in the actual candidate."))
        with self.assertRaisesRegex(ValueError, "Evidence"):
            c.report(self.run)

    def test_unknown_case_and_empty_output_fail(self):
        with self.assertRaises(ValueError):
            c.get_case("missing-case")
        manifest = self.outputs()
        (self.run / "outputs" / f"{manifest['jobs'][0]['id']}.md").write_text("\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Empty"):
            c.blind(self.run)


if __name__ == "__main__":
    unittest.main()
