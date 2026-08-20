---
name: idea-routing
description: Сырой замысел попадает в продуктовую проработку, а не сразу в требования фичи.
tags: [routing, product-discovery]
runs: 3
max_turns: 6
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
plugins: ["../.."]
expected_outcome: >
  Модель активирует скилл product-discovery и остаётся в проработке замысла.
  Прямой переход к требованиям фичи не происходит.
---

Есть мысль: люди у нас теряют то, что сами же сохранили. Обсудим?
