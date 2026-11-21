import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import _setup  # noqa: F401
import episodes as E
import evaluate as V
import local_backend as LB
import reference_policies as RP


def make_server(handler_fn):
    seen = []

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode())
            seen.append((self.path, body))
            code, payload = handler_fn(body)
            raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    return srv, th, seen


class LocalBackendTests(unittest.TestCase):
    def serve(self, fn):
        srv, th, seen = make_server(fn)
        self.addCleanup(th.join, 5)
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        return "http://127.0.0.1:%d/v1" % srv.server_address[1], seen

    def setUp(self):
        self.s = E.build_set("heldout1", {"S": 5})

    def test_request_shape_and_reply(self):
        def fn(body):
            view_text = body["messages"][-1]["content"]
            return 200, {"choices": [{"message": {"content": "x0 = 0\nx1 = 0\nx2 = 0\nx3 = 0",
                                                  "reasoning_content": "long hidden thought"},
                                      "finish_reason": "stop"}],
                         "usage": {"completion_tokens": 20}}
        url, seen = self.serve(fn)
        be = LB.LocalBackend(url, "m", 96)
        r = V.evaluate_arm(be, self.s, "C", 96, "local")
        self.assertEqual(len(seen), 5)
        path, body = seen[0]
        self.assertEqual(path, "/v1/chat/completions")
        self.assertEqual((body["model"], body["max_tokens"], body["temperature"]), ("m", 96, 0))
        self.assertEqual([m["role"] for m in body["messages"]], ["user", "assistant", "user"])
        self.assertEqual(r.n, 5)
        self.assertEqual(r.format_broken, 0)
        self.assertEqual(be.finish_reasons, ["stop"] * 5)

    def test_the_server_answer_is_scored_by_the_exact_checker(self):
        views = {}

        def fn(body):
            return 200, {"choices": [{"message": {"content": views["reply"]}, "finish_reason": "stop"}]}
        url, _ = self.serve(fn)
        be = LB.LocalBackend(url, "m", 96)
        ep = self.s.episodes[0]
        views["reply"] = RP.recompute(E.View(ep, "C"))
        self.assertEqual(V.evaluate_arm(be, E.EpisodeSet("heldout1", {"S": 1}, [ep]), "C", 96, "x").passed, 1)
        views["reply"] = ep and E.View(ep, "C").attempt_text
        self.assertEqual(V.evaluate_arm(be, E.EpisodeSet("heldout1", {"S": 1}, [ep]), "C", 96, "x").passed, 0)

    def test_count_over_the_cap_is_cut_by_the_harness(self):
        def fn(body):
            return 200, {"choices": [{"message": {"content": "word " * 500}, "finish_reason": "length"}],
                         "usage": {"completion_tokens": 500}}
        url, _ = self.serve(fn)
        r = V.evaluate_arm(LB.LocalBackend(url, "m", 96), self.s, "C", 96, "x")
        self.assertEqual((r.capped, r.format_broken), (5, 5))

    def test_only_http_urls_and_valid_caps(self):
        for u in ("file:///etc/passwd", "ftp://x/y", "https://x/v1", "https://127.0.0.1:1/v1", "ftp://localhost/x",
                  "nonsense", ""):
            with self.assertRaises(LB.BackendError):
                LB.LocalBackend(u, "m", 96)
        for cap in (0, -3, True):
            with self.assertRaises(LB.BackendError):
                LB.LocalBackend("http://127.0.0.1:1/v1", "m", cap)

    def test_only_loopback_hosts(self):
        for u in ("http://example.com/v1", "http://10.0.0.5:8080/v1", "http://127.0.0.1.example.com/v1",
                  "http://0.0.0.0:1/v1", "http://192.168.1.2/v1", "http://user@example.com:1/v1"):
            with self.assertRaises(LB.BackendError, msg=u):
                LB.LocalBackend(u, "m", 96)
        for u in ("http://localhost:1/v1", "http://127.0.0.1:1/v1", "http://[::1]:1/v1"):
            LB.LocalBackend(u, "m", 96)

    def test_http_error_and_malformed_json_raise(self):
        url, _ = self.serve(lambda b: (500, {"error": "x"}))
        with self.assertRaises(LB.BackendError):
            LB.LocalBackend(url, "m", 96)(E.View(self.s.episodes[0], "C"))
        url, _ = self.serve(lambda b: (200, b"not json"))
        with self.assertRaises(LB.BackendError):
            LB.LocalBackend(url, "m", 96)(E.View(self.s.episodes[0], "C"))
        url, _ = self.serve(lambda b: (200, {"choices": []}))
        with self.assertRaises(LB.BackendError):
            LB.LocalBackend(url, "m", 96)(E.View(self.s.episodes[0], "C"))

    def test_non_text_content_raises(self):
        url, _ = self.serve(lambda b: (200, {"choices": [{"message": {"content": 5}}]}))
        with self.assertRaises(LB.BackendError):
            LB.LocalBackend(url, "m", 96)(E.View(self.s.episodes[0], "C"))

    def test_connection_refused_raises(self):
        with self.assertRaises(LB.BackendError):
            LB.LocalBackend("http://127.0.0.1:9/v1", "m", 96, timeout=2)(E.View(self.s.episodes[0], "C"))

    def test_no_key_is_sent(self):
        be = LB.LocalBackend("http://127.0.0.1:1/v1", "m", 96)
        self.assertNotIn("authorization", json.dumps(be.payload(E.View(self.s.episodes[0], "C"))).lower())


if __name__ == "__main__":
    unittest.main()
