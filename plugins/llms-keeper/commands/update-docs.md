---
name: update-docs
description: Generate or update llms.txt and llms-full.txt for the current project
argument-hint: "[focus area or 'full' for complete regeneration]"
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "Agent"]
---

Analyze the current project and generate or update `llms.txt` and `llms-full.txt` files in the project root, following the llmstxt.org standard.

Use the `documentation-keeper` agent to perform the analysis and generation.

If the user provides a focus area argument (e.g., "architecture", "patterns"), prioritize that area during analysis. If the argument is "full" or empty, perform complete analysis.

If `llms.txt` and `llms-full.txt` already exist, update them based on recent changes rather than regenerating from scratch.
