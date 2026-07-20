# SoTA Research — Кураторская функция: провенанс, сборка носителя, дисциплина формата (Фаза 1, G.2)

> **Дата сбора:** 2026-07-06. **Метод:** FPF G.2 (SoTA Harvest), web-ресёрч (WebSearch/WebFetch).
> **Scope (FPF A.2.6 USM):** дисциплина курирования сводов знаний КАК АРТЕФАКТОВ — не их содержания.
> Традиции шире нашего каталога DPF: архивно-библиотечная наука (provenance/curation lifecycle),
> технический authoring (topic-based reuse, structured writing), редакторско-издательская дисциплина
> (сжатие без потери смысла, реферирование), governance разделяемых эталонных данных (golden record,
> taxonomy stewardship). **Наш bounded context (не ограничивает SoTA):** keeper курирует библиотеку
> `project/frameworks/DPF-*` (33 компетенции) + зеркалирует канон метода между `~/.claude/skills/
> dpf-authoring/` и комнатой `DPF-AUTHORING/`, вручную, markdown, без формальных архивных систем/RDF.
> **Intended reader:** роль, строящая `theses-antitheses.md` (Фаза 2) и `DPF.md` (Фаза 5) для
> DPF-KNOWLEDGE-CURATION. Этот файл — сырьё SoTA с источниками, не решения и не наш код.
> **Trust-cue:** `fact` = первичный документ/стандарт/код/данные; `hypothesis` = выведено/single-source/
> conditional; `opinion` = vendor/practitioner-фрейминг.
> **Carrier note (CC-DPF.5):** все web-источники — carriers, допущены через admission; каждый claim
> несёт источник+URL+дату (claim без источника = мнение, A.10).

---

## CorpusLedger (источники)

> Триаж: **include** = несущий, цитируем; **park** = полезно, но вторично/illustrative; **retire** = опровергнуто/устарело/несоответствие премиссе.

| # | Источник (URL) | Традиция | Тип | Триаж | Почему | Дата |
|---|----------------|----------|-----|-------|--------|------|
| S1 | ISO 14721:2025 — OAIS reference model (iso.org/standard/87471.html) | T1 Digital Curation | стандарт (сведения о) | **include** | текущая (3-е изд.) редакция эталонной модели архивации; идентична CCSDS 650.0-M-3 | 2025 (CCSDS дек-2024) |
| S2 | Wikipedia — Open Archival Information System (en.wikipedia.org/wiki/Open_Archival_Information_System) | T1 Digital Curation | secondary/encyclopedia | **include** | компактное определение 3 типов информационных пакетов + 6 функциональных сущностей | rolling 2026 |
| S3 | DCC — Digital Curation 101: OAIS Reference Model (dcc.ac.uk/sites/default/files/documents/DCC%20101%20OAIS%20Overview.pdf) | T1 Digital Curation | practitioner primary (DCC — UK Digital Curation Centre) | **include** | учебный разбор PDI (Preservation Description Information), включая Provenance Information | rolling |
| S4 | DCC — Using the OAIS Reference Model for Curation (dcc.ac.uk/resources/curation-reference-manual/chapters-production/using-oais-reference-model-curation) | T1 Digital Curation | practitioner primary | **include** | практическое применение модели к процессу курирования (не только архивации) | rolling |
| S5 | Higgins, S. — The DCC Curation Lifecycle Model (dcc.ac.uk/sites/default/files/documents/publications/DCCLifecycle.pdf) | T1 Digital Curation | academic/practitioner primary | **include** | canonical lifecycle-модель: full lifecycle / sequential / occasional actions; первая публикация 2007, финализирована 2008 | 2008 (модель), ссылка rolling |
| S6 | Wikipedia — Digital Curation Centre (en.wikipedia.org/wiki/Digital_Curation_Centre) | T1 Digital Curation | secondary | **park** | организационный контекст DCC, вторично к S5 | rolling 2026 |
| S7 | OASIS — Introduction to DITA, DITA 1.3 spec (oxygenxml.com/dita/1.3/specs/archSpec/base/introduction-to-dita.html) | T2 Structured Authoring | primary стандарт (OASIS) | **include** | канон-определение: topic = discrete typed unit (concept/task/reference), модульность+специализация | 2016 (DITA 1.3), актуальна |
| S8 | Wikipedia — Darwin Information Typing Architecture (en.wikipedia.org/wiki/Darwin_Information_Typing_Architecture) | T2 Structured Authoring | secondary | **include** | история: IBM-происхождение нач. 2000-х → OASIS 2004 → стандарт 2005; content reuse без дублирования в исходниках | rolling 2026 |
| S9 | Wikipedia — Structured writing (en.wikipedia.org/wiki/Structured_writing) | T2 Structured Authoring | secondary | **include** | определение дисциплины: структурированные документы для быстрого усвоения | rolling |
| S10 | Wikipedia — Robert E. Horn (en.wikipedia.org/wiki/Robert_E._Horn) | T2 Structured Authoring | secondary (биографич. + метод) | **include** | Information Mapping (1963–1965), Chunking Principle — дробление на короткие связанные блоки | rolling |
| S11 | Wikipedia — Minimalism (technical communication) (en.wikipedia.org/wiki/Minimalism_(technical_communication)) | T2 Structured Authoring | secondary | **include** | DITA построена на минимализме Кэрролла + Information Mapping Хорна; JoAnn Hackos связывает минимализм с DITA-практикой | rolling |
| S12 | Writer's Digest — Omit Needless Words: Ruthless Editing 101 (writersdigest.com/be-inspired/omit-needless-words-ruthless-editing-101) | T3 Editorial Compression | practitioner (издательская традиция, восходит к Strunk & White) | **include** | принцип: не используй наречие, если хватит сильного глагола (структурная, не косметическая правка) | rolling |
| S13 | The Journalist's Resource — Copyediting for reporters (journalistsresource.org/home/copyediting-for-reporters/) | T3 Editorial Compression | practitioner (журналистика) | **include** | copyediting = обрезка под объём с сохранением важнейших пунктов; устранение жаргона | rolling |
| S14 | ANSI/NISO Z39.14-1997 (R2015) — Guidelines for Abstracts (niso.org/publications/ansiniso-z3914-1997-r2015-guidelines-abstracts) | T3 Editorial Compression | primary стандарт (ANSI/NISO) | **include** | формальный национальный стандарт сжатия: abstract = «abbreviated ACCURATE representation of a document»; переиздан 1987/2002/2010/2015 — долгоживущий консенсус | 1997, reaffirmed 2015 |
| S15 | Profisee — What Is a Golden Record in MDM? (profisee.com/blog/what-is-a-golden-record/) | T4 Reference-Data Governance | vendor/practitioner | **include** | golden record = согласованное представление сущности из НЕСКОЛЬКИХ систем, не назначение одной системы «главной» | rolling |
| S16 | Informatica — What is a Golden Record in MDM? (informatica.com/blogs/golden-record.html) | T4 Reference-Data Governance | vendor/practitioner | **include** | ключевое разграничение: «single source of truth — организационный ИСХОД (consistent reliance), не сущность данных» | rolling |
| S17 | KMWorld — Best Practices for Taxonomy Governance (kmworld.com/Articles/News/News/Best-Practices-for-Taxonomy-Governance-128364.aspx) | T4 Reference-Data Governance | practitioner | **include** | governance = team + policy + editorial guidelines для добавления/правки/удаления терминов словаря | rolling |
| S18 | Hedden Information Management — Taxonomy Governance (hedden-information.com/taxonomy-governance/) | T4 Reference-Data Governance | practitioner primary (признанный автор в taxonomy-практике) | **include** | team charter описывает scope+роли+ответственность команды словаря; непрерывный пересмотр | rolling |
| S19 | Microsoft — LLMLingua (github.com/microsoft/LLMLingua) | AI-slice | primary (репозиторий + EMNLP'23/ACL'24 статьи) | **include** | до 20× сжатие промпта «with minimal performance loss» — perplexity-based token pruning | 2023–2024 |
| S20 | LLMLingua-2 — Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression (aclanthology.org/2024.findings-acl.57/) | AI-slice | academic (ACL Findings 2024) | **include** | сжатие переформулировано как supervised token-classification, обучен на дистилляции GPT-4, явная цель — «faithful», не только короче | 2024 (ACL Findings) |
| S21 | LongLLMLingua (aclanthology.org/2024.acl-long.91.pdf) | AI-slice | academic (ACL 2024) | **park** | question-aware coarse-to-fine сжатие для длинного контекста, до +21.4% качества при меньшем числе токенов — иллюстрирует, но вторично к S20 | 2024 |
| S22 | Prompt Compression for Large Language Models: A Survey (arxiv.org/html/2410.12388v2) | AI-slice | academic survey | **include** | систематизация подходов; общий вывод поля — компрессия без явной faithfulness-цели рискует смысловыми потерями | 2024-10 |
| S23 | FaithBench: A Diverse Hallucination Benchmark for Summarization by Modern LLMs (arxiv.org/abs/2410.13210; NAACL 2025) | AI-slice | academic benchmark | **include** | «challenging» галлюцинации = случаи, где SOTA-детекторы (включая GPT-4o-судью) РАСХОДЯТСЯ; детекторы держат ~50% точности — сжатие/пересказ смысла AI сегодня ненадёжно самопроверяемо | 2024-10 (arXiv) / 2025 (NAACL) |
| S24 | Scientific Reports — A hallucination detection and mitigation framework for faithful text summarization using LLMs (nature.com/articles/s41598-025-31075-1) | AI-slice | academic | **park** | фреймворк детекции/митигации несоответствий source↔summary; иллюстрация направления, не несущий claim | 2025 |
| S25 | VeriCite: Towards Reliable Citations in RAG via Rigorous Verification (dl.acm.org/doi/10.1145/3767695.3769505, SIGIR-AP 2025) | AI-slice | academic | **include** | явная верификация цитаты→claim снижает недостоверную атрибуцию в RAG-ответах | 2025 |
| S26 | TREC 2025 RAG Track overview (arxiv.org/abs/2603.09891) | AI-slice | academic (community benchmark track) | **include** | многоуровневая оценка: relevance + response completeness + **attribution verification** + agreement — provenance стал измеримым критерием, не декларацией | 2026-03 (препринт номер), трек 2025 |
| S27 | Document360 — Documentation Drift: Causes, Impact & How to Prevent It (document360.com/blog/documentation-drift/) | AI-slice/practitioner (docs-as-code) | vendor/practitioner | **include** | причина дрейфа — «too many places that look like source of truth»: README, wiki, тикеты, устная память | rolling 2026 |
| S28 | Docuwiz — Docs-as-Code: How to Prevent API Documentation Drift (blog.docuwiz.io/p/docs-as-code-how-to-prevent-api-documentation) | AI-slice/practitioner | vendor/practitioner | **park** | иллюстрация решения (генерация доков из одной спеки) — вторично к S27, наш случай (канон метода) не кодогенерируем | rolling |
| R1 | Премисса «токен-прунинг compression по умолчанию безопасен для смысла, если сохраняет perplexity/длину» | AI-slice | — | **retire** | опровергнуто мотивацией самого LLMLingua-2: LLMLingua-1 (чистый perplexity-based pruning) потребовал отдельной faithfulness-ориентированной версии именно потому, что «сжато и правдоподобно» ≠ «сжато и верно» (S19 vs S20) | — |

---

## ClaimSheets по традициям

### Традиция 1 — Digital Curation / Archival Science: OAIS + DCC Curation Lifecycle

**Commitments школы:** курируемый объект несёт явную, накопительную **Provenance Information** — историю
происхождения и всех трансформаций, а не только текущее состояние; курирование — не разовое действие, а
**жизненный цикл** с разными типами действий (постоянные/описательные, последовательные/трансформирующие,
случающиеся эпизодически). **Validity region:** долгоживущие цифровые объекты, которые должны оставаться
понятными/используемыми ПОСЛЕ смены контекста создания (архивы, датасеты, институциональная память);
избыточна полная OAIS-механика (Submission/Archival/Dissemination пакеты, 6 функциональных сущностей) для
одного markdown-каталога, поддерживаемого вручную маленькой командой — берём принцип, не аппарат.

- **T1.1** Provenance Information — часть Preservation Description Information (PDI), фиксирующая историю
  объекта: происхождение, цепочку хранения, все трансформации с момента создания. — *bounded:* архивный
  объект, переживающий смену контекста. — *evidence:* S1, S3. — **fact**
- **T1.2** OAIS различает 3 вида информационных пакетов (Submission/Archival/Dissemination) — то, ЧТО
  поступает, ЧТО хранится, ЧТО отдаётся потребителю, НЕ идентичны по составу метаданных. — *evidence:*
  S1, S2. — **fact**
- **T1.3** DCC Curation Lifecycle Model делит действия на 3 класса: **full-lifecycle** (постоянные —
  description/representation information, preservation planning, community watch/participation),
  **sequential** (conceptualise → create/receive → appraise/select → ingest → preservation action →
  store → access/use/reuse → transform), **occasional** (dispose, reappraise, migrate). — *evidence:*
  S5. — **fact**
- **T1.4** Метаданные создаются одновременно с объектом (administrative/descriptive/structural/technical),
  preservation-метаданные добавляются НЕ постфактум, а в момент создания — откладывание удорожает
  реконструкцию провенанса позже. — *evidence:* S5. — **fact/hypothesis** (принцип задокументирован; наш
  перенос на «пиши source-pack в момент решения, не после DPF.md» — прямая параллель Research-first
  гейту метода, но это НАШ вывод, не дословный источник)
- **T1.5** Курирование добавляет ценность через provenance + метаданные + СВЯЗИ между выходами
  («links between outputs to provide context» — практика context-mapping архивной науки). — *evidence:*
  S4, S5. — **fact**

### Традиция 2 — Structured / Topic-Based Technical Authoring: DITA, Information Mapping, Minimalism

**Commitments школы:** содержимое разбивается на маленькие, типизированные, самодостаточные единицы
(topics), которые **переиспользуются по ссылке**, а не копируются; каждый topic отвечает РОВНО на один тип
вопроса (concept/task/reference); информация группируется в маленькие связанные «чанки», размер которых
подобран под возможности читателя удержать их разом. **Validity region:** документация с несколькими
изданиями/продуктами/аудиториями из общего корпуса контента; избыточен XML/DITA-тулинг для одного канона
метода с единственным изданием — берём принцип reuse-by-reference и chunking, не формат.

- **T2.1** Topic — дискретная, типизированная (concept/task/reference) единица информации с ЕДИНЫМ
  намерением; удобна и человеку (сканирование), и машине (обработка). — *evidence:* S7. — **fact**
- **T2.2** Content reuse: элемент/topic определяется ОДИН раз и подключается в разные места через
  ссылку (conref/keyref), не копипастом в исходники — иначе правка в одном месте не долетает до других
  копий (документационный аналог T1-провенанса: без явной связи копии расходятся незаметно). —
  *evidence:* S8. — **fact**
- **T2.3** DITA донирован IBM в OASIS (2004), стандарт с 2005 — модульность + специализация как
  архитектурные примитивы, не разовое решение одного автора. — *evidence:* S8. — **fact**
- **T2.4** Chunking Principle (Horn, 1963–1965): чтобы аудитория удерживала информацию, автор ОБЯЗАН
  дробить её на компактные, тематически цельные блоки — предшественник современного «один
  паттерн/секция = одна функция» в структурированных носителях. — *evidence:* S10. — **fact**
- **T2.5** Минимализм (Кэрролл) + Information Mapping (Хорн) — двойной фундамент DITA-практики (Hackos):
  контент действие-ориентирован, читателю не выдаётся лишнее сверх того, что нужно для текущей задачи.
  Прямая параллель PFM2 («паттерны — главный язык носителя», тяжёлые карты — вторичны/в references). —
  *evidence:* S11. — **fact** (принцип) / **hypothesis** (наша параллель к PFM2 — не заявлена дословно
  источником)

### Традиция 3 — Editorial / Publishing Compression Discipline: copyediting + formal abstracting (ANSI Z39.14)

**Commitments школы:** сжатие текста — не произвольное укорачивание, а РЕМЕСЛО с критерием: результат
остаётся **самодостаточным и точным представлением** источника, без добавления и без потери
смыслонесущих утверждений; формальный жанр (abstract) имеет стандартизованные требования к составу
(назначение, метод, результат, вывод), не просто «покороче». **Validity region:** любой перенос текста
из длинного/первичного носителя в короткий/вторичный (научные абстракты, новостные лиды, release notes);
неприменимо там, где сокращение НЕ требуется (сырой лог, verbatim-цитата как evidence).

- **T3.1** «Omit needless words» (Strunk & White через журналистскую традицию) — сокращение достигается
  заменой слабых конструкций (прилагательное+существительное, наречие+глагол) на точные слова, а не
  вырезанием случайных кусков. — *evidence:* S12. — **fact/opinion** (принцип стилистики, не
  измеримый стандарт)
- **T3.2** Copyediting под объём («cutting to fit») сохраняет ВАЖНЕЙШИЕ пункты, устраняя избыточность/
  жаргон — редактор обязан знать, ЧТО является несущим утверждением, ДО того как резать. — *evidence:*
  S13. — **fact**
- **T3.3** ANSI/NISO Z39.14 формально определяет abstract как «abbreviated ACCURATE representation of a
  document» — точность (accuracy) — обязательный, не опциональный, критерий сжатия; стандарт
  переиздавался 1987/2002/2010/2015 — долгоживущий межиндустриальный консенсус (>25 лет ревизий без
  замены принципа). — *evidence:* S14. — **fact**
- **T3.4** Формальный abstract воспроизводим «с малыми изменениями или без них» во вторичных
  публикациях — то есть должен быть **самодостаточным носителем**, не требующим оригинала для
  корректной интерпретации. Прямая параллель CC-DPF.8 (структурный отчёт носителя должен быть понятен
  сам по себе). — *evidence:* S14. — **fact** (стандарт) / **hypothesis** (наша параллель к CC-DPF.8)

### Традиция 4 — Governance разделяемых эталонных данных: MDM Golden Record + Taxonomy Governance

**Commitments школы:** «единый источник истины» — это НЕ один физический артефакт, назначенный главным, а
**организационный результат согласования** нескольких источников по явному процессу (survivorship rules,
editorial guidelines); поддержание эталона требует постоянной РОЛИ (steward/team), а не разового
создания. **Validity region:** данные/термины, которыми пользуются НЕСКОЛЬКО независимых потребителей
(системы, команды, роли) и которые должны оставаться взаимно согласованными во времени; избыточно для
единичного файла с одним читателем и одним автором.

- **T4.1** Golden Record — согласованное entity-level представление, полученное **примирением** данных
  из нескольких систем-источников, а НЕ выбором одной системы как «главной». — *evidence:* S15. —
  **fact**
- **T4.2** Single Source of Truth — организационный ИСХОД («consistent reliance on the same authoritative
  information»), не свойство отдельного файла/таблицы. Файл может называться «канон», но SSoT
  достигается только если ВСЕ потребители реально им пользуются, а не параллельными копиями. —
  *evidence:* S16. — **fact/hypothesis** (переопределение — vendor-фрейминг, но логически устойчивое)
- **T4.3** Golden record создаётся явным процессом из 6 шагов: ingestion → matching → survivorship rules
  → validation → publication → **maintenance** — поддержание не менее формально, чем создание. —
  *evidence:* S15. — **fact**
- **T4.4** Taxonomy governance требует team charter (scope + роли + ответственность) и editorial
  guidelines для добавления/правки/удаления терминов — governance словаря ИМЕЕТ Owner-роль (steward),
  без которой словарь дрейфует несмотря на первоначальное качество. — *evidence:* S17, S18. — **fact**

---

## Срез: ИИ в курировании и сжатии знаний (compression faithfulness, citation grounding, drift)

**Тезис среза:** для ИИ-агентов курирование текста — не редакторское удобство, а измеримый риск:
compression/пересказ без явной faithfulness-цели статистически теряет смыслонесущие токены, а
неявная/неверифицированная атрибуция источника в генерируемом тексте порождает недостоверные claim'ы,
которые «звучат убедительно» ровно так же, как достоверные (тот же провал, что и в S24-S26 у
DPF-KNOWLEDGE, здесь — применительно к самому акту компрессии/курирования, не к домену).

**Инструменты / кодоген / институциональное знание:**
- **AI.1** LLMLingua (2023) — perplexity-based token pruning, до 20× сжатие «with minimal performance
  loss» — заявка на low-loss, но БЕЗ явной faithfulness-цели в обучении. — *evidence:* S19. — **fact**
- **AI.2** LLMLingua-2 (2024) — переформулировал компрессию как supervised token-classification,
  обученный на GPT-4-дистилляции ИМЕННО для «efficient AND faithful» сжатия — индустрия сама признала,
  что «короче» и «сохраняет смысл» не одно и то же, потребовалась ОТДЕЛЬНАЯ метрика/цель faithfulness.
  — *evidence:* S20. — **fact** [ключевой контрпример для DPF-KNOWLEDGE-CURATION: «сжатие без потери
  смысла» — не побочный эффект компактности, а отдельная, explicitly optimized цель]
- **AI.3** Prompt Compression Survey (2024) фиксирует поле целиком движется от «чисто короче» к «короче
  и верифицируемо faithful» как явному критерию качества компрессора. — *evidence:* S22. — **fact**
  (обзорное наблюдение)

**Failure modes (специфичные для ИИ-курирования):**
- **AI.4** FaithBench (2025): даже SOTA-детекторы галлюцинаций (включая LLM-судей) держат ~50% точности
  на «сложных» случаях — то есть **самопроверка AI собственного сжатия ненадёжна** на грани; нужен
  внешний критерий (наш аналог — guardian-критик Фазы 6, отдельный от автора сжатия). — *evidence:*
  S23. — **fact**
- **AI.5** VeriCite (2025) и TREC 2025 RAG Track вводят **явную верификацию** цитата→claim (attribution
  verification) как отдельный измеримый шаг, а не следствие «хорошего» текста — прямая параллель нашему
  правилу «claim без источника+даты = мнение» (A.10), но с индустриальным evidence, что БЕЗ явной
  верификации атрибуция систематически ненадёжна даже когда ссылки присутствуют синтаксически. —
  *evidence:* S25, S26. — **fact**
- **AI.6** Documentation Drift (практика docs-as-code): корень проблемы — «слишком много мест, похожих
  на источник истины» (README, wiki, тикеты, устная память); канон и его зеркала расходятся именно
  потому, что расхождение НЕ детектируется автоматически, если места хранения формально разные системы.
  Прямая параллель задаче «зеркалирование канона» этой компетенции: скилл (`~/.claude/skills/
  dpf-authoring/`) и комната (`DPF-AUTHORING/`) — два места, похожих на источник истины, без
  автоматического detection расхождения. — *evidence:* S27. — **fact/opinion** (механизм
  задокументирован практикой; наш перенос на 2 конкретных файла — hypothesis)

**Research-gap (для Фазы 2/critic):** нет контролируемого исследования, изолирующего именно ЭФФЕКТ
структурного гейта (research-first, canon-скелет, PFM7 «носитель без процессного состояния») НА
downstream-точность маленькой мультиагентной команды, курирующей МАРКДАУН-каталог (не архив/датасет и
не индустриальный prompt-компрессор). AI.1–AI.6 — из смежных, но не тождественных масштабов (prompt-
инженерия для LLM inference, industrial RAG citation, docs-as-code для кода). Перенос на «keeper
курирует markdown-DPF вручную» — hypothesis, не проверенный факт; то же ограничение уже зафиксировано
в `DPF-KNOWLEDGE/references/sota-research.md` для соседней компетенции — не переоткрывать, а
унаследовать как общее ограничение SoTA-переноса в этом каталоге.

---

## MicroExamples (worked, ОБЩИЕ — дисциплина, НЕ наш DPF-каталог)

**ME-1 — Provenance-цепочка растёт, не переписывается (OAIS/DCC, T1).** Датасет оцифрован в 2010,
мигрирован в новый формат в 2015, обогащён метаданными в 2020. Provenance Information после 2020 —
это ВСЕ ТРИ события по порядку, а не только «текущий формат, создан 2010». Аналог: реестр
`source-pack.md` при ремонте DPF пополняется записью о ремонте, старые adopted/rejected-строки не
стираются задним числом — иначе теряется история решений (A.10, Source loss). — *источник:* S1, S3, S5.

**ME-2 — Reuse-by-reference vs копипаст (DITA, T2).** Раздел «предварительные требования установки»
переиспользуется в 3 руководствах (Windows/Linux/Docker) через ссылку на ОДИН topic. При изменении
требования правится ОДИН файл, все 3 руководства получают правку автоматически. Если бы раздел был
скопирован 3 раза текстом — правка в одном месте молча не долетела бы до двух других (документационный
аналог documentation drift, AI.6). — *источник:* S8.

**ME-3 — Chunking: 12 фактов → 3 подписанных блока по 4 (Horn, T2).** Абзац, перечисляющий вперемешку
причины отказа сервера, шаги диагностики и контакты поддержки, читатель не удерживает целиком.
Разбивка на 3 подписанных чанка («Причины», «Диагностика», «Эскалация») по 4 факта каждый — тот же
объём информации, но каждый чанк отвечает на ОДИН имплицитный вопрос читателя. — *источник:* S10.

**ME-4 — Формальный abstract как самодостаточный носитель (ANSI Z39.14, T3).** Статья на 3000 слов
сжимается до abstract на 250 слов, обязательно содержащего: назначение исследования, метод, ключевой
результат, вывод — НИ ОДНОГО нового утверждения сверх статьи, но и ни одного из этих четырёх элементов
не пропущено. Читатель abstract'а не должен открывать статью, чтобы понять, ЧТО было сделано и найдено
(хотя КАК — уже требует перехода к тексту). — *источник:* S14.

**ME-5 — Naive vs faithful compression (LLMLingua-1 vs -2, AI-slice).** Perplexity-based прунинг может
выбросить токен «not» в фразе «the service is not affected», потому что «not» статистически
низко-неожиданный (частое слово) — при этом его удаление МЕНЯЕТ смысл фразы на противоположный.
LLMLingua-2 переформулировал задачу как классификацию «сохранить/выбросить» с обучением на
faithfulness-размеченных данных именно чтобы поймать такие смыслонесущие, но статистически «скучные»
токены. — *источник:* S19, S20.

---

## Operator/Object inventory (стабы терминов для glossary/паттернов)

> Кандидаты в `glossary.md` (RU/EN/определение/«не является») и в имена паттернов DPF.md (Фаза 4, F.18).
> Не определения-в-камне — стабы.

**Единицы провенанса (Digital Curation, T1):**
- **Provenance Information** — накопительная история происхождения и ВСЕХ трансформаций объекта.
  *Не является:* снапшотом текущего состояния (это отдельный вид метаданных).
- **Curation Lifecycle Action** — действие над объектом, классифицируемое как постоянное (full-lifecycle),
  последовательное (sequential) или эпизодическое (occasional). *Не является:* разовым событием создания.

**Единицы переиспользуемого носителя (Structured Authoring, T2):**
- **Topic** — дискретная, типизированная, самодостаточная единица информации с ОДНИМ намерением
  (concept/task/reference). *Не является:* произвольным разделом длинного документа.
- **Reuse-by-reference (single-sourcing)** — контент определён один раз, подключается ссылкой в разных
  местах. *Не является:* копированием текста в несколько файлов («похоже, но расходится молча»).
- **Chunking** — дробление информации на компактные тематически цельные блоки под объём внимания
  читателя. *Не является:* произвольной нарезкой по длине абзаца.

**Единицы формального сжатия (Editorial Compression, T3):**
- **Faithful compression** — сокращение, сохраняющее точность (accuracy) как обязательный критерий,
  не только краткость. *Не является:* любым укорачиванием текста.
- **Self-contained abstract** — сжатый носитель, понятный БЕЗ обращения к оригиналу для того, «что было
  сделано», но не для «как именно». *Не является:* тизером/затравкой, требующей перехода к полному
  тексту для базового понимания.

**Единицы governance разделяемых данных (Reference-Data Governance, T4):**
- **Golden Record** — согласованное представление, полученное примирением НЕСКОЛЬКИХ источников.
  *Не является:* выбором одной системы как «главной» без согласования.
- **Single Source of Truth (SSoT)** — организационный исход (все потребители реально полагаются на один
  канон), не свойство отдельного файла. *Не является:* автоматически истинным просто потому, что файл
  называется «канон».
- **Steward / Governance Team** — постоянная роль, ответственная за поддержание согласованности эталона
  во времени. *Не является:* разовым автором на момент создания.

**Единицы ИИ-эры (AI-slice):**
- **Faithfulness (compression/summarization)** — сжатый/пересказанный текст не добавляет и не теряет
  смыслонесущих утверждений источника; отдельная, явно оптимизируемая цель, а не побочный эффект
  краткости. *Не является:* синонимом «низкой perplexity» или «похоже на оригинал по стилю».
  [S20]
- **Attribution Verification** — явная, отдельно проверяемая связь claim→источник в генерируемом
  тексте. *Не является:* наличием синтаксической ссылки/цитаты самой по себе (ссылка может быть
  неверной). [S25, S26]
- **Documentation Drift** — расхождение между каноном и его копией/зеркалом из-за отсутствия
  автоматического детектирования расхождения, а НЕ из-за недостатка дисциплины авторов. [S27]

**Школы/традиции SoTA:** архивно-библиотечная наука OAIS/DCC curation lifecycle (T1) · structured/
topic-based technical authoring DITA/Information Mapping/минимализм (T2) · editorial compression
discipline copyediting/ANSI Z39.14 abstracting (T3) · governance разделяемых эталонных данных MDM golden
record/taxonomy stewardship (T4) · AI-курирование: faithful prompt compression/summarization
hallucination benchmarks/RAG citation verification/documentation drift (AI-slice).
