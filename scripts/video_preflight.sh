#!/usr/bin/env bash
# TriGuard final-video pre-flight (WSL, bash). READ-ONLY: curl + python3 +
# git status only. Run AFTER scripts/demo_up.sh has printed ALL GREEN:
#
#   wsl -e bash /mnt/c/dev/triguard/scripts/video_preflight.sh
#
# Checks (see docs/Video_Shot_List_Final.md, pre-record checklist):
#   (a) GET :PORT/  pretty-printed; PASS/FAIL that backends.text=hf,
#       backends.image=blip, backends.audio=real, backends.ocr=true
#       (keys from src/triguard/api/main.py:85-100)
#   (b) `ollama ps` output; WARN (not FAIL) if the demo model tag is absent —
#       the Ollama-down fallback shot in the shot list then applies
#   (c) presence of each media file named in data/local_demo/README.txt
#       (WARN when missing: the presets then use the mock wrappers)
#   (d) FAIL if `git status --porcelain -- outputs/evaluation` is non-empty;
#       other modified/untracked repo paths are printed as INFO (keep WIP off screen)
#   (e) GET :PORT/eval/summary -> track -> file -> run -> committed -> config.judge
#   (f) exit non-zero on any FAIL
# It does not start or stop anything and never modifies scripts/demo_up.sh.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO" || exit 2

PORT="${TRIGUARD_DEMO_PORT:-8006}"
BASE="http://127.0.0.1:$PORT"
MODEL_TAG="${TRIGUARD_OLLAMA_MODEL:-llama3:8b-instruct-q4_K_M}"
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || { echo "  [FAIL] $PY not found"; exit 2; }

FAILS=0; WARNS=0
pass() { echo "  [PASS] $1"; }
fail() { echo "  [FAIL] $1"; FAILS=$((FAILS+1)); }
warn() { echo "  [WARN] $1"; WARNS=$((WARNS+1)); }
info() { echo "  [INFO] $1"; }

echo "== TriGuard video_preflight ($BASE) =="

# (a) health endpoint ------------------------------------------------------
echo "-- (a) health: GET $BASE/"
HEALTH="$(curl -s -m 5 "$BASE/")"
if [ -z "$HEALTH" ]; then
  fail "health endpoint unreachable on :$PORT (run scripts/demo_up.sh first)"
else
  printf '%s' "$HEALTH" | "$PY" -m json.tool 2>/dev/null | sed 's/^/      /' \
    || info "health body is not JSON: $HEALTH"
  # One line per key: key<TAB>expected<TAB>actual<TAB>ok
  printf '%s' "$HEALTH" | "$PY" -c '
import json, sys
try:
    h = json.load(sys.stdin)
except Exception as e:
    print("parse\t-\t%s\tno" % e); sys.exit(0)
b = h.get("backends") or {}
want = {"text": "hf", "image": "blip", "audio": "real", "ocr": True}
for k, exp in want.items():
    act = b.get(k)
    print("%s\t%s\t%s\t%s" % (k, exp, act, "yes" if act == exp else "no"))
' | while IFS=$'\t' read -r key exp act ok; do
    if [ "$ok" = "yes" ]; then pass "backends.$key = $act"
    else fail "backends.$key = $act (expected $exp)"; fi
  done
  # The while-loop ran in a subshell; recount FAILs from the same data.
  BAD="$(printf '%s' "$HEALTH" | "$PY" -c '
import json, sys
try:
    b = (json.load(sys.stdin).get("backends") or {})
except Exception:
    print(4); sys.exit(0)
want = {"text": "hf", "image": "blip", "audio": "real", "ocr": True}
print(sum(1 for k, v in want.items() if b.get(k) != v))
')"
  FAILS=$((FAILS + BAD))
fi

# (b) ollama ps ------------------------------------------------------------
echo "-- (b) ollama ps"
OLLAMA_BIN="$(command -v ollama 2>/dev/null || true)"
[ -z "$OLLAMA_BIN" ] && [ -x "$HOME/ollama/bin/ollama" ] && OLLAMA_BIN="$HOME/ollama/bin/ollama"
if [ -z "$OLLAMA_BIN" ]; then
  warn "ollama binary not found (PATH, \$HOME/ollama/bin) — cannot list resident models"
else
  PS_OUT="$("$OLLAMA_BIN" ps 2>&1)"
  printf '%s\n' "$PS_OUT" | sed 's/^/      /'
  if printf '%s' "$PS_OUT" | grep -q -- "$MODEL_TAG"; then
    pass "$MODEL_TAG resident (keep_alive: demo_up.sh warm-up 60m, app judge default 30m)"
  else
    warn "$MODEL_TAG not listed by ollama ps — llama3 shots will fall back to ollama->rule (see fallback shot)"
  fi
fi

# (c) local demo media -----------------------------------------------------
echo "-- (c) data/local_demo media named in README.txt"
README="data/local_demo/README.txt"
if [ ! -f "$README" ]; then
  warn "$README missing"
else
  NAMES="$(grep -oE '^[[:space:]]+[A-Za-z0-9_.-]+\.(jpg|jpeg|png|wav|mp3)' "$README" | tr -d ' \t' || true)"
  if [ -z "$NAMES" ]; then
    warn "no media names parsed from $README"
  fi
  for n in $NAMES; do
    if [ -f "data/local_demo/$n" ]; then pass "present: data/local_demo/$n"
    else warn "missing: data/local_demo/$n (preset falls back to mock wrappers for that modality)"; fi
  done
fi

# (d) git status -----------------------------------------------------------
echo "-- (d) git status --porcelain -- outputs/evaluation"
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  fail "not a git work tree: $REPO"
else
  EVAL_STATUS="$(git status --porcelain -- outputs/evaluation)"
  if [ -n "$EVAL_STATUS" ]; then
    printf '%s\n' "$EVAL_STATUS" | sed 's/^/      /'
    fail "outputs/evaluation has uncommitted changes (dashboard may show UNCOMMITTED RUN; commit or remove deliberately)"
  else
    pass "outputs/evaluation clean"
  fi
  WIP="$(git status --porcelain | grep -v ' outputs/evaluation' || true)"
  if [ -n "$WIP" ]; then
    info "other modified/untracked paths (keep off screen):"
    printf '%s\n' "$WIP" | sed 's/^/      /'
  else
    info "no other WIP in the working tree"
  fi
fi

# (e) eval summary ---------------------------------------------------------
echo "-- (e) GET $BASE/eval/summary  (track -> file -> run -> committed -> config.judge)"
SUMMARY="$(curl -s -m 10 "$BASE/eval/summary")"
if [ -z "$SUMMARY" ]; then
  fail "/eval/summary unreachable"
else
  printf '%s' "$SUMMARY" | "$PY" -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception as e:
    print("FAIL\tsummary not JSON: %s" % e); sys.exit(0)
if not d.get("available"):
    print("FAIL\tsummary unavailable: %s" % d.get("reason")); sys.exit(0)
def row(track, e):
    data = e.get("data") or {}
    judge = (data.get("config") or {}).get("judge")
    if judge is None and track == "t7":
        judge = data.get("judge")
    print("ROW\t%s -> %s -> %s -> committed=%s -> config.judge=%s"
          % (track, e.get("file"), e.get("run"), e.get("committed"), judge))
for track, e in sorted((d.get("tracks") or {}).items()):
    if "runs_by_backend" in e:
        for be, sub in sorted(e["runs_by_backend"].items()):
            row("%s[%s]" % (track, be), sub)
    elif "runs_by_config" in e:
        for cfg, sub in sorted(e["runs_by_config"].items()):
            row("%s[%s]" % (track, cfg), sub)
    else:
        row(track, e)
' | while IFS=$'\t' read -r kind rest; do
    case "$kind" in
      ROW) echo "      $rest" ;;
      FAIL) echo "  [FAIL] $rest" ;;
    esac
  done
  if printf '%s' "$SUMMARY" | "$PY" -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("available") else 1)' 2>/dev/null; then
    pass "/eval/summary available"
  else
    fail "/eval/summary not available"
  fi
fi

# (f) verdict --------------------------------------------------------------
echo
echo "PREFLIGHT: $FAILS FAIL, $WARNS WARN"
if [ "$FAILS" -eq 0 ]; then
  echo "GO — record per docs/Video_Shot_List_Final.md"
  exit 0
fi
echo "NO-GO — fix the [FAIL] lines above"
exit 1
