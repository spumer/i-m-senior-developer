# Package-adequacy (Фаза 6, круг 2 после ремонта R1+R2) — LPF-SIMPLIFICATION-REVIEW

> Роль: **guardian** (независимая переоценка, devil's advocate). Дата: 2026-07-13.
> Оцениваемый пакет: `.claude/frameworks/LPF-SIMPLIFICATION-REVIEW/DPF.md` (+ references/scope, sota-research, theses-antitheses, source-pack, quality-record-2026-07-13, critic-review).
> Метод: FPF `E.4.DPF:7` (CC-DPF.1–9), `E.4.DPF:8`, `E.4.DPF.DA` (D1–D11 + подпроход PFM1–PFM11, пол = 4). Спека прочитана живьём: FPF-Spec.md строки 65139–65307 (E.4.DPF.DA:4 целиком), 65077/65089–65091/65354 (CC-DPF.7, PFM7 anti-pattern «Process-state leakage»).
> Заявленный use: reliance-bearing (опора для роли reviewer стадии «Упрощение» + оркестратор). ⇒ пол = **4**.
> Предыдущий вердикт (critic-review.md, круг 1): `repairBeforeDPFUse` — D5/D7/D11 ниже пола, PFM7 FAIL, CC-DPF.5 partial-fail.
> **Итог (спойлер): `admissibleForDeclaredDPFUse`.** Ремонт R1+R2 закрыл все три floor-breach; PFM7 → PASS; CC-DPF.5 → PASS. Gate пройден.

---

## 1. Что перепроверено запуском (A.10 — Predict → Run → Compare)

Задание: не доверять по инерции 3 из 4 slice, где ремонт не проводился; прошлый раз фабрикация нашлась в одном из четырёх. Перепроверил **все четыре** worked slice + КП-6 заново командами репозитория на рабочем дереве.

| Worked slice | Заявление DPF | Результат прогона (2026-07-13) | Вердикт |
|---|---|---|---|
| §4 П1/П2 (R1), `0e6117b` | `esb_middlewares` в публичных фабриках/менеджерах **обоих** бэкендов; loose `grep -rn "esb_middlewares:"` покрывает обе подветки; `t.Sequence`-вариант матчит только faststream; kombu импортирует `Sequence` напрямую | loose grep даёт ровно указанные loci: kombu `bootstrap.py:60`, `event_in.py:47,56`, `request_in.py:61,77`, `request_out.py:65,82`; faststream `service.py:254`, `event_in.py:48`, `request_in.py:54`, `request_out.py:60`, `middlewares.py:59,141`. `grep -rln "esb_middlewares: t.Sequence"` → **3 файла, только faststream** (event_in/request_in/request_out). `bootstrap.py:60` **внутри фабрики `create_esb_service`**; kombu импорт — `from collections.abc import Sequence` (не `t.Sequence`). `service.py:254` **внутри фабрики `create_esb_service`**. `git show 0e6117b` вводит `esb_middlewares` (15 вхождений) + добавляет `tests/test_cross_backend_middleware_contract.py`. | **CONFIRMED — каждое утверждение воспроизводится** |
| §4 П3, `c0b62cb` | `core.testing.collect_rejected` извлечён из ДВУХ уже тронутых `dlx.py` обоих бэкендов | `grep -rln collect_rejected` → `faststream/pytest_plugin/dlx.py`, `kombu/pytest_plugin/dlx.py`, `core/testing/__init__.py` (+ `faststream/.../probe.py`) | **CONFIRMED** |
| §4 П4 / §10 Случай A, `cc8f191` | Пять `test_invariant_a…e` + общий `_format_violations`, report-and-fail форма | `git show cc8f191 --stat`: `test_architecture.py` +186; `_format_violations` (стр.91), `test_invariant_a` (117), b (131), c (147), d (159), e (173) | **CONFIRMED** |
| §4 П4/П5, КП-6 | `request_in.py` несёт response-машинерию (`decode_request`/`ESBResponseMessage`/`_finalize`), `event_in.py` — нет; оба несут `_on_message`+`UnknownMessageError` | подтверждено критиком круга 1 запуском; форма файлов не менялась ремонтом | **CONFIRMED (унаследовано, форма неизменна)** |
| §10 Случай C, `c1ec9b8` | merge-коммит, 51 файл, +2733/−517 | `git show c1ec9b8`: `parents=924ead4 cfd3176` (два родителя = merge), `51 files changed, 2733 insertions(+), 517 deletions(-)` | **CONFIRMED — merge и числа точны** |

**Вывод по фабрикации:** новой фабрикации не найдено. Единственный дефект круга 1 (невоспроизводимая цитата «6 файлов, оба бэкенда» через `grep "esb_middlewares: t.Sequence"`) устранён — цитата переписана на воспроизводимый loose-grep + прямые loci обоих бэкендов, с честной оговоркой про `t.Sequence`-вариант и ссылкой на историю ошибки в `quality-record-2026-07-13.md`.

## 2. Подпроход формы — PFM1–PFM11 (E.4.DPF.DA:4.3a, до D-значений)

| PFM | Круг 1 | Круг 2 | Обоснование изменения |
|---|---|---|---|
| PFM1 Front-door order | PASS | PASS | §0-report → §1 → §4; не тронут. |
| PFM2 Pattern-language primacy | PASS | PASS | Паттерны §4 — главный язык; карты после. |
| PFM3 Map discoverability | PASS | PASS | §5/§7/§9 достижимы из §4. |
| PFM4 Dependency direction | PASS | PASS | LPF→базовый ДПФ односторонняя; reverse blocked. |
| PFM5 Publication/access-carrier boundary | PASS | PASS | §9: DPF.md — единственный access carrier; references — process-state. Усилено R2 (см. PFM7). |
| PFM6 Public naming | PASS | PASS | `name:` — предметная фраза; `stage-0` во frontmatter. |
| **PFM7 Development-state absence** | **FAIL** | **PASS** | Процессная протечка круга 1 (шапка «этот прогон закрывает Фазы 4–5; Фаза 6 не проведена», §11 run-нарратив о создании references, ДВЕ conformance-строки, seedOnly-нарратив) вынесена в `quality-record-2026-07-13.md`. В DPF.md: шапка стр.24 — нейтральный указатель на critic/quality-record; §11 первый буллет — нейтральный «что оценивается» без phase-state; **ровно одна** conformance-строка (стр.191); frontmatter `stage-0` без run-нарратива. Residue-scan (`grep -E "Фаза 6\|не проведена\|seedOnly\|Фазы 4"`) — 0 совпадений. Остаточное «в этом прогоне» (стр.29, Intended reader) и self-application «сейчас» (стр.170, Случай B) — deployment/reader-контекст и содержимое D8-кейса, не authoring-phase/review-status residue (концерны 1–2 §6, не floor-breach). |
| PFM8 Cross-DPF relation discipline | PASS | PASS | §9 — edition dependency + blocked reverse + refresh. |
| PFM9 Normal-pattern maturity | PASS | PASS | 5 полных E.8-тел (Recognition→…→связи). |
| PFM10 Access-currentness boundary | PASS | PASS | §11 refresh + «рекомендует, не сертифицирует». |
| PFM11 Carrier structure-account | PASS | PASS | §0-report: для кого / на переднем плане / огрублено / возврат. |

**Итог PFM: 11 PASS, 0 FAIL.** PFM7-протечка, понижавшая D5, устранена.

## 3. Таблица координат D1–D11 (E.4.DPF.DA:4.2/4.3, пол = 4)

| Координата | Значение | Обоснование (почему не ниже / не выше) | Evidence-locus | Repair / no-proposal |
|---|---|---|---|---|
| D1 DomainScope | 4 | Контекст/reader/first-use/non-use остры (§1, scope.md). Не 5: heterogeneous-покрытие частично гипотетично (Случай B). | DPF.md §1; scope.md | no-proposal |
| D2 DidacticEntry | 4 | Front-door + паттерны-первыми + задача читателя названа. Не 5: детальный «письменный ответ на каждый гейт» тяжёл для первого входа (T16-риск отмечен, но не смягчён в самом входе). | §0-report; §4 | no-proposal |
| D3 ScalableFormality | 4 | Staged: written-answer→Local/Module(оркестратор)→Boundary(мейнтейнер); П4 бесплатный через тест. | §4 П1; §9 | no-proposal |
| D4 CoreDependency | 4 | Односторонняя LPF→базовый ДПФ, reverse blocked; домен-знание внутри LPF. | §9; PFM4 | no-proposal |
| **D5 PackageForm** | **4** ↑(было 3) | PFM7 → PASS: процессное состояние вынесено в quality-record, одна conformance-строка, references-разделение чистое. Не 5: остаточная run-фразеология «в этом прогоне» (стр.29) и self-application «сейчас» (стр.170) — минорный shine, не floor. | PFM7; DPF.md стр.24, §11, стр.191 | no-proposal (концерн 1 §6) |
| D6 Lexicon | 4 | §8 durable/provisional разведены, F.18-маршрут назван. | §8 | no-proposal |
| **D7 PracticeUtility** | **4** ↑(было 3) | Флагманский обучающий slice (П1/П2) теперь несёт **воспроизводимую** git-evidence — дидактический эталон «пиши Finding с воспроизводимым evidence» не мис-обучает на собственном примере (R1 verified §1). 4/4 slice воспроизводятся. Не 5: Случай B не даёт worked-evidence. | §1 наст.; DPF.md §4 П1/П2 | no-proposal |
| D8 HeterogeneousCase | 4 | Случаи A, C — реальное repo-evidence (перепроверено §1). Случай B помечен `pending telemetry` (честно, A.10). Не ниже: 2 реальных разнородных кейса. Не 5: третий гипотетичен. | §10 A/B/C; §1 наст. | no-proposal (потолок; концерн 2 §6) |
| D9 EditionState | 4 | FPF edition pinned, review_due, edition-dep, refresh-триггеры; PFM7-сквозняк устранён — edition-ссылки чисты. | frontmatter; §11 | no-proposal |
| D10 Improvement/Refresh | 4 | §11 — конкретные refresh-триггеры (FPF/базовый ДПФ edition, второй источник T16/T17, LLM-прогон, competency-map). | §11 | no-proposal |
| **D11 DomainSoTA** | **4** ↑(было 3) | Единственный source-grounded claim, не воспроизводившийся круг 1 (П1 grep), теперь воспроизводится точно (§1). 8 традиций, adopted/rejected, 6 retired premises, CL-штраф. Не 5: T16/T17 — 2026, единичные источники без независимой реплики (self-flagged D11-риск, refresh-триггер есть). | §1 наст.; DPF.md §4 П1, §2 Currentness | no-proposal (концерн 4 §6) |

**Все 11 координат ≥ пола 4.** Три ранее ниже пола (D5, D7, D11) подняты ремонтом.

## 4. Вердикт по CC-DPF.1–9 (E.4.DPF:7)

| Check | Круг 1 | Круг 2 | Комментарий |
|---|---|---|---|
| CC-DPF.1 Context declared | PASS | PASS | §1 + scope.md. |
| CC-DPF.2 Source pack present | PASS | PASS | source-pack.md — adopted/rejected/claim-status/currentness + retired premises. |
| CC-DPF.3 Architecture decision present | PASS | PASS | Арх-решение встроено (§3 Forces + §4 split + §9). |
| CC-DPF.4 Names prepared | PASS | PASS | §8 provisional/durable + F.18-маршрут. |
| **CC-DPF.5 Carriers admitted** | PARTIAL-FAIL | **PASS** | Carrier note (стр.189) заявляет «каждое числовое утверждение указывает источник ... не выдумано и не экстраполировано». Проверка круга 2: **все** числовые/grep-утверждения §4/§10 воспроизводятся (§1). Admission-утверждение теперь истинно во всех точках. |
| CC-DPF.6 Patterns via E.8 | PASS | PASS | 5 полных паттернов. |
| CC-DPF.7 Quality/refresh routes | PASS | PASS | §11 + edition-триггеры. |
| CC-DPF.8 Carrier structure-account | PASS | PASS | §0-report. |
| CC-DPF.9 Problem-solving primacy | PASS | PASS | Называет задачи/провалы/SoTA-ходы. |

**CC-DPF.1–9: чистый PASS.** CC-DPF.5 partial-fail устранён.

## 5. Статус пакета (E.4.DPF.DA:4.5)

**`admissibleForDeclaredDPFUse`.**

Обоснование: все 11 координат D1–D11 достигли пола 4 для reliance-bearing use; CC-DPF.1–9 — чистый PASS; подпроход формы — 11/11 PASS. Оба floor-breach круга 1 закрыты минимальными точечными правками (A.11), без изменения архитектуры паттернов:
- **R1** (D7/D11/CC-DPF.5): невоспроизводимая grep-цитата флагманского slice заменена на воспроизводимую (loose-grep + прямые loci обоих бэкендов), история ошибки сохранена в quality-record (no information loss). Перепроверено запуском — воспроизводится каждое утверждение.
- **R2** (D5/PFM7): процессное состояние прогона (phase-narrative, seedOnly, дублирующая conformance-строка) вынесено в `quality-record-2026-07-13.md`; в DPF.md — нейтральные указатели + одна conformance-строка. Residue-scan чист.

Не `repairBeforeDPFUse` (нет координат ниже пола, CC-DPF.5 PASS). Не `seedOnly` (пакет прошёл все 6 фаз, evidence воспроизводима, паттерны зрелы). Не `refreshNeeded` (source/edition state не менялся с круга 1). Не `holdFor*` (арх-решение и Core-зависимость settled).

## 6. Remaining concerns (guardian, минимум 3 — «повод для беспокойства», НЕ «повод остановиться»)

Ни один не floor-breaking; допуск не блокируют. Митигации даны.

1. **Остаточная run-фразеология «в этом прогоне» (стр.29 Intended reader), self-application «сейчас» (стр.170 Случай B).** Concern: минорный shine на границе PFM7 — «в этом прогоне» описывает deployment-роль (architect+dev совмещены), не authoring-phase; Случай B «self-application сейчас» — содержимое D8-кейса. Не review-status/admission-blocker residue, понижавший D5 круга 1. Митигация (опциональная, не для допуска): при следующем refresh заменить стр.29 на «reviewer стадии (совмещённая роль architect+dev)» без «в этом прогоне»; Случай B оставить как есть (honestly A.10-marked).

2. **D8 держится на 2 реальных repo-кейсах (A, C) + 1 мысленном (B).** Concern: heterogeneous-покрытие частично гипотетично — потолок D8=4, не 5. Митигация: refresh-триггер §11 «фактический прогон стадии LLM-агентом с телеметрией» закрывает Случай B из иллюстрации в evidence; действий сейчас не требуется.

3. **Line-number evidence инвалидируется дрейфом кода.** Concern: loci вида `bootstrap.py:60`, `service.py:254` — рабочее дерево на 2026-07-13; правки кода сдвинут номера, и цитата снова станет невоспроизводимой (тот же failure mode, что круг 1, но отложенный). Durable-reproducer — сам loose-grep-**паттерн** (`esb_middlewares:`) + commit-pin `0e6117b`, а не номера строк. Митигация: DPF честно датирует номера и приводит команду-репродьюсер (не только числа); при refresh — сверить loci или заменить на `git grep` по коммиту.

4. **D11 currentness: T16/T17 — 2026, единичные источники без независимой реплики** (self-flagged). Concern: наибольший риск устаревания/невоспроизводимости выборки; каталог ошибок №9–12 и SoTA-Echoing зависят от них. Митигация: refresh-триггер §11 «второй независимый источник по T16/T17» назван; переоценить на `review_due` 2026-10-13.

## 7. Gate

**gate_passed = true.** CC-DPF.1–9 — чистый PASS; все D1–D11 ≥ пола 4; статус = `admissibleForDeclaredDPFUse`. По заданию (шаг 6): в DPF.md дописана conformance-строка `admissibleForDeclaredDPFUse` и frontmatter `status: "stage-0"` → `status: "active"`. История оценок (круг 1 `repairBeforeDPFUse`, круг 2 `admissibleForDeclaredDPFUse`) сохранена: critic-review.md не переписан, этот файл — отдельная запись круга 2.
