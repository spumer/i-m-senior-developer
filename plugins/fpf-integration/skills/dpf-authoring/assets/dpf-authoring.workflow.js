export const meta = {
  name: 'dpf-authoring-pipeline', // двигатель; парадная дверь — скилл dpf-authoring (../SKILL.md)
  description: 'Авторинг DPF по методу DPF-AUTHORING (E.4.DPF × G.2, ред. FPF f7c7e93f): SoTA→тезисы/анти-тезисы→source-pack→сборка→критик (CC-DPF.1–9 + оценка пакета E.4.DPF.DA). Роли фаз — встроенные в скилл пакеты компетенций формата framework-apply (Bridge/Critic ← frameworks/DPF-ADVERSARIAL-REVIEW, Source-pack/Assemble ← frameworks/DPF-KNOWLEDGE-CURATION) — зависимостей от .claude/agents проекта нет. Все артефакты передаются ТОЛЬКО через файлы. Список компетенций — ТОЛЬКО явный args.competencies (fail-fast при пустом: массового bootstrap-фолбэка нет — инцидент 2026-07-04, прогон всех 29 вместо 5).',
  phases: [
    { title: 'SoTA Harvest' },
    { title: 'Bridge' },
    { title: 'Source-pack' },
    { title: 'Assemble' },
    { title: 'Critic' },
  ],
}

// ============ args (fail-fast) ============
// Раннер может донести args JSON-строкой — парсим сами (инцидент 2026-07-04:
// строковый args не распознался, сработал bootstrap-фолбэк и прогнал ВСЮ карту).
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})

// ============ config ============
// Скилл самодостаточен: метод и шаблон лежат ВНУТРИ скилла. Обязательные внешние
// пути: args.repoRoot (целевой проект, куда пишутся каталоги DPF) и args.skillDir
// (каталог скилла, откуда читаются метод, шаблоны и пакеты ролей). Тихого
// дефолта записи нет намеренно: запись в чужую репу должна быть невозможна
// (класс ошибки bootstrap-инцидента 2026-07-04).
if (!A.repoRoot) {
  throw new Error(
    'FAIL-FAST: args.repoRoot не передан. Укажи абсолютный путь ТЕКУЩЕГО проекта — ' +
    'туда будут записаны каталоги DPF (<repoRoot>/project/frameworks, либо задай args.frameworksDir).'
  )
}
if (!A.skillDir) {
  throw new Error(
    'FAIL-FAST: args.skillDir не передан. Укажи абсолютный путь каталога скилла dpf-authoring — ' +
    'тот, из которого читался SKILL.md (…/skills/dpf-authoring). Из него конвейер читает ' +
    'references/method.md, assets/ и встроенные пакеты frameworks/.'
  )
}
const SKILL_DIR = A.skillDir
const ROOT = A.repoRoot
const FW = A.frameworksDir || ROOT + '/project/frameworks'
const METHOD = SKILL_DIR + '/references/method.md'
const TEMPLATE = SKILL_DIR + '/assets/template-dpf.md'
const EXEMPLAR = A.exemplar || TEMPLATE // опц. args.exemplar: абс. путь лучшего DPF целевого проекта как эталон формата
const COMPMAP = FW + '/competency-map.md'
const FPF_SPEC = '~/.claude/knowledge/fpf/FPF-Spec.md'
const FPF_EDITION = A.fpfEdition || 'ailev/FPF@f7c7e93f' // редакция, под которую запинен метод (references/method.md)
const RUN_DATE = A.date || ''

// ---- список компетенций: ТОЛЬКО явный (bootstrap-фолбэк удалён намеренно) ----
const argList = Array.isArray(A) ? A : A.competencies || []
const only = A.only || null                        // массив id — оставить только их
const exclude = A.exclude || ['DPF-AUTHORING', 'DPF-EBPF']  // уже готовы

let competencies = argList.filter((c) => c && c.id && !exclude.includes(c.id))
if (only && only.length) competencies = competencies.filter((c) => only.includes(c.id))

if (!competencies.length) {
  throw new Error(
    'FAIL-FAST: args.competencies пуст или не дошёл (проверь, что args передан объектом, а не забыт). ' +
    'Массовый bootstrap из competency-map.md удалён намеренно (2026-07-04: фолбэк запустил все 29 DPF вместо 5). ' +
    'Передай явный список: Workflow({name:"dpf-authoring-pipeline", args:{repoRoot, skillDir, competencies:[{id,name,kind,owner,bounded_context,status},...]}}). ' +
    'Формат — SKILL.md скилла dpf-authoring.'
  )
}
const missing = competencies.filter((c) => !c.name || !c.owner || !c.bounded_context)
if (missing.length) {
  throw new Error('FAIL-FAST: у компетенций не хватает полей (name/owner/bounded_context): ' + missing.map((c) => c.id).join(', '))
}
log(`DPF-authoring: ${competencies.length} компетенций: ${competencies.map((c) => c.id).join(', ')}`)

// ============ prompts ============
const STATUS = {
  type: 'object', additionalProperties: false,
  required: ['ok', 'file_written', 'gate_passed', 'notes'],
  properties: { ok: { type: 'boolean' }, file_written: { type: 'string' }, gate_passed: { type: 'boolean' }, notes: { type: 'string' } },
}
const dirOf = (c) => FW + '/' + c.id

// Роль фазы = ВСТРОЕННЫЙ пакет компетенции (формат framework-apply: DPF.md +
// assets/apply-prompt.md) в каталоге скилла — скилл самодостаточен, роли сильные
// (полные процедуры проверки, не однострочный "ты guardian"). Никаких agentType из
// .claude/agents проекта. Fail-fast: пакет не читается → фаза падает, а не работает
// «как получится».
const roleOf = (pkgId, declaredUse) => `
РОЛЬ — из встроенного пакета компетенции ${SKILL_DIR}/frameworks/${pkgId} (declaredUse: ${declaredUse}).
Прочитай ОБА файла и работай строго по ним:
1) ${SKILL_DIR}/frameworks/${pkgId}/assets/apply-prompt.md — процедура роли (исполняй буквально: чек-листы, порядок проверок, критерии отказа);
2) ${SKILL_DIR}/frameworks/${pkgId}/DPF.md — паттерны, контрпримеры, типовые ошибки роли (рабочий справочник, не фон).
Файлы недоступны → НЕ выполняй фазу: верни ok=false, gate_passed=false, notes='FAIL-FAST: пакет роли ${pkgId} не найден в скилле' и остановись.
`
const common = (c) => `
КОМПЕТЕНЦИЯ: ${c.id} — ${c.name} (${c.kind || 'Domain Principle Framework'}); owner: ${c.owner || 'architect'}.
Bounded context: ${c.bounded_context || '(см. competency-map.md)'}
Каталог DPF (абсолютные пути обязательны): ${dirOf(c)}
Метод (ОБЯЗАТЕЛЬНО прочитай): ${METHOD}
FPF — читать ЖИВЬЁМ, не выжимки, по приоритету источника:
  (1) если доступен FPF-справочник через MCP (fpf_reference: search_fpf / read_fpf_doc / query_fpf_spec) — читать через него (точные ID, цитаты, живая свежесть). Метод запинен на редакцию ${FPF_EDITION}; сверь её с фактической (get_fpf_index_status) — при расхождении ЯВНО отметь его в references (не работай молча по чужой редакции, E.4.DPF.DA edition-пин).
  (2) MCP недоступен → Grep по ${FPF_SPEC} (паттерн вида '^## E\\.4\\.DPF', НЕ по номеру строки), затем Read вокруг матча.
Контекст: ${ROOT}/project/domain.md ; ${ROOT}/project/decisions/ ; ${COMPMAP} ; эталон формата — ${EXEMPLAR}
ПРАВИЛО ПЕРЕДАЧИ (критично): ВСЕ артефакты пиши ТОЛЬКО в файлы (абсолютные пути). НЕ возвращай контент в ответе — следующая фаза читает твои ФАЙЛЫ. В ответ верни лишь короткий статус по schema.
ПУТИ С ~: раскрывай в абсолютные через $HOME (Bash: echo $HOME) перед Read/Grep — инструменты с относительными путями не работают.
Дата прогона: ${RUN_DATE || '(используй текущую)'}.
`
const sotaPrompt = (c) => `Фаза 1 — SoTA Harvest (FPF G.2), роль architect+dev. ${common(c)}
0) mkdir -p ${dirOf(c)}/references ${dirOf(c)}/assets
1) Phase-0 scope → ${dirOf(c)}/references/scope.md (bounded context, intended reader, first use, non-use boundary).
2) Глубокий web-ресёрч (WebSearch/WebFetch) → ${dirOf(c)}/references/sota-research.md по G.2: CorpusLedger (источники+триаж); ClaimSheets по ≥3 ТРАДИЦИЯМ (каждый claim: bounded context + evidence источник+URL+ДАТА [A.10] + freshness + trust-cue); ОБЯЗАТЕЛЬНЫЙ срез «ИИ в этой области» (tooling, кодоген, failure modes); MicroExamples (ОБЩИЕ, не наш код); Operator/Object inventory.
ГЕЙТ: ≥3 традиции; КАЖДЫЙ claim с источником+датой.`
const bridgePrompt = (c) => `Фаза 2 — Bridge / тезисы-антитезисы. ${roleOf('DPF-ADVERSARIAL-REVIEW', 'диалектика Bridge: тезисы/анти-тезисы/контрпримеры по свежему SoTA-ресёрчу')} ${common(c)}
Прочитай ${dirOf(c)}/references/sota-research.md. Сверь форму с FPF E.4.DPF:3, E.4.PFR, A.2.6, B.5.2.1, A.11 — поиск по спеке (MCP search_fpf/read_fpf_doc или Grep, см. правило FPF выше).
→ ${dirOf(c)}/references/theses-antitheses.md: BridgeMatrix (alignment/divergence + ЯВНЫЕ потери + scope строк, no silent fusion); на каждый тезис scope (A.2.6) + анти-тезис (NQD ≥3) + тип связи (E.4.PFR); КОНТРПРИМЕРЫ (A.11, отдельно от анти-паттернов); КАТАЛОГ ТИПОВЫХ ОШИБОК (симптом→почему→исправление, с источником), вкл. ИИ-специфичные.
ГЕЙТ: каждый тезис со scope; конфликты не слиты; есть контрпримеры и каталог ошибок.`
const sourcePackPrompt = (c) => `Фаза 3 — Source-pack (provenance). ${roleOf('DPF-KNOWLEDGE-CURATION', 'провенанс-реестр по G.2 для собранного ресёрча')} ${common(c)}
Прочитай все файлы в ${dirOf(c)}/references/. Образец: ${SKILL_DIR}/assets/template-source-pack.md.
→ ${dirOf(c)}/references/source-pack.md: по КАЖДОМУ источнику adopted/rejected+причина/claim-status/currentness; retired-premises отдельно; «открытые provenance-вопросы».
ГЕЙТ: каждый источник имеет решение adopted/rejected.`
const assemblePrompt = (c) => `Фазы 4–5 — Сборка DPF.md. ${roleOf('DPF-KNOWLEDGE-CURATION', 'сборка пользовательского носителя по канон-скелету метода')} ${common(c)}
Прочитай ${METHOD}, ${TEMPLATE}, эталон ${EXEMPLAR} и все ${dirOf(c)}/references/.
→ ${dirOf(c)}/DPF.md по канон-скелету: frontmatter (status:"stage-0", kind: Domain Principle Framework | Local Practice Framework); 0 Структурный отчёт носителя в шапке (CC-DPF.8: для кого файл, что на переднем плане, что сознательно огрублено/опущено, куда возврат за деталями); 1 Контекст; 2 Source pack; 3 Forces (scoped); 4 Паттерны (E.8 ≥4, КАЖДЫЙ: recognition→ПРИНЦИП SoTA→инстанциация→контрпример[A.11]→анти-паттерн[E.8]→conformance→связи[E.4.PFR]); 5 Связи паттернов; 6 Типовые ошибки (E.4.DPF:8; новичковые И ошибки опытных из устаревшей/локальной практики); 7 SoTA-Echoing (E.4.DPF:11); 8 Имена (F.18); 9 Relations; 10 Разнородные приёмочные случаи (2–3 НЕпохожих кейса, где паттерны обязаны сработать за пределами мотивирующего примера); 11 Quality&refresh; + Артефакты; Carrier note; Conformance CC-DPF.1–9.
ПРАВИЛО: общий принцип ПЕРЕД частностью; паттерны — главный язык носителя (тяжёлые карты после них или в references); НИКАКОГО процессного состояния в DPF.md (ход прогона, статусы ревью — только в references/); FPF живьём; assumption'ы не повышать до fact.
ГЕЙТ: скелет полон + ≥4 обогащённых паттерна + SoTA-Echoing + приёмочные случаи.`
const criticPrompt = (c) => `Фаза 6 — Quality + completeness-critic. ${roleOf('DPF-ADVERSARIAL-REVIEW', 'completeness-критика собранного DPF + оценка пакета по E.4.DPF.DA')} ${common(c)}
Прочитай ${dirOf(c)}/DPF.md и references. Сверь CC-DPF.1–9 (E.4.DPF:7) и анти-паттерны (E.4.DPF:8) — поиск по спеке (MCP read_fpf_doc E.4.DPF или Grep '^#* *E\\.4\\.DPF', см. правило FPF выше).
Затем оцени ПАКЕТ по E.4.DPF.DA (MCP read_fpf_doc E.4.DPF.DA или Grep '^#* *E\\.4\\.DPF\\.DA'): сперва подпроход формы PFM1–PFM11, затем таблица всех 11 координат D1–D11 — каждая строка: значение 0–5 | краткое обоснование | evidence-locus (конкретная секция/файл) | repair-предложение. Пол = 4 (опора ролей). Средним баллом паттернов подменять НЕЛЬЗЯ (CC-DPFDA.4).
→ ${dirOf(c)}/references/critic-review.md: упущенное (традиция/тензия/claim без источника/голая частность/нет контрпримера); PFM-подпроход; таблица D1–D11; вердикт CC-DPF.1–9 (pass/fail); статус пакета: admissibleForDeclaredDPFUse | seedOnly | repairBeforeDPFUse | refreshNeeded; список наименьших правок.
Если статус admissible — допиши в конец ${dirOf(c)}/DPF.md одну строку: «> conformance: CC-DPF.1–9 verified; E.4.DPF.DA: admissibleForDeclaredDPFUse (critic, guardian, дата)».
ГЕЙТ: gate_passed=true ТОЛЬКО если CC-DPF.1–9 PASS и статус admissibleForDeclaredDPFUse.`

// ============ run: pipelined, handoff только через файлы ============
// model по сложности фазы (DEC-003): Sonnet — дефолт; Bridge+Critic — Opus (диалектика/adversarial,
// где Opus покупает качество); механика — Haiku. agentType (роль, КТО) ≠ model (тир, НАСКОЛЬКО ТРУДНО);
// модель задаётся ЯВНО, не наследуется от role-default (gate 5).
const results = await pipeline(
  competencies,
  (c) => agent(sotaPrompt(c), { label: `sota:${c.id}`, phase: 'SoTA Harvest', agentType: 'general-purpose', model: 'sonnet', schema: STATUS }),
  (_, c) => agent(bridgePrompt(c), { label: `bridge:${c.id}`, phase: 'Bridge', agentType: 'general-purpose', model: 'opus', schema: STATUS }),
  (_, c) => agent(sourcePackPrompt(c), { label: `spack:${c.id}`, phase: 'Source-pack', agentType: 'general-purpose', model: 'sonnet', schema: STATUS }),
  (_, c) => agent(assemblePrompt(c), { label: `assemble:${c.id}`, phase: 'Assemble', agentType: 'general-purpose', model: 'sonnet', schema: STATUS }),
  (_, c) => agent(criticPrompt(c), { label: `critic:${c.id}`, phase: 'Critic', agentType: 'general-purpose', model: 'opus', schema: STATUS }),
)

const report = competencies.map((c, i) => ({ id: c.id, dir: dirOf(c), critic: results[i] }))
log('DPF-authoring завершён. Результат каждой компетенции — в её каталоге (DPF.md + references/).')
return report
