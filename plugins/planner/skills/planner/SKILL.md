---
name: planner
description: >
  Builds and saves architecture or execution plans. Use when the user asks to
  plan a task, split implementation work, prepare a feature README for
  implementation, or turn an architecture document into executable phases.
---

# Planner — file-backed planning

The planner produces one complete file per activation:

- **architecture mode** writes or updates `ARCHITECTURE.md`;
- **execution mode** writes or updates `PLANNER_EXECUTION.md`.

A successful activation never emits the full document to chat. It reports the path, kind, version, and two to four main outcomes. Full chat output is reserved for a failed write or failed metadata synchronization.

The planner writes plans; it does not execute implementation phases and does not invoke working agents.

## Principles

1. **Ready result.** Architecture mode produces architecture itself, not instructions for a future architect session.
2. **Separate roles.** Requirements, architecture, and execution planning live in different files. Never write architecture and execution content to the same path.
3. **File first.** A run is successful only after the full document and its metadata are stored.
4. **Evidence.** Read the actual input and existing neighboring plans before deciding mode, version, or staleness.
5. **Minimal change.** Rewrite the current target in place. Do not create numbered history files; Git owns history.
6. **Fail fast.** Missing, unreadable, ambiguous, or colliding paths stop the run before planning.
7. **No information loss.** A stale execution plan keeps its body. A legacy `PLANNER_OUTPUT.md` is not deleted.

## Workflow

### 1. Read project context

Read `<project-root>/.claude/planner-context.md`. If it is missing, stale, or the user explicitly requests a rescan, follow `references/bootstrap.md`, then return here.

The state helper is:

```text
${CLAUDE_PLUGIN_ROOT}/skills/planner/assets/plan_state.py
```

Run it with `python3`. Do not reproduce its parsing or hashing logic in the prompt.

### 2. Classify the input

- Feature `README.md`, or a feature directory containing one → architecture mode in that directory.
- Existing architecture path (`ARCHITECTURE.md`, `*-PLAN-*.md`, `*-DESIGN-*.md`, or an explicitly supplied equivalent) → execution mode beside that file.
- Free text with no readable filesystem path → architecture mode under `.claude/plans/<task-slug>/`.

A supplied path that does not exist or cannot be read is an error. Do not reinterpret a path-looking argument as free text.

For free text, create a short kebab-case slug. Before reusing an existing directory, read its plan files. If it belongs to another task or remains ambiguous, append the smallest available numeric suffix. After the final slug is selected, create that one directory with `mkdir` before validating the target path.

### 3. Validate the target and load one mode reference

Resolve the target directory and run the matching check before preparing the document.

Architecture mode:

```text
python3 "${CLAUDE_PLUGIN_ROOT}/skills/planner/assets/plan_state.py" \
  validate-architecture-target <architecture-path> \
  --directory <target-directory> [--source <README-path>]
```

Omit `--source` only for free-text input. Execution mode:

```text
python3 "${CLAUDE_PLUGIN_ROOT}/skills/planner/assets/plan_state.py" \
  validate-execution-target <execution-path> \
  --architecture <architecture-path> --directory <target-directory>
```

Exit status `3` or `64` stops the run before the mode reference is loaded and before the document body is prepared. The checks reject wrong names, paths outside the selected directory, symbolic links, hard links, overlap with a protected input, and an execution target that is not beside its architecture.

After the check succeeds, load exactly one reference:

- Architecture mode → `references/architecture-mode.md`.
- Execution mode → `references/execution-mode.md`.

### 4. Prepare the complete body

Read the existing target without changing it. Prepare the complete new body without YAML frontmatter and keep that body in the current context until synchronization succeeds.

Decide whether the new body changes meaning:

- `yes` when decisions, contracts, phases, dependencies, risks, or expected behavior changed;
- `no` when the body is unchanged or only formatting and wording changed without changing its instructions.

This decision is explicit input to the helper. The helper owns metadata consistency; it does not judge prose.

### 5. Write the prepared body and synchronize

`Write` must never change the target plan directly. Write the body to the exact transient path `<target-name>.prepared` beside the target. Do not use another neighboring file, a symbolic link, or a hard link.

#### Architecture

Write `<target-dir>/ARCHITECTURE.md.prepared`, then run:

```text
python3 "${CLAUDE_PLUGIN_ROOT}/skills/planner/assets/plan_state.py" \
  sync-architecture <architecture-path> \
  --body-file <target-dir>/ARCHITECTURE.md.prepared \
  --semantic-change <yes|no>
```

The helper reads and removes the prepared file before atomically replacing the complete target. If `PLANNER_EXECUTION.md` exists beside it, immediately run:

```text
python3 "${CLAUDE_PLUGIN_ROOT}/skills/planner/assets/plan_state.py" \
  check <execution-path> --mark-stale
```

Exit status `2` here is an expected stale result, not a helper failure. Keep the execution body and report that it must be rebuilt.

#### Execution plan

Inspect the supplied architecture after the target check from step 3:

```text
python3 "${CLAUDE_PLUGIN_ROOT}/skills/planner/assets/plan_state.py" \
  inspect <architecture-path>
```

An architecture without supported planner frontmatter is reported as version `0` and must not be modified merely for migration. This includes ordinary Markdown that starts with a `---` horizontal separator.

Write `<target-dir>/PLANNER_EXECUTION.md.prepared`, then run:

```text
python3 "${CLAUDE_PLUGIN_ROOT}/skills/planner/assets/plan_state.py" \
  sync-execution <execution-path> \
  --body-file <target-dir>/PLANNER_EXECUTION.md.prepared \
  --architecture <architecture-path> --semantic-change <yes|no>
```

The helper requires the exact prepared-file name, removes that file after reading it, then validates the architecture and atomically writes body and metadata together. A later validation error leaves the target unchanged and does not leave a prepared file behind.

### 6. Handle failures

A prepared-file `Write` error or helper exit status `3`/`64` means the new plan was not saved successfully. The existing target remains the current file result.

1. State the target path and the concrete error.
2. Say that the new file result is unavailable and whether an older target remains.
3. Emit the complete prepared document from the current context to chat as the fallback result.
4. Do not emit a success summary and do not write the body directly to the target as a recovery attempt.

Do not catch the error and continue with stale metadata.

### 7. Emit only a short success summary

After a successful write, output:

```text
<Kind> saved: <path>
Version: <N> — <current|stale>
Summary:
- <main outcome 1>
- <main outcome 2>
- <optional outcome 3>
- <optional outcome 4>
Next: <command, if needed>
```

Never include the full plan after this summary. If a legacy `PLANNER_OUTPUT.md` remains beside the new files, add one concise note that it was preserved and ignored as the current plan.

## Exact YAML header templates

These are the exact field sets and nesting used in saved plan files. Dynamic values are computed by `plan_state.py`, not authored in the prepared body. The complete saved-file templates, including their Markdown bodies, are in `references/architecture-mode.md` and `references/execution-mode.md`.

### Architecture

```yaml
---
plan_type: architecture
version: 1
status: current
content_sha256: <body fingerprint>
---
```

### Execution plan

```yaml
---
plan_type: execution
version: 1
status: current
content_sha256: <body fingerprint>
architecture:
  path: "./ARCHITECTURE.md"
  version: 1
  content_sha256: <architecture body fingerprint>
---
```

Rules:

- New documents start at version 1.
- A semantic body change increments that document's version.
- A non-semantic rewrite preserves the version and refreshes the fingerprint.
- Changing only execution status from `current` to `stale` preserves its version and body.
- Architecture without a supported header is version 0 and stays untouched during `inspect`.
- The helper computes fingerprints from the body, excluding frontmatter.
- Direct body changes are detected even when a person forgets to update `version`.

## Write boundary

The planner may write only:

1. `<project-root>/.claude/planner-context.md` during bootstrap or explicit rescan;
2. architecture and execution targets under the resolved feature directory or `.claude/plans/<task-slug>/`;
3. one transient `<target-name>.prepared` file beside the selected target.

`Write` may create the transient prepared file but must not overwrite a target plan. The state helper validates the paths, consumes the prepared file, and is the only writer of the target architecture or execution file. Use Bash only to create the selected plan directory and invoke this helper. Do not use shell redirection or another command to bypass the write boundary.

## Reference index

- `references/bootstrap.md` — project scan and `planner-context.md` creation.
- `references/template-context.md` — canonical bootstrap template.
- `references/architecture-mode.md` — architecture body requirements and update rules.
- `references/execution-mode.md` — dependency graph, phase grouping, model choice, and execution body requirements.