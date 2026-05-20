#!/usr/bin/env bash
# v0.3 lint-cleanup — fix the ruff failures introduced by M1 + M2 patches.
# Run AFTER M1 and M2 are installed. Idempotent.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_LABEL="v0.3 lint-cleanup — ruff compliance for M1 + M2"

say() { printf "%s\n" "$*"; }
die() { printf "ERROR: %s\n" "$*" >&2; exit 1; }

DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      cat <<EOF
Usage: $(basename "$0") [--dry-run]

Apply the ruff-compliance fixes for M1 + M2 patches:
  - I001 import sorting in orchestrator/main.py (AutoApprover, TYPE_CHECKING)
  - UP017 datetime.UTC alias in M1's channel tests
  - UP037 quoted annotations in orchestrator/main.py
  - F401 channels re-exports in sovereign_agent/__init__.py
EOF
      exit 0
      ;;
  esac
done

# Find repo root (same logic as the module installers)
find_repo_root() {
  local d
  for d in "$PWD" "$HERE"; do
    while [[ "$d" != "/" ]]; do
      if [[ -f "$d/pyproject.toml" ]] && { [[ -d "$d/sovereign_agent" ]] || [[ -d "$d/src/sovereign_agent" ]]; }; then
        echo "$d"; return 0
      fi
      d="$(dirname "$d")"
    done
  done
  return 1
}
REPO_ROOT="$(find_repo_root || true)"
[[ -z "$REPO_ROOT" ]] && die "could not find the sovereign-agent repository root."
cd "$REPO_ROOT"

# Detect layout
if [[ -d "$REPO_ROOT/src/sovereign_agent" ]]; then
  PKG_ROOT="src/sovereign_agent"; LAYOUT="src layout  (package at $PKG_ROOT/)"
elif [[ -d "$REPO_ROOT/sovereign_agent" ]]; then
  PKG_ROOT="sovereign_agent"; LAYOUT="flat layout  (package at $PKG_ROOT/)"
else
  die "no sovereign_agent package directory found at $REPO_ROOT"
fi

say "-----------------------------------------------------------------"
say "${MODULE_LABEL}"
say "-----------------------------------------------------------------"
say "Repository root: $REPO_ROOT"
say "Package layout:  $LAYOUT"

[[ ! -d ".git" ]] && die "$REPO_ROOT is not a git repository."

if [[ $DRY_RUN -eq 1 ]]; then
  say
  say "DRY RUN — running patcher without writing"
  SA_PKG_ROOT="$PKG_ROOT" python3 - <<'PY'
import os, sys
sys.path.insert(0, os.environ["HERE"] if "HERE" in os.environ else ".")
PY
  # Actually a real dry-run inspection
  SA_PKG_ROOT="$PKG_ROOT" python3 "$HERE/patch_lint_cleanup.py" --dry-run 2>/dev/null || \
    SA_PKG_ROOT="$PKG_ROOT" python3 -c "
import os, sys
sys.path.insert(0, '$HERE')
os.environ['SA_PKG_ROOT'] = '$PKG_ROOT'
import patch_lint_cleanup as m
for p in m.ALL_PATCHES:
    exists = p.path.exists()
    has_marker = exists and p.marker in p.path.read_text(encoding='utf-8')
    has_anchor = exists and p.anchor in p.path.read_text(encoding='utf-8')
    state = 'absent' if not exists else ('skipped' if has_marker else ('applied' if has_anchor else 'NO ANCHOR'))
    print(f'  {state:>10}  {p.label}')
"
  exit 0
fi

# Apply
say
SA_PKG_ROOT="$PKG_ROOT" python3 "$HERE/patch_lint_cleanup.py"

# Compile-check
say
say "Syntax check (py_compile):"
FAIL=0
for f in \
  "$PKG_ROOT/orchestrator/main.py" \
  "$PKG_ROOT/__init__.py" \
  "tests/test_channels_protocol.py" \
  "tests/test_channels_router.py" \
  "tests/test_channels_integration.py" \
  "tests/test_channels_cli.py" \
  "tests/test_engage_modes.py" ; do
  if [[ -f "$REPO_ROOT/$f" ]]; then
    if ! python3 -m py_compile "$REPO_ROOT/$f" 2>/dev/null; then
      say "  FAIL: $f"; FAIL=1
    fi
  fi
done
[[ $FAIL -eq 1 ]] && die "one or more files failed py_compile."
say "  ok — all files compile."

# Run ruff format + ruff check --fix to canonicalize what the patcher wrote.
# Anchored string-replace can't account for blank lines between blocks or
# trailing-comma style — let ruff do its job after the structural edits.
say
say "Canonicalizing with ruff (format + autofix):"
RUFF=""
if command -v ruff >/dev/null 2>&1; then
  RUFF="ruff"
elif command -v uv >/dev/null 2>&1 && uv run --quiet ruff --version >/dev/null 2>&1; then
  RUFF="uv run --quiet ruff"
fi
if [[ -n "$RUFF" ]]; then
  $RUFF format "$PKG_ROOT/__init__.py" "$PKG_ROOT/orchestrator/main.py" tests/ 2>&1 | sed 's/^/  /'
  $RUFF check --fix "$PKG_ROOT/__init__.py" "$PKG_ROOT/orchestrator/main.py" tests/ 2>&1 | sed 's/^/  /'
  if $RUFF check "$PKG_ROOT/__init__.py" "$PKG_ROOT/orchestrator/main.py" tests/ 2>&1; then
    say "  ok — ruff clean."
  else
    say "  warn — ruff still reports issues (see above)."
  fi
else
  say "  ruff not found (and uv not on PATH either). Run 'uv run ruff format ...' yourself."
fi

say
say "-----------------------------------------------------------------"
say "Done. Review 'git diff' and commit (suggested message):"
say "  chore: fix ruff lint after v0.3 M1+M2 patches (I001, UP017, UP037, F401)"
say "-----------------------------------------------------------------"
