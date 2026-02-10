#!/usr/bin/env bash
# Functional Clarity — SessionStart hook
# Brief reminder of core principles for every session

cat <<'EOF'
## Functional Clarity Active

Core values: simplicity, reliability, clarity, maintainability.

Key principles for this session:
- **Fail-fast**: No Error Hiding. Exceptions must bubble up or be reflected in data
- **Minimal changes**: Understand existing code before modifying. Extend, don't duplicate
- **Limited responsibility**: Each function solves one task, 20-30 lines max
- **Explicit errors**: Custom exceptions with informative messages. No blanket try-except
- **Modern Python**: Type annotations, pathlib, context managers

Use the `functional-clarity` skill for the full set of 22 principles and style guide.
Do NOT silently swallow exceptions or return defaults on errors.
EOF
