# Clarity Language Plugin

Помогает сделать текст ясным и естественным — от технической документации до
художественной прозы. Этот файл отвечает на устройство
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

`mode` обязателен: без него, как и с пустым `files` в режиме `deep`, workflow
падает с ошибкой до первого вызова модели. Ещё принимаются `repo_root`,
`skill_path` (путь к `russian-style`; по умолчанию считается от рабочего каталога,
поэтому сходится только внутри этого репозитория), `lexicon_path` — вердикты
проекта по конкретным словам, они в оценке главнее общего списка в скилле, — и
`max_files` со значением 60.

## Установка

```bash
claude --plugin-dir plugins/clarity-language
```

Или добавьте в настройки проекта/глобальные настройки Claude Code.

## Происхождение

На **First Principles Framework** (FPF, `https://github.com/ailev/FPF`) опирается
один скилл из трёх: `clarity-validator` называет свою аксиому у каждого паттерна —
A.7 (Strict Distinction), A.10 (Evidence Graph), A.1.1 (BoundedContext),
A.11 (Ontological Parsimony), а также B.5 и F.0.1.

В `russian-style` и `ai-prose-detector` ссылок на FPF нет. Про `russian-style` сам
скилл говорит, что правила выведены из реальных правок рабочих текстов; про
происхождение методов `ai-prose-detector` в плагине не сказано ничего.
