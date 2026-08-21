import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Any, NoReturn


EXIT_STALE = 2
EXIT_INVALID = 3
EXIT_USAGE = 64
_VALID_STATUSES = {"current", "stale"}


class PlanStateError(Exception):
    pass


class CliParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"plan_state: {message}\n")


@dataclass(frozen=True)
class PlanDocument:
    path: Path
    metadata: dict[str, Any]
    body: str
    has_frontmatter: bool
    source: str


def normalize_body(body: str) -> str:
    return body.replace("\r\n", "\n").replace("\r", "\n")


def fingerprint(body: str) -> str:
    return hashlib.sha256(normalize_body(body).encode()).hexdigest()


def parse_scalar(value: str, path: Path, integer: bool) -> str | int:
    if integer:
        if value.isascii() and value.isdigit():
            return int(value)
        return value
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            raise PlanStateError(f"{path}: invalid quoted frontmatter value") from error
        if not isinstance(parsed, str):
            raise PlanStateError(f"{path}: quoted frontmatter value must be a string")
        return parsed
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1]
    return value


def split_field(line: str, path: Path) -> tuple[str, str]:
    key, separator, value = line.partition(":")
    if not separator or not key.strip():
        raise PlanStateError(f"{path}: invalid frontmatter line: {line!r}")
    return key.strip(), value.strip()


def parse_frontmatter(lines: list[str], path: Path) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    section: str | None = None
    for raw_line in lines:
        line = raw_line.rstrip("\r\n")
        if not line.strip():
            continue
        if line.startswith("  "):
            if len(line) > 2 and line[2].isspace():
                raise PlanStateError(
                    f"{path}: frontmatter supports two-space nesting only"
                )
            if section is None or not isinstance(metadata[section], dict):
                raise PlanStateError(f"{path}: nested field without a section")
            key, value = split_field(line[2:], path)
            if key in metadata[section]:
                raise PlanStateError(f"{path}: duplicate frontmatter field {section}.{key}")
            metadata[section][key] = parse_scalar(value, path, integer=key == "version")
            continue
        if line[0].isspace():
            raise PlanStateError(f"{path}: frontmatter supports two-space nesting only")
        key, value = split_field(line, path)
        if key in metadata:
            raise PlanStateError(f"{path}: duplicate frontmatter field {key}")
        if value:
            metadata[key] = parse_scalar(value, path, integer=key == "version")
            section = None
        else:
            metadata[key] = {}
            section = key
    return metadata


def read_document(path: Path) -> PlanDocument:
    resolved = path.expanduser().resolve()
    try:
        with resolved.open("r", encoding="utf-8", newline="") as source:
            text = source.read()
    except (OSError, UnicodeError) as error:
        raise PlanStateError(f"{resolved}: {error}") from error

    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return PlanDocument(resolved, {}, text, False, text)
    if len(lines) < 2 or not lines[1].startswith("plan_type:"):
        return PlanDocument(resolved, {}, text, False, text)

    closing_index = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.rstrip("\r\n") == "---"
        ),
        None,
    )
    if closing_index is None:
        raise PlanStateError(f"{resolved}: frontmatter has no closing delimiter")

    metadata = parse_frontmatter(lines[1:closing_index], resolved)
    body = "".join(lines[closing_index + 1 :])
    return PlanDocument(resolved, metadata, body, True, text)


def read_optional_document(path: Path) -> PlanDocument:
    resolved = path.expanduser().resolve()
    if resolved.exists():
        return read_document(resolved)
    return PlanDocument(resolved, {}, "", False, "")


def require_fields(
    metadata: dict[str, Any],
    allowed: set[str],
    required: set[str],
    path: Path,
) -> None:
    unknown = set(metadata) - allowed
    missing = required - set(metadata)
    if unknown:
        raise PlanStateError(f"{path}: unsupported frontmatter fields: {sorted(unknown)}")
    if missing:
        raise PlanStateError(f"{path}: missing frontmatter fields: {sorted(missing)}")


def require_version(value: Any, field: str, path: Path) -> int:
    if not isinstance(value, int) or value < 0:
        raise PlanStateError(f"{path}: {field} must be a non-negative integer")
    return value


def require_fingerprint(value: Any, field: str, path: Path) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise PlanStateError(f"{path}: {field} must be a SHA-256 fingerprint")
    try:
        int(value, 16)
    except ValueError as error:
        raise PlanStateError(f"{path}: {field} must be a SHA-256 fingerprint") from error
    return value


def validate_architecture(metadata: dict[str, Any], path: Path) -> dict[str, Any]:
    require_fields(
        metadata,
        {"plan_type", "version", "status", "content_sha256"},
        {"plan_type", "version", "status"},
        path,
    )
    if metadata["plan_type"] != "architecture":
        raise PlanStateError(f"{path}: plan_type must be architecture")
    require_version(metadata["version"], "version", path)
    if metadata["status"] != "current":
        raise PlanStateError(f"{path}: architecture status must be current")
    if "content_sha256" in metadata:
        require_fingerprint(metadata["content_sha256"], "content_sha256", path)
    return metadata


def validate_execution(
    metadata: dict[str, Any], path: Path, require_hashes: bool
) -> dict[str, Any]:
    required = {"plan_type", "version", "status", "architecture"}
    if require_hashes:
        required.add("content_sha256")
    require_fields(
        metadata,
        {"plan_type", "version", "status", "content_sha256", "architecture"},
        required,
        path,
    )
    if metadata["plan_type"] != "execution":
        raise PlanStateError(f"{path}: plan_type must be execution")
    require_version(metadata["version"], "version", path)
    if metadata["status"] not in _VALID_STATUSES:
        raise PlanStateError(f"{path}: status must be current or stale")
    if "content_sha256" in metadata:
        require_fingerprint(metadata["content_sha256"], "content_sha256", path)

    architecture = metadata["architecture"]
    if not isinstance(architecture, dict):
        raise PlanStateError(f"{path}: architecture must be a mapping")
    architecture_required = {"path", "version"}
    if require_hashes:
        architecture_required.add("content_sha256")
    require_fields(
        architecture,
        {"path", "version", "content_sha256"},
        architecture_required,
        path,
    )
    if not isinstance(architecture["path"], str) or not architecture["path"]:
        raise PlanStateError(f"{path}: architecture.path must be a non-empty path")
    require_version(architecture["version"], "architecture.version", path)
    if "content_sha256" in architecture:
        require_fingerprint(
            architecture["content_sha256"], "architecture.content_sha256", path
        )
    return metadata


def architecture_state(document: PlanDocument) -> dict[str, Any]:
    current_hash = fingerprint(document.body)
    if not document.has_frontmatter:
        return {
            "content_sha256": current_hash,
            "path": str(document.path),
            "plan_type": "architecture",
            "status": "current",
            "version": 0,
        }

    metadata = validate_architecture(document.metadata, document.path)
    return {
        "content_sha256": current_hash,
        "path": str(document.path),
        "plan_type": "architecture",
        "status": "current",
        "version": metadata["version"],
    }


def render_architecture(version: int, content_hash: str, body: str) -> str:
    return (
        "---\n"
        "plan_type: architecture\n"
        f"version: {version}\n"
        "status: current\n"
        f"content_sha256: {content_hash}\n"
        "---\n"
        f"{body}"
    )


def render_execution(metadata: dict[str, Any], body: str) -> str:
    architecture = metadata["architecture"]
    return (
        "---\n"
        "plan_type: execution\n"
        f"version: {metadata['version']}\n"
        f"status: {metadata['status']}\n"
        f"content_sha256: {metadata['content_sha256']}\n"
        "architecture:\n"
        f"  path: {json.dumps(architecture['path'], ensure_ascii=False)}\n"
        f"  version: {architecture['version']}\n"
        f"  content_sha256: {architecture['content_sha256']}\n"
        "---\n"
        f"{body}"
    )


def atomic_write(path: Path, content: str) -> None:
    if path.exists() and content == read_document(path).source:
        return

    temporary: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent, prefix=f".{path.name}.", text=True
        )
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as target:
            target.write(content)
            target.flush()
            os.fsync(target.fileno())
        if path.exists():
            os.chmod(temporary, path.stat().st_mode)
        os.replace(temporary, path)
    except OSError as error:
        cleanup_error: OSError | None = None
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError as caught_cleanup_error:
                cleanup_error = caught_cleanup_error
        message = f"{path}: {error}"
        if cleanup_error is not None:
            message = f"{message}; temporary cleanup failed: {cleanup_error}"
        raise PlanStateError(message) from error


def changed_since_recorded(document: PlanDocument, current_hash: str) -> bool:
    recorded_hash = document.metadata.get("content_sha256")
    return recorded_hash is None or recorded_hash != current_hash


def next_version(
    document: PlanDocument, current_hash: str, semantic_change: bool
) -> int:
    if not document.has_frontmatter:
        return 1
    previous = require_version(document.metadata["version"], "version", document.path)
    if semantic_change and changed_since_recorded(document, current_hash):
        return previous + 1
    return previous


def print_payload(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def inspect_architecture(path: Path) -> int:
    print_payload(architecture_state(read_document(path)))
    return 0


def consume_prepared_body(body_path: Path, target: Path) -> str:
    prepared = absolute_path(body_path)
    expected = target.with_name(f"{target.name}.prepared")
    if prepared != expected:
        raise PlanStateError(f"{prepared}: prepared body must be {expected.name}")
    if prepared.is_symlink():
        raise PlanStateError(f"{prepared}: prepared body must not be a symbolic link")

    try:
        prepared_stat = prepared.stat()
        if not stat.S_ISREG(prepared_stat.st_mode):
            raise PlanStateError(f"{prepared}: prepared body must be a regular file")
        if prepared_stat.st_nlink != 1:
            raise PlanStateError(f"{prepared}: prepared body must not be a hard link")
        with prepared.open("r", encoding="utf-8", newline="") as source:
            body = source.read()
        prepared.unlink()
    except PlanStateError:
        raise
    except (OSError, UnicodeError) as error:
        raise PlanStateError(f"{prepared}: {error}") from error
    return body


def sync_architecture(
    path: Path, body_path: Path, semantic_change: bool
) -> int:
    target_path = absolute_path(path)
    target = resolve_architecture_target(
        target_path, target_path.parent
    )
    body = consume_prepared_body(body_path, target)
    document = read_optional_document(target)
    if document.has_frontmatter:
        validate_architecture(document.metadata, document.path)
    current_hash = fingerprint(body)
    version = next_version(document, current_hash, semantic_change)
    atomic_write(
        target,
        render_architecture(version, current_hash, body),
    )
    print_payload(architecture_state(read_document(target)))
    return 0


def relative_architecture_path(execution: Path, architecture: Path) -> str:
    relative = os.path.relpath(architecture, start=execution.parent)
    if not relative.startswith(".") and os.sep not in relative:
        return f"./{relative}"
    return relative


def require_consistent_architecture(document: PlanDocument) -> dict[str, Any]:
    state = architecture_state(document)
    if document.has_frontmatter:
        recorded_hash = document.metadata.get("content_sha256")
        if recorded_hash is not None and recorded_hash != state["content_sha256"]:
            raise PlanStateError(
                f"{document.path}: architecture content hash does not match its body"
            )
    return state


def absolute_path(path: Path) -> Path:
    expanded = path.expanduser()
    return expanded.parent.resolve() / expanded.name


def same_existing_file(left: Path, right: Path) -> bool:
    if not left.exists() or not right.exists():
        return False
    try:
        return os.path.samefile(left, right)
    except OSError as error:
        raise PlanStateError(f"cannot compare {left} and {right}: {error}") from error


def validate_target_file(
    path: Path,
    directory: Path,
    expected_name: str,
    protected: Path | None = None,
) -> Path:
    target = absolute_path(path)
    allowed_directory = directory.expanduser().resolve()
    protected_path = absolute_path(protected) if protected is not None else None

    if target.is_symlink():
        raise PlanStateError(f"{target}: target must not be a symbolic link")
    if protected_path is not None and target == protected_path:
        raise PlanStateError("architecture and execution must be different files")
    if protected_path is not None and same_existing_file(target, protected_path):
        raise PlanStateError(f"{target}: target is a hard link to the protected file")
    if target.name != expected_name:
        raise PlanStateError(f"{target}: target name must be {expected_name}")
    if target.parent.resolve() != allowed_directory:
        raise PlanStateError(f"{target}: target must stay inside {allowed_directory}")

    if target.exists():
        target_stat = target.stat()
        if not stat.S_ISREG(target_stat.st_mode):
            raise PlanStateError(f"{target}: target must be a regular file")
        if target_stat.st_nlink != 1:
            raise PlanStateError(f"{target}: target must not be a hard link")
    return target.resolve()


def resolve_architecture_target(
    architecture_path: Path, directory: Path, source_path: Path | None = None
) -> Path:
    return validate_target_file(
        architecture_path, directory, "ARCHITECTURE.md", source_path
    )


def resolve_execution_target(
    execution_path: Path, architecture_path: Path, directory: Path
) -> tuple[Path, Path]:
    allowed_directory = directory.expanduser().resolve()
    architecture = architecture_path.expanduser().resolve()
    if architecture.parent != allowed_directory:
        raise PlanStateError(
            "architecture and execution must be in the same directory"
        )
    execution = validate_target_file(
        execution_path, allowed_directory, "PLANNER_EXECUTION.md", architecture
    )
    return execution, architecture


def validate_architecture_target(
    architecture_path: Path, directory: Path, source_path: Path | None
) -> int:
    architecture = resolve_architecture_target(
        architecture_path, directory, source_path
    )
    print_payload({"path": str(architecture), "status": "current"})
    return 0


def validate_execution_target(
    execution_path: Path, architecture_path: Path, directory: Path
) -> int:
    execution, architecture = resolve_execution_target(
        execution_path, architecture_path, directory
    )
    print_payload(
        {
            "architecture_path": str(architecture),
            "execution_path": str(execution),
            "status": "current",
        }
    )
    return 0


def sync_execution(
    execution_path: Path,
    body_path: Path,
    architecture_path: Path,
    semantic_change: bool,
) -> int:
    target_path = absolute_path(execution_path)
    execution, architecture = resolve_execution_target(
        target_path, architecture_path, target_path.parent
    )

    body = consume_prepared_body(body_path, execution)
    architecture_document = read_document(architecture)
    architecture_data = require_consistent_architecture(architecture_document)
    execution_document = read_optional_document(execution)
    if execution_document.has_frontmatter:
        validate_execution(execution_document.metadata, execution, require_hashes=False)

    execution_hash = fingerprint(body)
    version = next_version(execution_document, execution_hash, semantic_change)
    metadata = {
        "plan_type": "execution",
        "version": version,
        "status": "current",
        "content_sha256": execution_hash,
        "architecture": {
            "path": relative_architecture_path(execution, architecture),
            "version": architecture_data["version"],
            "content_sha256": architecture_data["content_sha256"],
        },
    }
    atomic_write(execution, render_execution(metadata, body))
    print_payload(
        {
            "architecture": metadata["architecture"],
            "content_sha256": execution_hash,
            "path": str(execution),
            "plan_type": "execution",
            "status": "current",
            "version": version,
        }
    )
    return 0


def resolve_architecture(execution: PlanDocument) -> Path:
    architecture_path = Path(execution.metadata["architecture"]["path"])
    if architecture_path.is_absolute():
        return architecture_path.resolve()
    return (execution.path.parent / architecture_path).resolve()


def stale_reason(
    execution: PlanDocument,
    architecture: PlanDocument,
    architecture_data: dict[str, Any],
) -> str | None:
    recorded_architecture_hash = architecture.metadata.get("content_sha256")
    if (
        architecture.has_frontmatter
        and recorded_architecture_hash is not None
        and recorded_architecture_hash != architecture_data["content_sha256"]
    ):
        return "architecture content hash mismatch"
    reference = execution.metadata["architecture"]
    if reference["version"] != architecture_data["version"]:
        return "architecture version mismatch"
    if reference["content_sha256"] != architecture_data["content_sha256"]:
        return "architecture content hash mismatch"
    if execution.metadata["status"] == "stale":
        return "execution status is stale"
    return None


def mark_execution_stale(document: PlanDocument) -> None:
    metadata = dict(document.metadata)
    metadata["architecture"] = dict(document.metadata["architecture"])
    metadata["status"] = "stale"
    atomic_write(document.path, render_execution(metadata, document.body))


def check_execution(path: Path, mark_stale: bool) -> int:
    execution = read_document(path)
    if not execution.has_frontmatter:
        raise PlanStateError(f"{execution.path}: execution frontmatter is required")
    metadata = validate_execution(execution.metadata, execution.path, require_hashes=True)
    if fingerprint(execution.body) != metadata["content_sha256"]:
        raise PlanStateError(f"{execution.path}: execution content hash mismatch")

    architecture = read_document(resolve_architecture(execution))
    architecture_data = architecture_state(architecture)
    reason = stale_reason(execution, architecture, architecture_data)
    if reason is None:
        print_payload(
            {
                "architecture_path": architecture_data["path"],
                "current_version": architecture_data["version"],
                "execution_path": str(execution.path),
                "recorded_version": metadata["architecture"]["version"],
                "status": "current",
            }
        )
        return 0

    if mark_stale and metadata["status"] != "stale":
        mark_execution_stale(execution)
    print_payload(
        {
            "architecture_path": architecture_data["path"],
            "current_version": architecture_data["version"],
            "execution_path": str(execution.path),
            "reason": reason,
            "recorded_version": metadata["architecture"]["version"],
            "status": "stale",
        }
    )
    return EXIT_STALE


def semantic_change(value: str) -> bool:
    return value == "yes"


_REPORT_PREFIXES = {
    "implementation": "IMPLEMENTATION",
    "review": "REVIEW",
    "documentation": "DOCUMENTATION",
}
_REPORT_NUMBER_LIMIT = 99
_RESERVATION_ATTEMPTS = 100


def report_directory_numbers(directory: Path, prefix: str) -> tuple[list[int], list[str]]:
    pattern = re.compile(rf"^{prefix}-(\d{{2}})\.md$")
    numbers: list[int] = []
    empties: list[str] = []
    try:
        entries = sorted(directory.iterdir())
    except OSError as error:
        raise PlanStateError(f"{directory}: {error}") from error
    for entry in entries:
        match = pattern.fullmatch(entry.name)
        if match is None:
            continue
        try:
            size = entry.stat().st_size
        except OSError as error:
            raise PlanStateError(f"{entry}: {error}") from error
        numbers.append(int(match.group(1)))
        if size == 0:
            empties.append(str(entry.resolve()))
    return numbers, empties


def report_exhausted(prefix: str, empties: list[str]) -> PlanStateError:
    listing = ", ".join(empties) if empties else "none"
    return PlanStateError(
        f"{prefix} numbers 01-99 exhausted; cannot create {prefix}-100.md; "
        f"empty reserved files: {listing}"
    )


def reserve_report(directory: Path, kind: str) -> dict[str, Any]:
    prefix = _REPORT_PREFIXES[kind]
    resolved = directory.expanduser().resolve()
    if not resolved.is_dir():
        raise PlanStateError(f"{resolved}: report directory must exist")
    numbers, empties = report_directory_numbers(resolved, prefix)
    number = max(numbers, default=0) + 1
    for _ in range(_RESERVATION_ATTEMPTS):
        if number > _REPORT_NUMBER_LIMIT:
            raise report_exhausted(prefix, empties)
        target = resolved / f"{prefix}-{number:02d}.md"
        try:
            descriptor = os.open(
                target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666
            )
        except FileExistsError:
            number += 1
            continue
        except OSError as error:
            raise PlanStateError(f"{target}: {error}") from error
        os.close(descriptor)
        return {
            "created": True,
            "empties": empties,
            "kind": kind,
            "number": number,
            "path": str(target.resolve()),
        }
    raise report_exhausted(prefix, empties)


def build_parser() -> CliParser:
    parser = CliParser(prog="plan_state.py")
    commands = parser.add_subparsers(
        dest="command", required=True, parser_class=CliParser
    )

    inspect_command = commands.add_parser("inspect")
    inspect_command.add_argument("path", type=Path)

    architecture_target_command = commands.add_parser(
        "validate-architecture-target"
    )
    architecture_target_command.add_argument("path", type=Path)
    architecture_target_command.add_argument("--directory", type=Path, required=True)
    architecture_target_command.add_argument("--source", type=Path)

    execution_target_command = commands.add_parser("validate-execution-target")
    execution_target_command.add_argument("path", type=Path)
    execution_target_command.add_argument("--architecture", type=Path, required=True)
    execution_target_command.add_argument("--directory", type=Path, required=True)

    architecture_command = commands.add_parser("sync-architecture")
    architecture_command.add_argument("path", type=Path)
    architecture_command.add_argument("--body-file", type=Path, required=True)
    architecture_command.add_argument(
        "--semantic-change", choices=("yes", "no"), required=True
    )

    execution_command = commands.add_parser("sync-execution")
    execution_command.add_argument("path", type=Path)
    execution_command.add_argument("--body-file", type=Path, required=True)
    execution_command.add_argument("--architecture", type=Path, required=True)
    execution_command.add_argument(
        "--semantic-change", choices=("yes", "no"), required=True
    )

    check_command = commands.add_parser("check")
    check_command.add_argument("path", type=Path)
    check_command.add_argument("--mark-stale", action="store_true")

    reserve_command = commands.add_parser("reserve-report")
    reserve_command.add_argument("--directory", type=Path, required=True)
    reserve_command.add_argument(
        "--kind", choices=tuple(_REPORT_PREFIXES), required=True
    )
    return parser


def run(arguments: list[str] | None = None) -> int:
    options = build_parser().parse_args(arguments)
    if options.command == "inspect":
        return inspect_architecture(options.path)
    if options.command == "validate-architecture-target":
        return validate_architecture_target(
            options.path, options.directory, options.source
        )
    if options.command == "validate-execution-target":
        return validate_execution_target(
            options.path, options.architecture, options.directory
        )
    if options.command == "sync-architecture":
        return sync_architecture(
            options.path,
            options.body_file,
            semantic_change(options.semantic_change),
        )
    if options.command == "sync-execution":
        return sync_execution(
            options.path,
            options.body_file,
            options.architecture,
            semantic_change(options.semantic_change),
        )
    if options.command == "reserve-report":
        print_payload(reserve_report(options.directory, options.kind))
        return 0
    return check_execution(options.path, options.mark_stale)


def main() -> int:
    try:
        return run()
    except PlanStateError as error:
        print(f"plan_state: {error}", file=sys.stderr)
        return EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
