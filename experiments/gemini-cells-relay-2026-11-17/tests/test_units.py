"""Fast unit tests of the referee's pure parts and the hidden checkers. No model, no
sandbox: the checkers run cell code through tasks.local_run_py. Run from the record folder:

    python3 -I -B -m unittest discover -s tests -p 'test_units.py' -v
"""

import pathlib
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from referee import relay  # noqa: E402
from referee.brain import BrainServer, Scripted  # noqa: E402
from referee.tasks import _util, bugfix, local_run_py, spec  # noqa: E402

RUN = local_run_py


class Gate(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(relay.gate(0.80, 0.82, 0.02), "commit")      # exactly at the margin
        self.assertEqual(relay.gate(0.7999, 0.82, 0.02), "regress")   # just past it
        self.assertEqual(relay.gate(0.90, 0.82, 0.02), "commit")
        self.assertEqual(relay.gate(0.0, 0.0, 0.0), "commit")         # a tie is kept
        self.assertEqual(relay.gate(0.5, 0.5 + 1e-9, 0.0), "regress")


class Server(unittest.TestCase):
    def test_server_clips_prompts_and_counts_calls(self):
        seen = []
        backend = Scripted(lambda system, prompt: seen.append((system, prompt)) or "ok")
        srv = BrainServer(pathlib.Path(tempfile.mkdtemp()) / "s.sock", backend, calls=2,
                          prompt_chars=1000, log_path=pathlib.Path(tempfile.mkdtemp()) / "log.jsonl")
        r1 = srv._handle({"op": "call", "system": "s" * 9000, "prompt": "p" * 50000})
        self.assertEqual(r1, {"reply": "ok"})
        self.assertLessEqual(len(seen[0][1]), 1000)
        self.assertLessEqual(len(seen[0][0]), 8000)
        self.assertTrue(srv.records[0]["clipped"])
        self.assertEqual(srv._handle({"op": "left"})["left"], 1)
        srv._handle({"op": "call", "prompt": "q"})
        self.assertEqual(srv._handle({"op": "call", "prompt": "q"}), {"error": "budget"})
        self.assertEqual(len(seen), 2)
        self.assertGreaterEqual(srv.model_wait_s(), 0.0)


class Instances(unittest.TestCase):
    def test_deterministic_and_bound_to_the_key(self):
        fams = ("ledger", "logwin")
        a = relay.instances("secret|cand1", 3, fams, 4)
        self.assertEqual(a, relay.instances("secret|cand1", 3, fams, 4))
        self.assertEqual(len(a), 8)
        self.assertEqual([f for f, _ in a], ["ledger"] * 4 + ["logwin"] * 4)
        self.assertNotEqual(a, relay.instances("secret|cand2", 3, fams, 4))   # another candidate
        self.assertNotEqual(a, relay.instances("other|cand1", 3, fams, 4))    # another secret
        self.assertNotEqual(a, relay.instances("secret|cand1", 4, fams, 4))   # another turn
        self.assertEqual(len({s for _, s in a}), 8)

    def test_exam_never_overlaps_turn_seeds_by_construction(self):
        cfg = relay.Config()
        exam = relay.exam_instances(cfg)
        self.assertTrue(all(seed >= cfg.exam_seed_base for _, seed in exam))
        self.assertTrue(all(s < 800000 for _, s in relay.instances("k", 1, cfg.families, 50)))
        self.assertGreaterEqual(cfg.exam_seed_base, 800000)


class Decode(unittest.TestCase):
    def test_round_trip_of_plain_values(self):
        for value in [None, True, False, 0, -7, 10 ** 30, 1.5, float("inf"), "", "aé",
                      [1, [2, (3,)]], (1, "x"), {"k": [1, 2], 3: None, (1, 2): True},
                      {1, 2}, frozenset({"a"})]:
            encoded = self._encode(value)
            self.assertEqual(_util.decode(encoded), value)
            self.assertIs(type(_util.decode(encoded)), type(value))

    @staticmethod
    def _encode(value):
        """Run the sandbox-side encoder from RUNNER on one value, here in the test."""
        source = _util.RUNNER[_util.RUNNER.index("def _enc"):_util.RUNNER.index("def attempt")]
        namespace = {}
        exec(source, namespace)
        return namespace["_enc"](value)

    def test_malformed_is_rejected(self):
        bad = [{"i": "1.5"}, {"i": "--1"}, {"i": "١"}, {"i": "9" * 5000}, {"f": "x" * 41},
               {"b": 1}, {"s": 3}, {"l": {"s": "a"}}, {"d": [[{"s": "a"}]]}, {"q": 1},
               {"s": "a", "i": "1"}, [1], "text", {"S": [{"l": []}]}, {"d": [[{"l": []}, None]]}]
        for item in bad:
            ok, _ = _util.outcome_value({"v": item})
            self.assertFalse(ok, item)
        deep = None
        for _ in range(_util.MAX_DEPTH + 5):
            deep = {"l": [deep]}
        self.assertFalse(_util.outcome_value({"v": deep})[0])
        self.assertFalse(_util.outcome_value({"v": {"i": "1"}, "x": "y"})[0])
        self.assertFalse(_util.outcome_value("text")[0])

    def test_value_error_marker(self):
        self.assertTrue(_util.raised_value_error({"x": "ValueError"}))
        for item in [{"x": "failed"}, {"x": "ValueError", "v": None}, {"v": {"s": "ValueError"}}, "ValueError"]:
            self.assertFalse(_util.raised_value_error(item))


class Checkers(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="gc-units-"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _instance(self, family, seed, level=2):
        folder = pathlib.Path(tempfile.mkdtemp(dir=self.root))
        return folder, family.generate(seed, folder, level)

    def test_bugfix_honest_scores(self):
        folder, truth = self._instance(bugfix, 3)
        shipped = bugfix.check(folder, truth, RUN)
        self.assertTrue(0.2 < shipped < 0.8)
        bugfix.solve_from_files(folder)
        self.assertEqual(bugfix.check(folder, truth, RUN), 1.0)

    def test_bugfix_forgeries_score_nothing_extra(self):
        folder, truth = self._instance(bugfix, 3)
        shipped = bugfix.check(folder, truth, RUN)
        first = folder / "pkg" / f"{truth['modules'][0]['spec']}.py"
        first.write_text("import __main__ as m\n"
                         "t = sum(len(e.get('exprs', [])) for e in m.MODULES)\n"
                         "m.emit([{'v': {'b': True}}] * t)\n")
        self.assertLess(bugfix.check(folder, truth, RUN), shipped)
        folder, truth = self._instance(bugfix, 4)
        for path in (folder / "pkg").glob("*.py"):
            path.write_text(path.read_text() + "\nclass _AE:\n    def __eq__(self, o):\n        return True\n"
                            "import types\nfor _n, _f in list(globals().items()):\n"
                            "    if isinstance(_f, types.FunctionType):\n"
                            "        globals()[_n] = lambda *a, **k: _AE()\n")
        self.assertEqual(bugfix.check(folder, truth, RUN), 0.0)

    def test_hidden_script_holds_no_expected_result(self):
        folder, truth = self._instance(spec, 5)
        seen = {}

        def spy(script, cwd, timeout_s):
            seen["script"] = script
            return RUN(script, cwd, timeout_s)

        spec.solve_from_files(folder)
        self.assertEqual(spec.check(folder, truth, spy), 1.0)
        import json
        body = seen["script"][len(_util.RUNNER) - 200:]
        self.assertNotIn(json.dumps(truth["tests"]), seen["script"])
        self.assertNotIn('"value"', body)
        self.assertNotIn('"raises"', body)
        folder, truth = self._instance(bugfix, 5)
        bugfix.check(folder, truth, spy)
        self.assertNotIn('"tests"', seen["script"])

    def test_spec_forgeries_score_nothing_extra(self):
        folder, truth = self._instance(spec, 6, level=3)
        (folder / "solution.py").write_text(
            "import __main__ as m\nm.emit([{'v': {'s': 'x'}}] * len(m.CALLS))\n")
        self.assertEqual(spec.check(folder, truth, RUN), 0.0)
        (folder / "solution.py").write_text(
            "import __main__ as m\nm.finish(len(getattr(m, 'TESTS', [1])), len(getattr(m, 'TESTS', [1])))\n")
        self.assertEqual(spec.check(folder, truth, RUN), 0.0)

    def test_result_line_needs_the_nonce_and_the_count(self):
        folder, truth = self._instance(spec, 7)
        spec.solve_from_files(folder)
        good = spec.check(folder, truth, RUN)
        self.assertEqual(good, 1.0)

        def drop_nonce(script, cwd, timeout_s):
            rc, out = RUN(script, cwd, timeout_s)
            return rc, out.replace('"nonce"', '"nonc"')

        def drop_one(script, cwd, timeout_s):
            rc, out = RUN(script, cwd, timeout_s)
            import json
            line = json.loads(out.strip().splitlines()[-1])
            line["results"] = line["results"][:-1]
            return rc, json.dumps(line)

        self.assertEqual(spec.check(folder, truth, drop_nonce), 0.0)
        self.assertEqual(spec.check(folder, truth, drop_one), 0.0)



class Block2Commands(unittest.TestCase):
    def setUp(self):
        import importlib
        self.run = importlib.import_module("run")
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="gc-appr-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _approval(self, **over):
        import hashlib
        import json
        body = {"plan_sha256": hashlib.sha256(self.run.PLAN_FILE.read_bytes()).hexdigest(),
                "tag": "partA", "cap_usd": 15}
        body.update(over)
        path = self.tmp / "approval.json"
        path.write_text(json.dumps(body))
        return str(path)

    def test_approval_is_bound_to_plan_tag_and_cap(self):
        self.assertEqual(self.run.check_approval(self._approval(), "partA"), 15.0)
        for bad in (None, str(self.tmp / "missing.json"), self._approval(plan_sha256="0" * 64),
                    self._approval(tag="partB"), self._approval(cap_usd=0), self._approval(cap_usd=51),
                    self._approval(cap_usd="lots")):
            with self.assertRaises(SystemExit):
                self.run.check_approval(bad, "partA")

    def test_assay_order_is_balanced(self):
        plan = self.run.assay2_plan(["r1", "r2"], ["A", "B"], 3, 2)
        self.assertEqual(len(plan), 2 * 2 * 3 + 2)
        self.assertEqual(len(set(plan)), len(plan))
        first = plan[:5]                      # the first repeat covers every harness once, then the seed
        self.assertEqual({(run, slot) for _, run, slot in first},
                         {("r1", "A"), ("r1", "B"), ("r2", "A"), ("r2", "B"), (None, "seed")})
        for cut in range(len(plan) + 1):      # however short a run is cut, counts differ by at most one
            counts = {}
            for _, run, slot in plan[:cut]:
                if run is not None:
                    counts[(run, slot)] = counts.get((run, slot), 0) + 1
            if counts and len(counts) == 4:
                self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)

if __name__ == "__main__":
    unittest.main()
