#!/usr/bin/env bash
set -euo pipefail

# command-line flags
DRY_RUN=0
while [[ ${1:-} != "" ]]; do
  case "$1" in
    --dry-run|-n)
      DRY_RUN=1
      shift
      ;;
    --help|-h)
      cat <<'USAGE'
Usage: create_issues.sh [--dry-run]

Options:
  --dry-run, -n   Print the gh command(s) that would be executed instead of running them
  --help, -h      Show this help
USAGE
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

# Allow overrides via environment variables (useful for CI or non-standard locations)
JQ=${JQ_CMD:-}
GH=${GH_CMD:-}

# locate jq if not overridden
if [ -z "${JQ:-}" ]; then
  if command -v jq >/dev/null 2>&1; then
    JQ=jq
  else
    echo "jq not found in PATH. Please install jq (e.g. WSL: 'sudo apt install jq', Windows: choco/scoop)" >&2
    exit 1
  fi
fi

# locate gh (GitHub CLI). prefer in-PATH; fallback to common Windows locations when running under WSL/Git-Bash
if [ -z "${GH:-}" ]; then
  if command -v gh >/dev/null 2>&1; then
    GH=gh
  else
    if [ -x "/mnt/c/Program Files/GitHub CLI/gh.exe" ]; then
      GH="/mnt/c/Program Files/GitHub CLI/gh.exe"
    elif [ -x "/c/Program Files/GitHub CLI/gh.exe" ]; then
      GH="/c/Program Files/GitHub CLI/gh.exe"
    else
      echo "gh (GitHub CLI) not found. Install gh in this environment or ensure it's on PATH." >&2
      echo " - WSL: see https://github.com/cli/cli#installation" >&2
      echo " - Windows: install GitHub CLI and make sure it's reachable from the bash session." >&2
      exit 1
    fi
  fi
fi

if [ ! -f issues.json ]; then
  echo "issues.json not found in $(pwd)" >&2
  exit 1
fi

# iterate JSON objects safely
$JQ -c '.[]' issues.json | while IFS= read -r row; do
  title=$($JQ -r '.title // empty' <<<"$row")
  body=$($JQ -r '.body // empty' <<<"$row")

  # build gh command as an array to handle spaces/newlines safely
  cmd=("${GH}" issue create)
  if [ -n "$title" ]; then
    cmd+=(--title "$title")
  fi
  if [ -n "$body" ]; then
    cmd+=(--body "$body")
  fi

  # labels: accept either an array or a single string
  labels_type=$($JQ -r 'if has("labels") then (.labels | type) else "none" end' <<<"$row")
  if [ "$labels_type" = "array" ]; then
    while IFS= read -r lab; do
      [ -z "$lab" ] && continue
      cmd+=(--label "$lab")
    done < <($JQ -r '.labels[]' <<<"$row")
  elif [ "$labels_type" = "string" ]; then
    lab=$($JQ -r '.labels' <<<"$row")
    if [ -n "$lab" ] && [ "$lab" != "null" ]; then
      cmd+=(--label "$lab")
    fi
  fi

  # milestone: optional string
  if $JQ -e 'has("milestone")' >/dev/null 2>&1 <<<"$row"; then
    milestone=$($JQ -r '.milestone // empty' <<<"$row")
    if [ -n "$milestone" ] && [ "$milestone" != "null" ]; then
      cmd+=(--milestone "$milestone")
    fi
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    # print a safely quoted version of the command
    printf 'DRY RUN: ' >&2
    for a in "${cmd[@]}"; do
      printf '%q ' "$a" >&2
    done
    printf '\n' >&2
  else
    "${cmd[@]}"
  fi
done
