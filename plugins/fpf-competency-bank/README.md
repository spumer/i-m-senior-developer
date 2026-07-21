# fpf-competency-bank

Эталонный банк компетенций FPF — distributable-набор проверенных сводов (DPF/LPF), которые резолвер `dpf-apply` находит и подтягивает наравне с проектными и пользовательскими сводами. Плагин несёт только данные (`frameworks/`) — резолвер, гейт свежести и журнал worked-evidence живут в `fpf-integration`.

## Что внутри

| id | kind | modes | назначение |
|----|------|-------|-----------|
| `DPF-COUPLING-GENERALIZATION` | Domain Principle Framework | knowledge | когда более крупная правка сокращает связи между объектами — доменный свод, применим в любом проекте |
| `LPF-SIMPLIFICATION-REVIEW` | Local Practice Framework | executable | ревью-обобщение диффов на стадии «Упрощение» — образец класса LPF, см. ниже |

Полная карта с cue-словами для UserPromptSubmit-хука — `frameworks/competency-map.md`.

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

## LPF-SIMPLIFICATION-REVIEW — образец класса, не готовый к использованию как есть

`LPF-SIMPLIFICATION-REVIEW` унаследовал вердикт критика `admissibleForDeclaredDPFUse` из исходного проекта esb-tools — но этот вердикт скоуплен на **declaredUse исходного пакета**: `intendedReaderOrOperator` = reviewer стадии «Упрощение» конвейера esb-tools 4.0. Пакет **локален** к этому пайплайну, не доменный.

Помещая его в банк, мы не переобъявляем его use и не выдаём за доменно-переиспользуемый. Практическое следствие:

- **Читать и изучать** пакет в другом проекте можно свободно — это образец того, как из доменного DPF получается специализированная executable-практика.
- **Применять как есть** в чужом пайплайне нельзя — нужно **форкнуть и адаптировать**: скопировать пакет, переписать `declaredDomainOrLocalContext`/`intendedReaderOrOperator` под свой процесс, прогнать свежий adversarial-критик-прогон (`dpf-authoring`, роль `DPF-ADVERSARIAL-REVIEW`) под новым declaredUse. Унаследованный вердикт на новый контекст не переносится автоматически.

`DPF-COUPLING-GENERALIZATION`, в отличие от LPF, доменный — его `intendedReader` не привязан к конкретному проекту, применим напрямую.

## Вход в банк

Критерии допуска пакета в этот банк (различение DPF/LPF, fail-closed гейт) — `CONTRIBUTING.md`.
