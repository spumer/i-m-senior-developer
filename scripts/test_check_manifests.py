"""Тесты стража манифестов: запрет верхнеуровневого ключа hooks и
совпадение описания плагина с его карточкой в маркетплейсе.

Скрипт вызывается подпроцессом на временном корне — проверяются код
возврата и вывод, то есть наблюдаемый контракт CLI.
"""

import json
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


def make_marketplace(tmp, cards):
    """Собирает .claude-plugin/marketplace.json из словаря имя→описание."""
    marketplace_dir = Path(tmp) / ".claude-plugin"
    marketplace_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": "test-marketplace",
        "plugins": [
            {"name": name, "description": description, "source": f"./plugins/{name}"}
            for name, description in cards.items()
        ],
    }
    (marketplace_dir / "marketplace.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


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

    def test__nested_hooks_before_top_level_hooks__reports_top_level_line(self):
        text = (
            "{\n"
            '  "name": "alpha",\n'
            '  "commands": {\n'
            '    "hooks": "allowed"\n'
            "  },\n"
            '  "hooks": {}\n'
            "}\n"
        )
        make_root(self.root, {"alpha": text})
        result = run_guard(self.root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("строка 6", result.stdout)


class MarketplaceMirrorTests(unittest.TestCase):
    """Описание плагина и его карточка в маркетплейсе не расходятся."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test__same_description__exit_0_silent(self):
        make_root(self.root, {"alpha": '{"name": "alpha", "description": "Помогает A."}'})
        make_marketplace(self.root, {"alpha": "Помогает A."})
        result = run_guard(self.root)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout, "")

    def test__different_description__exit_1_names_plugin_and_both_files(self):
        make_root(self.root, {"alpha": '{"name": "alpha", "description": "Помогает A."}'})
        make_marketplace(self.root, {"alpha": "Does A."})
        result = run_guard(self.root)
        self.assertEqual(result.returncode, 1)
        out = result.stdout
        self.assertIn("alpha", out)
        self.assertIn(".claude-plugin/marketplace.json", out)
        self.assertIn("plugins/alpha/.claude-plugin/plugin.json", out)

    def test__several_plugins__reports_only_the_diverged_one(self):
        make_root(
            self.root,
            {
                "alpha": '{"name": "alpha", "description": "Помогает A."}',
                "beta": '{"name": "beta", "description": "Помогает B."}',
            },
        )
        make_marketplace(self.root, {"alpha": "Помогает A.", "beta": "Помогает иначе."})
        result = run_guard(self.root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("beta", result.stdout)
        self.assertNotIn("alpha", result.stdout)

    def test__plugin_without_card__exit_0(self):
        # Наличие карточки — предмет другой проверки; здесь сверяется только
        # совпадение описаний у тех плагинов, что есть в обоих файлах.
        make_root(self.root, {"alpha": '{"name": "alpha", "description": "Помогает A."}'})
        make_marketplace(self.root, {})
        result = run_guard(self.root)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test__no_marketplace_file__exit_0(self):
        make_root(self.root, {"alpha": '{"name": "alpha", "description": "Помогает A."}'})
        result = run_guard(self.root)
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
