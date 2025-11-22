#!/usr/bin/env bash
set -euo pipefail

# command-line flags
DRY_RUN=0
CONTINUE_ON_ERROR=0
VERBOSE=0
ISSUES_JSON=${ISSUES_JSON:-data/issues.json}
while [[ ${1:-} != "" ]]; do
  case "$1" in
    --dry-run|-n)
      DRY_RUN=1
      shift
      ;;
    --verbose|-v)
      VERBOSE=1
      shift
      ;;
    --continue-on-error)
      CONTINUE_ON_ERROR=1
      shift
      ;;
    --file|-f)
      ISSUES_JSON="${2:-}"
      if [[ -z "$ISSUES_JSON" ]]; then
        echo "Missing value for --file" >&2
        exit 2
      fi
      shift 2
      ;;
    --help|-h)
      cat <<'USAGE'
Usage: create_issues.sh [--dry-run] [--file PATH]

Options:
  --dry-run, -n         Print the gh command(s) that would be executed instead of running them
  --continue-on-error   Do not stop on a failed issue creation (logs the error and continues)
  --verbose, -v         Verbose logging for each issue payload/command
  --file, -f PATH       Path to issues JSON (default: data/issues.json or $ISSUES_JSON)
  --help, -h            Show this help
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

if [ ! -f "$ISSUES_JSON" ]; then
  echo "issues file not found: $ISSUES_JSON" >&2
  exit 1
fi
# Avoid aborting the whole script on a single per-issue failure inside the pipeline
set +e
set +o pipefail

# iterate JSON objects safely
$JQ -c '.[]' "$ISSUES_JSON" | awk 'BEGIN{c=0} {print ++c "|" $0}' | while IFS='|' read -r idx row; do
  title=$($JQ -r '.title // empty' <<<"$row")
  body=$($JQ -r '.body // empty' <<<"$row")

  if [ "$VERBOSE" -eq 1 ]; then
    echo "Processing #$idx: $title"
  fi

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

  # projects: allow "project": "Roadmap" or "projects": ["Roadmap","Another"]
  projects_type=$($JQ -r 'if has("projects") then (.projects | type) else "none" end' <<<"$row")
  if [ "$projects_type" = "array" ]; then
    while IFS= read -r proj; do
      [ -z "$proj" ] && continue
      cmd+=(--project "$proj")
    done < <($JQ -r '.projects[]' <<<"$row")
  elif [ "$projects_type" = "string" ]; then
    proj=$($JQ -r '.projects' <<<"$row")
    if [ -n "$proj" ] && [ "$proj" != "null" ]; then
      cmd+=(--project "$proj")
    fi
  elif $JQ -e 'has("project")' >/dev/null 2>&1 <<<"$row"; then
    proj=$($JQ -r '.project // empty' <<<"$row")
    if [ -n "$proj" ]; then
      cmd+=(--project "$proj")
    fi
  fi

  # assignees: support "assignee": "user" or "assignees": ["user1","user2"]
  assignees_type=$($JQ -r 'if has("assignees") then (.assignees | type) else "none" end' <<<"$row")
  if [ "$assignees_type" = "array" ]; then
    while IFS= read -r assignee; do
      [ -z "$assignee" ] && continue
      cmd+=(--assignee "$assignee")
    done < <($JQ -r '.assignees[]' <<<"$row")
  elif [ "$assignees_type" = "string" ]; then
    assignee=$($JQ -r '.assignees' <<<"$row")
    if [ -n "$assignee" ] && [ "$assignee" != "null" ]; then
      cmd+=(--assignee "$assignee")
    fi
  elif $JQ -e 'has("assignee")' >/dev/null 2>&1 <<<"$row"; then
    assignee=$($JQ -r '.assignee // empty' <<<"$row")
    if [ -n "$assignee" ]; then
      cmd+=(--assignee "$assignee")
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
    # allow command substitution to capture stderr without aborting on non-zero
    out=$("${cmd[@]}" 2>&1)
    status=$?
    if [ $status -eq 0 ]; then
      echo "Created: $title -> $out"
    else
      if [ "$CONTINUE_ON_ERROR" -eq 1 ]; then
        echo "Issue creation failed for title: $title (idx=$idx)" >&2
        echo "Payload: $row" >&2
        echo "Error: $out" >&2
        continue
      else
        echo "Issue creation failed for title: $title (idx=$idx)" >&2
        echo "Payload: $row" >&2
        echo "Error: $out" >&2
        exit 1
      fi
    fi
  fi
done

# Restore strict modes after pipeline
set -euo pipefail
