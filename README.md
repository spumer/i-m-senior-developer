# I'm Senior Developer

Плагины для Claude Code, собранные на основе моей практики.

## Философия

Я изучаю методы создания жизнеспособных систем, которые развиваются вместе с требованиями.

В этом смысле органичное развитие идеи должно влечь за собой такое же органичное развитие кода

Жизнеспособная система - модульная система, итеративно адаптирующаяся к внешним вызовам, способная заменить или изменить свои компоненты для сохранения или развития функциональности в условиях динамично меняющихся требований к системе

О жизнеспособности:

- Никогда не находится в состоянии завершенности, всегда неидеальна.
- Не требует полного переписывания, рефакторинг кода локальный, модульный.
- Глобальный рефакторинг ограничивается выделением связей, модулей, не приводит к переписыванию кода.
- Каждое изменение в такой системе сокращает сложность и сроки будущих изменений.

Именно вышеописанные качества делают систему жизнеспособной.

Есть и множствео других факторов, которые делают её НЕ жизнеспособной

### Иллюзия простоты.

Всякая структура упрощает один вид работы и усложняет другие, в этом её основная задача - сфокусировать усилия.

На чем же стоит фокусироваться при разработке?

На адаптивности и специализации. Система неизбежно будет развиваться, и всё что она делает должна делать хорошо. 

### Каждая задача решается один раз

Иными словами каждая доработка инструмента или функциональности должна развивать его: увеличивать потенциал и возможные варианты использования.

Это не значит что мы должны создать "комбайн" и любой инструмент ждет бесконечное усложнение, напротив, этого не стоит допускать, а стоит четко определить идею и не выходить за её рамки.


## Что внутри

### [functional-clarity](plugins/functional-clarity/)

22 принципа Функциональной ясности. Fail-fast, запрет Error Hiding, минимальные изменения, явные зависимости. Загружается при старте сессии.

### [tdd-master](plugins/tdd-master/)

TDD по Кенту Беку и дяде Бобу. Red-Green-Refactor, FIRST, паттерны для pytest и Django.

### [llms-keeper](plugins/llms-keeper/)

Поддержка `llms.txt` и `llms-full.txt` по стандарту [llmstxt.org](https://llmstxt.org). Агент анализирует кодовую базу и генерирует контекст проекта для AI-инструментов.

### [planner](plugins/planner/)

Мета-диспетчер: анализирует задачу, строит план исполнения (architecture / execution mode), детектирует пробелы в каталоге агентов проекта, учится на прошлых сессиях через `/plan-reflect`. Заменяет legacy `~/.claude/agents/planner.md`.

### [sdlc](plugins/sdlc/)

SDLC-конвейер: 3 агента (`architect`, `code-implementer`, `code-reviewer`) покрывают design → implement → review для backend (Python: Django/FastAPI) и frontend (React). Stack-aware через on-demand references. Ссылается на `tdd-master` и `functional-clarity` вместо дублирования. Заменяет legacy `~/.claude/agents/python-implementer.md`, `django-architect.md`, `code-reviewer.md`.

## Установка

```
/plugin marketplace add spumer/i-m-senior-developer
/plugin install functional-clarity@i-m-senior-developer
/plugin install tdd-master@i-m-senior-developer
/plugin install llms-keeper@i-m-senior-developer
/plugin install planner@i-m-senior-developer
/plugin install sdlc@i-m-senior-developer
```

Локально:

```bash
claude --plugin-dir plugins/functional-clarity --plugin-dir plugins/tdd-master --plugin-dir plugins/llms-keeper --plugin-dir plugins/planner --plugin-dir plugins/sdlc
```

## Автор

Svyatoslav Posokhin
