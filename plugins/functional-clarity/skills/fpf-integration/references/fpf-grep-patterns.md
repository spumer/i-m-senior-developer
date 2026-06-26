# FPF — Паттерны для Grep

> Сгенерировано из FPF-Spec.md @ ailev/FPF `40b232f11ed9` (2026-06-26). Полный SHA: `40b232f11ed950ed34082273c57ff4f6c45b7f06`.
> Проверять актуальность: сравни с `~/.claude/knowledge/fpf/FPF-Spec.version` и текущим upstream.

> Используй с инструментом Grep по FPF-Spec.md. Паттерны проверены: каждый реально матчится в спеке этого SHA.

| Паттерн | Что найдёт |
|---------|-----------|
| `U\.Holon (121)` | (паттерн навигации) |
| `U\.BoundedContext (249)` | (паттерн навигации) |
| `U\.RoleAssignment (290)` | (паттерн навигации) |
| `U\.Capability (51)` | (паттерн навигации) |
| `U\.PromiseContent (91)` | (паттерн навигации) |
| `U\.EvidenceRole (7)` | (паттерн навигации) |
| `U\.RoleStateGraph (1)` | (паттерн навигации) |
| `U\.Scope (49)` | (паттерн навигации) |
| `U\.RoleAlgebra (1)` | (паттерн навигации) |
| `U\.Commitment (99)` | (паттерн навигации) |
| `U\.SpeechAct (47)` | (паттерн навигации) |
| `U\.Method (420)` | (паттерн навигации) |
| `U\.MethodDescription (182)` | (паттерн навигации) |
| `U\.Dynamics (91)` | (паттерн навигации) |
| `Temporal Duality (13)` | (паттерн навигации) |
| `Signature Stack (18)` | (паттерн навигации) |
| `Boundary Norm Square (17)` | (паттерн навигации) |
| `U\.EffectFreeEpistemicMorphing (35)` | (паттерн навигации) |
| `U\.EpistemicViewing (71)` | (паттерн навигации) |
| `U\.EpistemicRetargeting (51)` | (паттерн навигации) |
| `Relational Precision Restoration (7)` | (паттерн навигации) |
| `Strict Distinction (46)` | (паттерн навигации) |
| `Universal Core (4)` | (паттерн навигации) |
| `Cross-Scale Consistency (1)` | (паттерн навигации) |
| `Evidence Graph (33)` | (паттерн навигации) |
| `Ontological Parsimony (13)` | (паттерн навигации) |
| `External Transformer (2)` | (паттерн навигации) |
| `Agential Role (5)` | (паттерн навигации) |
| `Advanced Mereology (12)` | (паттерн навигации) |
| `Role-Method-Work (9)` | (паттерн навигации) |
| `U\.Work (823)` | (паттерн навигации) |
| `U\.WorkPlan (221)` | (паттерн навигации) |
| `Characteristic (979)` | (паттерн навигации) |
| `CSLC (159)` | (паттерн навигации) |
| `Characteristic Space (2)` | (паттерн навигации) |
| `CN-frame (15)` | (паттерн навигации) |
| `Unified Normalization Mechanism (4)` | (паттерн навигации) |
| `Unified Scoring Mechanism (3)` | (паттерн навигации) |
| `Unified Comparison Mechanism (3)` | (паттерн навигации) |
| `Meta-Holon Transition (10)` | (паттерн навигации) |
| `F-G-R (24)` | (паттерн навигации) |
| `Canonical Evolution Loop (17)` | (паттерн навигации) |
| `Canonical Reasoning Cycle (15)` | (паттерн навигации) |
| `Abductive Loop (9)` | (паттерн навигации) |
| `NQD (178)` | (паттерн навигации) |

## Исправлены под текущую спеку (переименованные концепты)

| Старый (не находится) | Новый паттерн | Что найдёт |
|------------------------|---------------|-----------|
| `Language-State Transduction` | `U\.LanguageStateSpace` | Трансдукция языка-состояния |
| `CHR Mechanism Suite` | `CHRMechanismSuite` | Сюиты CHR |
| `Selector Mechanism` | `SelectorMechanism` | Механизмы селекции |
| `Constraint Validity` | `ConstraintValidity` | Валидность ограничений |
| `Gate Profilization` | `GateProfilization` | Профилизация гейтов |
| `Gamma Operator` | `Γ-fold` | Оператор Gamma |
| `MUST\|SHALL` | `MUST|SHALL` | Нормативные требования |
| `MAY\|SHOULD` | `MAY|SHOULD` | Рекомендации |

## Новые паттерны (крупные новые области спеки)

| Паттерн | Что найдёт |
|---------|-----------|
| `U\.Episteme` | The claim-bearing, non-agentive episteme type — the core knowledge object of FPF (defined in C.2.1 'U.Episteme - Epistemes and their slot relation'; the holon root is now A.1 'Holon Ontic Foundation (U.Holon and Admitted Holon Kinds)'). 691 hits; navigates episteme definitions, kinds (U.EpistemeCard/View/Publication), and definitionEpistemeRef usage across the spec. |
| `U\.EpistemePublication` | The publication of an episteme as a distinct object from the episteme itself and from its carrier/projection (governed by A.10 Evidence Graph Referring and E.24.PUB). 86 hits; key for the 'a credential/badge/excerpt is only a publication, not the governing register entry' distinction and EFEM object kinds (A.6.3). |
| `U\.Publication` | Publication-discipline area: U.PublicationScope and publication carriers that gate usage (USM publication discipline, MVPK views). 25 hits; pins where PublicationScope must be declared and kept a subset of ClaimScope/WorkScope, plus Bridge+CL requirements for cross-context publications. |
| `EntityOfConcern` | The EntityOfConcern (EoC) — the entity a pattern is fundamentally about, used pervasively to fix the core boundary of each pattern (e.g. 'Core boundary: the CharacteristicSpace is the EoC here'). 1991 hits; the highest-frequency new locator for finding what any pattern centers on. Companion abbreviation 'EoC' (57) for terser scans. |
| `U\.Ontic` | The Ontic Introduction Discipline area (E.24, E.24.CD Ontic Candidate Detection, E.24.PUB Ontic Description and Publication Discipline) — governs when a repeated construct becomes a durable action-facing ontic vs staying a local record. 29 hits. NOTE: the requested term 'ontic debt' has NO literal match in the spec (0 hits); U.Ontic is the actual governing concept for that minting/avoidance discipline. |
| `Controlled Semantic Coarsening` | The A.6.3.CSC pattern — a specialization under A.6.3 U.EpistemicViewing for same-lineage coarsening (summary/redaction/dashboard tile) that may stand in only for a narrower admissible use and must reopen the source-bearing episteme otherwise. 31 hits; lands on the section heading '## A.6.3.CSC - Controlled Semantic Coarsening' and its reopen-trigger rules. Abbreviation 'CSC' (156) is broader. |
| `Evidence Graph Referring` | The A.10 pattern title — claim-bound evidence and provenance graph (evidence carriers, authority-reliance evidence path, status register, register excerpt, SCR/RSCR). 17 hits; pins the A.10 section heading '## A.10 - Evidence Graph Referring: Claim-Bound Evidence and Provenance Graph' and references to it as a guard alongside Strict Distinction. |
