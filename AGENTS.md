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
- Treat question words such as “是什么、为什么、怎么做” as weak signals. Route from object/result state, acting subject, user role, time direction, the real unknown, and the requested delivery.
- Model complex input as a problem structure: separate facts, user hypotheses, constraints, questions, and delivery requirements; distinguish the core question, supporting questions, and independent questions; preserve their real dependencies and the user's current explicit priority.
- Use prior conversation and project context as evidence for intent, not as permission to override the user's current explicit goal or invent missing personal facts.
- When intent remains ambiguous, clarify only when competing interpretations would produce materially different deliverables. Otherwise answer the shared core or state a temporary scope and continue.
- Before accepting a key causal or action node, classify whether it claims necessity, sufficiency, contribution, one implementation, or mere association; test counterexamples, counterfactuals, alternative paths, reverse causality, and common causes at a depth proportional to the node's impact.
- When node validation finds a gap, repair the node by adding conditions, splitting the mechanism, adding alternatives, weakening the claim, narrowing the scope, or removing it. Do not keep the original absolute claim with only an “exception” note.
- Before composition, preserve facts, causal direction, conditions, uncertainty, evaluation criteria, and the repaired strength of key nodes as invariants.
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
- Add or update reasoning regressions, focused intent-routing regressions, focused node-validation regressions, writing regressions, or paired writing samples for every new general rule.

## Branch workflow

- Perform normal development directly on `main`.
- Create a separate branch only when the work requires isolation.
- After completing and validating work on a separate branch, merge it back into `main`; do not leave completed work only on a non-`main` branch.

## Validation

Run:

```bash
python3 scripts/validate_skill.py
python3 scripts/validate_intent_routing.py
python3 scripts/validate_node_reasoning.py
python3 scripts/validate_writing.py
python3 scripts/validate_conclusions.py
python3 scripts/lint_language.py --strict
```

The scripts validate structure, focused intent-routing and node-validation cases, paired writing samples, and high-risk wording. They do not replace model-output evaluation, causal-invariant review, or reading-comprehension checks.
