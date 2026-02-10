---
name: functional-clarity
description: This skill should be used when the user asks about "functional clarity", "функциональная ясность", "принципы функциональной ясности", fail-fast architecture, Error Hiding prevention, context-adaptive defaults, or asks to apply the Functional Clarity methodology. Also activates when the user says "apply our coding principles", "check against our style guide", "how should I handle errors according to our principles", or "review this against functional clarity". Provides a 22-principle methodology for building reliable, simple, and understandable Python software with emphasis on fail-fast error handling, explicit dependencies, and minimal cognitive load.
---

# Functional Clarity — Development Philosophy

A methodology for building reliable, simple, and understandable software. Every principle serves one goal: minimize cognitive load while maximizing code reliability.

## Core Values

**Simplicity** — the right solution is the simplest one that works.
**Reliability** — fail-fast, no Error Hiding, honest error reflection.
**Clarity** — code reads like a story, names explain intent.
**Maintainability** — every change reduces cost of future changes.

## The 22 Principles

### Responsibility & Structure

1. **Limited Responsibility** — Each function solves one task, 20-30 lines max. One reason to change.
2. **Minimal Changes** — Understand existing abstractions first. Extend, don't duplicate. High cost of rewriting.
3. **Architecture Supporting Change** — Every change should reduce cost of future changes, not just solve today's task.
4. **Domain-Oriented Generalization** — Group by business meaning, not technical similarity. No context-free utility functions.
5. **Separation of Business Logic and Infrastructure** — Business logic operates on abstractions, not concrete DB/HTTP/API implementations.

### Error Handling (Critical)

6. **Fail-Fast Architecture** — System must crash immediately on errors. Graceful degradation only via feature flags.
   - Feature flag OFF → early return (None/0/skip)
   - Feature flag ON → functionality required → errors crash
   - No try-catch "just in case", no defaults on errors, no logging without re-raise

7. **Explicit Error Handling** — Custom exception classes with informative messages. Exception hierarchies for flexible handling.

8. **Error Hiding Prevention** — Concrete techniques against exception swallowing:
   - `try-except Exception` without re-raise — FORBIDDEN
   - Returning defaults (None/0/[]) instead of exception — FORBIDDEN
   - Logging error and continuing — FORBIDDEN
   - Marking as "processed" when actually skipped — FORBIDDEN
   - Error reaction hierarchy: status field → error table/metric → raise

9. **Immediate Parameter Validation** — Validate inputs at function start. Fast exit on invalid conditions.

### Code Quality

10. **Expressive Naming** — Names express purpose and context. Verbs for functions, nouns for objects. Answers "what?" and "why?".
11. **Explicit Entity Relationships** — Dependencies visible through constructor params or function args. No global state, no hidden side effects.
12. **Transparent State Management** — Explicit state transitions, validity checks. Prefer immutable structures. Controlled interfaces for state changes.
13. **Complexity = Understanding, Not Size** — Clear 30-line function beats cryptic 10-line one. Document complex algorithms, skip obvious code.

### Technical Excellence

14. **Modern Python** — Python 3.11+, type annotations, context managers, pathlib, modern syntax.
15. **Minimal Dependencies** — Prefer stdlib. Encapsulate external deps behind interfaces. Isolate via factories and services.
16. **Testability** — Pure functions, isolated side effects, explicit I/O params. Testable code = modular code.
17. **Atomic Transactions** — Explicit locks and transactions for data integrity. Optimistic/pessimistic locking by context.
18. **External Interaction Timeouts** — Always set timeouts for network calls. Your SLO depends on it.

### Meta-Principles

19. **Understand the Problem First** — Ask clarifying questions. Verify understanding on simple examples. Read existing code before writing new.
20. **Prevent Logical Deadlocks** — Analyze event dependencies at design time. No cyclic waits in component lifecycle.
21. **Minimum Sufficient Solution** — Complexity matching the task. Excessive complexity = imprecise understanding. Start simple, complicate only when needed.
22. **Ruthless Deletion of Unused Code** — Delete immediately when unused. No "just in case" code. VCS remembers everything.

### Context-Adaptive Defaults

| Role | Defaults | Rationale |
|------|----------|-----------|
| FK dependency | Minimal for validity | Consumer doesn't care about details |
| Entry point (API, factory) | Maximal for usefulness | Consumer wants to work, not configure |
| Edge case | Explicitly different | Deviation must be visible |

**Default != Error Hiding**: Returning empty value on error is NOT a default, it's Error Hiding.

## Python Style Guide

1. **Simple, single-task functions** — one task, minimal side effects, 20-30 lines
2. **Fail-fast error handling** — no unnecessary try/finally, custom exceptions
3. **Minimal dependencies** — stdlib first, encapsulate external deps
4. **Modern Python** — 3.11+, context managers, pathlib, type annotations
5. **Expressive naming** — descriptive names, docstrings for complex logic
6. **Code organization** — clear public API, hidden helpers, group by functionality
7. **Testability** — pure functions, isolated side effects, `pytest.fail()` not `raise` in tests
8. **Timeouts** — all blocking operations and external calls must have timeouts

## Error Handling Patterns

```python
# CORRECT: Fail-fast with feature flag
def process_with_feature(data):
    if not settings.FEATURE_ENABLED:
        return 0  # Only legitimate early return
    result = _do_actual_work(data)  # Let exceptions bubble up
    return result

# CORRECT: Re-raise with context enrichment
try:
    result = external_api.call()
except ExternalApiError as e:
    raise ServiceError(f"Failed for {user_id=}") from e

# CORRECT: Honest error reflection in data
except Config.DoesNotExist as e:
    event.status = 'FAILED'
    event.error_message = str(e)
    event.save()

# FORBIDDEN: Error Hiding
try:
    do_something()
except Exception:
    logger.error("Failed")  # Swallowed!
    return None
```

## Reference Documentation

Full detailed content is available in reference files:

- **`references/00-principles.md`** — Complete 22 principles with detailed explanations and code examples (numbering: 1, 2, 2A, 3-22)
- **`references/01-style-guide.md`** — Universal style guide: functions, errors, dependencies, naming, testability, timeouts
- **`references/02-analyze-solution.md`** — Solution analysis philosophy
- **`references/03-developer-levels.md`** — Developer level definitions
- **`references/04-bash-instructions.md`** — Bash script guidelines: check bash version, use `#!/usr/bin/env bash`
- **`references/frameworks/python.md`** — Python-specific: modern syntax, pathlib, type annotations, pytest patterns

## Reference Loading Order

1. **SKILL.md** is always sufficient for applying principles during normal coding
2. IF user asks for detailed explanation of a specific principle → read `references/00-principles.md`
3. IF writing or reviewing code and need style guidance → read `references/01-style-guide.md`
4. ALWAYS read: `references/02-analyze-solution.md` — core philosophy of solution analysis
5. IF discussing developer levels, requirements, expectations, or code review standards → read `references/03-developer-levels.md`
6. IF writing bash scripts → read `references/04-bash-instructions.md`
7. IF writing Python code → read `references/frameworks/python.md`

## Integration

This skill complements `tdd-master`:
- **functional-clarity** defines HOW to write code (principles, style, architecture)
- **tdd-master** defines WHEN to write tests (Red-Green-Refactor workflow)

Both share the Fail-Fast and Error Hiding prevention philosophy.
