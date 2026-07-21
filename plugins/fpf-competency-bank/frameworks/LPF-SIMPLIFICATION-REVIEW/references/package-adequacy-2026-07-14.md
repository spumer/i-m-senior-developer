# Package-adequacy (переоценка после содержательного изменения — Паттерн 6) — LPF-SIMPLIFICATION-REVIEW

> Два круга одного guardian-прохода 2026-07-14. **Круг 1** (§1–§8) — вердикт `repairBeforeDPFUse`, repair-список R1. **Круг 2** (§9–§13, после ремонта R1, последний допустимый) — **итоговый вердикт `admissibleForDeclaredDPFUse`**. Круг 1 сохранён дословно как история (no information loss).

---

## Круг 1 (до ремонта R1)

> Роль: **guardian** (независимая переоценка, devil's advocate — не автор, не самопроверка сборщика). Дата: 2026-07-14.
> Оцениваемый пакет: `.claude/frameworks/LPF-SIMPLIFICATION-REVIEW/` целиком — `DPF.md` + `assets/apply-prompt.md` + `assets/finding-schema.json` + `references/*`.
> Повод: `quality-record-2026-07-13.md` Addendum 3 — добавлен Паттерн 6 «Гейт ширины контракта» (СОДЕРЖАТЕЛЬНОЕ изменение при статусе `admissible`). Требует переподтверждения независимым критиком.
> Метод: FPF `E.4.DPF:7` (CC-DPF.1–9), `E.4.DPF:8`, `E.4.DPF.DA` (D1–D11 + подпроход PFM1–PFM11, пол = 4). Спека прочитана живьём: FPF-Spec.md строки 66506–66720 (E.4.DPF.DA:4 целиком, PFM1–11, D1–D11, status), 66420–66445 (CC-DPF.1–15). Governing patterns Паттерна 6 (`existing-code.md` Blast Radius, FPF A.7, `rules/python/main.md`) прочитаны в репозитории.
> Заявленный use: reliance-bearing (опора для роли reviewer стадии «Упрощение» + оркестратор; исполнение через `dpf-apply` **apply**-режим = спаун агента по `apply-prompt.md`). ⇒ пол = **4**.
> Предыдущий вердикт (`package-adequacy-2026-07-13.md`, круг 2): `admissibleForDeclaredDPFUse` (пакет П1–П5).
> **Итог (спойлер): `repairBeforeDPFUse`.** DPF.md-носитель Паттерна 6 полон и зрел, git-evidence воспроизводится, honesty-контракт (без фиктивной SoTA) соблюдён. НО исполнимые носители (`apply-prompt.md` scan+routing, `finding-schema.json`) **не несут Паттерн 6** — capability добавлена в свод, но не проведена в executable-путь. D2/D5/D7 ниже пола для apply-режима.

---

## 1. Что перепроверено запуском (A.10 — Predict → Run → Compare)

Задание переоценки: (а) git-evidence Паттерна 6 — коммит `9fa714c`, underscore-имена, правило `main.md`; (б) honesty — П6 не притворяется выросшим из SoTA T10–T17; (в) синхронность П1–П5→П1–П6 по ВСЕМ носителям, не только DPF.md.

| Проверка | Заявление | Результат прогона (2026-07-14) | Вердикт |
|---|---|---|---|
| Коммит `9fa714c` существует | worked slice §4 П6 | `git show --stat 9fa714c` — существует, 24 файла, Author Посохин, Tue Jul 14 | **CONFIRMED** |
| Тело коммита содержит абзац «Публичный контракт сознательно узкий» | §4 П6, §6 №13 | `git log -1 --format=%B 9fa714c` — абзац дословно присутствует («решение мейнтейнера»: только `RetryConfig/RetryFlow/retry` и `make_test_topology`+фикстуры публичны; машинерия — internal с подчёркиванием) | **CONFIRMED** |
| `_dlx_routing_key` в `core/topology.py` | §4 П6 | `core/topology.py:62` `def _dlx_routing_key(...)`; финальное дерево — **приватный** (сужение выполнено тем же диффом, как и заявлено). Передаётся строкой: `bootstrap.py:607` → `kombu/retry.py:50` — «дешёвый вариант» (готовая строка) в дереве | **CONFIRMED** |
| `_decide` в `core/retry.py` | §4 П6 | `core/retry.py:100` `def _decide(...)`; в модуле ещё 7 приватных (`_retry_delay_exchange_name`, `_attempts_from_headers`, `_Continue`, `_Exhausted` …) | **CONFIRMED** |
| `_should_publish_directly` в `core/queue_manager.py` | §4 П6 | `core/queue_manager.py:153` `def _should_publish_directly(...) -> TypeGuard[...]` | **CONFIRMED** |
| Правило leading underscore в `rules/python/main.md` | §4 П6 принцип, §6 №13 | `main.md:19` — «New names default to a leading underscore … public name is a contract … proposed to the maintainer explicitly … Litmus test: who breaks if we rename this tomorrow». Файл `M` в рабочем дереве | **CONFIRMED** |
| Публичные имена, оставшиеся публичными | §4 П6 | `RetryFlow`/`RetryConfig` (`core/retry.py:20,29`), `make_test_topology` (`core/testing/broker.py:116`) — публичны | **CONFIRMED** |
| Honesty: П6 не растёт из T10–T17 | задание §2 | §7 SoTA-Echoing — строки П6 **нет**; §2 харвест не расширялся; §4 П6 принцип: «(governing patterns, не новая SoTA-традиция)». Фиктивной SoTA-ссылки нет | **CONFIRMED (честно)** |

**Вывод по evidence Паттерна 6 в DPF.md:** новой фабрикации не найдено, каждая git-точка воспроизводится, honesty-контракт соблюдён. Носитель-в-DPF.md Паттерна 6 — полное E.8-тело (Recognition→принцип→инстанциация→контрпример→анти-паттерн→conformance→связи), PFM9-зрелое.

## 2. Найденный дефект — синхронизация оборвана на исполнимых носителях (floor-breach)

Addendum 3 заявляет: «синхронизированы упоминания П1–П5→П1–П6 (шапка, §8, §9, §11, apply-prompt)». Проверка запуском показывает — синхронизация **поверхностная** (bump заголовочных ссылок), operative-содержание executable-носителей Паттерн 6 НЕ несёт:

| Носитель | Что заявлено | Что в файле (2026-07-14) | Дефект |
|---|---|---|---|
| `apply-prompt.md` §2.1 «Скан кандидатов» | процедура ищет кандидатов на обобщение | «Просмотреть дифф на текстовый/структурный **повтор**… Каждый найденный повтор — `Candidate`» (стр.38–39) | Рекогниция Паттерна 6 — «новое имя без ведущего подчёркивания… **независимо от того, было ли это целью фазы**» — это НЕ повтор. Кандидаты ширины контракта не сканируются вовсе |
| `apply-prompt.md` §2.3 маршрутизация | заголовок «по **П1–П6** этой LPF» (стр.64,66) | буллеты: Маршрут(П1), Формат(П2), Scope-bounding(П3), Пустой список(П4), Автомат/LLM(П5). **Буллета П6 нет** | Заголовок обещает 6, тело даёт 5. Route=maintainer для нового публичного имени в enumeration отсутствует |
| `finding-schema.json` description (стр.5) | force-форма выхода | «…по маршрутизации **П1-П5** этой LPF…» — **не тронуто** Addendum 3 | Схема выхода не требует П6-вердикта; нет поля для candidate-класса «новое публичное имя» / смены видимости |

**Почему это floor, а не shine:** исполнение стадии в `apply`-режиме `dpf-apply` = спаун агента по `apply-prompt.md` (PUR-2, `.claude/rules/frameworks.md`; предыдущая adequacy 2026-07-13 явно оценивала executability assets как часть пакета). Агент, следующий operative-инструкции §2.1 буквально («сканируй повтор»), **не породит** кандидата на новое публичное имя; §2.3 не даст ему route=maintainer-буллета; схема не потребует вердикта. Итог: **ровно тот класс отказа, ради которого Паттерн 6 добавлен (утечка публичных имён, инцидент 2026-07-14, автоматические/параллельные треки имплементации), рецидивирует под автоматическим исполнением стадии.** Capability добавлена в свод (DPF.md), но не проведена в носитель, который эту capability исполняет. Step 0 грузит §4 целиком (П6 в контексте), но explicit operative-инструкция §2.1 (duplication-only) доминирует над фоновым знанием — это и есть failure mode «detailed prompt, wrong operative scope».

Guardian-инверсия (Munger): «Через 3 месяца Паттерн 6 не сработал. Почему?» → Стадию исполнял LLM-агент по apply-prompt; он честно просканировал дифф на дубли, нашёл 0, выдал `findings: []` с N вердиктами по дублям — и пропустил 12 новых публичных имён машинерии, потому что имена — не дубли, а scan их не ищет. Схема вердикт по ним не потребовала. Мейнтейнер снова ловит руками. Это воспроизведение исходного инцидента, не гипотеза.

## 3. Подпроход формы — PFM1–PFM11 (E.4.DPF.DA:4.3a, до D-значений)

| PFM | Круг (07-13) | Круг (07-14) | Обоснование |
|---|---|---|---|
| PFM1 Front-door order | PASS | PASS | §0-report→§1→§4; не тронут. |
| PFM2 Pattern-language primacy | PASS | PASS | §4 — главный язык; П6 добавлен как полное тело, карты после. |
| PFM3 Map discoverability | PASS | PASS | §5 (строка П6→П1), §7, §9 достижимы из §4. |
| PFM4 Dependency direction | PASS | PASS | LPF→базовый ДПФ односторонняя; П6 опирается на governing patterns, reverse blocked. |
| **PFM5 Publication/access-carrier boundary** | PASS | **PARTIAL-FAIL** | Access/executable-носители (`apply-prompt.md`, `finding-schema.json`) — часть пакета — рассинхронизированы со сводом: свод несёт П6, исполнимый носитель — нет. Носитель не «стал сводом», но перестал ВЫРАЖАТЬ актуальный свод. §2 наст. |
| PFM6 Public naming | PASS | PASS | `name:` предметный; frontmatter `active`. |
| **PFM7 Development-state absence** | PASS | PASS | Process-state Паттерна 6 корректно вынесен в `quality-record` Addendum 3, НЕ в DPF.md. Residue-scan DPF.md по «Addendum\|переподтвержд\|круг\|repair» — 0. Worked slice §4 П6 «инцидент 2026-07-14» — deployment/incident-контекст (аналог git-evidence прочих паттернов), не authoring-phase/review-status residue. |
| PFM8 Cross-DPF relation discipline | PASS | PASS | §9 edition-dep + blocked reverse; П6→базовый ДПФ не заведён (П6 опирается на governing patterns, не на базовый свод — корректно). |
| PFM9 Normal-pattern maturity | PASS | PASS | П6 — полное E.8-тело (7 частей), worked slice с воспроизводимой git-evidence, контрпример+анти-паттерн+conformance+связи. SoTA-ход = governing patterns (легитимно для LPF-специализации). |
| PFM10 Access-currentness boundary | PASS | PASS | §11 refresh + «рекомендует, не сертифицирует». |
| PFM11 Carrier structure-account | PASS | PASS | §0-report актуален. |

**Итог PFM: 10 PASS, 1 PARTIAL-FAIL (PFM5).** Понижает D2/D5/D7 (см. §4).

## 4. Таблица координат D1–D11 (E.4.DPF.DA:4.2/4.3, пол = 4)

| Координата | Значение | Обоснование (почему не ниже / не выше) | Evidence-locus | Repair / no-proposal |
|---|---|---|---|---|
| D1 DomainScope | 4 | Контекст/reader/first-use/non-use остры (§1). П6 расширил домен (ширина контракта) внутри той же границы. Не 5: heterogeneous частично гипотетичен (Случай B). | DPF.md §1; §4 П6 Recognition | no-proposal |
| **D2 DidacticEntry** | **3** ↓(было 4) | Human-ground путь (чтение §4 П6) полон. Но assisting-agent через `apply-prompt.md` получает НЕПОЛНУЮ процедуру: scan §2.1 — только дубли, routing §2.3 — только П1–П5, схема не требует П6-вердикта. Агент не получит «первый рабочий результат» для capability Паттерна 6. Не 2: DPF.md-путь и step 0 (грузит §4) частично спасают. | `apply-prompt.md` §2.1/§2.3; `finding-schema.json` стр.5; §2 наст. | **REPAIR** (§6 R1) |
| D3 ScalableFormality | 4 | Staged: written→Local/Module(оркестратор)→Boundary(мейнтейнер); П6 добавил visibility-переход как Boundary. | §4 П1/П6; §9 | no-proposal |
| D4 CoreDependency | 4 | Односторонняя; П6 опирается на governing patterns (existing-code.md, A.7, main.md) — не на Core reverse. reverse blocked. | §9; §4 П6 принцип | no-proposal |
| **D5 PackageForm** | **3** ↓(было 4) | Пакет = свод + assets + references. Свод несёт П6, но executable-носители (`apply-prompt.md`, `finding-schema.json`) — нет: force-форма выхода (схема) всё ещё «П1-П5», operative-scan не ищет имена. Слои рассинхронизированы — PFM5 PARTIAL-FAIL. Не 2: рассинхрон точечный (2 файла, заголовки бампнуты), DPF.md-слой корректен. | PFM5; `finding-schema.json` стр.5; `apply-prompt.md` §2.1/§2.3 | **REPAIR** (§6 R1) |
| D6 Lexicon | 4 | §8 provisional дополнен «Гейт ширины контракта» + «имена П1–П6»; durable/provisional разведены. | §8 | no-proposal |
| **D7 PracticeUtility** | **3** ↓(было 4) | Как ПАТТЕРН в DPF.md П6 меняет действие (полное тело, worked slice). Но через apply-путь — НЕ меняет: capability не сканируется, не маршрутизируется, не требуется схемой ⇒ исходный инцидент рецидивирует под автоисполнением (§2 инверсия). Для reliance-bearing apply-use utility нового паттерна не доставлена. Не 2: human-ground-use работает. | §2 наст.; `apply-prompt.md`; `finding-schema.json` | **REPAIR** (§6 R1) |
| D8 HeterogeneousCase | 4 | Случаи A/C — реальное repo-evidence; П6 worked slice (`9fa714c`) — четвёртый реальный разнородный кейс (не дубль, а ширина контракта). Не 5: Случай B гипотетичен. | §10 A/C; §4 П6; §1 наст. | no-proposal |
| D9 EditionState | 4 | FPF edition pinned, review_due, edition-dep, refresh. Frontmatter `active`, дата 2026-07-13 — не обновлена под содержательное изменение 2026-07-14 (минорно; см. концерн 5). | frontmatter; §11 | no-proposal (концерн 5) |
| D10 Improvement/Refresh | 4 | §11 refresh-триггеры конкретны. Не добавлен триггер «дрейф governing patterns Паттерна 6» (концерн 4) — минорно. | §11 | no-proposal (концерн 4) |
| D11 DomainSoTA | 4 | П6 честно НЕ добавляет SoTA (governing patterns), §7 без строки П6 — asymmetry принята. T16/T17 — 2026, единичные (self-flagged, refresh есть). | §7; §2 Currentness; §4 П6 | no-proposal (концерн 6) |

**Три координаты ниже пола 4: D2, D5, D7** — все из одного locus (Паттерн 6 не проведён в executable-носители). Остальные 8 ≥ пола.

## 5. Вердикт по CC-DPF.1–9 (E.4.DPF:7)

| Check | 07-13 | 07-14 | Комментарий |
|---|---|---|---|
| CC-DPF.1 Context declared | PASS | PASS | §1 + scope.md; П6 в границе. |
| CC-DPF.2 Source pack present | PASS | PASS | source-pack + honest «харвест не расширялся» для П6. |
| CC-DPF.3 Architecture decision present | PASS | PASS | §3 Forces + §4 split + §5 (строка П6→П1). |
| CC-DPF.4 Names prepared | PASS | PASS | §8 дополнен П6-именами. |
| CC-DPF.5 Carriers admitted | PASS | PASS | git-evidence П6 воспроизводится (§1); admission-утверждение Carrier note истинно для П6. |
| CC-DPF.6 Patterns via E.8 | PASS | PASS | П6 — полное E.8-тело; PFM9 PASS. |
| CC-DPF.7 Quality/refresh routes | PASS | PASS | §11 + edition-триггеры. |
| CC-DPF.8 Carrier structure-account | PASS | PASS | §0-report. |
| CC-DPF.9 Problem-solving primacy | PASS | PASS | П6 называет проблему (утечка публичных имён), failure mode (ошибка №13), governing-ход. |

**CC-DPF.1–9: чистый PASS** — свод как текст конформен. Floor-breach — не в CC-DPF (это про свод), а в E.4.DPF.DA-координатах D2/D5/D7 (это про пакет как исполнимую единицу): executable-носители отстали от свода.

## 6. Статус пакета и repair-список (E.4.DPF.DA:4.5)

**`repairBeforeDPFUse`.**

Обоснование: D2/D5/D7 ниже пола 4 для reliance-bearing apply-use. Не `admissibleForDeclaredDPFUse` (три координаты ниже пола). Не `seedOnly` (свод зрелый, evidence воспроизводима, пакет прошёл 6 фаз). Не `refreshNeeded` (source/edition не менялся — дефект внутренний, не внешний дрейф). Не `holdFor*` (арх-решение settled, Core-зависимость чиста).

Дефект — **один**, точечный, минимальный ремонт (A.11), не трогает архитектуру паттернов:

**R1 (D2/D5/D7, PFM5): провести Паттерн 6 в executable-носители.**
1. `apply-prompt.md` §2.1 «Скан кандидатов» — добавить второй класс кандидата помимо повтора: «новые имена без ведущего подчёркивания (функции/методы/свойства/константы/поля конфиг-типов) и расширения сигнатур публичных функций — `Candidate` ширины контракта (П6), независимо от того, дубль это или нет».
2. `apply-prompt.md` §2.3 — добавить буллет **«Гейт ширины контракта (П6 LPF): каждое новое публичное имя → находка `route=maintainer` с `pending_human_confirmation=true`, даже если рекомендуется оставить публичным; смена видимости существующего имени (в обе стороны) — всегда Boundary»**; привести заголовок в соответствие (сейчас обещает П1–П6, тело даёт 5).
3. `finding-schema.json` — description стр.5 «маршрутизации П1-П5 этой LPF» → «П1-П6»; предусмотреть, что candidate ширины контракта проходит вердикт (минимум — снять противоречие описания; при желании — enum-поле класса кандидата `duplication | contract_width`).

После R1 — переоценить D2/D5/D7 (ожидаемо ↑4) и перевести статус в `admissibleForDeclaredDPFUse`.

**До закрытия R1 DPF.md conformance-строку и frontmatter не менять** — по заданию (шаг 7): статус НЕ `admissibleForDeclaredDPFUse` ⇒ DPF.md не трогаю, выдаю repair-список. Пакет сейчас НЕСЁТ `admissible`+`active` при отставшем executable-носителе — это состояние переоценивается R1 (концерн 5).

## 7. Remaining concerns (guardian, «повод для беспокойства» ≠ «повод остановиться»)

Концерн 1 — floor-breaking (это и есть R1, «повод остановиться»). Остальные — worry, ремонт не блокируют.

1. **[STOP / R1] Паттерн 6 не проведён в `apply-prompt.md` (scan §2.1 + routing §2.3) и `finding-schema.json` (стр.5 «П1-П5»).** Класс отказа, ради которого добавлен П6, рецидивирует под автоисполнением стадии. Ремонт — §6 R1 (3 точечные правки, архитектура не трогается).

2. **[worry] Worked slice §4 П6 — occurrence «фиксер СДЕЛАЛ публичным `_dlx_routing_key`, мейнтейнер остановил» не реконструируется из git.** В `9fa714c` — один коммит; промежуточное публичное состояние не закоммичено. Evidence = тело коммита (decision) + финальное узкое дерево (`_dlx_routing_key` приватный, строка передаётся). Драматизированный промежуток — occurrence без replayable-цепи (A.10). Круг 1 уже ловил фабрикацию цитаты — эта asymmetry заслуживает пометки. Митигация: переформулировать инстанциацию как «сужение зафиксировано коммитом `9fa714c`; финальное дерево — приватное имя + передача строкой» (наблюдаемый факт), не как реконструкцию отменённого шага.

3. **[worry] П6 вводит ОРТОГОНАЛЬНУЮ ось кандидата (ширина контракта) в дубликат-центричный фреймворк.** §1 First use, §8 операторы (`scan`/`apply_gate`), весь конвейер §2 apply построены вокруг «повтора». П6 держится на собственной Recognition, которую ни §/оператор не обобщает на «второй проход скана». Даже human-ground-путь требует, чтобы reviewer сам осознал необходимость отдельного прохода по новым публичным именам. Митигация в рамках R1 (расширить §2.1 на второй класс кандидата) закрывает и это.

4. **[worry] П6 — единственный паттерн с 0 строк SoTA-Echoing.** Честно (governing patterns, не web-SoTA) и легитимно для LPF-специализации. Но долговечность П6 держится на неизменности `existing-code.md`/A.7/`rules/python/main.md`. Митигация: добавить в §11 refresh-триггер «дрейф governing patterns Паттерна 6 (Blast Radius / underscore-правило)».

5. **[worry] Пакет несёт `active`+`admissible`-conformance при отставшем executable-носителе; frontmatter `date: 2026-07-13` не отражает содержательное изменение 2026-07-14.** До R1 conformance-строка overstates executable-готовность. Митигация: после R1 обновить conformance-строку (2026-07-14) и `date`.

6. **[worry, унаследовано] D11: T16/T17 — 2026, единичные источники без независимой реплики** (self-flagged). Не затронуто П6. Refresh-триггер §11 назван; переоценить на `review_due`.

## 8. Gate (круг 1)

**gate_passed = false.** D2/D5/D7 ниже пола 4; статус = `repairBeforeDPFUse`. DPF.md не тронут — conformance-строка от 2026-07-13 сохранена. Выдан repair-список (§6 R1). Ремонт выполнен оркестратором тем же днём — переоценка ниже, круг 2.

---

## Круг 2 (после ремонта R1, 2026-07-14, последний допустимый)

> Тот же guardian, тот же метод и пол (=4). Объект — пакет после ремонта R1: `apply-prompt.md` (двухклассовый скан §2.1 + буллет П6 §2.3), `finding-schema.json` (description «П1-П6»), DPF.md frontmatter `date: 2026-07-14` + §11 refresh-триггер «дрейф governing patterns П6».
> **Итог (спойлер): `admissibleForDeclaredDPFUse`.**

## 9. Что перепроверено запуском/чтением (A.10)

| Проверка | Результат прогона (2026-07-14, круг 2) | Вердикт |
|---|---|---|
| §2.1 двухклассовый скан | Класс А — повтор (стр.38–40); класс Б — «новое публичное имя (П6 этой LPF)»: инвентаризация имён без подчёркивания + смены видимости в обе стороны, лакмус «кто сломается», вырожденная форма гейтов явно прописана (П1 — роль имени; П2 `connascence_form: none`; П3 рёбра пустые; П5/П6 по существу) | **PASS** |
| §2.3 буллет П6 + честный заголовок | Заголовок «по П1–П6» — теперь 6 буллетов; буллет П6: каждый кандидат класса Б → находка `route: maintainer` + `pending_human_confirmation: true` ДАЖЕ при рекомендации keep-public; контрпример (имя, обещанное фичей и подтверждённое владельцем — не кандидат); публикация приватного имени ради внутреннего call-site — всегда находка (`9fa714c`) | **PASS** |
| `finding-schema.json` description | «…по маршрутизации **П1-П6** этой LPF…» — исправлено | **PASS** |
| Схема допускает П6-кандидата (вырожденная форма) | `connascence_form` enum содержит `none`; `edges_before`/`edges_after`/`removed_edges` — БЕЗ `minItems` (пустые массивы валидны); `rentability.hypotheses` `minItems: 1` — выполнимо по существу («поддержка имени навсегда» — гипотеза стоимости); `route: maintainer` и `pending_human_confirmation` — required. Вырожденная форма представима, вердикт принудителен | **PASS** |
| JSON перевалидирован | `json.load` — синтаксически валиден. Полный `Draft7Validator` недоступен офлайн (pypi-индекс не резолвится); единственное изменение со структурно валидированной версии 2026-07-13 — description-строка, которая draft-07-валидность сломать не может; допустимость П6-инстанса выведена из фактических ограничений схемы (enum/minItems/required, скрипт-проверка) | **PASS (с оговоркой, концерн 3 §12)** |
| Frontmatter `date` | `2026-07-14` — отражает содержательное изменение | **PASS** |
| §11 refresh-триггер | «дрейф governing patterns Паттерна 6 (`existing-code.md` Blast Radius, `rules/python/main.md` underscore-правило) — переоценить П6, он опирается на них, не на SoTA-харвест» — добавлен | **PASS** |
| Мысленный прогон на диффе `9fa714c` | `RetryConfig`/`RetryFlow`/`retry`/`make_test_topology` — имена, обещанные фичей и подтверждённые владельцем (тело коммита) → контрпример П6 по §2.3, НЕ кандидаты (гипер-приватизация заблокирована). Гипотетическое новое публичное имя машинерии (напр. `decide` без подчёркивания) → кандидат класса Б → вырожденные гейты → `route=maintainer`, `pending_human_confirmation=true`. Двухклассовый скан порождает П6-кандидатов; инцидент 2026-07-14 под этой процедурой был бы пойман | **PASS** |

**Инверсия круга 1 перепроверена:** сценарий «агент сканирует только дубли и пропускает 12 публичных имён» больше не воспроизводится — класс Б порождает кандидатов независимо от повтора, схема требует по ним полный вердикт с принудительной маршрутизацией.

## 10. PFM и координаты — дельта к кругу 1

**PFM:** PFM5 PARTIAL-FAIL → **PASS** (executable-носители выражают актуальный свод; рассинхрон слоёв устранён). Остальные 10 — PASS без изменений. **Итог: 11/11 PASS.**

**Координаты (пол = 4):**

| Координата | Круг 1 | Круг 2 | Обоснование |
|---|---|---|---|
| D2 DidacticEntry | 3 | **4** | Assisting-agent через apply-prompt получает полную процедуру П6: скан класса Б → вырожденные гейты → route=maintainer. Не 5: детальный формат тяжёл для первого входа (как и было). |
| D5 PackageForm | 3 | **4** | Слои синхронизированы: свод, промпт, схема несут П6 согласованно. Не 5: остаточные текстовые рассинхроны полей схемы (концерн 2 §12) — shine, не floor. |
| D7 PracticeUtility | 3 | **4** | Capability П6 доставлена на apply-путь; мысленный прогон подтверждает порождение кандидатов и блокировку обоих failure modes (утечка имён И гипер-приватизация). Не 5: телеметрии реального LLM-прогона нет (как у П1–П5). |
| D1, D3, D4, D6, D8, D9, D10, D11 | 4 | 4 | Не менялись ремонтом; D9 усилен (frontmatter date честен), D10 усилен (триггер дрейфа governing patterns). |

**Все 11 координат ≥ пола 4.** CC-DPF.1–9 — чистый PASS (не менялись, свод R1 не трогал).

## 11. Статус пакета (E.4.DPF.DA:4.5, круг 2)

**`admissibleForDeclaredDPFUse`.**

Все 11 координат ≥ пола 4 для reliance-bearing use (ground И apply); CC-DPF.1–9 PASS; PFM 11/11 PASS. Ремонт R1 — три точечные правки исполнимых носителей (A.11), архитектура паттернов не тронута, свод не менялся. Не `repairBeforeDPFUse` (floor-breach D2/D5/D7 закрыт). Не `seedOnly`/`holdFor*`/`refreshNeeded` — основания круга 1 в силе.

## 12. Remaining concerns (guardian, «повод для беспокойства», не «повод остановиться»)

1. **[worry] П6-«находка» (проза §2.3) ≠ `findings[]` (схема).** Top-level `findings` индексирует только кандидатов с `decision=generalize`; П6-кандидат берёт `keep`/`defer` (enum не имеет значения «narrow») и в `findings[]` не попадает — эскалация живёт в `candidates[].route=maintainer` + `pending_human_confirmation=true` + summary. Механические проверки оркестратора (dpf-apply, шаг проверок выхода) обязаны сканировать `candidates[]` по route/pending, не только `findings[]` — иначе П6-эскалация терминологически невидима. Митигация: зафиксировать эту проверку в SKILL.md dpf-apply при следующей правке; либо добавить в enum `decision` значение вида `narrow`.
2. **[worry, косметика] Текстовые поля схемы отстали от класса Б:** `candidate.description` — «Что за повтор обнаружен» (класс Б — не повтор); `pending_human_confirmation.description` цитирует только П5 (П6 тоже его мандатирует). Валидацию не ломает; поправить при следующей правке схемы.
3. **[worry] Полный Draft7Validator-прогон П6-инстанса не выполнен** (jsonschema недоступен офлайн). Риск низкий: структурная валидность подтверждена прогоном 2026-07-13, с тех пор изменена только description-строка; допустимость вырожденной формы выведена из фактических ограничений (enum `none`, отсутствие `minItems` на рёбрах, required-набор) скрипт-проверкой. При доступной сети — прогнать `iter_errors` на П6-примере.
4. **[worry, унаследовано из круга 1] Occurrence «фиксер сделал `_dlx_routing_key` публичным» не реконструируется из git** (один коммит, промежуток не закоммичен); evidence = decision в теле + финальное узкое дерево. Переформулировать инстанциацию при следующем refresh (концерн 2 круга 1).
5. **[worry, унаследовано] D11: T16/T17 — 2026, единичные источники; Случай B без телеметрии.** Refresh-триггеры §11 названы; переоценить на `review_due` 2026-10-13.

## 13. Gate (круг 2, итоговый)

**gate_passed = true.** CC-DPF.1–9 PASS; D1–D11 ≥ 4; PFM 11/11; статус = `admissibleForDeclaredDPFUse`. По заданию: conformance-строка в DPF.md обновлена на 2026-07-14 (строка критика 2026-07-13 заменена — история сохранена в `package-adequacy-2026-07-13.md` и этом файле); frontmatter `status: active` не тронут. История оценок: круг 1 (`repairBeforeDPFUse`, §1–§8) сохранён дословно выше; `critic-review.md`, `package-adequacy-2026-07-13.md` не переписаны.
