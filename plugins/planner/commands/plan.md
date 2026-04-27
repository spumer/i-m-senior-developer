---
name: plan
description: Build an execution plan for a task or feature. Activates the planner skill in architecture or execution mode.
argument-hint: "[feature-dir or task description]"
allowed-tools: Read, Grep, Glob, Write
---

Activate the `planner` skill and follow its workflow start-to-finish.

Interpret `$ARGUMENTS` as follows:

- If `$ARGUMENTS` is a filesystem path that points to a feature `README.md` (or to a feature directory whose `README.md` is the only architecture-bearing artifact) — run **Mode 1 (architecture planning)**.
- If `$ARGUMENTS` is a path that points to an existing PLAN or DESIGN document (`*-PLAN-*.md`, `*-DESIGN-*.md`, `ARCHITECTURE.md`, etc.) — run **Mode 2 (execution planning)**.
- If `$ARGUMENTS` is free text with no path — treat it as a task description and work in **chat-output mode** (do not write `PLANNER_OUTPUT.md`; emit the plan to chat using the same template).

Emit `PLANNER_OUTPUT.md` per the skill's "Output format" section when a feature directory exists; otherwise output the same content to chat. Do not execute the plan, do not write code, do not invoke other agents — the planner builds the plan and stops.
