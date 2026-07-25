#!/bin/bash
# TriGuard pre-demo ritual (WSL). One command = demo-ready real server.
#
#   wsl -e bash /mnt/c/dev/triguard/scripts/demo_up.sh
#
# Does, in order: kill orphan servers on the demo port, start Ollama if it is
# not running, boot the real-backend API (USE_TF=0 + hf/blip/real + OCR),
# warm llama3 (30m keep_alive) and the perception models with one real preset,
# then print a green/red checklist. Idempotent — safe to run twice.
set -u
cd "$(dirname "$0")/.."   # repo root, so relative data/ and outputs/ resolve

PORT="${TRIGUARD_DEMO_PORT:-8006}"
OLLAMA_MODEL_TAG="${TRIGUARD_OLLAMA_MODEL:-llama3:8b-instruct-q4_K_M}"
PY=~/.venv-tri/bin/python
UVICORN=~/.venv-tri/bin/uvicorn

pass() { echo "  [OK]   $1"; }
fail() { echo "  [FAIL] $1"; FAILED=1; }
FAILED=0

echo "== TriGuard demo_up =="

# 1. Clear the port (orphan uvicorn from an earlier session keeps serving
#    stale code and blocks the new bind).
if pkill -f "uvicorn triguard.api.main.*--port $PORT" 2>/dev/null; then
  echo "  killed orphan uvicorn on :$PORT"; sleep 1
fi

# 2. Ollama up (no autostart exists — a reboot leaves it down).
if ! curl -s -m 2 http://127.0.0.1:11434/api/tags >/dev/null; then
  export PATH="$HOME/ollama/bin:$PATH"
  nohup ollama serve >/tmp/ollama_serve.log 2>&1 & disown
  for i in $(seq 1 20); do
    curl -s -m 2 http://127.0.0.1:11434/api/tags >/dev/null && break
    sleep 1
  done
fi
curl -s -m 2 http://127.0.0.1:11434/api/tags >/dev/null \
  && pass "Ollama serving" || fail "Ollama unreachable (llama3 segments will fall back to rule)"

# 3. Warm llama3 into VRAM with a long keep_alive (avoids 30-50s mid-demo reload).
curl -s -m 300 http://127.0.0.1:11434/api/generate \
  -d "{\"model\":\"$OLLAMA_MODEL_TAG\",\"prompt\":\"ok\",\"stream\":false,\"keep_alive\":\"60m\"}" \
  >/dev/null && pass "llama3 warm (keep_alive 60m)" || fail "llama3 warm-up failed"

# 4. Boot the real-backend server. USE_TF=0 is MANDATORY here (D-016: without
#    it transformers imports TensorFlow and the first toxic-bert call
#    segfaults the whole server).
USE_TF=0 TRIGUARD_TEXT_BACKEND=hf TRIGUARD_IMAGE_BACKEND=blip \
TRIGUARD_AUDIO_BACKEND=real TRIGUARD_IMAGE_OCR=1 OLLAMA_TIMEOUT=300 \
PYTHONPATH=src nohup "$UVICORN" triguard.api.main:app \
  --host 127.0.0.1 --port "$PORT" >/tmp/tg_demo.log 2>&1 & disown

for i in $(seq 1 30); do
  curl -s -m 2 "http://127.0.0.1:$PORT/" >/dev/null && break
  sleep 1
done
HEALTH=$(curl -s -m 5 "http://127.0.0.1:$PORT/")
echo "$HEALTH" | grep -q '"status": *"ok"' \
  && pass "API serving on :$PORT" || fail "API did not come up (see /tmp/tg_demo.log)"
echo "$HEALTH" | grep -q '"text": *"hf"' \
  && pass "real backends confirmed via health endpoint" \
  || fail "health endpoint does not show real backends — wrong env?"

# 5. Warm the perception models (first real request costs ~30s; pay it now).
WARM=$(curl -s -m 300 -X POST "http://127.0.0.1:$PORT/analyse/preset" \
  -H 'Content-Type: application/json' -d '{"name":"multimodal_real"}')
echo "$WARM" | grep -q 'real-hf' \
  && pass "perception warm (toxic-bert/BLIP/Whisper loaded)" \
  || fail "perception warm-up did not report real-hf"

# 6. One warm llama3 judgement through the API (compare path end-to-end).
CMP=$(curl -s -m 300 -X POST "http://127.0.0.1:$PORT/analyse/compare" \
  -F 'text=demo warm-up sentence, nothing to see')
echo "$CMP" | grep -q '"judge_label": *"ollama"' \
  && pass "llama3 judging via API (label: ollama)" \
  || fail "compare fell back to rule (check Ollama)"

echo
if [ "$FAILED" -eq 0 ]; then
  echo "ALL GREEN — open http://127.0.0.1:$PORT/ui  (dashboard: /dashboard)"
else
  echo "SOMETHING RED — fix before going on stage. Logs: /tmp/tg_demo.log /tmp/ollama_serve.log"
fi
exit "$FAILED"
