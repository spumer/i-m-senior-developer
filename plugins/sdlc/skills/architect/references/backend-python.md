# backend-python — design angle

> Design decisions for Python backends. This file covers the **design angle only**: which framework, how to draw bounded contexts, how to model the data layer, where async/sync boundaries live, how to design background task infrastructure. No implementation code, no test patterns, no review checklists.

## When to load

Load when SKILL.md stack-detection finds Python markers (`pyproject.toml`, `requirements.txt`, Django/FastAPI/Flask/SQLAlchemy in dependencies) and the design touches data, services, ORM, or background tasks.

## Framework decision matrix

Pick the smallest framework that fully covers requirements. Escalate only when requirements demand a feature the smaller framework does not provide.

| Framework | When to pick | When to avoid |
|---|---|---|
| **Django** | Full-stack with admin panel; team knows Django ORM; batteries wanted (auth, sessions, migrations, signals); monolith OK | Pure API-only service where admin/templates are dead weight; high async concurrency (native async is bolt-on) |
| **FastAPI** | API-first service; async I/O concurrency required; strong type-driven design (Pydantic); OpenAPI spec auto-generation needed | If admin UI is in scope without a separate service; small scripts where framework overhead is not justified |
| **Flask** | Minimal utility service; legacy compatibility needed; team owns an existing Flask codebase | New projects where Django or FastAPI answers the same question — Flask's minimal surface requires more manual wiring |
| **SQLAlchemy (stand-alone)** | Data layer without an HTTP framework (ETL, scripts, background workers); framework-agnostic ORM needed | When using Django — Django ORM is the correct pairing; mixing SQLAlchemy + Django creates two ORM mental models |

**Decision rule (FPF A.11 — parsimony):** Do not pick FastAPI "because it's modern" if Django answers the same question with less wiring. Do not pick Flask for a new API service if FastAPI provides the needed type safety out of the box.

## Bounded contexts in Python backends

A bounded context in a Django project corresponds to a **Django app**. One app = one bounded context. The seam between apps is the contract, not the import.

The design rule: cross-app communication must go through an explicit seam (event bus, service interface, public events module) — not through direct ORM imports of another app's models. If your design allows app B's view layer to import app A's model directly, you have published the entire ORM as the contract; refactoring app A becomes a cross-app breaking change. Name the seam type (event-driven / service-call / shared-read-model) per app pair in the Hand-off Contracts table.

Cross-app FK chains in Django (a model in `app_b` has a ForeignKey to a model in `app_a`) are not inherently wrong at the ORM level, but they must be a **conscious design decision** noted in the Hand-off Contracts table. Every cross-app FK is a coupling that makes the apps impossible to extract later.

**FastAPI** does not have an app-level boundary mechanism. The designer must impose it explicitly:
- Each bounded context = one router (in `routers/`) + one service module (in `services/`) + one repository module (in `repositories/`)
- Cross-context calls go through the service layer, never between repositories directly

**SQLAlchemy stand-alone:** Contexts share the same session factory but each context owns its set of mapped models. Cross-context queries that join across context-owned tables are a seam risk — name them in Integration Points.

## Data layer design

Design-time decisions that must be settled before any implementation begins:

**Aggregate roots vs anemic models.** Does each model carry business logic (rich domain model) or is logic in services (anemic model)? Pick one per bounded context and state it in the architecture document. Mixing both within the same context produces schizophrenic code where some logic is in the model and some is in the service.

**Access pattern analysis.** Identify at design time: which queries are read-heavy (candidates for `select_related` or `prefetch_related`), which are write-heavy (candidates for `bulk_create`/`bulk_update`), which require transactional consistency. Document these access patterns in Data Flow — the implementer will translate them into the correct ORM calls.

**Repository abstraction.** Abstract the repository layer (interface + concrete implementation) only if ≥2 storage backends are a stated requirement (e.g. PostgreSQL + read-replica, or PostgreSQL + test SQLite). Otherwise YAGNI (FPF A.11) — the service calling the ORM directly is the simpler design.

**Migration strategy.** Settle at design time, before the first migration ships:
- Forward-only migrations (default for most projects): simpler, no rollback path
- Reversible migrations (required if zero-downtime deploys mandate roll-back): every migration has a `reverse_sql` or `backwards` function
Document the choice in the architecture. Changing from forward-only to reversible after migrations have shipped is painful.

## Async vs sync

This is a design-time decision. It cannot be retrofitted cleanly once the project is live.

```
Do you have IO-bound concurrency requirements?
  (e.g. thousands of simultaneous long-lived HTTP connections,
  WebSocket clients, external API fan-out, streaming)
  │
  ├── YES → FastAPI (async-native from the start)
  │         Note the async boundary in architecture:
  │         which layers are async, which are sync,
  │         where sync_to_async wrappers are needed
  │
  └── NO  → Django (sync-native; simpler mental model)
            If async is needed at one point (e.g. WebSocket channel):
            use Django Channels; document the boundary explicitly
```

**Mixed async/sync boundary:** If the project has both sync and async code (common in Django + Channels or Django + Celery), name the boundary explicitly in the architecture document's Integration Points. The boundary is where `sync_to_async` / `async_to_sync` wrappers must appear. This is a design seam, not an implementation detail.

## Background tasks design

Background task infrastructure must be chosen and documented at design time. The wrong choice is hard to undo once workers are running in production.

| Option | Durability | Infra cost | Use case |
|---|---|---|---|
| **Celery + Redis/RabbitMQ** | Durable (queue persisted) | Medium (broker required) | Complex workflows, retry logic, ETA/countdown, chained tasks |
| **Django-RQ** | Durable (Redis queue) | Low (Redis only) | Simple background jobs, team already has Redis |
| **APScheduler / django-apscheduler** | In-process (not durable across restart) | None | Periodic jobs where data loss on restart is acceptable |
| **Cloud queues (SQS, Cloud Tasks)** | Durable (cloud-managed) | Managed | Cloud-native projects; avoid if running on-prem |

**Design output required:** The architecture document must name:
- The queue name (or set of queues if priority lanes are needed)
- The worker process (separate service or same dyno)
- The persistence backend (Redis, RabbitMQ, SQS)
- The retry policy (max retries, backoff strategy)
- The failure destination (dead-letter queue or alert)

**Design only:** Do not design the worker function code — that is implement angle. Name the task contract (input, output, side effects) in Hand-off Contracts.

## API surface in Python

When the Python backend exposes or consumes an API, load `references/api-design.md` for the protocol and contract design. This section covers only the Python-specific abstraction choice.

**DRF Serializers vs FastAPI Pydantic models vs raw Django views:**

| Abstraction | When to use |
|---|---|
| Django REST Framework serializers | Django project, CRUD-heavy API, admin integration needed, team knows DRF |
| FastAPI + Pydantic models | New API-first service, strong typing required, auto-OpenAPI wanted |
| Raw Django views (class-based or function-based) | Narrow internal API where DRF overhead is not justified |

**Decision rule:** Pick one abstraction and commit to it for the entire project. Do not mix DRF serializers and FastAPI Pydantic models in the same service — this creates two serialization mental models and two validation code paths.

Document the chosen abstraction in the architecture document's Bounded Contexts section (e.g. "all API inputs/outputs are typed Pydantic models; DRF is not used").

## Common design pitfalls

- **Business logic in views/routers.** Views and routers are I/O adapters, not business logic containers. Logic in a view cannot be called from a Celery task or a management command without importing the request cycle. Name the service layer in the architecture explicitly.

- **Cross-app raw SQL (Django).** `django.db.connection.execute()` with a query that JOINs across bounded contexts bypasses ORM-level seams and makes refactoring invisible. Flag any cross-context raw SQL as a design concern in Open Questions.

- **Global session scope (SQLAlchemy).** A module-level `Session()` instance shared across requests produces race conditions in concurrent environments. The architecture must specify session scope: per-request via FastAPI `Depends`, per-unit-of-work via context manager. Name it in the design.

- **ORM model as domain object.** Passing ORM model instances (Django model, SQLAlchemy mapped class) across context boundaries couples the receiver to the ORM. Design-time fix: define a plain dataclass or Pydantic schema as the cross-context contract; ORM model stays inside its context.

- **"We'll add caching later."** Cache invalidation is a design decision, not an afterthought. Identify at design time which endpoints are cache-bearing, what the cache key is, and what invalidates it. Document in Integration Points even if implementation of caching is deferred to a later phase.

- **Circular dependencies between apps (Django).** If `app_a` imports from `app_b` and `app_b` imports from `app_a`, neither is a bounded context — both are fragments of a larger context that hasn't been named. Resolve by naming the owning context and moving the shared concept there.

- **Celery tasks with direct model access.** When a background task imports and calls an ORM model directly, it couples the task to the database schema. The architecture should define a task contract (the input is a serializable payload, not a model instance) and name who produces that payload.

## Design checklist for Python backends

Before finalizing the architecture document for a Python backend, verify:

- [ ] Framework chosen with a stated reason (not "because it's popular")
- [ ] Every Django app = one named bounded context
- [ ] Service layer named if business logic is non-trivial
- [ ] ORM session scope declared (per-request, per-unit-of-work, or stand-alone)
- [ ] Async/sync boundary decision documented if async is in scope
- [ ] Background task infrastructure named (queue, worker, retry policy)
- [ ] Cross-app FK chains listed in Hand-off Contracts
- [ ] API abstraction choice (DRF vs Pydantic vs raw views) stated in Bounded Contexts
- [ ] Cache-bearing endpoints identified in Integration Points
