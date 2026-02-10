---
name: tdd-master
description: This skill should be used when the user asks to "write tests", "add tests", "create test", "implement feature", "fix bug", "TDD", "test-driven", "reproduce bug", "write failing test", "Red-Green-Refactor", or when implementing any new functionality that requires testing. Provides TDD methodology based on Kent Beck and Uncle Bob principles.
---

# TDD Master Skill

Test-Driven Development methodology for writing reliable, maintainable code.

## When to Activate

This skill activates automatically when:
- Implementing new features (write tests FIRST)
- Fixing bugs (reproduce with failing test FIRST)
- Writing or reviewing tests
- Refactoring code (ensure tests exist)

## Core Workflow: Red-Green-Refactor

### Step 1: Test List

Before coding, create a list of scenarios:

```markdown
## Test List for [Feature]
- [ ] Happy path: main scenario
- [ ] Edge case: empty input
- [ ] Edge case: boundary values
- [ ] Error case: invalid input
- [ ] Error case: external service failure
```

### Step 2: RED - Write Failing Test

Write test that defines expected behavior:

```python
def test__{what}__{scenario}__{outcome}():
    # Arrange
    order = Order(items=[Item(price=1500)])

    # Act
    discount = calculate_discount(order)

    # Assert
    assert discount == Decimal('150')
```

**CRITICAL**: Predict HOW the test will fail before running.

### Step 3: GREEN - Minimal Code

Write **MINIMUM** code to pass:
- Hardcoded values OK
- Simple if-statements OK
- "Fake it till you make it" OK

### Step 4: REFACTOR

After test passes:
- Remove duplication
- Improve naming
- Extract helpers
- Keep tests green

### Step 5: REPEAT

Next test from list until complete.

## Three Laws of TDD (Uncle Bob)

| # | Law |
|---|-----|
| 1 | Cannot write production code without failing test |
| 2 | Cannot write more test than sufficient to fail |
| 3 | Cannot write more production code than sufficient to pass |

## FIRST Principles

| Principle | Description |
|-----------|-------------|
| **F**ast | Tests run quickly |
| **I**ndependent | No test dependencies |
| **R**epeatable | Same result everywhere |
| **S**elf-validating | Clear pass/fail |
| **T**imely | Written BEFORE code |

## Fixture Defaults (P0 Pattern)

| Role | Defaults | Example |
|------|----------|---------|
| FK dependency | Minimal for validity | `Campaign(name='Test', status=ACTIVE)` |
| Entry point | Maximal for usefulness | `create_applicant(with_tilda=True, ...)` |
| Edge case | Explicitly marked | `create_applicant(with_tilda=False)` |

## Test Naming Convention

```python
# Pattern: test__{what}__{scenario}__{outcome}
def test__calculate_discount__order_over_1000__returns_10_percent(): ...
def test__calculate_discount__empty_order__returns_zero(): ...
def test__process_payment__timeout__raises_error(): ...
```

## External Service Mocking

### Dict-based States (Default - Sync APIs)

```python
def test_get_customer__exists(apibank):
    # Setup state
    apibank.reg_customer({'code': '123', 'fullName': 'Test'})

    # Execute
    result = service.get_customer('123')

    # Verify
    assert result.full_name == 'Test'
```

### Queue-based Responses (Async APIs Only)

```python
def test_threshold__fail(fns_admin, create_income_request):
    # Enqueue error response
    request = create_income_request(protocol.SmzPlatformError(...))

    # Execute
    tasks.register_income()

    # Verify
    request.refresh_from_db()
    assert request.state == IncomeRequestState.ERROR
```

## End-to-End Flow Pattern

**One test = One business flow from input to output.**

```python
# GOOD: Full flow
def test__welcome_email__full_flow():
    applicant = create_applicant(...)       # Input
    outbox = create_email_outbox(...)       # Step 1
    process_email_outbox()                  # Step 2
    assert len(mail.outbox) == 1            # Output

# BAD: Separate tests for each step
def test__create_outbox(): ...
def test__process_outbox(): ...
```

## Assertion Helpers

```python
from testing import AnyDict, ReStr, UnorderedList

# Partial dict matching
assert response == AnyDict({
    'status': 'success',
    'id': ReStr(r'[a-f0-9-]{36}'),
})

# Order-independent list
assert events == UnorderedList([event1, event2])
```

## Critical Anti-Patterns

### The Liar - Always Passes
```python
# BAD
def test_liar():
    assert True  # Useless
```

### Error Hiding in Tests
```python
# BAD: Exception can be swallowed
if not event.wait(timeout=2):
    raise TimeoutError('...')

# GOOD: pytest.fail() cannot be caught
if not event.wait(timeout=2):
    pytest.fail('Test timeout')
```

### Skipping Refactoring
> "The most common error is skipping the third step. Refactoring is critical." - Martin Fowler

## Framework Detection

**CRITICAL**: Before writing tests, detect which frameworks the project uses and load the corresponding reference documentation.

### Detection Steps

1. **Analyze project dependencies** — check `pyproject.toml`, `requirements.txt`, `setup.cfg`, `Pipfile`
2. **Scan imports** in existing test files — `import pytest`, `import django`, `import unittest`
3. **Check for config files** — `pytest.ini`, `conftest.py`, `manage.py`, `settings.py`

### Framework Reference Matrix

| Detected | Action | Reference File |
|----------|--------|----------------|
| `pytest` in dependencies | Read pytest patterns | `references/frameworks/pytest.md` |
| `django` in dependencies | Read Django patterns | `references/frameworks/django.md` |
| Both pytest + Django | Read both files | Both files above |
| Neither detected | Use TDD_GUIDE only | `references/TDD_GUIDE.md` |

### Detection Signals

**Pytest project:**
- `conftest.py` exists
- `pytest.ini` or `[tool.pytest]` in `pyproject.toml`
- `pytest` in dependencies
- Test files use `def test_...` without class

**Django project:**
- `manage.py` exists
- `settings.py` or `DJANGO_SETTINGS_MODULE` env
- `django` in dependencies
- `pytest-django` in dependencies
- `@pytest.mark.django_db` in test files

### Loading Order

```
1. ALWAYS read: references/TDD_GUIDE.md (core methodology)
2. ALWAYS read: references/P0_DEFAULT_CONTEXT.md (context-adaptive defaults)
3. IF pytest detected: references/frameworks/pytest.md
4. IF django detected: references/frameworks/django.md
```

## Reference Documentation

### Always Loaded

- **`references/TDD_GUIDE.md`** - Core TDD methodology (Kent Beck, Uncle Bob, FIRST principles, anti-patterns)
- **`references/P0_DEFAULT_CONTEXT.md`** - Context-adaptive default values (FK=minimal, entry=maximal, edge=explicit)

### Framework-Specific (loaded based on detection)

- **`references/frameworks/pytest.md`** - Pytest patterns: fixtures, markers, assertion helpers, mocking, conftest organization
- **`references/frameworks/django.md`** - Django patterns: django_db, factory_boy, background tasks, signals, ESB events, timezone testing

## Integration with Other Agents

Other agents can call tdd-master when tests are needed:

- **Before implementation** — call tdd-master to write failing tests, then implement code to pass them
- **During code review** — verify new code has tests, flag missing tests as P1 issue

## Quick Checklist

### Before Writing Test:
- [ ] Create test list
- [ ] Read reference docs
- [ ] Understand expected behavior

### When Writing Test:
- [ ] ONE behavior per test
- [ ] Name describes scenario
- [ ] Minimal setup
- [ ] Specific assertions

### Before Writing Code:
- [ ] Test fails for RIGHT reason
- [ ] Predicted failure matches actual

### After Test Passes:
- [ ] Code is minimal
- [ ] Refactoring done
- [ ] Tests still green

## Critical Rules

- Write tests BEFORE implementation
- Predict failure before running
- Write minimal code to pass
- Always refactor after green
- Use `pytest.fail()` not `raise Exception`
- Mock only external services
