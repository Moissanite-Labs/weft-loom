"""The only door from a cell to its model. Mounted read-only inside the sandbox.

A harness calls `brain(system, prompt)` and gets the model's reply as text. The referee
on the other side of the socket counts the calls, caps the prompt length and logs every
exchange. A harness cannot raise its own limits: they are not in the harness.
"""

import json
import os
import socket


class BudgetExhausted(Exception):
    """No model calls are left in this episode."""


def _rpc(obj):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(300)
    s.connect(os.environ["CELL_BRAIN_SOCK"])
    s.sendall((json.dumps(obj) + "\n").encode("utf-8"))
    buf = b""
    while not buf.endswith(b"\n"):
        chunk = s.recv(1 << 16)
        if not chunk:
            break
        buf += chunk
    s.close()
    return json.loads(buf.decode("utf-8"))


def calls_left():
    """Model calls still available in this episode."""
    return int(_rpc({"op": "left"})["left"])


def limits():
    """The referee's limits for this episode: {"calls": n, "prompt_chars": n, "left": n}."""
    return _rpc({"op": "left"})


def brain(system, prompt):
    """One model call. Raises BudgetExhausted when the episode's calls are used up."""
    r = _rpc({"op": "call", "system": str(system), "prompt": str(prompt)})
    if r.get("error") == "budget":
        raise BudgetExhausted()
    if r.get("error"):
        raise RuntimeError(r["error"])
    return r["reply"]
