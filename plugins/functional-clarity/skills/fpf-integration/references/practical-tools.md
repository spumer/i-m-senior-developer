# FPF Practical Tools

> Операционные инструменты FPF для повседневной работы мультиагентных команд.
> Источник: FPF-Spec March 2026 (https://github.com/ailev/FPF)

## 1. USF/KDF/MDF/NOF — 4-Question Diagnostic

Before any decision or analysis — answer 4 questions:

| Question | What it checks | If no answer |
|----------|----------------|--------------|
| **USF** — What is the system? | Boundaries, components, stakeholders | Don't decide about what you don't understand |
| **KDF** — How good is my knowledge? | Evidence quality: source? how old? how complete? | Low quality knowledge = hypothesis, not fact |
| **MDF** — What is the best method? | Approach: analytics, experiment, best practice, expert judgment? | No method = chaotic action |
| **NOF** — What is my ultimate goal? | Why am I doing this? Connection to OMTM? | No goal = high risk of goal displacement |

**Apply:** before every session, before every DRR, before every experiment.

## 2. NQD — Alternative Generation Protocol

Not just "3 alternatives." NQD is a portfolio with metrics.

### Three Evaluation Axes

- **Novelty (N):** how new? 0 = repeats known, 1 = fundamentally different approach
- **Quality (Q):** how well does it solve the problem? Measured by decision criteria
- **Diversity (D):** how different from other alternatives in the portfolio?

### Portfolio Rules

1. **ParetoOnly:** only Pareto-incomparable options enter the portfolio (no one is worse on ALL criteria)
2. **ReferencePlane:** fix the comparison baseline (which criteria? which weights?)
3. **E/E-LOG (Explore/Exploit):** explicit policy — when to explore new vs exploit known

### Minimum Protocol (for each Complicated/Complex decision)

1. Generate >= 3 alternatives
2. Check Diversity: do alternatives really differ? (not "same thing, slightly different")
3. Evaluate each by N, Q, D
4. Remove Pareto-dominated (worse on all axes)
5. Present remaining to the project owner/lead with trade-offs

## 3. DRR — Design Rationale Record

Key difference from ADR: every piece of evidence carries `valid_until`.

### Template

```yaml
---
decision_id: "DEC-NNN"
title: "Brief description"
status: "proposed | accepted | superseded | deferred"
date_proposed: "YYYY-MM-DD"
proposed_by: "role"
decided_in_session: "session_id"
evidence_valid_until: "YYYY-MM-DD"
review_date: "YYYY-MM-DD"
alternatives_considered: N
kill_criteria: "Cancellation condition"
---
```

### Decay Mechanism

When `evidence_valid_until` expires — team must:
- Re-confirm decision with updated evidence, OR
- Explicitly issue waiver: "decision stands without fresh data because..."

### Required Body Sections

1. Context and problem
2. Alternatives (>= 3 for Complicated/Complex) with trade-offs
3. Decision and rationale with evidence chain
4. Evidence quality: strong / partial / weak
5. Consequences (expected + unexpected)
6. Rejected alternatives with reasons

## 4. Conformance Checklist — Pattern for Artifacts

Before publishing any artifact:

- [ ] **Completeness:** all required sections filled?
- [ ] **Evidence:** every claim backed by source (A.10)?
- [ ] **Scope:** artifact scope explicitly defined — what's in AND what's out (A.1.1)?
- [ ] **Terminology:** all terms match glossary (A.1.1)?
- [ ] **Alternatives:** for each choice, rejected alternatives documented (NQD)?
- [ ] **Decay:** review_date or staleness condition set?
- [ ] **Parsimony:** no duplication with other artifacts (A.11)?

## 5. Intellect Stack — 5 Cognitive Layers

Diagnostic map: which layer is the current discussion on?

```
5. Governance   — Who decides? How do we coordinate? (DRR, protocols, roles)
4. Strategy     — Why are we doing this? Connection to goal? (OMTM, phases, priorities)
3. Action       — What specifically are we doing? (artifacts, experiments, tasks)
2. Knowledge    — What do we know and not know? (evidence, assumptions, metrics)
1. Structure    — What is the system made of? (bounded contexts, roles, processes)
```

**Diagnostic:** if discussion stalls — check if all participants are on the same layer. Typical error: one talks Strategy, another talks Action.

## 6. Three FPF Application Modes

| Mode | Description | When to use |
|------|-------------|-------------|
| **Human-only** | FPF as reading/writing/review discipline | Small teams, no AI |
| **Mixed team** | FPF as coordination layer between humans and AI agents | Most multi-agent projects |
| **AI assistant** | FPF as loaded reference model for assistant | Single AI with FPF context |

## 7. Quick Start Path (FPF Onboarding)

For new team member:

```
A.0 (Glossary)  →  A.1-A.3 (Foundation)  →  B.3 (Assurance)  →  F.17 (UTS)  →  E.9 (DRR)
   "What is it"    "What it's made of"     "How to trust"    "Dictionary"    "Decisions"
```

For deep FPF work: use Grep + Read on FPF-Spec.md with offset/limit.
