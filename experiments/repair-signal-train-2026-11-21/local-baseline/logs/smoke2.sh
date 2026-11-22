#!/bin/sh
# Second local test: how the chat template handles reasoning, and whether an answer fits under a 96-token cap.
set -u
D=${LLAMA_DIR:?set LLAMA_DIR to the folder that holds llama.cpp/build/bin/llama-server}
BIN=$D/llama.cpp/build/bin/llama-server
M=${MODEL_GGUF:?set MODEL_GGUF to the Inkling-2-Mini-Q8_0.gguf file}
"$BIN" -m "$M" --host 127.0.0.1 --port 8092 --jinja -ngl all -c 8192 -np 1 > "$D/smoke2-server.log" 2>&1 &
SP=$!
i=0; ok=0
while [ $i -lt 240 ]; do
  kill -0 $SP 2>/dev/null || { echo "SERVER EXITED"; tail -5 "$D/smoke2-server.log"; exit 3; }
  curl -s --max-time 2 http://127.0.0.1:8092/health | grep -q '"ok"' && { ok=1; break; }
  /bin/sleep 2; i=$((i+1))
done
[ $ok -eq 1 ] || { echo "NOT READY"; kill $SP; exit 3; }
curl -s --max-time 20 http://127.0.0.1:8092/props | python3 -I -c 'import json,sys; d=json.load(sys.stdin); t=d.get("chat_template") or ""; open("chat_template.jinja","w").write(t); print("template chars:", len(t)); import re; print("mentions:", sorted(set(re.findall(r"reasoning_effort|enable_thinking|thinking|effort|analysis|channel|<\|[a-z_]+\|>", t)))[:40])'
Q='Find rational values x0, x1, x2 with x0 - x1 <= 1/2, x1 - x2 <= -1 and x0 - x2 >= -1. Reply with exactly three lines of the form x0 = value, nothing else.'
req() {
  echo "--- $1"
  curl -s --max-time 300 http://127.0.0.1:8092/v1/chat/completions -H 'Content-Type: application/json' -d "$2" \
  | python3 -I -c 'import json,sys; d=json.load(sys.stdin)
if "choices" not in d: print("ERROR:", str(d)[:300]); raise SystemExit(0)
c=d["choices"][0]; m=c["message"]; u=d.get("usage") or {}
print("finish:",c.get("finish_reason"),"| completion_tokens:",u.get("completion_tokens"),"| reasoning chars:",len(m.get("reasoning_content") or ""),"| content:",repr((m.get("content") or "")[:160]))'
}
req "A default, cap 96" "{\"messages\":[{\"role\":\"user\",\"content\":\"$Q\"}],\"max_tokens\":96,\"temperature\":0}"
req "B reasoning_effort none, cap 96" "{\"messages\":[{\"role\":\"user\",\"content\":\"$Q\"}],\"max_tokens\":96,\"temperature\":0,\"reasoning_effort\":\"none\"}"
req "C template kwarg reasoning_effort none, cap 96" "{\"messages\":[{\"role\":\"user\",\"content\":\"$Q\"}],\"max_tokens\":96,\"temperature\":0,\"chat_template_kwargs\":{\"reasoning_effort\":\"none\"}}"
req "D template kwarg enable_thinking false, cap 96" "{\"messages\":[{\"role\":\"user\",\"content\":\"$Q\"}],\"max_tokens\":96,\"temperature\":0,\"chat_template_kwargs\":{\"enable_thinking\":false}}"
req "E default, cap 1500" "{\"messages\":[{\"role\":\"user\",\"content\":\"$Q\"}],\"max_tokens\":1500,\"temperature\":0}"
kill $SP; /bin/sleep 2; echo "stopped"
