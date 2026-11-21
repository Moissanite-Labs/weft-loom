"""Responder for an OpenAI-compatible local server (llama-server and similar).

The server is not started here. Tests run this against a tiny fake HTTP server.
Only the reply content is read. A separate reasoning field, if the server has
one, is ignored, so every arm answers under the same cap: max_tokens is the
cap and the server stops there.

No key is read or sent. The loop talks to a local server only: the host must
be a loopback address.
"""
import json
import urllib.error
import urllib.parse
import urllib.request


LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")


class BackendError(Exception):
    pass


class LocalBackend:
    def __init__(self, base_url, model, cap, timeout=120, seed=0, extra_body=None):
        parts = urllib.parse.urlparse(base_url)
        if parts.scheme != "http" or not parts.netloc:
            raise BackendError("the local backend takes an http:// URL only")
        if parts.hostname not in LOOPBACK_HOSTS:
            raise BackendError("the local backend talks to a loopback host only")
        if not isinstance(cap, int) or isinstance(cap, bool) or cap < 1:
            raise BackendError("cap must be a positive integer")
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.model, self.cap, self.timeout, self.seed = model, cap, timeout, seed
        self.extra_body = dict(extra_body or {})
        self.finish_reasons = []

    def payload(self, view):
        body = {"model": self.model, "messages": view.messages, "max_tokens": self.cap,
                "temperature": 0, "seed": self.seed, "stream": False}
        body.update(self.extra_body)
        return body

    def __call__(self, view):
        data = json.dumps(self.payload(view)).encode("utf-8")
        req = urllib.request.Request(self.url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                obj = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError) as exc:
            if isinstance(exc, urllib.error.HTTPError):
                exc.close()
            raise BackendError("request failed: %s" % type(exc).__name__)
        try:
            choice = obj["choices"][0]
            text = choice["message"]["content"] or ""
            ntok = obj.get("usage", {}).get("completion_tokens")
        except (KeyError, IndexError, TypeError):
            raise BackendError("the reply has no choices[0].message.content")
        if not isinstance(text, str):
            raise BackendError("content is not text")
        self.finish_reasons.append(str(choice.get("finish_reason")))
        if isinstance(ntok, int) and not isinstance(ntok, bool) and ntok <= self.cap:
            return text, ntok
        # No count, or a count over the cap: let the harness cut the text by its own rule.
        return text, None
