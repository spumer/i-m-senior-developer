# Scope (E.4.DPF:1, Фаза 0) — DPF-ADVERSARIAL-REVIEW

> Компетенция: **DPF-ADVERSARIAL-REVIEW**. Owner: guardian. Дата: 2026-07-06.

## Bounded context (A.1.1)

Функция внутри метода авторинга сводов знаний (`DPF-AUTHORING`, FPF E.4.DPF × G.2): **адверсарная проверка** пакета знаний на двух его точках — Фаза 2 (Bridge / тезисы-антитезисы) и Фаза 6 (Quality/critic/package adequacy). Предмет — сам ПАКЕТ (свод принципов, DPF), не продукт и не код. Роль guardian применяет здесь дисциплину «devil's advocate + completeness-critic», отдельную от исследовательской роли (owner делает research, guardian оспаривает — DEC-003, разделение ролей против «AI-consensus = evidence»).

Что входит в контекст:
- Диалектика тезис/анти-тезис по каждому claim'у source-pack (scope валидности + NQD ≥3 альтернатив, B.5.2.1).
- BridgeMatrix: явное сведение традиций, явные потери при слиянии (no silent fusion, G.2d).
- Контрпримеры как границы применимости (похоже, но не применять — A.11 Sharp Boundary).
- Devil's advocate против иллюзии «согласие ИИ с собой = evidence» (когда одна LLM-сессия сама придумывает тезис и сама же его подтверждает).
- Completeness-критика: какая традиция SoTA упущена, какой claim без источника, какая тензия не покрыта.
- Оценка пакета целиком по FPF E.4.DPF.DA: подпроход PFM1–PFM11 (форма) → координаты D1–D11 (содержание) → честный статус (admissible / seedOnly / repairBeforeDPFUse / refreshNeeded) без завышения за счёт среднего балла паттернов (CC-DPFDA.4) и без повышения заготовки без evidence (CC-DPFDA.8).

## Intended reader

Роль **guardian** (owner компетенции) — при выполнении Фазы 2 и Фазы 6 конвейера `dpf-authoring-pipeline` для ЛЮБОГО DPF в каталоге проекта. Вторично — facilitator (гейтит проход Фазы 6) и keeper (держит формат носителя).

## First use

Guardian получает на вход `sota-research.md` (Фаза 1, уже готов) конкретного авторимого DPF и производит:
1. `theses-antitheses.md` (Фаза 2) — BridgeMatrix + тезис/анти-тезис по каждому claim + контрпримеры + каталог типовых ошибок компетенции.
2. `package-adequacy-<date>.md` (Фаза 6) — таблица D1–D11 с обоснованием, PFM-подпроход, итоговый статус пакета + repair-шаги, если статус ниже `admissible`.

## Non-use boundary (A.11 Sharp Boundary)

- **НЕ** security-аудит продукт-кода / OWASP-ревью (→ `DPF-SECURITY-REVIEW`, owner test+guardian).
- **НЕ** риск-менеджмент проекта / kill-criteria / pre-mortem бизнес-решений (→ `DPF-RISK`, owner guardian, но другая компетенция).
- **НЕ** генерация исходного ресёрча / SoTA-харвест (→ Фаза 1 метода DPF-AUTHORING, обычно ведёт owner компетенции, не guardian).
- **НЕ** сама сборка DPF.md (Фаза 5) — guardian критикует, не пишет паттерны за автора.
- **НЕ** Decider Protocol / голосование команды по бизнес-тензиям (→ facilitator, `core-protocols.md`).
- Похоже, но не то же самое: обычный code review (проверяет корректность реализации против спеки) — здесь предмет проверки — корректность и полнота **свода принципов** против SoTA, а не код против ARCH.
