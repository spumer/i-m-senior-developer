---
name: plan-feat
description: Facilitate requirements for one deliverable slice — actor path, edge cases, acceptance criteria. Output features/FEAT-XXXX-<slug>/README.md.
argument-hint: "[slice description, IDEA with outcome feature, roadmap item, or existing feature path]"
allowed-tools: ["Read", "Grep", "Glob", "Write", "Bash(python3:*)", "Bash(mkdir:*)", "AskUserQuestion"]
---

Активируй скилл `product-discovery` с видом документа `feature` и выполни его порядок работы от начала до конца. Для этого вида скилл загружает `references/feature-mode.md`.

Разбор `$ARGUMENTS`:

- Свободное описание одной фичи — проработка требований новой фичи.
- Путь к замыслу с решённым исходом `feature` — проработка фичи из замысла; замысел передаётся в `sync` флагом `--parent`.
- Путь к `ROADMAP.md` с идентификатором элемента — фича для этого элемента порядка.
- Путь к существующей фиче (`README.md` или каталогу фичи) — продолжение или пересмотр; сначала посмотри состояние через `inspect`.
- Пустой аргумент — начни диалог с вопроса, что за фича.

Информационные вопросы задаются прозой порциями по два–четыре; выбор из вариантов и значимые решения — через `AskUserQuestion` по протоколу значимого решения скилла.

Успешный запуск всегда записывает результат в `features/FEAT-NNNN-<slug>/README.md`. После успешной записи в чате — только короткий итог по формату скилла: вид, путь и версия, два–четыре главных исхода, цепочка дальше. Полный документ в чат не дублируется.

Цепочка после готовой фичи (`readiness: ready`):

1. `/plan features/FEAT-NNNN-<slug>/README.md` — архитектура по требованиям;
2. `/plan features/FEAT-NNNN-<slug>/ARCHITECTURE.md` — план выполнения по архитектуре;
3. `/plan-do features/FEAT-NNNN-<slug>/` — реализация по плану.

Цепочку назови в итоге; не запускай её сам. Метод проработки и правила остановки — в скилле; не повторяй их здесь. При ошибке записи следуй разделу «Ошибка записи» скилла: подготовленное тело документа — запасной результат.
