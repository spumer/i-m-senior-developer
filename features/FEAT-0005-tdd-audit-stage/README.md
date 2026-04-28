# FEAT-0005 — TDD count audit как обязательный stage в /plan-do

> **Статус:** Backlog Idea (требует Architecture)
> **Marketplace:** `i-m-senior-developer`
> **Категория:** development / pipeline
> **Связь:** расширяет `plan-do` skill в `plugins/planner/skills/plan-do/`. Подкрепляется memory `feedback_tdd_count_audit_pipeline_stage.md` (см. ниже) и `feedback_test_count_creep_per_slice.md`.

## Problem Statement

После implementation в `/plan-do` многие имплементеры пишут TDD per slice и параллельно — это даёт три класса избыточных тестов:

1. **Дубли через слои** — один и тот же инвариант проверяется в `test_models`, `test_migrations` и `test_engine` (FEAT-0017 БРС: 5 тестов на одни и те же поля Quest).
2. **Implementation-coupled** — тесты приватных хелперов (`_count_*`), завязанные на имена кэшей или порядок миграций. При рефакторинге ломаются массово, не давая семантического сигнала.
3. **Enum-value тесты** — проверяют наличие Python-литералов (`assert AchievementType.MILESTONE == "milestone"`), не ловят DB-контракт (FEAT-0017: 5 таких).

`code-reviewer` проверяет **функциональность** (есть ли N+1, есть ли security gap, корректна ли формула). Он не делает count audit, потому что это другая роль — кардинальность тестов и наличие параметризации/Liar-детекции.

В результате: пользователь замечает «N тестов многовато» уже после успешного code-review fix-loop'а, требует пост-фактум аудит, тесты сокращаются на 23-24%, теряется один цикл.

**Зафиксированные кейсы:**
- FEAT-0016 (mcp-interface, Контракция): 162 → 124 backend (-23%) после жалобы Founder'а «уххх многовато».
- FEAT-0017 (brs-transparency, Контракция): 97 → 74 backend (-24%), 42 → 41 frontend после второй такой же жалобы.

## User Journey

**Starting Point:** разработчик запускает `/plan-do features/FEAT-XXXX-…/`. Идёт стандартный pipeline: planner → architect → implementer (parallel BE+FE) → code-reviewer → keeper.

**Step-by-Step Flow:**

1. После Phase 3 (implementation) и ДО Phase 4 (code review) — оркестратор автоматически запускает новый stage **«TDD count audit»**.
2. Skill `tdd-audit` (новый, в `plugins/planner/skills/`) запускается на агенте `tdd-master` (если plugin предоставляет) ИЛИ `general-purpose` с mandate-блоком (project-aware fallback из `planner-context.md` §1).
3. Skill читает все новые/изменённые тесты из git diff, классифицирует:
   - дубли (один инвариант на разных слоях)
   - implementation-coupled (приватные функции)
   - enum-value (тестируют Python-литералы)
   - параметризуемые (несколько похожих с разными значениями → один `parametrize`)
   - Liar-тесты (имя ≠ что проверяет)
4. **Constraint:** НЕ удалять регрессионные тесты на блокеры из review (P0/P1). НЕ удалять edge-cases из README (бизнес-инварианты).
5. Применяет правки через Edit. Запускает `pytest -q` / `npm test -- --run` для верификации.
6. Возвращает отчёт: было N → стало M (-X%), список удалений с обоснованиями.
7. Только после этого — Phase 4 (code review) и Phase 5 (documentation).

**Skip-условие:** S-фича с <30 тестов — пропускать, overhead больше выгоды.

**End State:** к моменту merge тесты дедуплицированы и параметризованы. Founder не видит «многовато» как отдельную жалобу — это уже встроено в pipeline.

## Architectural Decisions (предварительно)

| # | Решение | Выбор | Обоснование |
|---|---------|-------|-------------|
| 1 | **Где встроить stage** | Между Phase 3 (implementation) и Phase 4 (code review) | Reviewer = функциональность, audit = кардинальность. Разные роли. Reviewer работает на дедуплицированном наборе тестов — снижает его контекст. |
| 2 | **Какой агент** | `tdd-master` если plugin SDLC активен, иначе `general-purpose+mandate` | Project-aware из `planner-context.md` §1 |
| 3 | **Модель** | Sonnet | По калибровке FEAT-0017: ~100k tokens, ~9 мин для L-фичи. Opus избыточен. |
| 4 | **Опциональность** | По умолчанию ON для L-фич, skip для S<30 тестов | Cost-benefit: на S овеnhead больше выгоды |
| 5 | **Constraint regression-safety** | Промпт обязан перечислить P0/P1 issue-файлы из review-request-changes/ как «не трогать» | Иначе сократит тест-регресс на блокер |
| 6 | **Альтернатива: расширить code-reviewer** | Отвергнуто (на этапе backlog) | Reviewer уже большой, две роли в одном промпте → разводнение качества обоих |

## Open Questions

1. **Trigger size threshold** — точное число тестов от которого включать stage? (predлагается ≥30 на одну фичу). Калибровать по факту.
2. **Cross-FEAT audit** — нужен ли audit с учётом старых тестов проекта (на предмет дублей с прошлыми FEAT)? В FEAT-0017 дубли были только внутри новых тестов; cross-FEAT audit может быть тяжёлой задачей.
3. **Где хранить отчёт** — `features/FEAT-XXXX/TDD_AUDIT.md` отдельно или встроить в `REVIEW.md`?
4. **Конфликт с TDD red-green-refactor** — в какой момент жизненного цикла теста удаление безопасно? Если тест закрывал только что-исправленный bug — оставить даже если выглядит избыточным.

## Definition of Done (MVP)

- [ ] Skill `tdd-audit` в `plugins/planner/skills/tdd-audit/SKILL.md`
- [ ] Обновлённый skill `plan-do` в `plugins/planner/skills/plan-do/SKILL.md` — добавлен Phase 3.5 (TDD count audit) с условием skip для S-фич
- [ ] Промпт-шаблон для tdd-master / general-purpose с mandate (constraint regression-safety, классификация дублей)
- [ ] Smoke-тест на синтетической фиче с явными дублями (10 enum-value тестов + 5 implementation-coupled) — skill сокращает до 5+0
- [ ] Документация в `plugins/planner/README.md` — новый раздел «TDD audit phase»
- [ ] Бамп `version` в `plugin.json` (MINOR — новая функциональность)

## Зафиксированный урок (memory)

Файл: `feedback_tdd_count_audit_pipeline_stage.md`

```markdown
---
name: TDD count audit как обязательный stage в /plan-do
description: TDD audit (дедупликация, parametrize, Liar-детекция) должен быть встроенным stage между implementation и documentation в /plan-do, не post-hoc по жалобе пользователя на «многовато тестов»
type: feedback
---

После implementation многие агенты пишут TDD per slice, что даёт coupled-тесты, дубли через слои (model + migration + engine), implementation-coupled тесты приватных хелперов, набор enum-value тестов на Python-литералы. Reviewer проверяет функциональность кода, но не делает count audit. Пользователь замечает «N тестов многовато» уже после code review fix-loop'а — приходится откатывать назад.

**Why:** запускался ≥2 раза по жалобе пользователя:
- FEAT-0016 mcp-interface — 162 → 124 тестов (-23%) после поста-факт tdd-master запуска
- FEAT-0017 brs-transparency — 97 → 74 backend (-24%), 42 → 41 frontend после поста-факт запуска

Оба раза reviewer (code-reviewer) пропускал избыточность, фокусируясь на корректности. Это разные роли: reviewer = функциональность, tdd-master = кардинальность тестов.

**How to apply:** в orchestrator-flow `/plan-do` ИЛИ в proceeding-инструкции для оркестратора:

1. После implementation (Phase 3), ДО code review (Phase 4) — запустить `tdd-master` agent с явным промптом «cross-slice test audit: дубли, Liar-тесты, implementation-coupled, parametrize».
2. Sonnet, ~100k tokens, ~9 мин для L-фичи (по факту FEAT-0017).
3. Пропускать только для S-фич с <30 тестов (overhead больше выгоды).
4. Constraint: НЕ удалять регрессионные тесты на блокеры из review (P0/P1) — они оправданы. Удалять enum-литералы, дубли через слои, private helper-тесты.

Альтернативно — встроить count audit в обновлённый промпт code-reviewer'а. Trade-off: reviewer уже большой, разделение ролей чище.

**Эффект:** -24% тестов на L-фичу без потери coverage бизнес-инвариантов; экономит 1 цикл «жалоба → audit → правки → re-run».

**Связанная memory:** `feedback_test_count_creep_per_slice.md` (зачем срабатывает) — этот файл (как фиксить).
```

---

**Источник идеи:** `/plan-reflect` сессия после FEAT-0017 в проекте Контракция (2026-04-28). Cost-calibration §4 в `planner-context.md` зафиксировал ≥2 случая срабатывания на L-фичах.
