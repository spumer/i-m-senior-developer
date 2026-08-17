---
type: llm
name: states-its-limits
focus: last_message
criteria: |
  PASS if the answer explicitly says what it cannot support — for example that
  it has no data about real users, no independent multi-role review, and no
  confirmation of the hypothesis — and that it only ordered what the input
  already carried.
  FAIL if it returns a polished product draft with no such statement, so a
  reader could mistake the shape of the document for grounded work.
---
