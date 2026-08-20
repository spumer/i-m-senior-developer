# I'm Senior Developer

Плагины для Claude Code, собранные на основе моей практики.

Документация: состав плагинов, связи между ними, правила проверки и отчёты о
прогонах — в каталоге [`docs/`](docs/index.md). Сайт собирается Zensical и
публикуется в GitHub Pages.

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

22 принципа Функциональной ясности. Fail-fast, запрет Error Hiding, минимальные изменения, явные зависимости. Загружается при старте сессии. Включает 7-шаговую Code-Change Discipline (с FPF-нормативами) и дисциплину комментариев (объясняй «почему», не «что»).

### [tdd-master](plugins/tdd-master/)

TDD по Кенту Беку и дяде Бобу. Red-Green-Refactor, FIRST, паттерны для pytest и Django.

### [llms-keeper](plugins/llms-keeper/)

Поддержка `llms.txt` и `llms-full.txt` по стандарту [llmstxt.org](https://llmstxt.org). Агент анализирует кодовую базу и генерирует контекст проекта для AI-инструментов.

### [planner](plugins/planner/)

Конвейер фичи с продуктовым слоем: `/plan-idea` прорабатывает замысел — необязательный вход, можно начать сразу со среза; `/plan-epic` собирает общую гипотезу из нескольких срезов; `/plan-roadmap` задаёт порядок срезов; `/plan-feat` формулирует требования среза с проверяемой приёмкой. Каждый шаг пишет версионируемый файл. Дальше `/plan` строит готовую архитектуру и связанный с её версией план выполнения, реализация не запускается по устаревшему плану, а после работы `/plan-reflect` обновляет контекст проекта.

### [sdlc](plugins/sdlc/)

SDLC-конвейер: 3 агента (`architect`, `code-implementer`, `code-reviewer`) покрывают design → implement → review для backend (Python: Django/FastAPI) и frontend (React). Stack-aware через on-demand references. Ссылается на `tdd-master` и `functional-clarity` вместо дублирования.

### [clarity-language](plugins/clarity-language/)

Три скилла против AI-синтетики в текстах + SessionStart hook: `clarity-validator` (12 смысловых паттернов в тех-доках, FPF-обоснование), `ai-prose-detector` (стиль художественной прозы по 6 методам), `russian-style` (естественный русский — без кальки и придуманных русских переводов устоявшихся заимствований, без пустых антитез, простой язык для инженеров).

### [plugin-testing](plugins/plugin-testing/)

Поведенческая проверка плагинов Claude Code: кейсы и критерии, обёртка прогона, которая не даёт принять частичный результат за успех, разбор красного прогона, формат отчёта. Плюс утилита, находящая проверки, проходящие всегда.

### [fpf-integration](plugins/fpf-integration/)

Экосистема First Principles Framework ([ailev/FPF](https://github.com/ailev/FPF)): аудит решений с графом подтверждений, механизм устаревания решений, авторинг сводов принципов, резолвер сводов компетенций с гейтом свежести и ритуал закрытия сессии. Без источника справочника скилл останавливается, а не работает вслепую.

### [fpf-competency-bank](plugins/fpf-competency-bank/)

Только данные: два проверенных свода компетенций и карта для резолвера. Подключается через `~/.claude/frameworks.paths`, исполняется резолвером из `fpf-integration`.

## Установка

```
/plugin marketplace add spumer/i-m-senior-developer
/plugin install functional-clarity@i-m-senior-developer
/plugin install tdd-master@i-m-senior-developer
/plugin install llms-keeper@i-m-senior-developer
/plugin install planner@i-m-senior-developer
/plugin install sdlc@i-m-senior-developer
/plugin install clarity-language@i-m-senior-developer
/plugin install plugin-testing@i-m-senior-developer
/plugin install fpf-integration@i-m-senior-developer
/plugin install fpf-competency-bank@i-m-senior-developer
```

`sdlc` подтянет `tdd-master` и `functional-clarity`, `fpf-competency-bank` — `fpf-integration`: это объявленные зависимости.

Локально:

```bash
claude --plugin-dir plugins/functional-clarity --plugin-dir plugins/tdd-master --plugin-dir plugins/llms-keeper --plugin-dir plugins/planner --plugin-dir plugins/sdlc --plugin-dir plugins/clarity-language --plugin-dir plugins/plugin-testing --plugin-dir plugins/fpf-integration --plugin-dir plugins/fpf-competency-bank
```

Что за что отвечает, как плагины связаны и в каких случаях каждым лучше не пользоваться — в [документации](docs/index.md).

## Смежные проекты

Оба опираются на эту витрину и не дублируют её методологию — ставятся рядом, а не вместо.

- [senior-developer-tools](https://gitlab.com/mlopotkov/senior-developer-tools) — витрина по плагину на язык или связку: rust, python, typescript, web-svelte, плюс System Design для веб-сервисов, GitLab MR-flow, Bruno, SQLite-паттерны. TDD, Функциональная ясность и SDLC-роли там не дублируются, а подтягиваются отсюда, поэтому подключать нужно обе витрины.
- [core-team](https://github.com/noxxer/core-team) — саморазворачивающийся мультиагентный фреймворк: фасилитатор и команда ролей, слой памяти между сессиями, гейты качества. Ставится копированием каталога `.claude/` в проект, а не через витрину. Для `planner` это один из внешних поставщиков продуктовой проработки — тот самый «пакет Core Team» из таблицы способностей.

## Первоисточник

- [ailev/FPF](https://github.com/ailev/FPF) — First Principles Framework А. Левенчука. Плагин `fpf-integration` читает эту спецификацию через MCP или локальную копию и без источника останавливается, а не работает вслепую. Своды компетенций в `fpf-competency-bank` собраны по её правилам.

## Автор

Svyatoslav Posokhin
