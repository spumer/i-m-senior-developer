# llms.txt Specification

Source: https://llmstxt.org

## Purpose

A `/llms.txt` file provides a concise, structured overview of a project optimized for consumption by AI agents (LLMs). It serves as a navigation index — a starting point for AI to understand the project quickly.

A companion `/llms-full.txt` file provides the full content in a self-contained format, so the AI can answer questions without fetching other files.

## llms.txt Structure (Navigation Index)

Required format:

```markdown
# Project Name

> One-paragraph summary with key information for understanding the project

Optional: additional context paragraphs (tech stack, main purpose)

## Section Name
- [Link Title](url_or_path): Brief description of what's covered

## Another Section
- [Another Link](url_or_path): Description

## Optional
- [Extra Resource](url_or_path): Can be skipped if shorter context needed
```

### Rules

1. **H1** = Project name (REQUIRED, exactly one)
2. **Blockquote** = One-paragraph summary (REQUIRED, immediately after H1)
3. **H2 sections** with markdown link lists
4. Links follow format: `- [Name](url): Description`
5. **"Optional" section** — resources that can be skipped for shorter context
6. Use concise, clear language
7. Avoid ambiguous terms or unexplained jargon
8. NO code blocks in llms.txt (navigation only)
9. Important content FIRST (context window optimization)
10. Total length: 50-100 lines

## llms-full.txt Structure (Complete Content)

Required format:

```markdown
# Project Name

> One-paragraph summary with key information

Tech Stack: Language X.Y, Framework A.B, Database, key libraries

## Architecture
[Module hierarchy, dependency direction, data flow diagrams]

## Key Patterns
[Code examples with context comments]

## Module Responsibilities
[Ultra-compressed: Module: responsibility (location)]

## Common Pitfalls
[Problem → Solution with brief code]

## Development
[Essential commands, setup instructions]
```

### Rules

1. **H1** = Project name (REQUIRED)
2. **Blockquote** = Summary (REQUIRED)
3. Contains ACTUAL CONTENT, not links
4. **Self-contained** — AI can answer questions without fetching other files
5. Code blocks with context comments
6. Strict heading hierarchy: H1 → H2 → H3 (no skips)
7. Total length: 200-600 lines (depends on project size)

## Token Optimization for llms-full.txt

Apply compression to maximize information density:

### Ultra-Compressed Prose
- Remove articles: "the module" → "module"
- Shorten: "is responsible for" → "handles"
- Remove filler: "It's important to note that" → (delete)
- Keep key terms intact: `DatabaseSession`, `connection_pool`

### Format Optimization
- Use fenced code blocks (```), never inline code for patterns
- Metadata-first: location, purpose before description
- YAML over JSON in examples (fewer tokens)

## Quality Checklist

- [ ] H1 with project name
- [ ] Blockquote summary
- [ ] llms.txt: navigation links only, no code blocks
- [ ] llms-full.txt: self-contained, no external links needed
- [ ] Headings hierarchical (no skips)
- [ ] Code patterns in fenced blocks
- [ ] Concise language, no jargon without explanation
- [ ] Important sections first
