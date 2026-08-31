#!/usr/bin/env python3
"""Контракт SessionStart-публикатора источника банка компетенций."""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HOOKS_DIR = Path(__file__).parent
sys.path.insert(0, str(HOOKS_DIR))

import publish_frameworks_path as publisher  # noqa: E402


class PublishFrameworksPathTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name) / "home"
        self.plugin_root = Path(self._tmp.name) / "plugin"
        self.home.mkdir()
        (self.plugin_root / "frameworks").mkdir(parents=True)

    def test__session_start_hook__runs_publisher_command(self):
        payload = json.loads((HOOKS_DIR / "hooks.json").read_text(encoding="utf-8"))

        command = payload["hooks"]["SessionStart"][0]["hooks"][0]["command"]

        self.assertEqual(
            command,
            "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/publish_frameworks_path.py",
        )

    def test__publisher__replaces_published_file_without_changing_human_paths(self):
        claude_dir = self.home / ".claude"
        claude_dir.mkdir()
        paths_file = claude_dir / "frameworks.paths"
        paths_file.write_text("/human/frameworks\n", encoding="utf-8")
        published_file = claude_dir / "frameworks.published"
        published_file.write_text("/old/plugin/frameworks\n", encoding="utf-8")

        with mock.patch.dict(
            os.environ,
            {"HOME": str(self.home), "CLAUDE_PLUGIN_ROOT": str(self.plugin_root)},
        ):
            with mock.patch.object(publisher.os, "replace", wraps=os.replace) as replace:
                code = publisher.main()

        self.assertEqual(code, 0)
        self.assertEqual(
            published_file.read_text(encoding="utf-8"),
            f"{self.plugin_root / 'frameworks'}\n",
        )
        self.assertEqual(paths_file.read_text(encoding="utf-8"), "/human/frameworks\n")
        replace.assert_called_once()
        temporary_path, destination = replace.call_args.args
        self.assertEqual(destination, str(published_file))
        self.assertEqual(Path(temporary_path).parent, published_file.parent)

    def test__empty_plugin_root__reports_reason_without_failing_session_start(self):
        published_file = self.home / ".claude" / "frameworks.published"
        published_file.parent.mkdir()
        published_file.write_text("/old/plugin/frameworks\n", encoding="utf-8")
        stderr = io.StringIO()

        with mock.patch.dict(os.environ, {"HOME": str(self.home), "CLAUDE_PLUGIN_ROOT": ""}):
            with mock.patch.object(sys, "stderr", stderr):
                code = publisher.main()

        self.assertEqual(code, 0)
        self.assertIn("CLAUDE_PLUGIN_ROOT", stderr.getvalue())
        self.assertEqual(published_file.read_text(encoding="utf-8"), "/old/plugin/frameworks\n")

    def test__write_error__reports_reason_without_failing_session_start(self):
        published_file = self.home / ".claude" / "frameworks.published"
        published_file.parent.mkdir()
        published_file.write_text("/old/plugin/frameworks\n", encoding="utf-8")

        with mock.patch.dict(
            os.environ,
            {"HOME": str(self.home), "CLAUDE_PLUGIN_ROOT": str(self.plugin_root)},
        ):
            with mock.patch.object(publisher.os, "replace", side_effect=OSError("denied")):
                stderr = io.StringIO()
                with mock.patch.object(sys, "stderr", stderr):
                    code = publisher.main()

        self.assertEqual(code, 0)
        self.assertIn("denied", stderr.getvalue())
        self.assertEqual(published_file.read_text(encoding="utf-8"), "/old/plugin/frameworks\n")


if __name__ == "__main__":
    unittest.main()
