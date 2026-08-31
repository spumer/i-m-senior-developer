export const meta = {
  name: 'plan-do-workflow',
  description: 'Явный экспериментальный цикл реализации с гейтами свежести, файловыми отчётами и последовательным ревью',
  whenToUse: 'Когда команда plan-do-workflow передала нормализованный текущий план, точные роли и абсолютные пути. Обычный plan-do этот workflow не вызывает.',
  phases: [
    { title: 'Гейт', detail: 'проверка свежести непосредственно перед каждым рабочим вызовом' },
    { title: 'Реализация', detail: 'реализация очередной фазы по зарезервированному пути отчёта' },
    { title: 'Ревью', detail: 'независимое ревью завершённой реализации' },
    { title: 'Правки', detail: 'не более двух кругов подтверждённых правок' },
    { title: 'Документация', detail: 'разрешённая документационная работа после чистого ревью всех фаз' },
  ],
}

const COMMAND_RECEIPT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['exit_code', 'raw_stdout', 'raw_stderr'],
  properties: {
    exit_code: { type: 'integer' },
    raw_stdout: { type: 'string' },
    raw_stderr: { type: 'string' },
  },
}

const INPUT_PATHS = [
  { name: 'feature_directory', kind: 'directory' },
  { name: 'execution_path', kind: 'file' },
  { name: 'architecture_path', kind: 'file' },
  { name: 'planner_context_path', kind: 'file' },
  { name: 'helper_path', kind: 'file' },
]
const INPUT_PROBE_LABEL = 'проверка пригодности входа'
const INPUT_PROBE_SCRIPT = [
  'import json',
  'import os',
  'import sys',
  `names = ${JSON.stringify(INPUT_PATHS.map(({ name }) => name))}`,
  'def inspect(path):',
  '    if not os.path.exists(path):',
  "        return {'kind': 'missing', 'readable': False}",
  '    if os.path.isdir(path):',
  "        kind = 'directory'",
  '    elif os.path.isfile(path):',
  "        kind = 'file'",
  '    else:',
  "        kind = 'other'",
  "    return {'kind': kind, 'readable': os.access(path, os.R_OK)}",
  'print(json.dumps(dict(zip(names, map(inspect, sys.argv[1:]))), sort_keys=True))',
].join('\n')

function isNonemptyString(value) {
  return typeof value === 'string' && value.trim().length > 0
}

function isAbsolutePath(value) {
  return isNonemptyString(value) && value.startsWith('/')
}

function hasUnsubstitutedVariable(value) {
  return typeof value === 'string' && /\$\{[^}]*\}/.test(value)
}

function shellQuote(value) {
  return `'${value.replaceAll("'", "'\"'\"'")}'`
}

function inputProbeCommand(input) {
  const paths = INPUT_PATHS.map(({ name }) => shellQuote(input[name])).join(' ')
  return `python3 -c ${shellQuote(INPUT_PROBE_SCRIPT)} ${paths}`
}

function errorMessage(error) {
  if (error instanceof Error && isNonemptyString(error.message)) return error.message
  return String(error)
}

function renderPlanValue(value) {
  return typeof value === 'string' ? value : JSON.stringify(value, null, 2)
}

function createRunResult(rawArgs) {
  return {
    mode: 'workflow-experiment',
    feature_directory: rawArgs && rawArgs.feature_directory ? rawArgs.feature_directory : null,
    execution_path: rawArgs && rawArgs.execution_path ? rawArgs.execution_path : null,
    state: 'initializing',
    reason: null,
    requires_human: false,
    last_completed_phase: null,
    planned_phases: [],
    completed_phases: [],
    remaining_due_to_stop: [],
    unexpectedly_omitted: [],
    order_violations: [],
    phase_trace: [],
    freshness_checks: 0,
    working_calls: 0,
    max_working_calls_between_freshness_checks: 0,
    review_rounds: { total: 0, by_phase: {} },
    fix_rounds: { total: 0, by_phase: {} },
    human_interventions: 0,
    reports: { implementation: [], review: [], documentation: [] },
    reservations: [],
    summary_deviations: [],
    commands: [],
    certification_boundaries: [],
  }
}

function requireRole(role, name, problems) {
  if (!role || typeof role !== 'object' || Array.isArray(role)) {
    problems.push(`${name} must be an object`)
    return false
  }
  if (!isNonemptyString(role.agent_type)) problems.push(`${name}.agent_type must be a nonempty string`)
  if (!isNonemptyString(role.model)) problems.push(`${name}.model must be a nonempty string`)
  if (!Array.isArray(role.skills)) problems.push(`${name}.skills must be an array`)
  return true
}

function normalizeArguments(rawArgs, result) {
  const problems = []
  if (!rawArgs || typeof rawArgs !== 'object' || Array.isArray(rawArgs)) {
    return { problems: ['args must be an object'] }
  }

  for (const { name } of INPUT_PATHS) {
    if (hasUnsubstitutedVariable(rawArgs[name])) {
      problems.push(`${name}: contains an unsubstituted variable`)
    } else if (!isAbsolutePath(rawArgs[name])) {
      problems.push(`${name} must be an absolute path`)
    }
  }
  if (rawArgs.execution_path === rawArgs.architecture_path) {
    problems.push('execution_path and architecture_path must be different')
  }
  if (!Array.isArray(rawArgs.phases) || rawArgs.phases.length === 0) {
    problems.push('phases must be a nonempty array')
  }
  if (rawArgs.max_fix_rounds !== 2) problems.push('max_fix_rounds must equal 2')
  requireRole(rawArgs.reviewer, 'reviewer', problems)

  const phaseKeys = new Set()
  if (Array.isArray(rawArgs.phases)) {
    rawArgs.phases.forEach((phaseDefinition, index) => {
      const prefix = `phases[${index}]`
      if (!phaseDefinition || typeof phaseDefinition !== 'object' || Array.isArray(phaseDefinition)) {
        problems.push(`${prefix} must be an object`)
        return
      }
      if (!isNonemptyString(phaseDefinition.key)) problems.push(`${prefix}.key must be a nonempty string`)
      if (!isNonemptyString(phaseDefinition.title)) problems.push(`${prefix}.title must be a nonempty string`)
      if (phaseKeys.has(phaseDefinition.key)) problems.push(`${prefix}.key must be unique`)
      phaseKeys.add(phaseDefinition.key)
      if (!Object.hasOwn(phaseDefinition, 'inputs')) problems.push(`${prefix}.inputs is required`)
      if (!Object.hasOwn(phaseDefinition, 'outputs')) problems.push(`${prefix}.outputs is required`)
      if (!Object.hasOwn(phaseDefinition, 'review_scope')) problems.push(`${prefix}.review_scope is required`)
      requireRole(phaseDefinition.implementer, `${prefix}.implementer`, problems)
    })
  }

  if (rawArgs.documentation !== 'not_required') {
    requireRole(rawArgs.documentation, 'documentation', problems)
    if (!rawArgs.documentation || !Array.isArray(rawArgs.documentation.allowed_paths)) {
      problems.push('documentation.allowed_paths must be an array')
    }
  }

  if (problems.length > 0) return { problems }

  result.feature_directory = rawArgs.feature_directory
  result.execution_path = rawArgs.execution_path
  result.planned_phases = rawArgs.phases.map((phaseDefinition) => phaseDefinition.title)
  return { value: rawArgs }
}

function finishRun(context, state, reason, requiresHuman) {
  const result = context.result
  result.state = state
  result.reason = reason
  result.requires_human = requiresHuman
  if (requiresHuman) result.human_interventions = 1
  result.remaining_due_to_stop = result.planned_phases.filter(
    (title) => !result.completed_phases.includes(title),
  )
  return result
}

function stopRun(context, reason) {
  return finishRun(context, 'stopped', reason, true)
}

function failRun(context, reason) {
  return finishRun(context, 'failed', reason, true)
}

function appendTrace(result, phaseKey, event, round) {
  const trace = { phase: phaseKey, event }
  if (Number.isInteger(round)) trace.round = round
  result.phase_trace.push(trace)
}

function recordSummaryDeviation(result, phaseKey, detail) {
  result.summary_deviations.push({ phase: phaseKey, detail })
}

function recordReport(result, kind, path) {
  if (!result.reports[kind].includes(path)) result.reports[kind].push(path)
}

function recordCommands(result, phaseKey, commands) {
  if (commands.length > 0) result.commands.push({ phase: phaseKey, commands })
}

function updateReservation(result, path, status, size) {
  const reservation = result.reservations.find((item) => item.path === path)
  if (reservation) {
    reservation.status = status
    reservation.size = size
  }
}

function normalizeSummaryText(value) {
  return typeof value === 'string' ? value.replaceAll('\r\n', '\n').replaceAll('\r', '\n') : null
}

function parseProtocolSections(value, headings) {
  const text = normalizeSummaryText(value)
  if (text === null) return { ok: false, reason: 'summary must be plain text' }

  const entries = []
  for (const heading of headings) {
    const expression = new RegExp(`^${heading}:\\s*(.*)$`, 'gm')
    const matches = [...text.matchAll(expression)]
    if (matches.length === 0) return { ok: false, reason: `missing ${heading}` }
    if (matches.length > 1) return { ok: false, reason: `duplicate ${heading}` }
    entries.push({
      heading,
      index: matches[0].index,
      // Совпадение съедает строку заголовка целиком, поэтому значение в той же
      // строке живёт только в группе; срез до следующего заголовка добавляет
      // продолжение многострочного поля.
      inline: matches[0][1],
      valueStart: matches[0].index + matches[0][0].length,
    })
  }

  const ordered = [...entries].sort((left, right) => left.index - right.index)
  const sections = {}
  const deviations = []
  const expectedOrder = headings.join('|')
  const actualOrder = ordered.map((entry) => entry.heading).join('|')
  if (actualOrder !== expectedOrder) deviations.push('protocol headers are out of order')
  if (text.slice(0, ordered[0].index).trim()) deviations.push('summary contains text before protocol headers')

  for (let index = 0; index < ordered.length; index += 1) {
    const current = ordered[index]
    const next = ordered[index + 1]
    const continuation = text.slice(current.valueStart, next ? next.index : text.length)
    sections[current.heading] = `${current.inline}${continuation}`.trim()
  }

  const allowed = new Set(headings)
  const extraHeadings = [...text.matchAll(/^([A-Za-z][A-Za-z -]*):/gm)]
    .map((match) => match[1])
    .filter((heading) => !allowed.has(heading))
  if (extraHeadings.length > 0) deviations.push(`additional headers: ${extraHeadings.join(', ')}`)
  return { ok: true, sections, deviations }
}

function parseCommands(value) {
  const lines = value.split('\n').map((line) => line.trim()).filter(Boolean)
  if (lines.length === 0) return { ok: false, reason: 'Commands must contain at least one command' }
  if (lines.some((line) => !line.startsWith('- ') || !line.includes(' — '))) {
    return { ok: false, reason: 'Commands must contain observed command outcomes' }
  }
  return { ok: true, commands: lines.map((line) => line.slice(2)) }
}

function parseImplementationSummary(value, expectedPath, statuses) {
  const parsed = parseProtocolSections(value, ['Status', 'Report', 'Commands', 'Summary', 'Blocked checks'])
  if (!parsed.ok) return parsed
  const sections = parsed.sections
  if (!statuses.includes(sections.Status)) return { ok: false, reason: `invalid Status: ${sections.Status}` }
  if (sections.Report !== expectedPath) return { ok: false, reason: 'Report does not match the reserved path' }
  const commands = parseCommands(sections.Commands)
  if (!commands.ok) return commands
  if (!sections.Summary) return { ok: false, reason: 'Summary must be nonempty' }
  if (!sections['Blocked checks']) return { ok: false, reason: 'Blocked checks must be present' }
  if (sections.Summary.length > 1200) parsed.deviations.push('Summary exceeds 1200 characters')
  return {
    ok: true,
    status: sections.Status,
    commands: commands.commands,
    summary: sections.Summary,
    blockedChecks: sections['Blocked checks'],
    deviations: parsed.deviations,
  }
}

function parseReviewSummary(value, expectedPath) {
  const parsed = parseProtocolSections(value, ['Status', 'Report', 'Findings', 'Blocking', 'Certification boundary', 'Summary'])
  if (!parsed.ok) return parsed
  const sections = parsed.sections
  if (!['clean', 'changes-requested'].includes(sections.Status)) {
    return { ok: false, reason: `invalid Status: ${sections.Status}` }
  }
  if (sections.Report !== expectedPath) return { ok: false, reason: 'Report does not match the reserved path' }
  const findings = sections.Findings.match(/^major (\d+); minor (\d+); security (\d+); design (\d+)$/)
  if (!findings) return { ok: false, reason: 'Findings must contain four nonnegative counters' }
  if (!/^\d+$/.test(sections.Blocking)) return { ok: false, reason: 'Blocking must be a nonnegative integer' }
  if (!sections['Certification boundary']) return { ok: false, reason: 'Certification boundary must be nonempty' }
  if (!sections.Summary) return { ok: false, reason: 'Summary must be nonempty' }
  if (sections.Summary.length > 1200) parsed.deviations.push('Summary exceeds 1200 characters')
  return {
    ok: true,
    status: sections.Status,
    findings: {
      major: Number(findings[1]),
      minor: Number(findings[2]),
      security: Number(findings[3]),
      design: Number(findings[4]),
    },
    blocking: Number(sections.Blocking),
    certificationBoundary: sections['Certification boundary'],
    summary: sections.Summary,
    deviations: parsed.deviations,
  }
}

function isTargetOccupied(value, path) {
  return typeof value === 'string' && value.trim() === `Целевой путь занят: ${path}`
}

function parseJsonStdout(receipt, stage) {
  try {
    const payload = JSON.parse(receipt.raw_stdout)
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
      throw new Error('JSON value must be an object')
    }
    return payload
  } catch (error) {
    throw new Error(`${stage}: helper stdout is not an object JSON value: ${errorMessage(error)}`)
  }
}

function requireReceipt(receipt, stage) {
  if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt)) {
    throw new Error(`${stage}: command relay returned no receipt`)
  }
  if (!Number.isInteger(receipt.exit_code) || typeof receipt.raw_stdout !== 'string' || typeof receipt.raw_stderr !== 'string') {
    throw new Error(`${stage}: command relay returned an invalid receipt`)
  }
  return receipt
}

async function relayCommand(command, label) {
  const receipt = await agent(
    `Выполни ровно одну команду и ничего больше:\n\n${command}\n\n` +
      'Верни exit_code, raw_stdout и raw_stderr. raw_stdout и raw_stderr передай дословно, без пересказа, исправлений или повторного запуска команды.',
    { label, phase: 'Гейт', schema: COMMAND_RECEIPT_SCHEMA, effort: 'low' },
  )
  return requireReceipt(receipt, label)
}

async function checkInputSuitability(context) {
  const { input } = context
  const receipt = await relayCommand(inputProbeCommand(input), INPUT_PROBE_LABEL)
  if (receipt.exit_code !== 0) {
    failRun(context, `input suitability check failed: ${receipt.raw_stderr || receipt.raw_stdout}`)
    return false
  }

  let payload
  try {
    payload = parseJsonStdout(receipt, 'input suitability check')
  } catch (error) {
    failRun(context, errorMessage(error))
    return false
  }

  for (const { name, kind: expectedKind } of INPUT_PATHS) {
    const node = payload[name]
    if (!node || typeof node !== 'object' || Array.isArray(node) || typeof node.kind !== 'string' || typeof node.readable !== 'boolean') {
      failRun(context, `input ${name}: invalid suitability probe result`)
      return false
    }
    if (node.kind === 'missing') {
      failRun(context, `input ${name}: path does not exist`)
      return false
    }
    if (!node.readable) {
      failRun(context, `input ${name}: path is not readable`)
      return false
    }
    if (node.kind !== expectedKind) {
      failRun(context, `input ${name}: expected ${expectedKind}, got ${node.kind}`)
      return false
    }
  }
  return true
}

async function checkFreshness(context, before) {
  const { input, result } = context
  const command = `python3 ${shellQuote(input.helper_path)} check ${shellQuote(input.execution_path)}`
  const receipt = await relayCommand(command, `гейт:${before}`)
  result.freshness_checks += 1
  context.callsSinceFreshness = 0

  if (receipt.exit_code === 0) {
    const payload = parseJsonStdout(receipt, `гейт ${before}`)
    if (payload.status !== 'current' || !isNonemptyString(payload.recorded_version === undefined ? '' : String(payload.recorded_version)) || !isNonemptyString(payload.current_version === undefined ? '' : String(payload.current_version))) {
      failRun(context, `гейт ${before}: invalid current-plan payload`)
      return false
    }
    return true
  }

  if (receipt.exit_code === 2) {
    const payload = parseJsonStdout(receipt, `гейт ${before}`)
    const reason = isNonemptyString(payload.reason) ? payload.reason : 'plan is stale'
    stopRun(context, `stale-plan: ${reason}. Rebuild with /planner:plan ${input.architecture_path}`)
    return false
  }
  if (receipt.exit_code === 3) {
    stopRun(context, `invalid-plan before ${before}: ${receipt.raw_stderr || receipt.raw_stdout}`)
    return false
  }
  if (receipt.exit_code === 64) {
    failRun(context, `helper usage failure before ${before}: ${receipt.raw_stderr || receipt.raw_stdout}`)
    return false
  }
  failRun(context, `unexpected helper exit code before ${before}: ${receipt.exit_code}; ${receipt.raw_stderr || receipt.raw_stdout}`)
  return false
}

async function reserveReport(context, kind, phaseKey) {
  const { input, result } = context
  const directory = kind === 'review'
    ? `${input.feature_directory}/review-request-changes`
    : input.feature_directory
  const command = `python3 ${shellQuote(input.helper_path)} reserve-report --directory ${shellQuote(directory)} --kind ${shellQuote(kind)}`
  const receipt = await relayCommand(command, `резерв:${phaseKey}:${kind}`)

  if (receipt.exit_code === 0) {
    const payload = parseJsonStdout(receipt, `резерв ${phaseKey}`)
    if (payload.kind !== kind || !isAbsolutePath(payload.path) || !Number.isInteger(payload.number) || payload.number < 1 || !Array.isArray(payload.empties)) {
      failRun(context, `резерв ${phaseKey}: invalid reserve-report payload`)
      return null
    }
    const reservation = {
      kind,
      number: payload.number,
      path: payload.path,
      status: 'empty',
      size: 0,
      empties: payload.empties,
    }
    result.reservations.push(reservation)
    return reservation
  }
  if (receipt.exit_code === 3) {
    stopRun(context, `cannot reserve ${kind} report for ${phaseKey}: ${receipt.raw_stderr || receipt.raw_stdout}`)
    return null
  }
  if (receipt.exit_code === 64) {
    failRun(context, `helper usage failure while reserving ${kind} report for ${phaseKey}: ${receipt.raw_stderr || receipt.raw_stdout}`)
    return null
  }
  failRun(context, `unexpected reserve-report exit code for ${phaseKey}: ${receipt.exit_code}; ${receipt.raw_stderr || receipt.raw_stdout}`)
  return null
}

async function inspectReport(context, reservation, phaseKey) {
  const { input } = context
  const command = `python3 ${shellQuote(input.helper_path)} inspect-report ${shellQuote(reservation.path)}`
  const receipt = await relayCommand(command, `осмотр:${phaseKey}`)
  if (receipt.exit_code !== 0) {
    failRun(context, `cannot inspect report for ${phaseKey}: ${receipt.raw_stderr || receipt.raw_stdout}`)
    return null
  }
  const payload = parseJsonStdout(receipt, `осмотр ${phaseKey}`)
  if (
    payload.path !== reservation.path ||
    !['missing', 'empty', 'nonempty'].includes(payload.status) ||
    !Object.hasOwn(payload, 'size') ||
    (payload.status === 'missing' ? payload.size !== null : !Number.isInteger(payload.size) || payload.size < 0)
  ) {
    failRun(context, `осмотр ${phaseKey}: invalid inspect-report payload`)
    return null
  }
  updateReservation(context.result, reservation.path, payload.status, payload.size)
  return payload
}

async function callWorkingRole(context, role, prompt, label, phaseName) {
  context.callsSinceFreshness += 1
  context.result.working_calls += 1
  context.result.max_working_calls_between_freshness_checks = Math.max(
    context.result.max_working_calls_between_freshness_checks,
    context.callsSinceFreshness,
  )
  if (context.callsSinceFreshness > 1) {
    throw new Error(`freshness invariant violated before ${label}`)
  }

  try {
    const response = await agent(prompt, {
      label,
      phase: phaseName,
      agentType: role.agent_type,
      model: role.model,
    })
    return { response, error: null }
  } catch (error) {
    return { response: null, error: errorMessage(error) }
  }
}

function roleGuard(featureDirectory) {
  return (
    `Рабочий каталог: ${featureDirectory}\n\n` +
    'Идентификатор фичи допустим только в имени артефакта внутри переданного каталога фичи. Не помещай его в код, комментарии, docstring, имена тестов, идентификаторы и документацию проекта вне этого каталога. Не выполняй commit, push или tag.\n\n'
  )
}

function implementationPrompt(input, phaseDefinition, reportPath, correction) {
  const correctionText = correction
    ? correction.summaryOnly
      ? `Полный корректный отчёт уже записан по пути ${reportPath}. Не записывай, не заменяй, не удаляй и не переименовывай этот файл. Верни только корректную компактную сводку; в предыдущем ответе нарушено: ${correction.reason}.\n\n`
      : `Предыдущий ответ не позволил принять работу: ${correction.reason}. Этот вызов обязан записать полный отчёт по пути ${reportPath}; если по нему есть пустая бронь, она зарезервирована для тебя.\n\n`
    : `Запиши полный implementation report по пути ${reportPath}.\n\n`
  const mode = correction && correction.isFix ? 'Это круг правок после ревью.' : 'Это первичная реализация фазы.'
  return (
    roleGuard(input.feature_directory) +
    `${mode}\n${correctionText}` +
    `Фаза: ${phaseDefinition.title}\n` +
    `Входы фазы:\n${renderPlanValue(phaseDefinition.inputs)}\n\n` +
    `Ожидаемые выходы фазы:\n${renderPlanValue(phaseDefinition.outputs)}\n\n` +
    'Верни в чат только эту сводку, не дублируя полный отчёт:\n\n' +
    `Status: complete | blocked\nReport: ${reportPath}\nCommands:\n- <точная команда> — <наблюдённый итог>\nSummary: <проза не длиннее 1200 символов>\nBlocked checks: <список | none>`
  )
}

function reviewPrompt(input, phaseDefinition, implementationReportPath, reportPath, correction) {
  const correctionText = correction
    ? correction.summaryOnly
      ? `Полный корректный review report уже записан по пути ${reportPath}. Не изменяй этот файл. Верни только корректную компактную сводку; в предыдущем ответе нарушено: ${correction.reason}.\n\n`
      : `Предыдущий ответ не позволил принять ревью: ${correction.reason}. Этот вызов обязан записать полный отчёт по пути ${reportPath}.\n\n`
    : `Прочитай implementation report по пути ${implementationReportPath} и запиши полный review report по пути ${reportPath}.\n\n`
  return (
    roleGuard(input.feature_directory) +
    correctionText +
    `Фаза: ${phaseDefinition.title}\nОбласть ревью:\n${renderPlanValue(phaseDefinition.review_scope)}\n\n` +
    'Не изменяй исходники, архитектуру, план, индекс или ветку. При design concern дословно помести concern в Summary.\n\n' +
    'Верни в чат только эту сводку, не дублируя полный отчёт:\n\n' +
    `Status: clean | changes-requested\nReport: ${reportPath}\nFindings: major N; minor N; security N; design N\nBlocking: N\nCertification boundary: <что статическое ревью не удостоверяет>\nSummary: <проза не длиннее 1200 символов>`
  )
}

function documentationPrompt(input, documentation, reportPath, correction) {
  const correctionText = correction
    ? correction.summaryOnly
      ? `Полный корректный documentation report уже записан по пути ${reportPath}. Не изменяй этот файл. Верни только корректную компактную сводку; в предыдущем ответе нарушено: ${correction.reason}.\n\n`
      : `Предыдущий ответ не позволил принять документационную работу: ${correction.reason}. Этот вызов обязан записать полный отчёт по пути ${reportPath}.\n\n`
    : `Запиши полный documentation report по пути ${reportPath}.\n\n`
  return (
    roleGuard(input.feature_directory) +
    correctionText +
    `Разрешённые пути документации:\n${renderPlanValue(documentation.allowed_paths)}\n\n` +
    `Не изменяй файлы вне разрешённого списка, кроме полного documentation report по пути ${reportPath}.\n\n` +
    'Верни в чат только эту сводку, не дублируя полный отчёт:\n\n' +
    `Status: complete | blocked | not-needed\nReport: ${reportPath}\nCommands:\n- <точная команда проверки> — <наблюдённый итог>\nSummary: <проза не длиннее 1200 символов>\nBlocked checks: <список | none>`
  )
}

function acceptSummary(context, kind, phaseKey, reservation, summary) {
  recordReport(context.result, kind, reservation.path)
  for (const deviation of summary.deviations) {
    recordSummaryDeviation(context.result, phaseKey, deviation)
  }
  if (summary.commands) recordCommands(context.result, phaseKey, summary.commands)
  if (summary.certificationBoundary) {
    context.result.certification_boundaries.push({ phase: phaseKey, boundary: summary.certificationBoundary })
  }
}

async function invokeRole(context, options) {
  let collisions = 0

  while (collisions < 3) {
    // Разрешение на корректирующий вызов принадлежит пути, а не роли: занятый
    // путь отменяет попытку целиком, и новый путь получает своё разрешение.
    let correctionUsed = false
    const reservation = await reserveReport(context, options.kind, options.phaseKey)
    if (!reservation) return { accepted: false }

    phase(options.phaseName)
    if (!(await checkFreshness(context, `${options.phaseKey}:${options.kind}`))) return { accepted: false }

    const initial = await callWorkingRole(
      context,
      options.role,
      options.makePrompt(reservation.path, null),
      `${options.phaseKey}:${options.kind}:${collisions + 1}`,
      options.phaseName,
    )
    const initialInspection = await inspectReport(context, reservation, options.phaseKey)
    if (!initialInspection) return { accepted: false }

    if (isTargetOccupied(initial.response, reservation.path)) {
      collisions += 1
      recordSummaryDeviation(context.result, options.phaseKey, `target path occupied: ${reservation.path}`)
      if (collisions === 3) {
        stopRun(context, `target-path-collision-limit: ${reservation.path}`)
        return { accepted: false }
      }
      continue
    }

    const initialSummary = options.parseSummary(initial.response, reservation.path)
    const initialReason = initial.error || (initialSummary.ok ? null : initialSummary.reason) || `report is ${initialInspection.status}`
    if (initialInspection.status === 'nonempty' && initialSummary.ok) {
      acceptSummary(context, options.kind, options.phaseKey, reservation, initialSummary)
      return { accepted: true, summary: initialSummary, reservation }
    }

    recordSummaryDeviation(context.result, options.phaseKey, initialReason)
    if (correctionUsed) {
      stopRun(context, `second summary protocol failure in ${options.phaseKey}: ${initialReason}`)
      return { accepted: false }
    }
    correctionUsed = true

    if (!(await checkFreshness(context, `${options.phaseKey}:${options.kind}:correction`))) return { accepted: false }
    const correction = {
      summaryOnly: initialInspection.status === 'nonempty',
      reason: initialReason,
      isFix: options.isFix,
    }
    const corrected = await callWorkingRole(
      context,
      options.role,
      options.makePrompt(reservation.path, correction),
      `${options.phaseKey}:${options.kind}:correction`,
      options.phaseName,
    )
    const correctedInspection = await inspectReport(context, reservation, options.phaseKey)
    if (!correctedInspection) return { accepted: false }

    if (isTargetOccupied(corrected.response, reservation.path)) {
      collisions += 1
      recordSummaryDeviation(context.result, options.phaseKey, `target path occupied: ${reservation.path}`)
      if (collisions === 3) {
        stopRun(context, `target-path-collision-limit: ${reservation.path}`)
        return { accepted: false }
      }
      continue
    }

    const correctedSummary = options.parseSummary(corrected.response, reservation.path)
    const correctedReason = corrected.error || (correctedSummary.ok ? null : correctedSummary.reason) || `report is ${correctedInspection.status}`
    if (correctedInspection.status === 'nonempty' && correctedSummary.ok) {
      acceptSummary(context, options.kind, options.phaseKey, reservation, correctedSummary)
      return { accepted: true, summary: correctedSummary, reservation }
    }

    recordSummaryDeviation(context.result, options.phaseKey, correctedReason)
    stopRun(context, `second summary protocol failure in ${options.phaseKey}: ${correctedReason}`)
    return { accepted: false }
  }

  stopRun(context, `target-path-collision-limit in ${options.phaseKey}`)
  return { accepted: false }
}

function incrementCounter(counter, phaseKey) {
  counter.total += 1
  counter.by_phase[phaseKey] = (counter.by_phase[phaseKey] || 0) + 1
}

async function runImplementationPhase(context, phaseDefinition) {
  const { input, result } = context
  const phaseKey = phaseDefinition.key
  appendTrace(result, phaseKey, 'pending')
  appendTrace(result, phaseKey, 'implementing')

  let implementation = await invokeRole(context, {
    kind: 'implementation',
    role: phaseDefinition.implementer,
    phaseKey,
    phaseName: 'Реализация',
    parseSummary: (value, path) => parseImplementationSummary(value, path, ['complete', 'blocked']),
    makePrompt: (path, correction) => implementationPrompt(input, phaseDefinition, path, correction),
    isFix: false,
  })
  if (!implementation.accepted) return false
  if (implementation.summary.status === 'blocked') {
    stopRun(context, `implementation blocked in ${phaseDefinition.title}: ${implementation.summary.summary}; blocked checks: ${implementation.summary.blockedChecks}`)
    return false
  }

  let fixRound = 0
  while (true) {
    appendTrace(result, phaseKey, 'reviewing', fixRound)
    const review = await invokeRole(context, {
      kind: 'review',
      role: input.reviewer,
      phaseKey,
      phaseName: 'Ревью',
      parseSummary: parseReviewSummary,
      makePrompt: (path, correction) => reviewPrompt(input, phaseDefinition, implementation.reservation.path, path, correction),
      isFix: false,
    })
    if (!review.accepted) return false
    incrementCounter(result.review_rounds, phaseKey)

    if (review.summary.findings.design > 0) {
      stopRun(context, `design finding in ${phaseDefinition.title}: ${review.summary.summary}`)
      return false
    }
    if (review.summary.status === 'clean' && review.summary.blocking === 0) {
      appendTrace(result, phaseKey, 'clean', fixRound)
      result.completed_phases.push(phaseDefinition.title)
      result.last_completed_phase = phaseDefinition.title
      return true
    }
    if (fixRound >= input.max_fix_rounds) {
      stopRun(context, `review-round-limit in ${phaseDefinition.title}`)
      return false
    }

    fixRound += 1
    incrementCounter(result.fix_rounds, phaseKey)
    appendTrace(result, phaseKey, 'fixing', fixRound)
    implementation = await invokeRole(context, {
      kind: 'implementation',
      role: phaseDefinition.implementer,
      phaseKey,
      phaseName: 'Правки',
      parseSummary: (value, path) => parseImplementationSummary(value, path, ['complete', 'blocked']),
      makePrompt: (path, correction) => implementationPrompt(
        input,
        phaseDefinition,
        path,
        correction ? { ...correction, isFix: true } : null,
      ),
      isFix: true,
    })
    if (!implementation.accepted) return false
    if (implementation.summary.status === 'blocked') {
      stopRun(context, `fixes blocked in ${phaseDefinition.title}: ${implementation.summary.summary}; blocked checks: ${implementation.summary.blockedChecks}`)
      return false
    }
  }
}

function completeRun(context) {
  const { result } = context
  const expected = result.planned_phases
  const completed = result.completed_phases
  result.unexpectedly_omitted = expected.filter((title) => !completed.includes(title))
  const actualOrder = completed.join(' | ')
  const expectedOrder = expected.join(' | ')
  if (actualOrder !== expectedOrder) {
    result.order_violations.push(`expected ${expectedOrder}; completed ${actualOrder}`)
  }
  if (result.unexpectedly_omitted.length > 0 || result.order_violations.length > 0) {
    return failRun(context, 'completion guard rejected an incomplete or reordered phase list')
  }
  return finishRun(context, 'completed', 'all planned implementation phases completed with clean review', false)
}

async function runWorkflow(rawArgs) {
  const result = createRunResult(rawArgs)
  const context = { result, input: null, callsSinceFreshness: 0 }
  try {
    const normalized = normalizeArguments(rawArgs, result)
    if (!normalized.value) return failRun(context, `invalid workflow args: ${normalized.problems.join('; ')}`)
    context.input = normalized.value

    phase('Гейт')
    if (!(await checkInputSuitability(context))) return result
    if (!(await checkFreshness(context, 'initialization'))) return result
    result.state = 'running'

    for (const phaseDefinition of context.input.phases) {
      if (!(await runImplementationPhase(context, phaseDefinition))) return result
    }

    if (context.input.documentation === 'not_required') {
      appendTrace(result, 'documentation', 'not-required')
      return completeRun(context)
    }

    appendTrace(result, 'documentation', 'documenting')
    const documentation = await invokeRole(context, {
      kind: 'documentation',
      role: context.input.documentation,
      phaseKey: 'documentation',
      phaseName: 'Документация',
      parseSummary: (value, path) => parseImplementationSummary(value, path, ['complete', 'blocked', 'not-needed']),
      makePrompt: (path, correction) => documentationPrompt(context.input, context.input.documentation, path, correction),
      isFix: false,
    })
    if (!documentation.accepted) return result
    if (documentation.summary.status === 'blocked') {
      stopRun(context, `documentation blocked: ${documentation.summary.summary}; blocked checks: ${documentation.summary.blockedChecks}`)
      return result
    }
    appendTrace(result, 'documentation', documentation.summary.status)
    return completeRun(context)
  } catch (error) {
    return failRun(context, `workflow failure: ${errorMessage(error)}`)
  }
}

return await runWorkflow(args)
