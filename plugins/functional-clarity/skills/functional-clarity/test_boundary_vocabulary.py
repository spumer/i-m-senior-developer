from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]

REQUIRED_MARKERS = {
    Path(
        "plugins/functional-clarity/skills/functional-clarity/"
        "references/06-boundary-vocabulary.md"
    ): (
        "**Всё, что контекст объявляет на своей границе",
        "## Три канала утечки",
        "## Тест подстановки",
        "## Границы применения",
    ),
    Path("plugins/functional-clarity/skills/functional-clarity/SKILL.md"): (
        "`references/06-boundary-vocabulary.md`",
        "IF designing, implementing, or reviewing elements declared on a context boundary",
    ),
    Path(
        "plugins/functional-clarity/skills/functional-clarity/"
        "references/00-principles.md"
    ): ("тест подстановки", "`references/06-boundary-vocabulary.md`"),
    Path("plugins/sdlc/skills/architect/SKILL.md"): (
        "| Caller | Callee | Input shape | Output shape | Error mode | Vocabulary |",
        "**Substitution test**",
        "`references/06-boundary-vocabulary.md`",
    ),
    Path("plugins/sdlc/skills/architect/references/design-conventions.md"): (
        "**Vocabulary leak across the boundary.**",
        "substitution test",
    ),
    Path("plugins/sdlc/skills/code-implementer/SKILL.md"): (
        "## Boundary vocabulary — the owner's words",
        "substitution test",
        "`references/06-boundary-vocabulary.md`",
    ),
    Path("plugins/sdlc/skills/code-reviewer/SKILL.md"): (
        "**Vocabulary leak across a context boundary**",
        "Severity: major",
        "`references/06-boundary-vocabulary.md`",
    ),
    Path("plugins/sdlc/skills/code-reviewer/references/review-conventions.md"): (
        "vocabulary leak across a context boundary",
        "failed substitution test",
    ),
}


def find_missing_markers(
    root: Path, requirements: dict[Path, tuple[str, ...]]
) -> list[str]:
    missing: list[str] = []
    for relative_path, markers in requirements.items():
        path = root / relative_path
        if not path.is_file():
            missing.append(f"{relative_path}: file is missing")
            continue

        text = path.read_text(encoding="utf-8")
        missing.extend(
            f"{relative_path}: {marker!r}"
            for marker in markers
            if marker not in text
        )
    return missing


class BoundaryVocabularyIntegrationTest(unittest.TestCase):
    def test__boundary_vocabulary__repository_wiring__is_complete(self) -> None:
        self.assertEqual(find_missing_markers(REPOSITORY_ROOT, REQUIRED_MARKERS), [])

    def test__boundary_vocabulary__missing_marker__is_reported(self) -> None:
        requirements = {Path("rule.md"): ("substitution test",)}
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "rule.md").write_text("ownership rule", encoding="utf-8")

            self.assertEqual(
                find_missing_markers(root, requirements),
                ["rule.md: 'substitution test'"],
            )


if __name__ == "__main__":
    unittest.main()
