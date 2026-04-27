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

## Migrations

**Django:** `makemigrations` → review SQL (`sqlmigrate`) → `migrate`.
Reversible operations only unless the ARCH document states otherwise.
Data migrations in separate files (`RunPython` blocks). Never edit a
migration after it ships to any shared environment.

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

## Common implementation pitfalls

- **No `transaction.atomic`** on multi-step writes — one failure
  leaves partial state.
- **Tests against shared DB** — use `pytest-django` transactional
  rollback fixture (`db` / `transactional_db`) to isolate each test.
- **Signals as primary control flow** — receiver order is
  non-deterministic; use services at the domain layer instead.
- **`except Exception: pass`** — Error Hiding; catch specific types,
  let unexpected exceptions propagate. See
  `functional-clarity:functional-clarity`.
- **Skipping `mypy`** because tests cover it — types catch a
  different bug class than tests.
