# Critic-review (Фаза 6) — LPF-SIMPLIFICATION-REVIEW

> Роль: **guardian** (независимая критика, devil's advocate). Дата прогона: 2026-07-13.
> Оцениваемый пакет: `.claude/frameworks/LPF-SIMPLIFICATION-REVIEW/DPF.md` (+ references/scope, sota-research, theses-antitheses, source-pack).
> Метод: FPF `E.4.DPF:7` (CC-DPF.1–9), `E.4.DPF:8` (анти-паттерны), `E.4.DPF.DA` (координаты D1–D11 + подпроход PFM1–PFM11, пол = 4). Спека прочитана живьём (FPF-Spec.md строки 64878–65390).
> Заявленный use: reliance-bearing (опора для роли reviewer стадии «Упрощение» + оркестратор). ⇒ пол = **4**.
> **Итог (спойлер): `repairBeforeDPFUse`.** CC-DPF.5 частично не выполнен (карриер-нота переобъявляет верность evidence); D5/D7/D11 ниже пола из-за одного ПОДТВЕРЖДЁННОГО дефекта evidence + PFM7-протечки процессного состояния. Правки минимальны и перечислены (§6). Gate НЕ пройден.

---

## 1. Что проверено запуском (evidence, A.10 — Predict→Run→Compare)

Пакет декларирует (Carrier note, CC-DPF.5): «git-evidence получено прямым чтением репозитория ... не выдумано и не экстраполировано ... каждое числовое утверждение в §4/§10 указывает источник». Я проверил **все четыре** несущих worked slice запуском команд репозитория.

| Worked slice | Заявление DPF | Результат прогона | Вердикт |
|---|---|---|---|
| §4 П3, c0b62cb | `core.testing.collect_rejected` извлечён из ДВУХ файлов, оба тронуты диффом: `faststream/pytest_plugin/dlx.py` + `kombu/pytest_plugin/dlx.py` | `git show c0b62cb --stat`: оба `dlx.py` изменены, `core/testing/__init__.py` добавлен с `collect_rejected` | **CONFIRMED** |
| §4 П4 / §10 Случай A, cc8f191 | Пять `test_invariant_a…e` + общий `_format_violations`, report-and-fail форма | `grep`: `_format_violations` (стр.91) + `test_invariant_a…e` (стр.117/131/147/159/173) | **CONFIRMED** |
| §4 П4/П5, КП-6 | `request_in.py` несёт `decode_request`+`ESBResponseMessage`+`_finalize` (роль другая), `event_in.py` — нет; оба несут `_on_message`+`UnknownMessageError` | `grep`: request_in — `decode_request` (98), `ESBResponseMessage.from_request` (120), `_finalize` присутствует; event_in — только `UnknownMessageError`, без response-машинерии | **CONFIRMED** |
| §4 П1 / §4 П2 / Carrier note, 0e6117b | `esb_middlewares` добавлен в конструкторы Manager-классов **обоих бэкендов**, «подтверждено `grep -rln "esb_middlewares: t.Sequence" esb_tools/backends/` — **6 файлов, оба бэкенда**» | На commit 0e6117b и в рабочем дереве **точная** команда даёт **3 файла, ТОЛЬКО faststream** (`event_in`, `request_in`, `request_out`). НЕ 6, НЕ оба бэкенда. | **DEFECT (CONFIRMED)** |

### Разбор дефекта П1 (главная находка)

- Точная цитируемая команда `grep -rln "esb_middlewares: t.Sequence"` на 0e6117b → 3 файла faststream. В рабочем дереве → те же 3.
- Kombu-конструктор параметр ИМЕЕТ (`backends/kombu/bootstrap.py:60`), но с иной аннотацией: `Sequence[Callable[[ESBContext], MiddlewareCM]]` (прямой импорт `Sequence`, не `t.Sequence`; `ESBContext`, не `core.context.ESBContext`) — поэтому строка `esb_middlewares: t.Sequence` его НИКОГДА не матчит.
- Число «6 файлов» не воспроизводится ни одной командой: loose `grep -rln esb_middlewares` на commit = 4 (все faststream), в рабочем дереве = 10 (оба бэкенда). Ни 6, ни «оба бэкенда через цитируемый grep».
- **Важно (в пользу пакета):** архитектурный ВЫВОД паттерна ИСТИНЕН и самодокументирован. Оба бэкенда реально несут публичный конструкторный параметр: `kombu/bootstrap.py:60` + `faststream/service.py:254` (проверено). Сообщение самого коммита 0e6117b: «единый контракт ... на обоих бэкендах (параметр esb_middlewares у менеджеров)». То есть Boundary-классификация и must-meet-маршрут (П1) — верны. **Ломается только цитата-доказательство, не архитектура.**
- **Почему это всё же ниже пола, а не «повод для беспокойства»:** вся ценность этой LPF — научить писать Finding с *воспроизводимым* git-evidence вместо «стало чище». Флагманский worked slice содержит невоспроизводимую grep-цитату — прямой контрпример к собственной Carrier note («не выдумано и не экстраполировано») и к conformance Паттерна 2 («проверка: можно ли посчитать конвейером»). `CC-DPFDA.5`: неверная/декоративная цитата понижает D11. Для reliance-bearing use (пол 4) это floor-breach, а не косметика: пакет моделирует ровно тот failure mode, против которого создан.

---

## 2. Упущенное (традиция / тензия / claim без источника / голая частность / нет контрпримера)

Проверка по чек-листу критика. Здесь пакет силён — большинство пунктов закрыто.

- **Традиции:** 8 (T10–T17), `FamilyCoverageFloorK=3` перекрыт. Не упущено значимой традиции ревью-практики; AI-специфика (T16/T17) покрыта отдельной осью. OK.
- **Тензии:** §3 Forces — 5 scoped-тензий; внутренние тензии традиций (T11 lightweight vs чек-лист; T12 чини-здесь vs выноси; T16↔T17 hypothesis vs факт) зафиксированы без silent fusion. OK.
- **Claim без источника:** каждый claim в SoTA-Echoing §7 имеет ref + статус (fact/hypothesis/opinion/unverified secondary). Единственный claim, чья evidence-цепь РВЁТСЯ на прогоне — grep-цитата П1 (см. §1). Это не «claim без источника», а claim с НЕВЕРНЫМ источником — хуже: источник назван и не воспроизводится.
- **Голая частность (A.1.1 leak):** не найдено — каждый worked slice предварён SoTA-принципом (метод §6). OK.
- **Контрпримеры:** 8 КП (§2 theses-antitheses) + инстанцированы в §4 (КП-2…КП-8). Sharp Boundary соблюдён. OK.
- **Реально упущенное:** §10 **Случай B** (LLM-исполнитель) — открыто помечен «НЕ evidence из истории esb-tools ... телеметрии не существует ... перенесённая SoTA-иллюстрация». Честно (A.10), но означает: из трёх «разнородных приёмочных случаев» D8 только два (A, C) — реальное repo-evidence, третий — мысленный эксперимент. Это **потолок D8 (4, не 5)**, не floor-breach. Не требует правки для допуска.

---

## 3. Подпроход формы — PFM1–PFM11 (CC-DPFDA.6a, до выставления D-значений)

| PFM | Disposition | Обоснование |
|---|---|---|
| PFM1 Front-door order | PASS | Шапка §0-report → §1 контекст → §4 паттерны; читатель выбирает паттерн без чтения тяжёлых карт. |
| PFM2 Pattern-language primacy | PASS | Паттерны §4 — главный язык; карты связей §5/§9 и SoTA §7 после паттернов. |
| PFM3 Map discoverability | PASS | Таблицы §5/§7/§9 достижимы из §4 (ссылки на Forces, связи паттернов). |
| PFM4 Dependency direction | PASS | LPF→`DPF-COUPLING-GENERALIZATION` односторонняя (§9); FPF Core / базовый ДПФ не цитируют эту LPF. |
| PFM5 Publication/access-carrier boundary | PASS | §9 явно: DPF.md — единственный access carrier; references — process-state, не второй носитель. |
| PFM6 Public naming | PASS | `name:` — предметная фраза; `stage-0` во frontmatter, не в заголовке. `LPF-` — id каталога, допустимо. |
| **PFM7 Development-state absence** | **FAIL** | Пользовательский носитель DPF.md насыщен процессным состоянием прогона: шапка стр.22–24 («этот прогон закрывает Фазы 4–5; Фаза 6 ... не проведена»), §11 первый буллет (run-нарратив «Фаза 6 этого прогона НЕ проведена ... references не созданы в рамках этого прогона»), ДВЕ conformance-строки в футере. Метод §5 / ошибка №5: «в DPF.md — не более одной conformance-строки», процессное — в `references/quality-record-*`. E.4.DPF.DA анти-паттерн «Process-state leakage». Понижает D5 (и частично D9/D10). |
| PFM8 Cross-DPF relation discipline | PASS | §9 — edition dependency с blocked reverse, refresh-условие. |
| PFM9 Normal-pattern maturity | PASS | 5 паттернов §4 — полные E.8-тела (Recognition→Принцип→инстанциация→контрпример→анти-паттерн→conformance→связи). |
| PFM10 Access-currentness boundary | PASS | §11 refresh-триггеры + edition; шапка «рекомендует, не сертифицирует». |
| PFM11 Carrier structure-account | PASS | §0-report шапки: для кого, что на переднем плане, что огрублено/опущено, куда возврат. |

**Итог PFM:** 10 PASS, 1 FAIL (PFM7). Провал PFM7 понижает D5.

---

## 4. Таблица координат D1–D11 (E.4.DPF.DA:4.2/4.3, пол = 4)

| Координата | Значение | Краткое обоснование (почему не ниже / не выше) | Evidence-locus | Repair / no-proposal |
|---|---|---|---|---|
| D1 DomainScope | 4 | Контекст, reader, first use, non-use — присутствуют и остры (§1, scope.md). Не ниже: границы явные. Не 5: heterogeneous-покрытие частично гипотетично (Случай B). | DPF.md §1; scope.md §Non-use | no-proposal |
| D2 DidacticEntry | 4 | Front-door + паттерны-первыми + задача читателя названа. Не 5: детальный формат «письменный ответ на каждый гейт» сам по себе тяжёл для первого входа (T16-риск отмечен, но не смягчён в самом входе). | §0-report; §4 | no-proposal |
| D3 ScalableFormality | 4 | Стадия staged: written-answer→Local/Module (оркестратор)→Boundary (мейнтейнер); П4 бесплатный через тест. | §4 П1; §9 | no-proposal |
| D4 CoreDependency | 4 | Односторонняя зависимость LPF→базовый ДПФ, reverse blocked (CC-DPFDA.6b PASS), домен-знание внутри LPF. | §9; PFM4 | no-proposal |
| **D5 PackageForm** | **3** | Разделение носителей в целом верное (паттерны/references), НО PFM7 FAIL: процессное состояние прогона протекло в пользовательский носитель (шапка стр.22–24, §11, две conformance-строки). Ниже пола. | PFM7; DPF.md стр.22–24, §11, футер | **R2 (§6)** |
| D6 Lexicon | 4 | §8 durable/provisional разведены, F.18-маршрут назван. | §8 | no-proposal |
| **D7 PracticeUtility** | **3** | Паттерны решают реальные задачи ревью-стадии (подтверждено 3/4 slice). НО флагманский обучающий worked slice (П1/П2, esb_middlewares) несёт невоспроизводимую evidence-цитату — дидактический эталон «пиши Finding с воспроизводимым git-evidence» мис-обучает на собственном примере. Ниже пола для reliance-bearing use. | §1 наст. файла; DPF.md §4 П1/П2, Carrier note | **R1 (§6)** |
| D8 HeterogeneousCase | 4 | Случаи A, C — реальное repo-evidence (проверено). Случай B помечен `worked-evidence pending` (честно, A.10). Не ниже: 2 реальных разнородных кейса. Не 5: третий гипотетичен. | §10 A/B/C; §1 наст. файла | no-proposal (потолок) |
| D9 EditionState | 4 | FPF edition pinned, review_due, edition-dep на базовый ДПФ, refresh-триггеры. Частичный сквозняк PFM7, но edition-ссылки сами чисты. | frontmatter; §11 | частично R2 |
| D10 Improvement/Refresh | 4 | §11 — конкретные refresh-триггеры (смена FPF/базового ДПФ edition, второй источник T16/T17, LLM-прогон, competency-map). | §11 | no-proposal |
| **D11 DomainSoTA** | **3** | 8 традиций, adopted/rejected, 6 retired premises, CL-штраф — дисциплина сильная. НО один source-grounded claim (П1 grep) НЕ воспроизводится на прогоне; CC-DPFDA.5: неверная цитата понижает D11. Один CONFIRMED floor-breach на evidence. | §1 наст. файла; DPF.md §4 П1, Carrier note | **R1 (§6)** |

**Три координаты ниже пола 4: D5, D7, D11.** По E.4.DPF.DA:4.5 → статус `repairBeforeDPFUse`.

---

## 5. Вердикт по CC-DPF.1–9 (E.4.DPF:7)

| Check | Вердикт | Комментарий |
|---|---|---|
| CC-DPF.1 Context declared | PASS | §1 + scope.md. |
| CC-DPF.2 Source pack present | PASS | source-pack.md — adopted/rejected/claim-status/currentness по каждому источнику + retired premises. |
| CC-DPF.3 Architecture decision present | PASS (embedded) | Арх-решение встроено (§3 Forces + §4 split + §9 Relations); отдельного PFAD/DRR-носителя нет, но метод допускает решение «в DPF.md» (Фаза 4). |
| CC-DPF.4 Names prepared | PASS | §8 provisional/durable + F.18-маршрут. |
| **CC-DPF.5 Carriers admitted** | **PARTIAL-FAIL** | Carrier note заявляет «git-evidence ... не выдумано и не экстраполировано ... каждое числовое утверждение указывает источник». Проверка: число «6 файлов, оба бэкенда» через цитируемый grep НЕ воспроизводится (3 файла, faststream). Само admission-утверждение о верности evidence ложно в одной точке. Требует R1. |
| CC-DPF.6 Patterns via E.8 | PASS | 5 полных паттернов. |
| CC-DPF.7 Quality/refresh routes | PASS | §11. |
| CC-DPF.8 Carrier structure-account | PASS | §0-report. |
| CC-DPF.9 Problem-solving primacy | PASS | Называет задачи (поймать №8/№9/№11 без №11/№12), провалы, SoTA-ходы. |

**CC-DPF.1–9: НЕ чистый PASS** — CC-DPF.5 partial-fail (evidence-fidelity self-claim нарушен). Это независимо от D-таблицы уже блокирует gate.

---

## 6. Список наименьших правок (repair before DPF use)

Оба — минимальные, точечные (A.11); архитектура паттернов НЕ меняется.

**R1 — исправить evidence-цитату П1 (закрывает D7, D11, CC-DPF.5).**
В §4 Паттерн 1, §4 Паттерн 2 и Carrier note заменить невоспроизводимую цитату:
- Убрать «подтверждено `grep -rln "esb_middlewares: t.Sequence"` — 6 файлов, оба бэкенда» (не воспроизводится).
- Заменить на воспроизводимое: либо loose-команда `grep -rln esb_middlewares esb_tools/backends/` (оба бэкенда, 10 файлов в рабочем дереве), либо — точнее для «конструктор публичного менеджера» — назвать два loci прямо: `backends/kombu/bootstrap.py:60` и `backends/faststream/service.py:254` (оба — публичные Manager-конструкторы, оба несут параметр; проверено).
- Архитектурный вывод (Boundary, must-meet, оба бэкенда) оставить — он ИСТИНЕН и самодокументирован сообщением коммита 0e6117b; правится только цитата-доказательство.
- В Carrier note снять сверх-обобщённое «каждое числовое утверждение ... не экстраполировано» либо привести число в соответствие.

**R2 — вынести процессное состояние прогона (закрывает PFM7 → D5, частично D9).**
- Перенести run-нарратив в `references/quality-record-2026-07-13.md`: шапка стр.22–24 («этот прогон закрывает Фазы 4–5; Фаза 6 не проведена»), §11 первый буллет (статус созданности references), лишние conformance-строки.
- В DPF.md оставить **не более одной** conformance-строки со статусом пакета (метод §5, ошибка №5).
- После фиксации этого ревью (Фаза 6 проведена) — обновить `status:` и схлопнуть seedOnly-нарратив.

**R3 (не для допуска, потолок D8→5):** оставить Случай B помеченным `worked-evidence pending` до реальной телеметрии LLM-прогона (уже сделано; действий не требуется).

После R1+R2: D5/D7/D11 поднимаются до ≥4, CC-DPF.5 → PASS ⇒ ожидаемый статус `admissibleForDeclaredDPFUse` на повторном прогоне.

---

## 7. Статус пакета (E.4.DPF.DA:4.5, честный — CC-DPFDA.8)

**`repairBeforeDPFUse`.**

Обоснование: пакет на входе сам объявлен `status: stage-0` / seedOnly. Промоушен до опоры роли блокируют два дефекта ниже пола 4: (D11/D7/CC-DPF.5) один ПОДТВЕРЖДЁННЫЙ невоспроизводимый evidence-citation во флагманском worked slice — прямой контрпример к собственной evidence-дисциплине пакета; (D5/PFM7) протечка процессного состояния прогона в пользовательский носитель. Обе правки минимальны и перечислены (§6). Это НЕ повод переписывать паттерны — идея и архитектура здоровы (три из четырёх worked slice воспроизводятся, П1-вывод истинен). Это повод исправить факт и вынести процессный сор ПЕРЕД опорой роли.

**Не `seedOnly`** (пакет прошёл все 6 фаз и близок к допуску), **не `admissible`** (три координаты и CC-DPF.5 ниже пола до R1/R2).

## 8. Gate

**gate_passed = false.** CC-DPF.1–9 не чистый PASS (CC-DPF.5 partial-fail); статус = `repairBeforeDPFUse` ≠ `admissibleForDeclaredDPFUse`. Conformance-строка `admissibleForDeclaredDPFUse` в DPF.md **НЕ дописана** (условие задания не выполнено). После R1+R2 — повторный прогон Фазы 6.
