# backend-python — implement angle

> **Angle:** implement only. Design rationale lives in
> `architect/references/backend-python.md`. Review checklists live
> in `code-reviewer/references/backend-python.md`.

## When to load

Load when `SKILL.md` stack-detection finds Python markers
(`pyproject.toml`, `requirements.txt`, `manage.py`, `fastapi` /
`django` / `flask` in dependencies).

## Project structure conventions

Follow the project's existing layout. If none exists, propose:

**Django:** `<app>/models.py`, `<app>/views.py`, `<app>/services.py`
(business logic; views stay thin), `<app>/tests/`.

**FastAPI:** `routers/` (HTTP only), `services/` (use cases),
`repositories/` (data access), `schemas/` (Pydantic), `tests/`.

**Flask:** per blueprint — `<blueprint>/routes.py`, `services.py`,
`tests/`.

Rule: follow the project's convention. If absent, ask before imposing.
Do not mix conventions in one project.

## ORM patterns (Django)

`select_related` for single-valued FK / OneToOne. `prefetch_related`
for M2M / reverse FK. Decide at the queryset, not inside the loop.

```python
users = User.objects.select_related("profile").filter(active=True)
posts = Post.objects.prefetch_related("tags").all()
```

Bulk writes — single query:

```python
Item.objects.bulk_create([Item(name=n) for n in names])
Item.objects.filter(pk__in=ids).update(status="done")
```

Service-layer transactions:

```python
from django.db import transaction

@transaction.atomic
def transfer(from_user, to_user, amount):
    from_user.balance -= amount
    to_user.balance += amount
    from_user.save(); to_user.save()
```

`update_or_create` for upserts; wrap in `transaction.atomic` when
surrounding logic must be consistent.

## SQLAlchemy patterns

Session scope: one session per request. FastAPI dependency:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Eager loading at query time — `selectinload` for collections (2 queries,
safe for large sets); `joinedload` for single FK (1 JOIN). Unit-of-work:
commit once at the service boundary, not inside loops.

## pytest fixtures

Function scope by default. Widen to `module` / `session` only for
expensive read-only resources.

```python
# Django — transactional rollback per test
@pytest.fixture
def user(db):          # pytest-django 'db' handles rollback
    return UserFactory()

# FastAPI — override DB dependency
@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()
```

`factory_boy` for model creation — keep tests independent. Use
`pytest-asyncio` + `@pytest.mark.asyncio` for async FastAPI routes.

Anti-pattern: shared mutable fixtures across tests — causes
ordering-dependent failures.

**`--reuse-db` can show stale failures.** With `pytest-django --reuse-db`
the test DB keeps the prior schema/seed, so a migration- or seed-dependent
test may fail against a stale DB. Before blaming your change, re-run the
affected tests with `--create-db` (rebuilds from migrations). Only a
`--create-db` failure is evidence of a real regression (FPF A.10).

## Wire-contract tests (serialization boundary)

A green suite that asserts the inner DTO does NOT prove a field reaches the
client. When a value crosses a serialization/interface boundary — Django
serializer / `TypedDict` → FastAPI Pydantic out-model, a hand-written mapper,
or two handlers for the same data (REST view vs MCP tool) — the mapper can
silently drop the field while every inner test stays green.

Rule: when you add or change a field on a response contract, assert it on the
*real serialized output*, not the intermediate object.

```python
def test_event_out_exposes_submission_url(client, event):
    resp = client.get(f"/events/{event.id}")
    assert resp.status_code == 200
    assert resp.json()["submission_url"] == event.submission_url  # fails before mapper fix
```

- Drive it through the real chain (`TestClient` / Django `Client`); assert on
  `resp.json()`, not the view/serializer return value.
- The test must FAIL before the mapper change and PASS after (RED-GREEN via `tdd-master`).
- Cover every render path that serves the field: list AND detail, and every
  parallel handler (REST AND MCP tool) — a field added to one mapper is not
  automatically in the other.
- Same gate for a brand-new endpoint or MCP tool: at least one test exercising
  the real serialized response end-to-end.

## mypy configuration and patterns

```toml
[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["mypy_django_plugin.main"]  # or sqlalchemy-stubs

[[tool.mypy.overrides]]
module = ["third_party_without_stubs.*"]
ignore_missing_imports = true
```

Common patterns: `TypedDict` for untyped dict shapes; `Protocol` for
duck-typing at service boundaries (prefer over `Any`); `Annotated`
for FastAPI metadata. Use `cast` only when narrowing is provably
correct — never to silence a misunderstood error.

## Strict type-checker patterns (basedpyright / pyright strict)

When the project runs `basedpyright`/`pyright` in strict mode, freshly
written Django/pytest test modules repeatedly trip the same patterns. Apply
them up front instead of paying a later type-cleanup pass:

- **Build users with the typed manager.** `User.objects.create(...)` (typed)
  rather than `create_user(...)` (often untyped/`Any` in stubs). Pass
  `password` only when the test needs auth.
- **Acknowledge the pytest-django `db` fixture.** A bare `db` param reads as
  unused under strict: bind it `_ = db`, or use `@pytest.mark.usefixtures("db")`.
- **`cast()` late-bound attributes** (reverse relations, `*_set`, dynamically
  added fields) only when the cast is provably correct — never to silence a
  misunderstood error.
- **Annotate dicts fully** — `dict[str, Any]` / `dict[str, str]`, never bare
  `dict` (which is `dict[Unknown, Unknown]` under strict).
- **Narrow ORM meta before use** — `if isinstance(field, models.Field):`
  before touching field-specific attributes; the meta API is loosely typed.
- **FK id shortcuts** — reference `obj.related_id` (the late-bound `*_id`)
  instead of `obj.related.pk` when you only need the key.
- **Guard `Optional` before method calls** — `dt.isoformat()` on an
  `Optional[datetime]` fails strict; guard or assert non-None first.
- **`# pyright: ignore[<rule>]` is last resort, always with a named rule and a
  one-line reason** — bare `# pyright: ignore` is forbidden (same discipline
  as `# type: ignore`).

## Migrations

**Django:** `makemigrations` → review SQL (`sqlmigrate`) → `migrate`.
Reversible operations only unless the ARCH document states otherwise.
Data migrations in separate files (`RunPython` blocks). Never edit a
migration after it ships to any shared environment.

**DoD gate — `makemigrations --check`.** Any model-field change, including
adding a value to `TextChoices` / `IntegerChoices` / an Enum, can silently
require a migration. Before hand-off run `python manage.py makemigrations
--check --dry-run`; a non-zero exit means a migration is missing — generate
it now, do not defer to review (it surfaces there as a P0). Add the command
to the report's "Commands run".

**Alembic:** `alembic revision --autogenerate` → review → apply.
Implement `downgrade()` unless explicitly designated irreversible.
Test both `upgrade` and `downgrade` in CI.

## Async/sync boundary patterns

Django ORM is synchronous. In async contexts use `sync_to_async`:

```python
from asgiref.sync import sync_to_async
users = await sync_to_async(list)(User.objects.filter(active=True))
```

FastAPI + SQLAlchemy sync session — off-load to thread pool:

```python
return await asyncio.to_thread(db.query(Item).get, item_id)
```

Failure mode: calling sync ORM directly in `async def` blocks the
event loop and degrades all concurrent requests.

## Extending existing behavior

When the feature is "another one like X", mirror the analogous existing
implementation rather than duplicate or rewrite it:

- **Find the analogue.** Locate the existing function that already does the
  closest thing (an existing `create_*` / `issue_*` flow next to the one you
  are adding). Mirror its structure and call its public helpers — do not
  copy-paste the helper bodies. Shared logic stays in one place.
- **Extend, don't break the signature.** To add a capability to a shared
  helper, add an *optional* parameter whose default reproduces current
  behavior, so every existing call site is unchanged (e.g.
  `def issue_token(..., ttl_seconds: int | None = None)`). A new required
  parameter, a changed return type, or a changed default is a contract change
  — see SKILL.md "Don't change contract without discussion" (Code-Change
  Discipline rule 6).
- **Preserve overridable hooks across a refactor (FPF A.7 — role vs
  implementation).** If a method is a documented or `_`-private extension
  point that downstream code overrides (e.g. a `_build_headers` hook), its
  *role* is "override seam", not just its current body. Keep the seam as a
  thin overridable shim when you refactor so subclasses/callers do not break —
  removing it silently is information-removal (Code-Change Discipline rule 7).

Parsimony default (FPF A.11): prefer composing existing primitives + a
backward-compatible extension over a new parallel implementation.

## Common implementation pitfalls

- **No `transaction.atomic`** on multi-step writes — one failure
  leaves partial state.
- **Tests against shared DB** — use `pytest-django` transactional
  rollback fixture (`db` / `transactional_db`) to isolate each test.
- **Fixtures that fake the write-path for cross-module data** — when the code
  under test READS data a *different* module WRITES, build the fixture by
  calling that module's real writer (the service function or signal, e.g.
  `grant_achievement(...)`), not `Model.objects.create(...)` and not a curated
  pool. A direct `.create()` can set fields the real path never sets
  (`team=team`, `actor_id=...`) while production writes `None` — the suite goes
  green over a feature that is dead in prod. A `factory_boy` factory is fine for
  data this module owns; it is not a substitute for another module's real producer.
- **Signals as primary control flow** — receiver order is
  non-deterministic; use services at the domain layer instead.
- **`except Exception: pass`** — Error Hiding; catch specific types,
  let unexpected exceptions propagate. See
  `functional-clarity:functional-clarity`.
- **Skipping `mypy`** because tests cover it — types catch a
  different bug class than tests.
