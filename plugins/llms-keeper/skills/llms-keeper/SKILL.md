---
name: llms-keeper
description: >
  This skill should be used when the user asks to "generate llms.txt",
  "create llms-full.txt", "update llms.txt", "regenerate llms-full.txt",
  "create AI context files for this project",
  "обновить llms.txt", "сгенерировать llms-full.txt",
  "создать контекст проекта для AI",
  or mentions "llms.txt", "llms-full.txt", "llmstxt",
  "llmstxt.org standard", "project context for AI agents",
  "контекст проекта для AI".
  Also applicable when user asks about the llmstxt.org format,
  wants to know how to structure llms.txt, or asks
  "what should llms-full.txt contain".
---

# llms-keeper — Project Context for AI Agents

Generate and maintain `llms.txt` and `llms-full.txt` files following the [llmstxt.org](https://llmstxt.org) standard to give AI agents quick project understanding.

## Core Philosophy

**"Find the smallest set of high-signal tokens that maximize the likelihood of desired outcome."**

Every sentence must answer: "Will an AI agent produce worse results without this information?" If no — delete without hesitation.

## Two Files, Two Purposes

| File | Purpose | Audience | Length |
|------|---------|----------|--------|
| `llms.txt` | Navigation index | AI needing quick orientation | 50-100 lines |
| `llms-full.txt` | Complete context | AI needing full understanding | 200-600 lines |

## Signal vs Noise

### Always Include (High-Signal)
- Project purpose and tech stack
- Architecture: module hierarchy, dependency direction
- Data flow patterns (ASCII diagrams for complex flows)
- Key patterns used across 3+ files
- Configuration approach and entry points
- Common pitfalls with solutions
- Essential development commands
- Testing approach and conventions

### Never Include (Noise)
- Step-by-step tutorials or implementation guides
- Temporary workarounds, TODOs, FIXMEs
- Patterns used in only 1 file
- Verbose explanations ("This module is responsible for...")
- Obvious information for experienced developers
- Credentials, API keys, secrets

## Workflow

Delegate analysis and generation to the `documentation-keeper` agent.

The agent handles the full process: framework auto-detection, codebase scanning, pattern extraction, file generation, and quality verification.

For manual or informational use, the workflow is:
1. **Scan** project structure and detect tech stack from manifest files
2. **Read** key sources: entry points, core modules, configs, tests, docs
3. **Extract** high-signal information (architecture, patterns, pitfalls)
4. **Generate** `llms-full.txt` first (self-contained content)
5. **Derive** `llms.txt` from it (navigation index linking to sections)
6. **Verify** quality checklist from `references/llmstxt-spec.md`

## Update vs Generate

- **No llms.txt exists** → full generation from scratch
- **llms.txt exists** → analyze git changes since last update, update only affected sections, verify consistency between both files

## Reference

For format details, structure requirements, and quality checklist, see `references/llmstxt-spec.md`.
