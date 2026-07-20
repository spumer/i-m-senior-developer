---
dpf_id: "DPF-ADVERSARIAL-REVIEW"
name: "Адверсарная проверка пакетов знаний"
kind: "Local Practice Framework"
owner: ["guardian"]
referenced_by: ["facilitator", "keeper"]
status: "active"
maturity: "conformant"
edition: "1.0"
grounded_in: ["FPF E.4.DPF", "FPF E.4.DPF.DA", "FPF E.4.PFR", "FPF G.2", "FPF E.8", "FPF A.2.6", "FPF B.5.2.1", "FPF A.10", "FPF A.11", "FPF A.7", "FPF A.1.1", "FPF F.18", "FPF G.11", "DEC-003"]
fpf_edition: "ailev/FPF@f7c7e93f (снимок 2026-07-03; локальная копия ~/.claude/knowledge/fpf/FPF-Spec.md обновлена 2026-07-06)"
date: "2026-07-06"
review_due: "2026-10-06"
---

# DPF-ADVERSARIAL-REVIEW: Адверсарная проверка пакетов знаний

> Компетенция: диалектика + критика + оценка адекватности ПАКЕТА знаний (свода принципов, DPF) на двух точках метода авторинга `DPF-AUTHORING` — Фаза 2 (Bridge) и Фаза 6 (Critic/package adequacy). Owner — guardian.
> **Особый класс носителя:** это **встроенный пакет ролей** скилла `dpf-authoring` (формат framework-apply: `DPF.md` + `apply-prompt.md`), не позиция таблицы `competency-map.md` (33 DPF) — access carrier для Фаз 2/6 метода на ЛЮБОМ авторимом DPF проекта (см. `DPF-AUTHORING/DPF.md` §Access carriers). Отсутствие в таблице 33 — не пробел.
> **FPF читать живьём** (не по памяти, не выжимки) через Grep по `~/.claude/knowledge/fpf/FPF-Spec.md`. Метод и фазы — `DPF-AUTHORING/DPF.md`.

---

## Оглавление (PFM1 — паттерны первым делом)

1. [Паттерны](#4-паттерны-e8-cc-dpf6) — Role-separation-gate · DI≠DA · Falsifiability-gate · Package-adequacy protocol · Anti-sycophancy discipline · Knowledge distribution
2. [Контекст](#1-контекст-cc-dpf1) · [Source Pack](#2-source-pack--g2-cc-dpf2) · [Forces](#3-forces--тензии-e4dpf3-scoped)
3. [Связи паттернов](#5-связи-паттернов-e4pfr) · [Типовые ошибки](#6-типовые-ошибки-e4dpf8) · [SoTA-Echoing](#7-sota-echoing-e4dpf11)
4. [Имена](#8-имена--f18-cc-dpf4) · [Relations](#9-relations-e4pfr) · [Quality & Refresh](#11-quality--refresh-e4dpfdae21g11-cc-dpf7)
5. [Разнородные приёмочные случаи](#10-разнородные-приёмочные-случаи-d8)
6. [Артефакты](#артефакты-каталога-references) · [Carrier note](#carrier-note-cc-dpf5) · [Conformance checklist](#conformance-checklist-e4dpf7)

---

## 0. Структурный отчёт носителя (CC-DPF.8 / PFM11)

- **Для кого файл и первая задача:** guardian, выполняющий Фазу 2 (Bridge) или Фазу 6 (Critic/package adequacy) конвейера `dpf-authoring-pipeline` для ЛЮБОГО DPF в каталоге проекта; первая задача — распознать, какой из 6 паттернов (роль-разделение / DI-vs-DA / фальсифицируемость / протокол адекватности / anti-sycophancy / knowledge distribution) применить к конкретной точке прогона. Вторично — facilitator (гейтит проход Фазы 6) и keeper (держит формат носителя, эту сборку).
- **Что на переднем плане:** 6 обогащённых паттернов (Sec 4) — главный язык носителя; каталог из 10 типовых ошибок компетенции (Sec 6, включая 5 AI-специфичных); честный статус пакета (D1–D11 не подменяется чек-листом присутствия секций, CC-DPFDA.4).
- **Что сознательно огрублено/опущено:** полный BridgeMatrix (5 традиций × 4 оси) и все 6 тезисов с NQD≥3 антитезисами и типом связи — в `references/theses-antitheses.md`, здесь только сведённые паттерны; полный CorpusLedger/ClaimSheets (14 источников) — в `references/sota-research.md`; провенанс-решения по каждому источнику — в `references/source-pack.md`.
- **Куда возврат за деталями:** `references/scope.md` (Фаза 0), `references/sota-research.md` (Фаза 1, G.2), `references/theses-antitheses.md` (Фаза 2, BridgeMatrix+тезисы+контрпримеры+каталог ошибок), `references/source-pack.md` (Фаза 3, provenance-решения); `references/critic-review.md` (Фаза 6, package-adequacy этого же пакета — прогнана независимо 2026-07-06, статус admissible, см. Conformance).

---

## 1. Контекст (CC-DPF.1)

- **Bounded context (A.1.1):** функция внутри метода авторинга сводов знаний (`DPF-AUTHORING`, FPF E.4.DPF × G.2) — адверсарная проверка ПАКЕТА (свода принципов), не продукта и не кода. Guardian применяет дисциплину «devil's advocate + completeness-critic», структурно отделённую от исследовательской роли (owner делает research, guardian оспаривает — DEC-003, против «AI-consensus = evidence»).
- **Intended reader:** guardian (owner). Вторично — facilitator, keeper.
- **First use:** на вход — `sota-research.md` (Фаза 1) авторимого DPF; на выход — `theses-antitheses.md` (Фаза 2: BridgeMatrix + тезис/анти-тезис + контрпримеры + каталог ошибок) и `package-adequacy-<date>.md` (Фаза 6: D1–D11 + PFM-подпроход + статус + repair-шаги).
- **Non-use boundary (A.11):** НЕ security-аудит продукт-кода/OWASP (→ `DPF-SECURITY-REVIEW`); НЕ риск-менеджмент проекта/kill-criteria/pre-mortem бизнес-решений (→ `DPF-RISK`); НЕ генерация исходного ресёрча/SoTA-харвест (→ Фаза 1, обычно owner); НЕ сборка DPF.md (Фаза 5, → `DPF-KNOWLEDGE-CURATION`); НЕ Decider Protocol/голосование по бизнес-тензиям (→ facilitator). Похоже, но не то же: обычный code review (код против спеки) — здесь предмет — свод принципов против SoTA, не код против ARCH.

---

## 2. Source Pack — G.2 (CC-DPF.2)

> Полный реестр provenance — [`references/source-pack.md`](references/source-pack.md). SoTA-харвест — [`references/sota-research.md`](references/sota-research.md). Ниже — сводка.

- **Adopted:** 5 независимо верифицированных традиций (FamilyCoverageFloorK=3 пройден с запасом) — (i) интеллект-анализ/Structured Analytic Techniques [Heuer & Pherson 2014/2020]; (ii) групповое принятие решений/dialectical inquiry [Mason & Mitroff 1981; Schweiger et al. 1986; Schwenk 1984; Janis 1972]; (iii) философия науки/фальсификационизм [Popper 1963]; (iv) систематический обзор/SE-peer-review [PRISMA 2020; AMSTAR 2 2017; Sadowski et al. 2018; Yang et al. 2026]; (v) ИИ-специфика self-critique/red-team/sycophancy [Bai et al. (Constitutional AI) 2022; Ding 2026-07-10; Noshin & Sultana 2026-03-22; Purpura et al. 2025]. 14 ClaimSheets с evidence-anchor+trust-cue; 9 MicroExamples; Operator/Object inventory (9 объектов, 11 операторов-заготовок). DEC-003 (owner≠guardian≠keeper по агентам) — прямой enforcement-механизм против self-agreement illusion.
- **Rejected/Park:** источник #14 (DeepTeam/LLMFuzzer/Auto-RT) — **park**: домен jailbreak-фаззинга прод-LLM не совпадает буквально с доменом ревью текстовых пакетов знаний; переиспользован только паттерн attacker/defender loop. `project/domain.md` (все 8 блоков) и 7 из 8 DEC — explicit rejected целиком: доменный/процессный контент продукта, вне non-use boundary.
- **Claim status:** демаркация Поппера, эмпирика DI/DA>consensus (Schweiger 1986), PRISMA/AMSTAR 2, knowledge distribution (Sadowski 2018) — **fact** (strong trust-cue, институционализированные стандарты/крупная эмпирика). Self-consistency≠correctness (Ding 2026) и sycophantic softening (Noshin 2026) — **fact направления, hypothesis точных цифр**: единственные авторы, свежие препринты (medium trust-cue), но согласуются с более широким корпусом.
- **Currentness:** харвест 2026-07-06; Ding — препринт 2026-07-10 (4 дня на момент харвеста, максимально decay-чувствителен); Purpura — 2025, качественный вывод (деградация защит устаревает) устойчив, точная цифра >90% — методологически варьируется. review_due 2026-10-06 (см. Sec 11 — ранний refresh-триггер для Ding/Noshin отдельно).

---

## 3. Forces / тензии (E.4.DPF:3, scoped)

> Источник полного bridge-анализа — `references/theses-antitheses.md` (BridgeMatrix + 6 тезисов).

| # | Тензион | Scope | Как разрешается |
|---|---------|-------|------------------|
| F-1 | Оппозиция встроена по конструкции (роль/альтернатива/фальсификатор/протокол/раздельный проход) **vs** оставлена автору идеи | Любая точка метода, где claim/пакет проверяется | 5 разных локусов (BridgeMatrix Alignment); «автор сам поправит» не считается сигналом надёжности ни в одной из 5 традиций |
| F-2 | Dialectical Inquiry (альтернатива с нуля, ДО сборки) **vs** Devil's Advocacy (атака готового, ПОСЛЕ сборки) | Фаза 2 (DI) vs Фаза 6 (DA) одного и того же метода | Держать оба режима явно раздельными, не сливать в одно «покритиковать» (Тезис 1, BridgeMatrix Divergence) |
| F-3 | Качество структурированной оппозиции **vs** её социальная цена (сопротивление, меньшая лояльность команды) | Назначение guardian на Фазу 2/6 | Цена — форс (trade-off), не баг; устранять оппозицию ради комфорта = путь в groupthink (Тезис 2) |
| F-4 | Дешевизна LLM-генерации критики **vs** риск иллюзии оппозиции без реальной оппозиции | Одна сессия делает research+bridge+critic вместо раздельных агентов | role-separation-gate (DEC-003): owner≠guardian≠keeper по агентам, необходимое, но не достаточное условие (Тезис 6) |
| F-5 | Формальный протокол D1–D11 (PRISMA/AMSTAR-класс) **vs** «на глаз»-впечатление или чек-лист присутствия секций | Фаза 6 — оценка адекватности пакета целиком | PRISMA-класс воспроизводимый протокол; статус ≠ средний балл паттернов (CC-DPFDA.4) (Тезис 4) |
| F-6 | Фиксированный каталог типовых ошибок/контрпримеров **vs** его моральное устаревание (static-checklist decay) | Каталог ошибок этой компетенции (Sec 6) и любого авторимого DPF | Refresh-триггеры G.11: адаптивный каталог, не статичный навсегда (Purpura et al. 2025 — деградация фиксированных защит) |

---

## 4. Паттерны (E.8, CC-DPF.6)

> Правило (A.1.1 / DPF-AUTHORING Паттерн 2): **общий принцип (SoTA) → наша инстанциация (worked slice)**. Голых частностей без предшествующего принципа нет.

---

### Паттерн 1: Role-separation-gate против self-agreement illusion

**Recognition** — когда одна и та же LLM-сессия/агент готовится делать research И bridge И critic одного пакета; когда «согласие проходов между собой» готовятся принять за проверку.

**Принцип (SoTA-grounded).** Согласие модели с собой (self-consistency) и между моделями (cross-model agreement) — ненадёжный сигнал корректности: модели могут согласованно ошибаться из-за общего смещения или заученной эвристики [Ding, arXiv:2607.08065, 2026-07-10]. Self-critique — рабочий инженерный паттерн (Critique→Revision), но précisement потому что критик и автор — РАЗНЫЕ проходы с разными системными промптами/весами, а не одна недифференцированная сессия [Bai et al. (Constitutional AI), arXiv:2212.08073, 2022].

**Наша инстанциация (worked slice).** DEC-003: модель каждого dispatch задаётся явно по сложности фазы, роли разделены по агентам (owner ≠ guardian ≠ keeper); в pipeline метода Bridge/Critic-фазы получают отдельный `agent()`-dispatch с текстом роли `DPF-ADVERSARIAL-REVIEW`, инжектированным через `roleOf()`, а не однострочное «ты теперь критик» внутри той же сессии.

**Контрпример [A.11 Sharp Boundary].** Несколько прогонов одной модели (или несколько разных LLM), которые совпали во мнении — ВЫГЛЯДИТ как независимая проверка (NQD ≥3), но НЕ является ей: это согласованность вычислительных носителей, возможно с общим смещением, а не множественность независимых традиций/источников. Тест: «различаются ли эпистемические источники, или только вычислительные носители одного смещения?»

**Анти-паттерн [E.8].** «Одна сессия сама сгенерила research, сама написала bridge, сама же себя критикнула» — self-agreement illusion; или «разделили owner и guardian по агентам — self-agreement устранён, можно расслабиться» (разделение необходимо, но НЕ достаточно: общий pretrain-bias и sycophancy остаются, Паттерн 5).

**Conformance.** Фаза 2 (Bridge) и Фаза 6 (Critic) — отдельные `agent()`-вызовы с разным prompt-текстом; если один агент/сессия выполнил research+bridge+critic — BLOCK, requeue с разделением.

**Связи [E.4.PFR].** **requires** DEC-003 (role separation по агентам); **composes** с Паттерном 5 (анти-sycophancy — необходимое дополнение, разделение проходов само по себе не гасит sycophantic softening); **conflicts** с «AI-consensus = evidence».

---

### Паттерн 2: Dialectical Inquiry (Фаза 2) ≠ Devil's Advocacy (Фаза 6) — два разных механизма, оба нужны

**Recognition** — строится BridgeMatrix пакета (ДО сборки DPF.md) ИЛИ критикуется уже собранный DPF.md (ПОСЛЕ сборки).

**Принцип (SoTA-grounded).** Dialectical Inquiry — две (или более) конкурирующие альтернативы формулируются с нуля и формально сравниваются, а не одна идея критикуется постфактум [Mason & Mitroff, AMR 1981]. Devil's Advocacy — назначенный голос строит наилучший возможный контраргумент против уже готового суждения [Heuer & Pherson, SATfIA 2014/2020]. Лабораторная эмпирика: оба режима дают решения лучше consensus; DI лучше DA именно по вскрытию скрытых допущений, потому что альтернатива не привязана к защите исходной идеи [Schweiger, Sandberg, Ragan, AMJ 1986, pp.51–71].

**Наша инстанциация (worked slice).** Фаза 2 метода = DI: `theses-antitheses.md` строит BridgeMatrix пяти традиций с нуля, ДО того как DPF.md существует (research-first гейт DPF-AUTHORING). Фаза 6 = DA: guardian атакует уже собранный DPF.md наилучшим возможным контраргументом через D1–D11.

**Контрпример [A.11 Sharp Boundary].** Считать оба режима «просто покритиковать» и слить их в одну метрику — контрпример границы: коллапс 5 разных локусов оппозиции (роль/альтернатива/claim-свойство/протокол/проход) BridgeMatrix Divergence в одну недифференцированную критику; тест: «на каком этапе я нахожусь — альтернатива строится с нуля, или уже существующий пакет атакуется?»

**Анти-паттерн [E.8].** «Хватит одного режима, зачем ещё и BridgeMatrix» — пропуск DI-фазы: DA привязан к защите/атаке уже готовой идеи, системно вскрывает МЕНЬШЕ скрытых допущений, чем DI, где альтернатива не привязана к исходной идее. Пропуск режима — не экономия, а слепое пятно (первый-hour-route допускает грубое исполнение обоих, не отсутствие одного из них).

**Conformance.** В каталоге DPF присутствуют оба артефакта: `theses-antitheses.md` (DI, до сборки) И `package-adequacy-<date>.md` (DA, после сборки) — структурно и датированно различимые, не один смешанный документ.

**Связи [E.4.PFR].** **scope-dependent** (DI и DA активны на разных фазах, не одновременно); **composes** с Паттерном 4 (оба режима протоколируются через D1–D11); **conflicts** с error №2 (Sec 6, коллапс локусов оппозиции).

---

### Паттерн 3: Falsifiability-gate (Popper) — claim без потенциального фальсификатора не годится как несущий

**Recognition** — claim добавляется в source-pack пакета или формулируется как тезис Фазы 2.

**Принцип (SoTA-grounded).** Утверждение годится как знание, только если у него есть потенциальный фальсификатор — условие/наблюдение, при котором оно было бы опровергнуто; знание растёт через конъектуры и опровержения, не через накопление подтверждений [Popper, *Conjectures and Refutations*, 1963].

**Наша инстанциация (worked slice).** Каждый из 6 тезисов `theses-antitheses.md` несёт явную строку **Scope (A.2.6)** — границу применимости, при которой тезис не работает; фактически это операционализация фальсификатора для практических (не строго научных) claim'ов метода.

**Контрпример [A.11 Sharp Boundary].** Именующие конвенции («называем компетенцию `DPF-ADVERSARIAL-REVIEW`») — у них нет истинностного значения, фальсифицировать нечего; гейт применяется к claim'ам о мире/практике, не к алиасам/именам. Тест: «можно ли помыслить наблюдение, при котором это ложно?» Если нет и это имя — контрпример, не дефект.

**Анти-паттерн [E.8].** FPF-звучащий, связный текст LLM принимается как источник истины без указания, при каком наблюдении он был бы опровергнут (fluency-as-authority); «фальсифицируемость = истинность, прошёл гейт → claim верный» — путает демаркацию научности с гарантией корректности.

**Conformance.** У каждого claim'а/тезиса явно написана scope-граница ИЛИ прямой источник+дата (A.10); claim без того и другого не входит в source-pack как несущий, а помечается opinion.

**Связи [E.4.PFR].** **composes** с Паттерном 4 (фальсификатор фиксируется как evidence-anchor в D1–D11); **conflicts** с fluency-as-authority (error №7, Sec 6).

---

### Паттерн 4: Package-adequacy protocol — D1–D11 не подменяется средним баллом паттернов

**Recognition** — пакет объявляется готовым/`admissible`; кто-то предлагает статус по факту, что «все секции CC-DPF.1–9 присутствуют» или «паттерны сильные».

**Принцип (SoTA-grounded).** Оценка адекватности — формализованный воспроизводимый протокол (screening→eligibility→inclusion + явный risk-of-bias инструмент), не свободное впечатление [PRISMA 2020; AMSTAR 2, Shea et al., BMJ 2017]. Completeness-критика — аналог publication-bias/selective-reporting check: «какая традиция упущена, какой claim без источника».

**Наша инстанциация (worked slice).** FPF E.4.DPF.DA: PFM1–PFM11 подпроход (форма пакета) → координаты D1–D11 (содержание) → честный статус (`admissibleForDeclaredDPFUse` / `seedOnly` / `repairBeforeDPFUse` / `refreshNeeded`); статус не подставляется средним баллом паттернов (CC-DPFDA.4). Прецедент: DPF-AUTHORING — все CC-DPF.1–9 PASS, но D5/D11 ниже пола (процессные следы в носителе, source-pack без независимых традиций) — `references/package-adequacy-2026-07-06.md` в `DPF-AUTHORING/` (см. Sec 10).

**Контрпример [A.11 Sharp Boundary].** Прогнать E.21 по одному паттерну и получить высокий балл — НЕ есть оценка пакета целиком; E.21 — объект «один паттерн», E.4.DPF.DA — объект «пакет». Тест: «оцениваю один паттерн или весь свод?»

**Анти-паттерн [E.8].** «Все секции присутствуют → пакет готов» (путают чек-лист присутствия E.4.DPF:7 с адекватностью E.4.DPF.DA:2); «достаточно среднего балла по паттернам» (CC-DPFDA.4 явно запрещает эту подмену — сильные паттерны маскируют слабую source-basis/relations/refresh, отдельные координаты).

**Conformance.** Наличие таблицы D1–D11 с обоснованием + evidence-locus + repair-предложением на каждой строке ниже пола 4; итоговый статус явно один из четырёх, не «зелёный чек-лист».

**Связи [E.4.PFR].** **requires** Фазы 1–2 как вход (нечего оценивать без research+bridge); **composes** с Паттернами 1, 2, 3, 5, 6 (все механизмы протоколируются здесь); **conflicts** с «зелёный чек-лист = готово».

---

### Паттерн 5: Anti-sycophancy critique discipline — severity как есть, ≥3 значимых концерна, не марафон

**Recognition** — критик-агент пишет ревью пакета, особенно когда контекст диалога сигналит «автор ждёт одобрения».

**Принцип (SoTA-grounded).** Эффект структурированной оппозиции зависит от task involvement критика — медиатор эффекта, механическое исполнение роли без вовлечённости не даёт результата [Schwenk, Decision Sciences 1984]. Дополнительный риск для LLM-критика: sycophancy — систематическое занижение остроты критики под RLHF-оптимизацию под удовлетворённость пользователя, усиливается контекстом взаимодействия [Noshin & Sultana, arXiv:2603.21409, 2026-03-22].

**Наша инстанциация (worked slice).** Guardian-промпт Фазы 6 явно требует ≥3 значимых контрпримера/концерна (вероятных и значимых, не теоретических придирок), а не подтверждений; критика — не марафон: эмпирика Google — >80% ревью проходят с ≤1 итерацией правок [Sadowski et al., ICSE-SEIP 2018].

**Контрпример [A.11 Sharp Boundary].** Критик, дотошно перечисляющий 50 мелких придирок — это НЕ вовлечённость, а театр без значимости; граница: концерн должен быть вероятный + значимый, не любой теоретически возможный.

**Анти-паттерн [E.8].** Критик смягчает вывод, потому что «автор старался» или история диалога сигналит ожидание одобрения (sycophantic softening); или назначает роль guardian без реального incentive искать контрпримеры — ритуальная критика.

**Conformance.** Ревью содержит ≥3 явных контрпримера/концерна, сформулированных как «вероятно и значимо», без подстройки под ожидаемую реакцию автора; не превышает разумный объём (≤1–2 итерации в норме).

**Связи [E.4.PFR].** **composes** с Паттерном 1 (role separation необходимо, но не достаточно против sycophancy — нужен ещё явный анти-sycophancy промпт); **conflicts** с groupthink-comfort/consensus-driven softening (F-3, Sec 3).

---

### Паттерн 6: Ревью ценно даже при «чистом» пакете (knowledge distribution)

**Recognition** — критик прогнал Фазу 6 и не нашёл критичных дефектов; возникает соблазн счесть ревью «пустой тратой».

**Принцип (SoTA-grounded).** Peer review даёт эффект knowledge distribution наравне с defect detection — второй инженер/роль теперь понимает изменение/пакет, независимо от того, сколько багов найдено [Sadowski, Söderberg, Church, Sipko, Bacchelli, ICSE-SEIP 2018, 9М ревью в Google].

**Наша инстанциация (worked slice).** Guardian фиксирует разбор Фазы 6 как inspectable-артефакт (`package-adequacy-<date>.md`) даже когда итоговый статус близок к `admissible` — следующие роли (facilitator при гейте, keeper при сборке следующей версии) читают его и получают понимание пакета, не только финальный статус-штамп.

**Контрпример [A.11 Sharp Boundary].** «Раз ревью распространяет понимание — пусть критикует бесконечно, чем дольше тем лучше» — НЕ следует из принципа: эмпирика Google — ≤1 итерация в >80% случаев; марафон-ревью = diminishing returns и блокирует прогресс. Ценность в первом внимательном проходе, не в количестве итераций.

**Анти-паттерн [E.8].** Пропустить Фазу 6 целиком для «явно готового» пакета («и так всё ясно»); или считать ревью проваленным потому, что критичных дефектов не найдено (defect detection — лишь один из двух эффектов).

**Conformance.** `package-adequacy-<date>.md` существует и содержит содержательный разбор (не пустой файл-штамп) даже при итоговом `admissible`-статусе.

**Связи [E.4.PFR].** **composes** с Паттерном 4 (эффект реализуется через протокол-артефакт, не через устное впечатление); **scope-dependent** (ценность максимальна именно когда defect-detection молчит).

---

## 5. Связи паттернов (E.4.PFR)

| Паттерн | requires | composes | conflicts |
|---------|----------|----------|-----------|
| **P1** Role-separation-gate | DEC-003 (role separation по агентам) | P5 (анти-sycophancy — необходимое дополнение) | «AI-consensus = evidence» |
| **P2** DI ≠ DA | — (сам определяет разграничение фаз) | P4 (оба режима протоколируются в D1–D11) | коллапс 5 локусов оппозиции в одну критику (error №2) |
| **P3** Falsifiability-gate | — | P4 (фальсификатор → evidence-anchor) | fluency-as-authority (error №7) |
| **P4** Package-adequacy protocol | Фазы 1–2 как вход | P1, P2, P3, P5, P6 (все механизмы протоколируются здесь) | «зелёный чек-лист = готово» (error №4) |
| **P5** Anti-sycophancy discipline | — | P1 (разделение проходов необходимо, но не достаточно) | groupthink-comfort / consensus-driven softening |
| **P6** Knowledge distribution | — | P4 (эффект реализуется через протокол-артефакт) | «ревью без найденных дефектов = провал» |

**Sequence (типовой прогон):** P2-DI (Фаза 2, BridgeMatrix, до сборки) → P3 (falsifiability-check каждого тезиса) → [Фаза 5, сборка DPF.md, вне этой компетенции] → P2-DA + P5 (Фаза 6, критика готового пакета, анти-sycophancy дисциплина) → P4 (протоколирование в D1–D11, честный статус) → P6 (ценность зафиксирована независимо от найденных дефектов). P1 — сквозной структурный гейт, действует на входе в Фазу 2 И Фазу 6.

---

## 6. Типовые ошибки (E.4.DPF:8)

> Полный bridge-анализ (scope+антитезис по каждому пункту) — `references/theses-antitheses.md`. Новичковые и AI-специфичные (5 из 10) — вместе (D7).

| № | Симптом | Почему происходит | Исправление | Источник |
|---|---------|--------------------|--------------| ---------|
| 1 (AI) | Research, bridge и critic пакета сделаны одной LLM-сессией; «сессия согласна с собой» принята за проверку | Self-agreement illusion: несколько проходов одной модели воспринимаются как независимая верификация | role-separation-gate: owner ≠ guardian ≠ keeper по агентам (DEC-003); один агент делал всё → BLOCK | Ding arXiv:2607.08065; ConstitAI arXiv:2212.08073; метод DPF-AUTHORING error №7 |
| 2 | Guardian «просто критикует», не различая, каким механизмом ловится провал | Коллапс 5 локусов оппозиции (роль/альтернатива/claim-свойство/протокол/проход) в одно «покритиковать» | Явно называть механизм: Фаза 2 = DI, Фаза 6 = DA, + falsifiability-check + D1–D11 + role-separation; не сливать | Mason & Mitroff AMR 1981; BridgeMatrix Divergence |
| 3 (AI) | Критик занижает остроту критики, потому что контекст сигналит «автор ждёт одобрения» | Sycophantic softening: RLHF-оптимизация под удовлетворённость, усиливается контекстом | Явный анти-sycophancy промпт («severity как есть, ≥3 контрпримера»); отдельная сессия без истории «одобрения» | Noshin & Sultana arXiv:2603.21409; CHI 2026 |
| 4 | Пакет объявлен `admissible`, потому что все секции CC-DPF.1–9 присутствуют или паттерны написаны полно | Путают чек-лист присутствия (E.4.DPF:7) с адекватностью пакета (E.4.DPF.DA); confirmation+sunk-cost | Всегда прогонять D1–D11+PFM поверх CC-чек-листа; статус — не средний балл паттернов, не награда за прошлые прогоны | PRISMA/AMSTAR 2; E.4.DPF.DA:2/:8; кейс DPF-AUTHORING (Sec 10, HC-1) |
| 5 (AI) | Каталог контрпримеров/типовых ошибок зафиксирован «навсегда» | Static-checklist decay: фиксированный набор устаревает как фиксированный набор red-team атак | refresh-триггеры G.11 (смена FPF-Spec / 3+ повтора / фидбэк ролей); каталог адаптивен | Purpura et al. arXiv:2503.01742 |
| 6 (AI) | «Спросили 3 модели, все согласны» выдаётся за NQD ≥3 альтернатив | Consensus-vs-correctness conflation: множественность моделей принята за множественность традиций | NQD требует ≥3 независимых традиций/гипотез (B.5.2.1), не ≥3 проходов; проверять различие источников, не носителей | Ding arXiv:2607.08065; контрпример P1 |
| 7 (AI) | FPF-звучащий связный текст LLM принят как источник истины без фальсификатора | Fluency-as-authority: беглость воспринимается как проверенность | Admission через C.33/C.34/C.35 прежде чем стать claim'ом; falsifiability-check | Popper 1963; метод error №6 |
| 8 | Критик механически исполняет роль без вовлечённости — придирки ради галочки | Task involvement (медиатор эффекта) отсутствует; критика = театр | Явный incentive искать вероятные+значимые контрпримеры; ≥3 главных концерна, не длинный шум | Schwenk 1984 |
| 9 | Оппозицию убрали ради консенсуса/лояльности команды | Комфорт consensus-группы принят за качество решения | Держать оппозицию как форс, не устранять; иначе прямой путь в groupthink | Janis 1972; Schweiger 1986 |
| 10 | Ревью объявлено пустым, потому что критичных дефектов не найдено | Defect detection считается единственным эффектом ревью | Учитывать knowledge distribution: разбор — inspectable-артефакт и при «чистом» пакете; не марафонить (≤1 итерация в норме) | Sadowski et al. ICSE-SEIP 2018 |

---

## 7. SoTA-Echoing (E.4.DPF:11)

> Формат: claim → источник (URL/DOI+дата) → adoption-статус в этом DPF. Полные ClaimSheets — `references/sota-research.md`.

| # | Claim | Источник | Trust-cue | Adoption в DPF |
|---|-------|----------|-----------|----------------|
| SE-1 | Devil's Advocacy — назначенный голос строит наилучший контраргумент против готового суждения | Heuer & Pherson, SATfIA, 2014/2020 (ODNI/ICD 203 tradecraft) | strong | Adopted: Паттерн 2 (DA-режим, Фаза 6) |
| SE-2 | Dialectical Inquiry — конкурирующие альтернативы формулируются с нуля, а не критикуется готовая идея | Mason & Mitroff, AMR 1981 | strong | Adopted: Паттерн 2 (DI-режим, Фаза 2, BridgeMatrix) |
| SE-3 | DI и DA дают более качественные решения, чем consensus; DI лучше по вскрытию скрытых допущений | Schweiger, Sandberg, Ragan, AMJ 1986, pp.51–71 | strong | Adopted: обоснование Forces F-2/F-3, Паттерн 2 |
| SE-4 | Эффект структурированной оппозиции зависит от task involvement критика (медиатор) | Schwenk, Decision Sciences 1984 | medium | Adopted: Паттерн 5, error №8 |
| SE-5 | Группа без структурированной оппозиции скатывается в groupthink (иллюзия единодушия, самоцензура) | Janis, *Victims of Groupthink*, 1972 | strong | Adopted: Forces F-3, Паттерн 5, error №9 |
| SE-6 | Claim без потенциального фальсификатора — мнение, не знание | Popper, *Conjectures and Refutations*, 1963 | strong | Adopted: Паттерн 3, error №7 |
| SE-7 | Peer review — воспроизводимый протокол screening→eligibility→inclusion с risk-of-bias инструментом, не свободное впечатление | PRISMA 2020 (Page et al., BMJ); AMSTAR 2 (Shea et al., BMJ 2017) | strong | Adopted: Паттерн 4, D1–D11 |
| SE-8 | Ревью даёт knowledge distribution наравне с defect detection | Sadowski et al., ICSE-SEIP 2018 (9М ревью, Google) | strong | Adopted: Паттерн 6, error №10 |
| SE-9 | Фиксированный набор тестовых атак/контрпримеров переоценивает эффективность защиты; адаптивная атака вскрывает провал | Purpura et al., arXiv:2503.01742, 2025; независимое исследование Anthropic/OpenAI/DeepMind, окт. 2025 | strong (факт), medium (цифра) | Adopted: Forces F-6, error №5, refresh-триггеры G.11 |
| SE-10 | Self-critique работает только когда критик и автор — разные проходы с разными промптами/весами | Bai et al. (Constitutional AI), arXiv:2212.08073, 2022 | strong | Adopted: Паттерн 1 |
| SE-11 | Self-consistency и cross-model agreement — ненадёжный сигнал корректности | Ding, arXiv:2607.08065, 2026-07-10 | medium (единственный автор, свежий препринт) | Adopted: Паттерн 1, контрпример P1, error №1/№6 (центральная находка компетенции) |
| SE-12 | Sycophancy — систематическое занижение остроты критики под RLHF-оптимизацию удовлетворённости | Noshin & Sultana, arXiv:2603.21409, 2026-03-22 | medium (качественный анализ, не контролируемый эксперимент) | Adopted: Паттерн 5, error №3 |

---

## 8. Имена — F.18 (CC-DPF.4)

> Кандидаты в `project/glossary.md`. Источник: `references/sota-research.md` Operator/Object inventory.

| RU термин | EN (код) | Определение | Не является |
|-----------|----------|--------------|-------------|
| Адвокат дьявола | Devil's Advocacy | назначенный голос строит наилучший контраргумент против уже готового суждения (Фаза 6) | альтернатива, сформулированная с нуля (это Dialectical Inquiry) |
| Диалектическое исследование | Dialectical Inquiry | конкурирующие тезис/анти-тезис формулируются с нуля и формально сравниваются (Фаза 2, BridgeMatrix) | атака на уже готовую идею (это Devil's Advocacy) |
| Мост-матрица | BridgeMatrix | таблица сведения традиций с явными потерями при слиянии (no silent fusion) | таблица консенсуса/усреднения мнений |
| Гейт фальсифицируемости | falsifiability-gate | проверка: есть ли у claim'а потенциальный фальсификатор (наблюдение, при котором он ложен) | проверка истинности claim'а (демаркация ≠ верификация) |
| Гейт разделения ролей | role-separation-gate | структурная проверка: критик и автор — разные агенты/проходы с разными промптами | гарантия против общего смещения весов (необходимо, но недостаточно само по себе) |
| Протокол адекватности пакета | package-adequacy protocol (D1–D11) | воспроизводимая оценка ПАКЕТА целиком по E.4.DPF.DA (PFM-подпроход + 11 координат) | средний балл по паттернам (это E.21, другой объект оценки) |
| Иллюзия самосогласия | self-agreement illusion | ложное чувство корректности от согласия модели с собой/между моделями | независимая верификация |
| Смягчение из угодливости | sycophantic softening | критик занижает остроту критики под сигнал «автор ждёт одобрения» | осознанное решение критика смягчить вывод |
| Распространение понимания | knowledge distribution | эффект ревью — следующие роли/сессии лучше понимают пакет, даже без найденных дефектов | единственная цель ревью (defect detection — второй, отдельный эффект) |
| Пробел полноты | CompletenessGap | именованный пробел: упущенная традиция SoTA / claim без источника / непокрытая тензия | любой недостаток текста (конкретно про полноту SoTA-охвата) |

**Provisional (рабочие термины, не фиксировать до стабилизации):** «театр критики» (ритуализированный концерн без вероятности/значимости, error №8); «static-checklist decay» (термин sota-research, ещё не в глоссарии); «ACH-matrix», «key-assumptions-check» (заготовки операторов из Operator/Object inventory, не инстанцированы в паттернах этого DPF).

---

## 9. Relations (E.4.PFR)

| Relation | Target | Function | Note |
|----------|--------|----------|------|
| grounded_in | DEC-003 | dependency | role-separation по агентам; owner ≠ guardian ≠ keeper |
| embedded_role_in | DPF-AUTHORING | dependency | access carrier для Фаз 2/6 метода на любом авторимом DPF (§Access carriers) |
| peer_role | DPF-KNOWLEDGE-CURATION | peer | соседний встроенный пакет (Source-pack/Assemble, owner keeper) — Фазы 3/5, не эта компетенция |
| scope_boundary | DPF-SECURITY-REVIEW | peer | code review/OWASP продукт-кода — другой предмет (текст пакета vs исполняемый артефакт) |
| scope_boundary | DPF-RISK | peer | риск-менеджмент бизнес-решений/kill-criteria — другой предмет (свод знаний vs бизнес-инициатива) |
| scope_boundary | DPF-CODE-REVIEW | peer | код против ARCH/спеки — другой предмет |
| uses | FPF E.4.DPF / E.4.DPF.DA | meta | spine + CC-DPF.1–9; PFM1–PFM11 + D1–D11 package adequacy |
| uses | FPF E.8 | meta | форма паттернов (recognition/principle/instance/counterexample/anti-pattern/conformance/relations) |
| uses | FPF E.4.PFR | meta | типы связей паттернов и тезисов (composition/conflict/scope-dependent/requires) |
| uses | FPF A.2.6 (USM) | meta | ClaimScope на каждом тезисе |
| uses | FPF B.5.2.1 (NQD) | meta | ≥3 антитезиса на каждый тезис |
| uses | FPF A.10 (Evidence Graph) | meta | evidence-anchor обязателен для каждого claim |
| uses | FPF A.11 (Sharp Boundary) | meta | контрпримеры отдельно от анти-паттернов |
| uses | FPF A.7 (Strict Distinction) | meta | Role vs Function; Method vs Work — критик ≠ роль без исполнения |
| uses | FPF A.1.1 (BoundedContext) | meta | принцип первичен, инстанциация вторична |
| uses | FPF F.18 | meta | форма именования (Sec 8) |
| uses | FPF G.11 | meta | refresh-триггеры (Sec 11) |

---

## 10. Разнородные приёмочные случаи (D8)

> Проверка, что паттерны реально сработали за пределами мотивирующего примера (Фаза 6 метода уже прогнана guardian на 12 DPF-пакетах проекта 2026-07-06, `wf_fc1abade-9f7` оценка + `wf_db814081-1e1` ремонт). Ниже — 3 непохожих кейса: мета-домен (сам метод), технический домен, организационный домен.

| # | Кейс | Отличие от мотивирующего примера | Что показал прогон паттернов 1–4 | Evidence |
|---|------|-----------------------------------|-----------------------------------|----------|
| **HC-1** | **DPF-AUTHORING (self-application)** — мета-домен, инструмент применил себя к себе | Предельный риск self-agreement illusion (Паттерн 1): один и тот же метод оценивает сам себя | Прогон вскрыл РЕАЛЬНЫЙ дефицит: все CC-DPF.1–9 PASS, но D5 PackageFormLayeringAndRelation=3 и D11 DomainSoTAAlignment=3 — ниже пола 4 (процессные следы в носителе, PFM7; source-pack без независимых традиций, authority-by-citation). Статус `repairBeforeDPFUse` → после ремонта (research-first гейт закрыт, PFM7-остаток вынесен) независимая переоценка дала `admissibleForDeclaredDPFUse`. Прямое опровержение error №4 («все секции PASS → готово») и подтверждение Паттерна 4 | `DPF-AUTHORING/references/package-adequacy-2026-07-06.md` (D5/D11 таблица, репарация, переоценка) |
| **HC-2** | **DPF-EBPF** — технический/кодовый домен, максимально далёкий от мета-авторинга | Предмет ревью — свод принципов про eBPF-инженерию (maps-first, atomic reload), не про сам метод авторинга | Прогон нашёл D9 EditionStateAndCurrentnessAdequacy=4 с repair-пометкой (`status: stage-0` вместо явного edition-идентификатора — process-phase протёк в frontmatter, PFM7-класс дефект). После мелкого repair (замена process-phase на `maturity:conformant`+`edition:"1.1"`) — статус `admissibleForDeclaredDPFUse`. Подтверждает: Паттерн 4 ловит форменные дефекты даже в «зрелом», содержательно сильном пакете (4 полных паттерна с worked slice) | `DPF-EBPF/references/package-adequacy-2026-07-06.md` (D9 строка, repair, итоговый статус) |
| **HC-3** | **DPF-TEAM-TRAINING** — организационный/процессный домен (обучение вайб-кодеров), не технический и не мета | Предмет — curriculum/comprehension-gate/AI-skill-matrix; ни кода, ни eBPF, ни самого метода авторинга | Прогон нашёл D9 residue (review-status остаток «1 Medium + 4 Low + R1–R5» внутри самого DPF.md, PFM7 process-state leakage) — тот же класс дефекта (D9/PFM7), что и HC-2, но в организационном домене, независимо найден. После repair (вынос residue в `references/critic-review.md`, в носителе — только durable-attestation) — `admissibleForDeclaredDPFUse` | `DPF-TEAM-TRAINING/references/package-adequacy-2026-07-06.md` (D9 residue, repair, итоговая durable-attestation-строка) |

**Вывод кейсов.** Паттерн 4 (D1–D11 ≠ чек-лист присутствия) сработал одинаково в трёх непохожих доменах (мета/технический/организационный) и трижды нашёл РЕАЛЬНЫЙ дефект (не театр): дважды D9 (edition-state/PFM7 process-residue), один раз D5+D11 (форма+source-basis). Ни в одном случае средний балл по содержательно сильным паттернам не подменил статус (CC-DPFDA.4 удержан). **HC-4 (self-application, 2026-07-06):** Фаза 6 для самого DPF-ADVERSARIAL-REVIEW прогнана независимо (guardian, отдельно от сборки keeper — `references/critic-review.md`): все 11 координат ≥ пола 4, но найден собственный форменный дефект того же класса D9/PFM7 (frontmatter `status: stage-0` — ровно то, что HC-2 чинил у DPF-EBPF) — прямое подтверждение error №4 и Паттерна 4 на себе; после наименьшей правки статус `admissibleForDeclaredDPFUse`.

---

## 11. Quality & Refresh (E.4.DPF.DA/E21/G.11, CC-DPF.7)

**Что оценивается:** прошли ли Фазы 1–3 (research-first гейт: `sota-research.md`+`theses-antitheses.md`+`source-pack.md` присутствуют — да); ≥3 традиции (да, 5); каждый тезис со scope+NQD≥3 антитезис+тип связи (да, 6 тезисов); контрпримеры отдельно от анти-паттернов (да); каталог типовых ошибок с AI-срезом (да, 10, из них 5 AI); **пакет целиком по E.4.DPF.DA** (НЕ прогнано для самого этого DPF — см. Conformance).

**Refresh triggers (G.11):**
- `review_due` 2026-10-06 (DRR) — общий пересмотр.
- **Ранний триггер (2026-08-15 или раньше):** переоценить SE-11 (Ding, arXiv:2607.08065) и SE-12 (Noshin & Sultana, arXiv:2603.21409) на независимую репликацию/цитирование — оба препринты на дату харвеста, trust-cue medium, максимально decay-чувствительны.
- Изменение FPF-Spec (E.4.DPF / E.4.DPF.DA / G.2 / E.8) → пересмотреть структуру паттернов.
- 3+ DPF с одинаковым D9/PFM7-отклонением (process-residue в носителе, см. HC-2/HC-3) → это уже системный паттерн, эскалировать в `DPF-AUTHORING` (шаблон/скилл), не чинить точечно каждый раз.
- Появление прямой цитаты ODNI/ICD 203 Analytic Standards (сейчас только контекст к Heuer & Pherson) → добавить отдельным источником.
- Обратная связь ролей (facilitator/keeper) о ложных срабатываниях или пропусках гейта.

**Open assumptions (`references/source-pack.md` §Hypothesis soft-spots, §Открытые provenance-вопросы):**
- Self-consistency≠correctness (Ding) — единственный автор, требует независимой репликации для upgrade до strong.
- Sycophantic softening (Noshin) — качественный Reddit-анализ, требует контролируемого A/B на реальном пакете этого проекта.
- Cross-model agreement как альтернатива NQD — граница названа (контрпример Паттерна 1), но операционный тест для конкретной сессии не спроектирован.
- Role-separation-gate: `agentType` у Bridge и Critic в реальном pipeline-коде — оба `'general-purpose'`, разделение достигается через отдельный `agent()`-dispatch + разный prompt-текст, не через разные веса/agentType. Тезис 6 (theses-antitheses.md) признаёт это структурно достаточным по аналогии с Constitutional AI, но explicit CI-гейт (`role-separation-gate` как исполняемая проверка) — по-прежнему stub, не implemented.

---

## Артефакты каталога (references/)

- [`references/scope.md`](references/scope.md) — Фаза 0: bounded context, intended reader, first use, non-use boundary.
- [`references/sota-research.md`](references/sota-research.md) — Фаза 1 (G.2): 5 традиций, 14 ClaimSheets, AI-срез (5 failure modes), 9 MicroExamples, Operator/Object inventory.
- [`references/theses-antitheses.md`](references/theses-antitheses.md) — Фаза 2 (G.2d): BridgeMatrix, 6 тезисов со scope+NQD≥3 антитезис+тип связи, 5 контрпримеров, каталог из 10 типовых ошибок.
- [`references/source-pack.md`](references/source-pack.md) — Фаза 3 (G.2): provenance-решения adopted/rejected по каждому источнику, retired-premises, hypothesis soft-spots, открытые provenance-вопросы.
- `references/package-adequacy-<date>.md` — Фаза 6 (E.4.DPF.DA) этого же пакета: **ещё не создан** (см. Conformance ниже — честно, не самозаявлено).

---

## Carrier note (CC-DPF.5)

Все web/LLM-источники (Heuer/Pherson, Mason/Mitroff, Popper, PRISMA/AMSTAR, Sadowski et al., Bai et al., Ding, Noshin & Sultana, Purpura et al.) — carriers, допущены через admission C.33/C.35, каждый с URL/DOI/arXiv-ID+датой (claim без источника = мнение, A.10). `project/domain.md` и 7 DEC явно проверены и **rejected** как источники этой компетенции (доменный/процессный контент продукта, не смешаны — A.7). FPF-разделы читаются живьём Grep по `FPF-Spec.md`, не по памяти.

---

## Conformance checklist (E.4.DPF:7)

- [x] CC-DPF.1 Context declared — Sec 1, зеркалит `references/scope.md`.
- [x] CC-DPF.2 Source pack present — `references/source-pack.md` (G.2), adopted/rejected по каждому источнику.
- [x] CC-DPF.3 Architecture decision present — Sec 0 (структурный отчёт) + non-use boundary Sec 1 + Forces Sec 3 (purpose/pattern-split/must-NOT-land).
- [x] CC-DPF.4 Names prepared — Sec 8, 10 терминов, provisional отмечены.
- [x] CC-DPF.5 Carriers admitted — carrier note выше, admission C.33/C.35.
- [x] CC-DPF.6 Patterns drafted through E.8 — 6 паттернов, каждый: recognition→принцип(SoTA)→инстанциация→контрпример[A.11]→анти-паттерн→conformance→связи[E.4.PFR].
- [x] CC-DPF.7 Quality & refresh routes present — Sec 11.
- [x] CC-DPF.8 Структурный отчёт носителя в шапке — Sec 0.
- [x] CC-DPF.9 Примат решения задач — Sec 4 (принцип→worked slice на каждый паттерн), Sec 6 (10 типовых ошибок, блокируемые provалы), Sec 7 SoTA-Echoing (source-grounded solution moves); не vocabulary/ontology-only.

> **Честный статус пакета (CC-DPFDA.8, против собственного error №4 этого DPF).** Фаза 6 (E.4.DPF.DA: PFM-подпроход + координаты D1–D11) для **этого самого пакета** (`DPF-ADVERSARIAL-REVIEW`) **прогнана независимо 2026-07-06** guardian (отдельная сессия от сборки keeper — role-separation-gate, Паттерн 1) → `references/critic-review.md`. Секции CC-DPF.1–9 присутствуют И, по собственному Паттерну 4 (присутствие секций ≠ адекватность), пакет оценён по D1–D11: все 11 координат ≥ пола 4; найден и устранён собственный форменный дефект D9/PFM7 (`status: stage-0` → `maturity/edition`, как HC-2). Статус: **`admissibleForDeclaredDPFUse`** (не самоподтверждение — независимый прогон, A.10; см. HC-4 в Sec 10 и `references/critic-review.md`). Открытые наименьшие правки (не блокирующие) — в §F critic-review.

> conformance: CC-DPF.1–9 verified; E.4.DPF.DA: admissibleForDeclaredDPFUse (critic, guardian, 2026-07-06)
