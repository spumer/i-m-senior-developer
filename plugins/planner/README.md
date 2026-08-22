# planner

Claude Code plugin for file-backed product discovery, feature planning, and
implementation orchestration. This file answers how the plugin is structured in
the repository. The contract — what each command takes and returns, the
freshness gate, capability routing, report discipline — lives on
[`docs/plugins/planner.md`](../../docs/plugins/planner.md).

## Structure

```text
plugins/planner/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   └── planner.md
├── commands/
│   ├── plan-idea.md
│   ├── plan-epic.md
│   ├── plan-roadmap.md
│   ├── plan-feat.md
│   ├── plan-jira.md
│   ├── plan.md
│   ├── plan-do.md
│   ├── plan-do-workflow.md
│   └── plan-reflect.md
├── workflows/
│   └── plan-do-workflow.js
├── skills/
│   ├── planner/
│   │   ├── SKILL.md
│   │   ├── assets/
│   │   │   ├── plan_state.py
│   │   │   └── test_plan_state.py
│   │   └── references/
│   │       ├── bootstrap.md
│   │       ├── architecture-mode.md
│   │       ├── execution-mode.md
│   │       └── template-context.md
│   ├── product-discovery/
│   │   ├── SKILL.md
│   │   ├── assets/
│   │   │   ├── product_state.py
│   │   │   └── test_product_state.py
│   │   └── references/
│   │       ├── routing.md
│   │       ├── dialogue.md
│   │       ├── pov-review.md
│   │       ├── idea-mode.md
│   │       ├── epic-mode.md
│   │       ├── roadmap-mode.md
│   │       └── feature-mode.md
│   ├── product-baseline/
│   │   └── SKILL.md
│   └── planner-reflect/
│       └── SKILL.md
├── hooks/
│   ├── hooks.json
│   └── product_intake_hint.py
├── evals/
│   ├── README.md
│   ├── run.py
│   ├── idea-routing/
│   ├── multi-step-input/
│   └── baseline-provider-limits/
└── README.md
```

## Installation

Add this marketplace to Claude Code and install the plugin:

```text
/plugin marketplace add spumer/i-m-senior-developer
/plugin install planner@i-m-senior-developer
```

## Evaluation

```bash
python3 plugins/planner/evals/run.py
```

The wrapper pins the run contract, verifies the aggregate result, and refuses a
partial run. General rules for plugin testing live in `docs/testing/`; the
observed result of the latest run is recorded in `docs/reports/planner.md`.
