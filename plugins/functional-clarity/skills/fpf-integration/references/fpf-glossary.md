# FPF — Глоссарий ключевых терминов

> Сгенерировано из FPF-Spec.md @ ailev/FPF `40b232f11ed9` (2026-06-26). Полный SHA: `40b232f11ed950ed34082273c57ff4f6c45b7f06`.
> Проверять актуальность: сравни с `~/.claude/knowledge/fpf/FPF-Spec.version` и текущим upstream.


> 100 основных терминов FPF. Для поиска в спеке используй Grep по EN-термину.

| Термин (EN) | Термин (RU) | Определение | Где найти |
|-------------|-------------|-------------|-----------|
| Holon | Холон | Сущность, которая является одновременно целым и частью большего целого в иерархической структуре. | A.1, A.1.1, B.2 |
| Bounded Context | Ограниченный контекст | Семантическая рамка с локальным словарем и явными мостами к другим контекстам для управления амбигвитностью. | A.1.1, A.2.6, F.0.1 |
| Role Assignment | Присвоение роли | Контекстное назначение роли держателю с учетом enactment и RCS/RSG. | A.2.1, A.2, A.15 |
| Capability | Способность | Диспозиционная свойство системы, определяющая ее ability к действию в scope. | A.2.2, A.2.6, B.2.4 |
| Promise Content | Содержание обещания | Потребительское обещание с accessSpec и acceptanceSpec, включая SLO/SLA. | A.2.3, A.6.C, F.12 |
| Evidence Role | Роль доказательства | Станс эпистемы как поддержки claims с justification. | A.2.4, A.10, B.3 |
| Role State Graph | Граф состояний роли | Именованное пространство состояний роли для моделирования lifecycle. | A.2.5, A.19, A.3.3 |
| Unified Scope Mechanism | Унифицированный механизм scope | Механизм для контекстных слайсов и scopes как set-valued объектов. | A.2.6, A.6.1, B.3 |
| Role Algebra | Алгебра ролей | Операторы для отношений ролей: specialization, incompatibility, bundles. | A.2.7, A.15, A.2.5 |
| Commitment | Обязательство | Деонтический объект с modality, scope и evidence hooks по BCP-14. | A.2.8, A.6.B, A.6.C |
| Speech Act | Речевой акт | Коммуникативная работа как approval или revocation с provenance. | A.2.9, A.6.C |
| Transformer Quartet | Квартет трансформера | Конституция действия: System-in-Role, MethodDescription, Method, Work. | A.3, A.15 |
| Method | Метод | Абстрактный способ действия как procedure или recipe. | A.3.1, A.15, B.1.5 |
| Method Description | Описание метода | Спецификация процедуры как epistemic artifact или SOP. | A.3.2, A.15 |
| Dynamics | Динамика | Закон изменения для state transitions и simulations. | A.3.3, A.19, B.4 |
| Temporal Duality | Временная двойственность | Разделение design-time и run-time для эволюции и versioning. | A.4, B.4 |
| Signature Stack | Стек сигнатур | Дисциплина границ с routing laws, admissibility, deontics, evidence. | A.6, E.8, E.17 |
| Boundary Norm Square | Квадрат норм границ | Разложение граничных утверждений на laws, gates, duties, effects. | A.6.B, A.6, E.17 |
| Effect Free Epistemic Morphing | Безэффектный эпистемический морфинг | Морфизмы эпистем без эффектов для трансформаций descriptions. | A.6.2, A.6.3, E.17.0 |
| Epistemic Viewing | Эпистемический просмотр | Просмотр с сохранением describedEntity через viewpoints. | A.6.3, E.17, E.18 |
| Epistemic Retargeting | Эпистемическое перенаправление | Морфизм с изменением describedEntity через kind bridges. | A.6.4, E.18, C.2.1 |
| Relational Precision Restoration | Восстановление точности отношений | Сюита для ремонта underspecified relations через qualified records. | A.6.P, A.6.A |
| Strict Distinction | Строгое различие | Clarity lattice для избежания category errors как Object ≠ Description. | A.7, A.1, A.3 |
| Universal Core | Универсальное ядро | Трансдисциплинарное ядро без domain-specifics. | A.8, P-8 |
| Cross Scale Consistency | Последовательность через масштабы | Инварианты в композиции holarchies. | A.9, B.1, P-8 |
| Evidence Graph Referring | Ссылки на граф доказательств | Traceability claims через evidence с SCR/RSCR. | A.10, B.3, G.6 |
| Ontological Parsimony | Онтологическая экономность | Минимализм концептов по Occam's razor. | A.11, P-1 |
| External Transformer | Внешний трансформер | Принцип causality с external agent для self-modification. | A.12, B.2.5 |
| Agential Role | Агентивая роль | Роль с autonomy в agency spectrum. | A.13, C.9 |
| Advanced Mereology | Продвинутая mereology | Отношения part-of: ComponentOf, PortionOf, PhaseOf. | A.14, B.1.1, A.6.H |
| Role Method Work Alignment | Выравнивание роль-метод-работа | Контекстное enactment с MIC и WorkPlan. | A.15, A.2, A.3 |
| Work | Работа | Запись occurrence как execution event. | A.15.1, B.1.6, Part D |
| Work Plan | План работы | Расписание intent как forecast. | A.15.2, A.15.3 |
| Language State Transduction | Трансдукция языка-состояния | Координация moves через reopen, respecify. | A.16, C.2.2a, B.4.1 |
| Characteristic | Характеристика | Измеримое свойство, заменяющее dimension/axis. | A.17, A.18, C.16 |
| CSLC | CSLC | Характеристика/шкала/уровень/координата для measurements. | A.18, C.16, G.0 |
| Characteristic Space | Пространство характеристик | State space с dynamics hook для моделирования. | A.19, A.3.3 |
| CN Frame | CN-фрейм | Фрейм comparability и normalization с bridges. | A.19.CN, G.0 |
| CHR Mechanism Suite | Сюита механизмов CHR | Анкер свиты для characterization с CN/CG specs. | A.19.CHR, G.5, C.23 |
| Unified Normalization Mechanism | Унифицированный механизм нормализации | UNM для CV→NCV с invariants и tri-state guards. | A.19.UNM, G.2 |
| Unified Indicatorization Mechanism | Унифицированный механизм индикаторизации | UINDM для indicator choice с evidence gating. | A.19.UINDM, E.20 |
| Unified Scoring Mechanism | Унифицированный механизм скоринга | USCM для profiles с SCP и minimal evidence. | A.19.USCM, G.2 |
| Unified Lawful Scale Aggregation | Унифицированная законная агрегация шкал | ULSAM для fold_Γ с contributor sets. | A.19.ULSAM, F.18 |
| Unified Comparison Mechanism | Унифицированный механизм сравнения | CPM для partial orders с set-valued outcomes. | A.19.CPM, G.5 |
| Selector Mechanism | Механизм селектора | Kernel для set-returning selection с eligibility. | A.19.SelectorMechanism, G.5 |
| Constraint Validity | Валидность ограничений | Eulerian stance в flows для transduction. | A.20, E.18 |
| Gate Profilization | Профилизация гейтов | OperationalGate для GateFit с decision logs. | A.21, E.17 |
| Universal Algebra of Aggregation | Универсальная алгебра агрегации | Γ для composition с invariants как IDEM, COMM. | B.1, A.1, A.9 |
| Meta Holon Transition | Транзиция мета-холона | MHT для recognizing emergence и re-identification. | B.2, B.1 |
| Trust Assurance Calculus | Калькулюс доверия и assurance | F-G-R с congruence для reliability. | B.3, A.10, C.2 |
| Canonical Evolution Loop | Канонический цикл эволюции | Run-observe-refine-deploy для continuous improvement. | B.4, A.4 |
| Canonical Reasoning Cycle | Канонический цикл рассуждений | Abduction-deduction-induction для problem-solving. | B.5, A.10 |
| Abductive Loop | Абдуктивная петля | Генерация hypotheses с plausibility filters. | B.5.2, B.5.2.1 |
| NQD | NQD | Novelty, quality, diversity для creative abduction. | B.5.2.1, C.17, C.18 |
| Role Projection Bridge | Мост проекции ролей | Bridge для domain-specific vocabulary. | B.5.3, C.3 |
| Sys CAL | Sys-CAL | CAL для physical systems с conservation laws. | C.1, B.1.2 |
| KD CAL | KD-CAL | CAL для knowledge с F-G-R и trust. | C.2, B.1.3, B.3 |
| Episteme | Эпистема | Slot relation с EntityOfConcern и grounding holon. | C.2.1, A.6.2, E.17 |
| Reliability R | Надежность R | Warrant в F-G-R с CL penalties и bridge-only reuse. | C.2.2, B.3, F.9 |
| Language State Space | Пространство языка-состояния | Chart over characteristic space для position claims. | C.2.2a, A.16, B.4.1 |
| Formality F | Формальность F | F-scale от F0-F9 для rigor и proofs. | C.2.3, B.3 |
| Evidence Graph | Граф доказательств | Структура для traceability и audit с PathId. | G.6, A.10, B.3 |
| Bridge | Мост | Mapping для cross-context sameness с CL и direction. | A.6.9, F.9, G.7 |
| Multi View Publication Kit | MVPK | Kit для multi-view descriptions с viewpoints. | E.17, A.6, G.12 |
| Assurance Level | Уровень assurance | L0-L2 с TA/VA/LA для artifact maturity. | B.3.3, B.3 |
| Epistemic Debt | Эпистемический долг | Decay evidence от freshness и staleness. | B.3.4, B.3 |
| Gamma Operator | Оператор Gamma | Агрегация для holons с invariants и proofs. | B.1, B.1.1 |
| Emergence | Эмерджентность | Recognition через MHT и BOSC triggers. | B.2, B.2.2 |
| Feedback Loop | Петля обратной связи | Supervisor-subholon для stability в control. | B.2.5, A.12 |
| Abductive Prompt | Абдуктивный промпт | Prompt с anomaly и rival-set для hypothesis generation. | B.5.2.0, B.5.2 |
| Parity Run | Parity run | Сравнение для comparability с reference plane. | A.0, G.9 |
| Illumination Map | Карта illumination | Telemetry для QD archives без dominance. | A.0, G.12:Ext.QDTelemetry |
| Portfolio | Портфолио | Set-returning selection для diversity. | G.5, A.19.SelectorMechanism |
| Dominance Regime | Режим доминирования | Policy для selection в portfolios. | G.5, G.12:Ext.PortfolioTelemetry |
| SoTA Pack | SoTA-pack | Synthesis pack для state-of-the-art с palettes. | G.2, G.10 |
| CG Spec | CG-Spec | Spec для comparability groups с minimal evidence. | G.0, A.19.CHR |
| CN Spec | CN-Spec | Spec для comparability и normalization modes. | A.19.CN, G.0 |
| RSCR Trigger | RSCR-trigger | Typed causes для refresh и selective computation. | G.11, G.Core |
| Dashboard | Дашборд | Projection over DHC series с telemetry pins. | G.12, C.21 |
| Interop Surface | Interop-surface | Summary для external sources с edition pins. | G.13, G.13:4.2 |
| External Index Card | Карта внешнего индекса | Registration внешнего источника с snapshot и edition. | G.13:4.2, G.13 |
| Claim Mapper Card | Карта мэппера claims | Recipe для mapping external в FPF artefacts. | G.13:4.2, G.13 |
| Scale Embedding Spec | Spec embedding шкал | Constraints для alignment representations. | G.13:4.2, G.13:Ext.EmbeddingBasedAlignment |
| Maturity Ladder | Лестница maturity | View для SoS-LOG с rung claims и evidence. | G.12:Ext.MaturityLadderPanel, G.8 |
| Parity Harness | Parity-harness | Harness для comparable runs с DRR. | G.9, A.0 |
| Shipping | Shipping | Pack inclusion с citations и interop hooks. | G.10, G.12:Ext.PackInclusion |
| Refresh Orchestration | Оркестрация refresh | Slice-scoped refresh на основе triggers. | G.11, G.13 |
| UTS | UTS | Unified terminology surface с tech/plain twins. | F.17, E.10, G.12 |
| LEX Bundle | LEX-bundle | Bundle для lexical discipline с twins. | E.10, F.18 |
| E TGA | E-TGA | Graph для transduction и gate crossings. | E.18, A.20 |
| Gate Fit | Gate-fit | Core для operational gates с profiles. | A.21, A.6.1 |
| Plane Map | Plane-map | Map для cross-plane reuse с penalties. | G.7, F.9 |
| Congruence Level | Уровень congruence | CL для penalty routing в bridges. | C.2.2, F.9 |
| Weakest Link | Слабое звено | Discipline для propagation R в paths. | C.2.2, G.6 |
| Evidence Decay | Устаревание доказательств | Aging evidence с epistemic debt. | B.3.4, G.11 |

## Новые термины (добавлено при ре-индексации, проверено по спеке)

| Термин (EN) | Термин (RU) | Определение | Где найти |
|-------------|-------------|-------------|-----------|
| U.Episteme | Эпистема (U.Episteme) | Несущий утверждения неагентивный холон со слотами EntityOfConcern, GroundingHolon, ClaimGraph, Viewpoint и ReferenceScheme; реализуется видами Card/View/Publication. | C.2.1, A.1, A.6.2 |
| U.EpistemePublication | Публикация эпистемы (U.EpistemePublication) | Вид эпистемы, публикующий определение/представление через форму и носитель; публикация не становится определяющей эпистемой по факту того, что её встретили. | C.2.1, E.24.PUB, A.10 |
| EntityOfConcern | Сущность интереса (EntityOfConcern) | Слот эпистемы, указывающий о ЧЁМ утверждение; сохраняется при viewing (A.6.3) и намеренно ретаргетится только через KindBridge (A.6.4). | A.6.2, A.6.3, C.2.1 |
| U.Ontic | Онтик (U.Ontic) | То, что существует независимо от своего описания; отделяется от описывающей эпистемы, публикации и формы публикации, чтобы карточки/таблицы/диаграммы не подменяли сам онтик. | E.24, E.24.PUB, A.7 |
| Controlled Semantic Coarsening | Контролируемое семантическое огрубление | Безэффектное огрубление эпистемы или публикации до узкой допустимой области использования с обязательным условием reopen к источнику при выходе за её пределы. | A.6.3.CSC, A.6.3, E.17.EFP |
| Evidence Graph Referring | Отсылка к графу доказательств | Конституционный принцип (C-4): каждое утверждение прослеживается до носителя доказательств через SCR/RSCR, с разделением носителя и сообщаемого им состояния. | A.10, G.6, B.3 |
| Evidence Graph & Provenance Ledger | Граф доказательств и реестр происхождения | Структура трассируемости (PathId) и реестр provenance, отделённая от принципа отсылки (A.10); хранит цепочки доказательств для аудита. | G.6, A.10, B.3 |
| U.LanguageStateSpace | Пространство языка-состояния (U.LanguageStateSpace) | Карта языка-состояния поверх U.CharacteristicSpace: частичные координаты и пороги для публикации position-claim до публикации endpoint-claim. | C.2.2a, A.16, B.4.1 |
| Publication Discipline (Ontic Description) | Дисциплина публикации (описание онтика) | Держит онтик, его описывающую эпистему, публикацию и форму публикации различимыми; карточки/схемы/виды/источники не становятся онтиком по внешнему виду. | E.24.PUB, E.24, C.2.1 |
| NQD Onboarding Glossary | Онбординг-глоссарий NQD (A.0) | Вводный глоссарий по novelty/quality-diversity и explore/exploit (E/E-LOG): какие термины обязан публиковать генератор/селектор/публикация набора результатов, чтобы избежать single-winner bias. | A.0, C.18, C.19 |
| PublicationUnit Stability Discipline | Дисциплина стабильности единицы публикации | Правила стабильности PublicationUnit при ауд­ите и редактировании: восстановление локальной головы и сохранение первичной EntityOfConcern единицы публикации. | E.17.AUD, E.17, E.17.AUD.OOTD |
| U.EpistemicRetargeting | Эпистемический ретаргетинг (U.EpistemicRetargeting) | Безэффектный морфизм эпистемы, намеренно меняющий entityOfConcernRef под объявленным KindBridge, инвариантом и границей потерь, с сохранением только проверяемых мостом обязательств. | A.6.4, A.6.3, E.18 |

> Правки ссылок при ре-индексации `40b232f` (полный дифф — в `CHANGES-fpf-spec.md`): `A.6.Q` quality-term restoration переехал в `C.16.Q`, relational — в `A.6.P`; планируемые заглушки `B.2.1`/`B.3.1`/`B.3.2` свёрнуты под живых родителей `B.2`/`B.3` (`B.2.2` Meta-System Transition); термин «Ontic Debt» в спеке отсутствует — используется `U.Ontic` / `Epistemic Debt` (B.3.4). `describedEntity` → `EntityOfConcern` почти завершено (8 остаточных упоминаний).
