# Mode 1 — Architecture planning

Detailed mechanics for the architecture-planning mode of the planner skill. `SKILL.md` ("Mode 1 — architecture planning") routes here when the input is a feature README that does not yet have an architecture document.

## 1. When to load

Load this reference when the planner is invoked with a feature `README.md` as input and no `*-PLAN-*.md` / `*-DESIGN-*.md` / `ARCHITECTURE.md` exists yet inside the feature directory. Architecture mode answers a single question: **how should the architecture pass be conducted to be efficient and rentable?**

If an architecture document already exists, do **not** load this reference — load `execution-mode.md` instead.

## 2. Inputs and exit criterion

- **Input:** `<feature-dir>/README.md` (the feature spec). The feature-directory pattern comes from `planner-context.md` §5.
- **Exit:** a written `<feature-dir>/PLANNER_OUTPUT.md` that proposes how to run the architecture phase. If no feature directory was found (e.g. `/plan` was invoked with free-text task description), the output goes to chat instead — see `SKILL.md` ("Where to write").

The exit criterion is a **plan**, not architecture. This reference does not produce architecture itself; it picks the agents / models / parallelism for the phase that will produce architecture.

## 3. Option matrix

Pick one of the four options below. They are mutually exclusive within a single feature, although different features can use different options.

1. **Single architect on Opus.** Choose when the feature is monolithic with strong coupling between modules — e.g. a refactor that touches one core domain end-to-end, or an algorithmic redesign where every decision affects every module. Opus's deeper reasoning earns its cost when the integration surface is wide.
2. **N parallel sub-architects on Sonnet (N ≤ 4).** Choose when the feature splits cleanly into weakly coupled domains — e.g. backend / frontend / DB / security tracks for a CRUD feature. The integration cost between sub-architects is low because each owns a separate slice; LIFT-COT caps N at 4 to keep the integration phase manageable. Default model is Sonnet (sufficient for routine domain work) unless one sub-track is itself security-critical (then that sub-track gets Opus).
3. **Single quick-pass on Haiku.** Choose when the feature is small: <200 LOC impact, single module, no DB migrations, no new endpoints, no new dependencies. Haiku's speed and cost win when the work is bounded; Sonnet would be overkill.
4. **Separate security sub-plan.** Choose **in addition to** options 1-3 (it is an add-on, not a substitute) when the feature touches authentication, authorization, PII, secrets, or data-export paths. The security sub-plan runs as its own phase with explicit review gates — it is never an inline "and also" item inside another architect's phase.

## 4. Decision rules

- **Default = single Sonnet architect.** Do not escalate to Opus or split into N agents on a guess. Per FPF A.11 (Ontological Parsimony), add only what you cannot subtract. The default covers ~80% of architecture work.
- **Escalate to Opus only with evidence.** Evidence for "Opus needed" looks like: the feature touches a security-sensitive core, the feature requires a non-standard algorithm or data structure, or the team has historical lessons (logged in `planner-context.md` §6 by `/plan-reflect`) that Sonnet was weak on this kind of task in this project.
- **Split into N sub-architects only with evidence of decoupling.** Evidence for "decoupled enough to parallelize" looks like: distinct domains with clear interface contracts already drafted in the README, separate code-ownership areas, no shared mutable state across the proposed slices. If you have to invent the boundaries to parallelize — don't parallelize.
- **Down-shift to Haiku only with concrete bounds.** "<200 LOC impact, 1 module, no migrations" is a hard threshold, not a vibe — count the files in the README. If the README is ambiguous about scope, default to Sonnet, not Haiku.

## 5. Output mapping

The chosen option fills the "Phase X" blocks of `PLANNER_OUTPUT.md` per the template in `SKILL.md` ("Output format"). Specifically:

- **Option 1 (single Opus architect):** one phase, one agent line, model `opus`, focus = "produce architecture document".
- **Option 2 (N parallel Sonnet sub-architects):** one phase tagged `parallel`, N agent lines (N ≤ 4), each with its domain in `Focus`. Add a follow-up phase tagged `serial, depends on Phase 1` for integration / consolidation of the sub-architectures into a single document.
- **Option 3 (single Haiku quick-pass):** one phase, one agent line, model `haiku`, focus = "lightweight architecture pass for small feature".
- **Option 4 (security sub-plan add-on):** an additional phase with the security-focused agent, model usually `opus` (security-core gets the better model — see legacy boundaries about the rentability ↔ reliability conflict). Place this phase **before** the integration phase so security findings can shape the consolidated architecture.

The Cost-estimate row of `PLANNER_OUTPUT.md` should compare the chosen option against a naive `/plan-do` baseline (which would default-pick Sonnet for everything serially).

## 6. Common pitfalls

- **Over-parallelizing a tightly coupled domain.** When sub-architects work on overlapping concerns, the integration phase ends up rewriting their outputs — the savings from parallelism are eaten by the coordination cost. If the README does not draw clean boundaries, do not invent them.
- **Picking Opus "to be safe".** Opus on routine architecture is rent-negative (≈5× Sonnet cost for ≤1.2× quality on routine work). The boundaries section of the legacy planner is explicit: every Opus pick must be justified by evidence, not anxiety.
- **Folding security into another track as an "and also".** Security review demands its own attention budget. If auth / PII / secrets are in scope, they get an explicit phase with named review gates — the cost of a mis-handled security item dwarfs the cost of one extra phase.
