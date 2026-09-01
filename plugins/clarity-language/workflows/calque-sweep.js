export const meta = {
  name: 'calque-sweep',
  description: 'Первый проход собирает кандидатов, оценка проверяет референт и выбирает вердикт по каждому вхождению, отчёт пишется файлом',
  whenToUse: 'Когда нужен разбор русских текстов на кальки, придуманные переводы и замены с потерянным референтом по скиллу russian-style. Режим deep — только названные файлы. Режим full — весь репозиторий, запускается только явно. Режим по умолчанию не подставляется.',
  phases: [
    { title: 'Список файлов', detail: 'только в режиме full: перечислить русские тексты' },
    { title: 'Поиск', detail: 'Haiku собирает кандидатов, решений не принимает' },
    { title: 'Оценка', detail: 'каждый кандидат сверяется со списком решённых слов' },
    { title: 'Отчёт', detail: 'глоссарий и места замены пишутся файлом' },
  ],
}

const FILES_SCHEMA = {
  type: 'object',
  required: ['files'],
  properties: {
    files: { type: 'array', items: { type: 'string' } },
    note: { type: 'string' },
  },
}

const CANDIDATES_SCHEMA = {
  type: 'object',
  required: ['file', 'candidates'],
  properties: {
    file: { type: 'string' },
    candidates: {
      type: 'array',
      items: {
        type: 'object',
        required: ['word', 'line', 'phrase'],
        properties: {
          word: { type: 'string' },
          line: { type: 'integer' },
          phrase: { type: 'string' },
          why: { type: 'string' },
        },
      },
    },
  },
}

// Вердикт «спросить-человека» — не заглушка, а рабочий исход: протокол скилла
// запрещает решать спорное «перевести или оставить» в одиночку.
const VERDICTS_SCHEMA = {
  type: 'object',
  required: ['file', 'verdicts'],
  properties: {
    file: { type: 'string' },
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        required: ['word', 'line', 'verdict'],
        properties: {
          word: { type: 'string' },
          line: { type: 'integer' },
          phrase: { type: 'string' },
          verdict: {
            type: 'string',
            enum: [
              'устоявшееся',
              'калька',
              'новодел',
              'потерян-референт',
              'референт-восстановим-рядом',
              'пример-или-цитата',
              'спросить-человека',
            ],
          },
          replacement: { type: 'string' },
          basis: { type: 'string' },
          // Для «референт-восстановим-рядом» — что именно его восстанавливает:
          // без этого текста вердикт не отличается от «устоявшееся».
          restored_by: { type: 'string' },
        },
      },
    },
  },
}

const REPORT_SCHEMA = {
  type: 'object',
  required: ['report_path', 'glossary_terms', 'places'],
  properties: {
    report_path: { type: 'string' },
    glossary_terms: { type: 'integer' },
    places: { type: 'integer' },
  },
}

const MODES = ['deep', 'full']
const mode = args && args.mode
if (!MODES.includes(mode)) {
  throw new Error(
    'calque-sweep: args.mode обязателен и равен "deep" или "full". ' +
      'Значение по умолчанию не подставляется: full идёт по всему репозиторию и запускается только явно.',
  )
}

const repoRoot = (args && args.repo_root) || '.'
const reportPath = (args && args.report_path) || 'calque-sweep-report.md'
const skillPath = (args && args.skill_path) || 'plugins/clarity-language/skills/russian-style/SKILL.md'
const lexiconPath = args && args.lexicon_path
const maxFiles = Number.isInteger(args && args.max_files) ? args.max_files : 60

let files = Array.isArray(args && args.files) ? args.files : []

if (mode === 'deep') {
  if (files.length === 0) {
    throw new Error('calque-sweep: режим deep разбирает только названные файлы — нужен непустой args.files.')
  }
} else {
  phase('Список файлов')
  const listed = await agent(
    `Рабочий каталог: ${repoRoot}\n\n` +
      `Перечисли файлы с русскоязычной прозой, которые стоит разобрать на кальки: ` +
      `документацию, промпты скиллов и агентов, README, справочники. ` +
      `Не включай файлы без русского текста, сгенерированные каталоги, файлы результатов прогонов ` +
      `и всё, что игнорируется git. Верни пути относительно рабочего каталога. ` +
      `Если файлов больше ${maxFiles}, верни ${maxFiles} самых крупных по объёму русского текста ` +
      `и скажи в note, сколько осталось за границей.`,
    { label: 'список файлов', phase: 'Список файлов', schema: FILES_SCHEMA, effort: 'low' },
  )
  files = listed && Array.isArray(listed.files) ? listed.files : []
  if (listed && listed.note) log(`охват: ${listed.note}`)
}

if (files.length > maxFiles) {
  log(`файлов ${files.length}, разбираются первые ${maxFiles}; за границей осталось ${files.length - maxFiles}`)
  files = files.slice(0, maxFiles)
}
if (files.length === 0) {
  return { mode, files: 0, report_path: null, note: 'разбирать нечего: список файлов пуст' }
}
log(`режим ${mode}, файлов к разбору: ${files.length}`)

const lexiconLine = lexiconPath
  ? `Список вердиктов проекта по конкретным словам: ${lexiconPath}. Он главнее общего списка.`
  : 'Списка вердиктов проекта не передано — опирайся только на список решённых слов в скилле.'

// Поиск и оценка идут конвейером: файл уходит на оценку, как только по нему
// собраны кандидаты, и не ждёт остальных.
const perFile = await pipeline(
  files,
  (file) =>
    agent(
      `Рабочий каталог: ${repoRoot}\n\n` +
        `Прочитай файл ${file} и собери кандидатов на кальку и на придуманный перевод термина: ` +
        `иноязычные слова там, где есть точное русское; отглагольные существительные на месте глагола; ` +
        `русские новоделы вместо живого заимствования; математические знаки в прозе.\n\n` +
        `Твоя работа — только собрать кандидатов. Решений не принимай, замен не предлагай, ` +
        `устоявшиеся заимствования не отсеивай: отсев — работа следующего шага. ` +
        `На каждого кандидата верни слово, номер строки и фразу целиком, в которой он стоит.`,
      { label: `поиск:${file}`, phase: 'Поиск', schema: CANDIDATES_SCHEMA, model: 'haiku', effort: 'low' },
    ),
  (found, file) => {
    if (!found || !Array.isArray(found.candidates) || found.candidates.length === 0) {
      return { file, verdicts: [] }
    }
    const listing = found.candidates
      .map((c) => `- строка ${c.line}: «${c.word}» в фразе «${c.phrase}»`)
      .join('\n')
    return agent(
      `Рабочий каталог: ${repoRoot}\n\n` +
        `Прочитай правило 1 и раздел про устоявшиеся заимствования в ${skillPath}. ${lexiconLine}\n\n` +
        `Оцени кандидатов из файла ${file}:\n${listing}\n\n` +
        `Порядок работы: сначала сверься со списком решённых слов — по ним вопрос закрыт, ` +
        `заново их не разбирай. Эвристику произносимости применяй только к словам вне списка.\n\n` +
        `На каждого кандидата дай вердикт:\n` +
        `- «устоявшееся» — слово прижилось, трогать не надо;\n` +
        `- «калька» — есть точное русское слово, приведи его в replacement;\n` +
        `- «новодел» — придуман русский перевод термина, который говорят только заимствованием; ` +
        `в replacement верни заимствование;\n` +
        `- «потерян-референт» — замена уже сделана и дословно верна, но читатель без ` +
        `английского оригинала не может назвать вещь или поведение. Признаки: признак ` +
        `термина стал существительным («зелёный прогон» → «зелень»); переведена половина ` +
        `сочетания; исчез различительный признак поведения («нестабильные тесты» вместо ` +
        `flaky). В replacement дай форму, где референт назван;\n` +
        `- «референт-восстановим-рядом» — слово размыто само по себе, но соседний текст ` +
        `восстанавливает референт числом, определением или примером. В restored_by приведи ` +
        `этот текст дословно. Без него вердикт не годится: тогда это «потерян-референт»;\n` +
        `- «пример-или-цитата» — слово стоит внутри правила как образец ошибки, в таблице ` +
        `«так не пишем» или в дословной цитате. Такой текст не правится, и дефектом он не ` +
        `считается: замена сломала бы само правило. Не помечай его калькой с оговоркой ` +
        `в основании — для этого случая есть отдельный вердикт;\n` +
        `- «спросить-человека» — случай спорный. Свой вердикт вместо человека не выноси: ` +
        `при сомнении «перевести или оставить» это и есть правильный ответ.\n\n` +
        `В basis укажи, на чём вердикт стоит: строка списка решённых слов, запись лексикона ` +
        `или эвристика произносимости.`,
      { label: `оценка:${file}`, phase: 'Оценка', schema: VERDICTS_SCHEMA },
    )
  },
)

const byFile = perFile.filter(Boolean)
// Вердикт контекстен: одно слово в контрактном литерале и в свободной прозе
// получает разные решения. Путь принадлежит каждому вхождению, а не только
// внешней обёртке результата — иначе при выравнивании он теряется, и отчёт
// вынужден угадывать источник по строке.
const verdicts = byFile.flatMap((r) =>
  Array.isArray(r.verdicts) ? r.verdicts.map((v) => ({ ...v, file: r.file })) : [],
)
const actionable = verdicts.filter(
  (v) => v.verdict === 'калька' || v.verdict === 'новодел' || v.verdict === 'потерян-референт',
)
const toAsk = verdicts.filter((v) => v.verdict === 'спросить-человека')
const settled = verdicts.filter((v) => v.verdict === 'устоявшееся')
const asExample = verdicts.filter((v) => v.verdict === 'пример-или-цитата')

log(
  `кандидатов оценено: ${verdicts.length}; к замене: ${actionable.length}; ` +
    `на решение человеку: ${toAsk.length}; оставлено как есть: ${settled.length}; ` +
    `примеры и цитаты: ${asExample.length}`,
)

if (verdicts.length === 0) {
  return {
    mode,
    files: files.length,
    report_path: null,
    note: 'кандидатов не нашлось — отчёт не пишется',
  }
}

phase('Отчёт')
const written = await agent(
  `Рабочий каталог: ${repoRoot}\n\n` +
    `Запиши отчёт разбора в файл ${reportPath}. Данные разбора:\n\n` +
    JSON.stringify(
      {
        mode,
        requested_files: files,
        evaluated_files: byFile.map((r) => r.file),
        verdicts,
      },
      null,
      1,
    ) +
    `\n\nОтчёт состоит из двух частей.\n\n` +
    `Первая — решения ПО ВХОЖДЕНИЯМ, не по слову. У каждой строки обязательны ` +
    `путь:строка, слово, вердикт, предлагаемая замена, фраза целиком и основание. ` +
    `Не объединяй два вхождения одного слова: в контрактном литерале и в свободной прозе ` +
    `они законно получают разные вердикты. Разнеси строки по семи разделам-вердиктам. ` +
    `Для «референт-восстановим-рядом» обязательно напечатай restored_by; без него строка ` +
    `считай недействительной. Для «спросить-человека» сформулируй вопрос тремя исходами.\n\n` +
    `Вторая — места замены: все вхождения с вердиктами «калька», «новодел» ИЛИ ` +
    `«потерян-референт». Примеры, цитаты, устоявшиеся слова и «референт-восстановим-рядом» ` +
    `сюда не попадают. Одна строка — одно вхождение вида ` +
    `«путь:строка — фраза целиком → замена». Не группируй по слову: замена зависит от фразы. ` +
    `Фраза нужна целиком, а не обрезанная — согласование живёт в соседних словах.\n\n` +
    `Перед двумя частями напиши покрытие: сколько файлов запросили и сколько реально получили ` +
    `вердикты; перечисли непроверенные файлы. «Разобрано файлов» означает число evaluated_files, ` +
    `а не размер requested_files. Отчёт нужен для применения человеком, поэтому не пиши в нём ` +
    `ничего, кроме покрытия и этих двух частей. Файлы, кроме отчёта, не правь.`,
  { label: 'отчёт', phase: 'Отчёт', schema: REPORT_SCHEMA },
)

return {
  mode,
  requested_files: files.length,
  evaluated_files: byFile.length,
  candidates: verdicts.length,
  to_replace: actionable.length,
  to_ask_human: toAsk.length,
  left_as_is: settled.length,
  report_path: written ? written.report_path : null,
}
