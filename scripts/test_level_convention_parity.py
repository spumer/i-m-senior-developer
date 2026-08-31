#!/usr/bin/env python3
"""Страж одинакового поведения двух намеренно независимых конвенций уровней.

Запуск из корня репозитория::

    python3 scripts/test_level_convention_parity.py

Для проверки подготовленной копии дерева::

    python3 scripts/test_level_convention_parity.py --root /путь/к/копии
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
RESOLVE_RELATIVE_PATH = Path("plugins/fpf-integration/skills/dpf-apply/scripts/resolve.py")
HINT_RELATIVE_PATH = Path("plugins/fpf-integration/hooks/prompt_competency_hint.py")


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"не удалось загрузить {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_level_builders(root: Path) -> tuple[ModuleType, ModuleType]:
    resolve_path = root / RESOLVE_RELATIVE_PATH
    hint_path = root / HINT_RELATIVE_PATH
    for path in (resolve_path, hint_path):
        if not path.is_file():
            raise FileNotFoundError(f"не найден исходный файл: {path}")
    return (
        load_module(resolve_path, "resolve_level_convention"),
        load_module(hint_path, "hint_level_convention"),
    )


def levels_from(module: ModuleType, home: Path, project: Path) -> list[tuple[str, str]]:
    with mock.patch.dict(os.environ, {"HOME": str(home)}):
        with mock.patch.object(os, "getcwd", return_value=str(project)):
            return module.build_levels()


def assert_levels(label: str, actual: list[tuple[str, str]], expected: list[tuple[str, str]]) -> None:
    if actual != expected:
        raise AssertionError(
            f"{label} вернул не ту последовательность уровней\n"
            f"ожидалось: {expected}\n"
            f"получено: {actual}"
        )


def assert_same_levels(
    resolve_module: ModuleType,
    hint_module: ModuleType,
    home: Path,
    project: Path,
    expected: list[tuple[str, str]],
) -> None:
    resolve_levels = levels_from(resolve_module, home, project)
    hint_levels = levels_from(hint_module, home, project)
    assert_levels("resolve.py.build_levels()", resolve_levels, expected)
    assert_levels("prompt_competency_hint.py.build_levels()", hint_levels, expected)
    if resolve_levels != hint_levels:
        raise AssertionError(
            "копии конвенции вернули разные последовательности уровней\n"
            f"resolve.py: {resolve_levels}\n"
            f"prompt_competency_hint.py: {hint_levels}"
        )


def assert_full_source_convention(resolve_module: ModuleType, hint_module: ModuleType) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        home = temporary_root / "home"
        project = temporary_root / "project"
        claude_dir = home / ".claude"
        project_root = project / ".claude" / "frameworks"
        user_root = claude_dir / "frameworks"
        paths_root = temporary_root / "paths-frameworks"
        published_root = temporary_root / "published-frameworks"
        paths_alias = temporary_root / "paths-alias"

        for directory in (project_root, user_root, paths_root, published_root):
            directory.mkdir(parents=True)
        paths_alias.symlink_to(paths_root, target_is_directory=True)
        (claude_dir / "frameworks.paths").write_text(
            f"# локальный источник плагина\n\n{paths_root}\n", encoding="utf-8"
        )
        (claude_dir / "frameworks.published").write_text(
            f"# опубликованные источники\n{published_root}\n{paths_alias}\n", encoding="utf-8"
        )

        assert_same_levels(
            resolve_module,
            hint_module,
            home,
            project,
            [
                ("project", str(project_root)),
                ("user", str(user_root)),
                ("plugin", str(paths_root)),
                ("plugin", str(published_root)),
            ],
        )


def assert_missing_published_convention(resolve_module: ModuleType, hint_module: ModuleType) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        home = temporary_root / "home"
        project = temporary_root / "project"
        claude_dir = home / ".claude"
        project_root = project / ".claude" / "frameworks"
        user_root = claude_dir / "frameworks"
        paths_root = temporary_root / "paths-frameworks"

        for directory in (project_root, user_root, paths_root):
            directory.mkdir(parents=True)
        (claude_dir / "frameworks.paths").write_text(f"{paths_root}\n", encoding="utf-8")

        assert_same_levels(
            resolve_module,
            hint_module,
            home,
            project,
            [
                ("project", str(project_root)),
                ("user", str(user_root)),
                ("plugin", str(paths_root)),
            ],
        )


def assert_level_convention_parity(root: Path = REPOSITORY_ROOT) -> None:
    resolve_module, hint_module = load_level_builders(root)
    assert_full_source_convention(resolve_module, hint_module)
    assert_missing_published_convention(resolve_module, hint_module)


def test__level_conventions__same_source_files__same_levels() -> None:
    assert_level_convention_parity()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=REPOSITORY_ROOT,
        help="корень репозитория или подготовленной копии",
    )
    args = parser.parse_args(argv)
    try:
        assert_level_convention_parity(args.root)
    except (AssertionError, OSError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print("PASS: конвенции уровней совпадают")
    return 0


if __name__ == "__main__":
    sys.exit(main())
