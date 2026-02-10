#!/bin/bash
# TDD Master — SessionStart hook
# Injects TDD workflow context into every new session

cat <<'EOF'
## TDD Workflow Active

For all new features and bug fixes: follow Test-Driven Development methodology.

1. Write failing tests FIRST (RED)
2. Write minimal code to pass (GREEN)
3. Refactor while keeping tests green (REFACTOR)

Use the `tdd-master` skill for structured TDD workflow and reference documentation.
Do NOT write implementation code without a failing test.
EOF
