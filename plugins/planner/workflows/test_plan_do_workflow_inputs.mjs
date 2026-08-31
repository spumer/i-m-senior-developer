#!/usr/bin/env node

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const WORKFLOW_RELATIVE_PATH = 'plugins/planner/workflows/plan-do-workflow.js'
const NEIGHBOUR_WORKFLOW_PATH = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  'plan-do-workflow.js',
)
const INPUT_PROBE_LABEL = 'проверка пригодности входа'
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor

const ROLE = { agent_type: 'stub', model: 'stub', skills: [] }
const PATHS = {
  feature_directory: '/tmp/workflow-input-fixture/feature',
  execution_path: '/tmp/workflow-input-fixture/PLANNER_EXECUTION.md',
  architecture_path: '/tmp/workflow-input-fixture/ARCHITECTURE.md',
  planner_context_path: '/tmp/workflow-input-fixture/planner-context.md',
  helper_path: '/tmp/workflow-input-fixture/plan_state.py',
}
const EXPECTED_KINDS = {
  feature_directory: 'directory',
  execution_path: 'file',
  architecture_path: 'file',
  planner_context_path: 'file',
  helper_path: 'file',
}
const INPUT = {
  ...PATHS,
  phases: [
    {
      key: 'phase-a',
      title: 'Фаза A',
      inputs: {},
      outputs: {},
      review_scope: {},
      implementer: ROLE,
    },
  ],
  max_fix_rounds: 2,
  reviewer: ROLE,
  documentation: 'not_required',
}

function loadWorkflowBody(scriptPath) {
  const source = fs.readFileSync(scriptPath, 'utf8')
  const body = source.replace(/^export const meta = \{[\s\S]*?\n\}\n/, '')
  if (body === source) throw new Error(`не удалось отрезать meta в ${scriptPath}`)
  return new AsyncFunction('agent', 'phase', 'parallel', 'log', 'args', body)
}

function receipt(payload) {
  return { exit_code: 0, raw_stdout: JSON.stringify(payload), raw_stderr: '' }
}

function inputProbe(overrides = {}) {
  return Object.fromEntries(
    Object.entries(EXPECTED_KINDS).map(([name, kind]) => [
      name,
      { kind, readable: true, ...(overrides[name] || {}) },
    ]),
  )
}

function workingSummary(kind, reportPath) {
  if (kind === 'review') {
    return [
      'Status: clean',
      `Report: ${reportPath}`,
      'Findings: major 0; minor 0; security 0; design 0',
      'Blocking: 0',
      'Certification boundary: тестовая подмена не подтверждает работу ролей',
      'Summary: замечаний нет',
    ].join('\n')
  }
  return [
    'Status: complete',
    `Report: ${reportPath}`,
    'Commands:',
    '- node test — подмена рабочего вызова',
    'Summary: работа выполнена',
    'Blocked checks: none',
  ].join('\n')
}

// Ответ «занятый путь» приходит вместо сводки, поэтому проверяется подменой
// самого ответа рабочей роли, а не подменой файла отчёта.
function occupiedAfterCorrection(rounds) {
  let occupied = 0
  return (label, reportPath) => {
    if (!label.startsWith('phase-a:implementation:')) return undefined
    if (occupied >= rounds) return undefined
    if (label.endsWith(':correction')) {
      occupied += 1
      return `Целевой путь занят: ${reportPath}`
    }
    return 'Сводка прозой без обязательных полей'
  }
}

async function runWorkflow(scriptPath, args, probe, workingScript) {
  const body = loadWorkflowBody(scriptPath)
  const calls = { sequence: [], inputProbes: [], working: [], reservations: [] }
  const reservations = new Map()
  const stubAgent = async (prompt, options = {}) => {
    const label = options.label || ''
    calls.sequence.push(label)

    if (options.agentType) {
      calls.working.push(label)
      const [, kind] = label.split(':')
      const reportPath = reservations.get(kind)
      if (!reportPath) throw new Error(`нет брони для рабочего вызова ${label}`)
      if (workingScript) {
        const scripted = workingScript(label, reportPath)
        if (scripted !== undefined) return scripted
      }
      return workingSummary(kind, reportPath)
    }

    if (label === INPUT_PROBE_LABEL) {
      calls.inputProbes.push({ prompt, options })
      return receipt(probe)
    }
    if (label.startsWith('гейт:')) {
      return receipt({ status: 'current', recorded_version: '1', current_version: '1' })
    }
    if (label.startsWith('резерв:')) {
      const [, phaseKey, kind] = label.split(':')
      const number = calls.reservations.filter((entry) => entry.kind === kind).length + 1
      const reportPath = `/tmp/workflow-input-fixture/${phaseKey}-${kind}-${number}.md`
      calls.reservations.push({ kind, path: reportPath })
      reservations.set(kind, reportPath)
      return receipt({ kind, path: reportPath, number, empties: [] })
    }
    if (label.startsWith('осмотр:')) {
      const [, phaseKey] = label.split(':')
      const kind = calls.working[calls.working.length - 1].split(':')[1]
      return receipt({
        path: reservations.get(kind),
        status: 'nonempty',
        size: 1,
        phaseKey,
      })
    }
    throw new Error(`неожиданный вызов агента «${label}»`)
  }

  try {
    return {
      result: await body(stubAgent, () => {}, async (thunks) => Promise.all(thunks.map((thunk) => thunk())), () => {}, args),
      calls,
    }
  } catch (error) {
    return { error: error.message, calls }
  }
}

const SCENARIOS = [
  {
    name: 'несуществующий помощник останавливает прогон до рабочего вызова',
    probe: inputProbe({ helper_path: { kind: 'missing', readable: false } }),
    expect: { reason: 'helper_path: path does not exist', probes: 1 },
  },
  {
    name: 'нечитаемый контекст останавливает прогон до рабочего вызова',
    probe: inputProbe({ planner_context_path: { readable: false } }),
    expect: { reason: 'planner_context_path: path is not readable', probes: 1 },
  },
  {
    name: 'неподставленная переменная останавливает прогон отдельной причиной',
    args: { ...INPUT, helper_path: '${CLAUDE_PLUGIN_ROOT}/plan_state.py' },
    probe: inputProbe(),
    expect: { reason: 'helper_path: contains an unsubstituted variable', probes: 0 },
  },
  {
    name: 'файл вместо каталога фичи останавливает прогон',
    probe: inputProbe({ feature_directory: { kind: 'file' } }),
    expect: { reason: 'feature_directory: expected directory, got file', probes: 1 },
  },
  {
    name: 'каталог вместо плана останавливает прогон',
    probe: inputProbe({ execution_path: { kind: 'directory' } }),
    expect: { reason: 'execution_path: expected file, got directory', probes: 1 },
  },
  {
    name: 'каталог вместо помощника останавливает прогон',
    probe: inputProbe({ helper_path: { kind: 'directory' } }),
    expect: { reason: 'helper_path: expected file, got directory', probes: 1 },
  },
  {
    name: 'пригодный вход доходит до первого рабочего вызова',
    probe: inputProbe(),
    expect: { reachesWorking: true },
  },
  {
    name: 'сводка по договору принимается и фаза доходит до ревью',
    probe: inputProbe(),
    expect: { accepted: { workingLabels: ['phase-a:implementation:1', 'phase-a:review:1'] } },
  },
  {
    name: 'занятый путь в ответе корректирующего вызова даёт новую бронь и повтор роли',
    probe: inputProbe(),
    working: occupiedAfterCorrection(1),
    expect: { collisionRetry: { repeatLabel: 'phase-a:implementation:2', implementationReservations: 2 } },
  },
  {
    name: 'три занятых пути после корректирующих вызовов останавливают прогон пределом',
    probe: inputProbe(),
    working: occupiedAfterCorrection(3),
    expect: { stopped: true, reason: 'target-path-collision-limit', workingCalls: 6 },
  },
]

function mismatch(outcome, expect) {
  if (outcome.error) return `сценарий выбросил исключение: ${outcome.error}`
  const { result, calls } = outcome
  if (expect.probes !== undefined && calls.inputProbes.length !== expect.probes) {
    return `релеев проверки пригодности ${calls.inputProbes.length} вместо ${expect.probes}`
  }
  if (expect.probes === 1) {
    const probeCommand = calls.inputProbes[0].prompt
    for (const value of Object.values(PATHS)) {
      if (!probeCommand.includes(`'${value}'`)) {
        return `релей проверки пригодности не получил путь ${value}`
      }
    }
  }

  if (expect.reachesWorking) {
    if (calls.working.length === 0) return 'пригодный вход не дошёл до рабочего вызова'
    return null
  }

  if (expect.accepted) {
    if (result.state === 'stopped' || result.state === 'failed') {
      return `прогон остановлен: ${result.reason}`
    }
    for (const label of expect.accepted.workingLabels) {
      if (!calls.working.includes(label)) {
        return `не было рабочего вызова ${label}: ${calls.working.join(', ')}`
      }
    }
    if (result.summary_deviations.length > 0) {
      return `сводка по договору записана в отклонения: ${JSON.stringify(result.summary_deviations)}`
    }
    return null
  }

  if (expect.collisionRetry) {
    const { repeatLabel, implementationReservations } = expect.collisionRetry
    if (result.state === 'stopped' || result.state === 'failed') {
      return `прогон остановлен вместо новой брони: ${result.reason}`
    }
    if (!calls.working.includes(repeatLabel)) {
      return `после занятого пути роль не вызвана заново: рабочие вызовы ${calls.working.join(', ')}`
    }
    const implementations = calls.reservations.filter((entry) => entry.kind === 'implementation')
    if (implementations.length !== implementationReservations) {
      return `броней реализации ${implementations.length} вместо ${implementationReservations}`
    }
    if (!result.summary_deviations.some((entry) => String(entry.detail).includes('target path occupied'))) {
      return 'занятый путь не записан в отклонения формы'
    }
    return null
  }

  if (expect.stopped) {
    if (result.state !== 'stopped') return `состояние «${result.state}» вместо stopped`
    if (!String(result.reason).includes(expect.reason)) {
      return `причина «${result.reason}» не называет «${expect.reason}»`
    }
    if (expect.workingCalls !== undefined && calls.working.length !== expect.workingCalls) {
      return `рабочих вызовов ${calls.working.length} вместо ${expect.workingCalls}: ${calls.working.join(', ')}`
    }
    return null
  }

  if (result.state !== 'failed') return `состояние «${result.state}» вместо failed`
  if (!String(result.reason).includes(expect.reason)) {
    return `причина «${result.reason}» не называет «${expect.reason}»`
  }
  if (result.working_calls !== 0) return `working_calls равен ${result.working_calls} вместо 0`
  if (calls.working.length !== 0) return `заглушка увидела ${calls.working.length} рабочих вызовов`
  return null
}

const rootIndex = process.argv.indexOf('--root')
const root = rootIndex === -1 ? null : process.argv[rootIndex + 1]
if (rootIndex !== -1 && !root) {
  console.error('FAIL: у --root нет значения')
  process.exit(1)
}
const scriptPath = root ? path.join(root, WORKFLOW_RELATIVE_PATH) : NEIGHBOUR_WORKFLOW_PATH
if (!fs.existsSync(scriptPath)) {
  console.error(`FAIL: не найден файл сценария: ${scriptPath}`)
  process.exit(1)
}

let failed = 0
for (const scenario of SCENARIOS) {
  const outcome = await runWorkflow(scriptPath, scenario.args || INPUT, scenario.probe, scenario.working)
  const problem = mismatch(outcome, scenario.expect)
  if (problem) {
    failed += 1
    console.log(`FAIL: ${scenario.name}\n      ${problem}`)
  } else {
    console.log(`ok: ${scenario.name}`)
  }
}

if (failed > 0) {
  console.log(`\nFAIL: сценариев с расхождением ${failed} из ${SCENARIOS.length}`)
  process.exit(1)
}
console.log(`\nPASS: ${SCENARIOS.length} сценариев рабочего workflow`)
