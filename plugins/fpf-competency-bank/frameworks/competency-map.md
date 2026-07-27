# Карта компетенций — fpf-competency-bank

Плоская таблица сводов, которые несёт этот банк. Резолвер `dpf-apply` (`resolve.py`) находит банк через строку в `~/.claude/frameworks.paths` (см. README) и читает эту карту вместе с `DPF.md` каждого пакета.

| id | path | kind | status | edition | modes | cues | depends_on | maturity_level |
|----|------|------|--------|---------|-------|------|------------|-----------------|
| `DPF-COUPLING-GENERALIZATION` | `DPF-COUPLING-GENERALIZATION/` | Domain Principle Framework | active | 2026-07-13 | knowledge | обобщать; обобщение; дублирующийся код; дублирование; связность; coupling; генерализация | — | L1 |
| `LPF-SIMPLIFICATION-REVIEW` | `LPF-SIMPLIFICATION-REVIEW/` | Local Practice Framework | active | 2026-07-14 | executable | упрощение; стадия упрощение; ревью диффа; simplification; обобщить дифф | `DPF-COUPLING-GENERALIZATION@2026-07-13` | L2 |

Колонка `cues` — тот же список, который читает хук `UserPromptSubmit` для подсказок (разделитель `;`, word-boundary, без учёта регистра). Колонки-ссылки на источник вердикта критика в карте нет и не будет: авторитетный источник статуса `admissible` — финальная conformance-строка `DPF.md` каждого пакета (проверяет `resolve.py --verify --scope bank`), не эта карта и не `references/`.

Колонка `maturity_level` (значение строго `Lx`) — профиль зрелости над полом допуска (источник истины: `references/package-adequacy-<date>.md`, раздел «Профиль зрелости»); ≠ frontmatter-ключ `maturity` в `DPF.md` (там edition-state, напр. `conformant`).

## LPF-SIMPLIFICATION-REVIEW — не доменный, это образец класса

`LPF-SIMPLIFICATION-REVIEW` локален к пайплайну «Упрощение» конвейера esb-tools 4.0: его `declaredDomainOrLocalContext` и `intendedReaderOrOperator` заявлены на этот конкретный пайплайн, а не на домен в целом. В банке он лежит как **образец класса LPF** — показывает, как из доменного DPF получается специализированная локальная практика с исполняемым `assets/apply-prompt.md`.

Для другого проекта его нельзя применять как есть — только форкать и адаптировать: скопировать пакет, переписать `declaredDomainOrLocalContext`/`intendedReaderOrOperator` под свой пайплайн и прогнать свежий adversarial-критик-прогон (`dpf-authoring`, роль `DPF-ADVERSARIAL-REVIEW`) под новым `declaredUse`. Унаследованный вердикт `admissibleForDeclaredDPFUse` из этой копии на новый контекст не переносится.

`DPF-COUPLING-GENERALIZATION`, напротив, доменный: `intendedReader` — любой в домене, применим напрямую без форка.
