# Плагины

```text
/plugin marketplace add spumer/i-m-senior-developer
/plugin install <плагин>@i-m-senior-developer
```

| Плагин | Версия | Команды | Скиллы | Агенты | Хуки |
|---|---|---|---|---|---|
| [planner](planner.md) | 1.1.0 | 8 | 4 | 1 | `UserPromptSubmit` |
| [sdlc](sdlc.md) | 0.3.0 | — | 3 | 3 | — |
| [tdd-master](tdd-master.md) | 0.1.0 | — | 1 | 1 | `SessionStart` |
| [functional-clarity](functional-clarity.md) | 1.1.0 | — | 1 | — | `SessionStart` |
| [clarity-language](clarity-language.md) | 0.3.0 | — | 3 | — | `SessionStart` |
| [plugin-testing](plugin-testing.md) | 0.1.0 | — | 1 | — | — |
| [llms-keeper](llms-keeper.md) | 0.1.0 | 1 | 1 | 1 | `SessionStart` |
| [fpf-integration](fpf-integration.md) | 0.6.0 | — | 4 | 1 | `SessionStart`, `UserPromptSubmit` |
| [fpf-competency-bank](fpf-competency-bank.md) | 0.1.0 | — | — | — | — |

Версия в таблице — состояние в репозитории. Выпуск идёт общим тегом `vX.Y.Z`,
версия плагина поднимается один раз при выпуске.

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
