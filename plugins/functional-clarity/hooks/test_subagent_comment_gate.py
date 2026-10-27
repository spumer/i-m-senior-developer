#!/usr/bin/env python3
"""Тесты `subagent_comment_gate.py` (SubagentStart-хук).

Запуск:
  python3 test_subagent_comment_gate.py
  python3 -m unittest test_subagent_comment_gate

stdlib only (unittest).
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import subagent_comment_gate as gate  # noqa: E402


def run_main(stdin_text: str, plugin_root) -> tuple[int, str]:
    env = {"CLAUDE_PLUGIN_ROOT": plugin_root} if plugin_root is not None else {}
    buf = io.StringIO()
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(stdin_text)
    try:
        with mock.patch.dict(os.environ, env, clear=False):
            if plugin_root is None:
                os.environ.pop("CLAUDE_PLUGIN_ROOT", None)
            with contextlib.redirect_stdout(buf):
                code = gate.main()
    finally:
        sys.stdin = old_stdin
    return code, buf.getvalue()


def make_plugin_root(gate_body: str | None) -> str:
    """Временный каталог плагина с (опционально) hooks/comment-gate.txt внутри."""
    root = tempfile.mkdtemp()
    hooks_dir = os.path.join(root, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    if gate_body is not None:
        with open(os.path.join(hooks_dir, "comment-gate.txt"), "w", encoding="utf-8") as handle:
            handle.write(gate_body)
    return root


class GateTextTests(unittest.TestCase):
    """Прямые проверки `gate_text` — без похода через main()/окружение."""

    def test_substitutes_placeholder_with_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "comment-gate.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("line one\n{{PLUGIN_ROOT}}/skills/comment-style/SKILL.md\n")
            text = gate.gate_text(path, "/plugins/functional-clarity")
        self.assertIn("/plugins/functional-clarity/skills/comment-style/SKILL.md", text)
        self.assertNotIn("{{PLUGIN_ROOT}}", text)

    def test_missing_file_returns_empty(self):
        self.assertEqual(gate.gate_text("/no/such/file.txt", "/root"), "")

    def test_empty_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "comment-gate.txt")
            with open(path, "w", encoding="utf-8"):
                pass
            self.assertEqual(gate.gate_text(path, "/root"), "")

    def test_empty_root_returns_empty_even_if_file_exists_and_nonempty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "comment-gate.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("some gate text {{PLUGIN_ROOT}}/x")
            self.assertEqual(gate.gate_text(path, ""), "")

    def test_undecodable_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "comment-gate.txt")
            with open(path, "wb") as handle:
                handle.write(b"gate text \xff\xfe {{PLUGIN_ROOT}}/x")
            self.assertEqual(gate.gate_text(path, "/root"), "")


class MainTests(unittest.TestCase):
    """Поведение целиком через main(): конверт на выходе и пути отказа."""

    def _plugin_root(self, gate_body):
        root = make_plugin_root(gate_body)
        self.addCleanup(shutil.rmtree, root, True)
        return root

    def test_71_valid_root_and_gate_file_produce_subagent_start_envelope(self):
        root = self._plugin_root("Rule text.\n{{PLUGIN_ROOT}}/skills/comment-style/SKILL.md\n")
        code, out = run_main("{}", root)
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(
            payload["hookSpecificOutput"]["hookEventName"], "SubagentStart"
        )
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn(f"{root}/skills/comment-style/SKILL.md", context)
        self.assertNotIn("{{PLUGIN_ROOT}}", context)

    def test__main__ascii_stdout__preserves_unicode_context(self):
        body = "Правило ❌/✅ — {{PLUGIN_ROOT}}/skills/comment-style/SKILL.md\n"
        root = self._plugin_root(body)
        result = subprocess.run(
            [sys.executable, gate.__file__],
            input="{}",
            capture_output=True,
            text=True,
            encoding="ascii",
            env={**os.environ, "CLAUDE_PLUGIN_ROOT": root, "PYTHONIOENCODING": "ascii:strict"},
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(payload["hookEventName"], "SubagentStart")
        self.assertEqual(payload["additionalContext"], body.replace("{{PLUGIN_ROOT}}", root))

    def test_72_missing_gate_file_is_silent(self):
        root = self._plugin_root(None)
        code, out = run_main("{}", root)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_73_empty_gate_file_is_silent(self):
        root = self._plugin_root("")
        code, out = run_main("{}", root)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_74_empty_plugin_root_is_silent(self):
        self._plugin_root("Rule text {{PLUGIN_ROOT}}/x")
        code, out = run_main("{}", None)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_undecodable_gate_file_is_silent(self):
        root = make_plugin_root(None)
        self.addCleanup(shutil.rmtree, root, True)
        with open(os.path.join(root, "hooks", "comment-gate.txt"), "wb") as handle:
            handle.write(b"Rule text \xff\xfe {{PLUGIN_ROOT}}/x")
        code, out = run_main("{}", root)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_75_malformed_stdin_json_behaves_like_success(self):
        root = self._plugin_root("Rule text.\n{{PLUGIN_ROOT}}/skills/comment-style/SKILL.md\n")
        code, out = run_main("{not json", root)
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(
            payload["hookSpecificOutput"]["hookEventName"], "SubagentStart"
        )


if __name__ == "__main__":
    unittest.main()
