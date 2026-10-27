#!/usr/bin/env python3
"""SubagentStart hook: puts the comment write-gate into every subagent's context.

The gate text lives in a sibling data file, owned elsewhere; this hook only
reads it, substitutes the plugin root and forwards it through
`hookSpecificOutput.additionalContext`. No selector on agent type: any
marketplace's subagent should receive the same condition. Input is not
parsed at all — nothing in it is used.

Fail-open: any missing piece (root, file, content) means silence, exit 0.

Only stdlib.
"""

from __future__ import annotations

import json
import os
import sys

PLACEHOLDER = "{{PLUGIN_ROOT}}"


def gate_text(gate_path: str, plugin_root: str) -> str:
    """Gate text with `plugin_root` substituted in. Any problem -> ""."""
    if not plugin_root:
        return ""
    try:
        with open(gate_path, encoding="utf-8") as handle:
            raw = handle.read()
    except (OSError, UnicodeDecodeError):
        # A damaged file is silence, not garbled instructions: reading with
        # errors="replace" would forward mangled text into every subagent.
        return ""
    if not raw.strip():
        return ""
    return raw.replace(PLACEHOLDER, plugin_root)


def main() -> int:
    try:
        sys.stdin.read()
    except Exception:
        pass

    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    gate_path = os.path.join(plugin_root, "hooks", "comment-gate.txt") if plugin_root else ""
    text = gate_text(gate_path, plugin_root)
    if not text:
        return 0

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SubagentStart",
            "additionalContext": text,
        }
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
