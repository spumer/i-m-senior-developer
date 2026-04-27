# FEAT-0001 — Plugin `planner`

> **Статус:** Ready for Architecture
> **Marketplace:** `i-m-senior-developer`
> **Категория:** development / meta
> **Связь:** часть P0+P1 фикса fail-mode «оркестратор делает работу сам при agent-gap'е» (см. memory `feedback_orchestrator_no_diy_on_agent_gap`)

## Problem Statement

Текущий `planner` живёт как один subagent (`~/.claude/agents/planner.md` + проектный override). Это даёт три структурных пробела:

1. **Нет петли обратной связи.** План пишется до работы, но никто не сверяет его с фактом по итогу. `planner-context.md` обновляется только вручную и только когда кто-то вспомнит. Gap'ы в каталоге агентов не выявляются автоматически.
2. **Bootstrap-логика смешана с режимами планирования.** В одном `.md`-файле — и сканирование агентов/команд/skills (одноразовое), и архитектурное/исполнительное планирование (постоянное). Раздутый context, плохое разделение ответственности.
3. **Не видны ошибки прошлого.** Если оркестратор выбрал слабую модель и переделывал работу — это нигде не фиксируется. Если пользователь явно указал «эта структура была неправильной» — урок теряется. В следующий раз планнер совершит ту же ошибку.

Эти три пробела регулярно приводят к одному и тому же сбою: `/plan-do` для frontend-фичи начинается, gap (нет frontend-агента) не отмечен в §1, оркестратор «творчески подбирает» (нелепо) или сваливается в DIY-режим. Лазейка нашлась дважды за одну сессию (FEAT-0014 + правки этого плагина).

## User Journey

**Starting Point:** разработчик в проекте N, в репозитории корень с `frontend/` и `backend/`. Установлен плагин `planner` из marketplace `i-m-senior-developer`.

**Step-by-Step Flow:**

1. **Первый запуск (`/plan` или автоматически из `/plan-do`):**
   - Плагин обнаруживает отсутствие `<project>/.claude/planner-context.md`.
   - Запускает skill `planner-bootstrap`: сканирует `.claude/agents/`, `~/.claude/agents/`, slash-команды, skills, plugin-MCP инструменты.
   - **Gap-detection (новое):** детектирует стэк проекта по файлам — `package.json` → frontend (React/Vue/...), `pyproject.toml`/`requirements.txt` → Python, `go.mod` → Go, `Dockerfile`+`docker-compose.yml` → infra, `android/`/`ios/` → mobile, и т.д. Сравнивает обнаруженные стеки с описаниями агентов из §1. Дыры помечает как `❌ GAP — fallback: general-purpose`.
   - Записывает `planner-context.md` (формат см. ниже).
   - Возвращает оркестратору: «bootstrap done, ready to plan».

2. **Architecture planning mode:** на вход приходит README фичи. Планнер читает фичу, оценивает размер/тип/стек/критичность, предлагает: одного архитектора, N параллельных, или quick-pass. Выходной файл — `<feature-dir>/PLANNER_OUTPUT.md`.

3. **Execution planning mode:** на вход приходит готовый ARCHITECTURE.md. Планнер строит dependency graph стейджей, группирует независимые в параллельные фазы (≤7), подбирает модель по таблице §4. Выход — обновлённый `PLANNER_OUTPUT.md`.

4. **Команда `/plan-reflect` (новое, post-task):**
   - Запускается явно пользователем после завершения работы (либо вручную, либо как часть `/end-session` в проектах где это завязано).
   - Читает: `PLANNER_OUTPUT.md` (что планировалось), фактические артефакты сессии (commits, новые файлы, review-файлы), доступные транскрипты агентов через TaskGet/TaskOutput.
   - Анализирует:
     - **Какие агенты вызывались по факту?** Если оркестратор использовал `general-purpose` там, где «должен был» быть dedicated → пометить `gap` в §1.
     - **Пришлось ли переделывать работу?** Если у агента в транскрипте видны итерации «test failed → retry → still failed → escalate» — это сигнал слабой модели. Зафиксировать в §4 (моделях): «для задач X модель Y оказалась слабой, рекомендуется Z».
     - **Явные ошибки от пользователя:** если в сессии есть сообщения «не делай сам», «это неправильно», «переделай» — извлечь паттерн ошибки и записать в §6 (соглашения) как «избегать в будущем».
     - **Cost actual vs estimated:** сверить плановые токены/время с фактом, скорректировать §4.
   - Записывает результат в `planner-context.md` с пометкой `<!-- learned <ISO-date> from FEAT-XXXX -->`.
   - Опционально создаёт feedback-memory в auto-memory пользователя для критичных уроков.

**End State:**
- `planner-context.md` отражает реальное состояние проекта и его команды агентов.
- Gap'ы в каталоге явно видны.
- Cost estimates калиброваны фактом.
- Ошибки прошлого зафиксированы как guard-rails.
- Следующая сессия начинается из улучшенного контекста.

## Edge Cases & Behaviors

| Сценарий | Ожидаемое поведение |
|----------|---------------------|
| Bootstrap в проекте без `.claude/agents/` | Записать пустой каталог §1 с пометкой `TODO: fill manually` или предложить fallback `general-purpose` для всех ролей. |
| Gap-detection не нашёл известных стеков (нестандартный проект) | Записать обнаруженные «маркеры» в §8 (новая секция), пометить `unknown stack` и попросить пользователя описать вручную. |
| Существует ручная правка в `planner-context.md` | НЕ перезаписывать. Только дополнять новыми авто-строками с меткой `<!-- auto-added YYYY-MM-DD -->`. |
| Bootstrap вызван повторно | Сравнить найденное с записанным. Если есть новые агенты/skills — добавить с меткой `<!-- auto-added ... -->`. Если что-то исчезло — пометить `<!-- stale, last seen ... -->`, но не удалять. |
| `/plan-reflect` без `PLANNER_OUTPUT.md` (планнер не запускался) | Сообщить «нечего рефлексировать, сначала запусти /plan». Не падать. |
| `/plan-reflect` не имеет доступа к транскриптам агентов | Деградировать на анализ git-diff и review-файлов; явно отметить «transcript-based learnings unavailable». |
| Архитектурный план уже есть, но `PLANNER_OUTPUT.md` не существует | Это execution mode без architecture-фазы планнера. Не падать, прочитать ARCH-план как input. |
| Плагин установлен, но в `~/.claude/agents/planner.md` лежит старый файл | На первом запуске показать предупреждение: «обнаружен legacy planner.md, удали его — плагин теперь источник правды». README плагина содержит чёткую migration-инструкцию. |
| Конфликт имени `/plan` с другой командой пользователя | Плагин занимает `/plan`. Если у пользователя своя `/plan` — Claude Code разрулит по приоритету; в README плагина указать что плагинная команда имеет префикс `planner:plan` как fallback. |
| `/plan-reflect` нашёл ошибку «слабая модель» | Не обвинять модель в §4 категорически. Записать как «для задач типа X на этом проекте Sonnet оказался слабым → попробовать Opus», с привязкой к фиче (FEAT-XXXX). |
| Транскрипт агента содержит секреты/PII | НЕ записывать сырые куски. Извлекать только обобщённые паттерны: «3 итерации до зелёных тестов», без содержимого. |

## Definition of Done

**Must Have:**
- [ ] `plugins/planner/.claude-plugin/plugin.json` (name, version 0.1.0, description, author, keywords).
- [ ] `plugins/planner/agents/planner.md` — тонкий agent-wrapper, активирует skill `planner`. Frontmatter: name, description, model=sonnet, tools=[Read, Grep, Glob, Write].
- [ ] `plugins/planner/skills/planner/SKILL.md` — общее ядро: два режима (architecture / execution), формат output, метод анализа задачи. Без bootstrap-логики и без reflect-логики.
- [ ] `plugins/planner/skills/planner/references/bootstrap.md` — детальный алгоритм сканирования + gap-detection (heuristics по файлам стеков).
- [ ] `plugins/planner/skills/planner/references/architecture-mode.md` — детали Режима 1.
- [ ] `plugins/planner/skills/planner/references/execution-mode.md` — детали Режима 2.
- [ ] `plugins/planner/skills/planner/references/template-context.md` — шаблон `planner-context.md` (8 секций).
- [ ] `plugins/planner/skills/planner-reflect/SKILL.md` — пост-задачная рефлексия (4 типа обновлений).
- [ ] `plugins/planner/commands/plan.md` — слаш-команда вызова planner.
- [ ] `plugins/planner/commands/plan-reflect.md` — слаш-команда рефлексии.
- [ ] `plugins/planner/README.md` — что делает плагин, как установить, **migration guide со старого `~/.claude/agents/planner.md`** (явные команды на удаление + проверка).
- [ ] Запись плагина добавлена в `i-m-senior-developer/.claude-plugin/marketplace.json`.
- [ ] Bump version бамп при последующих правках (CLAUDE.md правило).

**Polish:**
- [ ] Список стеков для gap-detection — расширяемый: 6+ базовых (backend-python, backend-node, frontend, mobile-android, mobile-ios, infra) + heuristics-таблица «сигнал → стек».
- [ ] Skill `planner-reflect` явно указывает 5 источников evidence для анализа: PLANNER_OUTPUT, git-log, review-файлы, transcripts (через TaskGet/TaskOutput), user-messages.
- [ ] В output `planner-reflect` всегда есть отдельная секция «Lessons learned» — даже если она пустая (force-функция «подумать о провалах»).
- [ ] Все скиллы плагина используют progressive disclosure (короткий SKILL.md + references/) — чтобы не раздувать context активацией.

## Plugin Structure

```
plugins/planner/
  .claude-plugin/
    plugin.json
  agents/
    planner.md                          # тонкий wrapper (~30 строк)
  skills/
    planner/
      SKILL.md                          # ядро (~200 строк)
      references/
        bootstrap.md                    # +gap-detection
        architecture-mode.md
        execution-mode.md
        template-context.md             # шаблон planner-context.md
    planner-reflect/
      SKILL.md                          # post-task рефлексия (~150 строк)
  commands/
    plan.md
    plan-reflect.md
  README.md                             # description + install + migration guide
  hooks/                                # пока пусто, оставить на потом
```

## Visual Description

**Before (status quo):**
- `~/.claude/agents/planner.md` (450 строк, всё в одном).
- `<project>/.claude/agents/planner.md` (override, дублирует).
- `<project>/.claude/planner-context.md` (обновляется вручную, дрейфует).
- `/plan-reflect` не существует. Уроки сессий не фиксируются.

**After:**
- Plugin `planner` в marketplace, устанавливается одной командой.
- Skill `planner` (ядро) активируется автоматически по триггерам "план", "разбей задачу", "оптимизируй процесс", или явно через `/plan`.
- Skill `planner-reflect` активируется по `/plan-reflect` или из `/end-session`.
- `planner-context.md` живёт в проекте, обновляется планнером (auto-added) и пользователем (manual). Конфликта правил нет — auto-added строки не трогают ручные.
- Gap'ы в §1 явно видны как `❌ GAP — fallback: general-purpose`.
- Каждая сессия с `/plan-reflect` → +N строк уроков в §6/§7.

## Migration Guide (для README плагина)

```bash
# 1. Установить плагин из marketplace
# (после публикации — claude plugin install i-m-senior-developer/planner)

# 2. Удалить legacy planner.md
rm -f ~/.claude/agents/planner.md
rm -f <project>/.claude/agents/planner.md  # если есть

# 3. Проверить, что planner-context.md проекта не сломан
# (плагин при первом запуске сам предложит обновить структуру до новой)

# 4. Запустить /plan на любой фиче — bootstrap должен пройти чисто
```

## Open Questions

1. **Транскрипты агентов:** доступны ли `TaskGet`/`TaskOutput` после завершения сессии (cross-session) или только в текущей? Если только в текущей — `/plan-reflect` обязан быть в той же сессии что и работа. Это нужно проверить опытом и зафиксировать в Edge Cases.
2. **Hook-интеграция с `/end-session`:** в Контракции есть свой `/end-session`, но в плагин-marketplace мы не контролируем. Решение: плагин предлагает hook через `hooks/session-end.sh`, пользователь сам решает подключать или нет. Hook просто запускает `/plan-reflect` если в сессии было `/plan-do`.
3. **Plugin namespace для команд:** `/plan` или `planner:plan`? Claude Code-конвенции по namespacing уточнить через context7.

---

**Ready for Technical Design:** Yes
**Next:** `/plan-do features/FEAT-0001-planner-plugin/README.md` (после подтверждения README) — но сначала нужно решить, как закрыть FEAT-0001 без самого планнера. Предложение: использовать `general-purpose` с явным mandate для architect-фазы, потом `general-purpose` для implementer, потом `code-reviewer` (он уже есть в каталоге).
