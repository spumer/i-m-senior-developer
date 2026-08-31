---
name: product-baseline
model: sonnet
tools: ["Read", "Grep", "Glob"]
description: |
  Use this agent when the product-discovery workflow has routed a request to
  `planner:product-baseline` as its built-in fallback provider.

  <example>
  Context: Routing found no available external provider with the required product capabilities.
  user: "Подготовь продуктовую проработку для этой идеи."
  assistant: "Маршрутизация выбрала встроенного поставщика. Запускаю `planner:product-baseline` через Agent tool."
  <commentary>
  The product-discovery workflow selected this built-in provider after external
  candidates could not cover the request.
  </commentary>
  </example>

  <example>
  Context: An external provider was available but its response did not satisfy the calling workflow's contract.
  user: "Нужно продолжить продуктовую проработку без внешней команды."
  assistant: "Использую `planner:product-baseline` через Agent tool как выбранного встроенного поставщика."
  <commentary>
  This agent triggers only after routing selects it as the fallback provider.
  </commentary>
  </example>
---

# Product baseline — встроенный ограниченный поставщик

Read the `product-baseline` skill and follow it start-to-finish.
