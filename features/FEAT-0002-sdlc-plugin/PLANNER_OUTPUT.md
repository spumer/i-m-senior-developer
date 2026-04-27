# Planner Output — FEAT-0002-sdlc-plugin

**Mode:** architecture (Stage 0 — pre-architect)
**Generated:** 2026-04-26
**Inputs read:**
- `features/FEAT-0002-sdlc-plugin/README.md` (feature spec, 181 lines)
- `features/FEAT-0001-planner-plugin/FEAT-0001-PLAN-01.md` (template/prior-art, 554 lines)
- `plugins/planner/.claude-plugin/plugin.json` (prior-art manifest)
- `plugins/planner/agents/planner.md` (thin wrapper pattern)
- `plugins/planner/skills/planner/SKILL.md` (skill pattern)
- `.claude-plugin/marketplace.json` (marketplace state)
**Planner-context version:** 2026-04-26 (bootstrap this session)

---

## Task summary

- **Type:** feature (new plugin authoring)
- **Size:** L — 15 files to create (3 agents + 3 SKILL.md + 8 references + plugin.json + README + marketplace edit), cross-cutting decisions on skill split / references decomposition / namespacing / migration
- **Criticality:** normal (no security/PII/migrations in the traditional sense; but migration guide touches `~/.claude/agents/` — requires careful wording)
- **Parallelism axis:** Architecture phase is serial (cross-cutting decisions must resolve before any file is written). After architecture approval: 3 skill groups are independent of each other; agent wrappers depend on skill names; plugin meta (plugin.json, README, marketplace) is independent of skills.
- **Risk gates:** Architecture document must be approved before implementation starts. Migration guide requires human review before publication (touches user's global agent directory).

---

## Execution plan

### Phase 1 — Architecture (serial, this phase)

- **Agent:** `agent-architect` | **Model:** opus | **Skills:** none (design only)
  - **Focus:** Produce `FEAT-0002-PLAN-01.md` — the complete implementation contract for the `sdlc` plugin. Must resolve: (1) skill split and section outlines for all 3 SKILL.md files; (2) references decomposition (which content in SKILL.md vs which in each reference file); (3) cross-plugin integration wording (functional-clarity, tdd-master, frontend-design); (4) agent frontmatter specs (models, tools, description triggers); (5) namespacing decisions; (6) migration guide exact steps; (7) plugin.json fields; (8) marketplace entry; (9) length budgets per file; (10) parallelization schedule for Phase 2+.
  - **Inputs:** `features/FEAT-0002-sdlc-plugin/README.md`, `features/FEAT-0001-planner-plugin/FEAT-0001-PLAN-01.md` (as structural template), `plugins/planner/` (prior-art), `.claude-plugin/marketplace.json`
  - **Outputs:** `features/FEAT-0002-sdlc-plugin/FEAT-0002-PLAN-01.md`
  - **Est. tokens:** ~8,000–12,000 | **Est. wall-clock:** ~15–20 min

**Why serial, not parallel:** The 15 deliverables share cross-cutting constraints — skill boundaries, reference depth, cross-plugin wording, migration steps. Parallelizing before these are resolved produces inconsistent artifacts that require expensive re-reconciliation. One Opus architect pass is cheaper and more reliable than N parallel architects + a reconciliation step.

**Why Opus (not Sonnet):** The architecture document is the contract all implementers follow. FEAT-0001-PLAN-01.md is 554 lines of tightly specified decisions. This feature has comparable complexity: 3 skills × (SKILL + N references), 3 agent wrappers, 2 open questions on shared content (see §5 below). A misrouted architecture choice (wrong model assignment, wrong skill boundary, wrong reference depth) propagates into all 15 downstream files. Opus is justified by the complexity and the downstream propagation risk.

---

### Phase 2 — Parallel implementation (after Phase 1 approval)

> This is a forward-looking sketch. The final Phase 2 plan will be produced in Stage 2 of `/plan-do` after the architecture document is approved. Assignments below are indicative.

**Phase 2a — Parallel skill groups (3 agents, independent)**

Each group = 1 SKILL.md + its N references. Groups are independent because skills do not reference each other's internals.

| Agent slot | Agent | Model | Focus | Files |
|------------|-------|-------|-------|-------|
| 2a-1 | `python-implementer` or `general-purpose` | sonnet | `architect` skill group | `skills/architect/SKILL.md` + 3 references (`backend-python.md`, `frontend-react.md`, `api-design.md`) |
| 2a-2 | `python-implementer` or `general-purpose` | sonnet | `code-implementer` skill group | `skills/code-implementer/SKILL.md` + 2 references (`backend-python.md`, `frontend-react.md`) |
| 2a-3 | `python-implementer` or `general-purpose` | sonnet | `code-reviewer` skill group | `skills/code-reviewer/SKILL.md` + 3 references (`security.md`, `backend-python.md`, `frontend-react.md`) |

Note: After `sdlc` plugin is built, these slots map to `sdlc:code-implementer`. Until then, `python-implementer` or `general-purpose` fills the role.

**Phase 2b — Plugin meta (1 agent, independent of 2a)**

| Agent slot | Agent | Model | Focus | Files |
|------------|-------|-------|-------|-------|
| 2b-1 | `general-purpose` | sonnet | Scaffolding | `plugins/sdlc/.claude-plugin/plugin.json`, `plugins/sdlc/README.md` (with migration guide), edit to `.claude-plugin/marketplace.json` |

**Phase 2c — Agent wrappers (1 agent, depends on 2a — needs skill names confirmed)**

| Agent slot | Agent | Model | Focus | Files |
|------------|-------|-------|-------|-------|
| 2c-1 | `general-purpose` | sonnet | Thin wrappers | `agents/architect.md`, `agents/code-implementer.md`, `agents/code-reviewer.md` |

**Phase 2 parallelization diagram:**
```
[serial]  Phase 1 (architect, opus)
             |
     ┌───────┴────────┐
     |                |
[parallel] 2a (3 agents, sonnet)   [parallel] 2b (1 agent, sonnet)
     |
[serial]  2c (1 agent, sonnet, depends on 2a)
             |
[serial]  Phase 3 — review
```

**Phase 3 — Review (serial, after 2a + 2b + 2c)**

| Agent | Model | Focus |
|-------|-------|-------|
| `code-reviewer` | opus | Consistency check across all 15 files: skill boundaries, reference depth (≤1 level), cross-plugin integration wording, migration steps accuracy, length budgets (SKILL.md ≤500 lines), semver in plugin.json |

---

## Cost estimate

| | Naive `/plan-do` | Optimized | Delta |
|---|---|---|---|
| Tokens | ~60,000 (15 files × ~4,000 each, no coordination) | ~35,000 (serial arch ~10k + parallel impl ~20k + review ~5k) | -42% |
| Wall-clock | ~60 min (serial naive) | ~30 min (parallel 2a+2b) | -50% |
| $-cost (relative) | 1.0 | ~0.65 | -35% |

Обоснование экономии: параллельная фаза 2a (3 независимых skill-группы) сокращает wall-clock вдвое. Один Opus-архитектор дешевле трёх параллельных Opus-агентов, которые потом требуют reconciliation. Architecture-first устраняет переделки на этапе имплементации.

---

## Risks & human-in-the-loop gates

1. **Shared content between references/backend-python.md across 3 skills** — each skill looks at backend-python from a different angle (design vs implement vs review). Architecture document must specify the split clearly. Risk: overlap leads to duplication or contradiction. Mitigation: architect explicitly specifies what belongs to each skill's reference; README Open Question 2 acknowledges this.
   - Gate: human approval of FEAT-0002-PLAN-01.md before implementation.

2. **Migration guide touches `~/.claude/agents/`** — rm -f on global agent files. Must be reviewed by human before publication. Risk: user loses customized agents if they have local modifications. Mitigation: migration guide must include a "check for local modifications" step.
   - Gate: human review of `plugins/sdlc/README.md` migration section before release.

3. **Cross-plugin integration wording** — sdlc skills reference `functional-clarity:functional-clarity`, `tdd-master:tdd-master`, `document-skills:frontend-design`. Anthropic's "reference other Skills by name" mechanism must be used correctly. Risk: wrong invocation pattern → skill not activated. Mitigation: architect to verify against Anthropic plugin docs; architecture document must specify exact wording.

4. **`code-reviewer` name conflict** — legacy `~/.claude/agents/code-reviewer.md` vs `sdlc:code-reviewer`. Planner-context §1 already notes this. Migration guide and planner-context update (via `/plan-reflect` after FEAT-0002) resolves it. No risk to implementation; risk to user's workflow during transition.

5. **SKILL.md length budget** — 3 skills × ~300 lines + 8 references. If any SKILL.md exceeds 500 lines, content must move to a new reference file. Architecture document must set hard budgets per section to prevent overflow.

6. **Agent model choices** — `architect.md` wraps `model=opus` (design-only tasks justify it). `code-implementer.md` and `code-reviewer.md` wrap `model=sonnet`. This is specified in feature README. Architecture document should confirm or override.

---

## Fallback

Если Phase 1 (architecture document) не готов или не одобрен пользователем — не переходить к Phase 2. Implementation без контракта приводит к inconsistent SKILL.md boundaries и дорогостоящему переписыванию.

Если `agent-architect` недоступен — fallback: `general-purpose` (opus) с явным промптом «ты архитектор, напиши implementation contract по образцу FEAT-0001-PLAN-01.md». Качество ниже, но артефакт получается.

---

## §1 Agent assignments — model/skill/role per subtask

| Subtask | Agent | Model | Justification |
|---------|-------|-------|---------------|
| Phase 1: Architecture document | `agent-architect` | opus | Cross-cutting decisions across 15 files; contract for all downstream work; complexity comparable to FEAT-0001-PLAN-01.md (554 lines); wrong decision propagates to all 15 artifacts |
| Phase 2a-1: architect skill group | `general-purpose` | sonnet | Standard plugin content authoring; architecture doc provides complete spec |
| Phase 2a-2: code-implementer skill group | `general-purpose` | sonnet | Standard plugin content authoring |
| Phase 2a-3: code-reviewer skill group | `general-purpose` | sonnet | Standard plugin content authoring |
| Phase 2b: Plugin meta | `general-purpose` | sonnet | Templated work (plugin.json, marketplace entry, README) |
| Phase 2c: Agent wrappers | `general-purpose` | sonnet | Thin wrappers ~30 lines each, well-defined pattern from planner prior-art |
| Phase 3: Review | `code-reviewer` | opus | Consistency check across 15 interdependent files; security-adjacent (migration guide); Opus justified by scope |

---

## §2 Parallelization constraints (LIFT-COT compliance)

- Phase 2a: 3 agents — within LIFT-COT limit (≤7 per phase, ≤6 for planning phases).
- Phase 2 total agents running concurrently: 4 (2a × 3 + 2b × 1) — within limit.
- Phase 3: 1 agent (serial by nature).
- No phase exceeds 7 agents.

---

## §3 Decision rationale

**Why not parallelize architecture?**
The 3 skills share constraints: cross-plugin integration wording must be identical across SKILL.md files; reference depth rule (≤1 level) applies to all; migration guide must be consistent with agent wrapper descriptions. An architect sees the whole picture; 3 parallel sub-architects would each produce locally consistent but globally inconsistent artifacts, requiring an expensive reconciliation step. This violates FPF A.11 (parsimony) and FPF A.10 (evidence: FEAT-0001 architecture was produced as a single monolithic document, and it served as a coherent contract).

**Why `agent-architect` (opus) and not `general-purpose` (sonnet) for architecture?**
The architecture document is the implementation contract: every section name, length budget, content origin, and frontmatter field is specified there. FEAT-0001-PLAN-01.md is the evidence — a 554-line document with exhaustive detail. Producing an equally rigorous document for FEAT-0002 requires: (a) understanding the Anthropic plugin authoring best-practices at depth, (b) resolving the 2 open questions (shared content, cross-plugin invocation), (c) specifying 15 files' content in enough detail that implementers make zero architectural decisions. Sonnet risks under-specifying, leading to implementer guesses and divergence. Opus cost is justified by the downstream savings (no rework on 15 files).

**Why implementation slots use `general-purpose` (sonnet) and not `python-implementer`?**
This is a plugin-authoring repo. The deliverables are Markdown files (SKILL.md, references, agent wrappers) and JSON (plugin.json). `python-implementer` is Django/pytest-specialized and overkill for Markdown authoring. `general-purpose` (sonnet) is the correct fit. Note: this is the exact gap FEAT-0002 addresses — after sdlc plugin is built, `sdlc:code-implementer` becomes the appropriate slot for implementation tasks in downstream projects.

**Semver compliance (CLAUDE.md mandate):**
The new plugin starts at `version: 0.1.0`. Any subsequent change to any file in `plugins/sdlc/` requires a semver bump in `plugins/sdlc/.claude-plugin/plugin.json`. Architecture document must include this as a checklist item.
