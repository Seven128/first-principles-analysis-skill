# Repository instructions

This repository contains the `first-principles-analysis` skill.

## Source hierarchy

Runtime authority:

1. `references/core/`
2. Relevant files in `references/subjects/`
3. Relevant cards in `references/conclusions/`
4. `references/writing/` when the user needs an article, report, memo, or detailed plan
5. `SKILL.md` orchestration and output rules

Historical source baselines:

- `references/第一性原理分析逻辑.md`
- `references/第一性原理分析提示词.md`
- `references/经验/`
- `references/回归样例/`

Do not silently edit historical source baselines. If a source-controlled file changes, update `references/source-manifest.json` and explain why.

## Change principles

- Fix the most upstream reusable cause, not one example only.
- Keep common reasoning separate from subject-specific guidance.
- Keep complete reasoning separate from article composition.
- Before composition, preserve facts, causal direction, conditions, uncertainty, and evaluation criteria as invariants.
- Optimize effective information density: preserve correct and useful information while reducing the reader's understanding cost.
- Do not flatten proven dependencies into attribute lists, and do not invent causal order among parallel conditions.
- Prefer concrete subjects, actions, and state changes over nominalized abstractions when accuracy is preserved.
- Introduce fields, modules, and terms when they first become necessary to the current causal step, not merely because they belong to the same structure.
- Use examples and metaphors only when they reduce understanding cost; author voice, slang, emotion, and fixed narrative structures are optional flavor, not universal rules.
- Treat conclusion cards as candidate explanations, never axioms.
- Preserve the distinction between facts, inferences, hypotheses, and evaluation criteria.
- Do not add hidden value judgments such as “long-term is better” unless the user selects that standard.
- Use plain Chinese in reader-facing rules. Avoid internal symbols and inflated wording.
- Do not solve verbosity by deleting necessary causal steps, and do not interpret “detailed” as permission to repeat every implementation detail.
- Add or update reasoning regressions, writing regressions, or paired writing samples for every new general rule.

## Validation

Run:

```bash
python3 scripts/validate_skill.py
python3 scripts/validate_writing.py
python3 scripts/validate_conclusions.py
python3 scripts/lint_language.py --strict
```

The scripts validate structure, paired writing samples, and high-risk wording. They do not replace model-output evaluation, causal-invariant review, or reading-comprehension checks.
