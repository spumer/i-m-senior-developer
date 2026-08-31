# Functional Clarity Plugin

Помогает писать простой, надёжный и понятный код, а существующий менять без
лишнего риска. Этот файл отвечает на устройство плагина:
какие компоненты поставляются и где лежат. Договор — что даёт плагин, когда
включается, чего не делает — на странице
[`docs/plugins/functional-clarity.md`](../../docs/plugins/functional-clarity.md).

## Состав

- **Хук `SessionStart`** — `hooks/hooks.json` подключает
  `hooks/session-start.sh` с пределом ожидания 5 секунд. Скрипт печатает готовый
  текст выжимки; фильтр по источнику события не задан, поэтому выжимка попадает
  и в продолженную сессию, и в сессию после `/clear` или сжатия контекста.
- **Скилл `functional-clarity`** — `skills/functional-clarity/SKILL.md`, при нём
  восемь справочников: `00-principles.md` (перечень принципов),
  `01-style-guide.md` (стиль программирования), `02-code-change-discipline.md`
  (дисциплина изменения существующего кода с опорами FPF),
  `03-developer-levels.md` (грейды), `04-bash-instructions.md` (скрипты bash),
  `05-comment-style.md` (дисциплина комментариев), `06-boundary-vocabulary.md`
  (словарь границ контекста), `frameworks/python.md` (особенности Python).
- **Тест** — `skills/functional-clarity/test_boundary_vocabulary.py`: сверяет,
  что нужные строки про словарь границы есть в справочнике, в `SKILL.md` и в
  пяти файлах плагина `sdlc`, и что сама сверка сообщает о пропаже строки.
  Запуск из корня репозитория:

```bash
python3 -m unittest discover -s plugins/functional-clarity/skills/functional-clarity -p 'test_*.py'
```

Полное изложение принципов и стиля живёт в справочниках рядом со скиллом;
вторая копия здесь не держится.

## Установка

```bash
claude --plugin-dir plugins/functional-clarity
```

Или добавьте в настройки проекта/глобальные настройки Claude Code.

## Куда делся скилл интеграции FPF

Скилл `fpf-integration` (внедрение First Principles Framework в multi-agent
проекты) переехал в отдельный плагин `fpf-integration` этого же маркетплейса —
вместе со всей FPF-экосистемой (авторинг сводов `dpf-authoring`, резолвер
компетенций `dpf-apply`). Если он вам нужен — установите плагин
`fpf-integration`; этот плагин продолжает нести только принципы кода.
