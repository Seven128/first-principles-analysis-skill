#!/usr/bin/env python3
"""Prepare isolated generation packets, blind real outputs, and audit comparisons.

No model is called. Context isolation is reported by the operator, not proved by
this program. Run only when iterating the skill, never as a writing prerequisite.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import secrets
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evals/directness/cases.json"
WRITING = [
    "references/core/05-输出与表达规则.md", "references/core/06-文章成稿与压缩.md",
    *[f"references/writing/{name}.md" for name in (
        "00-分析定稿与文章契约", "01-写作规则卡", "02-文章任务适配", "03-成文检查",
        "04-信息密度、段落与例子控制", "05-结构节点、信息层级与标题")],
]
ANALYSIS = ["SKILL.md", *WRITING, *[f"references/core/{name}.md" for name in (
    "00-第一性原理核心原则", "01-问题识别与分类", "01a-目的、现状、问题与方案",
    "02-为什么类问题推理", "03-怎么做类问题推理", "04-客观性与证据规则",
    "04a-关键推理节点反向校验")]]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def get_case(case_id: str, suite: Path = SUITE) -> dict:
    cases = read_json(suite)["cases"]
    require(len({c["id"] for c in cases}) == len(cases), "Duplicate case IDs")
    matches = [c for c in cases if c["id"] == case_id]
    require(len(matches) == 1, f"Unknown case: {case_id}")
    case = matches[0]
    require(case["stage"] in {"analysis", "writing"}, "Invalid case stage")
    require(set(case["input"]) == {"request", "material"}, "Unexpected generation fields")
    require(bool(case["input"]["request"].strip()) and bool(case["input"]["material"]), "Empty input")
    for field in ("must_preserve", "must_not", "questions"):
        require(bool(case["evaluation"][field]), f"Missing review field: {field}")
    return case


def bundle(path: Path) -> dict:
    value = read_json(path)
    require(isinstance(value.get("revision"), str) and bool(re.fullmatch(r"[0-9a-f]{40}", value["revision"])), "Use a resolved 40-character commit SHA")
    files = value.get("files")
    require(isinstance(files, dict) and bool(files), "Missing policy files")
    for name, text in files.items():
        safe = name == "SKILL.md" or name.startswith(("references/core/", "references/writing/", "references/subjects/"))
        require(safe and ".." not in Path(name).parts and name.endswith(".md"), "Non-runtime policy path")
        require(isinstance(text, str) and bool(text.strip()), "Empty policy text")
    return value


def prepare(before: Path, after: Path, case_id: str, out: Path, repeats: int = 1, suite: Path = SUITE) -> None:
    require(1 <= repeats <= 20, "repeats must be between 1 and 20")
    case = get_case(case_id, suite)
    versions = {"before": bundle(before), "after": bundle(after)}
    require(set(versions["before"]["files"]) == set(versions["after"]["files"]), "Policy file sets differ")
    require(versions["before"]["revision"] != versions["after"]["revision"], "Use two different revisions")
    required = set(ANALYSIS if case["stage"] == "analysis" else WRITING) | set(case.get("guides", []))
    require(required <= set(versions["before"]["files"]), "Missing runtime authority files")
    out.mkdir(parents=True, exist_ok=False)
    jobs = []
    for trial in range(repeats):
        for variant, version in versions.items():
            job_id = secrets.token_hex(8)
            packet = {
                "job_id": job_id,
                "instruction": "在独立上下文执行本任务。只使用所附运行规则与固定材料，不读取其他输出、评审标准、版本对照或历史对话。材料不足时保留未知。交付要求见 task；不输出逐步思考记录。",
                "stage": case["stage"],
                "policy": version["files"],
                "task": case["input"],
            }
            target = out / "generation" / f"{job_id}.json"
            write_json(target, packet)
            jobs.append({"id": job_id, "variant": variant, "trial": trial, "packet_sha256": digest(target.read_bytes())})
    write_json(out / "private" / "manifest.json", {
        "case": case, "revisions": {k: v["revision"] for k, v in versions.items()},
        "bundle_sha256": {"before": digest(before.read_bytes()), "after": digest(after.read_bytes())},
        "jobs": jobs,
    })


def metadata(value: dict) -> None:
    require(isinstance(value, dict), "Metadata must be an object")
    for key in ("actor", "model", "context_id", "run_id"):
        require(isinstance(value.get(key), str) and bool(value[key].strip()), f"Missing metadata: {key}")
    require(isinstance(value.get("settings"), dict), "settings must be an object; record unknown settings explicitly")
    require(value.get("isolation") in {"fresh", "shared", "unknown"}, "Invalid isolation declaration")
    require(value.get("origin") in {"external", "self", "synthetic"}, "Declare output origin")


def blind(run: Path) -> None:
    manifest = read_json(run / "private" / "manifest.json")
    require(not (run / "review").exists(), "Already blinded; use a new run for changed outputs")
    outputs, bindings = {}, {}
    # Validate all jobs before creating any review packets.
    for job in manifest["jobs"]:
        jid = job["id"]
        packet_path = run / "generation" / f"{jid}.json"
        require(digest(packet_path.read_bytes()) == job["packet_sha256"], "Generation packet changed")
        text_path = run / "outputs" / f"{jid}.md"
        meta_path = run / "outputs" / f"{jid}.json"
        text, meta = text_path.read_text(encoding="utf-8"), read_json(meta_path)
        require(bool(text.strip()), "Empty model output")
        metadata(meta)
        require(meta.get("packet_sha256") == job["packet_sha256"], "Output uses a different generation packet")
        outputs[jid] = {"text": text, "metadata": meta}
        bindings[jid] = {"text": digest(text_path.read_bytes()), "metadata": digest(meta_path.read_bytes())}
    reviews = []
    for trial in sorted({j["trial"] for j in manifest["jobs"]}):
        pair = [j for j in manifest["jobs"] if j["trial"] == trial]
        secrets.SystemRandom().shuffle(pair)
        mapping = dict(zip(("A", "B"), (j["id"] for j in pair)))
        review_id = secrets.token_hex(8)
        packet = {
            "review_id": review_id, "task": manifest["case"]["input"],
            "criteria": manifest["case"]["evaluation"],
            "instruction": "先按材料检查事实、因果、范围与必须覆盖项，再比较问题层级、标题与正文的直接性。准确名称标题配充分正文可以通过；不能只按字数或个人文风选胜者。先回答 questions，再给判定与原文依据。不要猜测版本。",
            "candidates": {label: outputs[jid]["text"] for label, jid in mapping.items()},
        }
        path = run / "review" / f"{review_id}.json"
        write_json(path, packet)
        reviews.append({"id": review_id, "mapping": mapping, "packet_sha256": digest(path.read_bytes())})
    write_json(run / "private" / "blind.json", {"bindings": bindings, "reviews": reviews, "manifest_sha256": digest((run / "private" / "manifest.json").read_bytes())})


def report(run: Path) -> dict:
    manifest = read_json(run / "private" / "manifest.json")
    if not (run / "private" / "blind.json").exists():
        return {"status": "awaiting_outputs_or_blinding", "completed": 0, "declared_independent_comparison_complete": False}
    blind_data = read_json(run / "private" / "blind.json")
    require(digest((run / "private" / "manifest.json").read_bytes()) == blind_data["manifest_sha256"], "Manifest changed after blinding")
    for job in manifest["jobs"]:
        require(digest((run / "generation" / f"{job['id']}.json").read_bytes()) == job["packet_sha256"], "Generation packet changed")
    contexts, signatures, metadata_values = [], [], []
    for jid, binding in blind_data["bindings"].items():
        for suffix, field in ((".md", "text"), (".json", "metadata")):
            require(digest((run / "outputs" / f"{jid}{suffix}").read_bytes()) == binding[field], "Output changed after blinding")
        meta = read_json(run / "outputs" / f"{jid}.json")
        metadata_values.append(meta)
        contexts.append(meta["context_id"])
        signatures.append(json.dumps({"model": meta["model"], "settings": meta["settings"]}, sort_keys=True))
    same_settings = len(set(signatures)) == 1
    isolated = len(set(contexts)) == len(contexts) and all(m["isolation"] == "fresh" and m["origin"] == "external" for m in metadata_values)
    isolated = isolated and len({m["run_id"] for m in metadata_values}) == len(metadata_values)
    counts = {"before": 0, "after": 0, "tie": 0, "neither": 0}
    completed, judge_contexts = 0, []
    jobs = {j["id"]: j for j in manifest["jobs"]}
    for review in blind_data["reviews"]:
        packet_path = run / "review" / f"{review['id']}.json"
        require(digest(packet_path.read_bytes()) == review["packet_sha256"], "Review packet changed")
        judgment_path = run / "judgments" / f"{review['id']}.json"
        if not judgment_path.exists():
            continue
        judgment = read_json(judgment_path)
        metadata(judgment["metadata"])
        require(judgment.get("packet_sha256") == review["packet_sha256"], "Judgment uses a different packet")
        require(type(judgment.get("saw_mapping")) is bool, "Declare saw_mapping explicitly")
        verdict = judgment.get("verdict")
        require(verdict in counts or verdict in {"A", "B"}, "Invalid verdict")
        require(verdict not in {"before", "after"}, "Judge must not use version names")
        require(isinstance(judgment.get("reason"), str) and bool(judgment["reason"].strip()), "Missing review reason")
        candidates = read_json(packet_path)["candidates"]
        for label in ("A", "B"):
            quote = judgment.get("evidence", {}).get(label)
            require(isinstance(quote, str) and bool(quote.strip()) and quote in candidates[label], "Evidence must quote each actual output")
        answers = judgment.get("answers")
        require(isinstance(answers, list) and len(answers) == len(manifest["case"]["evaluation"]["questions"]), "Missing comprehension answers")
        require(all(isinstance(a, str) and bool(a.strip()) for a in answers), "Empty comprehension answer")
        meta = judgment["metadata"]
        isolated = isolated and meta["isolation"] == "fresh" and meta["origin"] == "external" and not judgment["saw_mapping"] and meta["context_id"] not in contexts
        judge_contexts.append(meta["context_id"])
        key = jobs[review["mapping"][verdict]]["variant"] if verdict in {"A", "B"} else verdict
        counts[key] += 1
        completed += 1
    isolated = isolated and len(set(judge_contexts)) == len(judge_contexts)
    all_done = completed == len(blind_data["reviews"])
    return {
        "status": "completed" if all_done else "awaiting_judgments", "completed": completed,
        "planned": len(blind_data["reviews"]), "preferences": counts, "same_model_and_settings": same_settings,
        "evidence_level": "operator-declared-isolated-blind" if completed and isolated and same_settings else "non-independent-or-incomplete",
        "declared_independent_comparison_complete": bool(all_done and isolated and same_settings),
        "limitation": "Isolation and model settings are operator declarations. This report checks file bindings, not actual provider context isolation or semantic correctness. Preferences from these samples do not prove stable improvement.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("input")
    p.add_argument("case_id")
    p = commands.add_parser("prepare")
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--after", type=Path, required=True)
    p.add_argument("--case", dest="case_id", required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--repeats", type=int, default=1)
    for name in ("blind", "report"):
        p = commands.add_parser(name)
        p.add_argument("run", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "input":
            print(json.dumps(get_case(args.case_id)["input"], ensure_ascii=False, indent=2))
        elif args.command == "prepare":
            prepare(args.before, args.after, args.case_id, args.out, args.repeats)
            print("Prepared packets only; no model generation or review has run.")
        elif args.command == "blind":
            blind(args.run)
            print("Blinded supplied outputs; independent review is still required.")
        else:
            print(json.dumps(report(args.run), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
