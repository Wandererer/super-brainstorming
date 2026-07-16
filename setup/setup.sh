#!/usr/bin/env bash
# First-run setup for super-brainstorming. Idempotent, non-blocking.
#   setup.sh            -> first-run marker only. SILENT: no star prompt.
#                          Used by skill / auto-trigger Step 0 (output is discarded).
#   setup.sh ask        -> same first-run setup, then — iff no star decision is on record —
#                          atomically records an "asked" marker AND prints "STAR_ASK <lang>".
#                          Recording the marker HERE (not via a model follow-up) guarantees
#                          the question is shown at most once per plugin, even if the caller
#                          never reports the answer back. <lang> is a best-effort fallback
#                          language code (ko/ja/en) derived from the shell locale ($LC_ALL/$LANG)
#                          — used only when the live conversation has no signal.
#   setup.sh star yes   -> record "yes" and star the repo.
#   setup.sh star no    -> record "no"; star nothing.
# The star question itself is asked by the command flow (AskUserQuestion is Claude-only and
# cannot be issued from bash); this script never stars without an explicit "star yes".
set -uo pipefail

PLUGIN="super-brainstorming"
OWN_REPO="Wandererer/super-brainstorming"

MARKER_DIR="$HOME/.super-brainstorming-setup"
SETUP_MARKER="$MARKER_DIR/$PLUGIN.json"
STAR_MARKER="$MARKER_DIR/$PLUGIN.star.json"
mkdir -p "$MARKER_DIR"

# --- detect a fallback UI language from the shell locale (best-effort) ---
# Maps $LC_ALL / $LANG (e.g. ko_KR.UTF-8) to ko/ja/en. Used only as a fallback for the
# one-time star prompt, when the live conversation gives no language signal.
detect_lang() {
  case "${LC_ALL:-${LANG:-}}" in
    ko*) echo ko ;;
    ja*) echo ja ;;
    *)   echo en ;;
  esac
}

# --- record the star decision (and star the repo on "yes") ---
write_star() {  # $1 = decision (yes|no|asked)
  ts=$(date +%s 2>/dev/null || echo 0)
  printf '{"star_decision":"%s","plugin":"%s","ts":%s}\n' "$1" "$PLUGIN" "$ts" > "$STAR_MARKER"
}

if [ "${1:-}" = "star" ]; then
  DECISION="${2:-no}"
  write_star "$DECISION"
  if [ "$DECISION" = "yes" ] && command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    gh api "user/starred/$OWN_REPO" >/dev/null 2>&1 || gh api -X PUT "user/starred/$OWN_REPO" >/dev/null 2>&1 || true
  fi
  exit 0
fi

# --- first-run marker (silent, once per machine) ---
if [ ! -f "$SETUP_MARKER" ]; then
  ts=$(date +%s 2>/dev/null || echo 0)
  printf '{"setup":true,"plugin":"%s","ts":%s}\n' "$PLUGIN" "$ts" > "$SETUP_MARKER"
fi

# --- ask mode: emit the star prompt EXACTLY ONCE, recording it deterministically ---
# Only the command flow passes "ask". Bare / silent skill invocations never reach here,
# so they neither prompt nor record — the prompt is shown at most once, by a command,
# and the "asked" marker is written by bash regardless of any model follow-up.
if [ "${1:-}" = "ask" ] && [ ! -f "$STAR_MARKER" ]; then
  write_star "asked"
  echo "STAR_ASK $(detect_lang)"
fi
exit 0
