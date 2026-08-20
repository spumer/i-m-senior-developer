---
name: code-reviewer
description: >
  This skill should be used when reviewing code changes — security
  issues, system-level defects, FPF/Functional Clarity violations,
  stack-specific pitfalls. Activates when the user asks to "review",
  "check this PR", "is this safe", "find bugs", "code review", or in
  russian «отревью», «проверь код», «есть ли проблемы», «code review».
  Operates on git-diff. Always loads `references/security.md`
  (OWASP Top 10 — non-negotiable). Loads stack-specific references
  (backend-python or frontend-react) on demand. Integrates with
  `functional-clarity:functional-clarity` for Error Hiding and FPF
  checks. Outputs a review report with file:line references; never
  modifies code itself.
---

# Code-Reviewer — system-level + security

Reviews code changes for system-level issues, security vulnerabilities, and FPF violations in changes not authored by the reviewer. Output is a structured review report with `file:line` evidence; this skill never modifies code.

**Always-active rule:** When reviewing any code, load `references/security.md` regardless of stack or apparent diff scope. This is non-negotiable.

## Principles

1. **System issues over taste.** "I would name this differently" is not a review item. "This name says what it does, but the function does something else" is. Flag objective defects — correctness, safety, contract adherence. Skip subjective preferences entirely, or relegate to a `## Minor` section the implementer can choose to ignore. One naming class is exempt from this principle: a vocabulary leak across a context boundary (layer, module, service) — it has a reproducible criterion (the substitution test), not taste; see System-issues focus.

2. **Evidence per finding (FPF A.10).** Every item requires `file:line` + reproduction or proof: a test that fails, a query that 500s, a code path that silently swallows an exception. A finding without evidence is an opinion. Opinions do not belong in a review report. Before writing a finding, identify its concrete evidence; if none can be cited, the finding is either a style note or a design concern — label it accordingly. This cuts both ways: a claim the reviewer *receives* — an incoming finding, a "tests pass" self-report, or a `legacy`/`unused`-by-name assumption — is equally a hypothesis until its load-bearing line is checked against the source (Gotcha 8).

3. **Security always.** Load `references/security.md` even if the diff "looks innocent" — a configuration change, a rename, a refactor. Secrets and auth bugs slip in via innocuous-looking changes. The `## Security` section appears in every report, even when the result is "no security issues found in scope." The empty section is a force-function; its presence proves the check ran.

4. **FPF lens.** Apply Functional Clarity principles when reviewing. Key checks: Error Hiding (silently swallowed exceptions, defaults masking failures), fail-fast violations (validation deep in the call stack), contract changes without explicit discussion, leaked invariants. If `functional-clarity:functional-clarity` is installed, activate it for the full 22-principle set.

5. **Don't propose implementation.** Describe the issue and the fix direction. The implementer chooses and applies the concrete fix. Writing corrected code in the review inlines the reviewer's assumptions about the surrounding context — assumptions that may be wrong. The reviewer's job is diagnosis; the implementer's job is treatment.

6. **Operate on git-diff.** Review the change set, not the whole codebase. The scope of a finding is what changed. Cross-reference with `Read` and `Grep` to understand context when needed, but keep findings anchored to lines that exist in the diff. Reviewing the entire project when a 3-file diff was supplied is a scope error.

These six principles establish the reviewer's epistemic discipline. Together they prevent the four most common review failure modes: (a) flooding the report with noise that buries real findings; (b) asserting problems without evidence, creating false blockers; (c) accidentally skipping security due to apparent diff innocuousness; (d) overstepping into implementation, producing a second set of unreviewed changes.

## Workflow

6-step pipeline, runs on every activation:

1. **Read input.** Obtain diff range or PR reference. If neither is provided → fail-fast: "need a diff range (`<base>..HEAD`), PR number, or branch name to review against; cannot proceed without scope." Do not begin reviewing without a defined scope. An undefined scope produces either an incomplete review or a whole-codebase review, both of which are wrong. When a PR number is given, resolve it to a base/head range first with `git log`.

2. **Run `git diff <base>..HEAD --stat`** (Bash) for the file overview — understand which files changed and how many lines before diving into individual files. Then `git diff <base>..HEAD -- <path>` per file for detailed review, prioritizing files with the highest churn (most lines changed) first. Then `git log <base>..HEAD --oneline` to understand the author's intent from commit messages.

3. **Always load `references/security.md`.** No stack condition. Load it first, before stack detection. Run the security checklist as the first pass over the diff. Record all security findings (or confirm "no issues") before moving to stack-specific checks. Do not defer security until after other checks — security findings block merge; stack findings are often advisory.

4. **Detect stack from changed files.** `*.py` files in diff → load `references/backend-python.md`. `*.tsx` / `*.jsx` / `*.ts` / `*.vue` / `*.svelte` in diff → load `references/frontend-react.md`. Both present in diff → load both references and apply both checklists. Unknown stack → apply universal principles (see §When references are missing below) and note in the report header.

5. **Walk the diff with loaded checklists.** Apply security checklist first, then FPF check (Error Hiding, fail-fast, contract), then stack-specific checklist. For each section of the diff: ask "what could go wrong here?", "is there a test for this behavior?", "does this change any contract silently?". Classify each finding: major (blocks merge), minor (advisory), security (always blocks merge), design concern (routes to architect). Consolidate duplicate findings — same pattern in multiple files becomes one item with all locations.

6. **Emit review report** per output format below. Write to `<feature-dir>/review-request-changes/REVIEW-NN.md` if a feature directory exists; output to chat otherwise. Output must always use the structured template — no freeform prose in place of the template sections. The structured format enables the implementer to process each finding as an independent work item.

## Git-diff approach

Exact commands used in this skill — do not deviate:

```bash
# Step 1: overview — which files changed, insertions/deletions
git diff <base>..HEAD --stat

# Step 2: per-file detailed diff (repeat per file under review)
git diff <base>..HEAD -- <path/to/file>

# Step 3: commit context — what did the author intend?
git log <base>..HEAD --oneline
```

Additional tools for context:

- **`Read`** — load the full file when the diff context is insufficient to understand the surrounding code (e.g. checking whether a changed function is called elsewhere without ownership checks, or reading the full model to understand which fields can be null).
- **`Grep`** — search for patterns across the codebase (e.g. `grep -r "mark_safe" .` to find all usages, not just new ones in the diff; `grep -r "select_for_update" .` to confirm all usages are inside `atomic` blocks; `grep -r "SECRET_KEY" .` to check for leaked credentials).
- **`Glob`** — list files matching a pattern to understand project structure when context is needed (e.g. `plugins/sdlc/**/*.py` to understand how many Python files exist before deciding to load `backend-python.md`).

**Forbidden commands in review mode:** `git checkout`, `git reset`, `git add`, `git commit`, `git push`, `git stash`, `git apply`, `git merge`, `git rebase`. The reviewer never mutates the working tree, the index, or any branch.

Review is strictly read-only. The rationale: a reviewer who can modify the repository is no longer a reviewer — they become a co-author of unreviewed changes. Maintain the separation of concerns.

If a finding requires running code to verify (e.g. confirming a race condition is observable), instruct the implementer: "unverified — implementer to reproduce by running `<command>`." The implementer confirms and reports back; the reviewer then updates the finding if the reproduction fails. The report's `## Certification boundary` section names, up front, the defect classes static review cannot certify — state them as a self-limitation; do not silently imply they were cleared.

## OWASP / security framing

`references/security.md` is always loaded — every activation, every stack, every diff size (Principle 3). The `## Security` section appears in every report: list findings as `file:path:line — <OWASP category> — <evidence> — <fix direction>`, or write exactly "no security issues found in scope". Severity labels: **critical** (exploitable now), **high** (low-effort, e.g. cross-user data access), **medium** (needs prerequisites/chaining), **low** (defense-in-depth). **Never downgrade a security finding for "it's internal" or "only admins reach it"** — assess on exploitability, not assumed access. Full rationale and the non-web confirmation form: `references/review-conventions.md`.

## FPF check (Functional Clarity)

Activate `functional-clarity:functional-clarity` for the full 22-principle methodology and bodies. Key checks the reviewer must surface, regardless of stack: **Error Hiding** (silently swallowed exceptions, defaults masking failures), **fail-fast violations** (validation deep in the call stack instead of at the entry boundary), **contract changes without migration** (changed signature/return-type/semantics for existing callers — Code-Change Discipline rule 6), **leaked invariants** (state assumptions not enforced in code), and **information removal** (removed log/comment/error without replacement — Code-Change Discipline rule 7). Code-Change Discipline ships with the `functional-clarity` plugin as `references/02-code-change-discipline.md`. Names only here; cite `functional-clarity:functional-clarity` for the bodies. The check runs on the entire diff regardless of language.

## System-issues focus

Categories the reviewer prioritizes, ordered by signal-to-noise ratio. Style is delegated to linter or listed last:

- **N+1 queries** — loops over querysets accessing related objects without `select_related`/`prefetch_related`; DRF nested serializers missing prefetch on the view queryset. Severity: critical on list endpoints, high on detail endpoints. See `references/backend-python.md` for Django-specific patterns.
- **Race conditions** — multi-step writes outside `transaction.atomic`, `get_or_create` without atomic wrapper, shared mutable module-level state in a web process.
- **Transaction boundaries** — any sequence of two or more writes (`save`, `create`, `update`, `delete`) that must succeed or fail together, without a wrapping atomic block.
- **Error swallowing** — `except`/`catch` that consumes an error and returns success or a silent default. Invisible to monitoring; produces incorrect system state while appearing healthy.
- **Contract changes** — changed function signatures, return types, or behavior for existing callers without explicit documentation of the breaking change.
- **Vocabulary leak across a context boundary** — an element declared in
  context A (port, method, parameter, event name, schema field, docstring)
  is named in context B's vocabulary: the counterpart's action, mechanism,
  or domain term (`InvoiceEmailQueuePort.enqueue_email`,
  `emit("trigger_welcome_email")`, a `queue=`/`retry=` parameter in an
  abstract port, a port docstring pointing into the subscriber's
  internals). The boundary can be a layer, a module, or a service — the
  criterion is the same at every scale, and the leak travels through any
  of three channels: name, type/signature, prose. Criterion — the
  substitution test: replace/add the counterpart behind the boundary; if
  the name, signature, or docstring becomes inaccurate, the finding is
  real. Explicitly EXEMPT from Principle 1 ("I would name this
  differently" is not a review item): reproducible criterion, not taste.
  Check especially where imports are clean — inverted dependencies are the
  blind spot of structural analysis. Do not flag names internal to one
  context, or presentation-layer copy (button labels, operator-facing
  texts). Severity: major on public ports/events/signatures/schemas
  (couples context evolution), minor in prose-only leaks
  (docstrings/comments). Normative text (leak channels, per-scale
  examples, ❌/✅, false positives): `functional-clarity`
  `references/06-boundary-vocabulary.md`.
- **Leaked secrets** — credentials, API keys, tokens in the diff. This includes test fixtures, comments, and URLs with embedded auth strings.
- **Missing migrations** — model or schema changes without a corresponding migration file. The migration is part of the change, not "to be added later."
- **Untested edge cases** — happy path is tested; negative paths, empty inputs, and permission boundaries are not. Flag each missing test case; the implementer adds them.
- **Object lifecycle / teardown** — manual `create`/`destroy` (init/dispose, subscribe/unsubscribe, mount/unmount) gets review regardless of apparent simplicity. Watch for orphan objects (never attached to the managed tree), a method called on an already-destroyed object, a non-null ref trusted as proof of liveness (guard on a liveness flag, not `!= null`), one-shot listeners surviving a skip/interrupt, and double-fired transition handlers. Severity: major on a live render/event path. Stack-neutral.
- **Incomplete sweep / partial migration** — the diff point-fixes one site of a defect class (hardcoded literal, missing auth check, un-migrated call site, renamed field) while identical sites remain. `Grep` the whole class; if others remain, format as "partial fix: N of M sites; remaining: `file:line`". For a project-wide invariant, recommend a scanning test (per `tdd-master:tdd-master`) over eternal manual audit. Severity: major if unswept sites are exploitable/user-visible, else minor.
- **Tracking IDs leaked into code** — `FEAT-XXXX`, issue numbers, or plan
  file names in code comments, docstrings, test names, or identifiers.
  These belong to artifact filenames in the feature directory; in code they
  are noise the team has to clean up. `Grep` the diff for the project's
  feature-id pattern. Severity: minor, but flag every occurrence.
- **Comment hygiene** — comments that cite internal project docs (`see
  DESIGN §…`, `per PLAN §2.4`), carry change history (`no longer reads`,
  `— unchanged`, `since v2`, `RED→GREEN`), restate the adjacent line
  (`// increment counter`), or report the author's own work — text written for
  whoever reviewed the change, not for the next reader of the code (`took a
  dict instead of the plan's list`, `left this untouched to keep tests green`);
  that belongs in the commit message. They state nothing the code cannot
  express and grow cognitive load. Distinct from the tracking-id bullet above (that
  covers `FEAT-XXXX`) — do not merge them. Normative text (smell classes,
  allowlist, borderline cases): `functional-clarity`
  `references/05-comment-style.md`. Known false positives — do not flag:
  external standards (`RFC 7231`, `PEP 8`), versioned-API doc conventions
  (`.. versionadded::`, `@since`), `TODO`/`FIXME`/`SAFETY:` lines, and
  changelog-looking wording that explains current behavior — if dropping the
  reference to the past leaves a useful statement, suggest a present-tense
  rewrite instead of deletion. `Grep` the diff's comment lines. Severity:
  minor. In a large diff, report one finding with the list of locations, not
  one finding per line.
- **Test runtime config diverges from prod** (stack-neutral) — tests run under a different runtime/concurrency config than production, so a prod-only failure mode stays green in CI (e.g. a test runner that auto-cleans pending work vs a long-lived prod runner; test parallelism flags masking shared/singleton-state leaks; a test config/middleware stack thinner than prod). Flag concurrency / parallel / shutdown code tested only under the harness default — require a test or smoke under the prod runtime config.

**Severity triage:** Major findings block the merge and require a fix commit before re-review. Minor findings are advisory — the implementer decides whether to address them now or file a ticket. Design concerns never block the current merge — they are inputs to the next architecture iteration. Security findings at high or critical severity always block merge; medium and low are advisory.

Style and naming: delegate to ESLint, Ruff, Flake8, or similar. If the project has a linter configured, add one line to the review: "style: delegated to linter." If no linter is configured, put style items in `## Minor` and keep the section to 5 items maximum.

## Stack detection (summary)

Stack is detected from the changed file extensions in the diff — not from project configuration. Detection is opportunistic (diff may not include config files):

| Signal in diff | Reference to load |
|---|---|
| `*.py` files | `references/backend-python.md` |
| `*.tsx`, `*.jsx`, `*.ts`, `*.vue`, `*.svelte` | `references/frontend-react.md` |
| Both present | Load both; apply both checklists |
| Neither | Universal principles; note in report header |

Mixed stack (Python + React in same diff): apply both checklists. Python-side findings go in `## Stack-specific / backend`, React-side findings go in `## Stack-specific / frontend`.

For stack-detection signals beyond the diff (detecting full project context), the master heuristic table lives in `plugins/planner/skills/planner/references/bootstrap.md` §4. The reviewer does not re-run bootstrap; it references it for context if needed.

## Output format — review report

Template for `<feature-dir>/review-request-changes/REVIEW-NN.md`. When no feature directory exists, output the same structure to chat.

```markdown
# Review — <feature-id or branch name> (REVIEW-NN)

> **Diff:** `<base>..<head>`
> **Commits:** <git log --oneline output, one line per commit>
> **Stack:** backend-python | frontend-react | mixed | unknown
> **References loaded:** security.md[, backend-python.md][, frontend-react.md]
> **Reviewed:** <ISO date>

## Summary
- Major: N
- Minor: N
- Security: N (or "no issues found in scope")
- Design concerns: N

## Security
<!-- Always present. "no security issues found in scope" if clean. -->
- `file:path:line` — <OWASP category> — <evidence/reproduction> — <fix direction>

## System issues
<!-- N+1, races, transactions, error-swallow, contract changes, missing migrations -->
- `file:path:line` — <category> — <evidence> — <fix direction>

## FPF / Functional Clarity violations
<!-- Error Hiding, fail-fast, contract, information removal -->
- `file:path:line` — <principle> — <evidence> — <fix direction>

## Stack-specific
<!-- Populated from loaded references. Skip section if no stack references loaded. -->
- `file:path:line` — <finding> — <evidence> — <fix direction>

## Minor
<!-- Taste, style, naming. Only if not delegated to a linter. Max 5 items. -->
- `file:path:line` — <observation>

## Certification boundary
<!-- Always present. What static review does NOT certify. -->
Static diff review certifies only what is readable in the diff. It does NOT
certify runtime behavior: defect classes that surface only at run time
(teardown/shutdown ordering, calls on destroyed objects, lifecycle leaks) or
at render (visual-spec deviation) are out of scope of static review — flag
them for runtime/human verification; do not record them as cleared.

## Hand-off
Next: `sdlc:code-implementer` to apply fixes for all major and security items.
Design concerns (if any): escalate to `sdlc:architect` via the orchestrator.
```

Finding format (mandatory for every non-minor item):

```
`file:path:line` — <issue description> — <evidence: test name, SQL query, code path> — <fix direction>
```

No finding without evidence. No finding without a file:line reference. No findings in freeform prose — the bullet format enables the implementer to act on each item independently without parsing paragraphs.

Two worked examples (a system-issue finding and a security finding) are in `references/review-conventions.md`.

## Gotchas

Headlines below; full explanations in `references/review-conventions.md`.

1. **Reviewer rewrites code in their head** — a review containing a corrected implementation is a code submission, not a review. Diagnose; the implementer treats.
2. **Style issues drown the report** — 40 nits bury 2 security findings. Delegate style to a linter; cap `## Minor` at 5.
3. **"Looks fine" — security still gets a section** — the `## Security` section is non-negotiable; write "no security issues found in scope" rather than omitting it.
4. **Reviewing without running tests** — the reviewer reads, does not run; mark run-required findings "unverified — implementer to reproduce by running `<cmd>`".
5. **Same finding in 5 places → consolidate** — one finding, all `file:line` locations.
6. **"I would have designed it differently" → design concern, not defect** — defect → `sdlc:code-implementer` (now); design concern → `sdlc:architect` (next iteration).
7. **Skipping `references/security.md` because "it's just a refactor"** — refactors expose secrets, disable CSRF, introduce Error Hiding. Run security unconditionally.
8. **Incoming claims are hypotheses, not evidence (FPF A.10)** — verify the load-bearing assertion against the source both ways (confirm the cited line exists and says so; `grep` for counter-evidence) before promoting or dismissing. Verify static claims against static source; do not run code (Gotcha 4).

## Integration with other plugins

- **`functional-clarity:functional-clarity`** — primary co-skill. Activate for the full 22-principle methodology when installed. If not installed, apply the Error Hiding, fail-fast, and contract discipline principles cited in the FPF check section above. Also apply Code-Change Discipline rule 7 (do not remove information).

- **`tdd-master:tdd-master`** — the reviewer checks "is there a test for this behavioral change?" A new or modified behavior without a covering test is a review item. Format: `"no test for <behavior> — implementer to add RED test per tdd-master:tdd-master workflow before merge."` The reviewer does NOT write the test — test authoring is implementer work, governed by `tdd-master`.

- **`planner:planner`** — the orchestrator dispatches this skill. The reviewer never invokes the planner back. If a finding implies a design change that cannot be fixed at the implementation level (e.g. a transaction boundary requiring a service-layer restructuring), record it as a design concern in the report and note "escalate to `sdlc:architect` via orchestrator." Do not improvise architecture decisions in the review.

- **`document-skills:frontend-design`** — for visual / UX review of frontend changes (design system compliance, spacing, typography, component composition), mention as an optional co-reference when installed. If not installed, graceful degrade: apply universal accessibility and visual-quality principles from `references/frontend-react.md`. `document-skills:frontend-design` is never required for this skill to function — it enhances review quality for frontend-heavy changes but is not a dependency.

**Co-activation order:** Load `references/security.md` unconditionally → activate `functional-clarity:functional-clarity` if installed → load stack references based on diff detection → optionally activate `document-skills:frontend-design` for frontend diffs. Do not alter this order. Security first, always.

This ordering ensures that even a partial review (stopped early) has produced the security output. Later sections (stack-specific, FPF) can be incomplete; the security section must be complete before any other section is started.

## When references are missing

If no stack-specific reference exists for the detected stack (Go, mobile, infrastructure, Terraform, SQL migrations, shell scripts, etc.) → apply universal review principles and note in the report header. Do not fail the review; do not invent stack-specific knowledge inline.

```
Stack: <detected> — no specific reference, universal principles applied
```

Universal principles applicable to any stack:

- **Error swallowing** is always a finding — regardless of language.
- **Secrets in code** are always a finding — regardless of language or context ("test fixture" is not an exemption).
- **Missing tests for behavioral changes** are always a finding — "there are no tests in this project" means the finding is "no tests exist; add them", not "skip the check."
- **Contract changes without documentation** are always a finding — a changed signature or return type affects callers who cannot be identified from this diff alone.

`references/security.md` is **required**. If the file does not exist at `plugins/sdlc/skills/code-reviewer/references/security.md`, the plugin installation is broken. Surface this as an error to the orchestrator; do not silently skip the security pass or substitute improvised security knowledge. A review without a security pass is not a review — it is a partial review presented as complete, which is worse than no review.

## Where to write

The reviewer has one writeable path:

- `<feature-dir>/review-request-changes/REVIEW-NN.md` — the review report, when a feature directory exists.

If no feature directory exists (e.g. reviewer was invoked on an ad-hoc diff), output the review report to chat. Do not create `REVIEW-NN.md` in an arbitrary location — only inside the feature directory.

The reviewer does **not** write to:
- The reviewed source files (reviewer reads, not edits).
- `<feature-dir>/PLANNER_EXECUTION.md` (that is the planner's artifact).
- The architecture document — `ARCHITECTURE.md`, `ARCH-NN.md`, or the project's own name from `planner-context.md` §5 (that is the architect's artifact).

One report per review round, not one file per finding: the `## Security` and `## Certification boundary` sections are properties of the round, and splitting the report loses them. The bullet format inside the report is what makes each finding an independent work item.

## Reference index

- `references/security.md` — **always loaded**, regardless of stack or diff size. OWASP Top 10 review checklist with grep patterns per category, secrets detection patterns, auth/authz review (IDOR, JWT pitfalls, missing decorators, session handling), injection vectors table, CSRF/CORS/CSP, SSRF. Non-optional; present in every review activation.

- `references/backend-python.md` — load when diff contains `*.py` files. Django security specifics (`mark_safe`, `raw()`, `extra()`), n+1 query detection and DRF nested serializer patterns, ORM pitfalls (`get_or_create` race, `bulk_create` bypass, `update()` signal skip, validators-on-`.create()`, nullable-unique `''`), transaction boundary rules (incl. counter/balance lost-update), re-runnable command idempotency, ASGI middleware & JWT-claim hazards, Error Hiding patterns in Python, type-safety and test quality review. Review angle only — no implementation patterns, no design decisions.

- `references/frontend-react.md` — load when diff contains `*.tsx` / `*.jsx` / `*.ts` / `*.vue` / `*.svelte` files. XSS vectors (`dangerouslySetInnerHTML`, `javascript:` scheme, `eval`), CSP violations, accessibility anti-patterns (`<div onClick>`, missing `alt`, unlabeled inputs, focus management), performance pitfalls (inline objects in JSX, overused `useMemo`), hooks anti-patterns (stale closures, missing cleanup, conditional hook calls), state management overengineering (incl. mixed state sources), form & rendering runtime pitfalls (tsc-clean, runtime-failing), type-safety and test quality review (incl. error-envelope mock fidelity). Review angle only — no implementation patterns, no design decisions.

- `references/review-conventions.md` — loaded on demand. Full Gotcha explanations, two worked finding examples, and the security-framing rationale (severity labels, non-web confirmation form, never-downgrade rule). SKILL.md keeps the headlines; this holds the detail.
