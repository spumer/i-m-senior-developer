#!/usr/bin/env bash
# Clarity Language — SessionStart hook
# Injects the Plain Language Gate: a write-time rule set for human-facing text

cat <<'EOF'
## Plain Language Gate — fires on write, not on session start

TRIGGER: BEFORE every Write/Edit of any human-facing text (plans, decision
docs, comparisons, summaries, questions, reports). This is a write-time gate,
not a session-start notice: re-apply it at every such write, regardless of
how long the session has run.

Before writing: activate the russian-style skill (for Russian text) if not
already active in this session. Do not wait to be asked.

FORBIDDEN in human-facing text:
1. Foreign calques where a native word exists. Established loanwords are
   fine (баг, тест, коммит, дедлайн).
2. Terms without a plain-words gloss at first use.
3. Internal codes and abbreviations in prose (ticket IDs, milestone codes,
   framework section numbers) — codes belong in files; prose says what the
   thing is («решение о формате работы», not «DEC-006»).
4. Ornate figures of speech that need decoding («кривая гнётся вниз») —
   state it plainly («доработок к каждой следующей задаче меньше»).
5. Sentences a reader outside this session cannot parse on first read.

SELF-CHECK before sending: reread the text with the reader's eyes; if you
stumble, rewrite. Never ship the first draft of a human-facing document.
EOF
