# planner

Claude Code plugin for file-backed product discovery, feature planning, and implementation orchestration.

Work happens in two layers.

The product layer shapes intent before anything technical exists:

- `ideas/IDEA-NNNN-<slug>.md` — a discovery record: problem, evidence, critical unknown, explicit outcome;
- `epics/EPIC-NNNN-<slug>/EPIC.md` — one shared hypothesis for an outcome delivered by several slices;
- `epics/EPIC-NNNN-<slug>/ROADMAP.md` — slice order across Now/Next/Later horizons.

The technical layer separates three artifacts per feature:

- `README.md` — requirements and user-visible behavior;
- `ARCHITECTURE.md` — ready technical design;
- `PLANNER_EXECUTION.md` — implementation phases tied to one architecture version.

The full result lives in a file. A successful run prints only the path, version, and two to four main outcomes.

## What it does

- **Product discovery** — `/plan-idea`, `/plan-epic`, `/plan-roadmap`, and `/plan-feat` facilitate problem framing, a shared hypothesis, slice ordering, and slice requirements, each ending in a versioned file.
- **Capability routing** — product work goes to the most capable available provider from the `§9` matrix in `.claude/planner-context.md`; the built-in `product-baseline` skill is a limited last resort.
- **Requirements gathering** — `/plan-jira` formats requirements from a Jira description into a task brief.
- **Project bootstrap** — scans available agents, commands, skills, stack markers, and feature-directory conventions into `.claude/planner-context.md`.
- **Architecture mode** — `/plan` on a feature README or free-text task writes a complete `ARCHITECTURE.md`.
- **Execution mode** — `/plan` on architecture writes a separate `PLANNER_EXECUTION.md` with phases, dependencies, models, and review gates.
- **Freshness guard** — architecture and execution plans carry versions and SHA-256 body fingerprints. Direct architecture edits make the execution plan stale even when its visible version was not updated manually.
- **Implementation orchestration** — `/plan-do` проверяет свежесть перед каждым вызовом роли, назначает файлы отчётов и координирует фазы реализации, ревью и документации.
- **Экспериментальный workflow** — `/planner:plan-do-workflow <каталог-фичи>` явно запускает отдельный workflow с кодовым порядком фаз; обычный `/planner:plan-do` остаётся действующим путём.
- **Post-task learning** — `/plan-reflect` writes stable lessons back to `.claude/planner-context.md`.

## Structure

```text
plugins/planner/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   └── planner.md
├── commands/
│   ├── plan-idea.md
│   ├── plan-epic.md
│   ├── plan-roadmap.md
│   ├── plan-feat.md
│   ├── plan-jira.md
│   ├── plan.md
│   ├── plan-do.md
│   ├── plan-do-workflow.md
│   └── plan-reflect.md
├── workflows/
│   └── plan-do-workflow.js
├── skills/
│   ├── planner/
│   │   ├── SKILL.md
│   │   ├── assets/
│   │   │   ├── plan_state.py
│   │   │   └── test_plan_state.py
│   │   └── references/
│   │       ├── bootstrap.md
│   │       ├── architecture-mode.md
│   │       ├── execution-mode.md
│   │       └── template-context.md
│   ├── product-discovery/
│   │   ├── SKILL.md
│   │   ├── assets/
│   │   │   ├── product_state.py
│   │   │   └── test_product_state.py
│   │   └── references/
│   │       ├── routing.md
│   │       ├── dialogue.md
│   │       ├── pov-review.md
│   │       ├── idea-mode.md
│   │       ├── epic-mode.md
│   │       ├── roadmap-mode.md
│   │       └── feature-mode.md
│   ├── product-baseline/
│   │   └── SKILL.md
│   └── planner-reflect/
│       └── SKILL.md
├── hooks/
│   ├── hooks.json
│   └── product_intake_hint.py
├── evals/
│   ├── README.md
│   ├── run.py
│   ├── idea-routing/
│   ├── multi-step-input/
│   └── baseline-provider-limits/
└── README.md
```

## Installation

Add this marketplace to Claude Code and install the plugin:

```text
/plugin marketplace add spumer/i-m-senior-developer
/plugin install planner@i-m-senior-developer
```

## Typical flow

The product layer, when used:

```text
/plan-idea "save items users keep losing"
        ↓ writes ideas/IDEA-0001-<slug>.md, ends with an explicit outcome
/plan-epic ideas/IDEA-0001-<slug>.md
        ↓ writes epics/EPIC-0001-<slug>/EPIC.md — one shared hypothesis
/plan-roadmap epics/EPIC-0001-<slug>/EPIC.md
        ↓ writes epics/EPIC-0001-<slug>/ROADMAP.md — slices across Now/Next/Later
```

The technical chain, starting from a slice:

```text
/plan-feat "bookmarks for items"        ← a roadmap item or a resolved idea works too
        ↓ writes features/FEAT-0001-<slug>/README.md
/plan features/FEAT-0001-<slug>/README.md
        ↓ writes features/FEAT-0001-<slug>/ARCHITECTURE.md
/plan features/FEAT-0001-<slug>/ARCHITECTURE.md
        ↓ writes features/FEAT-0001-<slug>/PLANNER_EXECUTION.md
/plan-do features/FEAT-0001-<slug>/
        ↓ проверяет свежесть; роли пишут полные отчёты фаз в файлы и возвращают доказательные сводки
/plan-reflect features/FEAT-0001-<slug>/
        ↓ records stable lessons in planner-context.md
```

The product layer is optional: `/plan-feat` accepts a slice description directly, and the technical chain works as before.

The namespaced forms (`/planner:plan`, `/planner:plan-do`, and others) are available when a local command has the same bare name.

## Product discovery

Four commands cover the layer before architecture: one facilitated dialogue each, one versioned document each, no implementation design.

| Command | Writes |
|---|---|
| `/plan-idea` | `ideas/IDEA-NNNN-<slug>.md` — problem, evidence, critical unknown, and an explicit outcome |
| `/plan-epic` | `epics/EPIC-NNNN-<slug>/EPIC.md` — one shared hypothesis for an outcome delivered by several slices |
| `/plan-roadmap` | `epics/EPIC-NNNN-<slug>/ROADMAP.md` — slice order across Now/Next/Later |
| `/plan-feat` | `features/FEAT-NNNN-<slug>/README.md` — requirements of one deliverable slice |

An idea must end in an explicit outcome — `feature` or `epic` — and either outcome feeds the next command. `/plan-feat` also accepts a slice description, a roadmap item, or an existing feature path directly. Existing requirement files are read as version 0 and are not rewritten for migration.

Product documents follow the same version discipline as plan documents: a semantic change increments the version, wording does not. Updating an epic marks a sibling `ROADMAP.md` stale by fingerprint, without rewriting its body.

### Capability routing

Product work is routed to a capability provider rather than done by the command alone. The capabilities required for the document kind are matched against the `§9 Способности и поставщики` matrix in `.claude/planner-context.md`, and the most capable available provider is selected for each: `full` coverage before `partial`, and `configured` before `project`, `plugin`, or built-in priority. A matching name alone proves nothing — coverage requires an evidence path. A pinned provider that is unavailable stops the run instead of being silently replaced.

When no external provider covers a required capability, the built-in `product-baseline` skill is the last resort. It orders and phrases what the input already carries, states its limitations in every response, and never writes files.

A provider draft is accepted only after the helper checks its shape: `check-response` rejects a draft missing `problem`, `outcome`, or `limitations`, and rejects fields belonging to another document kind instead of dropping them silently. Two parts of the same contract stay a judgement the skill makes — a provider reporting a file write, and a provider claiming user research, real human feedback, independent multi-role review, or a confirmed hypothesis.

### Проверка основания и черновика

Для участия в выборе строка матрицы должна содержать содержательное основание. Прочерк и одна служебная HTML-метка основанием не считаются: покрытие такой строки становится неизвестным. Если для обязательной способности не остаётся подходящего поставщика, проработка останавливается до его вызова. Сообщение называет непокрытую способность и все её отклонённые строки с номером, поставщиком и причиной. При успешном выборе итог также показывает выбранные и отклонённые строки.

Черновик ответа поставщика сохраняется только под именем `provider-response.json` в отдельном системном временном каталоге вне репозитория. Поставщик сам файлов не создаёт. После машинной проверки помощник удаляет черновик и его временный каталог и при принятии ответа, и при отказе.

### Write boundary

The canonical document is written only by the `product_state.py` helper. The model prepares the document body in a temporary `.prepared` file and calls the helper, which allocates numbered directories, assigns versions, records the parent's version and fingerprint, and writes or refuses. Providers never write files; neither does the model write the canonical file directly.

## Planning modes

### Architecture

Inputs:

- feature `README.md`;
- feature directory containing `README.md`;
- free-text task with no filesystem path.

Outputs:

- feature input → `ARCHITECTURE.md` beside the README;
- free text → `.claude/plans/<task-slug>/ARCHITECTURE.md`.

Architecture mode writes the complete design. It does not leave a separate file of instructions for a future architect run.

### Execution

Input: an existing architecture document, including an explicitly supplied legacy `*-PLAN-*.md` or `*-DESIGN-*.md`.

Output: `PLANNER_EXECUTION.md` beside the architecture.

The execution header records:

- its own version and status;
- its own body fingerprint;
- the architecture path, version, and body fingerprint.

## Freshness and versions

New architecture:

```yaml
---
plan_type: architecture
version: 1
status: current
content_sha256: <body fingerprint>
---
```

New execution plan:

```yaml
---
plan_type: execution
version: 1
status: current
content_sha256: <body fingerprint>
architecture:
  path: "./ARCHITECTURE.md"
  version: 1
  content_sha256: <architecture body fingerprint>
---
```

Rules:

- a semantic body change increments that document's version;
- wording or formatting without a semantic change preserves the version;
- changing only `current` to `stale` preserves the execution version and body;
- architecture without supported frontmatter is read as version 0 and is not rewritten merely for migration;
- direct body changes are detected by the fingerprint;
- Git owns history, so the plugin rewrites current files instead of creating numbered copies.

## `/plan-do` guard

`/plan-do` runs the state helper before every Agent call. It stops when:

- the execution file is missing or invalid;
- the architecture path is missing or invalid;
- recorded and current architecture versions differ;
- the architecture fingerprint differs;
- the execution plan is already marked `stale`.

The guard cannot be bypassed by confirmation. Rebuild the plan with:

```text
/plan <path-to-current-architecture>
```

## Экспериментальный workflow выполнения

`/planner:plan-do-workflow <каталог-фичи>` — отдельная экспериментальная команда для текущего плана выполнения. Она предварительно проверяет каталог и обязательные файлы, затем запускает workflow `planner:plan-do-workflow` из `workflows/plan-do-workflow.js`.

Обычный цикл `/planner:plan-do` не меняется и остаётся действующим путём. Экспериментальная команда не вызывается автоматически и не переключается на обычную команду при отказе.

Итог workflow возвращает состояние, число рабочих вызовов, число проверок свежести, забронированные пути и пути записанных отчётов. Полный текст отчётов в итог не включается.

## Отчёты фаз

Для каждой роли, вызванной оркестратором, действует один принцип: полный отчёт записывается в файл, а доказательная сводка возвращается в контекст оркестратора. Номер отчёта — наибольший занятый плюс один: дыры в нумерации не переиспользуются, номер только растёт (до 99). Путь бронируется до вызова роли, поэтому параллельные прогоны не затирают чужие отчёты. Прерванный прогон может оставить по пути пустой файл — это не ошибка, автоматически он не удаляется. Имена: `IMPLEMENTATION-NN.md` для реализации и кругов правок, `review-request-changes/REVIEW-NN.md` для ревью, `DOCUMENTATION-NN.md` для документации.

Замечание к проектированию не блокирует текущее ревью и не делает текущий диф дефектным. Оно останавливает план до следующей рабочей фазы, чтобы решение принял человек. `/plan-do` не вызывает архитектора автоматически; если решение меняет архитектуру, следующий гейт свежести требует пересобрать план выполнения.

## Chat output

After a successful write, `/plan` and the product commands print only:

- result kind;
- path and version;
- two to four main outcomes;
- next command, when needed.

If writing or metadata synchronization fails, the command says the file was not saved and returns the complete prepared document in chat as a fallback.

## Legacy `PLANNER_OUTPUT.md`

An existing `PLANNER_OUTPUT.md` is preserved. New planner runs do not delete it and do not treat it as the current architecture or execution plan.

## Commands

| Command | Purpose |
|---|---|
| `/plan-idea` | Facilitate idea discovery — problem, evidence, critical unknown, explicit outcome |
| `/plan-epic` | Facilitate a shared hypothesis for one outcome delivered by several slices |
| `/plan-roadmap` | Order the slices of one shared hypothesis across Now/Next/Later |
| `/plan-feat` | Gather requirements for one deliverable slice and write a feature README |
| `/plan-jira` | Gather requirements from a Jira description |
| `/plan` | Write architecture or execution planning to a file |
| `/plan-do` | Проверить свежесть, скоординировать роли и сохранить отчёты фаз |
| `/planner:plan-do-workflow <каталог-фичи>` | Явно запустить экспериментальный workflow `planner:plan-do-workflow` по текущему плану |
| `/plan-reflect` | Record stable project-specific lessons |

## Configuration

Project-specific agent mappings, model guidance, and artifact paths live in `.claude/planner-context.md`. Bootstrap creates it on first use. A rescan appends auto-discovered entries and marks missing entries stale without overwriting manual decisions.

Section `§9` of the same file is the machine-readable capability matrix used by product discovery: bootstrap fills it from discovered plugin agents, and product commands stop rather than substitute an unavailable pinned provider.

## Evaluation

Run the full behavioural suite with one command:

```bash
python3 plugins/planner/evals/run.py
```

The wrapper pins the run contract, verifies the aggregate result, and refuses a partial run. General rules for plugin testing live in `docs/testing/`; the observed result of the latest run is recorded in `docs/reports/planner.md`.

Three cases check what is observable without a dialogue: a raw idea reaching discovery instead of slice requirements, a multi-outcome input not collapsing into one slice, and the built-in provider naming its limitations while writing no file. All three pass three runs out of three at the strict threshold.

Routing into discovery is not left to the skill description alone: the `UserPromptSubmit` hook in `hooks/` recognises a product-shaped prompt by explicit markers and requires the skill before an answer. The hook never blocks a prompt and stays silent on technical requests.

What no case can cover is stated plainly. All four product commands ask the human through `AskUserQuestion`, and an eval case cannot script those answers; behaviour that depends on an answer needs a recorded transcript replayed through `context.history_file`. The helper and provider routing need no eval at all — they are covered by ordinary tests beside the code.