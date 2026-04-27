# FEAT-0001-ISSUE-001 — agent `tools` field uses non-canonical comma-string instead of YAML array

**Severity:** P1

**File:** `plugins/planner/agents/planner.md:5`

## Problem

PLAN-01 §3.1 (line 81) explicitly mandates the agent frontmatter `tools` field as a YAML array:

> `tools` | `["Read", "Grep", "Glob", "Write"]`

The implemented agent uses a comma-separated **string** instead:

```yaml
tools: Read, Grep, Glob, Write
```

This parses as a single `str` (`"Read, Grep, Glob, Write"`), not an array of tool names. Verified via PyYAML: `type(tools) == str`, not `list`.

Anthropic's official `agent-development` SKILL.md (cached at `~/.claude/plugins/cache/claude-plugins-official/plugin-dev/unknown/skills/agent-development/SKILL.md`) is unambiguous on this:

- Line 357 of the field reference table: `tools | No | Array of tool names | ["Read", "Grep"]`
- All three reference agents in the same plugin-dev plugin use array form: `agent-creator.md:34` (`tools: ["Write", "Read"]`), `skill-reviewer.md:35` (`tools: ["Read", "Grep", "Glob"]`), `plugin-validator.md:36` (`tools: ["Read", "Grep", "Glob", "Bash"]`).
- All inline examples in `agent-development/SKILL.md` (lines 44, 149) use array form.

The comma-string form is non-canonical. The runtime behavior is undocumented; the most likely outcomes are (a) the value is parsed as a string and the tool-restriction check fails-open (agent gets full tool access, breaking the least-privilege requirement that PLAN-01 §3.1 explicitly cites — *"Drop `WebSearch` ... least-privilege wins"*), or (b) the value is split on commas with permissive whitespace handling and the restriction works. Either way, deviating from the documented schema for an undocumented edge-case is not a contract this plugin should depend on, especially when the spec already pinned the canonical form.

## Fix

Change `plugins/planner/agents/planner.md` line 5 from:

```yaml
tools: Read, Grep, Glob, Write
```

to:

```yaml
tools: ["Read", "Grep", "Glob", "Write"]
```

This matches PLAN-01 §3.1 verbatim and aligns with every other agent shipped in the official `plugin-dev` plugin.

## Scope of remaining validation

All other validation gates passed:

- `plugin.json`: valid JSON; `name=planner`, `version=0.1.0`, `description`, `author.name`, `keywords` all present and well-formed; no `category` field (correctly delegated to marketplace.json per PLAN-01 §1).
- `marketplace.json`: valid JSON; `planner` entry appended after `llms-keeper` with the spec'd description, `source: ./plugins/planner`, `category: development`. Other three entries (`tdd-master`, `functional-clarity`, `llms-keeper`) bit-identical to pre-change state per `git diff` — only an addition, no edits.
- Directory layout matches PLAN-01 §0 exactly: `.claude-plugin/plugin.json`, `agents/planner.md`, `skills/planner/SKILL.md`, `skills/planner/references/{bootstrap,architecture-mode,execution-mode,template-context}.md`, `skills/planner-reflect/SKILL.md`, `commands/{plan,plan-reflect}.md`, `hooks/README.md`, `README.md`. No stray files. `hooks/hooks.json` correctly absent per PLAN-01 §8.
- All five `.md` files with frontmatter parse cleanly under PyYAML (`safe_load`). No tabs anywhere. No smart quotes (`U+2018`, `U+2019`, `U+201C`, `U+201D`) — the russian guillemets `«»` and the em-dash `—` are intentional content, not YAML hazards.
- Cross-references intact: `commands/plan.md` activates skill `planner` (exists at `skills/planner/SKILL.md`); `commands/plan-reflect.md` activates skill `planner-reflect` (exists at `skills/planner-reflect/SKILL.md`).
- Command `allowed-tools`: `commands/plan.md` uses `Read, Grep, Glob, Write` — which is the documented format for `allowed-tools` per official `command-development/SKILL.md` lines 117/148/468 (commands use comma-string for `allowed-tools`; this is a different field and a different convention from agent `tools`). `commands/plan-reflect.md` uses `Read, Grep, Glob, Write, Bash(git:*)` — the `Bash(git:*)` parenthetical-glob syntax is the canonical Claude Code restriction format per the same reference (lines 117, 489, 520, 578, 649, 676, 772, 843, 860). Both commands are correct.
- `hooks/README.md` is the placeholder per PLAN-01 §8.1 — describes the future-shape `SessionEnd` hook without shipping `hooks.json` or `session-end.sh`.
