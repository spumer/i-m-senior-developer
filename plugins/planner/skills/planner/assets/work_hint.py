"""Подсказка по истории git для объявленных выходов плана."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import Any

from execution_outputs import extract_outputs


_GIT_TIMEOUT_SECONDS = 10
_REJECTED_KEYS = ("absolute_path", "bare_path", "outside_repository", "placeholder")


class GitUnavailableError(Exception):
    """Git не смог предоставить данные, нужные для подсказки."""


def _run_git(directory: Path, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=directory,
            text=True,
            capture_output=True,
            check=False,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GitUnavailableError(str(error)) from error


def _repository_root(execution_path: Path) -> Path:
    result = _run_git(execution_path.parent, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        raise GitUnavailableError(result.stderr.strip())
    return Path(result.stdout.strip()).resolve()


def _literal_pathspec(path: str) -> str:
    return f":(literal){path}"


def _is_tracked(root: Path, path: str) -> bool:
    result = _run_git(
        root,
        ["ls-files", "--error-unmatch", "--", _literal_pathspec(path)],
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise GitUnavailableError(result.stderr.strip())


def _last_commit(root: Path, path: str) -> tuple[str, int] | None:
    result = _run_git(
        root,
        ["log", "-1", "--format=%H%x00%ct", "--", _literal_pathspec(path)],
    )
    if result.returncode != 0:
        raise GitUnavailableError(result.stderr.strip())
    output = result.stdout.rstrip("\n")
    if not output:
        return None
    commit, separator, timestamp = output.partition("\0")
    if not separator or not commit or not timestamp.isdigit():
        raise GitUnavailableError("git returned an invalid commit timestamp")
    return commit, int(timestamp)


def _format_timestamp_nanoseconds(timestamp_ns: int) -> str:
    seconds, nanoseconds = divmod(timestamp_ns, 1_000_000_000)
    moment = datetime.fromtimestamp(seconds, timezone.utc)
    return f"{moment:%Y-%m-%dT%H:%M:%S}.{nanoseconds:09d}Z"


def _format_timestamp_seconds(timestamp: int) -> str:
    moment = datetime.fromtimestamp(timestamp, timezone.utc)
    return f"{moment:%Y-%m-%dT%H:%M:%SZ}"


def _path_is_inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _unavailable_hint(
    plan_built_at_ns: int,
    rejected: dict[str, int],
    reason: str,
) -> dict[str, object]:
    return {
        "status": "unavailable",
        "message": "История git не позволила проверить изменение всех объявленных выходов.",
        "plan_built_at": _format_timestamp_nanoseconds(plan_built_at_ns),
        "plan_built_at_source": "execution_file_mtime",
        "complete": False,
        "paths": [],
        "rejected": rejected,
        "reason": reason,
    }


def _path_hint(
    root: Path,
    path: str,
    plan_built_at_ns: int,
) -> dict[str, object]:
    scope = "directory" if path.endswith("/") else "file"
    resolved = (root / path).resolve()
    base = {"path": path, "scope": scope}
    if not resolved.exists():
        return {**base, "state": "missing", "reason": "missing"}
    if not _is_tracked(root, path):
        return {**base, "state": "not_tracked", "reason": "not_tracked"}
    commit_data = _last_commit(root, path)
    if commit_data is None:
        return {**base, "state": "unavailable", "reason": "git_unavailable"}

    commit, committed_seconds = commit_data
    built_seconds = plan_built_at_ns // 1_000_000_000
    if committed_seconds == built_seconds:
        return {**base, "state": "unavailable", "reason": "ambiguous_timestamp"}
    if committed_seconds > built_seconds:
        state = "changed"
    else:
        state = "unchanged"
    return {
        **base,
        "state": state,
        "commit": commit,
        "committed_at": _format_timestamp_seconds(committed_seconds),
    }


def _message(status: str, has_directory: bool) -> str:
    if status == "outputs_changed":
        message = (
            "История git показывает, что после сборки менялся хотя бы один "
            "объявленный выход; это не подтверждает выполнение плана."
        )
        if has_directory:
            message = f"{message} Другая работа могла изменить файл в этом каталоге."
        return message
    if status == "outputs_unchanged":
        return "История git не показывает изменения проверенных выходов после сборки."
    return "История git не позволила проверить изменение всех объявленных выходов."


def build_work_hint(
    execution_path: Path,
    body: str,
    plan_built_at_ns: int,
) -> dict[str, object]:
    """Построить подсказку из выходов плана и достижимой истории git."""
    parsed = extract_outputs(body)
    rejected = {key: int(parsed["rejected"].get(key, 0)) for key in _REJECTED_KEYS}
    try:
        root = _repository_root(execution_path.resolve())
    except GitUnavailableError:
        return _unavailable_hint(plan_built_at_ns, rejected, "git_unavailable")

    paths: list[dict[str, object]] = []
    for path in parsed["paths"]:
        resolved = (root / path).resolve()
        if not _path_is_inside(root, resolved):
            rejected["outside_repository"] += 1
            continue
        try:
            paths.append(_path_hint(root, path, plan_built_at_ns))
        except GitUnavailableError:
            scope = "directory" if path.endswith("/") else "file"
            paths.append(
                {
                    "path": path,
                    "scope": scope,
                    "state": "unavailable",
                    "reason": "git_unavailable",
                }
            )

    states = [path["state"] for path in paths]
    complete = not any(rejected.values()) and all(
        state in {"changed", "unchanged"} for state in states
    ) and bool(paths)
    if "changed" in states:
        status = "outputs_changed"
    elif complete:
        status = "outputs_unchanged"
    else:
        status = "unavailable"

    return {
        "status": status,
        "message": _message(status, any(path.endswith("/") for path in parsed["paths"])),
        "plan_built_at": _format_timestamp_nanoseconds(plan_built_at_ns),
        "plan_built_at_source": "execution_file_mtime",
        "complete": complete,
        "paths": paths,
        "rejected": rejected,
    }
