#!/usr/bin/env node

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const WORKFLOW = path.join(path.dirname(fileURLToPath(import.meta.url)), 'calque-sweep.js')
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor

function loadWorkflow() {
  const source = fs.readFileSync(WORKFLOW, 'utf8')
  const body = source.replace(/^export const meta = \{[\s\S]*?\n\}\n/, '')
  if (body === source) throw new Error('не удалось отделить meta рабочего процесса')
  return new AsyncFunction('agent', 'pipeline', 'phase', 'log', 'args', body)
}

async function run() {
  const body = loadWorkflow()
  let reportPrompt = ''

  const stubAgent = async (prompt, options = {}) => {
    const label = options.label || ''
    if (label.startsWith('поиск:')) {
      return {
        file: 'docs/example.md',
        candidates: [
          { word: 'green', line: 1, phrase: 'green — имя статуса' },
          { word: 'green', line: 2, phrase: 'green переводится в прозе' },
          { word: 'зелень', line: 3, phrase: 'Зелень оказалась неустойчивой' },
        ],
      }
    }
    if (label.startsWith('оценка:')) {
      return {
        file: 'docs/example.md',
        verdicts: [
          {
            word: 'green',
            line: 1,
            phrase: 'green — имя статуса',
            verdict: 'пример-или-цитата',
            replacement: 'не требуется',
            basis: 'контрактный литерал',
          },
          {
            word: 'green',
            line: 2,
            phrase: 'green переводится в прозе',
            verdict: 'калька',
            replacement: 'зелёный',
            basis: 'свободная проза',
          },
          {
            word: 'зелень',
            line: 3,
            phrase: 'Зелень оказалась неустойчивой',
            verdict: 'потерян-референт',
            replacement: 'зелёный итог прогона',
            basis: 'признак потерял носителя',
          },
        ],
      }
    }
    if (label === 'отчёт') {
      reportPrompt = prompt
      return { report_path: '.claude/report.md', glossary_terms: 3, places: 2 }
    }
    throw new Error(`неожиданный вызов агента: ${label}`)
  }

  const pipeline = async (items, ...stages) => {
    const rows = []
    for (let index = 0; index < items.length; index += 1) {
      let value = items[index]
      for (const stage of stages) value = await stage(value, items[index], index)
      rows.push(value)
    }
    return rows
  }

  const result = await body(stubAgent, pipeline, () => {}, () => {}, {
    mode: 'deep',
    repo_root: '/repo',
    files: ['docs/example.md'],
    report_path: '.claude/report.md',
  })

  return { result, reportPrompt }
}

function check({ result, reportPrompt }) {
  const failures = []
  const marker = 'Данные разбора:\n\n'
  const end = '\n\nОтчёт состоит'
  const start = reportPrompt.indexOf(marker)
  const finish = reportPrompt.indexOf(end, start + marker.length)
  if (start === -1 || finish === -1) {
    failures.push('промпт отчёта не содержит машинный блок данных')
  } else {
    const data = JSON.parse(reportPrompt.slice(start + marker.length, finish))
    if (data.requested_files?.length !== 1) failures.push('нет списка запрошенных файлов')
    if (data.evaluated_files?.length !== 1) failures.push('нет списка реально оценённых файлов')
    if (!data.verdicts?.every((row) => row.file === 'docs/example.md')) {
      failures.push('путь потерян при выравнивании вердиктов')
    }
    const green = data.verdicts?.filter((row) => row.word === 'green') || []
    if (green.length !== 2 || new Set(green.map((row) => row.verdict)).size !== 2) {
      failures.push('два контекста одного слова не сохранены раздельно')
    }
  }

  if (!reportPrompt.includes('ПО ВХОЖДЕНИЯМ')) {
    failures.push('отчёт не требует решения по вхождениям')
  }
  if (!reportPrompt.includes('«потерян-референт»')) {
    failures.push('потерянный референт не включён в места правки')
  }
  if (result.requested_files !== 1 || result.evaluated_files !== 1) {
    failures.push(`покрытие в результате неверно: ${JSON.stringify(result)}`)
  }
  if (result.to_replace !== 2) {
    failures.push(`мест к правке ${result.to_replace} вместо 2`)
  }

  if (failures.length) {
    for (const failure of failures) console.error(`FAIL: ${failure}`)
    process.exit(1)
  }
  console.log('PASS: вердикты остаются привязаны к вхождениям и покрытию')
}

check(await run())
