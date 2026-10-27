import os
from pathlib import Path
import subprocess
import tempfile
import unittest


HOOK = Path(__file__).resolve().with_name("session-start.sh")


class SessionCommentGateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.plugin_root = Path(temporary.name) / "plugin root с пробелами"
        (self.plugin_root / "hooks").mkdir(parents=True)
        self.gate_path = self.plugin_root / "hooks/comment-gate.txt"

    def run_hook(self):
        return subprocess.run(
            ["bash", str(HOOK)],
            input=b"{}",
            capture_output=True,
            env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(self.plugin_root)},
            timeout=10,
        )

    def test__session_start__valid_utf8__substitutes_plugin_root(self):
        baseline = self.run_hook()
        body = "Правило ❌/✅ — {{PLUGIN_ROOT}}/skills/comment-style/SKILL.md\n"
        self.gate_path.write_text(body, encoding="utf-8")
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, b"")
        expected = body.replace("{{PLUGIN_ROOT}}", str(self.plugin_root)).encode("utf-8")
        self.assertEqual(result.stdout, baseline.stdout + expected)

    def test__session_start__missing_gate__preserves_principles(self):
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, b"")
        self.assertNotEqual(result.stdout.strip(), b"")

    def test__session_start__invalid_utf8__omits_the_entire_gate(self):
        baseline = self.run_hook()
        self.gate_path.write_bytes(b"valid prefix before damaged bytes: \xff\xfe\n")
        result = self.run_hook()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, b"")
        self.assertEqual(result.stdout, baseline.stdout)


if __name__ == "__main__":
    unittest.main()
