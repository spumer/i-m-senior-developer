"""Чистый разбор объявленных выходов плана из Markdown-тела.

Принимает Markdown-тело плана, возвращает нормализованные пути и счётчики
синтаксически отклонённых кандидатов. Файловой системы и git здесь нет.
"""

from __future__ import annotations

import re
from typing import Dict, List

FIELD_LABELS = (
    "Допустимые выходы",
    "Выходы",
    "Выход",
    "Allowed outputs",
    "Outputs",
    "Output",
)

_FIELD_LINE = re.compile(
    r"^\s*(?:[-*]\s+)?(?:\*\*)?\s*(" + "|".join(re.escape(label) for label in FIELD_LABELS) + r")\s*(?:\*\*)?\s*:(.*)$"
)
_HEADING = re.compile(r"^#{1,6}\s")
_LIST_ITEM = re.compile(r"^\s*[-*]\s+")
_CODE_SPANS = re.compile(r"`([^`]+)`")

_REJECTED_KEYS = ("bare_path", "absolute_path", "placeholder")


def _classify(candidate: str) -> str | None:
    if candidate.startswith("/") or candidate.startswith("~"):
        return "absolute_path"
    if any(mark in candidate for mark in ("*", "?", "[", "]", "<", ">", "\\")) or ".." in candidate.split("/"):
        return "placeholder"
    if "/" not in candidate:
        return "bare_path"
    return None


def _normalize(candidate: str) -> str:
    if candidate.startswith("./"):
        return candidate[2:]
    return candidate


def extract_outputs(body: str) -> Dict[str, object]:
    """Извлечь пути выходов и счётчики отклонённых кандидатов из тела плана."""
    paths: List[str] = []
    seen = set()
    rejected: Dict[str, int] = {key: 0 for key in _REJECTED_KEYS}

    in_outputs = False
    for line in body.splitlines():
        if _HEADING.match(line):
            in_outputs = False
            continue
        field_match = _FIELD_LINE.match(line)
        if field_match is not None:
            label = field_match.group(1)
            in_outputs = label in FIELD_LABELS
            if in_outputs:
                _collect(field_match.group(2), paths, seen, rejected)
            continue
        if in_outputs and (_LIST_ITEM.match(line) or not line.strip()):
            if line.strip():
                _collect(line, paths, seen, rejected)
            continue
        in_outputs = False

    return {"paths": paths, "rejected": rejected}


def _collect(text: str, paths: List[str], seen: set, rejected: Dict[str, int]) -> None:
    for match in _CODE_SPANS.finditer(text):
        candidate = match.group(1).strip()
        reason = _classify(candidate)
        if reason is not None:
            rejected[reason] += 1
            continue
        normalized = _normalize(candidate)
        if normalized not in seen:
            seen.add(normalized)
            paths.append(normalized)
