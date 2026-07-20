---
dpf_id: "DPF-ADVERSARIAL-REVIEW"
artifact: "source-pack"
phase: "3 (Source-pack / provenance, G.2)"
author_role: "keeper"
grounded_in: ["FPF G.2", "FPF A.10 Evidence Graph", "FPF A.1.1 BoundedContext", "FPF A.11 Parsimony", "FPF A.7 Strict Distinction"]
covers: ["scope.md", "sota-research.md (#1–14, 5 традиций)", "theses-antitheses.md", "DEC-003", "DPF-AUTHORING/references/method.md", "DPF-AUTHORING/DPF.md (Access carriers)", "dpf-authoring-pipeline.js (execution evidence)", "domain.md (проверено, нерелевантно)", "decisions/DEC-001,002,004–008 (проверены индивидуально)", "competency-map.md (проверено)"]
date: "2026-07-06"
gate: "каждый источник имеет явное решение adopted/rejected"
---

# Source Pack (G.2) — DPF-ADVERSARIAL-REVIEW

> Реестр provenance: по каждому источнику — что **взято** в DPF, что **намеренно отброшено** (и почему),
> статус claim'а и актуальность. Дом решений по референсам (FPF E.4.DPF шаг 2 / G.2).
> Контент источников — в `references/`/`domain.md`; здесь — **решения** по ним.
> Особенность bounded context: это **встроенный пакет ролей** скилла `dpf-authoring` (не позиция карты `competency-map.md`, 33 DPF) — owner guardian, access carrier для Фаз 2/6 метода на ЛЮБОМ авторимом DPF (см. `DPF-AUTHORING/DPF.md` §Access carriers). Поэтому в проверку явно включены и сам метод, и исполняющий его pipeline-код — не только `project/`-артефакты.

---

## Таблица источников (уровень файлов / решений)

| Источник | Adopted (взято в DPF) | Rejected (намеренно отброшено + причина) | Claim-status | Currentness |
|----------|------------------------|---------------------------------------------|--------------|-------------|
| `references/scope.md` | Bounded context (адверсарная функция в двух точках метода — Фаза 2 Bridge, Фаза 6 Critic); intended reader (guardian, вторично facilitator/keeper); non-use boundary (5 явных границ: не security-аудит кода, не риск-менеджмент бизнеса, не генерация ресёрча, не сборка DPF.md, не Decider Protocol) | Ничего не отброшено — Phase-0 артефакт метода, не первичный source | scope-note (design artifact) | 2026-07-06 |
| `references/sota-research.md` (#1–14, 5 традиций) | CorpusLedger 5 независимых традиций (SAT/интеллект-анализ [1], dialectical inquiry/групповое решение [2,3,4,5], фальсификационизм [6], systematic-review/SE-peer-review [7,8,9], AI-специфика self-critique/red-team/sycophancy [10,11,12,13]); 14 ClaimSheets с trust-cue; обязательный AI-срез (5 failure modes: self-agreement illusion, sycophantic softening, fluency-as-authority, static-checklist decay, consensus-vs-correctness conflation); 9 MicroExamples; Operator/Object inventory (9 объектов + 11 операторов-заготовок, вкл. `role-separation-gate`, `falsifiability-check`, `package-adequacy-score`) | Источник #14 (DeepTeam/LLMFuzzer/Auto-RT) — **park**: конкретные red-teaming фреймворки безопасности прод-LLM; домен инструментов (jailbreak-фаззинг кода/модели) не совпадает с доменом ревью текстовых пакетов знаний — переиспользован только паттерн attacker/defender loop, не сами инструменты (явно зафиксировано автором в «Открытые вопросы / park») | fact/hypothesis/opinion mixed (per trust-cue в ClaimSheets — 9 strong, 3 medium: Ding/Noshin/Purpura-числа) | 2026-07-06; Ding/Noshin — препринты июль/март 2026 (максимально свежие, decay-чувствительны) |
| `references/theses-antitheses.md` | BridgeMatrix (5 традиций × 4 оси, явные потери на каждой оси, no silent fusion — Divergence-строка отказывается сливать 5 разных локусов оппозиции в одну метрику); 6 тезисов со scope (A.2.6) + NQD≥3 антитезисов каждый + тип связи (E.4.PFR); 5 контрпримеров (Sharp Boundary, отдельно от ошибок); каталог из 10 типовых ошибок (5 из них AI-специфичные: self-agreement, sycophancy, static-decay, consensus-conflation, fluency-as-authority) | Ничего не отброшено — артефакт-синтез (guardian, «адверсарная дисциплина применена к себе»), не первичный source; gate-самопроверка Фазы 2 пройдена по всем пяти пунктам явно | synthesis artifact | 2026-07-06 |
| `project/decisions/DEC-003.md` | Прямой проектный enforcement-механизм типовой ошибки №1 этого DPF: «модель каждого dispatch задаётся явно по сложности фазы, не наследуется молча»; role separation по агентам (owner ≠ guardian ≠ keeper) явно названа как обоснование Bridge/Critic = Opus (диалектика/adversarial — где Opus покупает качество). Уже процитирован ВНУТРИ `theses-antitheses.md` (шапка, DEC-003 против «AI-consensus = evidence») — здесь подтверждена связь как первоисточник решения, не изобретена заново | Остальной контент решения (конкретные kill_criteria по цене Sonnet/Opus-прогонов, cost-model-discipline экономика) — **rejected как источник паттернов ЗДЕСЬ**: это cost-дисциплина cto/facilitator, не предмет адверсарной проверки; используется только role-separation-клауза | accepted | 2026-06-30; review 2026-09-30 |
| `~/.claude/skills/dpf-authoring/references/method.md` (канон метода, зеркало — `DPF-AUTHORING/DPF.md`) | Формулировки Фазы 2 (BridgeMatrix, alignment/divergence, no silent fusion) и Фазы 6 (completeness-critic: «какая традиция SoTA упущена? какая тензия не покрыта? какой claim без источника?» + E.4.DPF.DA подпроход) — прямой родитель bounded context этого DPF, дословно процитированный в `scope.md`; типовая ошибка метода №7 («один агент = research+bridge+critic, согласие с собой = evidence») — прямая причина существования этой компетенции | Остальные 4 фазы метода (Bootstrap/SoTA Harvest/Source-pack/Assemble) — **rejected**: это компетенция `DPF-KNOWLEDGE-CURATION` (соседний встроенный пакет, owner keeper), не адверсарная функция; явно отражено в non-use boundary scope.md («НЕ сама сборка DPF.md») | fact (canonical method text) | ред. FPF f7c7e93f (сверено `FPF-Spec.version` при последнем пересмотре метода 2026-07-06(2), keeper) |
| `project/frameworks/DPF-AUTHORING/DPF.md` §«Access carriers» | Явный структурный статус этого DPF: «встроенный пакет роли» скилла (формат framework-apply: `DPF.md` + `apply-prompt.md`), НЕ позиция `competency-map.md`; авторская комната этого каталога — соседний каталог библиотеки, как и у `DPF-KNOWLEDGE-CURATION`. Закрывает потенциальную путаницу «почему DPF-ADVERSARIAL-REVIEW отсутствует в таблице 33 DPF» — это не пробел, а другой класс носителя (PFM10) | Остальное содержимое DPF.md (паттерны самого метода авторинга, conformance-таблица DPF-AUTHORING) — **rejected**: относится к компетенции DPF-AUTHORING (keeper), не к адверсарной функции | fact (design decision, зафиксирован в тексте DPF.md) | 2026-07-06 |
| `.claude/workflows/dpf-authoring-pipeline.js` (проект) + `~/.claude/skills/dpf-authoring/assets/dpf-authoring.workflow.js` (канон) — **execution evidence** | Подтверждение (A.10, не «код прочитан → значит так себя ведёт», а прямая цитата диспетчера): Bridge/Critic-фазы РЕАЛЬНО получают отдельный `agent()`-dispatch с текстом роли `DPF-ADVERSARIAL-REVIEW`, инжектированным через `roleOf()` — НЕ однострочное «ты guardian» (комментарий кода, строка 73), а полная процедура. Прямой полигон применения `role-separation-gate` из Operator/Object inventory sota-research.md | **Открытая находка, не rejected:** `agentType` у Bridge и у Critic — оба `'general-purpose'` (не различаются как отдельные «личности» агента); разделение достигается ТОЛЬКО через отдельный `agent()`-вызов (свежий контекст на фазу) + разный `model` (Opus у обоих) + разный prompt-текст. Это ближе к паттерну Constitutional AI (разные проходы, могут быть те же веса) — тезис 6 анти-тезис 2 признаёт это ДОСТАТОЧНЫМ, но граница не проверена явно нигде в тексте DPF. Вынесено открытым provenance-вопросом №4 ниже | fact (прочитан и процитирован код, не домыслен) | 2026-07-06 |
| FPF `E.4.DPF` / `E.4.DPF.DA` / `A.2.6:6.3` (ClaimScope) / `B.5.2.1` (NQD) / `E.4.PFR:4` (relation functions) / `A.11:2` (Sharp boundary) / `A.10` (Evidence Graph) — live via `fpf-integration` | Формы Фазы 2/6 метода; PFM1–PFM11 подпроход + координаты D1–D11 (используются на будущей Фазе 6 этого же DPF, ещё не прогнана); scope-строка обязательна на каждом тезисе; ≥3 антитезисов; типы связи; sharp-boundary тест на каждый контрпример | Полный текст FPF-Spec (66K+ строк) — не хранится выжимкой в этом каталоге (carrier note CC-DPF.5: читаем живьём Grep+Read, не по памяти) | fact | `FPF-Spec.version`, сверено живым Grep 2026-07-06 (секции E.4.DPF:66066, E.4.DPF.DA:66506 существуют в текущей редакции) |
| `project/domain.md` (все 8 блоков) | — | **Explicit rejected целиком** — прочитаны все 8 блоков (eBPF/XDP, PR#133, архитектура/стек, поверхность атак A2S, защита/граница ответственности, хостинг-интеграция, рынок/конкуренты, Африка, SDD/вайб-кодеры) — ни один не относится к предмету «адверсарная проверка ПАКЕТА ЗНАНИЙ»; это доменные факты продукта (non-use boundary scope.md), не смешаны (A.7). Явно НЕ пропущено молча | n/a | 2026-07-06 (проверка) |
| `project/decisions/DEC-001.md` | — | **Rejected** — архитектура дата-плейна (loader-абстракция, Ячейка A) — доменный контент eBPF, вне bounded context | n/a | 2026-07-06 (проверка) |
| `project/decisions/DEC-002.md` | — | **Rejected как прямой источник паттернов** — governance-модель ВСЕЙ 33-DPF библиотеки (competency-map.md), в то время как DPF-ADVERSARIAL-REVIEW — встроенный пакет скилла, другой класс носителя (см. строку DPF-AUTHORING/DPF.md выше, которая закрывает этот же вопрос точнее); философия role-separation в DEC-002 уже покрыта прямой цитатой DEC-003 | n/a | 2026-07-06 (проверка) |
| `project/decisions/DEC-004.md`, `DEC-005.md`, `DEC-006.md`, `DEC-007.md`, `DEC-008.md` | — | **Rejected поимённо** (не единым блоком) — дистрибуция DPF-библиотеки (004), hot-path контракт детекции (005), формат работы внешней команды (006), roadmap v1/v2 (007/008) — все доменный/процессный контент продукта или команды, вне non-use boundary scope.md; проверены индивидуально, не пропущены молча (A.7) | n/a | 2026-07-06 (проверка) |
| `project/frameworks/competency-map.md` | Косвенно подтверждает структурный статус (33-DPF таблица НЕ содержит DPF-ADVERSARIAL-REVIEW — ожидаемо, см. DPF-AUTHORING/DPF.md выше, не ошибка/пробел) | Как источник паттернов адверсарной проверки — **rejected**: это индекс роль→DPF другого класса объектов | index artifact (accepted, DEC-002) | 2026-06-29 |

---

## Retired-premises

> Явно опровергнутые/устаревшие предпосылки (тег `retire`/R-номер в CorpusLedger). Проверено по `sota-research.md`
> CorpusLedger (#1–14): триаж содержит только **Include** (13) и **Park** (1) — **ни один источник не тегирован `Retire`**.
> `theses-antitheses.md` также не содержит опровергнутых предпосылок (Divergence-строка BridgeMatrix фиксирует явные
> потери/риски при наивном переносе, но это не то же самое, что retired premise — потери зафиксированы КАК ГРАНИЦА,
> не как опровержение). **Нет retired-premises на 2026-07-06.**

---

## Hypothesis soft-spots

> Claims с trust-cue medium (не strong) в `sota-research.md` ClaimSheets, влияющие на паттерны DPF. Требуют evidence для повышения статуса.

| Claim | Источник | Текущий статус | Что нужно для upgrade |
|-------|----------|-----------------|-------------------------|
| Self-consistency и cross-model agreement — ненадёжный сигнал корректности | Ding, arXiv:2607.08065 (2026-07-10) | medium — единственный автор, препринт без явного peer review; согласуется с более широким корпусом sycophancy-работ | Независимая репликация/цитирование другими авторами; на 2026-07-06 — самый свежий из всего корпуса (4 дня как опубликован на момент харвеста) |
| Sycophantic softening критика под контекст «автор ждёт одобрения» | Noshin & Sultana, arXiv:2603.21409 (2026-03-22) | medium — качественный анализ Reddit-дискуссий, не контролируемый эксперимент | Контролируемое A/B (один и тот же пакет, разный «сигнал ожидания одобрения» в промпте) — пока не проводилось в этом проекте |
| «>90% провал защит под адаптивной атакой» (конкретная цифра) | Purpura et al., arXiv:2503.01742 (2025) | strong для факта деградации, medium для точной цифры — методология оценки сама варьируется между исследованиями (Anthropic/OpenAI/DeepMind, окт. 2025) | Не критично для нашего использования — качественный вывод (каталог устаревает) достаточен для обоснования refresh-триггеров G.11, точная цифра не переносится как норматив |

---

## Открытые provenance-вопросы

> Assumptions, которым нужен evidence для закрытия (FPF A.10). Первые 3 — унаследованы из `sota-research.md` §«Открытые вопросы / park», не решены здесь самостоятельно (Факт≠решение, адресованы guardian как owner). Вопрос №4 — новая находка этой сверки (execution evidence).

1. **DeepTeam/LLMFuzzer/Auto-RT [14] — park, не адаптирован.** Домен инструментов (jailbreak-фаззинг прод-LLM) не совпадает буквально с доменом ревью текстовых пакетов знаний; переиспользован только паттерн attacker/defender loop. Если появится инструмент, специфично применимый к текстовым пакетам (не коду/модели), — пересмотреть на следующем refresh (G.11).

2. **Cross-model agreement как альтернатива NQD (несколько LLM вместо нескольких независимых традиций/людей) — не исследовано.** Контрпример 1 (`theses-antitheses.md`) даёт границу («различаются ли эпистемические источники, или только вычислительные носители одного смещения?»), но операционный тест для конкретной сессии этого проекта не спроектирован. Нужен: явный протокол проверки, применённый хотя бы раз на реальном DPF.

3. **ODNI ICD 203 (Analytic Standards) не проверен независимо** — только упомянут как контекст к Heuer & Pherson [1] в sota-research.md. Если появится прямая цитата стандарта, добавить отдельным источником при следующем refresh.

4. **Role-separation-gate: `agentType` не различается между Bridge и Critic в реальном pipeline-коде (найдено при этой сверке, execution evidence).** Оба используют `agentType: 'general-purpose'`; разделение достигается через отдельный `agent()`-dispatch (свежий контекст) + одинаковый `model: 'opus'` для обоих + разный prompt-текст (`bridgePrompt`/`criticPrompt`). Тезис 6 анти-тезис 2 (`theses-antitheses.md`) признаёт этот паттерн структурно достаточным по аналогии с Constitutional AI (разные проходы могут иметь общие веса), но: (a) Bridge и Critic в текущем pipeline — это ДРУГАЯ пара ролей, чем owner/guardian (Bridge и Critic — ОБЕ этот же DPF, DPF-ADVERSARIAL-REVIEW, обе owned guardian; настоящее «owner ≠ guardian» разделение — это Source-pack/Assemble ← `DPF-KNOWLEDGE-CURATION` (keeper) ПРОТИВ Bridge/Critic ← `DPF-ADVERSARIAL-REVIEW` (guardian), т.е. разделение есть НА УРОВНЕ ПАКЕТА РОЛИ, а не только модели); (b) нет явной проверки в коде (никакого `role-separation-gate` оператора из Operator/Object inventory реально не implemented — это по-прежнему stub, не CI-гейт). Нужен: явное решение (Фаза 4/5 этого же DPF) — считать ли текущее разделение (по пакету роли + свежий dispatch) достаточным инстанцированием паттерна role-separation-gate, или формализовать проверку.

---

## Gate-самопроверка Фазы 3 (G.2 / A.10)

- [x] Каждый источник из таблицы имеет явное решение **adopted / rejected + причина** (14 строк: 3 core-артефакта Фазы 0–2, 1 DEC, 2 method-уровня, 1 execution-evidence, FPF-секции, domain.md, 6 DEC поимённо, competency-map.md).
- [x] Каждый claim-status и currentness проставлены.
- [x] Retired-premises секция присутствует явно (найдено: ни одного — не пропущено молча).
- [x] Открытые provenance-вопросы зафиксированы (4), с конкретным evidence, который их закрыл бы; 3 унаследованы честно (не решены keeper самостоятельно), 1 — новая находка этой сверки.
- [x] Bounded context (A.1.1) удержан: domain.md и 7 DEC явно **rejected** поимённо как доменный/процессный контент продукта — не смешаны с предметом «адверсарная проверка пакета знаний» (A.7 Strict Distinction).
- [x] Особенность этого DPF (встроенный пакет роли, не позиция competency-map.md) явно зафиксирована и не оставлена implicit — закрывает потенциальную путаницу «почему отсутствует в таблице 33».
- [→] Следующая фаза: Фаза 4 (архитектурное решение DPF — purpose/pattern-split/must-NOT-land) → далее сборка `DPF.md` (Фаза 5, `DPF-KNOWLEDGE-CURATION`) → Фаза 6 (package adequacy, guardian, этот же DPF на себе).
