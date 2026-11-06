#!/usr/bin/env bash
# Local multi-agent orchestrator. See CLAUDE.md for the flow.
# Usage: bash scripts/orchestrator.sh [--dry-run] [--card <id>] [--base <branch>]
# Env:   GEMINI_OPTIONAL=1 -> run without the Gemini review (QA agent only)
set -uo pipefail
cd "$(dirname "$0")/.."

DRY=0; ONLY=""; BASE=main; MAX=3
while [ $# -gt 0 ]; do
  case $1 in
    --dry-run) DRY=1 ;;
    --card) ONLY=${2:?--card needs an id}; shift ;;
    --base) BASE=${2:?--base needs a branch}; shift ;;
    *) echo "unknown arg: $1"; exit 2 ;;
  esac; shift
done

LOG=board/_log.md; TMP=board/.tmp
mkdir -p "$TMP"
[ -f "$LOG" ] || printf '| time | card | agent | result | duration |\n|---|---|---|---|---|\n' > "$LOG"

ts()   { date '+%F %T'; }
log()  { printf '| %s | %s | %s | %s | %ss |\n' "$(ts)" "$1" "$2" "$3" "$(( SECONDS - ${4:-SECONDS} ))" >> "$LOG"; echo "[$1] $2: $3"; }
field(){ sed -n "s/^$1: *//p" "$CARD" | head -1 | sed 's/ *#.*//'; }
note() { echo "- $(ts) $*" >> "$CARD"; }
verdict() { grep -E '^VERDICT: (APPROVED|REJECTED)' "$1" | tail -1 | awk '{print $2}'; }
marker()  { grep -E '^RESULT: (PLANNED|DONE|BLOCKED)' "$1" | tail -1 | awk '{print $2}'; }

# run a CLI, retrying with backoff on rate-limit/quota errors.
# rc: CLI's rc | 98 = auth problem | 99 = limit never cleared
run_cli() {
  local out=$1; shift; local n=0 rc w
  while :; do
    "$@" <"${STDIN_FILE:-/dev/null}" >"$out" 2>&1; rc=$?
    [ $rc -eq 0 ] && return 0
    if grep -qiE 'oauth|failed to authenticate|not logged in|please (run )?/?login|invalid api key' "$out"; then return 98; fi
    if grep -qiE 'rate.?limit|quota|usage limit|too many requests|429|resource.?exhausted|overloaded|limit reached' "$out"; then
      n=$((n+1)); [ $n -gt 8 ] && return 99
      w=$(( 60 * 2**(n-1) )); [ $w -gt 1800 ] && w=1800
      log "${ID:--}" "$1" "rate limit, waiting ${w}s (retry $n)" ; sleep $w; continue
    fi
    return $rc
  done
}

# park work in progress and return to the base branch
park() {
  if [ -n "$(git status --porcelain)" ]; then git add -A; git commit -qm "WIP card $ID (parked)"; fi
  git checkout -q "$BASE"
  [ "$(git rev-list --count "$BASE..$BR" 2>/dev/null)" = 0 ] && git branch -qd "$BR" 2>/dev/null
  return 0
}

retro() {
  STDIN_FILE= run_cli "$TMP/$ID.retro.txt" claude -p --agent retro --permission-mode acceptEdits \
    "Run the retrospective for card $CARD (status: $1)." && log "$ID" retro ok "$T0"
  git add memory; git diff --cached --quiet || git commit -qm "retro: lessons from card $ID"
}

block() {  # reason
  note "BLOCKED: $1"; log "$ID" orchestrator "blocked: $1" "$T0"
  mv "$CARD" board/blocked/; CARD=board/blocked/$ID.md
  park; retro blocked
}

abort() {  # rc stage : environment problem, put card back and stop everything
  local why="auth failure (run 'claude' / 'gemini' and log in)"; [ "$1" = 99 ] && why="rate limit did not clear"
  note "ABORT at $2: $why"; log "$ID" orchestrator "ABORT $2: $why" "$T0"
  mv "$CARD" board/backlog/; park; exit 1
}

cli() {  # agent outfile prompt  (aborts the run on auth/limit failure)
  run_cli "$2" claude -p --agent "$1" --permission-mode acceptEdits "$3"
  local rc=$?; [ $rc -ge 98 ] && abort $rc "$1"; return $rc
}

review_input() {  # card without plan/log + diff + ci tail -> file
  { echo "# CARD"; awk '/^## (Plan|Status log)/{s=1;next} /^## /{s=0} !s' "$CARD"
    echo; echo "# DIFF"; cat "$TMP/$ID.diff"
    echo; echo "# CI OUTPUT (tail)"; tail -n 60 "$TMP/$ID.ci.txt"; } > "$TMP/$ID.review.txt"
}

process() {
  CARD=$1; ID=$(basename "$CARD" .md); BR=card/$ID; T0=$SECONDS
  local AREA AGENT TITLE n t qa gm
  AREA=$(field area); AREA=${AREA:-backend}; TITLE=$(field title)
  AGENT=$AREA; [ "$AREA" = both ] && AGENT=backend
  if [ $DRY = 1 ]; then echo "[dry-run] $ID | area=$AREA agent=$AGENT | branch=$BR from $BASE | up to $MAX attempts, qa+gemini review"; return; fi

  mv "$CARD" board/doing/; CARD=board/doing/$ID.md
  sed -i "s/^attempts:.*/attempts: 0/" "$CARD"
  if git rev-parse -q --verify "$BR" >/dev/null; then
    git checkout -q "$BR" && { git merge -q --no-edit "$BASE" || { git merge --abort; block "branch $BR conflicts with $BASE"; return; }; }
  else git checkout -q -b "$BR" "$BASE"; fi
  note "started on $BR (base $BASE)"

  # PLAN
  t=$SECONDS
  cli "$AGENT" "$TMP/$ID.plan.txt" "PHASE=PLAN. Card: $CARD. Follow your agent instructions and CLAUDE.md." || true
  case "$(marker "$TMP/$ID.plan.txt")" in
    PLANNED) log "$ID" "$AGENT/plan" planned "$t"; note "plan written" ;;
    BLOCKED) log "$ID" "$AGENT/plan" blocked "$t"; block "vague or missing info, see Blockers / questions"; return ;;
    *)       log "$ID" "$AGENT/plan" "no RESULT marker" "$t"; block "planning gave no result, see $TMP/$ID.plan.txt"; return ;;
  esac

  : > "$TMP/$ID.feedback.txt"
  for n in $(seq 1 $MAX); do
    sed -i "s/^attempts:.*/attempts: $n/" "$CARD"
    # IMPLEMENT
    t=$SECONDS
    cli "$AGENT" "$TMP/$ID.impl$n.txt" "PHASE=IMPLEMENT, attempt $n of $MAX. Card: $CARD. Feedback from the previous attempt (empty on the first): $TMP/$ID.feedback.txt" || true
    if [ "$(marker "$TMP/$ID.impl$n.txt")" = BLOCKED ]; then log "$ID" "$AGENT/impl$n" blocked "$t"; block "implementer found missing info, see Blockers / questions"; return; fi
    log "$ID" "$AGENT/impl$n" done "$t"

    # CI
    t=$SECONDS
    if ! bash scripts/ci.sh > "$TMP/$ID.ci.txt" 2>&1; then
      log "$ID" ci "FAIL (attempt $n)" "$t"; note "attempt $n: CI failed"
      { echo "CI FAILED. Fix these:"; tail -n 80 "$TMP/$ID.ci.txt"; } > "$TMP/$ID.feedback.txt"; continue
    fi
    log "$ID" ci PASS "$t"

    # REVIEW (qa agent + gemini, independent of the implementer)
    git add -A; git diff --cached "$BASE" > "$TMP/$ID.diff"; review_input
    t=$SECONDS
    cli qa "$TMP/$ID.qa$n.txt" "Evaluate card $ID. Card (no plan/log): $TMP/$ID.review.txt contains the card, the diff and the CI tail. Follow your agent instructions." || true
    qa=$(verdict "$TMP/$ID.qa$n.txt"); qa=${qa:-REJECTED}; log "$ID" qa "$qa" "$t"

    t=$SECONDS
    if [ "${GEMINI_OPTIONAL:-0}" = 1 ] && ! command -v gemini >/dev/null; then gm=APPROVED; echo "gemini skipped (not installed)" > "$TMP/$ID.gemini$n.txt"; log "$ID" gemini "SKIPPED" "$t"
    else
      STDIN_FILE="$TMP/$ID.review.txt" run_cli "$TMP/$ID.gemini$n.txt" gemini -p "Review the card and diff on stdin following GEMINI.md exactly."
      case $? in 98|99) abort $? gemini ;; esac
      gm=$(verdict "$TMP/$ID.gemini$n.txt"); gm=${gm:-REJECTED}; log "$ID" gemini "$gm" "$t"
    fi

    if [ "$qa" = APPROVED ] && [ "$gm" = APPROVED ]; then
      git commit -qm "card $ID: $TITLE" -m "Approved by qa + gemini after $n attempt(s); CI green."
      git checkout -q "$BASE" && git merge -q --no-ff "$BR" -m "Merge card $ID: $TITLE" || { git merge --abort; block "merge into $BASE failed"; return; }
      note "APPROVED after $n attempt(s), merged into $BASE"
      mv "$CARD" board/done/; CARD=board/done/$ID.md
      log "$ID" orchestrator "done (merged into $BASE)" "$T0"; retro done; return
    fi
    note "attempt $n rejected (qa=$qa gemini=$gm)"
    { echo "REVIEW REJECTED. Fix these failures."; echo "## QA"; cat "$TMP/$ID.qa$n.txt"; echo "## GEMINI"; cat "$TMP/$ID.gemini$n.txt"; } > "$TMP/$ID.feedback.txt"
  done
  block "needs human: $MAX attempts exhausted"
}

main() {
  git rev-parse -q --verify "$BASE" >/dev/null || { echo "base branch '$BASE' not found"; exit 1; }
  if [ $DRY = 0 ]; then
    [ -z "$(git status --porcelain)" ] || { echo "working tree not clean; commit or stash first"; exit 1; }
    command -v claude >/dev/null || { echo "claude CLI not found"; exit 1; }
    command -v gemini >/dev/null || [ "${GEMINI_OPTIONAL:-0}" = 1 ] || { echo "gemini CLI not found (npm i -g @google/gemini-cli, or GEMINI_OPTIONAL=1)"; exit 1; }
    git checkout -q "$BASE"
  fi
  local f found=0
  for f in board/backlog/*.md; do
    [ -f "$f" ] || continue
    [ -z "$ONLY" ] || [ "$(basename "$f" .md)" = "$ONLY" ] || continue
    found=1; process "$f"
  done
  [ $found = 1 ] && echo "done. log: $LOG" || echo "nothing to do (backlog empty${ONLY:+ or card '$ONLY' not found})"
}
main; exit $?
