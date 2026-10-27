# code-reviewer — conventions & worked detail

> **Angle:** review only. Loaded on demand. `SKILL.md` carries what is needed to
> judge a diff without opening this file — the rule, the criterion, the short form
> of each exemption. This file carries the full shape behind them: the read-only
> recipe for settling a review target, the complete gotcha explanations, the
> categories mined from past reviews with their whole exemption lists,
> Documentation mode in full, two worked finding examples, and the
> security-framing rationale. Where both name the same rule, SKILL.md is the
> short form and this file is the long one; neither is a copy of the other, and a
> list that exists in both is a defect to close, not a convention.

## Review target — read-only recipe

The skill settles one of two modes; this section is the exact recipe for each,
including the cases that make a review silently partial.

**Checking the target before reading anything.** Resolve every ref first:
`git rev-parse --verify <base>^{commit}` and, in `commit-range`, the same for
`<head>`. A ref that does not resolve stops the review with the failed ref
named; never substitute a different ref. An empty or unparsable scope stops the
review the same way. Scope is a list of explicit paths or the word `all`.

**`commit-range`.** The change set is exactly `git diff <base>..<head>`, limited
to scope. Local uncommitted work is not part of it: a file dirty in the working
tree is reviewed at its committed content, and an untracked file is not in the
review at all. Use `git log <base>..<head> --oneline` for author intent.

**`working-tree`.** The change set is the final content of the working tree
against `base`:

```bash
git status --porcelain=v1 -uall                          # the whole picture, including untracked
git diff <base> --find-renames --stat -- <scope>         # tracked files, final content
git diff <base> --find-renames -- <path>                 # per-file detail
git ls-files --others --exclude-standard -- <scope>      # untracked inside scope
```

- A file with both staged and unstaged edits is reviewed at its working-tree
  content. `git diff <base> -- <path>` already yields that; `--cached` yields the
  intermediate index state and is never the review subject. The split may be
  worth one finding about what a commit would capture, but it does not change
  which content is reviewed.
- Untracked files inside scope are part of the review as added files. They have
  no diff side, so read each one in full with `Read`.
- Ignored files are outside the change set: they are never added automatically,
  their content is not read, and a review does not certify them. They enter the
  review only when the caller names a path in scope explicitly.
- Deletions are reviewed as deletions: anchor a finding about removed code as
  `old/path.py:line (base)`, since the line exists only on the base side.
- Both sides of a rename stay in the review: `--find-renames` names the old and
  the new path, and content changes carried by the rename are reviewed on the
  new path.
- For both, the `Reviewed files` entry says which side was read — «deleted,
  reviewed on the base side», «renamed, both sides». A bare «deleted» or
  «renamed» leaves the reader unable to tell a reviewed deletion from a noticed
  one, and the finding list is not where that question is answered: a deletion
  with no finding then looks identical to a deletion nobody opened.
- Files inside scope that are unchanged against `base` are not findings-bearing
  material; list them as excluded with the reason `unchanged`.

**Coverage.** The report states `Coverage` independently of `Status`:

| Value | When |
|---|---|
| `complete` | every file of the settled target was reviewed |
| `empty` | the target contains no change at all |
| `incomplete` | at least one file of the target was not reviewed — name them |

`Status: clean` means no finding was raised. It never means the target was fully
covered, and `empty` or `incomplete` is never presented as a reviewed-clean
result. An unreadable file, a binary blob, or a file skipped for size makes the
review `incomplete` and each such file is named.

All three values describe a target that was settled. A review stopped before
that — an unresolvable ref, an unparsable scope — has no target to describe, so
it asserts no `Coverage` at all: the report says the target was not settled,
names the ref or scope that failed, and stops. Writing `empty` there claims the
target holds no change, and `complete` claims it was reviewed; both are false,
and `incomplete` still implies a target exists. If the caller asked for a
`Coverage` line, answer it with `not settled — <failed ref>` rather than
borrowing a value that asserts something the review never established.

**Allowed commands** in both modes: `git rev-parse`, `git status`, `git diff`,
`git log`, `git show`, `git ls-files`, `git cat-file`, plus `Read`, `Grep` and
`Glob`. **Forbidden** in both modes: `git checkout`, `git reset`, `git add`,
`git commit`, `git push`, `git stash`, `git apply`, `git merge`, `git rebase`,
`git mv`, `git rm`, and `git worktree`. A `working-tree` review never needs a
commit, a stash or a second worktree to become possible; if a review appears to
require one, the target was settled wrongly — stop and say so.

## Gotchas (full)

1. **Reviewer rewrites code in their head.** The impulse to write the "correct version" inline in the review report is an anti-pattern. A review that contains a complete corrected implementation is a code submission, not a review. The reviewer has incomplete context about surrounding constraints — the implementer knows which other callers exist, which tests would need updating, which invariants would break. The reviewer's job is diagnosis; the implementer's job is treatment.

2. **Style issues drown the report.** A report with 40 minor style items and 2 real security findings buries the security findings. The implementer opens the report, sees a wall of style nits, and mentally dismisses the whole thing. Configure a linter (ESLint, Ruff, Flake8). If no linter is configured, limit `## Minor` to 5 items and note "full style audit pending linter configuration." The reviewer's attention should be on system and security items only a human can find.

3. **"Looks fine" — security still gets a section.** The `## Security` section is non-negotiable. Write "no security issues found in scope" explicitly rather than omitting it. A missing section is indistinguishable from "reviewer forgot to check." The force-function of the always-present section is intentional — it signals to the implementer and any downstream auditors that the security pass was conscious, not accidental.

4. **Reviewing without running tests.** The reviewer reads code; the reviewer does not run the test suite during the review pass (that is the implementer's responsibility during the implementation phase). When a finding requires a test run to confirm reproduction — say so explicitly: "unverified — implementer to confirm by running `pytest tests/test_foo.py::test_bar`." Do not present unverified findings as confirmed; it wastes implementer time on false positives, and inflates the severity of the report.

5. **Same finding in 5 places → consolidate.** One finding with all `file:line` locations is cleaner and more actionable than 5 identical items. The pattern is the issue; enumerate all locations in one finding: "`file:a:10`, `file:b:44`, `file:c:7` — missing `transaction.atomic` on multi-step write — all three write sequences can produce partial state on failure." This makes it easy for the implementer to fix all instances in one commit.

6. **"I would have designed it differently" → design concern, not defect.** A defect means "code contradicts the existing design or its documented contract." A design concern means "the design itself could be better." They require different agents and different timelines: defect → `sdlc:code-implementer` (fix now, in the current PR); design concern → `sdlc:architect` via the orchestrator (address in a future design iteration). Misclassifying a design concern as a major defect inflates severity, routes to the wrong agent, and blocks a merge unnecessarily.

7. **Skipping `references/security.md` because the diff "is just a refactor."** Refactors that extract magic strings to named constants routinely expose hardcoded credentials. Refactors that restructure error handling introduce Error Hiding. Refactors that reorder middleware can silently disable CSRF protection. Refactors that rename functions can break the assumed calling convention in security-sensitive code. Run the security checklist unconditionally, every time, regardless of the apparent scope of the change.

8. **Incoming claims are hypotheses, not evidence (FPF A.10).** A finding handed to the reviewer, a PR/commit message ("tests pass", "lint clean"), a name that asserts `legacy`/`unused`, or an upstream agent's report carries no evidence by itself. Before promoting such a claim to a blocker — or dismissing it — the reviewer verifies the one load-bearing assertion against the source, both ways: confirm the cited `file:line` exists and says what the claim says (a phantom line drops the claim), and `grep` for counter-evidence that would falsify it (a "spec requires X" with zero hits was invented; a "missing ownership filter" may be enforced one frame up). When a self-reported "clean" conflicts with visible diagnostics, trust the diagnostics. The reviewer still does not run code (Gotcha 4) — it verifies static claims against static source.

## Categories added from mined review practice

### Test runtime config diverges from prod

Three shapes of the same divergence, all observed:

- a test runner that auto-cleans pending work while the production runner is
  long-lived, so a task never drained in production looks drained in the suite;
- test parallelism flags that mask a leak in shared or singleton state, because
  each worker gets its own copy of what production shares;
- a test configuration or middleware stack thinner than production, so a layer
  that only exists in production is never exercised.

The common root: the suite proves the code works under the test runtime, and
that is a different system from the one the users run. This is why the category
is stack-neutral — it is a property of the harness, not of a language.

### Duplicated source of truth

The defect is one predicate, constant, list or passage expressed in two places
instead of called from one owner. Two copies have no mechanism keeping them in
step: the next edit touches one of them, and the system now holds two
contradictory truths with nothing raising an error. This is among the most
missed categories precisely because each copy reads as locally correct — a clean
diff per file does not prove a clean diff across files.

Detection has a precondition: an owner must be declared somewhere the reviewer
can see — in the diff itself, or in the architecture document if one was
supplied. The reviewer does not go hunting for design documents it was not
given. When an owner is declared, `grep` its name across the changed files; a
render or call path that re-expresses the predicate instead of calling the owner
is the finding.

The category covers code — a boolean re-derived at each call site — and content
alike: a forbidden-strings list, a command specification, a configuration table
copied across documents. Evidence names the owner's location and every duplicate
`file:line`. Fix direction: call the owner, or replace the copy with a
cross-reference to the single canonical place. Severity: major when the copies
can silently diverge, minor when one is a documented mirror carrying an explicit
cross-link.

### Contract compatibility for a schema diff

The reviewer's question is not «did the schema change» but «does the change
break an existing consumer». Safe, and not a blocker on its own: adding a
response field, adding an enum value, adding a status code, weakening a required
response field to optional, extending a base schema while the base itself stays
untouched. Breaking, and major: changing a field's type, renaming a field,
strengthening a request field from optional to required, removing a required
field, and mutating a shared base schema's required fields in place — the last
one breaks every consumer of that base at once, and an honest note in a design
document does not make it non-breaking. Name the consumer count in the finding.

The error envelope needs care, because the reviewer often cannot see the
canonical shape: it is chosen by the architect and lives in a reference the
reviewer does not load. So the rule is conditional. If a canonical envelope is
established — stated in the supplied architecture document, or observable as the
existing convention across the endpoints in scope — a diverging 4xx/5xx body is
major, and the fix direction worth naming is that one global handler usually
closes all of them. With no established envelope visible, flag only
inconsistency the diff introduces within itself. Do not assert a blocker against
a shape you cannot see.

Keep the finding diagnostic. «Breaks the consumers of the shared base; fix
without mutating the base's required fields in place» is diagnosis. Naming the
subclass to write is treatment, and treatment belongs to the implementer.

### Domain pass

The generic security and system pass and a targeted domain pass find
non-overlapping defects — that is the whole reason for a second read. Observed
instances: a generic pass missed a tool-annotations gap and an undiscoverable
docstring example in protocol-server code that a targeted pass found; on a
document-heavy change, content fidelity, cross-file drift and reader
comprehension each surfaced a different defect class, of which cross-file drift
was the richest.

Triggers are not a closed list. A rendered interface surface, a protocol server,
a prose-heavy artifact are the three seen so far. The test is whether the diff
implements a recognizable domain for which a specialized skill is installed. If
none matches, the generic pass is sufficient and nothing needs to be said about
it: a missing domain pass has never been observed as a silent failure, so it
carries no force-function of its own.

Findings from the domain pass go in `## Stack-specific` with the same evidence
discipline as any other. The pass is read-only, like the rest of the review: the
domain skill's fixes are not written here.

### An already-decided class, and the twin outside the scope

Two report rules that share one root — a finding is only useful when its
addressee can act on it.

A finding that resembles a pattern the project has already adjudicated — a
recorded decision, a documented guard, a previously rejected shape — must state
the contrast inside the finding: it resembles that decision, and differs in
this. If the difference cannot be articulated, the finding is most likely the
settled case resurfacing, and it is downgraded or dropped. Without this, a
review reopens closed questions and the team learns to discount its findings.

The rule cuts both ways, and the second direction is the one a diff hides. When
the change under review is itself a proposal — a document arguing that the
project should adopt something — the settled record is where the answer already
lives, and it is almost never in the diff. Look for it beside the changed
document: a decisions file, an architecture record, a rejected-alternatives
section. Having found it, the report either names how the new argument differs
from the one already weighed, or says plainly that no new argument is offered
and the proposal restates a closed case. Reviewing such a proposal purely on its
merits, with the prior decision unread, is the failure this rule exists to
prevent: it reads as endorsement and costs the team the decision it already
paid for.

A twin defect — the same bug found in a module outside the review scope while
examining the one inside it — is recorded as its own finding, with its own
`file:line`, never appended to the in-scope item. The reviewer writes no code,
so «file it» means emitting a distinct item the orchestrator can route as its
own task. Folded into an unrelated finding, it is either lost or it silently
widens the scope of someone else's fix.

### Test exercises the skip path, not the mechanism

The detail for this category deliberately lives elsewhere: in the «Test quality
review» sections of `references/backend-python.md` and
`references/frontend-react.md`, beside its peers — the mock asserted instead of
the system, the snapshot with no behavioural assertion, the test that bypasses
the production chain. Those are all about a test that proves less than it looks
like it proves, and this one belongs with them rather than here.

### Anglicism in a translated value

When the diff touches a user-facing string catalogue, scan the translated values
for latin words inside non-latin text and for untranslated developer jargon.
Each hit is a term the reader of the interface will not understand.

Severity is minor and the finding is advisory, for two reasons. The choice of
wording belongs to whoever owns the product vocabulary, not to the reviewer —
so the fix direction is to route it there, never to invent a replacement. And
the scan produces honest false positives: brand names, unit abbreviations,
markup tags and identifiers quoted inside a message are all latin by necessity.
Report the hits as candidates, grouped into one finding, not as defects.

## Documentation mode in full

The mode turns on by absence: the diff carries no executable code — only prose,
prompt files, documentation, configuration comments. Two things change, and
nothing else does.

**The security pass narrows, it does not disappear.** Prose has no injection
surface and no auth surface, so walking the OWASP checklist over it produces
non-applicable findings that bury the real ones. Skip the walk-through. Keep the
`## Security` section — its emptiness is the proof the question was asked — and
keep grepping for secrets: a credential pasted into a README is a finding like
any other. If the diff also touches executable code, the mode does not apply and
the full checklist runs.

**The unit of reading becomes the file, not the hunk.** A prose defect lives in
the relationship between sections: a term redefined halfway down, a paragraph
duplicated, a cross-reference that now points nowhere, a caveat deleted without
a replacement. None of these is visible in a hunk, because each needs both ends
at once. Read every changed file end-to-end before reporting. This is a
deliberate exception to Principle 6, and it is bounded: the whole changed file
is in scope, the rest of the project is not.

Everything else stays as it is. Findings still carry `file:line` evidence
(Principle 2). Information removed without replacement is already a finding
under the FPF check, and so is a term that silently changes meaning across the
artifact. Wording preferences remain `## Minor`.

## Two system-issue categories in full

SKILL.md carries the rule, the criterion and the short form of the exemptions for
these two — enough to judge a diff without opening this file. What lives here is
the full shape: every leak channel, every allowlist entry, and the pointer to the
normative text in `functional-clarity`.

### Vocabulary leak across a context boundary

An element declared in context A — port, method, parameter, event name, schema
field, docstring — is named in context B's vocabulary: the counterpart's action,
its mechanism, or its domain term. Shapes seen in real diffs:
`InvoiceEmailQueuePort.enqueue_email`, `emit("trigger_welcome_email")`, a
`queue=` or `retry=` parameter on an abstract port, a port docstring that points
into the subscriber's internals.

The boundary can be a layer, a module, or a service — the criterion is the same
at every scale, and the leak travels through any of three channels: the name,
the type or signature, the prose. Criterion: the substitution test — replace or
add the counterpart behind the boundary; if the name, signature, or docstring
becomes inaccurate, the finding is real.

Check hardest where imports are clean: an inverted dependency is the blind spot
of structural analysis, because nothing structural stops B's words from entering
A's names.

Do not flag names internal to one context, and do not flag presentation-layer
copy — button labels and operator-facing texts. Severity: major on public ports,
events, signatures and schemas, because the leak couples the evolution of two
contexts; minor when the leak is prose only, in a docstring or comment.

This category is explicitly exempt from Principle 1: the substitution test is a
reproducible criterion, not a naming preference. Normative text — leak channels,
per-scale examples, ❌/✅ pairs, false positives:
`functional-clarity` `references/06-boundary-vocabulary.md`.

### Comment hygiene

Four smells, all of which state nothing the code cannot express and all of which
grow the cognitive load of the next reader:

- a citation of an internal project document — `see DESIGN §…`, `per PLAN §2.4`;
- change history carried in the source — `no longer reads`, `— unchanged`,
  `since v2`, `RED→GREEN`;
- a restatement of the adjacent line — `// increment counter`;
- a report of the author's own work, written for whoever reviewed the change
  rather than for whoever reads the code later — `took a dict instead of the
  plan's list`, `left this untouched to keep tests green`. That belongs in the
  commit message.

Known false positives — do not flag: external standards (`RFC 7231`, `PEP 8`);
versioned-API documentation conventions (`.. versionadded::`, `@since`);
`TODO`, `FIXME` and `SAFETY:` lines; and changelog-looking wording that in fact
explains current behavior. For the last one, apply the subtraction test: if
dropping the reference to the past leaves a useful statement, suggest a
present-tense rewrite instead of deletion.

`Grep` the diff's comment lines. Severity: minor. In a large diff, report one
finding with the list of locations rather than one finding per line. This
category is distinct from tracking identifiers leaked into code — that one
covers the project's feature-id pattern — and the two are not merged.

Normative text — smell classes, the allowlist, borderline cases:
skill `functional-clarity:comment-style`.

## Worked finding examples

Both follow the mandatory finding format: `` `file:path:line` — <issue> — <evidence> — <fix direction> ``.

**Well-formed finding (major, system issue):**

```
`services/order.py:47` — missing transaction.atomic on multi-step write — evidence: lines 47-52
create two records sequentially with no atomic wrapper; if the second save raises IntegrityError the
first record is committed (partial state) — fix direction: wrap lines 47-52 in
`with transaction.atomic():`
```

**Well-formed finding (security, high):**

```
`api/views.py:112` — IDOR via user-supplied pk — A01 Broken Access Control — evidence: line 112
`Order.objects.get(pk=request.GET['order_id'])` with no ownership filter; any authenticated user
can fetch any order by changing the ID — fix direction: add `.filter(user=request.user)` before .get()
```

**Well-formed finding (major, vocabulary leak across a context boundary):**

```
`billing/ports.py:14` — vocabulary leak across a context boundary — evidence: port declared in
`billing` is named `InvoiceEmailQueuePort.enqueue_email(invoice_id, queue="notifications")`:
"email" is the subscriber's action, "queue" its mechanism, the `queue` parameter its tuning knob;
substitution test fails — swapping the subscriber to a push channel makes the name and signature
inaccurate although nothing in `billing` changes behavior — fix direction: rename to the owner's
fact (e.g. `InvoiceObserverPort.invoice_created(invoice_id)`) and drop the subscriber parameters
```

Note the evidence: it is the failed substitution test, not "I dislike the name" — that is what
moves the finding out of taste and into the system-issues section.

## Security-framing rationale

`references/security.md` is the always-active checklist covering: OWASP Top 10 (current edition), secrets/credentials in code, auth/authz (IDOR, missing decorators, JWT pitfalls, session handling), injection vectors (SQL, template, shell, path traversal), CSRF/CORS/CSP, and SSRF. It loads regardless of stack, diff size, or apparent scope ("it's just a refactor" is the most common context for accidental secret exposure).

**Non-web confirmation form.** If the diff contains only non-web code (a CLI script, a data pipeline) and no security issues are found, still emit: "no security issues in scope — no web surface, secrets scan clean, no auth/authz changes." This three-element confirmation is more informative than the single-line form and proves each of the three major categories was checked.

**Severity rationale.** **critical** = exploitable now, no prerequisites (stop the merge immediately); **high** = exploitable with low effort (e.g. an authenticated user accessing other users' data); **medium** = requires prerequisites or chained vulnerabilities; **low** = defense-in-depth, not directly exploitable but weakens posture.

**Never downgrade for "it's internal" / "only admins reach it."** Internal services get breached; admin accounts get compromised. Security findings are assessed on exploitability, not on assumed access control.
