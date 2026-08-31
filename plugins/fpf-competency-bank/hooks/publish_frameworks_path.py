#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


def main() -> int:
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if not plugin_root:
        print("Cannot publish frameworks path: CLAUDE_PLUGIN_ROOT is empty.", file=sys.stderr)
        return 0

    published_file = Path.home() / ".claude" / "frameworks.published"
    temporary_path: str | None = None

    try:
        published_file.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=published_file.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            temporary_file.write(f"{Path(plugin_root) / 'frameworks'}\n")
        os.replace(temporary_path, str(published_file))
    except OSError as error:
        print(f"Cannot publish frameworks path: {error}", file=sys.stderr)
    finally:
        if temporary_path:
            try:
                Path(temporary_path).unlink(missing_ok=True)
            except OSError:
                pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
