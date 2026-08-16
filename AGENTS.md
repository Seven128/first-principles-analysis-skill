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
- For long-form delivery, materialize a semantics-locked analysis draft before composition. The draft must include the completed actual analysis question, repaired causal chain, applicable purpose nodes, evidence boundaries, and must-keep / optional / must-not-infer content.
- Treat article positioning as a contract: article type, target reader, reader task, scope, out-of-scope content, detail level, and narrative viewpoint. Effective information density is a quality criterion, not the article's purpose.
- In an article, put the completed actual analysis question immediately after the title. For purpose-bearing articles, preserve the visible order: actual analysis question → final purpose → current state and problems → adopted solution. Do not force the purpose nodes onto non-purpose objects.
- Treat question words such as “是什么、为什么、怎么做” as weak signals. Route from object/result state, acting subject, user role, time direction, the real unknown, and the requested delivery.
- Model complex input as a problem structure: separate facts, user hypotheses, constraints, questions, and delivery requirements; distinguish the core question, supporting questions, and independent questions; preserve their real dependencies and the user's current explicit priority.
- After problem modeling, decide whether the object carries an explicit purpose. Use the purpose/current-state/problem/solution chain for user goals, designed systems, plans, and supported conscious choices; do not force it onto definitions, natural processes, emergent group outcomes, or automatic emotions.
- For purpose-bearing problems, preserve the semantic order: final purpose and completion criteria → current facts, capabilities, and constraints → missing conditions and problems → design principles → concrete paths → validation, cost, and boundaries.
- Keep the final purpose at the result level. Do not leak modules, protocols, algorithms, class names, or implementation properties into the goal node.
- Keep current state and problem distinct even when they share one reader-facing heading. Current state supplies facts; the problem is the missing condition derived from the purpose-state gap.
- Every solution mechanism must trace to a proven problem. A mechanism introduced only for architectural completeness should be removed, deferred, or marked optional.
- Use prior conversation and project context as evidence for intent, not as permission to override the user's current explicit goal or invent missing personal facts.
- When intent remains ambiguous, clarify only when competing interpretations would produce materially different deliverables. Otherwise answer the shared core or state a temporary scope and continue.
- Before accepting a key causal or action node, classify whether it claims necessity, sufficiency, contribution, one implementation, or mere association; test counterexamples, counterfactuals, alternative paths, reverse causality, and common causes at a depth proportional to the node's impact.
- When node validation finds a gap, repair the node by adding conditions, splitting the mechanism, adding alternatives, weakening the claim, narrowing the scope, or removing it. Do not keep the original absolute claim with only an “exception” note.
- Before composition, preserve facts, causal direction, conditions, uncertainty, evaluation criteria, purpose-structure applicability, and the repaired strength of key nodes as invariants.
- Composition may select, order, compress, and phrase the analysis draft. It may not redefine the problem, silently add new conclusions, or pull unrelated personal/project context from the raw conversation. If the handoff is incomplete, return to reasoning and repair it before writing.
- Default the current requester as the target reader, but express that through information selection and explanation depth. Technical articles use a neutral, self-contained voice and must not contain phrases such as ‘用户当前材料’, ‘用户此前提到’, ‘你的求职材料’, or ‘本轮对话中’.
- Optimize effective information density: preserve correct and useful information while reducing the reader's understanding cost.
- Do not flatten proven dependencies into attribute lists, and do not invent causal order among parallel conditions.
- Prefer concrete subjects, actions, and state changes over nominalized abstractions when accuracy is preserved.
- Introduce fields, modules, and terms when they first become necessary to the current causal step, not merely because they belong to the same structure.
- Default to direct literal explanation before adding examples. Prefer one section-level or whole-chain example over separate micro-examples for every small point; retain multiple examples only when they have distinct indispensable functions.
- Paragraph boundaries follow major conclusions, not sentence count. Do not interpret “one sentence advances one relation” as “one sentence per paragraph.”
- Use code fences for code, configuration, exact data, protocols, complex flows, or copyable commands. Do not put ordinary prose, short lists, or simple causal chains in code blocks for display.
- Use examples and metaphors only when they reduce understanding cost; author voice, slang, emotion, and fixed narrative structures are optional flavor, not universal rules.
- Treat conclusion cards as candidate explanations, never axioms.
- Preserve the distinction between facts, inferences, hypotheses, and evaluation criteria.
- Do not add hidden value judgments such as “long-term is better” unless the user selects that standard.
- Use plain Chinese in reader-facing rules. Avoid internal symbols and inflated wording.
- Do not solve verbosity by deleting necessary causal steps, and do not interpret “detailed” as permission to repeat every implementation detail, example, or summary.
- Add or update reasoning regressions, focused intent-routing regressions, focused node-validation regressions, focused purpose-structure regressions, writing regressions, writing-density regressions, or paired writing samples for every new general rule.

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
python3 scripts/validate_purpose_structure.py
python3 scripts/validate_writing.py
python3 scripts/validate_writing_density.py
python3 scripts/validate_conclusions.py
python3 scripts/lint_language.py --strict
```

The scripts validate structure, focused intent-routing, node-validation, purpose-structure, writing-density cases, paired writing samples, and high-risk wording. They do not replace model-output evaluation, causal-invariant review, or reading-comprehension checks.
