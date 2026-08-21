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
_IDEA_STAGES = {"exploring", "resolved"}
_IDEA_OUTCOMES = {
    "open",
    "feature",
    "epic",
    "research",
    "experiment",
    "decision",
    "deferred",
    "rejected",
    "duplicate",
    "split",
}
_EPIC_STAGES = {"shaping", "active", "closed", "superseded"}
_ROADMAP_STATES = {"active", "paused", "completed", "cancelled"}
_FEATURE_READINESS = {"draft", "ready"}
_TARGET_OUTCOMES = {"feature", "epic", "duplicate"}
_REFERENCE_FIELDS = {"path", "version", "content_sha256"}
_KIND_PREFIXES = {"idea": "IDEA", "epic": "EPIC", "feature": "FEAT"}
_REFERENCE_FIELD_BY_KIND = {"epic": "origin", "roadmap": "epic", "feature": "parent"}
_SYNC_FIELD_NAMES = ("parent", "stage", "outcome", "target", "readiness", "state")
_SYNC_FIELDS_BY_KIND = {
    "idea": {"stage", "outcome", "target"},
    "epic": {"parent", "stage"},
    "roadmap": {"parent", "state"},
    "feature": {"parent", "readiness"},
}
_RESPONSE_SHARED_FIELDS = {
    "problem",
    "outcome",
    "actors",
    "scope_in",
    "scope_out",
    "assumptions",
    "unknowns",
    "limitations",
}
_RESPONSE_FIELDS_BY_KIND = {
    "idea": {"recommended_outcome"},
    "epic": {"candidate_slices"},
    "roadmap": {"candidate_slices"},
    "feature": set[str](),
}
_RESPONSE_LIST_FIELDS = {
    "assumptions",
    "unknowns",
    "candidate_slices",
    "limitations",
}
_RESPONSE_REQUIRED_FIELDS = ("problem", "outcome", "limitations")
_SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_IDEA_NAME_PATTERN = re.compile(
    r"IDEA-[0-9]{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.md\Z"
)
_CAPABILITY_HEADERS = (
    "Способность",
    "Нужна для",
    "Поставщик",
    "Источник",
    "Доступность",
    "Покрытие",
    "Основание",
    "Ограничения",
    "Приоритет",
)
_CAPABILITY_FIELDS = (
    "capability",
    "required_for",
    "provider",
    "source",
    "availability",
    "coverage",
    "evidence",
    "limitations",
    "priority",
)
_PRODUCT_KINDS = {"idea", "epic", "roadmap", "feature"}
_REQUIRED_CAPABILITIES_BY_KIND = {
    "idea": (
        "problem_outcome_framing",
        "product_synthesis",
        "decision_dialogue",
    ),
    "epic": (
        "problem_outcome_framing",
        "product_synthesis",
        "decision_dialogue",
    ),
    "roadmap": ("product_synthesis", "decision_dialogue"),
    "feature": ("problem_outcome_framing", "decision_dialogue"),
}
_CAPABILITY_AVAILABILITIES = {"available", "stale", "error", "not-surfaced"}
_CAPABILITY_COVERAGES = {"full", "partial", "unknown", "none"}
_CAPABILITY_PRIORITIES = {"configured", "project", "plugin", "builtin"}
_PRIORITY_ORDER = {"configured": 0, "project": 1, "plugin": 2, "builtin": 3}
_COVERAGE_ORDER = {"full": 0, "partial": 1}
_DATE_MARKER_PATTERN = re.compile(
    r"<!--[^>]*\b([0-9]{4}-[0-9]{2}-[0-9]{2})\b[^>]*-->"
)
_HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
_DASH = "—"
LEASE_DIRECTORY_PREFIX = "product-response-"
LEASE_FILE_NAME = "provider-response.json"


class ProductStateError(Exception):
    pass


class CliParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"product_state: {message}\n")


@dataclass(frozen=True)
class ProductDocument:
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
            raise ProductStateError(f"{path}: invalid quoted frontmatter value") from error
        if not isinstance(parsed, str):
            raise ProductStateError(
                f"{path}: quoted frontmatter value must be a string"
            )
        return parsed
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1]
    return value


def split_field(line: str, path: Path) -> tuple[str, str]:
    key, separator, value = line.partition(":")
    if not separator or not key.strip():
        raise ProductStateError(f"{path}: invalid frontmatter line: {line!r}")
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
                raise ProductStateError(
                    f"{path}: frontmatter supports two-space nesting only"
                )
            if section is None or not isinstance(metadata[section], dict):
                raise ProductStateError(f"{path}: nested field without a section")
            key, value = split_field(line[2:], path)
            if key in metadata[section]:
                raise ProductStateError(
                    f"{path}: duplicate frontmatter field {section}.{key}"
                )
            metadata[section][key] = parse_scalar(
                value, path, integer=key == "version"
            )
            continue
        if line[0].isspace():
            raise ProductStateError(
                f"{path}: frontmatter supports two-space nesting only"
            )
        key, value = split_field(line, path)
        if key in metadata:
            raise ProductStateError(f"{path}: duplicate frontmatter field {key}")
        if value:
            metadata[key] = parse_scalar(value, path, integer=key == "version")
            section = None
        else:
            metadata[key] = {}
            section = key
    return metadata


def read_document(path: Path) -> ProductDocument:
    resolved = path.expanduser().resolve()
    try:
        with resolved.open("r", encoding="utf-8", newline="") as source:
            text = source.read()
    except (OSError, UnicodeError) as error:
        raise ProductStateError(f"{resolved}: {error}") from error

    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return ProductDocument(resolved, {}, text, False, text)
    if len(lines) < 2 or not lines[1].startswith("plan_type:"):
        return ProductDocument(resolved, {}, text, False, text)
    closing_index = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.rstrip("\r\n") == "---"
        ),
        None,
    )
    if closing_index is None:
        raise ProductStateError(f"{resolved}: frontmatter has no closing delimiter")
    metadata = parse_frontmatter(lines[1:closing_index], resolved)
    body = "".join(lines[closing_index + 1 :])
    return ProductDocument(resolved, metadata, body, True, text)


def read_optional_document(path: Path) -> ProductDocument:
    resolved = absolute_path(path)
    if resolved.exists():
        return read_document(resolved)
    return ProductDocument(resolved, {}, "", False, "")


def require_fields(
    metadata: dict[str, Any],
    allowed: set[str],
    required: set[str],
    path: Path,
) -> None:
    unknown = set(metadata) - allowed
    missing = required - set(metadata)
    if unknown:
        raise ProductStateError(
            f"{path}: unsupported frontmatter fields: {sorted(unknown)}"
        )
    if missing:
        raise ProductStateError(
            f"{path}: missing frontmatter fields: {sorted(missing)}"
        )


def require_version(value: Any, field: str, path: Path) -> int:
    if not isinstance(value, int) or value < 0:
        raise ProductStateError(f"{path}: {field} must be a non-negative integer")
    return value


def require_fingerprint(value: Any, field: str, path: Path) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ProductStateError(f"{path}: {field} must be a SHA-256 fingerprint")
    try:
        int(value, 16)
    except ValueError as error:
        raise ProductStateError(
            f"{path}: {field} must be a SHA-256 fingerprint"
        ) from error
    return value


def require_choice(value: Any, field: str, choices: set[str], path: Path) -> str:
    if not isinstance(value, str) or value not in choices:
        raise ProductStateError(
            f"{path}: {field} must be one of {sorted(choices)}"
        )
    return value


def validate_common(
    metadata: dict[str, Any], plan_type: str, allowed: set[str], required: set[str], path: Path
) -> None:
    common = {"plan_type", "version", "status", "content_sha256"}
    require_fields(metadata, common | allowed, common | required, path)
    if metadata["plan_type"] != plan_type:
        raise ProductStateError(f"{path}: plan_type must be {plan_type}")
    require_version(metadata["version"], "version", path)
    require_choice(metadata["status"], "status", _VALID_STATUSES, path)
    require_fingerprint(metadata["content_sha256"], "content_sha256", path)


def validate_reference(value: Any, field: str, path: Path) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProductStateError(f"{path}: {field} must be a mapping")
    require_fields(value, _REFERENCE_FIELDS, _REFERENCE_FIELDS, path)
    reference_path = value["path"]
    if not isinstance(reference_path, str) or not reference_path:
        raise ProductStateError(f"{path}: {field}.path must be a non-empty path")
    require_version(value["version"], f"{field}.version", path)
    require_fingerprint(value["content_sha256"], f"{field}.content_sha256", path)
    return value


def validate_idea_relationships(metadata: dict[str, Any], path: Path) -> None:
    stage = metadata["stage"]
    outcome = metadata["outcome"]
    target = metadata.get("target")
    if stage == "exploring" and outcome != "open":
        raise ProductStateError(f"{path}: exploring idea requires outcome open")
    if stage == "exploring" and target is not None:
        raise ProductStateError(f"{path}: exploring idea must not have target")
    if stage == "resolved" and outcome == "open":
        raise ProductStateError(f"{path}: resolved idea cannot have outcome open")
    if outcome in _TARGET_OUTCOMES and target is None:
        raise ProductStateError(f"{path}: outcome {outcome} requires target")
    if target is not None and (not isinstance(target, str) or not target):
        raise ProductStateError(f"{path}: target must be a non-empty path")


def validate_idea(metadata: dict[str, Any], path: Path) -> dict[str, Any]:
    validate_common(
        metadata,
        "idea",
        {"stage", "outcome", "target"},
        {"stage", "outcome"},
        path,
    )
    require_choice(metadata["stage"], "stage", _IDEA_STAGES, path)
    require_choice(metadata["outcome"], "outcome", _IDEA_OUTCOMES, path)
    validate_idea_relationships(metadata, path)
    return metadata


def validate_epic(metadata: dict[str, Any], path: Path) -> dict[str, Any]:
    validate_common(metadata, "epic", {"stage", "origin"}, {"stage"}, path)
    require_choice(metadata["stage"], "stage", _EPIC_STAGES, path)
    if "origin" in metadata:
        validate_reference(metadata["origin"], "origin", path)
    return metadata


def validate_roadmap(metadata: dict[str, Any], path: Path) -> dict[str, Any]:
    validate_common(
        metadata, "roadmap", {"state", "epic"}, {"state", "epic"}, path
    )
    require_choice(metadata["state"], "state", _ROADMAP_STATES, path)
    validate_reference(metadata["epic"], "epic", path)
    return metadata


def validate_feature(metadata: dict[str, Any], path: Path) -> dict[str, Any]:
    validate_common(
        metadata, "feature", {"readiness", "parent"}, {"readiness"}, path
    )
    require_choice(metadata["readiness"], "readiness", _FEATURE_READINESS, path)
    if "parent" in metadata:
        validate_reference(metadata["parent"], "parent", path)
    return metadata


_VALIDATORS = {
    "idea": validate_idea,
    "epic": validate_epic,
    "roadmap": validate_roadmap,
    "feature": validate_feature,
}


def document_state(document: ProductDocument) -> dict[str, Any]:
    if not document.has_frontmatter:
        return {
            "content_sha256": fingerprint(document.body),
            "path": str(document.path),
            "plan_type": None,
            "status": "current",
            "version": 0,
        }
    plan_type = document.metadata.get("plan_type")
    if not isinstance(plan_type, str):
        raise ProductStateError(f"{document.path}: unsupported plan_type {plan_type!r}")
    validator = _VALIDATORS.get(plan_type)
    if validator is None:
        raise ProductStateError(f"{document.path}: unsupported plan_type {plan_type!r}")
    metadata = validator(document.metadata, document.path)
    payload = {
        "content_sha256": fingerprint(document.body),
        "path": str(document.path),
        "plan_type": plan_type,
        "status": metadata["status"],
        "version": metadata["version"],
    }
    for field in ("stage", "outcome", "target", "readiness", "state"):
        if field in metadata:
            payload[field] = metadata[field]
    for field in ("origin", "epic", "parent"):
        if field in metadata:
            payload[field] = metadata[field]
    return payload


def absolute_path(path: Path) -> Path:
    expanded = path.expanduser()
    return expanded.parent.resolve() / expanded.name


def validate_target_name(kind: str, target: Path) -> None:
    expected_names = {
        "epic": "EPIC.md",
        "roadmap": "ROADMAP.md",
        "feature": "README.md",
    }
    if kind == "idea":
        if _IDEA_NAME_PATTERN.fullmatch(target.name) is None:
            raise ProductStateError(f"{target}: invalid idea target name")
        return
    expected = expected_names[kind]
    if target.name != expected:
        raise ProductStateError(f"{target}: target name must be {expected}")


def validate_roadmap_parent(target: Path, parent: Path | None) -> None:
    if parent is None:
        raise ProductStateError(f"{target}: roadmap parent EPIC.md is required")
    parent_path = absolute_path(parent)
    if parent_path.name != "EPIC.md" or parent_path.parent != target.parent:
        raise ProductStateError(
            f"{target}: parent EPIC.md must be in the same directory"
        )


def validate_target_file_type(target: Path) -> None:
    if target.is_symlink():
        raise ProductStateError(f"{target}: target must not be a symbolic link")
    if not target.exists():
        return
    try:
        target_stat = target.stat()
    except OSError as error:
        raise ProductStateError(f"{target}: {error}") from error
    if not stat.S_ISREG(target_stat.st_mode):
        raise ProductStateError(f"{target}: target must be a regular file")
    if target_stat.st_nlink != 1:
        raise ProductStateError(f"{target}: target must not be a hard link")


def validate_protected_parent(target: Path, parent: Path | None) -> None:
    if parent is None:
        return
    parent_path = absolute_path(parent)
    if target == parent_path:
        raise ProductStateError("target and protected parent must be different files")


def resolve_target(
    kind: str, path: Path, directory: Path, parent: Path | None = None
) -> Path:
    target = absolute_path(path)
    allowed_directory = directory.expanduser().resolve()
    validate_target_name(kind, target)
    if target.parent != allowed_directory:
        raise ProductStateError(
            f"{target}: target must stay inside {allowed_directory}"
        )
    if kind == "roadmap":
        validate_roadmap_parent(target, parent)
    validate_protected_parent(target, parent)
    validate_target_file_type(target)
    return target


def validate_target(
    kind: str, path: Path, directory: Path, parent: Path | None = None
) -> int:
    target = resolve_target(kind, path, directory, parent)
    print_payload({"kind": kind, "path": str(target), "status": "current"})
    return 0


def render_document(metadata: dict[str, Any], body: str) -> str:
    lines = [
        "---\n",
        f"plan_type: {metadata['plan_type']}\n",
        f"version: {metadata['version']}\n",
        f"status: {metadata['status']}\n",
        f"content_sha256: {metadata['content_sha256']}\n",
    ]
    for field in ("stage", "outcome", "readiness", "state"):
        if field in metadata:
            lines.append(f"{field}: {metadata[field]}\n")
    if "target" in metadata:
        value = json.dumps(metadata["target"], ensure_ascii=False)
        lines.append(f"target: {value}\n")
    for field in ("origin", "epic", "parent"):
        if field not in metadata:
            continue
        reference = metadata[field]
        lines.extend(
            (
                f"{field}:\n",
                f"  path: {json.dumps(reference['path'], ensure_ascii=False)}\n",
                f"  version: {reference['version']}\n",
                f"  content_sha256: {reference['content_sha256']}\n",
            )
        )
    lines.extend(("---\n", body))
    return "".join(lines)


def next_version(
    document: ProductDocument, current_hash: str, semantic_change: bool
) -> int:
    if not document.has_frontmatter:
        return 1
    previous = require_version(document.metadata["version"], "version", document.path)
    recorded_hash = document.metadata.get("content_sha256")
    if semantic_change and recorded_hash != current_hash:
        return previous + 1
    return previous


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
        raise ProductStateError(message) from error


def sync_idea_document(
    path: Path,
    body_path: Path,
    semantic_change: bool,
    stage: str | None,
    outcome: str | None,
    target_reference: str | None,
) -> int:
    target_path = absolute_path(path)
    target = resolve_target("idea", target_path, target_path.parent)
    body = consume_prepared_body(body_path, target)
    document = read_optional_document(target)
    if document.has_frontmatter:
        document_state(document)
    content_hash = fingerprint(body)
    metadata: dict[str, Any] = {
        "plan_type": "idea",
        "version": next_version(document, content_hash, semantic_change),
        "status": "current",
        "content_sha256": content_hash,
        "stage": stage,
        "outcome": outcome,
    }
    if target_reference is not None:
        metadata["target"] = target_reference
    validate_idea(metadata, target)
    atomic_write(target, render_document(metadata, body))
    print_payload(document_state(read_document(target)))
    return 0


def relative_reference_path(document: Path, referenced: Path) -> str:
    relative = os.path.relpath(referenced, start=document.parent)
    if not relative.startswith(".") and os.sep not in relative:
        return f"./{relative}"
    return relative


def parent_snapshot(target: Path, parent: Path) -> dict[str, Any]:
    parent_document = read_document(parent)
    parent_state = document_state(parent_document)
    if parent_document.metadata["content_sha256"] != parent_state["content_sha256"]:
        raise ProductStateError(
            f"{parent_document.path}: content hash does not match its body"
        )
    return {
        "path": relative_reference_path(target, parent_document.path),
        "version": parent_state["version"],
        "content_sha256": parent_state["content_sha256"],
    }


def sync_linked_document(
    kind: str,
    path: Path,
    body_path: Path,
    semantic_change: bool,
    parent: Path | None,
    field_value: str | None,
) -> int:
    target_path = absolute_path(path)
    document: ProductDocument | None = None
    validation_parent = parent
    if kind == "roadmap" and parent is None:
        validate_target_name(kind, target_path)
        validate_target_file_type(target_path)
        document = read_optional_document(target_path)
        if document.has_frontmatter:
            document_state(document)
            reference = document.metadata.get("epic")
            if isinstance(reference, dict):
                validation_parent = resolve_parent(document, reference)

    target = resolve_target(kind, target_path, target_path.parent, validation_parent)
    reference_field = _REFERENCE_FIELD_BY_KIND[kind]
    parent_reference = (
        parent_snapshot(target, parent) if parent is not None else None
    )
    body = consume_prepared_body(body_path, target)
    if document is None:
        document = read_optional_document(target)
        if document.has_frontmatter:
            document_state(document)
    content_hash = fingerprint(body)
    value_field = {"epic": "stage", "roadmap": "state", "feature": "readiness"}[
        kind
    ]
    metadata: dict[str, Any] = {
        "plan_type": kind,
        "version": next_version(document, content_hash, semantic_change),
        "status": "current",
        "content_sha256": content_hash,
        value_field: field_value,
    }
    if parent_reference is not None:
        metadata[reference_field] = parent_reference
    elif document.has_frontmatter and reference_field in document.metadata:
        metadata[reference_field] = dict(document.metadata[reference_field])
    _VALIDATORS[kind](metadata, target)
    atomic_write(target, render_document(metadata, body))
    print_payload(document_state(read_document(target)))
    return 0


def resolve_parent(document: ProductDocument, reference: dict[str, Any]) -> Path:
    reference_path = Path(reference["path"])
    if reference_path.is_absolute():
        return reference_path.resolve()
    return (document.path.parent / reference_path).resolve()


def parent_stale_reason(
    reference_field: str,
    reference: dict[str, Any],
    parent: ProductDocument,
    parent_state: dict[str, Any],
) -> str | None:
    if parent.metadata["content_sha256"] != parent_state["content_sha256"]:
        return f"{reference_field} content hash does not match its body"
    if reference["version"] != parent_state["version"]:
        return f"{reference_field} version mismatch"
    if reference["content_sha256"] != parent_state["content_sha256"]:
        return f"{reference_field} content hash mismatch"
    return None


def mark_document_stale(document: ProductDocument) -> None:
    metadata = dict(document.metadata)
    for field in _REFERENCE_FIELD_BY_KIND.values():
        if field in metadata:
            metadata[field] = dict(metadata[field])
    metadata["status"] = "stale"
    atomic_write(document.path, render_document(metadata, document.body))


def check_document(path: Path, mark_stale: bool) -> int:
    document = read_document(path)
    state = document_state(document)
    if not document.has_frontmatter:
        print_payload(state)
        return 0
    metadata = document.metadata
    if metadata["content_sha256"] != state["content_sha256"]:
        raise ProductStateError(f"{document.path}: content hash mismatch")

    reference_field = _REFERENCE_FIELD_BY_KIND.get(state["plan_type"])
    reason: str | None = None
    parent_state: dict[str, Any] | None = None
    if reference_field is not None and reference_field in metadata:
        reference = metadata[reference_field]
        parent = read_document(resolve_parent(document, reference))
        parent_state = document_state(parent)
        reason = parent_stale_reason(
            reference_field, reference, parent, parent_state
        )
    if reason is None and metadata["status"] == "stale":
        reason = "document status is stale"

    payload: dict[str, Any] = {"path": str(document.path)}
    if parent_state is not None and reference_field is not None:
        payload.update(
            {
                "current_version": parent_state["version"],
                "parent_path": parent_state["path"],
                "recorded_version": metadata[reference_field]["version"],
            }
        )
    if reason is None:
        payload["status"] = "current"
        print_payload(payload)
        return 0

    if mark_stale and metadata["status"] != "stale":
        mark_document_stale(document)
    payload.update({"reason": reason, "status": "stale"})
    print_payload(payload)
    return EXIT_STALE


def consume_prepared_body(body_path: Path, target: Path) -> str:
    prepared = absolute_path(body_path)
    resolved_target = absolute_path(target)
    expected = resolved_target.with_name(f"{resolved_target.name}.prepared")
    if prepared != expected:
        raise ProductStateError(
            f"{prepared}: prepared body must be {expected.name}"
        )
    if prepared.is_symlink():
        raise ProductStateError(
            f"{prepared}: prepared body must not be a symbolic link"
        )
    try:
        prepared_stat = prepared.stat()
        if not stat.S_ISREG(prepared_stat.st_mode):
            raise ProductStateError(
                f"{prepared}: prepared body must be a regular file"
            )
        if prepared_stat.st_nlink != 1:
            raise ProductStateError(
                f"{prepared}: prepared body must not be a hard link"
            )
        with prepared.open("r", encoding="utf-8", newline="") as source:
            body = source.read()
        prepared.unlink()
    except ProductStateError:
        raise
    except (OSError, UnicodeError) as error:
        raise ProductStateError(f"{prepared}: {error}") from error
    return body


def scan_allocated_numbers(root: Path, prefix: str) -> tuple[list[int], list[int]]:
    pattern = re.compile(rf"{re.escape(prefix)}-([0-9]{{4}})-")
    numbers = [
        int(match.group(1))
        for entry in root.iterdir()
        if (match := pattern.match(entry.name)) is not None
    ]
    duplicates = sorted(
        number for number in set(numbers) if numbers.count(number) > 1
    )
    return numbers, duplicates


def allocation_target(kind: str, root: Path, number: int, slug: str) -> Path:
    prefix = _KIND_PREFIXES[kind]
    name = f"{prefix}-{number:04d}-{slug}"
    if kind == "idea":
        name = f"{name}.md"
    return root / name


def create_allocation(kind: str, target: Path) -> None:
    if kind == "idea":
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
        os.close(descriptor)
        return
    target.mkdir()
    if kind == "feature":
        review_directory = target / "review-request-changes"
        try:
            review_directory.mkdir()
        except OSError as error:
            cleanup_error: OSError | None = None
            try:
                target.rmdir()
            except OSError as caught_cleanup_error:
                cleanup_error = caught_cleanup_error
            message = f"{review_directory}: {error}"
            if cleanup_error is not None:
                message = f"{message}; allocation cleanup failed: {cleanup_error}"
            raise ProductStateError(message) from error


def validate_allocation_request(kind: str, root: Path, slug: str) -> Path:
    if kind == "roadmap":
        raise ProductStateError("roadmap cannot be allocated")
    if kind not in _KIND_PREFIXES:
        raise ProductStateError(f"unsupported product kind {kind!r}")
    if _SLUG_PATTERN.fullmatch(slug) is None:
        raise ProductStateError(f"invalid slug {slug!r}")
    resolved_root = root.expanduser().resolve()
    if not resolved_root.is_dir():
        raise ProductStateError(
            f"{resolved_root}: allocation root must be a directory"
        )
    return resolved_root


def allocation_payload(
    kind: str, target: Path, number: int, duplicates: list[int]
) -> dict[str, Any]:
    return {
        "created": True,
        "duplicates": duplicates,
        "id": f"{_KIND_PREFIXES[kind]}-{number:04d}",
        "kind": kind,
        "number": number,
        "path": str(target.resolve()),
    }


def allocate_artifact(kind: str, root: Path, slug: str) -> dict[str, Any]:
    resolved_root = validate_allocation_request(kind, root, slug)
    numbers, duplicates = scan_allocated_numbers(
        resolved_root, _KIND_PREFIXES[kind]
    )
    number = max(numbers, default=0) + 1
    for _ in range(100):
        if number > 9999:
            raise ProductStateError("allocation number exceeds four digits")
        target = allocation_target(kind, resolved_root, number, slug)
        try:
            create_allocation(kind, target)
        except FileExistsError:
            number += 1
            continue
        except OSError as error:
            raise ProductStateError(f"{target}: {error}") from error
        return allocation_payload(kind, target, number, duplicates)
    raise ProductStateError("allocation failed after 100 conflicts")


def capability_cells(line: str, path: Path, line_number: int) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        raise ProductStateError(
            f"{path}: line {line_number}: capability row must be a Markdown table row"
        )
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def require_capability_value(
    row: dict[str, Any],
    field: str,
    choices: set[str],
    path: Path,
    line_number: int,
) -> None:
    value = row[field]
    if not isinstance(value, str) or value not in choices:
        raise ProductStateError(
            f"{path}: line {line_number}: {field} has unknown value {value!r}"
        )


def validate_capability_row(
    row: dict[str, Any], path: Path, line_number: int
) -> None:
    require_capability_value(
        row, "availability", _CAPABILITY_AVAILABILITIES, path, line_number
    )
    require_capability_value(
        row, "coverage", _CAPABILITY_COVERAGES, path, line_number
    )
    require_capability_value(
        row, "priority", _CAPABILITY_PRIORITIES, path, line_number
    )
    required_for = row["required_for"]
    if not isinstance(required_for, list):
        raise ProductStateError(
            f"{path}: line {line_number}: required_for must be a list"
        )
    for kind in required_for:
        if kind not in _PRODUCT_KINDS:
            raise ProductStateError(
                f"{path}: line {line_number}: required_for has unknown value {kind!r}"
            )


def parse_capability_matrix(path: Path) -> list[dict[str, Any]]:
    resolved = path.expanduser().resolve()
    try:
        with resolved.open("r", encoding="utf-8", newline="") as source:
            lines = source.read().splitlines()
    except (OSError, UnicodeError) as error:
        raise ProductStateError(f"{resolved}: {error}") from error

    section_index = next(
        (
            index
            for index, line in enumerate(lines)
            if re.match(r"^##\s+§9(?:\s|$)", line) is not None
        ),
        None,
    )
    if section_index is None:
        raise ProductStateError(f"{resolved}: section §9 is required")
    table_index = next(
        (
            index
            for index in range(section_index + 1, len(lines))
            if lines[index].strip()
        ),
        None,
    )
    if table_index is None or lines[table_index].startswith("## "):
        raise ProductStateError(f"{resolved}: section §9 capability table is required")
    header = capability_cells(lines[table_index], resolved, table_index + 1)
    if tuple(header) != _CAPABILITY_HEADERS:
        raise ProductStateError(
            f"{resolved}: line {table_index + 1}: capability table columns must be "
            f"{list(_CAPABILITY_HEADERS)}"
        )
    separator_index = table_index + 1
    if separator_index >= len(lines):
        raise ProductStateError(
            f"{resolved}: line {table_index + 1}: capability table separator is required"
        )
    separator = capability_cells(
        lines[separator_index], resolved, separator_index + 1
    )
    if len(separator) != len(_CAPABILITY_HEADERS) or any(
        re.fullmatch(r":?-{3,}:?", cell) is None for cell in separator
    ):
        raise ProductStateError(
            f"{resolved}: line {separator_index + 1}: invalid capability table separator"
        )

    rows: list[dict[str, Any]] = []
    for index in range(separator_index + 1, len(lines)):
        line = lines[index]
        if not line.strip() or line.startswith("## "):
            break
        cells = capability_cells(line, resolved, index + 1)
        if len(cells) != len(_CAPABILITY_FIELDS):
            raise ProductStateError(
                f"{resolved}: line {index + 1}: capability row must have "
                f"{len(_CAPABILITY_FIELDS)} columns"
            )
        row: dict[str, Any] = dict(zip(_CAPABILITY_FIELDS, cells, strict=True))
        row["required_for"] = [
            kind.strip() for kind in row["required_for"].split(",")
        ]
        validate_capability_row(row, resolved, index + 1)
        row["line"] = index + 1
        if not substantive_evidence(row["evidence"]):
            row["coverage"] = "unknown"
        rows.append(row)
    return rows


def substantive_evidence(evidence: str) -> str:
    without_comments = _HTML_COMMENT_PATTERN.sub(" ", evidence)
    return without_comments.replace(_DASH, "").strip()


def print_payload(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def parse_capabilities(path: Path) -> int:
    print_payload(parse_capability_matrix(path))
    return 0


def row_is_selectable(row: dict[str, Any]) -> bool:
    return row["availability"] == "available" and row["coverage"] in _COVERAGE_ORDER


def candidate_rank(row: dict[str, Any]) -> tuple[int, int]:
    return _COVERAGE_ORDER[row["coverage"]], _PRIORITY_ORDER[row["priority"]]


def base_rejection_reason(candidate: dict[str, Any]) -> str | None:
    if candidate["availability"] != "available":
        return f"availability-{candidate['availability']}"
    if not substantive_evidence(candidate["evidence"]):
        return "no-substantive-evidence"
    if candidate["coverage"] not in _COVERAGE_ORDER:
        return f"coverage-{candidate['coverage']}"
    return None


def rejection_reason(
    candidate: dict[str, Any], selected: dict[str, Any], pin: str | None
) -> str:
    if pin is not None and candidate["provider"] != pin:
        return "not-pinned-provider"
    base = base_rejection_reason(candidate)
    if base is not None:
        return base
    candidate_coverage = _COVERAGE_ORDER[candidate["coverage"]]
    selected_coverage = _COVERAGE_ORDER[selected["coverage"]]
    candidate_priority = _PRIORITY_ORDER[candidate["priority"]]
    selected_priority = _PRIORITY_ORDER[selected["priority"]]
    if selected_coverage < candidate_coverage:
        if selected_priority < candidate_priority:
            return f"higher-priority-{selected['coverage']}-provider"
        return "higher-coverage-provider"
    if selected_priority < candidate_priority:
        return f"higher-priority-{selected['coverage']}-provider"
    return "earlier-equivalent-provider"


def unselected_reason(candidate: dict[str, Any], pin: str | None) -> str:
    base = base_rejection_reason(candidate)
    if base is not None:
        return base
    if pin is not None and candidate["provider"] != pin:
        return "not-pinned-provider"
    return "unselectable"


def rejected_candidates(rows: list[dict[str, Any]], pin: str | None) -> str:
    if not rows:
        return "no candidate rows"
    return "; ".join(
        f"line {row['line']}: provider {row['provider']}: "
        f"{unselected_reason(row, pin)}"
        for row in rows
    )


def trace_candidate(
    row: dict[str, Any], selected: dict[str, Any], pin: str | None
) -> dict[str, Any]:
    is_selected = row is selected
    return {
        "availability": row["availability"],
        "capability": row["capability"],
        "coverage": row["coverage"],
        "evidence": row["evidence"],
        "line": row["line"],
        "priority": row["priority"],
        "provider": row["provider"],
        "rejected": None if is_selected else rejection_reason(row, selected, pin),
        "selected": is_selected,
    }


def capability_context_scanned_at(matrix: list[dict[str, Any]]) -> str | None:
    dates = [
        date
        for row in matrix
        for date in _DATE_MARKER_PATTERN.findall(row["evidence"])
    ]
    return max(dates, default=None)


def route_capabilities(
    path: Path, kind: str, pin: str | None = None
) -> dict[str, Any]:
    matrix = parse_capability_matrix(path)
    relevant = [row for row in matrix if kind in row["required_for"]]
    required = list(_REQUIRED_CAPABILITIES_BY_KIND[kind])
    for row in relevant:
        if row["capability"] not in required:
            required.append(row["capability"])
    selected_by_capability: dict[str, dict[str, Any]] = {}
    for capability in required:
        capability_rows = [
            row for row in relevant if row["capability"] == capability
        ]
        rejected = rejected_candidates(capability_rows, pin)
        if pin is not None:
            pinned_rows = [row for row in capability_rows if row["provider"] == pin]
            if not pinned_rows:
                raise ProductStateError(
                    f"{path.expanduser().resolve()}: pinned provider {pin!r} is absent "
                    f"for required capability {capability!r}: {rejected}"
                )
            available_pinned = [
                row for row in pinned_rows if row["availability"] == "available"
            ]
            if not available_pinned:
                statuses = sorted({row["availability"] for row in pinned_rows})
                raise ProductStateError(
                    f"{path.expanduser().resolve()}: pinned provider {pin!r} is "
                    f"unavailable for required capability {capability!r}: {statuses}; "
                    f"{rejected}"
                )
            selectable = [row for row in available_pinned if row_is_selectable(row)]
            if not selectable:
                raise ProductStateError(
                    f"{path.expanduser().resolve()}: pinned provider {pin!r} does "
                    f"not cover required capability {capability!r}: {rejected}"
                )
        else:
            selectable = [row for row in capability_rows if row_is_selectable(row)]
            if not selectable:
                raise ProductStateError(
                    f"{path.expanduser().resolve()}: required capability "
                    f"{capability!r} is not covered: {rejected}"
                )
        selected_by_capability[capability] = min(selectable, key=candidate_rank)

    candidates = [
        trace_candidate(row, selected_by_capability[row["capability"]], pin)
        for row in relevant
    ]
    selected_rows = list(selected_by_capability.values())
    limitations = list(
        dict.fromkeys(
            row["limitations"]
            for row in selected_rows
            if row["limitations"] not in {"", "—"}
        )
    )
    return {
        "candidates": candidates,
        "context_scanned_at": capability_context_scanned_at(matrix),
        "fallback_used": any(row["priority"] == "builtin" for row in selected_rows),
        "for": kind,
        "limitations": limitations,
        "required": required,
        "writer": "planner",
    }


def route(path: Path, kind: str, pin: str | None = None) -> int:
    print_payload(route_capabilities(path, kind, pin))
    return 0


def inspect_document(path: Path) -> int:
    print_payload(document_state(read_document(path)))
    return 0


def read_response_draft(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ProductStateError(f"{path}: {error}") from error
    try:
        draft = json.loads(text)
    except json.JSONDecodeError as error:
        raise ProductStateError(
            f"{path}: provider response is not valid JSON: {error}"
        ) from error
    if not isinstance(draft, dict):
        raise ProductStateError(f"{path}: provider response must be a JSON object")
    return draft


def validate_response_field_names(
    draft: dict[str, Any], kind: str, path: Path
) -> None:
    accepted = _RESPONSE_SHARED_FIELDS | _RESPONSE_FIELDS_BY_KIND[kind]
    known = _RESPONSE_SHARED_FIELDS.union(*_RESPONSE_FIELDS_BY_KIND.values())
    unknown = sorted(set(draft) - known)
    if unknown:
        raise ProductStateError(
            f"{path}: provider response has fields outside the contract: {unknown}"
        )
    foreign = sorted(set(draft) - accepted)
    if foreign:
        raise ProductStateError(
            f"{path}: provider response for {kind} carries fields of another "
            f"kind: {foreign}"
        )


def validate_response_field_types(draft: dict[str, Any], path: Path) -> None:
    for field, value in sorted(draft.items()):
        if field in _RESPONSE_LIST_FIELDS:
            if not isinstance(value, list) or not all(
                isinstance(item, str) for item in value
            ):
                raise ProductStateError(
                    f"{path}: {field} must be a list of text values"
                )
        elif not isinstance(value, str):
            raise ProductStateError(f"{path}: {field} must be a text value")


def response_field_content(value: str | list[str]) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [item for item in value if item.strip()]


def validate_response_completeness(draft: dict[str, Any], path: Path) -> None:
    empty = [
        field
        for field in _RESPONSE_REQUIRED_FIELDS
        if not response_field_content(draft.get(field, ""))
    ]
    if empty:
        raise ProductStateError(
            f"{path}: provider response is rejected, required fields are "
            f"missing or empty: {empty}"
        )


def reserve_lease() -> int:
    directory = Path(tempfile.mkdtemp(prefix=LEASE_DIRECTORY_PREFIX))
    print_payload({"path": str(directory / LEASE_FILE_NAME)})
    return 0


def require_lease_path(path: Path) -> Path:
    resolved = absolute_path(path)
    if resolved.name != LEASE_FILE_NAME:
        raise ProductStateError(
            f"{resolved}: draft lease file must be named {LEASE_FILE_NAME}"
        )
    temp_directory = Path(tempfile.gettempdir()).resolve()
    if (
        not resolved.parent.name.startswith(LEASE_DIRECTORY_PREFIX)
        or resolved.parent.parent != temp_directory
    ):
        raise ProductStateError(
            f"{resolved}: draft lease must be in a {LEASE_DIRECTORY_PREFIX}* "
            f"directory directly inside system temporary directory {temp_directory}"
        )
    return resolved


def cleanup_lease(path: Path) -> str | None:
    errors: list[str] = []
    try:
        if path.exists() or path.is_symlink():
            path.unlink()
    except OSError as error:
        errors.append(f"{path}: {error}")
    try:
        path.parent.rmdir()
    except OSError as error:
        errors.append(f"{path.parent}: {error}")
    return "; ".join(errors) or None


def release_lease(path: Path) -> int:
    resolved = require_lease_path(path)
    existed = resolved.exists() or resolved.is_symlink()
    cleanup_error = cleanup_lease(resolved)
    if cleanup_error is not None:
        raise ProductStateError(f"draft lease release failed: {cleanup_error}")
    print_payload(
        {"draft_existed": existed, "path": str(resolved), "removed": existed}
    )
    return 0


def check_response(path: Path, kind: str, consume: bool) -> int:
    resolved = require_lease_path(path) if consume else absolute_path(path)
    error: ProductStateError | None = None
    payload: dict[str, Any] | None = None
    try:
        draft = read_response_draft(resolved)
        validate_response_field_names(draft, kind, resolved)
        validate_response_field_types(draft, resolved)
        validate_response_completeness(draft, resolved)
        payload = {
            "accepted": True,
            "fields": sorted(draft),
            "for": kind,
            "limitations": response_field_content(draft["limitations"]),
            "path": str(resolved),
        }
    except ProductStateError as caught:
        error = caught
    if consume:
        cleanup_error = cleanup_lease(resolved)
        if error is not None:
            message = str(error)
            if cleanup_error is not None:
                message = f"{message}; draft cleanup failed: {cleanup_error}"
            raise ProductStateError(message) from error
        if cleanup_error is not None:
            raise ProductStateError(
                f"{resolved}: accepted but draft cleanup failed: {cleanup_error}"
            )
        payload["draft_removed"] = True
    if error is not None:
        raise error
    print_payload(payload)
    return 0


def build_parser() -> CliParser:
    parser = CliParser(prog="product_state.py")
    commands = parser.add_subparsers(
        dest="command", required=True, parser_class=CliParser
    )
    allocate_command = commands.add_parser("allocate")
    allocate_command.add_argument(
        "kind", choices=("idea", "epic", "roadmap", "feature")
    )
    allocate_command.add_argument("--root", type=Path, required=True)
    allocate_command.add_argument("--slug", required=True)
    allocate_command.add_argument("--json", action="store_true")

    target_command = commands.add_parser("validate-target")
    target_command.add_argument(
        "kind", choices=("idea", "epic", "roadmap", "feature")
    )
    target_command.add_argument("path", type=Path)
    target_command.add_argument("--directory", type=Path, required=True)
    target_command.add_argument("--parent", type=Path)

    inspect_command = commands.add_parser("inspect")
    inspect_command.add_argument("path", type=Path)

    capabilities_command = commands.add_parser("parse-capabilities")
    capabilities_command.add_argument("context_path", type=Path)

    route_command = commands.add_parser("route")
    route_command.add_argument("context_path", type=Path)
    route_command.add_argument(
        "--for",
        dest="product_kind",
        choices=("idea", "epic", "roadmap", "feature"),
        required=True,
    )
    route_command.add_argument("--pin")

    check_command = commands.add_parser("check")
    check_command.add_argument("path", type=Path)
    check_command.add_argument("--mark-stale", action="store_true")

    response_command = commands.add_parser("check-response")
    response_command.add_argument("path", type=Path)
    response_command.add_argument(
        "--for",
        dest="product_kind",
        choices=("idea", "epic", "roadmap", "feature"),
        required=True,
    )
    response_command.add_argument("--consume", action="store_true")

    commands.add_parser("reserve-response-draft")

    release_lease_command = commands.add_parser("release-response-draft")
    release_lease_command.add_argument("path", type=Path)

    sync_command = commands.add_parser("sync")
    sync_command.add_argument(
        "kind", choices=("idea", "epic", "roadmap", "feature")
    )
    sync_command.add_argument("path", type=Path)
    sync_command.add_argument("--body-file", type=Path, required=True)
    sync_command.add_argument(
        "--semantic-change", choices=("yes", "no"), required=True
    )
    sync_command.add_argument("--parent", type=Path)
    sync_command.add_argument("--stage")
    sync_command.add_argument("--outcome")
    sync_command.add_argument("--target")
    sync_command.add_argument("--readiness")
    sync_command.add_argument("--state")
    return parser


def validate_sync_field_ownership(kind: str, options: argparse.Namespace) -> None:
    unexpected = [
        field
        for field in _SYNC_FIELD_NAMES
        if field not in _SYNC_FIELDS_BY_KIND[kind]
        and getattr(options, field) is not None
    ]
    if unexpected:
        raise ProductStateError(
            f"sync {kind} does not accept fields from another kind: {unexpected}"
        )


def run(arguments: list[str] | None = None) -> int:
    options = build_parser().parse_args(arguments)
    if options.command == "allocate":
        print_payload(allocate_artifact(options.kind, options.root, options.slug))
        return 0
    if options.command == "validate-target":
        return validate_target(
            options.kind, options.path, options.directory, options.parent
        )
    if options.command == "check":
        return check_document(options.path, options.mark_stale)
    if options.command == "check-response":
        return check_response(options.path, options.product_kind, options.consume)
    if options.command == "reserve-response-draft":
        return reserve_lease()
    if options.command == "release-response-draft":
        return release_lease(options.path)
    if options.command == "parse-capabilities":
        return parse_capabilities(options.context_path)
    if options.command == "route":
        return route(options.context_path, options.product_kind, options.pin)
    if options.command == "sync":
        validate_sync_field_ownership(options.kind, options)
        if options.kind == "idea":
            return sync_idea_document(
                options.path,
                options.body_file,
                options.semantic_change == "yes",
                options.stage,
                options.outcome,
                options.target,
            )
        field_value = {
            "epic": options.stage,
            "roadmap": options.state,
            "feature": options.readiness,
        }[options.kind]
        return sync_linked_document(
            options.kind,
            options.path,
            options.body_file,
            options.semantic_change == "yes",
            options.parent,
            field_value,
        )
    return inspect_document(options.path)


def main() -> int:
    try:
        return run()
    except ProductStateError as error:
        print(f"product_state: {error}", file=sys.stderr)
        return EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
