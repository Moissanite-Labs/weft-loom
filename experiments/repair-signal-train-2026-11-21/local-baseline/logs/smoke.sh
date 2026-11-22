#!/bin/sh
# Local smoke test: load Inkling 2 Mini, send two short requests, record timing and memory, stop the server.
set -u
D=${LLAMA_DIR:?set LLAMA_DIR to the folder that holds llama.cpp/build/bin/llama-server}
BIN=$D/llama.cpp/build/bin/llama-server
M=${MODEL_GGUF:?set MODEL_GGUF to the Inkling-2-Mini-Q8_0.gguf file}
LOG=$D/smoke-server.log
"$BIN" -m "$M" --host 127.0.0.1 --port 8092 --jinja -ngl all -c 8192 -np 1 --reasoning off > "$LOG" 2>&1 &
SP=$!
echo "server pid $SP started $(date -u +%H:%M:%SZ)"
ok=0
i=0
while [ $i -lt 240 ]; do
  if ! kill -0 $SP 2>/dev/null; then echo "SERVER EXITED EARLY"; tail -15 "$LOG"; exit 3; fi
  if curl -s --max-time 2 http://127.0.0.1:8092/health | grep -q '"ok"'; then ok=1; break; fi
  /bin/sleep 2; i=$((i+1))
done
[ $ok -eq 1 ] || { echo "SERVER NOT READY after 480 s"; tail -15 "$LOG"; kill $SP; exit 3; }
echo "ready $(date -u +%H:%M:%SZ) rss_kb=$(ps -o rss= -p $SP | tr -d ' ')"
req() {
  curl -s --max-time 300 http://127.0.0.1:8092/v1/chat/completions -H 'Content-Type: application/json' -d "$1" \
  | python3 -I -c 'import json,sys; d=json.load(sys.stdin); c=d["choices"][0]; m=c["message"]; print("finish:",c.get("finish_reason"),"| usage:",d.get("usage"),"| timings:",{k:round(v,1) for k,v in (d.get("timings") or {}).items() if isinstance(v,(int,float))}); print("reasoning_len:",len(m.get("reasoning_content") or "")); print("content:",repr((m.get("content") or "")[:400]))'
}
echo "--- request 1"
req '{"messages":[{"role":"user","content":"Reply with one line only: the value of 17/4 - 5/2 as a fraction."}],"max_tokens":96,"temperature":0}'
echo "--- request 2"
req '{"messages":[{"role":"user","content":"Find rational values x0, x1, x2 with x0 - x1 <= 1/2, x1 - x2 <= -1 and x0 - x2 >= -1. Reply with exactly three lines of the form x0 = value, nothing else."}],"max_tokens":96,"temperature":0}'
echo "after requests rss_kb=$(ps -o rss= -p $SP | tr -d ' ')"
grep -i -E "loop|passes|n_layer|arch |general.architecture|model size|offloaded" "$LOG" | head -12
kill $SP
/bin/sleep 2
echo "server stopped $(date -u +%H:%M:%SZ)"
