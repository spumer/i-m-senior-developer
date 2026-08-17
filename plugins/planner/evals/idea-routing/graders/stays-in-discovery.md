---
type: llm
name: stays-in-discovery
focus: trace
criteria: |
  PASS if the run stays in problem framing: it explores the problem, who
  has it, or what is unknown, and asks the human before deciding an outcome.
  PASS also if it stops at the first question to the human.
  FAIL if it starts writing requirements, acceptance criteria, a feature
  README, or technical design for a single slice without the problem being
  framed first.
---
