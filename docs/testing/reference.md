# Проверки planner через `claude plugin eval`

Эта страница предназначена для автора eval-кейсов плагина `planner`. Она описывает, что реально можно проверить, как устроен формат кейсов и как читать результат. Это не инструкция, которую нужно загружать модели во время работы.

## Уровень подтверждения

В тексте используются такие пометки:

- **[Запуск]** — проверено фактическим запуском CLI в Claude Code `2.1.234`.
- **[CLI 2.1.234]** — прочитано из встроенного reference и реализации установленного CLI. Гейт раннего доступа открыт переменной `CLAUDE_CODE_WALNUT_SPIRE=1`; полного успешного прогона кейсов ещё нет.
- **[Публичная документация]** — подтверждено публичной документацией. Публичной страницы со спецификацией `claude plugin eval` пока нет; публичные ссылки в конце относятся к общим eval-принципам и отдельному формату `skill-creator`.

---

## 1. Ранний доступ

### Как проверить гейт

Проверять нужно в пустом каталоге, а не в репозитории с кейсами:

```bash
tmpdir=$(mktemp -d)
(cd "$tmpdir" && claude plugin eval)
```

Результаты:

- **[Запуск]** `` `plugin eval` is currently in early access `` и код выхода `1` — команда есть в CLI, но доступ не включён для этой организации или не дошёл до процесса.
- **[Запуск]** `No eval cases found ...` и код выхода `1` — feature gate открыт, но в каталоге нет обнаруженных кейсов. Код выхода здесь тот же, различать состояния нужно по тексту сообщения.

Без локального включения гейт оставался закрыт на каждой проверенной версии — от `2.1.228` до `2.1.234`:

```text
`plugin eval` is currently in early access
```

В CLI `2.1.234` проверка реализована так:

```text
server flag tengu_walnut_spire OR CLAUDE_CODE_WALNUT_SPIRE
```

Для клиента со своим `ANTHROPIC_BASE_URL` серверный флаг не приходит, поэтому в пользовательском `~/.claude/settings.json` задано:

```json
{
  "env": {
    "CLAUDE_CODE_WALNUT_SPIRE": "1"
  }
}
```

После этого самотест возвращает `No eval cases found`, а `claude plugin eval init smoke --bare` создаёт шаблон и выходит с кодом `0`. Имя переменной внутреннее и может измениться при обновлении CLI; после обновления повторяйте самотест.

Если гейт закрыт, не диагностируйте его созданием кейсов в репозитории: они не будут прочитаны. Сначала проверьте обновление, новую сессию, доступ организации и окружение процесса.

### Требования к версии

Для planner стоит ориентироваться минимум на Claude Code `2.1.224`:

- `2.1.198` — появились `plugin eval`, `plugin eval init`, интервью и `--bare`;
- `2.1.210` — появился текущий JSON v1 для `--json`;
- `2.1.224` — текущая модель `aggregate-result.json`, HTML-отчёт и поле `scored` в результатах грейдеров;
- в исследованной среде установлена `2.1.234`.

### Что проверяет `plugin validate`

Структура плагина и frontmatter компонентов проверяются отдельной командой, доступной без раннего доступа:

```bash
claude plugin validate plugins/planner --strict
claude plugin validate plugins/planner/commands --strict
claude plugin validate plugins/planner/skills --strict
claude plugin validate plugins/planner/agents --strict
```

Указанный корень плагина проверяет только манифест. Frontmatter команд, скиллов и агентов проверяется, когда путь ведёт в соответствующий каталог, поэтому в CI нужны все четыре вызова.

`--strict` обязателен: без него отсутствующий `description` у скилла остаётся предупреждением и код выхода равен `0`. Со `--strict` тот же случай даёт код `1` — это проверено удалением поля на временной копии.

Границы проверки, установленные тем же способом: неизвестное поле во frontmatter команды не отклоняется даже со `--strict`, хотя описание флага обещает отказ на нераспознанных полях. Проверка договора команд на этом не строится.

Поведение скиллов эта команда не проверяет — она читает состав и схемы, а не результат работы.

### Обязательный полный прогон planner

Единая команда перед выпуском затронутого planner:

```bash
python3 plugins/planner/evals/run.py
```

Скрипт фиксирует полный договор запуска: Claude Code `2.1.234`, три повтора,
`--ablation none`, модель `opus` и судью `haiku`, локальный отчёт, выключенный
scaffold, операторское разрешение `Write` и предел стоимости `$6`. Сначала он
выполняет четыре `plugin validate --strict`, затем создаёт новый каталог
результатов и вызывает `plugin eval`.

Модель закреплена по наблюдению, а не по умолчанию CLI. На `sonnet`
маршрутизация в `product-discovery` не срабатывала ни в одном из шести
повторов, на `opus` те же кейсы вызывают скилл. Предел `$6` выбран по
измеренной стоимости: полный прогон на `opus` стоил `$1.93`.

Код выхода CLI сам по себе не считается доказательством. После нулевого кода
скрипт проверяет `aggregate-result.json`: `schemaVersion: 1`, `partial: false`,
точный набор трёх кейсов, три успешных запуска каждого, полный score и отсутствие
`skippedPaidGraders`. Также обязаны существовать свежие `aggregate-result.json`
и `report.html` в переданном каталоге.

`MAX_COST_USD` можно понизить или поднять через окружение; значение по умолчанию
— `6.00`. Достигнутый предел даёт частичный прогон и блокирует релиз. Пилот с
`--runs 1` пригоден для отладки после обновления CLI, но не заменяет полный
скрипт.

### Наблюдённый результат последнего прогона

Прогон на `opus` от 19.08.2026, `$1.93`, `partial: false`:

| Кейс | Оценка | Успешных повторов |
|---|---|---|
| `baseline-provider-limits` | `1.00` | 3 из 3 |
| `idea-routing` | `1.00` | 3 из 3 |
| `multi-step-input` | `0.67` | 1 из 3 |

Набор пока не проходит целиком, поэтому релизный гейт закрыт. Причина одна:
на входе из нескольких желаемых исходов скилл `product-discovery` вызывается
неустойчиво. Содержательные критерии при этом проходят во всех повторах —
модель не сворачивает три исхода в один срез.

Открытый вопрос для человека: требовать ли от гейта 3 из 3 при том, что речь
идёт о решении модели, или считать достаточным большинство повторов. Порог
`--threshold 1.0` сейчас требует полной устойчивости.

Отдельно: у части успешных повторов CLI сообщает `error: exit 1: (no stderr)`.
Это ожидаемо для маршрутизационных кейсов — скилл доходит до вопроса человеку,
а в headless-режиме `AskUserQuestion` недоступен. Скрипт намеренно не отклоняет
такие повторы: их договор задаётся критериями и оценкой.

Контракт скрипт покрыт `plugins/planner/evals/test_run.py` через подменный Claude
CLI без модельных вызовов. Тесты проверяют и ложный успех: CLI возвращает код
`0`, но результат частичный или неполный — скрипт обязан отказать.

---

## 2. Два формата кейса

Кейс — это директория под `evals/`, содержащая `case.yaml`, `prompt.md` или оба файла:

```text
evals/
└── idea-routing/
    ├── prompt.md
    ├── case.yaml              # необязательно
    ├── graders/
    │   ├── uses-discovery.md
    │   └── no-plan-feat.md
    ├── fixture.sh              # если нужен scaffold
    └── history.jsonl            # если нужен replay диалога
```

По умолчанию CLI ищет кейсы в `<plugin-root>/evals/`. В текущем CLI `2.1.234` опции `--eval-dir` нет.

### Формат A: `case.yaml`

Используйте его, когда нужны:

- `context.scaffold_script`;
- `context.history_file`;
- `context.add_dirs`;
- один полностью структурированный файл кейса;
- явное описание грейдеров в YAML.

`context.*` доступен только в `case.yaml`. В `prompt.md` эти поля задать нельзя.

Минимальная структура standalone-кейса:

```yaml
schema_version: "1.1"
name: example-case

execution:
  prompt: Do the task.

graders:
  - type: regex
    name: has-result
    pattern: "done"
    flags: i
```

У standalone `case.yaml` должны присутствовать `schema_version`, `name`, объект `execution` и непустой список `graders`. `execution.prompt` можно не задавать, если используется `context.history_file`.

### Формат B: `prompt.md` + `graders/*.md`

Используйте его для обычных естественно читаемых кейсов:

```text
evals/idea-routing/
├── prompt.md
└── graders/
    ├── uses-discovery.md
    └── no-plan-feat.md
```

`prompt.md`:

```markdown
---
name: idea-routing
runs: 3
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
plugins: ["../.."]
---

У меня есть идея, обсудим?
```

Тело файла становится пользовательским prompt. В frontmatter разрешены следующие плоские ключи.

Верхний уровень:

```text
schema_version
name
description
tags
plugins
runs
expected_outcome
```

Параметры запуска:

```text
model
max_turns
timeout_seconds
allowed_tools
append_system_prompt
env
```

Любой другой ключ во frontmatter `prompt.md` — ошибка.

Файл грейдера:

```markdown
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?product-discovery"'
min: 1
---
```

Имя грейдера по умолчанию — имя файла без `.md`. Поле `name` во frontmatter может его переопределить. Файл с frontmatter обязан иметь `type`. Markdown-файлы в `graders/` без frontmatter игнорируются.

Для `regex` тело Markdown может быть самим pattern, для `llm` и `baseline` — criteria. Для `tool_used`, `tool_order` и `file_exists` поля нужно задавать во frontmatter.

### Совмещение форматов

Оба файла можно использовать вместе:

```text
evals/idea-routing/
├── case.yaml
├── prompt.md
└── graders/
```

Правила совмещения:

1. `case.yaml` — базовый документ.
2. Frontmatter `prompt.md` переопределяет его верхнеуровневые и execution-поля.
3. Тело `prompt.md` становится `execution.prompt`.
4. Грейдеры из `case.yaml` идут первыми.
5. Грейдеры из `graders/*.md` добавляются после них в алфавитном порядке.
6. Если `case.yaml` присутствует, в нём всё равно должны быть `schema_version` и `name`.

---

## 3. Поля кейса

| Поле | Тип | Обязательность и default | Назначение |
|---|---|---|---|
| `schema_version` | string | Обязательно в `case.yaml`; используйте `"1.1"` | Версия формата. Сейчас проверяется major-версия; major `2` требует более нового CLI. |
| `name` | string | Обязательно в `case.yaml`; в prose-only берётся имя директории | Имя кейса, фильтры `--case` и имя в отчёте. |
| `description` | string | Необязательно | Пояснение для человека; не является грейдером. |
| `tags` | string[] | `[]` | Фильтрация через `--tag`; кейс остаётся, если совпал хотя бы один tag. |
| `plugins` | string[] | Автоопределение ближайшего plugin manifest | Пути плагинов под тестом, относительно директории кейса. Для папки только с `SKILL.md` задавайте явно. |
| `runs` | integer `1..50` | `3` | Число запусков на одну arm. Переопределяется `--runs`. |
| `context.scaffold_script` | path | Необязательно | Bash-скрипт подготовки sandbox; запускается только с `--scaffold`. |
| `context.history_file` | path | Необязательно | JSONL-транскрипт для replay предыдущих ходов. |
| `context.add_dirs` | string[] | `[]` | Дополнительные директории для `--add-dir`; должны находиться внутри директории кейса. |
| `execution` | object | Объект нужен в standalone `case.yaml` | Настройки дочернего `claude -p`. |
| `execution.prompt` | string | Необязательно, если есть `history_file` | Пользовательский prompt. В prose-формате это тело `prompt.md`. |
| `execution.max_turns` | integer `1..200` | `10` | Максимум ходов агента. |
| `execution.timeout_seconds` | integer `1..3600` | `300` | Тайм-аут одного запуска. |
| `execution.model` | string | Необязательно | Модель агента под тестом; переопределяется `--model`. |
| `execution.allowed_tools` | string[] | `[]` | Инструменты, которые кейс запрашивает. Сам по себе этот список не выдаёт опасные инструменты. |
| `execution.append_system_prompt` | string | Необязательно | Дополнение системного prompt дочернего агента. |
| `execution.env` | map string → string | `{}` | Только ключи вида `EVAL_[A-Z0-9_]*`. |
| `graders` | list | Минимум один, имена уникальны | Проверки результата. |
| `expected_outcome` | string | Необязательно | Описание ожидаемого результата для автора; само по себе не проверяется. |

Неизвестные ключи верхнего уровня, `context` и `execution` в текущем CLI игнорируются. Неизвестные ключи внутри грейдера — ошибка. Значения `execution.env` должны быть строками.

---

## 4. Шесть типов грейдеров

Общие поля:

- `type` — обязательный тип;
- `name` — обязательное уникальное имя;
- `weight` — положительный вес, default `1`;
- `arm` — необязательный `with-only` или `both`.

### 4.1. `regex`

Проверяет регулярным выражением выбранную цель.

```yaml
type: regex
name: mentions-migration
target: last_message
pattern: "storage|migration"
flags: i
match: contains
weight: 1
```

Поля:

- `pattern` — JavaScript RegExp source;
- `flags` — только `d`, `g`, `i`, `m`, `s`, `u`, `v`, `y`;
- `match` — `contains`, `not_contains` или `count:N`;
- `target` — `last_message`, `trace`, `files` или `{ source: file, path: ... }`.

Точное количество совпадений:

```yaml
type: regex
name: exactly-one-bullet
target:
  source: file
  path: CHANGELOG.md
pattern: "^- "
flags: m
match: count:1
```

Inline-флаги не поддерживаются:

```text
(?i)text
```

не используйте. Нужно:

```yaml
pattern: text
flags: i
```

`files` — это список путей, а не содержимое файлов. Для содержимого используйте:

```yaml
target:
  source: file
  path: CHANGELOG.md
```

`trace` — JSONL-текст с экранированными кавычками и переводами строк.

### 4.2. `tool_used`

Проверяет количество вызовов инструмента.

```yaml
type: tool_used
name: uses-product-discovery
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?product-discovery"'
min: 1
```

Поля:

- `tool` — точное имя инструмента в trace;
- `input_match` — необязательная регулярка по JSON-представлению input;
- `min` — default `1`;
- `max` — default без ограничения;
- `weight`;
- `arm`.

Проверка агента:

```yaml
type: tool_used
name: starts-review-agent
tool: Agent
min: 1
```

Для различения конкретного агента используйте `input_match`, предварительно посмотрев форму input в trace. В зависимости от версии и способа запуска имя инструмента может быть `Agent` или `Task`.

Проверка MCP-инструмента:

```yaml
type: tool_used
name: calls-plugin-mcp
tool: mcp__plugin_planner_server__lookup
min: 1
```

Проверка отсутствия вызова:

```yaml
type: tool_used
name: must-not-use-web
tool: WebFetch
min: 0
max: 0
arm: both
```

Ловушка: `max: 0` без `min: 0` **не работает**, потому что `min` по умолчанию равен `1`.

### 4.3. `tool_order`

Проверяет, что первый подходящий вызов `before` произошёл до первого подходящего вызова `after`.

```yaml
type: tool_order
name: read-before-edit
before: Read
after:
  tool: Edit
  input_match: CHANGELOG
```

Каждая сторона может быть именем инструмента или объектом:

```yaml
before:
  tool: Read
  input_match: package.json
after: Edit
```

Оба вызова должны присутствовать. Грейдер не проверяет отсутствие промежуточных инструментов и не утверждает полный порядок всей траектории.

### 4.4. `file_exists`

Проверяет, был ли создан файл во время run.

```yaml
type: file_exists
name: writes-changelog
path: "**/CHANGELOG.md"
exists: true
```

Для проверки отсутствия:

```yaml
type: file_exists
name: no-debug-log
path: "**/debug.log"
exists: false
```

`path` поддерживает `*` внутри сегмента и `**/` для любой глубины.

Грейдер видит только файлы, созданные агентом после подготовки начального состояния. Он не видит:

- файлы, которые существовали до запуска;
- файлы, созданные `scaffold_script`;
- файлы, которые агент только изменил.

Чтобы проверить содержимое изменённого или scaffold-файла, используйте `regex` с `target: { source: file, path: ... }` либо проверяйте вызов `Edit`/`Write`.

### 4.5. `llm`

Передаёт выбранный результат judge-модели и проверяет его по рубрике.

```yaml
type: llm
name: answer-is-useful
focus: last_message
criteria: |
  PASS if the answer distinguishes discovery from implementation
  and asks the next useful question.
  FAIL if it immediately starts implementation.
```

`focus` принимает:

- `last_message`;
- `trace`;
- `files`;
- `{ source: file, path: ... }`.

Judge запускается три раза. Нужны минимум два голоса `PASS`.

В результате появляются `judgeVotes` и `evidence`. Для длинных файлов judge менее стабилен; большие текстовые артефакты лучше проверять детерминированными `regex`-грейдерами.

### 4.6. `baseline`

Сравнивает новую траекторию с сохранённым JSONL-трейсом.

```yaml
type: baseline
name: no-worse-than-known-good
baseline_file: gold/trace.jsonl
criteria: |
  The NEW trajectory reaches the same user-visible result
  with no unnecessary extra interaction.
weight: 0.5
```

Judge получает baseline и новую траекторию, затем трижды отвечает, не хуже ли новая траектория. Проходят минимум два голоса `PASS`.

`baseline` и `--ablation with-without` — разные механизмы: первый сравнивает с сохранённым trace, второй самостоятельно запускает arm с плагином и без него.

---

## 5. Подсчёт очков

### Score одного запуска

```text
score = сумма весов пройденных грейдеров /
        сумма весов учитываемых грейдеров
```

`score` находится в диапазоне `0..1`.

`weight` позволяет сделать одну проверку важнее другой:

```yaml
weight: 2
```

`scored: false` означает, что результат грейдера отображается, но не участвует в score. Это бывает у `with-only`-индикаторов в ablation.

Если score запуска равен `1.0`, поле `passed` у этого запуска равно `true`.

### Агрегирование нескольких запусков

```text
cases[].aggregates.score    = среднее score with-запусков
cases[].aggregates.passRate = доля запусков с score == 1.0
```

Например, scores `1.0`, `1.0`, `0.5` дают:

```text
score    = 0.8333
passRate = 0.6667
```

`passRate` не является средней долей пройденных грейдеров.

### `--threshold`

```bash
claude plugin eval plugins/planner --threshold 0.8
```

Кейс считается прошедшим, если его агрегированный **with-score** не ниже порога:

```text
cases[].aggregates.score >= threshold
```

Default — `1.0`. При таком пороге каждый with-run должен получить полный score. Threshold применяется к score кейса, а не к `delta` и не к `passRate`.

---

## 6. `--ablation with-without`

```bash
claude plugin eval plugins/planner \
  --ablation with-without \
  --runs 3 \
  --no-publish
```

Для каждого кейса выполняются две независимые arm:

```text
with     — с плагином planner
without  — без plugin directories
```

### Delta

```text
delta = средний score(with) - средний score(without)
```

Положительная delta означает, что плагин улучшил результат относительно запуска без него. Это разница средних score, а не разница `passRate`.

```json
{
  "aggregates": {
    "score": 0.8333,
    "passRate": 0.6667,
    "scoreWithout": 0.3333,
    "passRateWithout": 0.0,
    "delta": 0.5
  }
}
```

### `with-only`

Грейдер с:

```yaml
arm: with-only
```

считается диагностическим индикатором наличия плагина. В ablation он исключается из score и помечается:

```json
{
  "withOnly": true,
  "scored": false
}
```

Кроме того, любой `tool_used` для инструмента `Skill` без явного `arm` автоматически становится `with-only` при ablation. Поэтому такой грейдер:

```yaml
type: tool_used
tool: Skill
input_match: 'product-discovery'
min: 1
```

показывает, сработал ли skill, но не должен сам по себе ухудшать baseline-сравнение.

Указать проверку в обеих arm можно явно:

```yaml
arm: both
```

Например, `min: 0, max: 0, arm: both` проверяет, что skill не вызывается ни с плагином, ни без него.

Для planner почти всегда нужен хотя бы один грейдер результата помимо индикатора `Skill`: например, regex по финальному ответу или проверка содержимого файла. Иначе suite в основном измеряет факт маршрутизации, а не полезность результата.

---

## 7. `scaffold_script`

Scaffold подготавливает исходную файловую систему перед запуском агента.

```yaml
context:
  scaffold_script: fixture.sh
```

```bash
#!/usr/bin/env bash
set -euo pipefail

mkdir -p input
printf '%s\n' 'prepared fixture' > input/source.txt
```

Запуск scaffold явно включается оператором:

```bash
claude plugin eval plugins/planner --scaffold
```

По умолчанию он выключен:

```bash
claude plugin eval plugins/planner --no-scaffold
```

Почему выключен по умолчанию:

- это авторский Bash-код;
- он выполняется с правами текущего пользователя;
- eval sandbox не является OS-level sandbox;
- сеть не блокируется;
- скрипт может запускать процессы и менять файлы за пределами ожидаемого сценария.

Ограничения scaffold:

- запускается через `bash` в пустом `cwd`;
- выполняется до копирования credentials;
- получает минимальное окружение;
- имеет лимит около двух минут;
- не получает SSH-ключи и credential helpers;
- путь должен находиться внутри директории кейса.

Если scaffold завершился ошибкой, run получает score `0`.

### Взаимодействие с `file_exists`

Состояние после scaffold считается исходным состоянием. Поэтому файл, который создал scaffold, не считается созданным агентом:

```text
scaffold создал input/source.txt
agent изменил input/source.txt
```

`file_exists` всё равно не обязан увидеть этот файл как созданный. Для таких случаев проверяйте содержимое:

```yaml
type: regex
name: fixture-was-updated
target:
  source: file
  path: input/source.txt
pattern: updated
flags: i
```

---

## 8. Sandbox и allowlist инструментов

Каждый run получает новый временный sandbox:

```text
/tmp/claude-eval-XXXXXX/
├── cwd/
├── config/
├── home/
└── out/
    └── trace.jsonl
```

### Что не загружается

В дочернюю сессию не попадают:

- проектные настройки;
- пользовательские настройки;
- `CLAUDE.md` проекта и пользователя;
- memory;
- пользовательские hooks;
- пользовательские MCP-серверы;
- другие установленные плагины;
- обычный пользовательский список skills.

Загружаются только plugin directories под тестом. Hooks и MCP самого плагина могут запускаться.

Это важно для planner: eval не получает автоматически инструкции из корневого `CLAUDE.md` и не должен случайно зависеть от локальной конфигурации разработчика.

Sandbox не блокирует сеть и не является границей безопасности. Разрешённые записи и чтение нужно рассматривать как операции от имени текущего пользователя.

### Tool allowlist

Read-only инструменты, которые могут быть доступны кейсу:

```text
Read
Glob
Grep
NotebookRead
Skill
AskUserQuestion
Task*
Agent
TodoWrite
```

Следующие инструменты требуют отдельного операторского grant:

```text
Bash
Write
Edit
WebFetch
WebSearch
mcp__*
```

### `execution.allowed_tools` и `--allow-tools`

Это два разных уровня.

В кейсе:

```yaml
execution:
  allowed_tools:
    - Read
    - Skill
    - Write
```

указывается, какие инструменты кейс хотел бы использовать.

Оператор отдельно разрешает опасный инструмент:

```bash
claude plugin eval plugins/planner --allow-tools Write
```

Фактически инструмент доступен только если он одновременно:

1. указан в `execution.allowed_tools` кейса;
2. разрешён оператором через `--allow-tools`, если относится к gated-набору.

Кейс не может сам себе выдать `Write`, `Bash`, `Edit`, Web или MCP-доступ.

---

## 9. JSON-результат

По умолчанию результаты появляются в:

```text
evals/results/<timestamp>/
├── aggregate-result.json
└── report.html
```

Полный JSON можно вывести:

```bash
claude plugin eval plugins/planner --json
```

или записать:

```bash
claude plugin eval plugins/planner --json results.json
```

Имя файла для `--json <path>` должно заканчиваться на `.json`.

### Основная структура

```json
{
  "schemaVersion": 1,
  "claudeVersion": "2.1.234",
  "startedAt": "2026-08-16T12:00:00.000Z",
  "durationSeconds": 88,
  "costUsd": 0.26,
  "partial": false,
  "suite": {
    "root": "/work/i-m-senior-developer/plugins/planner",
    "ablation": "none",
    "threshold": 1,
    "plugins": []
  },
  "cases": [],
  "aggregates": {
    "casesTotal": 0,
    "casesPassed": 0,
    "overallScore": 0,
    "overallPassRate": 0
  }
}
```

### Что находится в `cases[]`

```text
name
 dir
source
promptMarkdown
model?
runsPerCase
timeoutSeconds
maxTurns
graders[]
arms.with[]
arms.without[]?
aggregates
```

`source` — `prose`, `case_yaml` или `mixed`.

В `graders[]` находятся определения грейдеров. В `arms.*[]` — фактические результаты запусков.

### Что брать в CI

Для обычного single-arm запуска:

```text
cases[].aggregates.score
cases[].aggregates.passRate
cases[].arms.with[].score
cases[].arms.with[].passed
cases[].arms.with[].error
cases[].arms.with[].skippedPaidGraders
```

Для ablation:

```text
cases[].aggregates.score
cases[].aggregates.scoreWithout
cases[].aggregates.delta
cases[].aggregates.passRate
cases[].aggregates.passRateWithout
```

Также проверяйте:

```text
partial
partialReason
suite.threshold
schemaVersion
```

Не включайте в тренды документы с `partial: true` или runs с `skippedPaidGraders: true`.

### Результат одного run

```json
{
  "score": 1.0,
  "passed": true,
  "turns": 4,
  "costUsd": 0.14,
  "judgeCostUsd": 0.02,
  "durationSeconds": 41,
  "error": null,
  "tracePath": "/tmp/claude-eval-Ab12Cd/out/trace.jsonl",
  "skippedPaidGraders": false,
  "graders": [
    {
      "name": "uses-product-discovery",
      "passed": true,
      "weight": 1,
      "explanation": "Skill called 1x (expected 1..∞)",
      "withOnly": false,
      "scored": true
    }
  ]
}
```

`error` может быть ненулевым даже при наличии частично успешных результатов: например, run мог успеть создать файл до timeout. `tracePath` может указывать на временный путь, который исчезнет после очистки sandbox.

---

## 10. Коды выхода

| Код | Значение |
|---:|---|
| `0` | Все кейсы достигли `--threshold`, ошибок загрузки нет. |
| `1` | Кейс ниже порога, ошибка файла кейса, нет кейсов, неверная опция, закрытый early-access gate или ошибка записи JSON. |
| `2` | Частичный запуск: достигнут `--max-cost-usd`. Результаты всё равно записываются с `partial: true`. |
| `130` | Запуск прерван через Ctrl-C. |

Проблема публикации HTML-отчёта не меняет код выхода.

---

# Что это значит для planner

Все четыре продуктовые команды planner:

```text
/plan-idea
/plan-epic
/plan-roadmap
/plan-feat
```

обязаны задавать вопросы человеку через `AskUserQuestion`.

Eval запускает headless `claude -p` и не предоставляет скрипт для ответа на живой `AskUserQuestion`. Поэтому одношаговой проверкой нельзя честно покрыть полный процесс этих команд.

## Что проверять без диалога

### `product_state.py`

Помощник `product_state.py` покрыт обычными тестами рядом с исходником, включая состав ответа поставщика (`check-response`). Для него `claude plugin eval` не нужен: это детерминированный код с обычным машинным контрактом.

Не надо создавать eval, который просто ищет строки в prompt или наличие файла, если обычный тест может вызвать функцию и проверить результат.

### Маршрутизацию

Маршрутизацию по подготовленной матрице проверяйте обычным тестом через `route`. Это детерминированная функция, и unit-тест даст более точный сигнал, чем запуск модели.

### Срабатывание правильного skill

Eval полезен для естественных пользовательских формулировок, где нужно проверить, что модель выбрала правильный skill:

```yaml
type: tool_used
name: uses-product-discovery
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?product-discovery"'
min: 1
```

Для запрета прямого перехода в `plan-feat`:

```yaml
type: tool_used
name: does-not-use-plan-feat
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?plan-feat"'
min: 0
max: 0
arm: both
```

Если запускается `--ablation none`, оба грейдера считаются обычными scored-грейдерами. В `with-without` проверки `Skill` без `arm` автоматически становятся `with-only`, поэтому для них нужно учитывать `scored: false`.

### Выбор команды на многошаговом входе

Eval можно использовать, чтобы проверить выбор правильного skill или режима на естественном многошаговом входе, а не на искусственном коротком prompt. Но сам живой диалог нужно либо заранее записать, либо свести проверку к маршрутизации первого шага.

## Как проверять поведение, которое требует диалога

Используйте `context.history_file`.

Схема:

1. провести и записать состоявшийся диалог до нужного хода;
2. сохранить JSONL-транскрипт в директории кейса;
3. указать его в `context.history_file`;
4. передать следующий пользовательский ход через `execution.prompt` или тело `prompt.md`;
5. оценивать поведение именно на этом ходу.

Пример:

```yaml
schema_version: "1.1"
name: follow-up-after-discovery

context:
  history_file: history.jsonl

execution: {}

graders:
  - type: regex
    name: asks-next-relevant-question
    target: last_message
    pattern: "question|следующ"
    flags: i
```

Для таких replay-кейсов используйте:

```bash
claude plugin eval plugins/planner \
  --case follow-up-after-discovery \
  --ablation none \
  --runs 3 \
  --no-publish
```

`--ablation none` нужен потому, что baseline без planner не имеет того же смысла: он не должен проходить записанный planner-диалог как будто plugin-контекст присутствует.

## Что проверить нельзя

Нельзя надёжно проверить:

- живой интерактивный выбор пользователя в `AskUserQuestion`;
- полный процесс сократического диалога как последовательность реальных вопросов и ответов;
- поведение команды, если её обязательные ответы не были заранее записаны в replay;
- качество процесса, которое существует только в интерактивном обмене, но не оставляет проверяемого результата в финальном ответе, trace или файле.

Причина не в planner, а в контракте eval: дочерний агент запускается через `claude -p`, а механизм передачи ответов на `AskUserQuestion` в формате кейса отсутствует.

---

## Минимальный рабочий кейс для planner

Ниже разобранный пример. Готовый набор лежит в `evals/`, его состав и границы описаны в `evals/README.md`.

Цель: естественный запрос:

```text
Есть идея, обсудим?
```

должен привести к skill `product-discovery`, а не сразу к `plan-feat`.

### Структура

```text
evals/idea-routing/
├── prompt.md
└── graders/
    ├── uses-product-discovery.md
    └── does-not-use-plan-feat.md
```

### `prompt.md`

```markdown
---
name: idea-routing
runs: 3
max_turns: 6
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
plugins: ["../.."]
---

Есть идея, обсудим?
```

### `graders/uses-product-discovery.md`

```markdown
---
type: tool_used
name: uses-product-discovery
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?product-discovery"'
min: 1
---
```

### `graders/does-not-use-plan-feat.md`

```markdown
---
type: tool_used
name: does-not-use-plan-feat
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?plan-feat"'
min: 0
max: 0
arm: both
---
```

Запуск из корня репозитория:

```bash
claude plugin eval plugins/planner \
  --case idea-routing \
  --ablation none \
  --runs 3 \
  --no-scaffold \
  --no-publish
```

Это routing-кейс, а не проверка полного product-discovery-диалога. Скилл может успеть вызвать `AskUserQuestion`, после чего run завершится ошибкой или неполным результатом. Это допустимо для такого кейса: интересуют первые вызовы `Skill`, а не завершение диалога. Если нужно проверить ответ после человеческого выбора, создайте replay-кейс через `history_file` и оценивайте его в `--ablation none`.

Для более сильного routing-теста можно добавить грейдер по финальному сообщению, но не делайте его обязательным, если команда закономерно останавливается на первом вопросе.

---

## Риск раннего доступа

`claude plugin eval` пока не является зрелым публичным API Claude Code.

На что не стоит закладываться:

- на наличие публичной страницы со всей спецификацией;
- на неизменность поведения `AskUserQuestion` в headless-run;
- на будущие опции, которых нет в `claude plugin eval --help` текущей версии;
- на старый snake_case-формат JSON из версий до `2.1.210`;
- на то, что модель по умолчанию останется прежней;
- на совпадение scores между разными версиями CLI, моделями и изменёнными грейдерами;
- на автоматическую загрузку project settings, `CLAUDE.md`, памяти или пользовательских plugins.

Для CI:

1. фиксируйте версию Claude Code не ниже `2.1.224`;
2. задавайте `--model` и, при наличии `llm`/`baseline`, `--judge-model`;
3. разбирайте `schemaVersion: 1` и допускайте неизвестные дополнительные поля;
4. исключайте `partial`-результаты и runs со `skippedPaidGraders` из трендов;
5. держите детерминированные проверки отдельно от LLM-судьи;
6. при изменении CLI повторяйте самотест и небольшой пилот `--runs 1`.

---

## Источники

- Проверка CLI и gate: `claude --version`, `claude plugin eval --help`, `claude plugin eval init --help`, запуск `claude plugin eval` в пустом каталоге — **[Запуск]**.
- Формат кейсов, грейдеров, sandbox и JSON v1 — встроенный reference и реализация Claude Code `2.1.234` — **[CLI 2.1.234]**.
- Общие принципы выбора deterministic/model-based graders: [Anthropic — Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).
- Публичная документация skills: [Claude Code skills](https://code.claude.com/docs/en/skills.md). Она описывает отдельный workflow `skill-creator`, а не формат `claude plugin eval`.
- Отдельный формат `skill-creator`: [schemas.md](https://github.com/anthropics/skills/blob/main/skills/skill-creator/references/schemas.md). Он использует `evals/evals.json` и не заменяет `case.yaml`/`prompt.md` этого CLI.
