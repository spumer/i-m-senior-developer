---
argument-hint: [feature directory or description]
description: Orchestrate feature implementation with architecture, coding, and review phases
---

# Task

You are orchestrating implementation for: $ARGUMENTS

## Stage 0 — Planner (опциональный, рекомендуется для L-фич)

Перед запуском architect-фазы:

1. Если в директории фичи (путь — см. `planner-context.md`) нет
   `PLANNER_OUTPUT.md` ИЛИ фича визуально крупная (несколько модулей,
   миграции, cross-stack) — вызови агента `planner` в режиме
   **architecture planning** (или slash-команду `/plan`).
   - При первом запуске в проекте planner выполнит bootstrap: создаст
     `<project-root>/.claude/planner-context.md` с каталогами агентов,
     команд, skills и путей хранения фич.
2. Оркестратор читает `PLANNER_OUTPUT.md` и исполняет architect-фазу по
   нему (одного архитектора или N параллельных, модель и skills — из плана).
3. Перед implementation-фазой снова вызови `planner` в режиме **execution
   planning** — на входе готовый архитектурный план. Он обновит
   `PLANNER_OUTPUT.md`.

**Когда пропустить planner:**
- Маленькая фича (S: 1 модуль, <200 LOC, нет миграций).
- Bugfix в одной функции.
- Пользователь явно сказал «без planner» / «быстро».

Planner — оптимизатор, а не обязательный гейт.

## Workflow

Мульти-агентный конвейер с чётким разделением ответственности. Конкретные
имена агентов проекта — в `<project-root>/.claude/planner-context.md` §1.
Абстрактные роли ниже — маппинг на реальные имена делает оркестратор.

1. **architect** — проектирует архитектуру, модели данных, контракты. БЕЗ КОДА.
2. **implementer** — пишет код по плану. Может запускаться параллельно для
   независимых частей плана.
3. **reviewer** — запускает тесты, линтеры, находит проблемы, создаёт
   review-файлы.
4. **keeper** (после завершения фичи) — извлекает стабильные решения в
   проектную документацию.

## Implementation Loop

Для каждого стейджа:

### Step 1: Architecture
Запусти **architect** — создаёт/обновляет архитектурный план.

### Step 2: Implementation
Запусти **implementer** по плану. Можно несколько **implementer**-ов в
параллель для НЕЗАВИСИМЫХ частей плана (см. PLANNER_OUTPUT.md, если есть).

### Step 3: Review
Запусти **reviewer** — тесты, линтеры, проверка кода.

### Step 4: Fix or Complete
- Если reviewer нашёл проблемы → возврат к Step 1 с review-файлами.
- Если проблем нет → стейдж завершён.

### Step 5 (после завершения фичи): Documentation
Запусти **keeper** — обновление проектной документации стабильными
решениями (конкретные файлы — из `planner-context.md` §5).

### Step 6 (после завершения фичи): Reflect
Опционально предложи пользователю запустить `/plan-reflect` — пост-задачная
рефлексия с обновлением `planner-context.md` (gap-fill, model-strength,
user-corrections, cost-calibration). Особенно полезно после L-фич.

## Directory Structure

Конкретный путь к директории фич — в `planner-context.md` §5. Типовые
варианты:

```
<features-root>/
  FEAT-[0-9]{4}-<slug>/
    README.md                       # Requirements (из /plan-feat)
    FEAT-XXXX-PLAN-0N.md            # Architecture plan
    PLANNER_OUTPUT.md               # Planner output (optional)
    review-request-changes/         # Review findings
      FEAT-XXXX-ISSUE-0NN.md
      FEAT-XXXX-ISSUE-0NN_solved.md
    .test-output/                   # Test results
```

Если проект использует другой паттерн — следуй тому, что записано в
`planner-context.md`.

## Critical Rules

- **Separation of Concerns:** каждый агент имеет одну ответственность.
  - architect = design only (no code, no tests)
  - implementer = code only (no tests)
  - reviewer = test & review only
  - keeper = docs only (no code, no features)
- **Artifact Storage:** все файлы в директории фичи.
- **Loop Until Clean:** продолжать до тех пор, пока reviewer не перестанет
  находить проблемы.
- **Agent Knowledge:** каждый агент знает свои обязанности из своего .md.
  Имена и соответствия — в `planner-context.md` §1.
- **Проектные контекстные файлы** (UI guidelines, testing guide, project
  overview) используй, только если они перечислены в `planner-context.md`
  §5. Не придумывай несуществующие пути.
