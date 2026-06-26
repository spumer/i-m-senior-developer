# FPF-Spec — что изменилось (журнал ре-индексации)

> Индекс скилла обновлён под FPF-Spec.md @ ailev/FPF `40b232f11ed9` (2026-06-26, «architecture and FPF ecosystem architecture»).
> Полный SHA: `40b232f11ed950ed34082273c57ff4f6c45b7f06`. Спека выросла до ~93 220 строк, реестр — 279 паттернов (274 Stable + 5 Planned).
> Предыдущая база индекса — `646b0b9b164f` (2026-06-17, 279 паттернов: 242 Stable + 37 Planned).

## Сводка

- **+33 ID**, **−32 ID**, нетто +1; **59 переименований/нормализаций заголовков**. Реестр прошёл крупную чистку: число Planned-заглушек упало с 37 до 5.
- **Крупный новый слой архитектуры** (совпадает с месседжем коммита): `C.30.AD.BA`, `C.30.TFS-REL`, всё семейство `C.32.*` (синтез кандидатов архитектуры, Conway-соответствие, decision records, adequacy, failure-repair, starter-packs), `C.33`–`C.35` (структурная адекватность/соответствие/синтез) и `C.36` (культурная эволюция).
- **Многоуровневая этика переписана из заглушек в живые паттерны**: `D.1`–`D.4` (плюрализм ценностей, этика по уровням холона, межуровневые конфликты, медиация); старые Planned-подузлы `D.2.1`–`D.4.2`, `D.5.1`, `D.5.2` дерегистрированы, `D.5` остаётся.
- **Аннексные Части H / J / K и часть I удалены из реестра** как самостоятельные объекты (глоссарий-аннекс, индексы concept-to-pattern, лексический долг K.1–K.3). Живым остаётся только `I.2` (Expanded Entry Disambiguation, Stable).
- **Семейство авторинга экосистемы FPF**: `E.4.DPF` / `E.4.PFR` / `E.4.PFAD` (Domain Principle Framework, pattern-framework relation, architecture-decision).
- Сквозная **нормализация заголовков**: с многих снят префикс `U.`, унифицированы дефисы/тире; обновлены контрактные имена `A.2.4` (`U.EvidenceRole` → Episteme Evidence-Use), `A.2.5` (`U.RoleStateGraph` → RoleStateRelation@BoundedContext), `A.2.7` (`U.RoleAlgebra` → RoleRelationStructure@BoundedContext); B.1/B.2 ушли от Γ-формулировок к языку агрегации холонов.
- `A.0` (Onboarding Glossary NQD/E-E-LOG) теперь индексируется — в старой карте его не было.

## Добавлено (33)

- **Архитектура (C.30/C.32–C.36):** `C.30.AD.BA` Built-Asset Architecture Description, `C.30.TFS-REL` Architecture Transformation-Flow Structure Relation, `C.32` Architecture Candidate Synthesis + `C.32.ACE/ACS/ADA/ADR/CONWAY/FAIL/HCS/MLAO/P2S/PAD`, `C.33` Structural Information Adequacy, `C.34` Structural Correspondence/Equivalence/Morphism Adequacy, `C.35` Structural Synthesis & Discovery Adequacy, `C.36` Cultural Evolution Engineering + `C.36.P`.
- **Этика (Part D):** `D.1` Ethical Value Plurality & FPF Boundary, `D.2` Multilevel Ethics For System-Holon Work, `D.3` Interlevel Ethical Conflict Structure, `D.4` Ethical Mediation & Decision Use.
- **Экосистема/авторинг (Part E):** `E.4.DPF`, `E.4.PFR`, `E.4.PFAD`, `E.10.MOVE` (Move & Readiness wording precision), `E.11.PUR` (Pattern-Use Recommendation), `E.24.UK` (U-kind Governance).
- **Ядро/прочее:** `A.0` Onboarding Glossary, `A.15.5` Work-Entry Readiness & Full-Kit Preparation, `A.19.SOURCE-SET-SPACE-SUBSTRATE`, `A.19.DECLARED-SUBSTRATE-INTERPRETIVE-VIEW`, `B.2.P` Emergence & MHT Precision Restoration.

## Удалено (32)

- **Planned-заглушки без тела:** `B.2.1` (BOSC Triggers), `B.3.1` (Components & Epistemic Spaces), `B.3.2` (Evidence & Validation Logic), `B.4.2`, `B.4.3`, и планируемые CAL-стабы `C.4`, `C.7`, `C.10`, `C.12`, `C.15`. Содержание свёрнуто под живых родителей (эмерджентность — `B.2`/`B.2.2`; F-G-R-компоненты — `B.3`; CHR-семейства — `C.16`/`A.19`/`C.7`-эквиваленты внутри C).
- **Старые Planned-подузлы этики:** `D.2.1`–`D.2.4`, `D.3.1`, `D.3.2`, `D.4.1`, `D.4.2`, `D.5.1`, `D.5.2` — заменены живыми `D.1`–`D.4` (+ `D.5`).
- **Аннексы целиком:** `H.1`–`H.3`, `I.1`, `I.3`, `I.4`, `J.1`–`J.3`, `K.1`–`K.3` — дерегистрированы из реестра спеки.

## Переименования (выборка из 59)

- Снятие префикса/нормализация: `A.8` «Universal Core (C-1)» → «Universal Core Principle»; `A.11` «… (C-5)» → «Ontological Parsimony»; `A.12` «External Transformer & Reflexive Split (C-2)» → «Acting-Side Externalization and Reflexive Split»; `A.20` «U.Flow.ConstraintValidity» → «Flow Constraint Validity».
- Контрактные имена: `A.1` → «Holon Ontic Foundation (U.Holon and Admitted Holon Kinds)»; `A.2.4` → «Episteme Evidence-Use and Status-Use Relations»; `A.2.5` → «RoleStateRelation@BoundedContext …»; `A.2.7` → «RoleRelationStructure@BoundedContext …».
- B-кластер: `B.1` «Universal Algebra of Aggregation (Γ)» → «Holon Aggregation and Part-Whole Construction»; `B.2` → «Meta-Holon Transition - Whole Reidentification»; `B.5.3` «Role-Projection Bridge» → «Domain-Concept Bridge».

## Правки компаньонов индекса

- `fpf-grep-patterns.md` — все hit-counts перепроверены и обновлены под новый SHA (спека выросла: напр. `U\.Work` 618→823, `Characteristic` 742→979, `U\.Method` 326→420). Все паттерны (включая renamed-секцию) по-прежнему матчатся. Стейл-ссылка в описании `U.Episteme` поправлена: дом определения — `C.2.1`, не старый заголовок `A.1`.
- `fpf-glossary.md` / `fpf-tasks-lookup.md` — ID-ссылки сверены по валидности с реестром `40b232f`. Починены висячие ссылки на удалённые заглушки: `B.3.1`/`B.3.2` → `B.3`, `B.2.1` → `B.2.2`, `A.6.Q` → `A.6.RSIR` (relational) / `C.16.Q` (quality-term, живой дом). Стейл-термин `describedEntity` → `EntityOfConcern` (в спеке осталось 8 остаточных упоминаний).
