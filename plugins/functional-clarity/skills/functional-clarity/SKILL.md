---
name: functional-clarity
description: This skill should be used when the user asks about "functional clarity", "функциональная ясность", "принципы функциональной ясности", fail-fast architecture, Error Hiding prevention, context-adaptive defaults, error handling patterns, refactoring principles, or asks to apply the Functional Clarity methodology. Also activates when the user says "apply our coding principles", "check against our style guide", "review this against functional clarity", "how should I handle errors", "рефакторинг", "обработка ошибок", or "code review against our standards". Provides a 22-principle methodology for building reliable, simple, and understandable software with emphasis on fail-fast error handling, explicit dependencies, and minimal cognitive load.
---

# Functional Clarity — Development Philosophy

A methodology for building reliable, simple, and understandable software. Every principle serves one goal: minimize cognitive load while maximizing code reliability.

## Core Values

**Simplicity** — the right solution is the simplest one that works.
**Reliability** — fail-fast, no Error Hiding, honest error reflection.
**Clarity** — code reads like a story, names explain intent.
**Maintainability** — every change reduces cost of future changes.

## Foundation

Analyze your solutions to extract general principles and apply them to new tasks. This works not only for technical tasks but for any challenge. Programming reflects reality — solutions are inseparable from the real world. A principle works everywhere; if there's an exception, it's not a principle.

## The 22 Principles

Numbering follows the original scheme: 1, 2, 2A, 3–22.

### Responsibility & Structure

1. **Limited Responsibility** — Each function solves one task, 20-30 lines max. One reason to change.
2. **Minimal Changes** — Understand existing abstractions first. Extend, don't duplicate. High cost of rewriting.
2A. **Fail-Fast Architecture** — System must crash immediately on errors. Graceful degradation only via feature flags.
   - Feature flag OFF → early return (None/0/skip)
   - Feature flag ON → functionality required → errors crash
   - No try-catch "just in case", no defaults on errors, no logging without re-raise
3. **Architecture Supporting Change** — Every change should reduce cost of future changes, not just solve today's task.
4. **Explicit Error Handling** — Custom exception classes with informative messages. Exception hierarchies for flexible handling.
5. **Minimal Dependencies** — Prefer stdlib. Encapsulate external deps behind interfaces. Isolate via factories and services.

### Code Quality

6. **Domain-Oriented Generalization** — Group by business meaning, not technical similarity. No context-free utility functions.
7. **Expressive Naming** — Names express purpose and context. Verbs for functions, nouns for objects. Answers "what?" and "why?".
8. **Explicit Entity Relationships** — Dependencies visible through constructor params or function args. No global state, no hidden side effects.
9. **Transparent State Management** — Explicit state transitions, validity checks. Prefer immutable structures. Controlled interfaces for state changes.
10. **Separation of Business Logic and Infrastructure** — Business logic operates on abstractions, not concrete DB/HTTP/API implementations.

### Validation & Safety

11. **Immediate Parameter Validation** — Validate inputs at function start. Fast exit on invalid conditions.
12. **Atomic Transactions** — Explicit locks and transactions for data integrity. Optimistic/pessimistic locking by context.
13. **Complexity = Understanding, Not Size** — Clear 30-line function beats cryptic 10-line one. Document complex algorithms, skip obvious code.
14. **Modern Python** — Python 3.11+, type annotations, context managers, pathlib, modern syntax.
15. **Testability** — Pure functions, isolated side effects, explicit I/O params. Testable code = modular code.

### Meta-Principles

16. **Understand the Problem First** — Ask clarifying questions. Verify understanding on simple examples. Read existing code before writing new.
17. **Prevent Logical Deadlocks** — Analyze event dependencies at design time. No cyclic waits in component lifecycle.
18. **Minimum Sufficient Solution** — Complexity matching the task. Excessive complexity = imprecise understanding. Start simple, complicate only when needed.
19. **Ruthless Deletion of Unused Code** — Delete immediately when unused. No "just in case" code. VCS remembers everything.

### Error Hiding Prevention (Principle 20)

Concrete techniques against exception swallowing:
- `try-except Exception` without re-raise — FORBIDDEN
- Returning defaults (None/0/[]) instead of exception — FORBIDDEN
- Logging error and continuing — FORBIDDEN
- Marking as "processed" when actually skipped — FORBIDDEN
- Error reaction hierarchy: status field → error table/metric → raise

### External Interactions (Principle 21)

Always set timeouts for network calls. Your SLO depends on it.

### Context-Adaptive Defaults (Principle 22)

| Role | Defaults | Rationale |
|------|----------|-----------|
| FK dependency | Minimal for validity | Consumer doesn't care about details |
| Entry point (API, factory) | Maximal for usefulness | Consumer wants to work, not configure |
| Edge case | Explicitly different | Deviation must be visible |

**Default != Error Hiding**: Returning empty value on error is NOT a default, it's Error Hiding.

## Style Guide

1. **Simple, single-task functions** — one task, minimal side effects, 20-30 lines
2. **Fail-fast error handling** — no unnecessary try/finally, custom exceptions
3. **Minimal dependencies** — stdlib first, encapsulate external deps
4. **Expressive naming** — descriptive names, docstrings for complex logic
5. **Code organization** — clear public API, hidden helpers, group by functionality
6. **Testability** — pure functions, isolated side effects, `pytest.fail()` not `raise` in tests
7. **Timeouts** — all blocking operations and external calls must have timeouts

See `references/01-style-guide.md` for the full version with details.

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

- **`references/00-principles.md`** — Complete 22 principles with detailed explanations and code examples
- **`references/01-style-guide.md`** — Full style guide with details on each point
- **`references/03-developer-levels.md`** — Developer level definitions (Junior → Senior+)
- **`references/04-bash-instructions.md`** — Bash script guidelines
- **`references/frameworks/python.md`** — Python-specific: modern syntax, pathlib, type annotations, pytest patterns

## Reference Loading Order

1. **SKILL.md** provides the working summary for applying principles during coding
2. IF user asks for detailed explanation of a specific principle → read `references/00-principles.md`
3. IF writing or reviewing code and need detailed style guidance → read `references/01-style-guide.md`
4. IF discussing developer levels, requirements, expectations, or code review standards → read `references/03-developer-levels.md`
5. IF writing bash scripts → read `references/04-bash-instructions.md`
6. IF writing Python code → read `references/frameworks/python.md`

## Integration

This skill complements `tdd-master`:
- **functional-clarity** defines HOW to write code (principles, style, architecture)
- **tdd-master** defines WHEN to write tests (Red-Green-Refactor workflow)

Both share the Fail-Fast and Error Hiding prevention philosophy.

If the user asks about writing tests, TDD, or test-driven development and the `tdd-master` skill is not available, recommend installing the `tdd-master` plugin from the same repository: `plugins/tdd-master/`.
