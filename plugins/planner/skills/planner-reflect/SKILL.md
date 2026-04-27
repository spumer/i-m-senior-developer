---
name: planner-reflect
description: >
  This skill should be used when the user invokes /plan-reflect, says
  "reflect on the plan", "what did we learn", "post-mortem the planning",
  or in russian «отрефлексируй», «что пошло не так»,
  «обнови контекст планнера», «сверь план с фактом».
  Activates after a session that ran /plan-do or otherwise produced a
  PLANNER_OUTPUT.md. Compares plan against reality using five evidence
  sources and updates planner-context.md with four learning types:
  gap-fill, model-strength signals, user-correction patterns, and
  cost-calibration deltas. Always emits a "Lessons learned" section,
  even if empty, as a force-function for honest retrospection.
---

# Planner-Reflect — post-task learning

This skill compares what was planned against what actually happened, extracts lessons, and writes them back into `<project-root>/.claude/planner-context.md` so the next planning session starts smarter. It is the feedback loop that closes the gap described in feature README §35-44: plans drift from reality, gaps in the agent catalog go unnoticed, weak-model signals are forgotten, user corrections evaporate after the session ends. Run this skill explicitly via `/plan-reflect`, ideally in the same session as the work it reflects on — cross-session transcript availability is not guaranteed and the skill degrades gracefully if it is missing.

The run is short and linear: gather the five evidence sources, classify findings into the four update types, mask any PII in the proposed additions, write the result to `planner-context.md`, and emit a chat summary that always includes a "Lessons learned" block. There is no looping, no escalation, and no chaining into other skills — reflection is observation, not action.

## Inputs (5 evidence sources)

The skill reads exactly five sources, in this order. Each source is independent; missing one weakens the conclusions but does not block the run.

1. **`<feature-dir>/PLANNER_OUTPUT.md`** — the original plan: phases, agents chosen, model picks, cost estimate. Read with `Read`. This is the ground truth for "what was planned"; if it is missing, the skill exits (see next section).
2. **`git log --oneline <since-plan>..HEAD`** — actual commits made since the plan was written. Use `Bash(git log …)` constrained to git only. Compare commit subjects and files-touched against the plan's phases to spot scope creep, dropped phases, or unplanned files.
3. **Review files under `<feature-dir>/review-request-changes/`** — defects raised during the session, their severity tags, and the files they pointed at. Use `Glob` for discovery and `Read` for content. High-severity recurring defect categories feed §6 (user-corrections) and §4 (model-strength).
4. **Agent transcripts via `TaskGet` / `TaskOutput`** — used to detect retry/escalate patterns inside subagent runs (e.g. "test failed → fix → still failed → escalate"). Current-session-only by default; treat cross-session calls as best-effort and do not assume reachability.
5. **User messages from the current session** — explicit corrections such as «не делай сам», «это неправильно», «переделай», «не лезь сам в код». Source: the live conversation transcript visible to the skill at runtime.

## When evidence is missing

The skill must not fail loudly when an input source is missing — the reflection loop should produce *some* signal whenever it runs, even if degraded. The rules below cover the four common cases.

- **No `PLANNER_OUTPUT.md`** → exit gracefully with the message `nothing to reflect on; run /plan first`. Do not fail, do not write a half-formed lesson, do not invent a plan from git history.
- **No transcripts** (cross-session call, tool unavailable, or future Claude Code semantics changing) → degrade to git-diff plus review-files only. Label the output explicitly: `transcript-based learnings unavailable`. The four update types remain available; only the model-strength signal weakens because retry-loops are no longer directly observable.
- **No git history since the plan** → likely the plan was never executed; emit `plan exists but not yet executed; nothing to reflect` and stop without writing.
- **Partial evidence** (some sources present, others missing) → proceed with what is available, and note in the chat summary which sources were unavailable so the user can judge the strength of the conclusions before acting on them.

## The 4 update types

Each update type has a trigger (when the skill should produce it), a recording format (exactly what gets written), a destination section in `planner-context.md`, and a tone-rule (the wording discipline that prevents categorical or accusatory statements). Skip a type entirely if its trigger does not fire for this session — empty is better than fabricated.

### 4.1 gap-fill

- **Trigger** — the orchestrator used `general-purpose` where `planner-context.md` §1 had a `❌ GAP` flag for the relevant stack, OR a stack appeared during the session that was not even flagged in the catalog.
- **Record** — for an existing flag, append `<!-- gap-confirmed YYYY-MM-DD from FEAT-XXXX -->` to the gap row. For a newly discovered stack, add a new gap row in the format `❌ GAP (<stack>, <variant>) — fallback: general-purpose <!-- discovered YYYY-MM-DD from FEAT-XXXX -->`.
- **Destination** — §1 of `planner-context.md` (Каталог агентов).
- **Tone** — neutral and factual: describe the missing role, do not blame the orchestrator. The gap is a property of the catalog, not a failure of the run.

### 4.2 model-strength

- **Trigger** — transcripts (or git-log of repeat commits on the same files) show retry-loops, failed test cycles, or explicit escalation. Cost-actuals also feed here when they correlate with retry patterns.
- **Record** — a sentence in the form «for tasks of type X on this project, model Y was weak → consider model Z». Always tie the observation to (a) **task type**, (b) **this project**, (c) the **FEAT-id** as evidence anchor.
- **Destination** — §4 of `planner-context.md` (Таблица моделей), as a sub-bullet under the relevant model row.
- **Tone-rule (non-negotiable, README Edge-Case row 9)** — never write categorical statements like «Sonnet bad» or «Haiku unreliable». A model is weak *for a task-type in a project context*, never absolutely. If the skill cannot name all three of `task-type + project + FEAT-id`, it must not write the lesson — the evidence is too thin and a categorical claim would mislead future runs.

### 4.3 user-corrections

- **Trigger** — explicit user pushback in the session: «не делай сам», «это неправильно», «переделай», «не лезь в код», «верни как было» — pulled from the session messages source (input #5).
- **Record** — a one-line guard-rail, format `avoid <pattern> — learned from FEAT-XXXX`. Extract the *pattern* of the mistake (e.g. «orchestrator wrote code instead of dispatching»), not the verbatim rebuke.
- **Destination** — §6 of `planner-context.md` (Соглашения именования / lessons).
- **Tone** — descriptive, not accusatory. Capture the pattern, not the wording of the rebuke; the file is read by future sessions and emotional residue distorts decisions.

### 4.4 cost-calibration

- **Trigger** — delta between planned tokens/wall-clock (from `PLANNER_OUTPUT.md` § "Cost estimate") and actual usage exceeds ±30% in either direction.
- **Record** — `estimate adjustment: <task-type> takes ~Nx more/less than planned (FEAT-XXXX)`. Token counts come from session metadata; wall-clock from commit timestamps via `git log`.
- **Destination** — §4 of `planner-context.md` (alongside model notes — costs and model picks are tightly coupled).
- **Tone** — numeric and factual; do not infer cause unless evidence is direct. A 2x overshoot might be model weakness, scope creep, or a flaky test — name only what the evidence supports.

## Always-emit "Lessons learned" section

Every `/plan-reflect` run produces a `## Lessons learned (FEAT-XXXX, YYYY-MM-DD)` block in the chat output, even when nothing new was found. The block has two valid shapes — populated or explicitly empty — and the choice depends only on what the evidence actually supports.

The **empty** case shows exactly this — and only this:

```
## Lessons learned (FEAT-XXXX, YYYY-MM-DD)
_no actionable lessons this session_
```

The **populated** case lists each lesson on its own bullet, tagged with the originating evidence and the destination section, e.g.:

```
## Lessons learned (FEAT-0042, 2026-04-26)
- gap-fill: confirmed missing frontend agent (§1) — evidence: 3 commits routed through general-purpose
- cost-calibration: architecture phase took 1.8x planned tokens (§4) — evidence: session metadata
```

The always-on rule is a deliberate force-function (README §89). The user sees the section and notices when nothing was learned, which prompts a second look — sometimes there *was* a lesson and the skill missed it; sometimes the session was genuinely smooth and the empty block is honest evidence of that. A silent skip would let bad sessions leave no trace and erode trust in the reflection loop over time.

## Output protocol

The skill produces output in a fixed four-step order. Steps run sequentially; do not interleave or reorder.

1. **Write target** — the only file modified is `<project-root>/.claude/planner-context.md`. Use `Write` to create it on first run, or read-modify-write to extend it on subsequent runs. Every new line carries `<!-- learned YYYY-MM-DD from FEAT-XXXX -->` at the end, per README §43; this turns the file into a dated audit log of what the planner has learned about this project, queryable by date or by FEAT-id.
2. **Chat summary** — emit a short bullet list of what changed: which sections were touched, how many lines were added, which evidence sources were used, and which were unavailable. Then render the always-present "Lessons learned" block per the section above. The summary should fit in the user's screen without scrolling — terse beats exhaustive. A typical summary looks like:

   ```
   planner-context.md updated:
   - §1 (agents): +1 row (gap-confirmed)
   - §4 (models): +1 sub-bullet (cost-calibration)
   - evidence used: PLANNER_OUTPUT, git-log, review-files
   - evidence missing: transcripts (cross-session)
   ```

   Then the "Lessons learned" block renders below, completing the summary.
3. **HITL gate for auto-memory** — if the same lesson has been observed in **≥2 distinct sessions** (cross-FEAT), suggest the user create an auto-memory entry. Do **not** create memories autonomously. Phrase the suggestion as a question: «Этот урок встречается во второй раз (FEAT-A, FEAT-B). Создать memory? (требуется явное подтверждение)». The threshold of two is deliberate — single-session lessons are too noisy to promote, and silent auto-creation removes user agency over their global memory.
4. **Stop** — return control to the user or orchestrator. Do not loop, do not chain into `/plan`, do not "improve" the plan post-hoc. Reflection ends when the file is written and the summary is rendered.

## PII / secret stripping

Never copy raw transcript chunks into `planner-context.md`. Extract abstract patterns only — «3 retry iterations to green tests» is fine; «the test `test_user_login_xyz` failed because password = 'p4ssw0rd!'» is not. The file is committed to the project repository and read by every future planning session, so a single leaked secret can propagate widely and is hard to retract once committed.

Before each `Write`, scan the proposed addition and **mask in place** (do not drop the line, do not abort the run) any of the following three categories. Run the scan after lesson extraction and before file write — never trust upstream sources to be clean.

- **Emails** — pattern shaped like `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}` → replace each match with `<email>`. Keeps the structural fact "an email was here" without exposing the address. Applies to user emails, support addresses, and inline contact strings alike.
- **Long alphanumeric tokens** — any continuous run of 40+ characters from `[A-Za-z0-9_\-]` (API keys, OAuth secrets, JWTs, git SHAs in unusual contexts, password hashes) → replace with `<token>`. The 40-char threshold is deliberately conservative: short identifiers like `FEAT-0001` or `user_id_42` survive untouched, while real-world API tokens (which are nearly always longer than 40 chars) get caught.
- **User-home paths** — `/Users/<name>/...`, `/home/<name>/...`, `C:\\Users\\<name>\\...` → replace the user segment with `<user>` and keep the relative tail intact (e.g. `/Users/svp/projects/foo` becomes `/Users/<user>/projects/foo`). Project structure is signal worth preserving; the operator's username is not.

Masking preserves the lesson while neutralising the leak. Failing closed (refusing to write) is worse than masking — it loses the lesson entirely and discourages running the skill at all, which is exactly the failure mode the reflection loop exists to prevent. If after masking an addition is empty or semantically meaningless (e.g. the entire useful payload was a token), skip that single entry and note in the chat summary that one was dropped due to redaction, so the user knows there was something the skill could not safely record and can decide whether to investigate manually.

## Boundaries

- The **only** writeable target is `<project-root>/.claude/planner-context.md`. No other path may be touched, even with good intent.
- Do **not** modify code under any circumstance — this skill is read-mostly and has no business in source files.
- Do **not** modify `<feature-dir>/PLANNER_OUTPUT.md`. It is a historical record of what was planned at that moment; rewriting it destroys the very evidence this skill depends on for future runs and breaks the audit trail.
- Do **not** invoke other agents or chain into other skills; reflection is a single-pass observation, not an orchestration step.
- Do **not** invent lessons to pad the "Lessons learned" section. Emptiness is a valid, honest result and is preferable to fabricated insight.
- Do **not** rewrite or "tidy up" entries authored by the user manually in `planner-context.md`. Manual edits are sources of truth; only append new lines, never overwrite.

The boundaries above are deliberately strict because the value of `planner-context.md` lies in its trustworthiness. A reflection skill that quietly edits unrelated files, fabricates lessons to look productive, or rewrites historical artifacts is worse than no skill at all — it teaches the user not to trust the loop.

## Reference index

This skill has no references. The workflow is small and self-contained — five inputs, four update types, one writeable target, one always-emit section, one HITL gate. Loading it should not pull additional files; the entire procedure fits in this single document and benefits from being read top-to-bottom in one pass.

If a future change pushes content past the 170-line budget, the spec (PLAN-01 §6) calls for splitting into references at that point. Until then, inline beats progressive disclosure for a skill this focused — every fact is on the page when the skill activates, no second hop required, no risk of partial loading. The cost is one full read each time the skill runs; the benefit is zero ambiguity about where a rule lives.
