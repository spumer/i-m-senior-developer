---
dpf_id: "DPF-AUTHORING"
name: "Метод авторинга DPF (research-first)"
kind: "Local Practice Framework"
owner: ["keeper"]
referenced_by: ["facilitator", "architect", "cto", "dev", "test", "guardian", "product", "analyst", "customer"]
status: "stage-0"
grounded_in: ["FPF E.4.DPF", "FPF E.4.DPF.DA", "FPF G.2", "FPF E.4.PFR", "FPF E.4.PFAD", "FPF E.8", "FPF E.19", "FPF A.2.6 USM", "FPF B.5.2.1 NQD", "FPF A.10", "FPF A.1.1", "FPF A.11", "FPF A.7"]
fpf_edition: "ailev/FPF@f7c7e93f (снимок 2026-07-03; локальная копия ~/.claude/knowledge/fpf/FPF-Spec.md обновлена 2026-07-06)"
date: "2026-06-29"
updated: "2026-07-06"
review_due: "2026-09-29"
---

# DPF-AUTHORING: Метод авторинга DPF (research-first)

> **Этот файл — канон метода**, публикуется в составе самодостаточного скилла `dpf-authoring`. Для прогонов ничего вне скилла не нужно.
> **Авторская комната метода** (исследование, происхождение источников, записи качества; далее «комната»): каталог `DPF-AUTHORING/` библиотеки сводов в репозитории `aifirst` владельца метода — для прогонов не нужна.
>
> Мета-DPF: полный алгоритм построения DPF = **FPF E.4.DPF** (11-шаговый spine) × **G.2** (SoTA harvest) × наши дополнения.
> Owner — keeper. Provenance — `<комната>/references/source-pack.md`.
>
> **FPF читать живьём, не выжимки** (иначе дрейф понимания/архитектуры — G.11/DRR). Разделы даны по ID; поиск и чтение живых блоков — через скилл **`fpf-integration`** (его индекс fpf-sections-map / grep-patterns / tasks-lookup + Grep по FPF-Spec; версия — `~/.claude/knowledge/fpf/FPF-Spec.version`).
>
> **Используемые разделы FPF:** `E.4.DPF` (spine, CC-DPF.1–9, anti-patterns) · `E.4.DPF.DA` (адекватность ПАКЕТА: координаты D1–D11 + подпроход PFM1–PFM11 + статусы) · `E.4.PFAD` (арх-решение фреймворка) · `E.4.PFR` (связи/edition, в т.ч. access-carrier) · `G.2` (SoTA harvest) · `E.8` (форма паттерна) · `E.19` (admission-гейты, только когда заявлены) · `A.2.6` USM (scope) · `B.5.2.1` (NQD) · `A.10` (evidence) · `A.1.1` (bounded context) · `A.11` (parsimony / sharp boundary) · `A.7` (strict distinction) · `F.18` (имена) · `E.21/E.22/E.23` (quality) · `G.11` (refresh).
>
> **Структурный отчёт этого носителя (CC-DPF.8 / PFM11):** файл для роли, которая строит или пересматривает DPF; **первая задача читателя** — пройти 6-фазный алгоритм (§4) для конкретной компетенции, не читать метод целиком линейно; на переднем плане — сам алгоритм, гейты и 2 паттерна (§7); сознательно огрублено/опущено: полные формулировки FPF (читать живьём по ID), содержимое конкретных DPF, ход и телеметрия прошлых прогонов метода; возврат к источникам — `<комната>/references/` (source-pack, sota-research, theses-antitheses, quality-record) и живая спека.

## Оглавление (PFM1 — паттерны и типовые ошибки первым делом)
1. **Паттерны метода** (§7) — Research-first гейт · Принцип → инстанциация.
2. **Типовые ошибки авторинга** — чего избегать (новичковые + AI-специфичные).
3. Алгоритм — 6 фаз (§4) · Канонический скелет DPF.md (§5) · обогащённый блок паттерна (§6).
4. Разнородные приёмочные случаи — где спайн реально проверен, где `worked-evidence pending`.
5. Контекст / Source pack / Forces (§1–3).
6. Quality & refresh, Access carrier, Conformance (§8, конец файла).

## 1. Контекст (CC-DPF.1)
- **Bounded context:** система знаний `aifirst`. Каждая компетенция роли = один DPF.
- **Intended reader:** роль, создающая/обновляющая DPF; keeper — хранитель метода.
- **First use:** построить новый DPF по 6-фазному пайплайну (ниже).
- **Non-use boundary:** НЕ продуктовая документация sqproxy; НЕ факты (→domain.md); НЕ решения (→decisions/).

## 2. Source pack — G.2 (CC-DPF.2)
> Реестр provenance — `<комната>/references/source-pack.md`. Собственный SoTA-харвест метода (домен «авторинг pattern/principle-фреймворков», ≥3 независимо верифицированные традиции, репарация D11) — `<комната>/references/sota-research.md`; bridge/тезисы-антитезисы — `<комната>/references/theses-antitheses.md`.
- **Adopted:** E.4.DPF spine + CC-DPF.1–9; E.4.DPF.DA (координаты D1–D11, PFM-подпроход, статусы пакета, пол 4 для опорного использования); G.2 SoTA-pack (CorpusLedger/ClaimSheets/BridgeMatrix/MicroExamples, FamilyCoverageFloorK=3); E.4.PFR (связи, access-carrier); A.2.6 USM (scope); B.5.2.1 (NQD анти-тезисы); A.7/A.10/A.11; DSL co-evolution (Zhang), SPLE (Nazar), pattern-language практика (Riehle/Iba), архитектурные описания (ISO 42010), AI-в-паттернах (Corneli) — независимо от FPF-цитирования, см. `sota-research.md`.
- **Rejected:** авторинг DPF.md до research (даёт «checklist promoted to framework», E.4.DPF:8); голые частности без принципа (A.1.1 leak); опора только на секции самого FPF без независимого SoTA-харвеста (authority-by-citation, CC-DPFDA.5 — было дефицитом D11 до этой правки).

## 3. Forces / тензии авторинга (E.4.DPF:3, G.2:3)
- Плюрализм vs консолидация (no silent fusion).
- Срочность vs онтология (преждевременные имена/паттерны замораживают плохую модель).
- Стоимость ресёрча vs богатство DPF — **разрешается research-first гейтом** (дёшево пропустить → дорого получить бедный DPF).
- Общий принцип vs наша частность (учим дисциплине, заземляем на наш кейс — но принцип первичен).

## 4. Алгоритм построения DPF — ядро (6 фаз)

> Каждая фаза = inspectable-артефакт (A.10). **Ни одна не пропускается.** Роли фаз — встроенные в скилл пакеты компетенций (`../frameworks/<ID>/`: DPF.md + apply-prompt.md; формат framework-apply), не роли проекта: ресёрч — универсальный агент; **адверсарная функция** (анти-тезисы/контрпримеры/критика, devil's advocate против «AI-consensus = evidence») — пакет `DPF-ADVERSARIAL-REVIEW`; **кураторская функция** (провенанс, формат, сборка) — пакет `DPF-KNOWLEDGE-CURATION`. Фазы 1–2 можно вести параллельными агентами.

### Фаза 0 — Scope (E.4.DPF:1)
Назвать: компетенцию, bounded context, intended reader, first use, non-use boundary; owner + critic.
**Gate:** scope-нота существует.

### Фаза 1 — SoTA Harvest (G.2) → `references/sota-research.md`
Из pretrain + web, **с обязательным фокусом на ИИ-использование в этой области** (инструменты, как ИИ меняет навык, AI-specific failure modes).
- **CorpusLedger** (G.2a): источники + триаж include/park/retire + обоснование.
- **ClaimSheets** (G.2b): claim'ы с bounded context, evidence-anchor (источник+дата, A.10), freshness/decay, trust-cue.
- **MicroExamples** (G.2e): worked-примеры несущих claim'ов (общие, SoTA — не наш код).
**Gate:** ≥3 традиции (FamilyCoverageFloorK=3); каждый claim с источником+датой.

### Фаза 2 — Bridge / тезисы-антитезисы (G.2d + E.4.DPF:3 + A.2.6 + E.4.PFR + B.5.2.1) → `references/theses-antitheses.md`
- **BridgeMatrix**: alignment/divergence по традициям, **явные потери и scope строк** (no silent fusion).
- Каждый тезис: **scope валидности** (A.2.6 USM) + анти-тезис (NQD ≥3) + тип связи (composition / conflict / scope-dependent, E.4.PFR).
- **Контрпримеры** (похоже-но-не-применять, граница scope; A.11 Sharp Boundary).
- **Каталог типовых ошибок** компетенции (failure modes из ClaimSheets + ИИ-специфика; E.4.DPF:8).
**Gate:** каждый тезис со scope; конфликты не слиты молча.

### Фаза 3 — Source-pack решение (G.2 триаж → adoption) → `references/source-pack.md`
По каждому источнику: adopted / rejected + причина / claim-status / currentness.
**Gate:** provenance полон.

### Фаза 4 — Архитектурное решение DPF (E.4.DPF:3 PFAD/E.9) — в DPF.md
Purpose, pattern split, dependency boundary, must-NOT-land; имена (F.18 → glossary).

### Фаза 5 — Сборка DPF.md (E.4.DPF spine 4–7, E.8) — по канон-скелету (ниже)
Правило: **общий принцип (SoTA) → наша инстанциация (worked slice)**. Голых частностей нет.

### Фаза 6 — Quality, critic, refresh (E.4.DPF.DA/E.22/E.21/E.23/E.19, G.11; CC-DPF.1–9)
- **Completeness-critic** (guardian): «какая традиция SoTA упущена? какая тензия не покрыта? какой claim без источника?»
- **Оценка пакета по E.4.DPF.DA** (не только чек-лист секций): таблица 11 координат D1–D11, каждая строка = значение 0–5 + краткое обоснование + evidence-locus + repair-предложение. Перед выставлением значений — подпроход PFM1–PFM11 (форма пакета: порядок входа, примат паттернов, направление зависимостей, отсутствие процессного состояния в носителе, structure-account…). Средним баллом E.21 по паттернам подменять НЕЛЬЗЯ (CC-DPFDA.4).
- **Статус пакета** (честный, CC-DPFDA.8): `admissibleForDeclaredDPFUse` (все координаты ≥ пола; пол = 4 для опоры ролей) / `seedOnly` (полезен как заготовка, опираться нельзя) / `repairBeforeDPFUse` (+ наименьшие repair-шаги) / `refreshNeeded`. Заготовка не повышается до опорного пакета без evidence.
- refresh-триггеры + review_due.
**Gate:** CC-DPF.1–9 пройдены И статус пакета = `admissibleForDeclaredDPFUse`; иначе gate_passed=false + список наименьших repair-шагов.

> **Research-first гейт (ключевой):** запрещено писать `DPF.md` (Фаза 5), пока нет `sota-research.md` + `theses-antitheses.md`.
> **First-hour-route** допустим ВНУТРИ каждого артефакта (грубо, но inspectable), но фазы пропускать нельзя.
> **Carriers** (web/LLM-выдача) допускаются как evidence через admission C.33/C.34/C.35 (CC-DPF.5).

## 5. Канонический скелет DPF.md
0. **Структурный отчёт носителя** (CC-DPF.8, короткий абзац в шапке): для кого файл, что на переднем плане, что сознательно огрублено/опущено, куда возврат за деталями · 1. Контекст (E.4.DPF:1) · 2. Source pack → sota-research + source-pack (G.2) · 3. **Forces/тензии** (E.4.DPF:3, scoped) · 4. **Паттерны** (E.8, блок ниже; паттерны — главный язык носителя, тяжёлые карты — после них или в references, PFM2) · 5. **Связи паттернов** (E.4.PFR: compose/require/conflict/sequence) · 6. **Типовые ошибки** (E.4.DPF:8: симптом→почему→исправление, с источником; «типовые» = и новичковые, И ошибки опытных из устаревшей/локальной практики) · 7. **SoTA-Echoing** (E.4.DPF:11: claim→источник→adoption) · 8. Имена (F.18) · 9. Relations к внешним DPF/DEC · 10. **Разнородные приёмочные случаи** (E.4.DPF carrier-order §10: 2–3 непохожих кейса, заставляющих паттерны работать за пределами мотивирующего примера — питает D8) · 11. Quality & refresh
\+ Артефакты каталога · Carrier note · Conformance CC-DPF.1–9 + статус пакета по E.4.DPF.DA.

**Разделение носителей (PFM7):** `DPF.md` — пользовательский носитель; в нём нет процессного состояния (ход прогона, статусы ревью, handoff-заметки). Процессные артефакты живут в `references/` (critic-review, черновики), решения авторинга — в DEC/DRR. Допустима одна финальная conformance-строка со статусом пакета.
**Примат решения задач (CC-DPF.9):** DPF обязан называть, какие типовые задачи домена он решает, какие известные провалы блокирует и какие SoTA-ходы предлагает. Каталог терминов/онтология без ходов решения — не DPF (анти-паттерн «Ontology catalog as framework»).

## 6. Обогащённый блок паттерна (E.8)
```
### Паттерн N: <имя>
- Recognition — когда применять
- Принцип (общий, SoTA-grounded)            ← первичен (фикс A.1.1 leak)
- Наша инстанциация (worked slice)           ← частность как иллюстрация
- Контрпример (похоже, но НЕ применять + почему)   [A.11 Sharp Boundary]
- Анти-паттерн (как НЕ исполнять)                   [E.8, отдельно от контрпримера]
- Conformance — как проверить
- Связи — composes/conflicts с паттернами        [E.4.PFR]
```

## 7. Паттерны метода (E.8)

### Паттерн 1: Research-first гейт
- **Recognition:** создаётся/существенно меняется DPF.
- **Принцип:** principle-framework требует source-grounding до паттернов (E.4.DPF: иначе checklist).
- **Наша инстанциация:** нет sota-research.md + theses-antitheses.md → Фаза 5 заблокирована.
- **Контрпример:** правка опечатки/ссылки в готовом DPF — гейт не нужен (не новый knowledge).
- **Анти-паттерн:** «соберу research постфактум под уже написанный DPF».
- **Conformance:** в каждом DPF-каталоге присутствуют оба research-файла до DPF.md.
- **Связи:** требует Фазу 1–2; питает Паттерн 2.

### Паттерн 2: Принцип → инстанциация
- **Recognition:** пишется worked slice с нашими частностями (код, имена).
- **Принцип:** сначала общий SoTA-принцип, потом наш пример как иллюстрация.
- **Наша инстанциация:** в DPF-EBPF «maps-first» — сперва принцип (config = данные, не код; индустрия), потом `gameserver2proxy_port`.
- **Контрпример:** чисто локальная конвенция без аналога в дисциплине — частность уместна без общего принципа (но пометить как local-only).
- **Анти-паттерн:** worked slice без предшествующего принципа (BoundedContext leak).
- **Conformance:** каждый worked slice имеет предшествующий принцип.
- **Связи:** conflicts с «срочностью» (Forces); composes с Research-first.

## Типовые ошибки авторинга DPF (E.4.DPF:8)

> Симптом → почему → исправление, с источником. Новичковые ошибки и ошибки опытных из устаревшей практики — вместе (D7). Полный bridge-анализ (scope + анти-тезис по каждому пункту) — `<комната>/references/theses-antitheses.md`.

| № | Симптом | Почему происходит | Исправление | Источник |
|---|---------|--------------------|--------------| ---------|
| 1 | DPF.md написан, но `sota-research.md` нет или появился «задним числом» | Соблазн срочности (Forces §3); неверие, что research меняет решения | Блокировать Фазу 5 до наличия обоих research-артефактов (Research-first гейт) | E.4.DPF:8 «Checklist promoted to framework»; наш кейс D11 (см. ниже) |
| 2 | DPF — список терминов/определений без ходов решения задач | Автор путает онтологию с фреймворком | Проверить CC-DPF.9: называет ли DPF типовые задачи, провалы, SoTA-ходы; иначе вернуть на Фазу 4 | E.4.DPF:8 «Ontology catalog as framework»; Zhang et al. arXiv:2501.19222 |
| 3 | Пакет считается готовым, потому что секции CC-DPF.1–9 присутствуют | Путают чек-лист присутствия секций с адекватностью пакета | Всегда прогонять E.4.DPF.DA поверх CC-чек-листа перед статусом `admissible` | E.4.DPF.DA:2; наш кейс (все CC PASS, но D5/D11 ниже пола) |
| 4 | Статус пакета повышают за полноту паттернов или число прошлых прогонов | Confirmation bias + sunk-cost | CC-DPFDA.4/8: статус — не средний балл паттернов и не награда за прошлые успехи | E.4.DPF.DA:8 «E.21 averaging», «Seed promotion» |
| 5 | Процессные заметки (чек-листы прогонов, номера инцидентов, телеметрия) остаются в пользовательском DPF.md | Удобно писать статус там же, где писался DPF | Держать процессное состояние в `references/quality-record-*.md`; в DPF.md — не более одной conformance-строки | E.4.DPF.DA:8 «Process-state leakage»; PFM7 |
| 6 (ИИ) | LLM-сгенерированный текст принимается за источник истины, потому что «звучит убедительно и по-FPF-шному» | Fluency-bias | Admission через C.33/C.34/C.35 прежде чем LLM-выдача становится claim'ом | E.4.DPF:8 «Generated candidate authority» |
| 7 (ИИ) | Один агент/сессия генерирует и research, и bridge, и critic — «согласие с собой» = evidence | LLM-consensus иллюзия | Держать роли раздельными по агентам (owner ≠ guardian ≠ keeper, DEC-003) | Метод §4 (guardian против «AI-consensus = evidence»); B.5.2.1 NQD |
| 8 (ИИ) | Source-pack цитирует почти исключительно один источник (сам FPF) | Authority-by-citation | Считать традиции независимо от того, кто их уже упомянул (FamilyCoverageFloorK=3) | CC-DPFDA.5; наш кейс D11 (source-pack.md до 2026-07-06 ремонта) |

## Разнородные приёмочные случаи (E.4.DPF §10, D8)

> Обязательная секция скелета (репарация D8). Проверка, что 6-фазный спайн реально работает за пределами мотивирующего примера. Честно: где прогон ревизованного (2026-07-06) метода не состоялся — помечено `worked-evidence pending`, допущение не повышено до факта (A.10).

**Случай 1 — технический домен, низкий уровень: DPF-EBPF.** `kind: Domain Principle Framework` (отличается от DPF-AUTHORING по kind). Спайн дал паттерн «maps-first» (принцип «конфиг = данные» → инстанциация `gameserver2proxy_port`), уже цитируемый как worked-пример в §7 Паттерн 2. Под ревизией E.4.DPF.DA — **worked-evidence pending** (conformant по старой CC-DPF.1–7, переоценка на `review_due`).

**Случай 2 — процессный/организационный домен: DPF-TEAM-TRAINING.** `kind: Local Practice Framework` (тот же kind, что у DPF-AUTHORING, но домен — обучение команды, не авторинг). Собран прогоном 2026-07-05 (докат после инцидента 2026-07-04). Под ревизией — **worked-evidence pending**.

**Случай 3 — сам метод (self-application), ревизия 2026-07-06.** Предельный случай: инструмент применил себя к себе (риск «согласия с собой» — см. ошибку №7 выше). Guardian прогнал Фазу 6 (E.4.DPF.DA) на DPF-AUTHORING → статус `repairBeforeDPFUse`: спайн нашёл у себя реальный дефицит (D5/D11 ниже пола — процессные следы в носителе и source-pack без независимых традиций). Ремонт закрыл собственный research-first гейт (`sota-research.md` + `theses-antitheses.md` в комнате), процессный остаток вынесен в `<комната>/references/quality-record-2026-07-06.md`; независимая повторная проверка guardian дала `admissibleForDeclaredDPFUse` (не самоподтверждение — A.10). **Вывод случая:** гейт не декоративен. Граница отказа спайна на уровне оркестрации входа (не домена) — инцидент 2026-07-04 (бутстрап-фолбэк тихо расширил охват в разы).

## 8. Quality & refresh (CC-DPF.7)
- **Оценивается:** прошёл ли DPF все 6 фаз; ≥3 традиции; принцип→инстанциация; есть контрпримеры/типовые ошибки/связи паттернов; **пакет целиком — по E.4.DPF.DA** (11 координат, не средний балл паттернов).
- **Seed-дисциплина (CC-DPFDA.8):** статусы `stub`/`stage-0` в competency-map = `seedOnly` в терминах E.4.DPF.DA — полезная заготовка, на которую роль НЕ опирается как на проверенный свод; скелет с заголовками ≠ паттерн (анти-паттерн «Skeleton carrier as DPF»). Повышение до опорного — только через фазу 6.
- **Имена (PFM6):** каноническая расшифровка вида — **Domain Principle Framework** / Local Practice Framework. Публичное имя пакета — предметное («Свод принципов <области>»); процессные статусы (draft, stage-0) живут во frontmatter, не в заголовке.
- **Refresh — триггеры:** изменение FPF-Spec; 3+ DPF с одинаковым отклонением → улучшить шаблон/скилл; обратная связь ролей. Уже-conformant DPF (проверены по CC-DPF.1–7 старой редакции) переоцениваются по E.4.DPF.DA при своём review_due, не немедленно. История конкретных рефрешей (что и когда сработало) — `<комната>/references/quality-record-2026-07-06.md`.

## Артефакты
- **В скилле (нужны для прогонов):** этот файл (канон метода) · `../assets/template-dpf.md` (скелет нового DPF) · `../assets/template-source-pack.md` (образец provenance-реестра) · `../assets/dpf-authoring.workflow.js` (конвейер).
- **В комнате (происхождение и качество метода, для прогонов не нужны):** `references/source-pack.md` (provenance) · `references/sota-research.md` (собственный SoTA-харвест) · `references/theses-antitheses.md` (bridge) · `references/package-adequacy-2026-07-06.md` (оценка E.4.DPF.DA + повторная проверка, итог `admissibleForDeclaredDPFUse`) · `references/quality-record-2026-07-06.md` (вынесенное процессное состояние, PFM7).
- FPF-разделы — **не храним выжимки**; читаем живьём (Grep по `~/.claude/knowledge/fpf/FPF-Spec.md` или FPF MCP).

## Carrier note (CC-DPF.5)
Секции FPF берутся Grep по FPF-Spec (не по памяти, A.10). Web/LLM-материал допускается через admission.

## Conformance
Таблица D1–D11, PFM-подпроход и история проверок — `<комната>/references/package-adequacy-2026-07-06.md`. Итоговый статус — строка ниже.

## Access carriers и зависимости (PFM10, E.4.PFR)
У метода два канала доступа (по E.4.DPF — **access carrier**: способ вызвать метод, а не сам метод; архитектура и качество живут в этом файле и комнате, не в манифестах каналов):
- **Скилл `dpf-authoring`** (`../SKILL.md` — самодостаточный, без машинных путей; решение Founder 2026-07-06) — парадная дверь: четыре режима (полный авторинг / переоценка пакета по E.4.DPF.DA / ремонт / точечная правка), инварианты метода. Запуск из любого проекта: обязательный `args.repoRoot` = целевой проект.
- **Воркфлоу `dpf-authoring-pipeline`** (`../assets/dpf-authoring.workflow.js`) — двигатель: исполняемый 6-фазный конвейер.

Роли конвейера (E.4.PFR, relationFunction: dependency, governedUse: роли фаз): `DPF-ADVERSARIAL-REVIEW@2026-07-06` (Bridge, Critic) и `DPF-KNOWLEDGE-CURATION@2026-07-06` (Source-pack, Assemble) — **встроены в скилл** (`../frameworks/<ID>/`, формат framework-apply, чем и резолвятся при использовании вне конвейера); нечитаемый пакет = громкий отказ фазы, обратной зависимости пакетов от метода нет (E.5.3).

Оба канала обязаны показывать edition метода (`fpf_edition` выше) и ломаться громко при несовпадении входа (fail-fast). Правки метода — только в этом файле, затем зеркалятся в комнату при ревизии (манифест канала ≠ архитектура метода).

> conformance: CC-DPF.1–9 verified; E.4.DPF.DA: admissibleForDeclaredDPFUse (ремонт+переоценка 2026-07-06, guardian)
