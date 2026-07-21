# Critic-review (Фаза 6) — DPF-COUPLING-GENERALIZATION

> Роль: **guardian** (completeness-critic + Devil's Advocate, инверсия Мангера). Дата прогона: 2026-07-10.
> Метод: FPF **E.4.DPF.DA** (координаты D1–D11 + подпроход PFM1–PFM11 + статусы) поверх CC-DPF.1–9 (E.4.DPF:7). FPF прочитан живьём (FPF-Spec.md:64878–65390).
> Оцениваемый пакет: `DPF-COUPLING-GENERALIZATION/DPF.md` (edition `f7c7e93f`, date 2026-07-10) + `references/{scope,sota-research,theses-antitheses,source-pack}.md`.
> Declared use / floor: опора ролей architect/dev/code-review → **пол = 4** (reliance-bearing), не seed-floor 3.
> Этот файл — процессное состояние Фазы 6 (PFM7): НЕ публикуется как второй пользовательский носитель, живёт в `references/`.

---

## 0. Verdict (сначала итог, PFM1)

- **CC-DPF.1–9 (E.4.DPF:7):** PASS — все секции присутствуют и содержательны.
- **E.4.DPF.DA статус пакета:** **`repairBeforeDPFUse`** — одна координата ниже пола (**D5 = 3**, PFM7 process-state leakage в пользовательском носителе); вторичные концерны на D7/D8 не ниже пола, но с repair.
- **ГЕЙТ:** `gate_passed = false`. Гейт требует CC-DPF.1–9 PASS **И** статус `admissibleForDeclaredDPFUse`. Второе условие не выполнено.
- Строка `> conformance: ... admissibleForDeclaredDPFUse` в DPF.md **НЕ дописана** (условие не наступило). Существующая финальная строка DPF.md уже честно заявляет `seedOnly` и не претендует на admissible — правки DPF.md в этом прогоне не требуется, кроме repair-шагов §5 ниже.

> Это ровно демонстрация типовой ошибки авторинга №3 (method.md): «пакет считается готовым, потому что секции CC-DPF.1–9 присутствуют». CC-присутствие PASS, но DA поверх находит D5 ниже пола. Пакет силён и близок к admissible, но как есть — не reliance-bearing.

---

## 1. Что проверено доказательством (A.10 — против weightless claims)

Guardian не принимает несущие числа DPF на веру. Прямая проверка репозитория `esb-tools` (не по названиям файлов):

| Claim в DPF.md | Проверка | Итог |
|---|---|---|
| Коммит `c0b62cb` = «refactor: общая часть pytest_plugin в core/testing» | `git log -1 c0b62cb` | ✅ subject совпадает (дата Jul 7 2026) |
| `faststream/dlx.py` +11/-8, `kombu/dlx.py` +11/-8 | `git show --numstat c0b62cb` | ✅ обе строки ровно +11/-8 |
| `core/testing/__init__.py` новый, 95 строк, вместе с `fixtures.py` | numstat | ✅ 95 + fixtures.py 81 (оба новые) |
| Новые тесты `test_core_testing`, `test_faststream_plugin_standalone`, `test_no_pytest_at_import` | numstat | ✅ 148 / 66 / 34 строк, все новые |
| `collect_rejected` в `core.testing`, оба бэкенда его вызывают | grep | ✅ `core/testing/__init__.py:91`; вызовы `kombu/dlx.py:110`, `faststream/dlx.py:96` |
| Формат DLX-отчёта теперь в одном месте | diff + grep | ✅ f-string `'DLX (rejected) messages encountered ...'` перенесён в `core/testing/__init__.py:97`, из dlx.py удалён — критерий «2 места → 1» подтверждён |
| `pyproject`: `faststream` опциональна, `kombu` обязательна | `pyproject.toml` | ✅ `kombu>=5.5.4` в main deps (стр.13), `faststream` в `[project.optional-dependencies]` (стр.22–24) |
| Line counts §10: core/middlewares 88, core/system_middlewares 150, kombu/middlewares 387, faststream/middlewares 222 | `wc -l` | ✅ все четыре ТОЧНО совпадают |
| `imports.md` инвариант (в) «core не импортирует backends» | grep | ✅ дословно (imports.md:65) |

**Вывод по evidence-графу:** несущий worked-slice (§4/§10) полностью заземлён на реальный код и git, ни одно число не выдумано. Это сильный аргумент ЗА D7/D11/D8. Единственная мелкая вольность прозы — §4 Паттерн 3 «чистый прирост в бэкендах — только 2-строчный импорт»: фактический net = +3 строки (11−8); numstat процитирован верно, но словесная глосса чуть занижает. Не ниже пола, см. repair R4.

---

## 2. Упущенное (checklist критика: традиция / тензия / claim без источника / голая частность / контрпример)

- **Упущенная традиция?** Нет значимой. `FamilyCoverageFloorK=3` перевыполнен (9 традиций T1–T9), независимость обоснована (§0 sota-research), инструменты (dependency-cruiser/jscpd) корректно вынесены как Operator, не Tradition. Возможный кандидат на будущее — эмпирика code-review bias под fluency-гипотезу (№10) — сам пакет честно помечает это открытым provenance-вопросом. Не дефект.
- **Непокрытая тензия?** Нет. §3 Forces (6 осей) покрывает счётчик-vs-роль, срочность-vs-прогноз, DRY-vs-автономия, стабильность-vs-стартовый-тупик, AI-baseline. Конфликты T4↔T5, T7↔T8, SDP↔T5 зафиксированы как `conflict`, не слиты молча (проверено в theses-antitheses §1 типы связи).
- **Claim без источника?** Не найдено. Каждый несущий claim в §7 SoTA-Echoing имеет ref+статус (`fact`/`hypothesis`/`opinion`). Прогнозные величины (volatility, likely-change) явно помечены гипотезами (№7, §6).
- **Голая частность без принципа (A.1.1 leak)?** Не найдено. Каждый worked slice в §4 предварён SoTA-принципом (порядок «принцип → инстанциация» соблюдён во всех 6 паттернах).
- **Нет контрпримера?** Есть у всех 6 паттернов (A.11 Sharp Boundary), плюс 6 отдельных КП в theses-antitheses §2. Сильно.
- **Голый счётчик дуг как критерий (риск E.4.DPF:8 Checklist-promoted-to-framework)?** Пакет СОЗНАТЕЛЬНО избежал этого: критерий графа (заявленная в брифе компетенция «граф связей до/после») понижен до «необходимой, но недостаточной базы» (§4 П3, retired premise №1), паттерны ведут с role-first стоп-гейта (П1). Это главная сила пакета и прямой ответ на guardian-концерн 4 theses-antitheses. НЕ дефект — наоборот.

---

## 3. PFM-подпроход (E.4.DPF.DA:4.3a) — форма пакета ДО координат

| PFM | Условие | Диспозиция | Затрагивает |
|---|---|---|---|
| PFM1 Front-door order | ToC/readme/preface до паттернов; первый паттерн выбирается без чтения аппарата | **PASS (слабый)** — §0 структурный отчёт направляет в §4 П1→П6; но **отдельного индекса паттернов/ToC нет**, файл плотный (54 КБ) | D2, D5 |
| PFM2 Pattern-language primacy | паттерны — главный язык; тяжёлые карты после них | **PASS** — §4 паттерны; §5–7 таблицы и references ПОСЛЕ; провенанс в references | D2, D5, D7 |
| PFM3 Map discoverability | у каждой карты живой маршрут входа | **PASS** — references слинкованы из §2/§9, «Связи» паттернов ведут к §5 | D2, D5, D10 |
| PFM4 Dependency direction | DPF цитирует Core, не наоборот | **PASS** — §9 specialization existing-code/imports/box-stores; Core не зависит от DPF | D4, D5, D9 |
| PFM5 Publication/access boundary | носитель ≠ архитектура/quality/process | **PASS** — §9 явно: DPF.md единственный access carrier, references = process state | D5, D9 |
| PFM6 Public package naming | доменное имя, не file-slang; статус во frontmatter | **PASS (слабый)** — заголовок ведёт ID-сленгом `DPF-COUPLING-GENERALIZATION`, доменная фраза «Упрощение через обобщение» присутствует подзаголовком; `stage-0` во frontmatter | D1, D2, D5, D6, D9 |
| **PFM7 Development-state absence** | нет draft/DRR/handoff/review-status/process-run остатка; допустима 1 conformance-строка | **FAIL** — см. §3.1 ниже | **D5**, D9, D10 |
| PFM8 Cross-DPF relation discipline | ссылки на др. DPF как типизированная связь | **N/A** — первый DPF в каталоге, внешних DPF нет; §9 фиксирует отсутствие competency-map честно | D4, D5, D9 |
| PFM9 Normal-pattern maturity | каждый паттерн — полноценное E.8-тело | **PASS** — 6 паттернов, полный блок (recognition/принцип/инстанциация/контрпример/анти-паттерн/conformance/связи) | D2, D7, D8, D11 |
| PFM10 Access-currentness boundary | скилл/MCP экспонируют edition/refresh | **N/A** — нет skill/MCP access carrier (только файл) | D2, D5, D9, D10 |
| PFM11 Carrier structure-account | readme даёт structure-account: что экспонирует, что огрублено, куда возврат | **PASS** — §0 header: для кого, передний план (§4), сознательно огрублено (T1–T9, bridge, провенанс → references), почему нет чисел-порогов | D1, D2, D5, D7, D8, D10, D11 |

### 3.1 PFM7 FAIL — детально (evidence-locus)

Пользовательский носитель `DPF.md` несёт процессно-прогонное состояние сверх допустимой одной conformance-строки (method.md: «в DPF.md нет процессного состояния... Допустима одна финальная conformance-строка»; E.4.DPF.DA:8 anti-pattern «Process-state leakage»; drift-3 «quality proof leakage»):

1. **Секция «Conformance checklist (E.4.DPF:7)» целиком** (DPF.md:199–209) — 9 пунктов `[x]` с поштучной атрибуцией прогона «эта сборка (Фаза 4–5)», «порядок П1→П6 обоснован guardian-концерном 4» и т.п. Это ревью-транскрипт/quality-proof, место которому в `references/`, не в носителе.
2. **Буллет «Локальный гейт этого прогона (Фазы 4–5, не подменяет E.4.DPF.DA)»** (DPF.md:184) — self-review прогона (скелет полон — да; ≥4 паттерна — да…). Явное review-run состояние.
3. **Рассеянная run-фразеология** «в этом прогоне» / «Фазы 0–5 пройдены» / «получено... в рамках этого прогона» — §5 Паттерн 5 (в теле паттерна, стр.98), Carrier note (стр.197 ×2). В теле паттерна (стр.98) это ещё и drift-3: quality-proof просочился в user-facing прозу паттерна.

**Что НЕ является leakage (не штрафую):** §0 header status-line `stage-0 = seedOnly` и §11 статус-декларация — это САНКЦИОНИРОВАННЫЙ честный статус пакета (template-dpf.md прямо: «НЕ процессное состояние, а честный статус»; CC-DPFDA.8 требует seed-honesty В носителе). Финальная conformance-строка (DPF.md:211) — допустимая одна строка.

**Почему ниже пола, а не «повод для беспокойства»:** E.4.DPF.DA:4.3a — «A failure in this subpass lowers the affected coordinate even when individual pattern bodies pass E.21». Это не одна случайная строка, а целая секция + буллет + просачивание в тело паттерна. Для reliance-floor 4 (D5 = «records separated») quality/process-записи НЕ отделены от носителя. Это `povод остановиться` до reliance-использования, но дёшево чинится (R1).

---

## 4. Таблица координат D1–D11 (E.4.DPF.DA:4.3) — пол = 4

> Каждая строка: значение | обоснование (почему не ниже / почему не выше) | evidence-locus | repair.
> Средним баллом паттернов НЕ подменяется (CC-DPFDA.4): оценивается пакет как целое.

| Coord | V | ShortRationale (почему не ниже / не выше) | EvidenceLocus | Repair / no-proposal |
|---|---|---|---|---|
| **D1** DomainScope&Use | **5** | Reader/first-use/non-use-boundary остры и разведены; non-use явно отделяет DPF от existing-code.md/imports.md (специализация, не замена). Ниже — занизило бы (границы конкретны); 5 держится, т.к. scope.md добавляет полный текст. | §1 + `scope.md` | — |
| **D2** DidacticEntry&Adoption | **4** | Header направляет в §4, паттерны action-guiding, примеры конкретны. Не 5: нет отдельного индекса паттернов/ToC (PFM1 слабый), файл 54 КБ плотный — холодный reader входит только через §0-абзац. | §0 header; §4; PFM1 | R2: добавить короткий индекс П1–П6 (id + one-line recognition) в начало §4 |
| **D3** ScalableFormality | **4** | Стадийность есть: plain-принцип → conformance-строка паттерна → структурный enforcement (`test_architecture.py`) → references. Не выше: явной лестницы «local→typed→assured» как таковой нет, выводится. | §4 conformance-строки; §8 | — |
| **D4** CoreDependency&Boundary | **5** | Specializes existing-code/imports/box-stores, не переопределяет; Core от DPF не зависит; must-NOT-land явный. PFM4 PASS. | §9; §1 non-use | — |
| **D5** PackageForm Layering&Relation | **3** | references отлично отделены (scope/sota/bridge/source-pack) — это тянет к 5. НО PFM7 FAIL: CC-checklist + self-gate-буллет + run-фразеология в user-носителе = quality/process-записи НЕ отделены. Для reliance-floor 4 это ниже пола. Не 2: сепарация в остальном образцовая, дефект узкий и локализованный. | DPF.md:184, 197, 199–209; §3.1 выше | **R1 (несущий):** перенести CC-DPF.1–9 checklist + буллет «Локальный гейт этого прогона» в этот `critic-review.md`; убрать «в этом прогоне» из тела §5 Паттерн 5; оставить §0 status + одну финальную conformance-строку |
| **D6** Lexicon&Kind | **4** | §8 durable/provisional разведены, governing pattern назван (existing-code/A.7, A.1.1/Evans); kind=DPF во frontmatter. Не 5: provisional-имена (CouplingEdge и пр.) без F.18-candidate-comparison (сам DPF это признаёт). | §8 | — |
| **D7** PracticeUtility&Resolution | **4** | Паттерны решают реальное «обобщать/не обобщать», worked-slice заземлён (§1 проверка). Не 5: §5 Паттерн 5 заявляет open-вопрос bounded-context «**закрыт** evidence» на пакетинг-факте (pyproject-опциональность) + «инвариант не нарушен» — это collapsed scope (техническая зависимость → доменная семантика; absence-of-violation ≠ proof). source-pack сам держал вопрос ОТКРЫТЫМ. | §4 Паттерн 5 (стр.98); ср. source-pack §«открытые provenance-вопросы» | **R3:** смягчить «закрыт evidence» → «evidence склоняет к единому контексту (общий контракт core.box/core.middlewares — доменное, pyproject-опциональность — техническое); переоткрывается, если faststream перестанет быть опциональной / появится domain.md с явной границей» |
| **D8** HeterogeneousCase&Transfer | **4** | 3 кейса + мотивирующий, разные ПО ИСХОДУ (greenlight / stop-at-interface / stop-mid-runtime / org-level). Не 5: Случай C честно НЕ evidence репозитория (перенесённая SoTA-иллюстрация); реально завершённое кодовое обобщение — единственное (commit c0b62cb); A и B — «остановленные/частичные», и оба несут близкий урок «П4/П6 стопят». Трансфер-доказательность тонка, но кейсы честно размечены. | §10 Случаи A/B/C | R5: при появлении второго реально завершённого кросс-модульного обобщения — добавить как Случай D; пока пометить в §10, что завершённое кодовое evidence одно |
| **D9** EditionState&Currentness | **4** | frontmatter edition/review_due, §2 currentness по T1–T9, §11 refresh-триггеры. Не 5: та же PFM7 run-резидуальность слегка размывает «durable package content» (вторичный эффект D5). | frontmatter; §2; §11 | наследует R1 |
| **D10** Improvement&Refresh | **4** | §11 refresh-триггеры конкретны и actionable (смена FPF-edition; 2-й источник по T9; смена причины subtree-isolation; появление domain.md/competency-map). Не 5: улучшение-route не отделён явно от refresh, но выводим. | §11 | — |
| **D11** DomainSoTAAlignment | **4** | Источники РЕАЛЬНО меняют контент: role-first понижает граф-счётчик, T9 заперт в каталоге ошибок (не нормативный тезис), retired premises зафиксированы. Не 5: T8 (2024) без независимой валидации и T9 single-source — потолок обобщаемости честно ограничен самим пакетом. | §7; §2 claim-status; retired premises | R6 (refresh): при 2-м независимом количественном источнике по T9 — переоценить каталог №9–12 |

**Пол-нарушение:** D5 = 3 < 4. Все прочие ≥ 4. → статус `repairBeforeDPFUse` (E.4.DPF.DA:4.5: «one or more coordinates below floor»).

---

## 5. Наименьшие правки (repair-шаги, от несущего к косметике)

- **R1 (несущий, снимает D5<пол).** Убрать из `DPF.md` процессно-прогонное состояние (PFM7): (а) секцию «Conformance checklist (E.4.DPF:7)» (стр.199–209) перенести в этот `critic-review.md` как приложение; (б) буллет «Локальный гейт этого прогона (Фазы 4–5…)» (стр.184) — сюда же; (в) в теле §5 Паттерн 5 (стр.98) убрать «собранным в этом прогоне» (оставить факт evidence без прогонной атрибуции). Сохранить §0 status-line и одну финальную conformance-строку. После R1 D5 → 4, статус → кандидат в `admissibleForDeclaredDPFUse` (при отсутствии новых находок).
- **R3 (D7).** §5 Паттерн 5: заменить «открытый вопрос… **закрыт** evidence» на «evidence склоняет к единому контексту» + явное reopen-условие. Снимает collapsed-scope over-claim.
- **R2 (D2).** Короткий индекс паттернов П1–П6 (id + one-line recognition) в начале §4.
- **R4 (точность).** §4 Паттерн 3: «чистый прирост… только 2-строчный импорт» → «numstat +11/−8 (net +3): +2 импорт, остальное — замена цикла на вызов».
- **R5 (D8, при появлении evidence).** Второй завершённый кросс-модульный кейс → Случай D; до тех пор пометить в §10 единственность завершённого кодового evidence.
- **R6 (refresh).** Триггер уже есть в §11 (2-й источник по T9) — оставить.

R1 — единственный, требуемый для снятия пол-нарушения. R2–R6 — улучшения/честность, не блокеры.

---

## 6. Guardian-концерны (мин. 3, инверсия Мангера) + митигация

1. **[повод остановиться до reliance] Process-state leakage (D5).** Как провалится: роль обопрётся на DPF как на reliance-свод, а в носителе — ревью-транскрипт прошлого прогона; при следующем прогоне checklist устареет и будет вводить в заблуждение (temporal ambiguity). *Митигация: R1.*
2. **[повод для беспокойства] Over-claim «закрыт» в Паттерне 5 (D7).** Как провалится: architect прочитает «bounded-context вопрос закрыт» и обобщит через границу faststream/kombu на основании пакетинг-факта; если faststream-транспорт разойдётся с kombu по доменной роли — получит синхронные конфликты (ровно ошибка №6 собственного каталога). Absence-of-invariant-violation ≠ proof-of-single-context. *Митигация: R3 (смягчить + reopen-условие).*
3. **[повод для беспокойства] Тонкое трансфер-доказательство (D8).** Как провалится: единственное завершённое кодовое обобщение (dlx→core.testing) — маленькое (2 файла, формат-строка); паттерны могут не масштабироваться на крупное обобщение с сильной connascence of algorithm через много модулей — не проверено. Случай C — не evidence проекта. *Митигация: R5 + честная пометка единственности.*
4. **[инверсия: как провалится через год]** Самый вероятный сценарий (совпадает с guardian-концерном 4 из theses-antitheses и E.4.DPF:8 «Checklist promoted to framework»): DPF применят механически как «посчитай дуги → обобщай». *Уже смягчено самим пакетом:* role-first П1 ведёт, граф понижен до недостаточной базы, §6 №1 бьёт по этому симптому. Остаточный риск низкий — это сила пакета, не дефект.
5. **[повод для беспокойства, второго порядка] T8/T9 свежесть.** Balance-формула (2024) и GitClear (single-source) — самые слабые по валидации звенья; если T8 не воспроизведётся, П6 (рентабельность) теряет операциональную опору. *Митигация: уже в §11 refresh-триггерах + claim-status `hypothesis`. Достаточно.*

---

## 7. CC-DPF.1–9 вердикт (E.4.DPF:7) — присутствие секций

| CC | Условие | Вердикт |
|---|---|---|
| CC-DPF.1 Context | PASS (§1 + scope.md) |
| CC-DPF.2 Source pack | PASS (source-pack.md: adopted/rejected/claim-status/currentness по каждому) |
| CC-DPF.3 Architecture decision | PASS (purpose §1, split §4, deps §9, must-NOT-land §1; компрессированная PFAD в сборке — допустимо методом) |
| CC-DPF.4 Names | PASS (§8 durable/provisional) |
| CC-DPF.5 Carriers admitted | PASS (git-evidence + FPF читаны живьём, не generated-authority) |
| CC-DPF.6 Patterns via E.8 | PASS (6 полных паттернов + §5 связи + §6 ошибки + §7 SoTA-echoing) |
| CC-DPF.7 Quality&refresh | PASS (§11; честно помечено, что E.4.DPF.DA не выполнена авторами) |
| CC-DPF.8 Structure-account | PASS (§0 header) |
| CC-DPF.9 Problem-solving primacy | PASS (§4/§6 задачи+провалы+SoTA-ходы; имена вторичны) |

**CC-DPF.1–9 = PASS.** Но (типовая ошибка №3) присутствие секций ≠ адекватность пакета: E.4.DPF.DA даёт D5 ниже пола.

---

## 8. Статус пакета и гейт

- **Статус (E.4.DPF.DA:4.5):** `repairBeforeDPFUse` — D5 ниже пола 4 (PFM7), с наименьшим repair R1. Не `seedOnly`: пакет содержательно много выше заготовки (проверенный evidence, 9 традиций, 6 паттернов) — честнее назвать конкретный repair, чем «seed». Не `admissibleForDeclaredDPFUse`: до R1 нельзя.
- **ГЕЙТ:** `gate_passed = false`.
- **После R1** (и желательно R3): повторная проверка ожидаемо даст все координаты ≥ 4 → `admissibleForDeclaredDPFUse`. Оценка R1 как достаточного — прогноз (A.10), требует повторного прогона guardian, не самоподтверждения.

---

## Приложение A — куда переносится процессное состояние по R1

(Место для секции «Conformance checklist» и буллета «Локальный гейт этого прогона» из DPF.md после применения R1 — чтобы информация не потерялась, existing-code.md guard «не убирать информацию».)

- CC-DPF.1–9 присутствие: см. §7 выше (дублирует то, что было в DPF.md:199–211).
- Локальный self-гейт Фаз 4–5 (скелет полон; ≥4 паттерна — 6; SoTA-echoing 9 строк; 3 разнородных кейса): зафиксирован здесь как исторический факт прогона сборки 2026-07-10.
