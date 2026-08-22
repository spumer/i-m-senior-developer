# Clarity Language Plugin

Три скилла против AI-синтетики в текстах. Этот файл отвечает на устройство
плагина в репозитории: какие компоненты поставляются и где лежат. Договор — что
ловит каждый скилл, как вызывать разбор калек, границы — на странице
[`docs/plugins/clarity-language.md`](../../docs/plugins/clarity-language.md).

## Что внутри

```text
plugins/clarity-language/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   ├── hooks.json               # SessionStart: правило времени записи
│   └── session-start.sh
├── skills/
│   ├── clarity-validator/       # смысловые AI-паттерны в технических документах
│   │   ├── SKILL.md
│   │   └── references/
│   ├── ai-prose-detector/       # стилистические AI-паттерны в художественной прозе
│   │   ├── SKILL.md
│   │   └── references/
│   └── russian-style/           # естественность русской фразы
│       └── SKILL.md
└── workflows/
    └── calque-sweep.js          # сплошной разбор текстов на кальки
```

## Вызов разбора калек

```text
Workflow({name: "clarity-language:calque-sweep", args: {
  mode: "deep",
  files: ["docs/что-правили.md"],
  report_path: ".claude/calque-sweep-report.md"
}})
```

## Установка

```bash
claude --plugin-dir plugins/clarity-language
```

Или добавьте в настройки проекта/глобальные настройки Claude Code.

## Происхождение

Скиллы основаны на **First Principles Framework** (FPF, `https://github.com/ailev/FPF`):
аксиомы A.7 (Strict Distinction), A.10 (Evidence Graph), A.1.1 (BoundedContext),
A.11 (Ontological Parsimony). Правила `russian-style` выведены из реальных правок
рабочих текстов.
