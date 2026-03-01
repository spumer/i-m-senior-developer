#!/usr/bin/env bash
# llms-keeper — SessionStart hook
# Check if llms.txt exists and remind about project context

if [ -f "llms-full.txt" ]; then
  echo "## Project Context Available"
  echo ""
  echo "This project has \`llms-full.txt\` — read it for full project context."
  echo "Run \`/update-docs\` to sync documentation with current codebase state."
elif [ -f "llms.txt" ]; then
  echo "## Project Context Available"
  echo ""
  echo "This project has \`llms.txt\` — read it for project overview."
  echo "Run \`/update-docs\` to generate full documentation."
else
  echo "## No Project Context"
  echo ""
  echo "No \`llms.txt\` found. Run \`/update-docs\` to generate AI-optimized project documentation."
fi
