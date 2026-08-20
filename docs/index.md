# Плагины для Claude Code

```text
/plugin marketplace add spumer/i-m-senior-developer
/plugin install <плагин>@i-m-senior-developer
```

| Плагин | Что делает | Команды |
|---|---|---|
| [planner](plugins/planner.md) | планирование: замысел, требования среза, архитектура, план, исполнение | 8 |
| [sdlc](plugins/sdlc.md) | агенты `architect`, `code-implementer`, `code-reviewer` | — |
| [tdd-master](plugins/tdd-master.md) | цикл красный–зелёный–рефакторинг | — |
| [functional-clarity](plugins/functional-clarity.md) | 22 принципа кода, дисциплина изменения чужого кода | — |
| [clarity-language](plugins/clarity-language.md) | проверка текстов: смысл, русский стиль, проза | — |
| [plugin-testing](plugins/plugin-testing.md) | eval-кейсы и обёртка прогона для плагинов | — |
| [llms-keeper](plugins/llms-keeper.md) | `llms.txt` и `llms-full.txt` | `/update-docs` |
| [fpf-integration](plugins/fpf-integration.md) | аудит решений, авторинг и применение сводов компетенций | — |
| [fpf-competency-bank](plugins/fpf-competency-bank.md) | данные: два свода и карта для резолвера | — |

Зависимости: `sdlc` → `tdd-master`, `functional-clarity`;
`fpf-competency-bank` → `fpf-integration`. Подтягиваются при установке.

## Разделы

- [Плагины](plugins/index.md) — состав каждого плагина, команды, артефакты.
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
