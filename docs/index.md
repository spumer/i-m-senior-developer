# Плагины для Claude Code

Начните с нужного вопроса:

- [Что нужно](prerequisites.md) — требования и ограничения до установки.
- [Установка и обновление](install.md) — добавление маркетплейса, установка и обновление плагинов.
- [Релиз](release.md) — порядок выпуска изменений.
- [Если не сработало](troubleshooting.md) — известные отказы и способы проверки.

| Плагин | Что делает |
|---|---|
| [planner](plugins/planner.md) | планирование: замысел, требования фичи, архитектура, план, исполнение |
| [sdlc](plugins/sdlc.md) | агенты `architect`, `code-implementer`, `code-reviewer` |
| [tdd-master](plugins/tdd-master.md) | цикл красный–зелёный–рефакторинг |
| [functional-clarity](plugins/functional-clarity.md) | принципы кода и дисциплина изменения существующего кода; перечень принципов с разбором и примерами лежит в `plugins/functional-clarity/skills/functional-clarity/references/00-principles.md` |
| [clarity-language](plugins/clarity-language.md) | проверка текстов: смысл, русский стиль, проза |
| [plugin-testing](plugins/plugin-testing.md) | eval-кейсы и обёртка прогона для плагинов |
| [llms-keeper](plugins/llms-keeper.md) | `llms.txt` и `llms-full.txt` по команде `/update-docs` |
| [fpf-integration](plugins/fpf-integration.md) | аудит решений, авторинг и применение сводов компетенций |
| [fpf-competency-bank](plugins/fpf-competency-bank.md) | данные: два свода и карта для резолвера |

Зависимости: `sdlc` → `tdd-master`, `functional-clarity`;
`fpf-competency-bank` → `fpf-integration`. Подтягиваются при установке.

`planner` встраивается в уже принятый процесс планирования: продуктовую
проработку и исполнение он отдаёт ролям, объявленным в
`.claude/planner-context.md` — своим проектным, из `sdlc` или из другого
фреймворка. Своего процесса он не навязывает; подробнее —
[Интеграция с другими системами планирования](plugins/planner.md).

## Разделы

- [Плагины](plugins/index.md) — каталог для выбора; на странице каждого плагина
  его состав, команды и артефакты.
- [Связи между плагинами](plugins/relations.md) — зависимости, ссылки, смежные проекты.
- [Принятые решения](decisions.md) — спорные вопросы и что по ним решено.
- [Проверка плагинов](testing/index.md) — `plugin validate` и `plugin eval`.
- [Отчёты по проверкам](reports/index.md) — результаты прогонов.

## Сборка сайта

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install zensical
zensical build          # результат в site/, не коммитится
```
