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

These rules preserve the legacy planner's handling of manual edits and make re-scan behavior explicit.

The `/plan-reflect` skill writes its findings with the marker `<!-- learned YYYY-MM-DD -->` so lessons are auditable and traceable to the session that produced them.

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
> приходят с меткой `<!-- learned YYYY-MM-DD -->`.

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
| Opus 5 | Глубокие рассуждения, сложная архитектура, нестандартные алгоритмы | Дорого, медленно | ≈5× Sonnet | Security-core, новая незнакомая область, спорные ADR |
| Sonnet 5 | Баланс: контекст + надёжный код | Теряется в очень сложных цепочках | baseline | 80% задач: CRUD, компоненты, миграции, обычная архитектура |
| Haiku 4.5 | Быстрый, дешёвый | Слабее на нюансах | ≈0.2× Sonnet | Тривиальные правки, форматирование, проверка импортов |

## 5. Хранение артефактов фич

- **Корень фич:** `<обнаруженный-путь>` (например `agents/features/` или `features/`)
- **Корень замыслов:** `<обнаруженный-путь>` (например `ideas/`)
- **Корень общих гипотез:** `<обнаруженный-путь>` (например `epics/`)
- **Паттерн имени:** `FEAT-XXXX-<slug>/` (уточни по факту)
- **Артефакты внутри фичи:**
  - `README.md` — требования
  - `ARCHITECTURE.md` — готовая архитектура с версией и отпечатком тела
  - `PLANNER_EXECUTION.md` — план выполнения со ссылкой на архитектуру
  - `PLANNER_OUTPUT.md` — сохранённый legacy-артефакт; новые запуски его не используют
  - `review-request-changes/REVIEW-NN.md` — отчёт ревью за один раунд
  - `screenshots/`, `test_cases/`
- **Свободные задачи:** `.claude/plans/<task-slug>/`
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

## §9 Способности и поставщики

| Способность | Нужна для | Поставщик | Источник | Доступность | Покрытие | Основание | Ограничения | Приоритет |
|---|---|---|---|---|---|---|---|---|
| problem_outcome_framing | idea, epic, feature | planner:product-baseline | builtin | available | partial | plugins/planner/skills/product-baseline/SKILL.md | нет данных о пользователях; ограниченный режим | builtin |
| product_synthesis | idea, epic, roadmap | planner:product-baseline | builtin | available | partial | plugins/planner/skills/product-baseline/SKILL.md | нет данных о пользователях; ограниченный режим | builtin |
| decision_dialogue | idea, epic, roadmap, feature | planner:product-baseline | builtin | available | partial | plugins/planner/skills/product-baseline/SKILL.md | нет независимой многоролевой проверки; ограниченный режим | builtin |

Машинный раздел: его разбирает помощник `product_state.py` скилла
`product-discovery` (подкоманда `parse-capabilities`); правила выбора
поставщика и остановки — в `product-discovery/references/routing.md`.
Заголовок таблицы и порядок девяти колонок — дословно, менять нельзя; первая
непустая строка после заголовка раздела обязана быть заголовком таблицы,
проза допускается только после пустой строки за таблицей. Закрытые значения,
дословно: Доступность — `available`, `stale`, `error`, `not-surfaced`;
Покрытие — `full`, `partial`, `unknown`, `none`; Приоритет — `configured`,
`project`, `plugin`, `builtin`. «Нужна для» — виды документов через запятую:
`idea`, `epic`, `roadmap`, `feature`. «Основание» — конкретный путь или
запись обнаружения; пустое основание принудительно переводит покрытие в
`unknown`. Совпадение имени поставщика со способностью основанием не
является. Новые строки помечаются датой обнаружения, исчезнувшие не
удаляются, а помечаются; метки `<!-- ... -->` пишутся внутри ячейки
«Основание» — отдельная строка внутри таблицы ломает машинный разбор.
```

The 9 sections of the template map to legacy `~/.claude/agents/planner.md` as follows: §1 → lines 128-132, §2 → lines 134-138, §3 → lines 140-144, §4 → lines 146-152, §5 → lines 154-168, §6 → lines 170-172, §7 → lines 174-179. Section §8 (`Unknown markers`) records file markers that the stack table cannot classify. Section §9 (`Способности и поставщики`) has no legacy counterpart: it is the machine-readable capability matrix of the `product-discovery` skill, and its exact table format is owned by the `parse-capabilities` subcommand of `product_state.py` — if the two ever diverge, fix this template, not the helper.
