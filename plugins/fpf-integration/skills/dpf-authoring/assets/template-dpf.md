---
dpf_id: "DPF-XXX"
name: "Название компетенции"
kind: "Local Practice Framework"   # Domain Principle Framework | Local Practice Framework
owner: ["role"]                     # primary owner(s)
referenced_by: ["role", "role"]    # роли, которые ссылаются (shared)
status: "stub"                     # stub | active | stage-0
grounded_in: ["FPF E.4.DPF", "..."]
date: "YYYY-MM-DD"
review_due: "YYYY-MM-DD"
---

# DPF-XXX: Название

> Авторинг по FPF **E.4.DPF** (first-hour-route допустим: грубый, но inspectable > длинного монолита без структуры).
> Это `kind` для bounded context проекта. Роли-владельцы координируют работу согласно этому DPF.
> **FPF-разделы (по ID) читать живьём через скилл `fpf-integration`, не выжимки** (иначе дрейф). Метод и фазы — `DPF-AUTHORING/`.
>
> **Структурный отчёт носителя (CC-DPF.8):** <для кого этот файл и с какой первой задачей; что на переднем плане (паттерны); что сознательно огрублено/опущено и куда возврат за деталями (references/, источники)>.
>
> Пока status = stub/stage-0, пакет в терминах E.4.DPF.DA — **seedOnly**: заготовка, а не проверенный свод; НЕ процессное состояние в этом файле, а честный статус пакета.

## 1. Контекст (CC-DPF.1)
- **Bounded context:** <домен/локальная ситуация, где значения этого DPF держатся>
- **Intended reader:** <кто и в какой роли это читает>
- **First use:** <первая полезная задача, которую DPF помогает решить>
- **Non-use boundary:** <где DPF НЕ применяется>

## 2. Source pack — G.2 (CC-DPF.2)
> **Реестр «что взято / что намеренно отброшено» по каждому референсу — [`references/source-pack.md`](references/source-pack.md).** Ниже — сводка.
- **Adopted payload:** <что берём в основу: источники, факты из domain.md, прецеденты>
- **Rejected alternatives:** <что рассмотрели и отвергли, и почему>
- **Examples:** <конкретные примеры/кейсы>
- **Claim status:** <fact | hypothesis | opinion для ключевых утверждений (A.10)>
- **Currentness:** <дата актуальности источников; когда протухнут>

## 3. Архитектурное решение — PFAD (CC-DPF.3)
- **Purpose:** <зачем этот DPF>
- **Pattern split:** <на какие паттерны/правила разбит>
- **Dependency boundary:** <от чего зависит: другие DPF, DEC, domain.md>
- **Must NOT land:** <что НЕ должно сюда попадать (граница с соседними DPF)>

## 4. Имена — F.18 (CC-DPF.4)
- **Durable:** <устоявшиеся термины → glossary.md>
- **Provisional:** <временные имена/алиасы>

## 5. Паттерны — E.8 (CC-DPF.6)
> 1–3 паттерна. Каждый: распознавание → решение → worked slice → локальный анти-паттерн → conformance.

### Паттерн 1: <имя>
- **Когда применять (recognition):** ...
- **Решение (positive solution):** ...
- **Worked slice:** <конкретный пример из нашего проекта>
- **Локальный анти-паттерн:** <как НЕ надо>
- **Conformance:** <как проверить, что применён правильно>

## 6. Relations & editions — E.4.PFR
- **Uses / зависит от:** <DPF-..., DEC-...>
- **Shared с ролями:** <если referenced_by>
- **Supersedes / superseded_by:** <если применимо>

## 7. Разнородные приёмочные случаи (E.4.DPF, питает D8)
> Для полного DPF (фаза 6) — 2–3 НЕпохожих кейса, где паттерны обязаны сработать за пределами мотивирующего примера. На стадии stub допустимо оставить пустым.

- **Случай 1:** <ситуация из другого угла домена → какой паттерн применился и что показал>

## 8. Quality & refresh route — E.4.DPF.DA/E.21/E.23/G.11 (CC-DPF.7)
- **Что оценивается:** пакет целиком по E.4.DPF.DA (11 координат D1–D11 + PFM-подпроход; статус: admissibleForDeclaredDPFUse / seedOnly / repairBeforeDPFUse / refreshNeeded), паттерны — по E.21
- **Refresh triggers:** <что переоткрывает DPF: изменение источника, DEC, рынка, ядра, редакции FPF>

## Артефакты каталога (references/ · assets/)
- `references/source-pack.md` — **реестр provenance (G.2): что взято / намеренно отброшено по каждому источнику (обязателен).**
- `references/<...>.md` — выдержки ресёрча, источники, спеки, evidence.
- `assets/<...>` — шаблоны, чеклисты, код-сниппеты, диаграммы компетенции.

## Carrier note (CC-DPF.5)
<если использованы сгенерированные/внешние материалы как evidence — отметить admission (C.33/C.34/C.35)>

## Conformance checklist (E.4.DPF:7)
- [ ] CC-DPF.1 Context declared
- [ ] CC-DPF.2 Source pack present
- [ ] CC-DPF.3 Architecture decision present
- [ ] CC-DPF.4 Names prepared
- [ ] CC-DPF.5 Carriers admitted (если применимо)
- [ ] CC-DPF.6 Patterns drafted (E.8; скелеты/заготовки честно помечены как seed, не выданы за паттерны)
- [ ] CC-DPF.7 Quality & refresh routes present
- [ ] CC-DPF.8 Структурный отчёт носителя в шапке (кому, что на переднем плане, что огрублено, куда возврат)
- [ ] CC-DPF.9 Примат решения задач (названы типовые задачи, блокируемые провалы и SoTA-ходы; не каталог терминов)
