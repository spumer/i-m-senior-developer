---
name: fpf-integration
description: >
  This skill should be used when the user asks to "integrate FPF", "add FPF to project",
  "FPF audit", "review decisions with FPF", "check evidence quality", "add decay mechanism",
  "check cognitive biases in decisions", "add FPF checklists to roles", "NQD check",
  "alternatives check", "evidence graph review", "bounded context audit", "terminology drift",
  mentions "First Principles Framework" or "FPF", or wants to improve decision-making
  quality in a multi-agent system.
version: 0.3.0
---

# FPF Integration for Multi-Agent Systems

Integrate First Principles Framework (FPF) into multi-agent projects to improve
decision quality, reduce cognitive biases, and ensure evidence-based reasoning.

> **Источник:** First Principles Framework (FPF) — `https://github.com/ailev/FPF`
> (FPF-Spec). Этот скилл — практическая обвязка для интеграции FPF в проекты;
> канонические определения аксиом (A.7, A.10, A.11, A.1.1, NQD, DRR и др.) живут
> в FPF-Spec. См. протокол доступа к спецификации ниже.

> **Доступ к спецификации ОБЯЗАТЕЛЕН.** Работа скилла требует доступа к каноническому
> тексту FPF — одним из двух источников, по приоритету: **сначала FPF-справочник через
> MCP** (если подключён — самый авторитетный: точные ID, цитаты, живая свежесть),
> **иначе локальная копия `FPF-Spec.md`** (~9.5 МБ, не входит в плагин). Нет ни того,
> ни другого — **скилл не переходит в «облегчённый» режим и не работает по памяти: он
> блокируется и требует настроить доступ** (см. «Протокол доступа к FPF» → Уровень 3).
> Проверка источника — в момент первого обращения к спеке, не при активации.

## Entry Point Decision Tree

- **New project, no artifacts** → Phase 0 + Phase 1a (Foundation)
- **Existing project, need full integration** → Phase 0 + Phase 1b (Audit) + Phase 2-5
- **Single decision review** → Phase 1b step 2 only (6-question express review)
- **Add checklists to roles** → Phase 2 only
- **Upgrade decision format** → Phase 3 only

## Core FPF Principles (Quick Reference)

| Principle | Rule | Check |
|-----------|------|-------|
| **A.10 Evidence Graph** | Claim without proof = opinion | "Source? Method? Date?" |
| **A.7 Strict Distinction** | Description != capability != fact | "Is this how it SHOULD work or how it DOES work?" |
| **A.1.1 BoundedContext** | Meaning is local, translation explicit | "Does this term mean the same thing to all roles?" |
| **A.11 Parsimony** | Add only what cannot be subtracted | "Can existing tools express this?" |
| **NQD** | >= 3 alternatives before choosing | "What are 2 more options?" |
| **DRR Decay** | Evidence expires, decisions need review dates | "When does this evidence go stale?" |

## Integration Flow

Determine the entry point, then follow phases sequentially.

### Phase 0: Diagnose (30 min)

Ask the project owner/lead 5 key questions to determine scope. Use `AskUserQuestion` with structured options.

**Key questions:**
1. New project or existing? (greenfield vs retrofit)
2. How many roles/agents? (1-3 light / 4-10 medium / 10+ heavy)
3. How many decisions exist? (0 skip / 1-5 single session / 5+ dedicated session)
4. Domain complexity? (Clear/Complicated/Complex/Chaotic)
5. Current pain points? (terminology → A.1.1 / bad decisions → A.10 / no alternatives → NQD)

**Run the FPF Maturity Test** (5 yes/no questions):
1. Are claims in artifacts marked as fact/hypothesis/opinion? → A.10
2. Do all roles understand terms identically? → A.1.1
3. Are rejected alternatives documented for each decision? → NQD
4. Do decisions have review dates? → DRR
5. Do roles distinguish "as described" from "as observed"? → A.7

Score: 0-1 yes = integrate from scratch / 2-3 = partial / 4-5 = strengthen existing.

### Phase 1a: Foundation (Greenfield)

For new projects without existing artifacts.

1. **Create glossary.md** (A.1.1) — term | definition | "is NOT"
2. **Create domain.md** (A.10) — facts about reality, each with source + date
3. **Set DRR template** — add `evidence_valid_until`, `review_date`, `alternatives_considered` to decision format
4. **Establish USF/KDF/MDF/NOF** — 4-question diagnostic before every session:
   USF = What is the system? / KDF = How good is my knowledge? / MDF = Best method? / NOF = Ultimate goal?
   (Full protocol in `references/practical-tools.md`)

### Phase 1b: Audit (Retrofit)

For existing projects with decisions and artifacts.

1. **Inventory** all decisions, artifacts, roles
2. **6-question express review** per decision:
   - Evidence chain: every claim has a source? (A.10)
   - >= 3 alternatives considered? (NQD)
   - Which cognitive biases could have influenced? (bias check)
   - When does evidence expire? → set `evidence_valid_until`
   - Kill criteria exist and have a verification protocol?
   - "Described" vs "observed" distinguished? (A.7)
3. **Terminology audit** — cross-check terms across roles (A.1.1)
4. **Build role x principle matrix** — which principles matter most per role

For detailed audit patterns and an illustrative case study, consult `references/audit-patterns.md`.

### Phase 2: Role Checklists

For each role in the system:

1. Identify role domain (what it decides, what artifacts it writes)
2. Select top 3-5 FPF principles critical for this role
3. Identify top 2-3 cognitive biases dangerous for this role's domain
4. Compose checklist of 5-7 items — concrete, not abstract:
   - "Each score backed by specific observation from this interview" (concrete)
   - NOT "check for bias" (abstract)
5. Write checklist into role's context.md

For role-type templates (analyst, architect, critic, stakeholder voice, coordinator, builder),
consult `references/role-templates.md`.

### Phase 3: Decision Format (DRR)

Upgrade all decisions to Design Rationale Record format.

**Required YAML fields:**
```yaml
evidence_valid_until: "YYYY-MM-DD"
review_date: "YYYY-MM-DD"
alternatives_considered: N  # NQD >= 3 for Complicated/Complex
```

**Required body sections:**
1. Context and problem (USF: What is the system? What is broken?)
2. Alternatives (>= 3) with trade-offs for each
3. Decision and rationale with evidence chain (source, method, date per claim)
4. Evidence quality self-assessment (strong / partial / weak)
5. Rejected alternatives with reasons why not chosen
6. Kill criteria with verification protocol: who checks, when, by what method, what to do if triggered

Full DRR template with examples in `references/practical-tools.md`.

**Cynefin adaptation for alternatives count:**
- Clear → 0-1 sufficient (apply rules)
- Complicated → >= 3 strictly (NQD)
- Complex → >= 3 + safe-to-fail probes
- Chaotic → 0 (act first, analyze later)

### Phase 4: Operations

Embed FPF triggers into daily workflow.

| Event | FPF Action |
|-------|------------|
| Session start | USF/KDF/MDF/NOF express (30 sec) |
| New term | → glossary.md (A.1.1) |
| New fact | → domain.md with source (A.10) |
| Decision | DRR format + NQD >= 3 |
| Claim "works like X" | "Description, capability, or fact?" (A.7) |
| Single option proposed | "Two more alternatives" (NQD) |
| Discussion > 30 min | Navigator abstraction test |
| review_date reached | Re-verify evidence or issue waiver |

### Phase 5: Review Cycle

**Biweekly:** check all review_dates, raise expired as tensions.

**Monthly health check** (15 min):
- NQD compliance: % of decisions with >= 3 alternatives
- Evidence quality: any "weak" decisions?
- Decay coverage: all decisions have review_date?
- Terminology drift: terms outside glossary?

**Quarterly deep review** (1-2 hours):
- Full decision audit (Phase 1b step 2)
- Update role x principle matrix
- Retrospective: what FPF gave, what hindered, what to remove

**Escalation:** when issues found during review — raise as tension in next session. Expired evidence_valid_until without waiver = mandatory agenda item.

## 7 Questions for Any Artifact

Before publishing any artifact in a multi-agent system:

1. **Evidence (A.10):** Every claim — fact, hypothesis, or opinion? Marked?
2. **Scope (A.1.1):** Terms match glossary? Context explicit?
3. **Distinction (A.7):** Where are design-time claims?
4. **Alternatives (NQD):** >= 3 considered (for Complicated/Complex)?
5. **Decay (DRR):** When does evidence expire? review_date set?
6. **Parsimony (A.11):** Duplicates existing? Simpler possible?
7. **Kill (DRR):** What must happen to revoke this decision?

## Anti-Patterns

| Anti-pattern | Symptom | Fix |
|--------------|---------|-----|
| "All at once" | 20 FPF principles in session 1 | Start with 3: A.10, A.1.1, NQD |
| "FPF jargon" | Roles say "BoundedContext" | Use plain language: "fact or hypothesis?" |
| "Checklist for checklist's sake" | Roles tick boxes without thinking | Checklist = thinking trigger, not goal |
| "AI consensus = evidence" | 5 agents agree → must be right | AI agents on same model ≠ independent opinions |
| "FPF overload" | More time on checklists than work | FPF = tool, not goal. Simplify if heavier than problem |

## FPF Knowledge Base

Канонический текст FPF берётся из одного из трёх источников, по приоритету. Выбор
делается в момент ПЕРВОГО обращения к спеке (не при активации скилла).

### Уровень 1 — FPF-справочник через MCP (предпочтительно)

Если в сессии доступны инструменты FPF-справочника (MCP `fpf_reference` —
`get_fpf_index_status`, `search_fpf`, `read_fpf_doc`, `query_fpf_spec`,
`browse_fpf_catalog`) — использовать их. Это самый авторитетный источник: точные ID
паттернов, канонический текст с цитатами, живая проверка свежести — без локальной
копии и без дрейфа номеров строк.

- `get_fpf_index_status` — свежесть индекса (`builtAt`, `sourceHash`, `fresh`).
  Проверить перед trust-sensitive использованием.
- `search_fpf` — полнотекстовый поиск по узлам спеки (заменяет Grep по копии).
- `read_fpf_doc` — каноническая страница по ID / маршруту / лексеме, точный текст
  (заменяет Read секции по номеру строки).
- `query_fpf_spec` — вопрос к спеке с цитатами (`citations`), constraints и
  метаданными свежести.
- `browse_fpf_catalog` — обзор паттернов/маршрутов/лексикона по части и статусу.

При наличии MCP навигационные reference-файлы (`fpf-sections-map.md`,
`fpf-grep-patterns.md`, `fpf-tasks-lookup.md`) для поиска НЕ нужны — MCP авторитетнее
и не устаревает по номерам строк. Они остаются офлайн-резервом (уровень 2). Провенанс
индекса FPF даёт сам MCP через `get_fpf_index_status` — сверять с ним, а не с
номерами строк в reference-файлах.

### Уровень 2 — локальная копия FPF-Spec.md + навигационные файлы

Когда MCP недоступен, а копия спеки есть. FPF-Spec.md (~93K строк, ~9.5MB) слишком
велик для загрузки целиком — скилл включает навигационные файлы для точечного доступа:

- **`references/fpf-sections-map.md`** — карта **285 паттернов** (280 Stable + 5 Planned) по 22 разделам (части и кластеры), с номерами строк, статусом, заголовками и keywords/queries из встроенного реестра спеки
- **`references/fpf-grep-patterns.md`** — проверенные regex-паттерны для Grep (каждый реально матчится в спеке этого SHA)
- **`references/fpf-glossary.md`** — ключевые термины FPF (EN/RU) с определениями и ссылками на секции
- **`references/fpf-tasks-lookup.md`** — задачи → секции → grep-паттерны для поиска

> **Провенанс индекса:** все навигационные файлы сгенерированы из встроенного реестра
> FPF-Spec.md @ ailev/FPF `44dd88188a07` (2026-07-12). Что изменилось при последней
> ре-индексации — в `CHANGES-fpf-spec.md`. Насколько индекс актуален: сравни этот SHA
> с `upstream_commit` в `~/.claude/knowledge/fpf/FPF-Spec.version` (его пишет
> `scripts/fetch-fpf-spec.sh`) и с текущим `gh api repos/ailev/FPF/commits/main`.
> Расходятся → стоит перегенерировать индекс (Grep-навигация работает и при дрейфе,
> но номера строк устаревают).

Порядок работы с копией:

1. **Найти копию ПЕРЕД первым обращением к спеке.** Глобально:
   `~/.claude/knowledge/fpf/FPF-Spec.md` (разверни `~` в `$HOME` — Glob не раскрывает
   тильду). В проекте: Glob по `.claude/knowledge/fpf/FPF-Spec.md`, `FPF-Spec.md` в
   корне, `**/FPF-Spec.md`. Первый найденный (глобальный приоритетнее — общий на все
   проекты).
2. Определить задачу → найти в `fpf-tasks-lookup.md`.
3. Получить секцию и grep-паттерн → **Grep по FPF-Spec.md (по паттерну, не по номеру
   строки)**.
4. Read вокруг найденного совпадения. **Номера строк в `fpf-sections-map.md` —
   приблизительные якоря, не точные offset'ы:** спека в статусе "eternal alpha",
   свежескачанная версия почти наверняка имеет другие номера строк. Сначала Grep,
   потом Read вокруг матча — не доверять offset вслепую.

### Уровень 3 — блокер (нет ни MCP, ни копии)

Если недоступны И MCP, И локальная копия — **СТОП. Не продолжать работу по FPF, не
переходить в облегчённый режим, не разбирать аксиомы по памяти или по одной
Quick-Reference-табличке.** Облегчённого режима нет намеренно: разбор по памяти — это
claim without source (A.10), а в скилле про доказательность решений сам скилл не имеет
права его нарушать. Встроенные reference-файлы (`fpf-glossary.md`,
`fpf-sections-map.md` и др.) — навигация и офлайн-резерв для Уровня 2 при наличии
копии, НЕ замена спеке.

Сообщить пользователю и потребовать настроить доступ (не «спросить, продолжать ли
облегчённо» — продолжения нет):

> FPF недоступен: нет ни MCP-справочника, ни локальной копии `FPF-Spec.md`. Скилл не
> работает по памяти (это нарушило бы его собственный принцип A.10 — claim without
> source). Настрой один источник и повтори запрос:
> - подключить FPF-справочник как MCP-сервер (`fpf_reference`), **или**
> - скачать спеку: `scripts/fetch-fpf-spec.sh` (в `~/.claude/knowledge/fpf/FPF-Spec.md`;
>   `--project` — в проект, `--force` — перекачать), либо вручную из
>   `https://github.com/ailev/FPF`.

### Где взять FPF (по приоритету)

- **MCP-справочник (рекомендуется):** подключить FPF `fpf_reference` как MCP-сервер —
  тогда уровень 1 доступен без локальной копии.
- **Скрипт для копии:** `scripts/fetch-fpf-spec.sh` — качает с GitHub в
  `~/.claude/knowledge/fpf/FPF-Spec.md`. Флаги: `--project` (в проект), `--force` (перекачать).
- Вручную с GitHub: https://github.com/ailev/FPF (ветка `main`, файл `FPF-Spec.md`)
- Автор: Анатолий Левенчук. Версия: March 2026. Статус: "Normative kernel, eternal alpha"

## Additional Resources

### Reference Files — Integration Guide

- **`references/audit-patterns.md`** — Паттерны ретроспективного ревью + иллюстративный case study
- **`references/role-templates.md`** — Шаблоны FPF-чеклистов по 6 архетипам ролей + матрица
- **`references/practical-tools.md`** — USF/KDF/MDF/NOF, NQD-протокол, DRR-шаблон, Intellect Stack, Conformance Checklist

### Reference Files — FPF Knowledge Base

- **`references/fpf-glossary.md`** — 100 терминов FPF
- **`references/fpf-sections-map.md`** — Карта секций с номерами строк
- **`references/fpf-tasks-lookup.md`** — Задача → секция → grep-паттерн
- **`references/fpf-grep-patterns.md`** — Regex-паттерны для поиска в спеке
