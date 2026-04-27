# Template — `planner-context.md`

The canonical empty-shell template for `<project-root>/.claude/planner-context.md`. The bootstrap procedure (see `bootstrap.md` §8) writes this template on first run; subsequent re-scans only append/annotate rows per the conventions below.

## 1. Purpose

`planner-context.md` is the **project-local source of truth** for the planner skill: it lists which agents/commands/skills are actually available, which models the project prefers, where feature artifacts live, and what naming conventions the team uses. The planner skill reads this file before building any plan; without it, the planner would have to re-scan the project on every activation.

The body of this template is a fenced markdown block (see §3). On bootstrap, the implementer copies that block verbatim into `<project-root>/.claude/planner-context.md` and fills the auto-discoverable fields. Manual fields (e.g. "Когда звать", project naming conventions, lessons-learned) are filled by humans and updated by `/plan-reflect`.

## 2. Conventions

Three meta-rules govern every edit of this file:

1. **Auto-added rows.** When a re-scan discovers a new agent / skill / command since the last bootstrap, the planner appends a row tagged `<!-- auto-added YYYY-MM-DD -->`. Auto-added rows are honest about their origin so the user can review them.
2. **Stale rows.** When a re-scan does **not** find an agent / skill / command that existed in the previous bootstrap, the planner does not delete the row — it tags it `<!-- stale, last seen YYYY-MM-DD -->`. The user decides whether the entity was renamed, moved, or genuinely removed.
3. **Manual edits are sources of truth.** Anything the user wrote by hand (refined "Когда звать" notes, model overrides in §4, lessons-learned in §6, etc.) is **never** overwritten. The planner only adds, annotates with `<!-- ... -->` markers, or appends new sections.

These rules come from the legacy planner (`~/.claude/agents/planner.md` lines 109-113) plus the FEAT-0001 edge-case requirements (rows 3-4 of the README table).

The `/plan-reflect` skill writes its findings with the marker `<!-- learned YYYY-MM-DD from FEAT-XXXX -->` so lessons are auditable and traceable to the session that produced them.

## 3. The template

Copy the content of the fenced block below verbatim into `<project-root>/.claude/planner-context.md` on first bootstrap. Replace `<project-name>` with the actual project name (taken from the root `README.md` H1 or the directory name).

```markdown
# Planner Context — <project-name>

> Проект-специфичный контекст для skill'а `planner` (плагин `planner` из
> marketplace `i-m-senior-developer`). Планнер читает этот файл перед
> построением плана.
>
> Формат: таблицы. Допустимо редактировать вручную — планнер не
> перезаписывает ручные правки, только дополняет новыми автосканированными
> строками с меткой `<!-- auto-added YYYY-MM-DD -->` и помечает исчезнувшие
> элементы `<!-- stale, last seen YYYY-MM-DD -->`. Уроки из `/plan-reflect`
> приходят с меткой `<!-- learned YYYY-MM-DD from FEAT-XXXX -->`.

## 1. Каталог агентов

| Имя (как звать) | Источник | Роль | Сильные стороны | Когда звать |
|---|---|---|---|---|
| <name> | project / global / plugin | <из description> | <из description> | <заполни после review> |
| ❌ GAP (<stack>, <variant>) | — | <отсутствующая роль> | — | fallback: general-purpose |

## 2. Каталог slash-команд

| Команда | Источник | Назначение |
|---|---|---|
| /<name> | project / global / plugin | <из description> |

## 3. Каталог skills

| Skill | Источник | Триггер активации |
|---|---|---|
| <name> | project / global / plugin | <из description> |

## 4. Таблица моделей (default, переопределяй если нужно)

| Модель | Сила | Слабость | $/time | Применять для |
|---|---|---|---|---|
| Opus 4.7 | Глубокие рассуждения, сложная архитектура, нестандартные алгоритмы | Дорого, медленно | ≈5× Sonnet | Security-core, новая незнакомая область, спорные ADR |
| Sonnet 4.6 | Баланс: контекст + надёжный код | Теряется в очень сложных цепочках | baseline | 80% задач: CRUD, компоненты, миграции, обычная архитектура |
| Haiku 4.5 | Быстрый, дешёвый | Слабее на нюансах | ≈0.2× Sonnet | Тривиальные правки, форматирование, проверка импортов |

## 5. Хранение артефактов фич

- **Корень фич:** `<обнаруженный-путь>` (например `agents/features/` или `features/`)
- **Паттерн имени:** `FEAT-XXXX-<slug>/` (уточни по факту)
- **Артефакты внутри фичи:**
  - `README.md` — требования
  - `FEAT-XXXX-DESIGN-0N.md` — UI/UX (если применимо)
  - `FEAT-XXXX-PLAN-0N.md` — архитектурный план
  - `PLANNER_OUTPUT.md` — вывод планнера
  - `review-request-changes/FEAT-XXXX-ISSUE-0NN.md` — находки review
  - `screenshots/`, `test_cases/`
- **Контекстные файлы проекта** (если есть):
  - `<путь-или-пусто>` — UI guidelines
  - `<путь-или-пусто>` — testing guide
  - `<путь-или-пусто>` — project/architecture overview

## 6. Соглашения именования

- <из README/CLAUDE.md, иначе TODO: fill manually>
- <lessons-learned bullets from /plan-reflect appear here, tagged>

## 7. Метаданные bootstrap

- Последний auto-scan: <ISO-date>
- Количество найденных агентов: N (project: X, global: Y, plugin: Z)
- Количество найденных skills: N
- Количество найденных команд: N

## 8. Unknown markers

Файловые маркеры, обнаруженные при bootstrap, но не сопоставленные ни с одним
известным стеком из таблицы `bootstrap.md` §4. Заполни вручную — укажи стек и
вариант, либо удали строку, если маркер нерелевантен.

- <marker>: <discovered location> — TODO: assign stack
```

The 8 sections of the template map to legacy `~/.claude/agents/planner.md` as follows: §1 → lines 128-132, §2 → lines 134-138, §3 → lines 140-144, §4 → lines 146-152, §5 → lines 154-168, §6 → lines 170-172, §7 → lines 174-179. Section §8 (`Unknown markers`) is **new** per FEAT-0001 README §61 and the edge-case "unknown stack" row.
