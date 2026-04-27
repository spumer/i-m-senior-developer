# FEAT-0002 — Plugin `sdlc` (Software Development Life Cycle)

> **Статус:** Ready for Architecture
> **Marketplace:** `i-m-senior-developer`
> **Категория:** development
> **Зависимость:** работает в паре с FEAT-0001 (`planner`) — закрывает execution-фазу `/plan-do`. Ссылается на отдельные плагины `functional-clarity` и `tdd-master`.

## Problem Statement

Текущие dev-агенты (`django-architect`, `python-implementer`, `code-reviewer`) живут как одиночные `.md` в `~/.claude/agents/`. Это даёт три структурных пробела:

1. **Привязка к Python/Django.** `python-implementer.md` оптимизирован под Django/pytest. Для frontend (React/TS) приходится либо назначать его «по созвучию» (нелепо), либо сваливаться в DIY-режим — ровно тот fail, что зафиксирован в `feedback_orchestrator_no_diy_on_agent_gap`. Frontend-проекты остаются без покрытия.
2. **Монолитные .md-файлы.** Все 3 агента — один .md на 200-500 строк, общее (Functional Clarity, fail-fast, минимальные изменения) и язык-специфичное (Django ORM, pytest fixtures) перемешано. Это анти-паттерн progressive disclosure из официальных best-practices Anthropic — при активации сразу грузится 100% контекста, даже если задача тривиальная.
3. **Нет distribute-формы.** Агенты лежат глобально в `~/.claude/agents/` — недистрибутируемо, без semver, без marketplace. Команда не может установить «нашу SDLC-команду» одной командой.

Эти три пробела регулярно приводят к одному сбою: при `/plan-do` для не-Python фичи нет валидного маппинга → оркестратор соскальзывает в DIY-режим.

## User Journey

**Starting Point:** разработчик в проекте N установил marketplace `i-m-senior-developer`. У него уже стоят `tdd-master`, `functional-clarity`, `llms-keeper`, `planner` (FEAT-0001). Хочет полноценный multi-agent конвейер `/plan-do` для любого стека.

**Step-by-Step Flow:**

1. **Установка** (`claude plugin install i-m-senior-developer/sdlc`).
2. **Bootstrap planner** при первом `/plan` обнаруживает 3 новых агента из `sdlc`: `architect`, `code-implementer`, `code-reviewer`. Записывает их в `planner-context.md` §1.
3. **`/plan-do features/FEAT-XXXX/README.md`:**
   - Stage 0 (planner) → определяет stack (`backend-python`, `frontend-react`, `mixed`) по файлам проекта.
   - Stage 1 (architect): оркестратор вызывает `sdlc:architect` с параметром `stack=` или skill сам выбирает references по сигналам в README. Skill открывает `references/<stack>.md` и проектирует по нему.
   - Stage 2 (code-implementer): аналогично — TDD-цикл, ссылка на отдельный плагин `tdd-master:tdd-master` для тестов.
   - Stage 3 (code-reviewer): ревьюер активирует `references/security.md` всегда, плюс stack-specific `references/python-django.md` или `references/frontend-react.md`. Ссылается на плагин `functional-clarity:functional-clarity` для FPF/Error Hiding проверок.
4. **Frontend support:** при `stack=frontend-react` каждый skill в SDLC дополнительно говорит «при UI-fidelity tasks активируй также `document-skills:frontend-design`» (это уже существующий built-in plugin, не дублируем).
5. **Версионирование:** изменения в любом из 3 skills бампают `version` в `plugin.json` плагина sdlc по semver.

**End State:**
- Любой стек покрыт корректным маппингом: backend-python (django/fastapi), frontend (react/vue), node-cli, infra (через extension references/).
- Skills lean (~300 строк каждый), references загружаются on-demand.
- Functional Clarity и TDD не дублируются — отдельные плагины.
- `python-implementer` и старый `django-architect` мигрированы; в `~/.claude/agents/` чисто.

## Edge Cases & Behaviors

| Сценарий | Ожидаемое поведение |
|----------|---------------------|
| Stack не детектирован (нестандартный проект) | Skill использует базовый SKILL.md без stack-references, помечает в output: «stack unknown — universal principles applied». Не падает. |
| Mixed stack (`backend-python` + `frontend-react`) | Architect рассматривает оба ракурса (читает 2 references). Implementer запускается дважды — отдельно на backend-файлах и на frontend-файлах. Reviewer тоже двойной. |
| Запрос без README/ARCH | Skill требует input-файл явно. Fail-fast с сообщением «нужен README или PLAN». |
| `references/<stack>.md` отсутствует для редкого стека | SKILL.md содержит fallback: «Если нет конкретного reference — применяй универсальные принципы из этого SKILL.md и явно отметь в output какой стек обнаружен». |
| Дублирование принципов FC между 3 skills | Не дублировать. Каждый SKILL.md ссылается на `functional-clarity:functional-clarity` плагин, активируя его через стандартный mechanism «другой плагин» (Anthropic docs: «reference other Skills by name — model invokes if installed»). |
| Старый `python-implementer.md` в `~/.claude/agents/` | Migration guide в README плагина: явные `rm -f` инструкции + проверка. На первом запуске skill детектирует legacy и предупреждает. |
| Конфликт имён `code-reviewer` (старый) и `sdlc:code-reviewer` | Plugin namespace разрешает конфликт автоматически — `sdlc:code-reviewer`. Но в `planner-context.md` §1 нужно обновить запись. Migration guide описывает шаг. |
| Skill превышает 500 строк | Anthropic best-practice: split. Перенести в дополнительный references-файл (но не deeper than 1 level). |
| Frontend-design не установлен у пользователя | Skill в `sdlc` упоминает `document-skills:frontend-design`. Если плагин не установлен — Claude graceful degrade на universal принципы. Не падает. |

## Definition of Done

**Must Have:**
- [ ] `plugins/sdlc/.claude-plugin/plugin.json` (name=sdlc, version=0.1.0, description, author, keywords).
- [ ] `plugins/sdlc/agents/architect.md` — тонкий wrapper (~30 строк), активирует skill `sdlc:architect`. Frontmatter: name, description, model=opus (для архитектуры), tools.
- [ ] `plugins/sdlc/agents/code-implementer.md` — тонкий wrapper, model=sonnet.
- [ ] `plugins/sdlc/agents/code-reviewer.md` — тонкий wrapper, model=sonnet.
- [ ] `plugins/sdlc/skills/architect/SKILL.md` — ядро архитектора (~300 строк): bounded contexts, hand-offs, контракты, design-only рамка.
- [ ] `plugins/sdlc/skills/architect/references/backend-python.md` — Django/FastAPI/SQLAlchemy patterns, миграции, API design.
- [ ] `plugins/sdlc/skills/architect/references/frontend-react.md` — компоненты, state, типизация, Vite/Webpack, hooks.
- [ ] `plugins/sdlc/skills/architect/references/api-design.md` — REST/GraphQL контракты, OpenAPI, versioning.
- [ ] `plugins/sdlc/skills/code-implementer/SKILL.md` — ядро имплементера (~300 строк): TDD-цикл (ссылка на `tdd-master`), minimal changes, fail-fast.
- [ ] `plugins/sdlc/skills/code-implementer/references/backend-python.md` — Django ORM, pytest fixtures, mypy, миграции.
- [ ] `plugins/sdlc/skills/code-implementer/references/frontend-react.md` — vitest, RTL, hooks, async, types.
- [ ] `plugins/sdlc/skills/code-reviewer/SKILL.md` — ядро ревьюера (~300 строк): системные проблемы, OWASP, FPF, git-diff подход.
- [ ] `plugins/sdlc/skills/code-reviewer/references/security.md` — OWASP Top 10, secrets, auth, injection.
- [ ] `plugins/sdlc/skills/code-reviewer/references/backend-python.md` — Django security, n+1, ORM pitfalls, atomic ops.
- [ ] `plugins/sdlc/skills/code-reviewer/references/frontend-react.md` — XSS, CSP, accessibility, perf, hooks pitfalls.
- [ ] `plugins/sdlc/README.md` — описание плагина + детальный **migration guide** для `python-implementer`, `django-architect`, `code-reviewer`.
- [ ] Запись плагина в `i-m-senior-developer/.claude-plugin/marketplace.json`.

**Polish:**
- [ ] Каждый SKILL.md имеет блок **Gotchas** с реальными проблемами (Anthropic best-practice — «most valuable section»).
- [ ] Каждый SKILL.md имеет блок «Integration with other plugins» (явные ссылки на `tdd-master`, `functional-clarity`, `planner`, `frontend-design`).
- [ ] SKILL.md ≤500 строк (Anthropic best-practice).
- [ ] References ≤1 уровень от SKILL.md (Anthropic best-practice).
- [ ] Имена skills в gerund-form: `architecting-systems`? Нет — но agents/skills внутри плагина уже namespaced (`sdlc:architect`), читаемость важнее. **Решение:** `architect`, `code-implementer`, `code-reviewer` — короткие существительные/композиты, intuitive.
- [ ] Все references используют forward-slash paths.
- [ ] Каждый SKILL.md описывает явно «Execute or Read?» для своих внешних артефактов (Anthropic best-practice).

## Plugin Structure

```
plugins/sdlc/
  .claude-plugin/
    plugin.json
  agents/
    architect.md                              # ~30 строк, wrapper
    code-implementer.md                       # ~30 строк, wrapper
    code-reviewer.md                          # ~30 строк, wrapper
  skills/
    architect/
      SKILL.md                                # design only, общие принципы (~300 строк)
      references/
        backend-python.md                     # Django/FastAPI design
        frontend-react.md                     # React design
        api-design.md                         # REST/GraphQL contracts
    code-implementer/
      SKILL.md                                # implement, TDD-cycle (~300 строк)
      references/
        backend-python.md                     # Django impl, pytest, mypy
        frontend-react.md                     # React impl, vitest
    code-reviewer/
      SKILL.md                                # review, system issues (~300 строк)
      references/
        security.md                           # OWASP, secrets — всегда активируется
        backend-python.md                     # Python-specific pitfalls
        frontend-react.md                     # Frontend-specific pitfalls
  README.md                                   # description, install, migration guide
```

## Cross-Plugin Integration

Чтобы НЕ дублировать общие принципы:

- **`functional-clarity` plugin** (уже в marketplace) — каждый SKILL.md в sdlc ссылается:
  > «Apply Functional Clarity principles. If plugin `functional-clarity` is installed, activate `functional-clarity:functional-clarity` skill for full 22-principle methodology.»
- **`tdd-master` plugin** (уже в marketplace) — `code-implementer/SKILL.md` ссылается:
  > «For TDD workflow, activate `tdd-master:tdd-master` skill. Use it BEFORE implementing — RED-GREEN-REFACTOR.»
- **`document-skills:frontend-design`** (built-in plugin) — `architect/references/frontend-react.md` и `code-implementer/references/frontend-react.md` ссылаются:
  > «For UI-fidelity (visual quality, design polish), activate `document-skills:frontend-design`.»
- **`planner`** (FEAT-0001) — оркестратор `/plan-do` сам управляет вызовом sdlc-агентов через PLANNER_OUTPUT.md.

## Migration Guide (для README плагина)

```bash
# 1. Установить плагин
# (после публикации — claude plugin install i-m-senior-developer/sdlc)

# 2. Удалить legacy агенты
rm -f ~/.claude/agents/python-implementer.md
rm -f ~/.claude/agents/django-architect.md
rm -f ~/.claude/agents/code-reviewer.md

# 3. В каждом проекте обновить planner-context.md §1:
#    - убрать строки python-implementer, django-architect, code-reviewer
#    - добавить sdlc:architect, sdlc:code-implementer, sdlc:code-reviewer
#    (planner FEAT-0001 при /plan-reflect сделает это автоматически)

# 4. Запустить /plan-do на любой фиче — все 3 фазы должны пройти через sdlc
```

## Visual Description

**Before (status quo):**
- `~/.claude/agents/python-implementer.md` — 250 строк, Python/Django-only.
- `~/.claude/agents/django-architect.md` — 280 строк, Django-only.
- `~/.claude/agents/code-reviewer.md` — 320 строк, всё в одном.
- Frontend-фичи → DIY-режим (см. memory `feedback_orchestrator_no_diy_on_agent_gap`).
- Дублирование принципов Functional Clarity в трёх местах.

**After:**
- Plugin `sdlc` в marketplace. Установка одной командой.
- 3 skill (architect/implementer/reviewer), каждый ~300 строк ядра + references по стекам.
- 3 agent-wrapper в `agents/` плагина — minimum viable, делегируют в skills.
- Functional Clarity и TDD — не дублируются, ссылки на отдельные плагины.
- Frontend covered: `references/frontend-react.md` в каждом skill + ref-mention `frontend-design`.
- `planner` (FEAT-0001) видит SDLC через bootstrap, gap-detection в §1 чистый.

## Open Questions

1. **Naming convention для frontmatter `description` в skills:** третье лицо обязательно (Anthropic best-practice). Перепроверить тон описаний — часто хочется писать «I will architect…», нужно «Architects systems…».
2. **Шаринг common patterns между references/backend-python.md в 3 skills:** официально Anthropic не поддерживает shared/. Если дублирование станет болью — рассмотреть выделение `sdlc-common` плагина с общими принципами. Пока — keep things simple, дублировать осознанно (каждый skill смотрит со своего ракурса).
3. **Hooks:** нужен ли `hooks/session-start.sh` (как у `tdd-master`) для активации? **Решение:** на старте — нет (skills auto-activate по triggers в description). Можно добавить позже.
4. **Skill для DevOps/Infrastructure (Dockerfile, terraform, CI/CD):** не входит в скоуп этого FEAT. См. [FEAT-0003 (sdlc-infra)](../FEAT-0003-sdlc-infra/README.md) — backlog.
5. **Mobile (Android/iOS, React Native, Flutter):** см. [FEAT-0004 (sdlc-mobile)](../FEAT-0004-sdlc-mobile/README.md) — backlog.

## Sources (Anthropic best-practices, applied)

- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — concise, progressive disclosure, references one level deep, gotchas, third-person descriptions, gerund naming.
- [Create plugins](https://code.claude.com/docs/en/plugins.md) — directory structure, namespacing, version management.
- [Extend Claude with skills](https://code.claude.com/docs/en/skills) — skill discovery, multi-skill loading, share context window.

---

**Ready for Technical Design:** Yes
**Next:** `/plan-do features/FEAT-0002-sdlc-plugin/README.md` после согласования. Зависимость от FEAT-0001: рекомендуется делать B (planner) → A (sdlc), потому что sdlc-плагин полагается на planner для bootstrap-маппинга в §1.
