# FPF — Поиск по задаче

> Найди задачу → используй Grep-паттерны для поиска в FPF-Spec.md
>
> Сверено с FPF-Spec.md @ ailev/FPF `646b0b9b164f` (2026-06-17). Секции-ID стабильны;
> если grep-паттерн не находится, см. актуальные/починенные в `fpf-grep-patterns.md`
> (концепты переименованы: `describedEntity` → `EntityOfConcern`,
> `Language-State Transduction` → `Language-State Move`).

| Задача | Секции | Grep-паттерны |
|--------|--------|---------------|
| Разделить систему на bounded contexts | A.1.1, A.2.6, F.0.1 | "BoundedContext", "semantic frame", "bridge", "context slices" |
| Определить роли в команде | A.2, A.2.1, A.13, A.2.7 | "RoleAssignment", "AgentialRole", "role taxonomy", "role algebra" |
| Моделировать способности системы | A.2.2, A.2.6, B.2.4 | "Capability", "WorkScope", "dispositional property", "ability" |
| Создать обещания для сервисов | A.2.3, A.6.C, F.12 | "PromiseContent", "SLO", "SLA", "accessSpec" |
| Управлять доказательствами claims | A.2.4, A.10, B.3 | "EvidenceRole", "evidence graph", "SCR" |
| Моделировать состояния ролей | A.2.5, A.19, A.3.3 | "RoleStateGraph", "RSG", "state machine" |
| Определить scope применимости | A.2.6, A.6.1 | "Unified Scope Mechanism", "USM", "ClaimScope" |
| Составить commitments и deontics | A.2.8, A.6.B | "Commitment", "deontics", "BCP-14" |
| Моделировать речевые акты | A.2.9, A.6.C | "SpeechAct", "provenance", "institutes" |
| Описать трансформации и действия | A.3, A.3.1, A.3.2 | "Transformer Quartet", "Method", "MethodDescription" |
| Моделировать динамику изменений | A.3.3, A.19 | "Dynamics", "state evolution" |
| Управлять эволюцией систем | A.4, B.4 | "Temporal Duality", "evolution loop" |
| Разработать расширяемое ядро | A.5, A.IV | "Open-Ended Kernel", "extension layering" |
| Управлять границами и signatures | A.6, A.6.0, A.6.1 | "Signature Stack", "U.Signature", "U.Mechanism" |
| Разложить boundary statements | A.6.B, A.6.C | "Boundary Norm Square", "Contract Unpacking" |
| Трансформировать эпистемы без эффектов | A.6.2, A.6.3, A.6.4 | "EffectFreeEpistemicMorphing", "EpistemicViewing", "EpistemicRetargeting" |
| Восстановить точность отношений | A.6.P, A.6.Q, A.6.A | "RelationalPrecisionRestoration", "Q-TERM", "ACT-INV" |
| Избежать category errors | A.7, A.V | "Strict Distinction", "Clarity Lattice" |
| Обеспечить universality концептов | A.8, A.9 | "Universal Core", "Cross-Scale Consistency" |
| Обеспечить traceability через evidence | A.10, B.3 | "Evidence Graph Referring", "F-G-R" |
| Минимизировать онтологию | A.11 | "Ontological Parsimony" |
| Моделировать self-modification | A.12, B.2.5 | "External Transformer", "Feedback Loop" |
| Определить agency в ролях | A.13, C.9 | "Agential Role", "Agency Spectrum" |
| Моделировать part-of отношения | A.14, A.6.H | "Advanced Mereology", "RPR-WHOLE" |
| Выровнять роль-метод-работу | A.15, A.15.1, A.15.2 | "Role-Method-Work Alignment", "U.Work", "U.WorkPlan" |
| Координировать language-state | A.16, A.16.0 | "Language-State Transduction", "U.LanguageStateTransductionTrajectory" |
| Нормализовать термины измерений | A.17, A.18, Part-K | "CHR-NORM", "CSLC-KERNEL", "replacement map" |
| Моделировать пространство характеристик | A.19, A.19.CN | "CHR-SPACE", "CN-frame" |
| Реализовать normalization | A.19.UNM, G.2 | "Unified Normalization Mechanism", "UNM" |
| Создать индикаторы | A.19.UINDM | "Unified Indicatorization Mechanism" |
| Выполнить скоринг | A.19.USCM | "Unified Scoring Mechanism" |
| Агрегировать шкалы | A.19.ULSAM | "Unified Lawful Scale Aggregation" |
| Сравнить профили | A.19.CPM | "Unified Comparison Mechanism" |
| Выбрать портфолио | A.19.SelectorMechanism, G.5 | "Selector Mechanism", "portfolio" |
| Проверить валидность flows | A.20 | "U.Flow.ConstraintValidity" |
| Профилизировать гейты | A.21 | "GateProfilization" |
| Агрегировать холоны | B.1, B.1.1 | "Universal Algebra of Aggregation", "Gamma" |
| Распознать эмерджентность | B.2, B.2.1 | "Meta-Holon Transition", "BOSC Triggers" |
| Рассчитать trust | B.3, C.2 | "Trust & Assurance Calculus", "F-G-R" |
| Реализовать эволюционный цикл | B.4, B.4.1 | "Canonical Evolution Loop", "Observe-Notice-Stabilize-Route" |
| Организовать рассуждения | B.5, B.5.2 | "Canonical Reasoning Cycle", "Abductive Loop" |
| Генерировать креативные идеи | B.5.2.1, C.17 | "Creative Abduction with NQD", "NQD" |
| Интегрировать domain language | B.5.3, C.3 | "Role-Projection Bridge" |
| Моделировать физические системы | C.1, B.1.2 | "Sys-CAL" |
| Управлять знаниями и trust | C.2, C.2.1 | "KD-CAL", "U.Episteme" |
| Пропагировать reliability | C.2.2, F.9 | "Reliability R", "CL" |
| Определить formality | C.2.3 | "Unified Formality Characteristic F" |
| Создать дашборд | G.12, C.21 | "Dashboard", "DHC series" |
| Интегрировать внешние источники | G.13, G.13:4.2 | "Interop Hooks", "ExternalIndexCard" |