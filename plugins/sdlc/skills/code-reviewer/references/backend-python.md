# backend-python.md — Code Reviewer: Python-Specific Pitfalls

> **Angle:** review only. This file documents what to flag in a Python diff.
> It does not explain how to write Python code (implement angle) or how to
> design Python services (architect angle). Content overlap with those files
> is a defect.

## When to load

Load when the diff contains `*.py` files. Always load alongside `security.md` (never instead of it).

---

## Django security specifics

Beyond the OWASP Top 10 in `security.md`, Django introduces its own surface:

- **`mark_safe()` and `|safe` filter** — any usage in a diff is a review item. Require justification. `mark_safe` on user-supplied content is XSS. Flag: `file:line — mark_safe on user-controlled value — XSS risk — remove mark_safe or sanitize with bleach`.
- **`raw()` querysets** — `Model.objects.raw("SELECT ... WHERE id=%s" % user_id)` → injection. Parameterized `raw("... WHERE id=%s", [user_id])` is acceptable if ORM cannot express the query; still flag for review of the SQL.
- **`extra()` queryset method** — effectively raw SQL. Flag every usage; confirm the `where`/`params` split is correct.
- **`DEBUG = True` in non-local settings** — already in `security.md` but also surfaces in Django stack traces visible to end users.
- **`SECRET_KEY` in committed file** — already in `security.md`. Django-specific: also check `settings.py`, `settings/base.py`, `settings/production.py`.
- **`ALLOWED_HOSTS = ['*']`** — production misconfiguration; flag if present outside a `local.py` / `test.py` settings file.
- **Missing `SECURE_*` settings** — for any production settings change, check: `SECURE_HSTS_SECONDS`, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`. Absence of all of these in a production settings file is a medium finding.

---

## N+1 queries

**Pattern to recognize:**

```python
# N+1: accessing a FK relation inside a loop without prefetch
for order in Order.objects.filter(status='pending'):
    print(order.user.email)  # hits DB for every iteration
```

**Review signal:** a `for` loop over a queryset where the loop body accesses `.related_model`, `.foreignkey_field`, or any reverse-relation accessor without a preceding `select_related` / `prefetch_related`.

**Severity:** high on list endpoints (scales with data); medium on detail endpoints.

**DRF nested serializers:** `SerializerMethodField` that calls `.all()` on a relation inside `to_representation` → N+1 per serialized object. Require `prefetch_related` on the view's `get_queryset`.

**Tooling cue (for implementer, not reviewer):** `django-debug-toolbar` or `nplusone` package detects these at runtime. The reviewer flags the structural pattern; the implementer verifies with tooling.

**Fix direction:** add `select_related('user')` or `prefetch_related('items')` to the queryset; document the access pattern in the view's queryset.

---

## ORM pitfalls

**`get_or_create` race condition:**

```python
# Race: two concurrent requests can both pass the get(), then both try create()
obj, created = MyModel.objects.get_or_create(field=value)
```

Without `transaction.atomic()`, concurrent requests can each fail the `get` and both attempt `create`, causing `IntegrityError`. Flag any `get_or_create` / `update_or_create` outside an atomic block when the model has a unique constraint.

**`update()` skipping `save()` signals:**

`queryset.update(field=value)` bypasses `pre_save` / `post_save` signals and custom `save()` logic. Flag if the surrounding code expects signals to fire (e.g. cache invalidation, audit log on save).

**`bulk_create` skipping validators:**

`Model.objects.bulk_create([...])` does not call `full_clean()` or `save()`. If the model has validation logic in `clean()` or signal handlers on `post_save`, those are bypassed. Flag when data integrity depends on them.

**Querying inside templates:**

Django template tags or template code calling ORM methods. Flag as an architectural boundary violation — data fetching belongs in views/services, not templates.

**`iterator()` exhausted and re-used:**

`qs = Model.objects.iterator()` — after iterating once, the iterator is exhausted. A second `for` loop over `qs` yields nothing. Flag any code that stores `iterator()` result in a variable and iterates it more than once.

---

## Transaction and atomicity

**Multi-step writes outside `transaction.atomic`:**

Any sequence of two or more `Model.save()` / `.create()` / `.update()` / `.delete()` calls that must succeed or fail together, without a wrapping `with transaction.atomic():`, is a finding. Partial state on failure is a data integrity bug.

```python
# Missing atomic: if second save fails, first is committed
user.save()
profile.save()  # if this raises, user is saved but profile is not
```

**Nested `atomic` and savepoints:**

`transaction.atomic()` blocks can nest; inner blocks use savepoints. A `transaction.on_commit()` callback inside a nested `atomic` fires only when the outermost transaction commits. Flag if a developer assumes `on_commit` fires immediately on the inner block exit.

**`select_for_update` requires atomic:**

`Model.objects.select_for_update()` must be inside `transaction.atomic()`. If not, `django.db.transaction.TransactionManagementError` is raised at runtime. Flag any `select_for_update` diff without an enclosing `atomic`.

**FastAPI / SQLAlchemy async transactions:**

`transaction.atomic()` is Django-sync only. In FastAPI + SQLAlchemy async code, session commit/rollback is the unit-of-work boundary. Flag sync-style `atomic` patterns imported into async FastAPI routes.

---

## Error handling and Error Hiding

Review lens from `functional-clarity:functional-clarity` Error Hiding principle:

- **Catch-all with pass:** `except Exception: pass` — the error disappears entirely. Flag as high finding: silent failures produce incorrect system state that is invisible to monitoring.
- **Catch and return success:** `except Exception: return {"status": "ok"}` — caller gets success signal for a failed operation. Flag as high finding.
- **Logging and continuing:** `except Exception as e: logger.error(e); return default_value` — if `default_value` masks a required value, this is still Error Hiding. Flag when the default masks a required field.
- **Swallowing `DoesNotExist`:** `except ObjectDoesNotExist: return None` — acceptable if `None` is a documented valid return; a finding if callers assume the object always exists.
- **`print()` for error reporting:** `except Exception as e: print(e)` — no structured logging, invisible in production. Flag as minor if no other log; flag as major if this replaces a removed `logger` call (information loss per `code-change-discipline.md` rule 7).

---

## Type-safety review

- **Missing type hints on public APIs:** new `def` without parameter and return type annotations → a finding. Priority: public functions, service-layer boundaries, API endpoints.
- **`Any` smuggled in:** `from typing import Any; def foo(x: Any)` — defeats static analysis. Flag when `Any` is used where a more specific type is knowable.
- **`# type: ignore` without comment:** `obj.method()  # type: ignore` — acceptable with a reason (`# type: ignore[attr-defined] — Django dynamic attribute`); a finding without explanation.
- **Runtime type assumptions not validated:** function receives `data: dict` from external source (request body, event payload) and accesses keys directly without Pydantic / dataclass validation. Flag on any new code path that ingests unvalidated external data.

---

## Test quality review

- **Tests testing the mock, not the system:** `assert mock_send_email.called` without checking what arguments were passed → the test passes even if the call is wrong. Flag: require `mock_send_email.assert_called_with(expected_args)`.
- **`assert mock.called` only:** as above — checks invocation count, not correctness.
- **No negative-path tests:** new endpoint or function with only a happy-path test. Flag as minor finding: "no test for error case / unauthorized case / empty input case."
- **Flaky tests skipped instead of fixed:** `@pytest.mark.skip("flaky")` in the diff → flag as technical debt; skipped tests give a false green.
- **Shared mutable fixtures:** a `@pytest.fixture(scope="module")` that mutates database state and is used across test functions → ordering-dependent flakiness. Flag when the fixture is clearly stateful.

---

## Common review items

- **Raw f-string SQL** — `cursor.execute(f"... {user_input}")` → injection; always flag as critical.
- **Django signals as primary control flow** — logic that is only reachable via a `post_save` signal, with no direct call path. Invisible to the code reader; breaks when signal is disconnected. Flag as design concern; suggest service layer.
- **Global mutable state** — module-level dict/list used as a cache or accumulator in a web process (shared across requests/threads). Flag as race condition risk.
- **`print()` left in production code** — flag as minor; replace with `logging.debug()` or remove.
- **`TODO` / `FIXME` without ticket reference** — flag as minor: "add ticket reference or resolve before merge."
