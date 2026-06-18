#!/usr/bin/env bash
# Clarity Language — SessionStart hook
# Brief reminder of text & evidence discipline for every session

cat <<'EOF'
## Clarity Language Active

When writing or editing prose, documentation, scripts, or user-facing text, keep it
clear and free of AI-synthetic patterns. Evidence over assertion.

Evidence discipline (FPF A.10 — "a claim without proof is only an opinion"):
- No invented flows: "the bot assigns a reviewer", "the system notifies X" — verify the
  process exists with the owner or the docs before writing it as fact.
- No authority-by-number: "cuts load by 80%", "15-20 hours" without a source. Drop it or
  replace with measurable components.
- No references to things that don't exist: verify file/anchor/role links (Glob/Grep)
  before citing them.

Natural language (skill `russian-style`):
- No calques or unnatural foreign intrusions; prefer verbs over nominalizations.
- BUT keep established loanwords ("фидбек", "баг", "коммит", "дедлайн") — don't "fix" them.
- Uncertain whether a foreign word is established or a calque? ASK the human, don't decide
  alone. Record the verdict to memory (loanword lexicon) so you don't ask twice.
- No empty antitheses ("это не X, а Y" that carries no new fact); give the concrete action.
- Plain language for engineers: instruction, not persuasion. No hedging, no "обсыпание".

Skills available — activate proactively, don't wait to be told:
- `clarity-validator` — 12 meaning-level AI antipatterns in technical docs (run it BEFORE
  declaring docs "done", not after a reminder).
- `ai-prose-detector` — fiction prose style (distance, metaphors, physiology, rhythm).
- `russian-style` — natural Russian authoring rules.

Do NOT ship synthetic text: leaked invariants, negation-of-nothing, design/run-time mixing,
duplicated conclusions across sections.
EOF
