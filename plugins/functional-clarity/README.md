# Functional Clarity Plugin

Помогает писать простой, надёжный и понятный код, а существующий менять без
лишнего риска. Этот файл отвечает на устройство плагина:
какие компоненты поставляются и где лежат. Договор — что даёт плагин, когда
включается, чего не делает — на странице
[`docs/plugins/functional-clarity.md`](../../docs/plugins/functional-clarity.md).

## Состав

- **Хук `SessionStart`** — `hooks/hooks.json` подключает
  `hooks/session-start.sh` с пределом ожидания 5 секунд. Скрипт печатает готовую
  выжимку принципов, затем добавляет правило из `hooks/comment-gate.txt` и
  подставляет в него путь к плагину. Текст проверяется через `iconv`: если файл
  недоступен, повреждён или утилиты нет, выжимка принципов остаётся, а правило
  пропускается целиком. Фильтр по источнику события не задан, поэтому текст
  попадает и в продолженную сессию, и в сессию после `/clear` или сжатия контекста.
- **Хук `SubagentStart`** — `hooks/subagent_comment_gate.py` передаёт то же
  правило каждому подагенту. Если Python или текст правила недоступен, запуск
  подагента продолжается без сообщения об ошибке.
- **Скилл `functional-clarity`** — `skills/functional-clarity/SKILL.md`, при нём
  семь справочников: `00-principles.md` (перечень принципов),
  `01-style-guide.md` (стиль программирования), `02-code-change-discipline.md`
  (дисциплина изменения существующего кода с опорами FPF),
  `03-developer-levels.md` (грейды), `04-bash-instructions.md` (скрипты bash),
  `06-boundary-vocabulary.md` (словарь границ контекста),
  `frameworks/python.md` (особенности Python).
- **Скилл `comment-style`** — `skills/comment-style/SKILL.md`: правило
  комментариев «объясняй почему, а не что», проверка холодным чтением,
  допустимые комментарии и пограничные случаи.
- **Тесты** — `skills/functional-clarity/test_boundary_vocabulary.py` проверяет
  связность правила словаря границы, а `hooks/test_subagent_comment_gate.py` —
  выход хука `SubagentStart`, сохранение Unicode при ASCII-кодировке stdout и
  поведение при недоступном тексте. `hooks/test_session_comment_gate.py`
  проверяет доставку корректного UTF-8 и пропуск повреждённого файла в
  `SessionStart`. Запуск из корня репозитория:

```bash
python3 -m unittest discover -s plugins/functional-clarity/skills/functional-clarity -p 'test_*.py'
python3 plugins/functional-clarity/hooks/test_subagent_comment_gate.py
python3 plugins/functional-clarity/hooks/test_session_comment_gate.py
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
