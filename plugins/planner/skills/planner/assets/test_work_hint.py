import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from work_hint import build_work_hint


INITIAL_TIME = "2024-01-01T00:00:00+0000"
PLAN_TIME_SECONDS = 1_704_067_230
LATER_TIME = "2024-01-01T00:01:00+0000"


class WorkHintTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.run_git("init")
        self.execution = self.root / "plans" / "PLANNER_EXECUTION.md"
        self.execution.parent.mkdir()
        self.execution.write_text("# Plan\n", encoding="utf-8")
        os.utime(self.execution, ns=(PLAN_TIME_SECONDS * 1_000_000_000,) * 2)
        self.create_output("outputs/result.txt", "initial\n")
        self.initial_commit = self.commit("initial output", INITIAL_TIME)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_git(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=check,
        )

    def create_output(self, relative_path: str, content: str) -> Path:
        target = self.root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def commit(self, message: str, timestamp: str) -> str:
        self.run_git("add", "--", ".")
        environment = os.environ | {
            "GIT_AUTHOR_DATE": timestamp,
            "GIT_COMMITTER_DATE": timestamp,
        }
        result = subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test User",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-m",
                message,
            ],
            cwd=self.root,
            env=environment,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.run_git("rev-parse", "HEAD").stdout.strip()

    def hint(self, outputs: list[str]) -> dict[str, object]:
        lines = ["## Phase", "", "- **Outputs:**"]
        lines.extend(f"  - `{output}`" for output in outputs)
        return build_work_hint(
            self.execution,
            "\n".join(lines) + "\n",
            PLAN_TIME_SECONDS * 1_000_000_000,
        )

    def assert_contract_fields(self, hint: dict[str, object]) -> None:
        self.assertTrue(
            {"status", "message", "complete", "paths", "rejected"}.issubset(hint),
            hint,
        )
        self.assertEqual(hint["plan_built_at_source"], "execution_file_mtime")
        self.assertTrue(str(hint["plan_built_at"]).endswith("Z"))
        self.assertIsInstance(hint["message"], str)
        self.assertIsInstance(hint["paths"], list)
        self.assertIsInstance(hint["rejected"], dict)

    def test__work_hint__commit_before_build__reports_unchanged(self) -> None:
        hint = self.hint(["outputs/result.txt"])

        self.assert_contract_fields(hint)
        self.assertEqual(hint["status"], "outputs_unchanged")
        self.assertTrue(hint["complete"])
        self.assertEqual(hint["rejected"], {"absolute_path": 0, "bare_path": 0, "outside_repository": 0, "placeholder": 0})
        self.assertEqual(
            hint["paths"],
            [
                {
                    "path": "outputs/result.txt",
                    "scope": "file",
                    "state": "unchanged",
                    "commit": self.initial_commit,
                    "committed_at": "2024-01-01T00:00:00Z",
                }
            ],
        )

    def test__work_hint__commit_after_build__reports_changed(self) -> None:
        self.create_output("outputs/result.txt", "changed\n")
        later_commit = self.commit("change output", LATER_TIME)

        hint = self.hint(["outputs/result.txt"])

        self.assert_contract_fields(hint)
        self.assertEqual(hint["status"], "outputs_changed")
        self.assertTrue(hint["complete"])
        self.assertEqual(
            hint["paths"],
            [
                {
                    "path": "outputs/result.txt",
                    "scope": "file",
                    "state": "changed",
                    "commit": later_commit,
                    "committed_at": "2024-01-01T00:01:00Z",
                }
            ],
        )

    def test__work_hint__removed_output__is_unavailable(self) -> None:
        (self.root / "outputs" / "result.txt").unlink()

        hint = self.hint(["outputs/result.txt"])

        self.assert_contract_fields(hint)
        self.assertEqual(hint["status"], "unavailable")
        self.assertFalse(hint["complete"])
        self.assertEqual(
            hint["paths"],
            [
                {
                    "path": "outputs/result.txt",
                    "scope": "file",
                    "state": "missing",
                    "reason": "missing",
                }
            ],
        )

    def test__work_hint__changed_and_missing_outputs__keeps_positive_observation(self) -> None:
        self.create_output("outputs/result.txt", "changed\n")
        self.commit("change output", LATER_TIME)

        hint = self.hint(["outputs/result.txt", "outputs/missing.txt"])

        self.assert_contract_fields(hint)
        self.assertEqual(hint["status"], "outputs_changed")
        self.assertFalse(hint["complete"])
        self.assertEqual(hint["paths"][0]["state"], "changed")
        self.assertEqual(hint["paths"][1], {"path": "outputs/missing.txt", "scope": "file", "state": "missing", "reason": "missing"})

    def test__work_hint__old_and_missing_outputs__is_unavailable(self) -> None:
        hint = self.hint(["outputs/result.txt", "outputs/missing.txt"])

        self.assert_contract_fields(hint)
        self.assertEqual(hint["status"], "unavailable")
        self.assertFalse(hint["complete"])
        self.assertEqual(hint["paths"][0]["state"], "unchanged")
        self.assertEqual(hint["paths"][1]["reason"], "missing")

    def test__work_hint__directory_with_later_descendant__keeps_directory_scope_and_warning(self) -> None:
        self.create_output("plugins/shared/first.txt", "initial\n")
        self.commit("add directory", INITIAL_TIME)
        self.create_output("plugins/shared/other.txt", "later\n")
        later_commit = self.commit("other work in directory", LATER_TIME)

        hint = self.hint(["plugins/shared/"])

        self.assert_contract_fields(hint)
        self.assertEqual(hint["status"], "outputs_changed")
        self.assertEqual(
            hint["paths"],
            [
                {
                    "path": "plugins/shared/",
                    "scope": "directory",
                    "state": "changed",
                    "commit": later_commit,
                    "committed_at": "2024-01-01T00:01:00Z",
                }
            ],
        )

    def test__work_hint__commit_in_build_second__is_ambiguous(self) -> None:
        same_second = "2024-01-01T00:00:30+0000"
        self.create_output("outputs/result.txt", "same second\n")
        self.commit("change in build second", same_second)

        hint = self.hint(["outputs/result.txt"])

        self.assert_contract_fields(hint)
        self.assertEqual(hint["status"], "unavailable")
        self.assertFalse(hint["complete"])
        self.assertEqual(
            hint["paths"],
            [
                {
                    "path": "outputs/result.txt",
                    "scope": "file",
                    "state": "unavailable",
                    "reason": "ambiguous_timestamp",
                }
            ],
        )

    def test__work_hint__symlink_outside_repository__rejects_without_external_path(self) -> None:
        outside = self.root.parent / "outside.txt"
        outside.write_text("external\n", encoding="utf-8")
        target = self.root / "outputs" / "external.txt"
        target.parent.mkdir(exist_ok=True)
        target.symlink_to(outside)

        hint = self.hint(["outputs/external.txt"])

        self.assert_contract_fields(hint)
        self.assertEqual(hint["status"], "unavailable")
        self.assertFalse(hint["complete"])
        self.assertEqual(hint["paths"], [])
        self.assertEqual(hint["rejected"]["outside_repository"], 1)


if __name__ == "__main__":
    unittest.main()
