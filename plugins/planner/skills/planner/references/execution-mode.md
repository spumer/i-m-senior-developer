# Mode 2 — Execution planning

Load this reference when the input is an existing architecture document: `ARCHITECTURE.md`, `*-PLAN-*.md`, `*-DESIGN-*.md`, or another file explicitly supplied as architecture.

## Result

The completed result is `<architecture-dir>/PLANNER_EXECUTION.md`; store it through the prepared-file and helper workflow from the main skill. Never overwrite the architecture and never write execution content to `PLANNER_OUTPUT.md`.

Before planning, run the state helper's `inspect` command. An architecture without supported planner frontmatter is valid version 0 and remains untouched, including ordinary Markdown that starts with a `---` horizontal separator.

## Dependency graph

1. Extract each implementation stage from the architecture.
2. Record concrete prerequisites. A dependency must point to a file, contract, or decision produced by the preceding stage.
3. Topologically order the stages.
4. Group stages only when no dependency path exists between them.
5. Keep migrations → models → services/endpoints → clients strictly serial when a persistence boundary is involved.

Do not invent parallelism to make the plan look optimized.

## Agent and model choice

Resolve agent names only from `.claude/planner-context.md` §1.

- Default implementation model: Sonnet.
- Use Haiku only for tightly bounded mechanical edits.
- Use Opus only when project evidence or security-critical reasoning justifies the added cost.
- If a role has no active mapped agent, state the abstract role and require the orchestrator to use its documented fallback. Do not invent a name.

A phase may contain at most:

- 6 planning agents;
- 7 validation agents;
- 4 integration agents.

## Review placement

- Security, data migration, or breaking contract → review after every affected phase.
- Small and ordinary changes → one independent review after implementation.
- A design defect returns to architecture. Once architecture changes, execution stops until this file is rebuilt.

## Complete execution file format

The saved `PLANNER_EXECUTION.md` is the following YAML header and Markdown body concatenated in this order, without the code fences. The planner writes only the body to `PLANNER_EXECUTION.md.prepared`; `plan_state.py` fills the dynamic header values and atomically assembles the saved file.

### YAML header template

```yaml
---
plan_type: execution
version: 1
status: current
content_sha256: <SHA-256 of the execution body>
architecture:
  path: "./ARCHITECTURE.md"
  version: 1
  content_sha256: <SHA-256 of the architecture body>
---
```

The execution version and fingerprint belong to this file. The nested architecture version and fingerprint identify the exact architecture used to build it. `architecture.path` is a safely quoted path relative to the execution file. A newly synchronized file has `status: current`; `check --mark-stale` may change only that field to `stale`, preserving the execution version and body.

### Declared outputs

Each implementation phase declares its concrete repository outputs in an `Outputs:` field. Write every path in backticks and relative to the repository root: a file at the root uses the explicit form `./<name>`, for example `./README.md`; a directory ends with `/`, for example `plugins/example/`. Existing plans are not rewritten solely to adopt this form.

### Markdown body template

```markdown
# <task name> — Execution plan

## Task summary
- Type: <feature|bugfix|refactor|doc|research|mixed>
- Size: <S|M|L with evidence>
- Criticality: <normal|security|data-migration|breaking-API|ux-critical>
- Parallelism: <independent axes or strictly serial>

## Phase 1 — <name> (<serial|parallel>)
- Agent: <catalog name>
- Model: <opus|sonnet|haiku>
- Skills: <catalog names or none>
- Inputs: <paths and contracts>
- Work: <one bounded responsibility>
- Outputs: <paths or observable artifacts>
- Verification: <what must be observed before the next phase>

## Phase 2 — <name> (<dependency>)
...

## Estimate
<tokens, wall-clock, and relative cost compared with a straightforward serial run; state explicitly when no reliable estimate exists>

## Final review
<review agents, checks, and issue-file location>

## Documentation
<keeper and allowed documentation paths>

## Risks and gates
<risk, mitigation, and stop condition>

## Fallback
<what to do when a prerequisite or mapped agent is unavailable>
```

## Completion

Successful chat output names:

- `PLANNER_EXECUTION.md` path;
- execution version;
- architecture path and version;
- two to four main phases or gates;
- the exact `/planner:plan-do` command.

Do not paste the execution body into chat after a successful write.