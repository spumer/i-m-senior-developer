# Hooks (placeholder)

No hooks ship with `planner` v0.1.0.
This directory exists as a drop-in slot so users who want auto-reflect on session end can add their own `hooks.json` and `session-end.sh` here without forking the plugin.
The shape below is documentation only, not a recipe to copy verbatim — the script body is intentionally not provided.

## Future: SessionEnd auto-reflect

The intended (but not shipped) shape consists of two files:

- `hooks.json` — a plugin-format hooks file registering one entry under the `SessionEnd` event.
  The entry is a `command`-type hook.
  Its `command` field invokes `${CLAUDE_PLUGIN_ROOT}/hooks/session-end.sh`.
  The `timeout` field is set to 10 seconds.
- `session-end.sh` — a one-liner shell script that detects whether `<feature-dir>/PLANNER_OUTPUT.md` was modified during the current session, and if so emits a `systemMessage` reminding Claude to invoke `/plan-reflect`.
  The script does NOT call `/plan-reflect` itself — invocation stays a human (or orchestrator) decision, so the hook is a nudge, not an action.

## Why opt-in

Cross-session transcript availability is currently uncertain (see PLAN-01 §12 Decision 1).
An auto-firing `/plan-reflect` could trigger in a session whose transcripts are unreachable, producing partial, low-quality lessons that pollute `planner-context.md`.
The cost of staying opt-in is one paragraph of documentation; the cost of a mis-fired auto-reflect is corrupted project memory that future sessions would treat as ground truth.
Asymmetry favors opt-in until the cross-session question is answered with evidence.

## How to enable

Two manual steps, both performed inside this `hooks/` directory:

1. Create `hooks/hooks.json` containing the `SessionEnd` registration block described above — plugin hooks wrapper format, single `command`-type entry pointing to `${CLAUDE_PLUGIN_ROOT}/hooks/session-end.sh`, `timeout` 10.
2. Create `hooks/session-end.sh` containing the detection one-liner described above, then make it executable: `chmod +x hooks/session-end.sh`.

After both files exist, restart Claude Code.
Hooks are loaded once at session start, and changes to hook files are not picked up live in an already-running session.
