"""Тесты стража манифестов: запрет верхнеуровневого ключа hooks.

Скрипт вызывается подпроцессом на временном корне — проверяются код
возврата и вывод, то есть наблюдаемый контракт CLI.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("check_manifests.py")


def run_guard(root):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
    )


def make_root(tmp, manifests):
    """Собирает дерево plugins/*/.claude-plugin/plugin.json из словаря имя→текст."""
    for name, text in manifests.items():
        manifest_dir = Path(tmp) / "plugins" / name / ".claude-plugin"
        manifest_dir.mkdir(parents=True)
        (manifest_dir / "plugin.json").write_text(text, encoding="utf-8")


class ManifestGuardTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test__valid_manifest__exit_0_silent(self):
        make_root(self.root, {"alpha": '{"name": "alpha", "version": "0.1.0"}'})
        result = run_guard(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test__top_level_hooks__exit_1_names_path_key_line(self):
        text = '{\n  "name": "alpha",\n  "hooks": {}\n}\n'
        make_root(self.root, {"alpha": text})
        result = run_guard(self.root)
        self.assertEqual(result.returncode, 1)
        out = result.stdout
        self.assertIn("plugins/alpha/.claude-plugin/plugin.json", out)
        self.assertIn("hooks", out)
        self.assertIn("строка 3", out)

    def test__invalid_json__exit_1_names_path_and_parse_error(self):
        make_root(self.root, {"alpha": '{"name": "alpha",,}'})
        result = run_guard(self.root)
        self.assertEqual(result.returncode, 1)
        out = result.stdout
        self.assertIn("plugins/alpha/.claude-plugin/plugin.json", out)
        self.assertIn("Expecting", out)

    def test__several_manifests__reports_only_the_defective_one(self):
        good = '{"name": "good", "version": "0.1.0"}'
        bad = '{\n  "name": "bad",\n  "hooks": []\n}\n'
        make_root(self.root, {"alpha": good, "beta": bad, "gamma": good})
        result = run_guard(self.root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("plugins/beta/.claude-plugin/plugin.json", result.stdout)
        self.assertNotIn("plugins/alpha", result.stdout)
        self.assertNotIn("plugins/gamma", result.stdout)

    def test__nested_hooks_allowed__exit_0(self):
        # Ключ hooks внутри чужой структуры — не запрет; запрещён только
        # верхний уровень манифеста.
        text = '{"name": "alpha", "strict": false, "commands": {"hooks": "no"}}'
        make_root(self.root, {"alpha": text})
        result = run_guard(self.root)
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
