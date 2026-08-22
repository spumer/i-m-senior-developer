# Плагины

Установка и обновление описаны на [отдельной странице](../install.md).

| Плагин | Что делает |
|---|---|
| [planner](planner.md) | планирование: замысел, требования фичи, архитектура, план, исполнение |
| [sdlc](sdlc.md) | агенты `architect`, `code-implementer`, `code-reviewer` |
| [tdd-master](tdd-master.md) | цикл красный–зелёный–рефакторинг |
| [functional-clarity](functional-clarity.md) | принципы кода и дисциплина изменения существующего кода |
| [clarity-language](clarity-language.md) | проверка текстов: смысл, русский стиль, проза |
| [plugin-testing](plugin-testing.md) | eval-кейсы и обёртка прогона для плагинов |
| [llms-keeper](llms-keeper.md) | `llms.txt` и `llms-full.txt` по команде `/update-docs` |
| [fpf-integration](fpf-integration.md) | аудит решений, авторинг и применение сводов компетенций |
| [fpf-competency-bank](fpf-competency-bank.md) | данные: два свода и карта для резолвера |

Версию установленного плагина показывает `claude plugin list` — строкой
`Version:` рядом с его именем. Состав каждого плагина — команды, скиллы, агенты,
хуки, workflow — назван поимённо на его странице.

Версионирование и выпуск описаны на [странице релиза](../release.md).

`planner` рассчитан на подключение к существующему процессу: продуктовую
проработку и исполнение выполняют роли, объявленные проектом в
`.claude/planner-context.md`. Он может работать со своими агентами проекта, с
`sdlc` или с ролями другого фреймворка.

## Наборы

| Задача | Установить |
|---|---|
| разработка фич от требований до ревью | `planner`, `sdlc` (подтянет `tdd-master` и `functional-clarity`) |
| только принципы кода | `functional-clarity` |
| только цикл тестов | `tdd-master` |
| проверка текстов | `clarity-language` |
| разработка своих плагинов | `plugin-testing` |
| работа со сводами компетенций | `fpf-competency-bank` (подтянет `fpf-integration`) |

`fpf-competency-bank` дополнительно требует записи пути в
`~/.claude/frameworks.paths`.

## Локальный запуск без установки

```bash
claude --plugin-dir plugins/planner --plugin-dir plugins/sdlc
```

Связи между плагинами — [отдельная страница](relations.md).
