# FEAT-0003 — Plugin `sdlc-infra` (SSH + docker-compose deployment, v0.1)

> **Статус:** Ready for Technical Design
> **Marketplace:** `i-m-senior-developer`
> **Категория:** development / infra
> **Зависимость:** установленный FEAT-0002 (`sdlc`) — `sdlc-infra` дополняет его стадией deployment, но работает автономно.

## Problem Statement

После реализации FEAT-0002 (sdlc) проект имеет multi-agent конвейер для backend-python и frontend-react: design → implement → review. Как только разработчик доходит до **deployment**, конвейер обрывается. Реальные кейсы — простые single-host deployments через ssh + docker-compose — остаются ручной рутиной: Dockerfile копируется из StackOverflow, deploy-скрипт без `set -e`, `.env` иногда улетает в репо, контейнер крутится от root. Нет агента, который спроектирует docker-compose.yml, напишет deploy-скрипт и проверит безопасность по тем же FPF-инвариантам, что использует sdlc для кода (fail-fast, no information loss, explicit errors).

## Scope (v0.1)

**В скоупе:**
- Single-host deployment (1 VPS, ssh + docker-compose)
- `Dockerfile`, `docker-compose.yml`, bash deploy-скрипты (включая `.github/workflows/deploy.yml` как ssh-runner)
- Secrets через `.env`-файлы на хосте (gitignored, deploy-time copy)
- Опциональные best-practice валидаторы: `docker-compose config` и `shellcheck`

**Вне скоупа v0.1 (явные нон-цели):**
- Terraform / Pulumi / OpenTofu (IaC для cloud-ресурсов)
- Kubernetes / Helm / Kustomize / Docker Swarm
- Multi-host deployments, blue-green, canary
- Расширенные secrets (HashiCorp Vault, SOPS, Docker secrets)
- Compliance-сканеры (tfsec, checkov, trivy, dockle, hadolint)
- Полноценный TDD (Terratest, container-structure-test)

Эти позиции уходят в backlog v0.2 и поднимаются по факту накопления реальных кейсов (см. секцию **Triggers for v0.2**).

## User Journey

**Starting Point:**
Разработчик закончил фичу через `/plan-do` (`sdlc:architect → sdlc:code-implementer → sdlc:code-reviewer`). Код готов в репо. Нужно задеплоить на single-host VPS через ssh + docker-compose. Сейчас это означает «открыть Notion с записками и копипастить».

**Step-by-Step Flow:**

1. Разработчик вызывает `sdlc-infra:infra-architect` (через `/plan` или `Task` tool с `subagent_type=sdlc-infra:infra-architect`).
2. Агент читает репо и задаёт уточняющие вопросы: какой образ собирается, какие порты пробрасываются, какие volumes нужны для persistence, какие env-переменные обязательны, есть ли healthcheck, какой `restart`-policy, есть ли отдельный сервис БД.
3. Архитектор выпускает `INFRA-PLAN.md` с разделами: Dockerfile structure (base image, multi-stage, USER, COPY-порядок), docker-compose service shape (volumes, networks, healthcheck, restart, depends_on), deploy-flow (build локально → ssh → compose pull/up), `.env`-расположение, backup/rollback стратегия (минимально — компоненты, которые надо бэкапить, и команда rollback).
4. Разработчик вызывает `sdlc-infra:iac-implementer`.
5. Реализатор пишет: `Dockerfile`, `docker-compose.yml`, `deploy.sh` (или `.github/workflows/deploy.yml`), `.env.example`, обновляет `.gitignore`, добавляет deployment-секцию в репо-`README.md`. Тесты не пишет (политика v0.1 — опционально).
6. Разработчик вызывает `sdlc-infra:infra-reviewer`.
7. Ревьюер прогоняет статические проверки и выдаёт findings, классифицированные по приоритету:
   - `docker-compose config` (валидация yaml/синтаксиса)
   - `shellcheck` на deploy-скрипты
   - Проверка `.gitignore` (`.env` исключён? `.env.example` — нет?)
   - Hardcoded secrets в `Dockerfile` / `docker-compose.yml` / `deploy.sh`
   - `set -euo pipefail` в shell-скриптах (fail-fast)
   - `latest`-тег образов
   - `USER`-directive (не root)
   - Healthcheck/restart-policy на сервисах
   - Information-removal: не уходит ли логирование в `/dev/null`
8. Если P0/P1 чисто — деплой готов, разработчик запускает `bash deploy.sh` или пушит в `main` для GH Actions.

**End State:**
В репо появились: `Dockerfile`, `docker-compose.yml`, `deploy.sh` (или `.github/workflows/deploy.yml`), `.env.example`, `.gitignore` обновлён, deployment-секция в `README.md`. На сервере поднят docker-compose stack, `.env` лежит на хосте, не в репо. Все P0/P1 findings закрыты.

## Edge Cases & Behaviors

| Scenario | Expected Behavior |
|----------|-------------------|
| `.env` уже зафиксирован в git-истории | Reviewer P0: блокирует merge, требует ротации секретов и фильтра истории (`git filter-repo` или эквивалент) |
| `Dockerfile` делает `RUN apt-get update` без `&& apt-get install` в той же строке | Reviewer P1: layer-caching antipattern, рекомендует объединение |
| `docker-compose.yml` использует `image: …:latest` | Reviewer P1: рекомендует pin версии (`:1.2.3` или digest) |
| Deploy-скрипт без `set -euo pipefail` | Reviewer P0 (fail-fast violation per Functional Clarity) |
| Контейнер запущен от root (нет `USER` в Dockerfile) | Reviewer P1: рекомендует non-root user, кроме обоснованных случаев (init-контейнер, привилегированные операции) |
| Сервис без healthcheck / restart policy | Reviewer P2: best-practice warning, не блокирует |
| Запрос на multi-host / Docker Swarm / k8s | Architect отвечает «вне scope v0.1, см. backlog v0.2» — не изобретает решение |
| Запрос на Terraform / Pulumi | Architect отвечает «вне scope v0.1, см. backlog v0.2» |
| Запрос на TDD (Terratest, container-structure-test) | Architect: «опционально в v0.1, не блокируем merge» |
| `sdlc` плагин не установлен | sdlc-infra работает автономно, в `README.md` плагина — упоминание cross-pipeline сценария |
| `functional-clarity` плагин не установлен | iac-implementer/reviewer degrade-ит до универсальных fail-fast принципов и упоминает их inline |
| Архитектор просит пользователя «выбрать swarm/k8s» | Запрещено: scope-overreach. Должен предложить только compose-варианты |

## Definition of Done

**Must Have:**

- [ ] Каталог `plugins/sdlc-infra/` создан с `.claude-plugin/plugin.json` (`version: 0.1.0`)
- [ ] Запись в `.claude-plugin/marketplace.json` (по образцу sdlc)
- [ ] 3 агента в `agents/`: `infra-architect.md` (opus, design-only), `iac-implementer.md` (sonnet, code-only), `infra-reviewer.md` (sonnet, review-only — без Write/Edit в `tools`)
- [ ] 3 skill с одноимённой структурой: `skills/infra-architect/SKILL.md`, `skills/iac-implementer/SKILL.md`, `skills/infra-reviewer/SKILL.md`
- [ ] `infra-architect/SKILL.md` покрывает: docker-compose service shape, Dockerfile patterns (multi-stage, USER, COPY-порядок), deploy-flow дизайн, secrets handoff via `.env`, backup/rollback план — БЕЗ КОДА (design-only angle)
- [ ] `iac-implementer/SKILL.md` покрывает: написание `Dockerfile` (с pinned base image, USER, multi-stage), `docker-compose.yml` (healthcheck, restart, networks, env_file), bash `deploy.sh` (с `set -euo pipefail`), `.env.example`, обновление `.gitignore`, GH Actions workflow как ssh-runner — пример скрипта в reference, не в SKILL.md
- [ ] `infra-reviewer/SKILL.md` покрывает чек-лист: `.env` не в репо, `set -euo pipefail`, hardcoded secrets, `:latest`-тег, `USER` not root, healthcheck/restart, opt-in инструменты `docker-compose config` и `shellcheck` с инструкцией активации
- [ ] `iac-implementer/SKILL.md` и `infra-reviewer/SKILL.md` явно ссылаются на `functional-clarity:functional-clarity` для shell-скриптов (fail-fast, no information loss) и degrade-логику если плагин отсутствует
- [ ] Все SKILL.md ≤ 500 строк; все references ≤ 170 строк; references на ≤ 1 уровень вложенности
- [ ] `infra-reviewer/SKILL.md` явно классифицирует findings: **P0** (блокирует merge), **P1** (must-fix-before-merge), **P2** (nice-to-have)
- [ ] `plugins/sdlc-infra/README.md` объясняет scope v0.1 (включая явный список нон-целей), связь с `sdlc`, инструкции по установке `/plugin install sdlc-infra@i-m-senior-developer`
- [ ] Корневой `README.md` обновлён: добавлен раздел `### [sdlc-infra](plugins/sdlc-infra/)` с описанием
- [ ] Cross-plugin namespacing соблюдён: упоминания всегда в форме `functional-clarity:functional-clarity`, `sdlc:*`, `tdd-master:tdd-master` (не bare-имена)

**Polish:**

- [ ] `infra-architect/SKILL.md` имеет section «When NOT to use this plugin» (k8s, multi-host, IaC, supply-chain compliance)
- [ ] Пример минимального `deploy.sh` в `iac-implementer/references/deploy-script.md` (30-50 строк, с fail-fast, без exotic-зависимостей)
- [ ] Пример минимального `docker-compose.yml` в `iac-implementer/references/dockerfile-patterns.md` или отдельный reference (с healthcheck, restart, networks, env_file)
- [ ] Migration note в `plugins/sdlc-infra/README.md`: «Если использовали ad-hoc deploy.sh, sdlc-infra:infra-reviewer найдёт fail-fast нарушения и hardcoded secrets»
- [ ] `infra-architect/SKILL.md` имеет section «Backup/rollback minimum» (что бэкапить, как откатывать compose-стек)

## Plugin Structure

```
plugins/sdlc-infra/
  .claude-plugin/
    plugin.json           # name=sdlc-infra, version=0.1.0
  agents/
    infra-architect.md    # model=opus,    color=blue,   tools=[Read, Grep, Glob, Write]
    iac-implementer.md    # model=sonnet,  color=purple, tools=[Read, Edit, Write, Grep, Glob, Bash]
    infra-reviewer.md     # model=sonnet,  color=red,    tools=[Read, Grep, Glob, Bash]   ← без Write/Edit
  skills/
    infra-architect/
      SKILL.md
      references/
        compose-design.md        # service shape, networks, volumes, healthcheck (design-angle)
        secrets-flow.md          # .env handoff, gitignore policy, deploy-time copy
    iac-implementer/
      SKILL.md
      references/
        dockerfile-patterns.md   # multi-stage, USER, COPY order, pinned base
        deploy-script.md         # минимальный deploy.sh + GH Actions ssh-runner
    infra-reviewer/
      SKILL.md
      references/
        compose-checks.md        # latest-тег, healthcheck, USER, secrets-в-compose
        deploy-script-checks.md  # set -euo pipefail, shellcheck, info-removal
  README.md                      # scope v0.1, миграция, связь с sdlc
```

## Cross-Plugin Integration

| Источник | Тип | Обязательна |
|----------|-----|-------------|
| `functional-clarity:functional-clarity` | reference (fail-fast в shell-скриптах, no information loss) | да (мягко: degrade на универсальные принципы, если не установлен) |
| `sdlc` (FEAT-0002) | соседний плагин, не зависимость | нет; sdlc-infra работает автономно |
| `tdd-master:tdd-master` | reference | нет (deployment в v0.1 без TDD) |
| `plugin-dev:*` (skill-reviewer, plugin-validator) | dev-time review | используется при создании плагина в этом монорепо, не runtime |

## Triggers for v0.2 (out of scope сейчас)

Поднимаем sdlc-infra v0.2 при появлении одного из:

- Реальная задача с Terraform/Pulumi-модулем в проекте, где установлен sdlc-infra
- Реальная задача с Kubernetes/Helm-чартом
- 3+ внешних запросов на multi-host или IaC
- Инцидент, где `.env`-в-репо обошёл reviewer-чек (значит чек надо поднять до scanner-уровня — добавить trivy/hadolint как обязательные)

## Visual Description

**Before:**
Разработчик закончил `/plan-do` для sdlc backend/frontend, но дальше — пустота. Вручную пишет Dockerfile, копипастит deploy.sh из StackOverflow, забывает `set -e`, оставляет `.env`-файл в репо, деплоит контейнер от root.

**After (v0.1):**
Разработчик прогоняет `sdlc-infra:infra-architect → sdlc-infra:iac-implementer → sdlc-infra:infra-reviewer`. Получает: `Dockerfile` с pinned base + USER + multi-stage; `docker-compose.yml` с healthcheck, restart, env_file; `deploy.sh` с `set -euo pipefail`; `.env.example` шаблон; обновлённый `.gitignore`. Reviewer ловит fail-fast нарушения и hardcoded secrets до merge.

**Interaction:**
- Активация: `Task` tool с `subagent_type=sdlc-infra:infra-architect`/`iac-implementer`/`infra-reviewer`, или прямое чтение skill через trigger-слова в `description` (docker-compose, deploy, ssh, Dockerfile)
- Skills загружаются on-demand (progressive disclosure), references открываются по угол-ключу

## Open Questions

Все ключевые вопросы из бэклог-черновика закрыты:

1. ~~TDD для infra (Terratest, container-structure-test)~~ → опционально в v0.1, не блокирующий gate
2. ~~Compliance scanners (tfsec/checkov/trivy/dockle/hadolint)~~ → вне scope v0.1; минимальный opt-in набор `docker-compose config` + `shellcheck`
3. ~~Multi-cloud (AWS/GCP/Azure)~~ → вне scope v0.1; single-host VPS only
4. ~~Variant A vs B~~ → выбран B (отдельный плагин `sdlc-infra`)
5. ~~Plugin name~~ → `sdlc-infra` (scope сужен в v0.1, имя оставлено forward-compatible под расширения)
6. ~~Topology~~ → single-host
7. ~~Secrets~~ → `.env` на хосте, gitignored

Открытых вопросов для v0.1 нет.

## Sources

- Реальный кейс пользователя (2026-04-27): простые SSH + docker-compose deployments — единственный driver на момент v0.1
- FEAT-0002 (`sdlc`) — паттерн «3 agents + 3 skills + references-by-angle», наследуется
- `functional-clarity` плагин — fail-fast принципы для shell-скриптов
- Уточняющий диалог в `/plan-feat` (2026-04-27) — закрыты варианты scope/topology/secrets/test-policy

---

**Ready for Technical Design:** Yes

**Next steps:**

- `/planner:plan features/FEAT-0003-sdlc-infra/README.md` — выпуск архитектурного плана
- `/planner:plan-do features/FEAT-0003-sdlc-infra` — оркестрация имплементации (architect → 3 параллельных implementers по skill-группам → reviewers + plugin-dev:skill-reviewer + plugin-validator → keeper)

**Technical Agent Instructions:**

При проектировании следовать паттернам FEAT-0002 (`sdlc`) plugin:
- YAML-frontmatter с `tools` как **array** (не comma-string — это P1 из FEAT-0001)
- Reviewer-агент: `tools` без Write/Edit (FPF A.7 — review-only роль)
- SKILL.md ≤ 500 строк, references ≤ 170 строк, ≤ 1 уровень вложенности
- Cross-plugin namespaces всегда полные: `functional-clarity:functional-clarity`, `sdlc:*`, `tdd-master:tdd-master`
- semver: первый релиз `0.1.0`, бамп при любом изменении (project CLAUDE.md mandate)
