# fpf-integration — экосистема First Principles Framework

Вся FPF-экосистема одним плагином: интеграция FPF в multi-agent проекты, авторинг
сводов принципов и резолвер-исполнитель пакетов компетенций.

## Что получаете при установке

- **Skill `fpf-integration`** — внедрение First Principles Framework (FPF) в
  multi-agent проекты: evidence-аудит решений, decay-механизм (DRR), проверка
  альтернатив (NQD), аксиомы A.7/A.10/A.11/A.1.1, навигация по спеке через
  готовые карты и grep-паттерны. Загружается на "integrate FPF", "FPF audit",
  "review decisions with FPF", "evidence graph review". Источник FPF:
  `https://github.com/ailev/FPF`.
- **Skill `dpf-authoring`** — авторинг сводов принципов (DPF/LPF): 6-фазный
  конвейер с файловым handoff, встроенные пакеты ролей (adversarial review,
  knowledge curation), канон метода и шаблоны внутри. Загружается на «создай
  DPF», «авторинг DPF», «переоцени пакет».
- **Skill `dpf-apply`** — резолвер и исполнитель пакетов компетенций:
  находит пакет по уровням project → user → plugin, проверяет свежесть, читает
  свод в контекст (ground) или спаунит агента по apply-промпту (apply).
  Загружается на «примени компетенцию», id вида `DPF-*` / `LPF-*`.

## Установка

Из маркетплейса `i-m-senior-developer` — как обычный плагин Claude Code.

## Migration notes — если раньше пользовались этими скиллами

Раньше `fpf-integration` жил внутри плагина `functional-clarity`, а
`dpf-authoring` и `framework-apply` — личными скиллами в `~/.claude/skills/`.
При переходе на плагин:

1. **Удалите личные копии.** Если в `~/.claude/skills/` остались каталоги
   `dpf-authoring` или `framework-apply` — личный уровень затеняет плагинный:
   обновления плагина не будут действовать, а вы не заметите. Сам плагин ничего
   не удаляет — шаг ручной:
   `rm -rf ~/.claude/skills/dpf-authoring ~/.claude/skills/framework-apply`.
2. **Проверьте старые абсолютные пути в проектах.** Ссылки вида
   `~/.claude/skills/dpf-authoring/…` в правилах и сводах проектов больше не
   работают. Известные точки: `rules/frameworks.md` проекта esb-tools, DPF-своды
   проектов со ссылками на скилл, ссылки в `.claude/workflows/`. Эти проекты
   правятся отдельно — плагин их не трогает.
3. **Слэш-команды сменили имена.** `/dpf-authoring` →
   `/fpf-integration:dpf-authoring`, `/dpf-apply` →
   `/fpf-integration:dpf-apply`, `/fpf-integration` →
   `/fpf-integration:fpf-integration`. Редиректов нет.
4. **Редакция FPF у dpf-authoring не менялась.** Пин `ailev/FPF@f7c7e93f`
   переехал как есть; обновление редакции — отдельная задача, не связанная с
   переездом.

## Совместимость

Плагин `functional-clarity` (принципы кода, style guide, Code-Change Discipline)
теперь не содержит FPF-скиллов и развивается независимо. Ставьте оба, если нужны
и принципы кода, и FPF-экосистема.
