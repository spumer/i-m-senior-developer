#!/usr/bin/env bash
# fetch-fpf-spec.sh — download FPF-Spec.md for the fpf-integration skill.
#
# Source: https://github.com/ailev/FPF (branch main, file FPF-Spec.md, ~8.7 MB).
# Default target: ~/.claude/knowledge/fpf/FPF-Spec.md (global — one copy for all
# projects, which is what the skill's dependency check looks for first).
#
# Usage:
#   fetch-fpf-spec.sh             # download to ~/.claude/knowledge/fpf/
#   fetch-fpf-spec.sh --project   # download to <cwd>/.claude/knowledge/fpf/
#   fetch-fpf-spec.sh --force     # overwrite if it already exists
#   fetch-fpf-spec.sh /custom/dir # download into a custom directory
set -euo pipefail

RAW_URL="https://raw.githubusercontent.com/ailev/FPF/main/FPF-Spec.md"
MIN_BYTES=1000000   # sanity floor: a real spec is multiple MB, not an error page

dest_dir="$HOME/.claude/knowledge/fpf"
force=0

while [ $# -gt 0 ]; do
  case "$1" in
    -p|--project) dest_dir="$PWD/.claude/knowledge/fpf" ;;
    -f|--force)   force=1 ;;
    -h|--help)    grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*)           echo "unknown option: $1" >&2; exit 2 ;;
    *)            dest_dir="$1" ;;
  esac
  shift
done

target="$dest_dir/FPF-Spec.md"

if [ -f "$target" ] && [ "$force" -eq 0 ]; then
  echo "FPF-Spec.md already present: $target"
  echo "($(wc -c < "$target") bytes). Use --force to re-download."
  exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "error: curl not found. Install curl or download manually:" >&2
  echo "  $RAW_URL -> $target" >&2
  exit 1
fi

mkdir -p "$dest_dir"
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

echo "Downloading FPF-Spec.md from $RAW_URL ..."
curl -fSL --retry 3 -o "$tmp" "$RAW_URL"

bytes="$(wc -c < "$tmp")"
if [ "$bytes" -lt "$MIN_BYTES" ]; then
  echo "error: downloaded file is only $bytes bytes — likely not the real spec." >&2
  echo "Check the URL/branch at https://github.com/ailev/FPF" >&2
  exit 1
fi

mv "$tmp" "$target"
trap - EXIT
echo "Done: $target ($bytes bytes)."
echo "The fpf-integration skill will now find it (global copy, used across projects)."
