# fpf-competency-bank

Эталонный банк компетенций FPF: distributable-набор проверенных сводов (DPF/LPF),
которые резолвер `dpf-apply` находит и подтягивает наравне с проектными и
пользовательскими сводами. Этот файл отвечает на устройство плагина в
репозитории; договор — что даёт банк, границы применения сводов, допуск — на
странице [`docs/plugins/fpf-competency-bank.md`](../../docs/plugins/fpf-competency-bank.md).

Плагин несёт только данные (`frameworks/`) — резолвер, гейт свежести и журнал
worked-evidence живут в `fpf-integration`. Что значат «свод», «компетенция»,
DPF, LPF, ground/apply, затенение и протухание — словарь в README плагина
`fpf-integration`, раздел «Словарь». Здесь термины не пересказываются.

## Что внутри

| id | kind | modes | назначение |
|----|------|-------|-----------|
| `DPF-COUPLING-GENERALIZATION` | Domain Principle Framework | knowledge | когда более крупная правка сокращает связи между объектами — доменный свод, применим в любом проекте |
| `LPF-SIMPLIFICATION-REVIEW` | Local Practice Framework | executable | ревью-обобщение диффов на стадии «Упрощение» — образец класса LPF; ограничения применения — на странице договора |

Полная карта с cue-словами для UserPromptSubmit-хука — `frameworks/competency-map.md`.
Критерии допуска пакета в банк (различение DPF/LPF, fail-closed гейт) —
`CONTRIBUTING.md` рядом с этим файлом.

## Подключение

Резолвер `dpf-apply` ищет банки на трёх уровнях: project (`$PWD/.claude/frameworks`) → user (`~/.claude/frameworks`) → plugin (пути из `~/.claude/frameworks.paths`). Чтобы подключить этот банк, допиши в `~/.claude/frameworks.paths` одну строку — абсолютный путь до каталога `frameworks` внутри этого плагина:

```
/абс/путь/до/plugins/fpf-competency-bank/frameworks
```

`resolve.py` разворачивает `~` в каждой строке файла и ищет `<путь>/<ID>/DPF.md`. Правка вручную, автоматической записи в `frameworks.paths` при установке плагина в v1 нет — это сознательное ограничение первой версии, не баг.

После подключения проверить, что банк виден:

```
python3 ~/.claude/plugins/.../fpf-integration/skills/dpf-apply/scripts/resolve.py --list
```
