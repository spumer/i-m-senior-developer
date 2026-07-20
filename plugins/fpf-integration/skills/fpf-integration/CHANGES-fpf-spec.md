# FPF-Spec — что изменилось (журнал ре-индексации)

> Индекс скилла обновлён под FPF-Spec.md @ ailev/FPF `44dd88188a07` (2026-07-12, «readme 15 usage cards»).
> Полный SHA: `44dd88188a07646ef23aca32627a3f670525853f`. Спека выросла до 97 255 строк, реестр — 285 паттернов (280 Stable + 5 Planned).
> Предыдущая база индекса — `40b232f11ed9` (2026-06-26, 279 паттернов: 274 Stable + 5 Planned).

## Сводка (ре-индексация 2026-07-14)

- **+6 ID**, **−0 ID**; **13 переименований**. Покрыты коммиты апстрима: `e2453d1a` (A.22.CGUS, E.18.3), `f509a921` (seeds по CGUS), `4a55618e` (E.11.PUA + readme-карточки), `44dd8818` (readme).
- **Добавлено:** `A.22.CGUS` Constraint-Governed Unfolding Structure, `A.6.3.NAR` Structure-to-Narrative Rendering, `E.11.PUA` Pattern Use in a Working Situation and First Useful Result, `E.18.3` Constraint-Governed Transformation-Flow Unfolding Structure (специализация A.22.CGUS), `E.4.DPF.DA` DPF Package-Adequacy Evaluation CharacteristicSpace, `E.4.FPF` First Principles Framework Form and Publication-or-Access Carrier Assembly.
- **Переименования (выборка из 13):** `A.2.2` «System Ability (dispositional property)» → «System Ability Envelope and Measures»; `A.3.1` «The Abstract Way of Doing» → «Context-Defined Way of Doing»; `A.3.2` «The Recipe for Action» → «Description Episteme for a Way of Doing»; `A.15.1` «The Record of Occurrence» → «Dated Performed Work Occurrence»; `E.4.DPF` «…Local-Monolith Landing» → «…Publication-or-Access Carrier Assembly»; `E.11` → «Practical-Use Guidance and Pattern Discovery»; `B.1.5` `Γ_method` → `Gamma_method` (лексическая нормализация).
- **Структура карты:** разделы теперь повторяют реестр спеки — 22 раздела (части + кластеры) вместо 16 кластеров. Раньше строки частей без кластеров (B, D, G, I) сваливались в таблицу предыдущего кластера (G и I — в хвост F.IV); теперь у них свои разделы `## Part …`, а `A.0` — под «Part A».
- **Починено в карте:** 7 строк реестра (`A.19.UNM/UINDM/USCM/ULSAM/CPM/SelectorMechanism`, `G.8`) содержат неэкранированные `|` внутри `` `{pass|degrade|abstain}` `` — прошлая генерация рвала на них ячейки; теперь пайпы склеены и экранированы как `\|`, все 285 строк парсятся ровно на 5 колонок.

## Правки компаньонов индекса (2026-07-14)

- `fpf-grep-patterns.md` — все hit-counts перепроверены (метрика — вхождения, не строки; подтверждена сверкой с задокументированными значениями): `U\.Work` 823→883, `U\.Method` 420→581, `Characteristic` 979→1000, `U\.Episteme` 691→1050, `EntityOfConcern` 1991→2076, `CSC` 156→165. Все паттерны (включая renamed-секцию) матчатся; «ontic debt» — по-прежнему 0.
- `fpf-tasks-lookup.md` — grep-паттерн «dispositional property» протух (0 вхождений после переименования A.2.2) → заменён на «ability envelope». ID-ссылки сверены: висячих нет (ничего не дерегистрировано).
- `fpf-glossary.md` — шапка провенанса обновлена; ID-ссылки валидны, `describedEntity` — по-прежнему 8 остаточных упоминаний.

---

# Предыдущая ре-индексация: `40b232f11ed9`

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
