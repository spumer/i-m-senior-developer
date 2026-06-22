# code-reviewer — conventions & worked detail

> **Angle:** review only. Loaded on demand. `SKILL.md` keeps the headlines (the
> compact Gotcha list, the finding format, the security-framing essentials);
> this file holds the full gotcha explanations, two worked finding examples, and
> the security-framing rationale. Information lives here OR in SKILL.md, not both.

## Gotchas (full)

1. **Reviewer rewrites code in their head.** The impulse to write the "correct version" inline in the review report is an anti-pattern. A review that contains a complete corrected implementation is a code submission, not a review. The reviewer has incomplete context about surrounding constraints — the implementer knows which other callers exist, which tests would need updating, which invariants would break. The reviewer's job is diagnosis; the implementer's job is treatment.

2. **Style issues drown the report.** A report with 40 minor style items and 2 real security findings buries the security findings. The implementer opens the report, sees a wall of style nits, and mentally dismisses the whole thing. Configure a linter (ESLint, Ruff, Flake8). If no linter is configured, limit `## Minor` to 5 items and note "full style audit pending linter configuration." The reviewer's attention should be on system and security items only a human can find.

3. **"Looks fine" — security still gets a section.** The `## Security` section is non-negotiable. Write "no security issues found in scope" explicitly rather than omitting it. A missing section is indistinguishable from "reviewer forgot to check." The force-function of the always-present section is intentional — it signals to the implementer and any downstream auditors that the security pass was conscious, not accidental.

4. **Reviewing without running tests.** The reviewer reads code; the reviewer does not run the test suite during the review pass (that is the implementer's responsibility during the implementation phase). When a finding requires a test run to confirm reproduction — say so explicitly: "unverified — implementer to confirm by running `pytest tests/test_foo.py::test_bar`." Do not present unverified findings as confirmed; it wastes implementer time on false positives, and inflates the severity of the report.

5. **Same finding in 5 places → consolidate.** One finding with all `file:line` locations is cleaner and more actionable than 5 identical items. The pattern is the issue; enumerate all locations in one finding: "`file:a:10`, `file:b:44`, `file:c:7` — missing `transaction.atomic` on multi-step write — all three write sequences can produce partial state on failure." This makes it easy for the implementer to fix all instances in one commit.

6. **"I would have designed it differently" → design concern, not defect.** A defect means "code contradicts the existing design or its documented contract." A design concern means "the design itself could be better." They require different agents and different timelines: defect → `sdlc:code-implementer` (fix now, in the current PR); design concern → `sdlc:architect` via the orchestrator (address in a future design iteration). Misclassifying a design concern as a major defect inflates severity, routes to the wrong agent, and blocks a merge unnecessarily.

7. **Skipping `references/security.md` because the diff "is just a refactor."** Refactors that extract magic strings to named constants routinely expose hardcoded credentials. Refactors that restructure error handling introduce Error Hiding. Refactors that reorder middleware can silently disable CSRF protection. Refactors that rename functions can break the assumed calling convention in security-sensitive code. Run the security checklist unconditionally, every time, regardless of the apparent scope of the change.

8. **Incoming claims are hypotheses, not evidence (FPF A.10).** A finding handed to the reviewer, a PR/commit message ("tests pass", "lint clean"), a name that asserts `legacy`/`unused`, or an upstream agent's report carries no evidence by itself. Before promoting such a claim to a blocker — or dismissing it — the reviewer verifies the one load-bearing assertion against the source, both ways: confirm the cited `file:line` exists and says what the claim says (a phantom line drops the claim), and `grep` for counter-evidence that would falsify it (a "spec requires X" with zero hits was invented; a "missing ownership filter" may be enforced one frame up). When a self-reported "clean" conflicts with visible diagnostics, trust the diagnostics. The reviewer still does not run code (Gotcha 4) — it verifies static claims against static source.

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

## Security-framing rationale

`references/security.md` is the always-active checklist covering: OWASP Top 10 (current edition), secrets/credentials in code, auth/authz (IDOR, missing decorators, JWT pitfalls, session handling), injection vectors (SQL, template, shell, path traversal), CSRF/CORS/CSP, and SSRF. It loads regardless of stack, diff size, or apparent scope ("it's just a refactor" is the most common context for accidental secret exposure).

**Non-web confirmation form.** If the diff contains only non-web code (a CLI script, a data pipeline) and no security issues are found, still emit: "no security issues in scope — no web surface, secrets scan clean, no auth/authz changes." This three-element confirmation is more informative than the single-line form and proves each of the three major categories was checked.

**Severity rationale.** **critical** = exploitable now, no prerequisites (stop the merge immediately); **high** = exploitable with low effort (e.g. an authenticated user accessing other users' data); **medium** = requires prerequisites or chained vulnerabilities; **low** = defense-in-depth, not directly exploitable but weakens posture.

**Never downgrade for "it's internal" / "only admins reach it."** Internal services get breached; admin accounts get compromised. Security findings are assessed on exploitability, not on assumed access control.
