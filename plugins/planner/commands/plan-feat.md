---
name: plan-feat
description: Facilitate requirements for one deliverable slice — actor path, edge cases, acceptance criteria. Output features/FEAT-XXXX-<slug>/README.md.
argument-hint: "[slice description, IDEA with outcome feature, roadmap item, or existing feature path]"
allowed-tools: ["Read", "Grep", "Glob", "Write", "Bash(python3:*)", "Bash(mkdir:*)", "AskUserQuestion"]
---

Активируй скилл `product-discovery` с видом документа `feature` и выполни его порядок работы от начала до конца. Для этого вида скилл загружает `references/feature-mode.md`.

Разбор `$ARGUMENTS`:

- Свободное описание одного среза — проработка требований нового среза.
- Путь к замыслу с решённым исходом `feature` — проработка среза из замысла; замысел передаётся в `sync` флагом `--parent`.
- Путь к `ROADMAP.md` с идентификатором элемента — срез для этого элемента порядка.
- Путь к существующему срезу (`README.md` или каталогу среза) — продолжение или пересмотр; сначала посмотри состояние через `inspect`.
- Пустой аргумент — начни диалог с вопроса, что за срез.

Все вопросы человеку задаются через `AskUserQuestion` — это обязательный инструмент режима, вопросов сплошным текстом нет.

Успешный запуск всегда записывает результат в `features/FEAT-NNNN-<slug>/README.md`. После успешной записи в чате — только короткий итог по формату скилла: вид, путь и версия, два–четыре главных исхода, цепочка дальше. Полный документ в чат не дублируется.

Цепочка после готового среза (`readiness: ready`):

1. `/plan features/FEAT-NNNN-<slug>/README.md` — архитектура по требованиям;
2. `/plan features/FEAT-NNNN-<slug>/ARCHITECTURE.md` — план выполнения по архитектуре;
3. `/plan-do features/FEAT-NNNN-<slug>/` — реализация по плану.

Цепочку назови в итоге; не запускай её сам. Метод проработки и правила остановки — в скилле; не повторяй их здесь. При ошибке записи следуй разделу «Ошибка записи» скилла: подготовленное тело документа — запасной результат.
