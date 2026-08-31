import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
DIALOGUE_PATH = PLUGIN_ROOT / "skills/product-discovery/references/dialogue.md"
RULE_HEADING = "### Запреты"
RULE_COUNT = 7


class RuleOwnershipError(ValueError):
    pass


def normalized_text(text: str) -> str:
    return " ".join(text.split())


def file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_plugin_root(directory: str) -> Path:
    copied_root = Path(directory) / "planner"
    shutil.copytree(PLUGIN_ROOT, copied_root)
    return copied_root


def prohibited_phrasings(dialogue_path: Path) -> tuple[str, ...]:
    lines = dialogue_path.read_text(encoding="utf-8").splitlines()
    try:
        section_start = lines.index(RULE_HEADING) + 1
    except ValueError as error:
        raise RuleOwnershipError(
            f"диалоговый справочник не содержит раздел {RULE_HEADING!r}"
        ) from error

    phrasings: list[str] = []
    for line in lines[section_start:]:
        if line.startswith("### "):
            break
        if line.startswith("- "):
            phrasings.append(normalized_text(line.removeprefix("- ")))

    if len(phrasings) != RULE_COUNT:
        raise RuleOwnershipError(
            f"раздел {RULE_HEADING!r} должен содержать {RULE_COUNT} пунктов"
        )
    return tuple(phrasings)


def assert_rule_has_one_owner(plugin_root: Path) -> None:
    dialogue_path = plugin_root / DIALOGUE_PATH.relative_to(PLUGIN_ROOT)
    phrasings = prohibited_phrasings(dialogue_path)
    owner = dialogue_path.resolve()

    for candidate in plugin_root.rglob("*.md"):
        if candidate.resolve() == owner:
            continue
        content = normalized_text(candidate.read_text(encoding="utf-8"))
        for phrasing in phrasings:
            if phrasing in content:
                relative_path = candidate.relative_to(plugin_root)
                raise RuleOwnershipError(
                    f"{relative_path} повторяет запрет из {dialogue_path.name}"
                )


class DialogueRuleOwnershipTest(unittest.TestCase):
    def test__rule_ownership__canonical_plugin__has_no_copy(self) -> None:
        assert_rule_has_one_owner(PLUGIN_ROOT)

    def test__rule_ownership__copied_rule_in_command__raises(self) -> None:
        source_checksum = file_checksum(DIALOGUE_PATH)

        with tempfile.TemporaryDirectory() as directory:
            copied_root = copy_plugin_root(directory)
            copied_dialogue = copied_root / DIALOGUE_PATH.relative_to(PLUGIN_ROOT)
            copied_command = copied_root / "commands/plan-feat.md"
            copied_command.write_text(
                copied_command.read_text(encoding="utf-8")
                + "\n\n"
                + prohibited_phrasings(copied_dialogue)[0]
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuleOwnershipError, "commands/plan-feat.md"):
                assert_rule_has_one_owner(copied_root)

        self.assertEqual(file_checksum(DIALOGUE_PATH), source_checksum)

    def test__rule_ownership__six_rules__raises(self) -> None:
        source_checksum = file_checksum(DIALOGUE_PATH)

        with tempfile.TemporaryDirectory() as directory:
            copied_root = copy_plugin_root(directory)
            copied_dialogue = copied_root / DIALOGUE_PATH.relative_to(PLUGIN_ROOT)
            last_rule = prohibited_phrasings(copied_dialogue)[-1]
            copied_dialogue.write_text(
                copied_dialogue.read_text(encoding="utf-8").replace(
                    f"- {last_rule}\n", "", 1
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuleOwnershipError, "должен содержать 7 пунктов"):
                assert_rule_has_one_owner(copied_root)

        self.assertEqual(file_checksum(DIALOGUE_PATH), source_checksum)

    def test__rule_ownership__eight_rules__raises(self) -> None:
        source_checksum = file_checksum(DIALOGUE_PATH)

        with tempfile.TemporaryDirectory() as directory:
            copied_root = copy_plugin_root(directory)
            copied_dialogue = copied_root / DIALOGUE_PATH.relative_to(PLUGIN_ROOT)
            copied_dialogue.write_text(
                copied_dialogue.read_text(encoding="utf-8").replace(
                    "\n\nВклад человека",
                    "\n- проверочный восьмой запрет.\n\nВклад человека",
                    1,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuleOwnershipError, "должен содержать 7 пунктов"):
                assert_rule_has_one_owner(copied_root)

        self.assertEqual(file_checksum(DIALOGUE_PATH), source_checksum)

    def test__rule_ownership__edited_canonical_rule__has_no_copy(self) -> None:
        source_checksum = file_checksum(DIALOGUE_PATH)

        with tempfile.TemporaryDirectory() as directory:
            copied_root = copy_plugin_root(directory)
            copied_dialogue = copied_root / DIALOGUE_PATH.relative_to(PLUGIN_ROOT)
            original_rule = prohibited_phrasings(copied_dialogue)[0]
            edited_rule = f"{original_rule} Дополнительное уточнение."
            copied_dialogue.write_text(
                copied_dialogue.read_text(encoding="utf-8").replace(
                    f"- {original_rule}\n", f"- {edited_rule}\n", 1
                ),
                encoding="utf-8",
            )

            assert_rule_has_one_owner(copied_root)

            copied_command = copied_root / "commands/plan-feat.md"
            copied_command.write_text(
                copied_command.read_text(encoding="utf-8")
                + "\n\n"
                + edited_rule
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuleOwnershipError, "commands/plan-feat.md"):
                assert_rule_has_one_owner(copied_root)

        self.assertEqual(file_checksum(DIALOGUE_PATH), source_checksum)


if __name__ == "__main__":
    unittest.main()
