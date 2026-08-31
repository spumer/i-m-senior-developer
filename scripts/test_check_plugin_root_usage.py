"""Проверки стража способа получения корня плагина.

Контракт CLI: только подстановка ``${CLAUDE_PLUGIN_ROOT}`` допустима в
командах, скиллах и агентах; отказ называет путь и переменную. Корень должен
содержать каталог plugins. Хуки исключены, потому что получают переменную
окружения от среды выполнения. Документация вне каталогов компонентов не
сканируется: модель не исполняет её как инструкцию.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("check_plugin_root_usage.py")


def run_guard(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
    )


def write_file(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class PluginRootUsageGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        self.root = Path(self._temporary_directory.name)

    def test__root_without_plugins__exits_64_and_names_missing_directory(self) -> None:
        result = run_guard(self.root)

        self.assertEqual(result.returncode, 64)
        self.assertEqual(result.stdout, "")
        self.assertIn("нет каталога", result.stderr)
        self.assertIn(str(self.root / "plugins"), result.stderr)

    def test__substitution_in_command__exits_0_without_output(self) -> None:
        write_file(
            self.root,
            "plugins/planner/commands/plan.md",
            'python3 "${CLAUDE_PLUGIN_ROOT}/assets/helper.py"\n',
        )

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test__plain_name_in_command__exits_1_and_names_violation(self) -> None:
        write_file(
            self.root,
            "plugins/planner/commands/plan.md",
            "Получи путь через CLAUDE_PLUGIN_ROOT во время работы.\n",
        )

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("plugins/planner/commands/plan.md:1", result.stderr)
        self.assertIn("CLAUDE_PLUGIN_ROOT", result.stderr)

    def test__plain_name_in_skill__exits_1_and_names_violation(self) -> None:
        write_file(
            self.root,
            "plugins/planner/skills/planner/SKILL.md",
            "Получи путь через CLAUDE_PLUGIN_ROOT во время работы.\n",
        )

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("plugins/planner/skills/planner/SKILL.md:1", result.stderr)
        self.assertIn("CLAUDE_PLUGIN_ROOT", result.stderr)

    def test__plain_name_in_agent__exits_1_and_names_violation(self) -> None:
        write_file(
            self.root,
            "plugins/planner/agents/planner.md",
            "Получи путь через CLAUDE_PLUGIN_ROOT во время работы.\n",
        )

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("plugins/planner/agents/planner.md:1", result.stderr)
        self.assertIn("CLAUDE_PLUGIN_ROOT", result.stderr)

    def test__environment_lookup_in_hook__exits_0_without_output(self) -> None:
        write_file(
            self.root,
            "plugins/planner/hooks/session.py",
            'root = os.environ.get("CLAUDE_PLUGIN_ROOT")\n',
        )

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test__plain_name_in_nested_hooks_inside_skill__exits_1(self) -> None:
        write_file(
            self.root,
            "plugins/planner/skills/hooks/reference.md",
            "Получи путь через CLAUDE_PLUGIN_ROOT во время работы.\n",
        )

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("plugins/planner/skills/hooks/reference.md:1", result.stderr)

    def test__plain_name_outside_component__exits_0_silently(self) -> None:
        """Справка вне компонента не исполняется моделью как инструкция."""
        write_file(
            self.root,
            "plugins/planner/frameworks/reference.md",
            "Путь описывает CLAUDE_PLUGIN_ROOT как шаблонный параметр.\n",
        )

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test__plain_name_in_noncomponent_directory_named_skills__exits_0(
        self,
    ) -> None:
        write_file(
            self.root,
            "plugins/planner/frameworks/skills/reference.md",
            "Путь описывает CLAUDE_PLUGIN_ROOT как шаблонный параметр.\n",
        )

        result = run_guard(self.root)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
