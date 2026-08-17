---
type: llm
name: does-not-collapse-into-one-slice
focus: trace
criteria: |
  The input names three independent outcomes: a recycle bin, per-item change
  history, and notifications about other people's edits.

  PASS if the run treats them as more than one deliverable slice — for example
  it groups them under a shared hypothesis, proposes an order between them, or
  asks the human which one comes first.
  FAIL if it merges all three into requirements for a single feature, or
  silently picks one and starts writing its requirements without asking.
---
