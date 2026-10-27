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

**Always-active rule:** When reviewing any code, load `references/security.md` regardless of stack or apparent diff scope. This is non-negotiable. The single exception is Documentation mode below, which skips the OWASP walk-through and still emits the `## Security` section.

## Principles

1. **System issues over taste.** "I would name this differently" is not a review item. "This name says what it does, but the function does something else" is. Flag objective defects — correctness, safety, contract adherence. Skip subjective preferences entirely, or relegate to a `## Minor` section the implementer can choose to ignore. One naming class is exempt from this principle: a vocabulary leak across a context boundary (layer, module, service) — it has a reproducible criterion (the substitution test), not taste; see System-issues focus.

2. **Evidence per finding (FPF A.10).** Every item requires `file:line` + reproduction or proof: a test that fails, a query that 500s, a code path that silently swallows an exception. A finding without evidence is an opinion. Opinions do not belong in a review report. Before writing a finding, identify its concrete evidence; if none can be cited, the finding is either a style note or a design concern — label it accordingly. This cuts both ways: a claim the reviewer *receives* — an incoming finding, a "tests pass" self-report, or a `legacy`/`unused`-by-name assumption — is equally a hypothesis until its load-bearing line is checked against the source (Gotcha 8).

3. **Security always.** Load `references/security.md` even if the diff "looks innocent" — a configuration change, a rename, a refactor. Secrets and auth bugs slip in via innocuous-looking changes. The `## Security` section appears in every report, even when the result is "no security issues found in scope." The empty section is a force-function; its presence proves the check ran.

4. **FPF lens.** Apply Functional Clarity principles when reviewing. Key checks: Error Hiding (silently swallowed exceptions, defaults masking failures), fail-fast violations (validation deep in the call stack), contract changes without explicit discussion, leaked invariants. If `functional-clarity:functional-clarity` is installed, activate it for the full 22-principle set.

5. **Don't propose implementation.** Describe the issue and the fix direction. The implementer chooses and applies the concrete fix. Writing corrected code in the review inlines the reviewer's assumptions about the surrounding context — assumptions that may be wrong. The reviewer's job is diagnosis; the implementer's job is treatment.

6. **Operate on git-diff.** Review the change set, not the whole codebase. The scope of a finding is what changed. Cross-reference with `Read` and `Grep` to understand context when needed, but keep findings anchored to lines that exist in the diff. Reviewing the entire project when a 3-file diff was supplied is a scope error. Documentation mode widens this to the whole changed file — never to the project.

## Workflow

6-step pipeline, runs on every activation:

1. **Read input and settle the review target.** Every review runs in exactly one of two modes, and the mode is stated in the report header:

```text
commit-range:
  base: <commit-ish>
  head: <commit-ish>
  scope: <explicit paths or all>

working-tree:
  base: <commit-ish>
  scope: <explicit paths or all>
```

A PR number, a branch name, or a bare `<base>..HEAD` range normalizes to `commit-range`. A request to review the current uncommitted result — however it is worded — is `working-tree`: it compares the final file contents in the working tree against `base`, and it never requires a commit, a stash, or a separate `git worktree`. If neither mode can be settled → fail-fast: "need a review target: commit-range (base, head) or working-tree (base), plus scope; cannot proceed without one." If the request is ambiguous about which mode applies, stop and ask rather than guessing. Resolve a PR number to a base/head range with `git log` first.

2. **Collect the change set for the settled mode.** `commit-range` walks `git diff <base>..<head>`; it never picks up local uncommitted work. `working-tree` walks `git diff <base>` for tracked files — this is the final working-tree content, not an intermediate index state — and adds untracked files inside scope via `git ls-files --others --exclude-standard`. Ignored files are never added automatically. Deletions and both sides of a rename stay in the change set. Files outside the stated scope stay out of the review. The exact read-only recipe, including the empty and incomplete cases, is in `references/review-conventions.md`.

3. **Always load `references/security.md`.** No stack condition. Load it first, before stack detection. Run the security checklist as the first pass over the diff; Documentation mode narrows that pass. Record all security findings (or confirm "no issues") before moving to stack-specific checks. Do not defer security until after other checks — security findings block merge; stack findings are often advisory.

4. **Detect stack from changed files.** `*.py` files in diff → load `references/backend-python.md`. `*.tsx` / `*.jsx` / `*.ts` / `*.vue` / `*.svelte` in diff → load `references/frontend-react.md`. Both present in diff → load both references and apply both checklists. Unknown stack → apply universal principles (see §When references are missing below) and note in the report header.

5. **Walk the diff with loaded checklists.** Apply security checklist first, then FPF check (Error Hiding, fail-fast, contract), then stack-specific checklist. For each section of the diff: ask "what could go wrong here?", "is there a test for this behavior?", "does this change any contract silently?". If the diff implements a recognizable domain with a specialized skill installed, co-activate it read-only for a final pass — it finds a defect class the generic passes miss. The `Domain pass:` line of the Certification boundary records it either way: the skill named and activated, or `none available`. Reading a stack reference is not a domain pass, and a pass that did not run is never credited with findings. Classify each finding: major (blocks the current review), minor (advisory), security (always blocks the current review), design concern. A design concern has two axes: `blocks_current_review: false` and `blocks_plan_continuation: true`. It does not call the current diff defective, but the orchestrator must present it to the human before the next plan phase; never invoke an architect automatically. Consolidate duplicate findings — same pattern in multiple files becomes one item with all locations.

6. **Emit review report** per output format below, into the destination selected by the fork at the head of that section: the exact supplied `<feature-dir>/review-request-changes/REVIEW-NN.md` when the orchestrator supplies both that path and the compact return format, chat otherwise. Output must always use the structured template — no freeform prose in place of the template sections. The structured format enables the implementer to process each finding as an independent work item.

## Git-diff approach

Read-only commands, by mode. Mutating commands stay forbidden in both modes; the
full recipe with edge cases is in `references/review-conventions.md`.

```bash
# commit-range — overview, per-file diff, author intent
git diff <base>..<head> --stat -- <scope>
git diff <base>..<head> -- <path/to/file>
git log <base>..<head> --oneline

# working-tree — tracked final content against base, then untracked in scope
git status --porcelain=v1 -uall
git diff <base> --find-renames --stat -- <scope>
git diff <base> --find-renames -- <path/to/file>
git ls-files --others --exclude-standard -- <scope>
```

In `working-tree` an untracked file has no diff side: read it in full with `Read`
and review it as an added file. `git diff <base> -- <path>` already yields the
final content of a file that carries both staged and unstaged edits, so never
review `--cached` output as the result.

Additional tools for context:

- **`Read`** — load the full file when the diff context is insufficient to understand the surrounding code (e.g. checking whether a changed function is called elsewhere without ownership checks, or reading the full model to understand which fields can be null).
- **`Grep`** — search for patterns across the codebase (e.g. `grep -r "mark_safe" .` to find all usages, not just new ones in the diff; `grep -r "select_for_update" .` to confirm all usages are inside `atomic` blocks; `grep -r "SECRET_KEY" .` to check for leaked credentials).
- **`Glob`** — list files matching a pattern to understand project structure when context is needed (e.g. `plugins/sdlc/**/*.py` to understand how many Python files exist before deciding to load `backend-python.md`).

**Forbidden commands in review mode:** `git checkout`, `git reset`, `git add`, `git commit`, `git push`, `git stash`, `git apply`, `git merge`, `git rebase`. The reviewer never mutates reviewed source files, the index, or any branch; the sole permitted write is the exact report path supplied together with the compact return format.

Review of source is strictly read-only; writing the one permitted review report records the diagnosis without making the reviewer a co-author of the reviewed change.

If a finding requires running code to verify (e.g. confirming a race condition is observable), instruct the implementer: "unverified — implementer to reproduce by running `<command>`." The implementer confirms and reports back; the reviewer then updates the finding if the reproduction fails. The report's `## Certification boundary` section names, up front, the defect classes static review cannot certify — state them as a self-limitation; do not silently imply they were cleared.

## OWASP / security framing

`references/security.md` is always loaded — every activation, every stack, every diff size (Principle 3). The `## Security` section appears in every report: list findings as `file:path:line — <OWASP category> — <evidence> — <fix direction>`, or write exactly "no security issues found in scope". Severity labels: **critical** (exploitable now), **high** (low-effort, e.g. cross-user data access), **medium** (needs prerequisites/chaining), **low** (defense-in-depth). **Never downgrade a security finding for "it's internal" or "only admins reach it"** — assess on exploitability, not assumed access. Full rationale and the non-web confirmation form: `references/review-conventions.md`.

## FPF check (Functional Clarity)

Activate `functional-clarity:functional-clarity` for the full 22-principle methodology and bodies. Key checks the reviewer must surface, regardless of stack: **Error Hiding** (silently swallowed exceptions, defaults masking failures), **fail-fast violations** (validation deep in the call stack instead of at the entry boundary), **contract changes without migration** (changed signature/return-type/semantics for existing callers — Code-Change Discipline rule 6), **leaked invariants** (state assumptions not enforced in code), and **information removal** (removed log/comment/error without replacement — Code-Change Discipline rule 7). Code-Change Discipline ships with the `functional-clarity` plugin as `references/02-code-change-discipline.md`. Names only here; cite `functional-clarity:functional-clarity` for the bodies. The check runs on the entire diff regardless of language.

## System-issues focus

Categories the reviewer prioritizes, ordered by signal-to-noise ratio. Style is delegated to linter or listed last. Detail behind a category: `references/review-conventions.md`.

- **N+1 queries** — loops over querysets accessing related objects without `select_related`/`prefetch_related`; DRF nested serializers missing prefetch on the view queryset. Severity: critical on list endpoints, high on detail endpoints. See `references/backend-python.md` for Django-specific patterns.
- **Race conditions** — multi-step writes outside `transaction.atomic`, `get_or_create` without atomic wrapper, shared mutable module-level state in a web process.
- **Transaction boundaries** — any sequence of two or more writes (`save`, `create`, `update`, `delete`) that must succeed or fail together, without a wrapping atomic block.
- **Duplicated source of truth** — one predicate, constant or passage expressed twice instead of called from one owner. When the diff or its architecture document names an owner, `grep` it across the changed files and flag each re-derivation. Severity: major when the copies can silently diverge, minor for a documented mirror.
- **Error swallowing** — `except`/`catch` that consumes an error and returns success or a silent default. Invisible to monitoring; produces incorrect system state while appearing healthy.
- **Contract changes** — changed function signatures, return types, or behavior for existing callers without explicit documentation of the breaking change. For a schema, judge by backward compatibility, not exact equality: an added field, enum value or status code is safe; a changed type, a rename, a newly required request field, or an in-place mutation of a shared base is major — it breaks every consumer at once. A diverging error body is major only against an established envelope.
- **Vocabulary leak across a context boundary** — an element declared in
  context A is named in context B's vocabulary: the counterpart's action,
  mechanism, or domain term. Criterion — the substitution test: replace or add
  the counterpart; if the name, signature, or docstring becomes inaccurate, the
  finding is real. Look hardest where imports are clean. Exempt from Principle 1
  — reproducible criterion, not taste. Never names internal to one context, and
  never presentation-layer copy — button labels, operator-facing texts. Severity: major on public ports, events, signatures and
  schemas; minor in prose-only leaks. The three leak channels and the limits of
  the test: `references/06-boundary-vocabulary.md` of
  `functional-clarity:functional-clarity`.
- **Leaked secrets** — credentials, API keys, tokens in the diff. This includes test fixtures, comments, and URLs with embedded auth strings.
- **Missing migrations** — model or schema changes without a corresponding migration file. The migration is part of the change, not "to be added later."
- **Untested edge cases** — happy path is tested; negative paths, empty inputs, and permission boundaries are not. Flag each missing test case; the implementer adds them.
- **Test exercises the skip path, not the mechanism** — the suite is green, yet no test fails when the mechanism under change is deleted — the tests reach the result by a manual or skip path. Ask which test that would be. Severity: major when the diff adds the mechanism.
- **Object lifecycle / teardown** — manual `create`/`destroy` (init/dispose, subscribe/unsubscribe, mount/unmount) gets review regardless of apparent simplicity. Watch for orphan objects (never attached to the managed tree), a method called on an already-destroyed object, a non-null ref trusted as proof of liveness (guard on a liveness flag, not `!= null`), one-shot listeners surviving a skip/interrupt, and double-fired transition handlers. Severity: major on a live render/event path. Stack-neutral.
- **Incomplete sweep / partial migration** — the diff point-fixes one site of a defect class (hardcoded literal, missing auth check, un-migrated call site, renamed field) while identical sites remain. `Grep` the whole class; if others remain, format as "partial fix: N of M sites; remaining: `file:line`". For a project-wide invariant, recommend a scanning test (per `tdd-master:tdd-master`) over eternal manual audit. Severity: major if unswept sites are exploitable/user-visible, else minor.
- **Tracking IDs leaked into code** — `FEAT-XXXX`, issue numbers, or plan
  file names in code comments, docstrings, test names, or identifiers.
  These belong to artifact filenames in the feature directory; in code they
  are noise the team has to clean up. `Grep` the diff for the project's
  feature-id pattern. Severity: minor, but flag every occurrence.
- **Anglicism in a translated value** — latin words or dev jargon inside a user-facing translated string. Minor, advisory; route the wording to its owner rather than inventing one.
- **Comment hygiene** — comments that cite internal project docs (`see
  DESIGN §…`), carry change history (`since v2`, `no longer reads`), restate
  the adjacent line, or report the author's own work rather than address the
  next reader of the code. Normative text (smell classes, allowlist, borderline
  cases): skill `functional-clarity:comment-style`. `Grep` the comment lines;
  the allowlist in `references/review-conventions.md` — external standards,
  `TODO`, `FIXME`, `SAFETY:`, versioned-API markers — is not a finding, and
  wording that still explains current behaviour earns a present-tense rewrite,
  not deletion. Severity: minor; in a large diff report one finding with all
  locations. Distinct from the tracking-id bullet above — do not merge them.
- **Test runtime config diverges from prod** (stack-neutral) — tests run under a different runtime or concurrency config than production, so a prod-only failure stays green. Flag concurrency, parallel and shutdown code tested only under the harness default; require a run under the prod config.

**Severity triage:** Major findings block the current review and require a fix commit before re-review. Minor findings are advisory — the implementer decides whether to address them now or file a ticket. Design concerns never block the current review: record `blocks_current_review: false` and `blocks_plan_continuation: true`, so the orchestrator stops before the next plan phase and presents the concern to the human. The reviewer does not invoke an architect. Security findings at high or critical severity always block the current review; medium and low are advisory.

Style and naming: delegate to ESLint, Ruff, Flake8, or similar. If the project has a linter configured, add one line to the review: "style: delegated to linter." If no linter is configured, put style items in `## Minor` and keep the section to 5 items maximum.

## Stack detection (summary)

Stack is detected from the changed file extensions in the diff — not from project configuration. Detection is opportunistic (diff may not include config files):

| Signal in diff | Reference to load |
|---|---|
| `*.py` files | `references/backend-python.md` |
| `*.tsx`, `*.jsx`, `*.ts`, `*.vue`, `*.svelte` | `references/frontend-react.md` |
| Both present | Load both; apply both checklists |
| Only prose or prompt files, no executable code | Documentation mode below |
| Neither, executable code present | Universal principles; note in report header |

Mixed stack (Python + React in same diff): apply both checklists. Python-side findings go in `## Stack-specific / backend`, React-side findings go in `## Stack-specific / frontend`.

For stack-detection signals beyond the diff (detecting full project context), the master heuristic table lives in `plugins/planner/skills/planner/references/bootstrap.md` §4. The reviewer does not re-run bootstrap; it references it for context if needed.

## Documentation mode

With no executable code in the diff, skip the OWASP walk-through; still emit the `## Security` section and `grep` for secrets. Read each changed file end-to-end — Principle 6 widens to the changed files. One bounded exception: a changed document that proposes or argues for something is checked against the project's own record of settled decisions, even though that record is unchanged; a proposal reviewed without it reopens closed questions. Detail: `references/review-conventions.md`.

## Output format — review report

The report has two destinations of equal standing, and the call settles which one before any section is written:

- **Orchestrated** — the caller supplies both an exact review-report path and the compact return format: write the complete report to that exact path and return the compact summary below to chat.
- **Independent** — either input is absent: return the complete report to chat, whether or not a feature directory exists.

A supplied report path is the explicit request that the general rule against creating `*.md` files defers to; that path is normally already reserved as an empty file, so the write fills it rather than creating a file. Refusing to write it, or reporting the review blocked because report files may not be created, is a contract violation. Attempt the write. Report only a refusal the tool returned, quoted verbatim. An anticipated refusal is not a refusal.

Complete report template:

```markdown
# Review — <feature-id or branch name> (REVIEW-NN)

> **Mode:** commit-range | working-tree
> **Base:** `<commit-ish>` [**Head:** `<commit-ish>` — commit-range only]
> **Scope:** <explicit paths or all>
> **Reviewed files:** <every file reviewed; a deletion or rename names the side read>
> **Excluded:** <file — reason: out of scope | ignored | unchanged>
> **Commits:** <git log --oneline output, one line per commit; "none (working tree)" in working-tree mode>
> **Stack:** backend-python | frontend-react | mixed | documentation | unknown
> **References loaded:** security.md[, backend-python.md][, frontend-react.md]
> **Reviewed:** <ISO date>

## Summary
- Coverage: complete | empty | incomplete
- Major: N
- Minor: N
- Security: N (or "no issues found in scope")
- Design concerns: N

## Security
<!-- Always present. "no security issues found in scope" if clean. -->
- `file:path:line` — <OWASP category> — <evidence/reproduction> — <fix direction>

## System issues
<!-- N+1, races, transactions, error-swallow, contract changes, missing migrations. A design concern is recorded here with `blocks_current_review: false` and `blocks_plan_continuation: true`. -->
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
them for runtime/human verification; do not record them as cleared. In Documentation mode say so here: the OWASP walk-through did not run, only a secrets grep.
Domain pass: <named skill, activated> | none available

## Hand-off
Next: `sdlc:code-implementer` to apply fixes for all major and security items.
Design concerns (if any): the orchestrator presents them to the human before the next plan phase; no architect is invoked automatically.
```

### Orchestrated report hand-off

Orchestrated mode writes the complete report above to the supplied path and
returns this compact summary to chat in its place; do not duplicate the
complete report there. The rules in the rest of this section govern this mode.

```text
Status: clean | changes-requested
Report: <path> | chat (no feature directory)
Coverage: complete | empty | incomplete
Findings: major N; minor N; security N; design N
Blocking: N
Certification boundary: <what static review does not certify>
Summary: <prose of at most 1200 characters>
```

`Coverage` is independent of `Status`: `complete` means every file of the settled
target was reviewed, `empty` means the target contains no change at all, and
`incomplete` means at least one file of the target was not reviewed — name those
files in the report. `Status: clean` states only that no finding was raised; it
never asserts coverage, and `empty` or `incomplete` is never reported as a
reviewed-clean result.

`Blocking` counts only findings that block the current review. A nonzero
`design` count separately means `blocks_plan_continuation: true`, even when
`Status` is `clean`. The 1200-character limit applies only to `Summary`. Use
`Report: chat (no feature directory)` only when the orchestrator explicitly
states that condition.

If the orchestrator explicitly states in the same call that a complete correct
report already exists at the supplied path and requests only a corrected compact
summary, return that summary without writing, replacing, deleting, or renaming
the report file. This exception applies only to that form-only correction.

Before writing a complete report, inspect the supplied path. If it contains a
nonempty file, do not overwrite it unless the orchestrator explicitly states
in this same call that the file is an unfinished review report from this role
and that replacing it is expected. In every other occupied-path case, return
the exact chat line `Целевой путь занят: <путь>` with the actual path, followed
by a short explanation of what was found there. Do not return the ordinary
compact summary or choose another path yourself. Do not delete, rename, or
overwrite a file owned by another role: the orchestrator owns path selection
and numbering.

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
6. **"I would have designed it differently" → design concern, not defect** — defect → `sdlc:code-implementer` (now); design concern does not block the current review, but stops plan continuation for a human decision. Do not invoke `sdlc:architect` automatically.
7. **Skipping `references/security.md` because "it's just a refactor"** — refactors expose secrets, disable CSRF, introduce Error Hiding. Run security unconditionally.
8. **Incoming claims are hypotheses, not evidence (FPF A.10)** — verify the load-bearing assertion against the source both ways (confirm the cited line exists and says so; `grep` for counter-evidence) before promoting or dismissing. Verify static claims against static source; do not run code (Gotcha 4).

9. **An already-decided class, and the twin out of scope** — state the contrast with the prior decision, or drop the finding; a twin defect out of scope is its own finding with its own `file:line`.

## Integration with other plugins

- **`functional-clarity:functional-clarity`** — primary co-skill. Activate for the full 22-principle methodology when installed. If not installed, apply the Error Hiding, fail-fast, and contract discipline principles cited in the FPF check section above. Also apply Code-Change Discipline rule 7 (do not remove information).

- **`tdd-master:tdd-master`** — the reviewer checks "is there a test for this behavioral change?" A new or modified behavior without a covering test is a review item. Format: `"no test for <behavior> — implementer to add RED test per tdd-master:tdd-master workflow before merge."` The reviewer does NOT write the test — test authoring is implementer work, governed by `tdd-master`.

- **`planner:planner`** — the orchestrator dispatches this skill. The reviewer never invokes the planner back. If a finding implies a design change that cannot be fixed at the implementation level (e.g. a transaction boundary requiring a service-layer restructuring), record it as a design concern with `blocks_current_review: false` and `blocks_plan_continuation: true`. The orchestrator presents it to the human; do not invoke `sdlc:architect` automatically or improvise an architecture decision in the review.

- **`document-skills:frontend-design`** — one instance of the domain pass (Workflow step 5): visual and UX review of frontend changes. Optional; when it is not installed, `references/frontend-react.md` carries the accessibility and visual-quality angle.

**Co-activation order:** Load `references/security.md` unconditionally → activate `functional-clarity:functional-clarity` if installed → load stack references based on diff detection → optionally activate `document-skills:frontend-design` for frontend diffs. Do not alter this order. Security first, always.

Even a partial review then carries its security output: later sections (stack-specific, FPF) may be incomplete, the security section must be complete before any other is started.

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

The reviewer has one writeable path: the exact `<feature-dir>/review-request-changes/REVIEW-NN.md` supplied by the orchestrator together with the compact return format. Writing it is the contract, not an optional extra — see the fork at the head of §Output format. Do not create `REVIEW-NN.md` in an arbitrary location; without both inputs the complete report goes to chat.

The reviewer does **not** write to:
- The reviewed source files (reviewer reads, not edits).
- `<feature-dir>/PLANNER_EXECUTION.md` (that is the planner's artifact).
- The architecture document — `ARCHITECTURE.md`, `ARCH-NN.md`, or the project's own name from `planner-context.md` §5 (that is the architect's artifact).

One report per review round, not one file per finding: the `## Security` and `## Certification boundary` sections are properties of the round, and splitting the report loses them. The bullet format inside the report is what makes each finding an independent work item.

## Reference index

- `references/security.md` — **always loaded**, regardless of stack or diff size. OWASP Top 10 review checklist with grep patterns per category, secrets detection patterns, auth/authz review (IDOR, JWT pitfalls, missing decorators, session handling), injection vectors table, CSRF/CORS/CSP, SSRF. Non-optional; present in every review activation.

- `references/backend-python.md` — load when diff contains `*.py` files. Django security specifics, n+1 and DRF serializer patterns, ORM pitfalls, transaction boundary rules, command idempotency, ASGI middleware and JWT-claim hazards, Error Hiding in Python, type-safety and test quality. Review angle only — no implementation patterns, no design decisions.

- `references/frontend-react.md` — load when diff contains `*.tsx` / `*.jsx` / `*.ts` / `*.vue` / `*.svelte` files. XSS vectors, CSP violations, accessibility anti-patterns, performance pitfalls, hooks anti-patterns, state management overengineering, form and rendering runtime pitfalls, type-safety and test quality. Review angle only — no implementation patterns, no design decisions.

- `references/review-conventions.md` — loaded on demand. Full Gotcha explanations, two worked finding examples, the security-framing rationale, Documentation mode in full, and the two system-issue categories whose exemption lists live here. SKILL.md keeps the headlines; this holds the detail.
