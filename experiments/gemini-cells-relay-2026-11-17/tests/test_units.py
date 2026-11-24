"""Fast unit tests of the referee's pure parts and the hidden checkers. No model, no
sandbox: the checkers run cell code through tasks.local_run_py. Run from the record folder:

    python3 -I -B -m unittest discover -s tests -p 'test_units.py' -v
"""

import json
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
        self.assertEqual(relay.gate(0.5, 0.5 + 1e-6, 0.0), "regress")
        self.assertEqual(relay.gate(0.4816, 0.5016, 0.02), "commit")   # exact margin despite float error
        self.assertEqual(relay.gate(0.4815, 0.5016, 0.02), "regress")


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

    def _server(self, fn, calls=10):
        return BrainServer(pathlib.Path(tempfile.mkdtemp()) / "s.sock", Scripted(fn), calls=calls,
                           prompt_chars=1000, log_path=pathlib.Path(tempfile.mkdtemp()) / "log.jsonl")

    def test_empty_prompt_is_refused_without_a_model_call(self):
        seen = []
        srv = self._server(lambda system, prompt: seen.append(prompt) or "ok", calls=2)
        self.assertEqual(srv._handle({"op": "call", "prompt": "  \n"}), {"error": "empty prompt"})
        self.assertEqual(seen, [])
        self.assertEqual(srv._handle({"op": "left"})["left"], 1)   # the refused call is spent

    def test_failed_call_stops_the_wait_clock(self):
        import time

        def fail(system, prompt):
            time.sleep(0.2)
            raise RuntimeError("backend down")

        srv = self._server(fail)
        self.assertEqual(srv._handle({"op": "call", "prompt": "x"}), {"error": "model call failed"})
        first = srv.model_wait_s()
        self.assertGreaterEqual(first, 0.19)
        time.sleep(0.3)
        self.assertAlmostEqual(srv.model_wait_s(), first, places=6)   # nothing still counted as in flight

    def test_wait_clock_counts_overlapping_calls_once(self):
        import threading
        import time
        srv = self._server(lambda system, prompt: time.sleep(0.5) or "ok")
        threads = [threading.Thread(target=srv._handle, args=({"op": "call", "prompt": "x"},)) for _ in range(3)]
        started = time.monotonic()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.monotonic() - started
        self.assertGreaterEqual(srv.model_wait_s(), 0.45)
        self.assertLessEqual(srv.model_wait_s(), elapsed + 0.01)
        self.assertLess(srv.model_wait_s(), 1.0)                     # not 3 x 0.5


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
        for value in [None, True, False, 0, -7, 10 ** 30, 1.5, float("inf"), "", "a\u00e9",
                      [1, [2, (3,)]], (1, "x"), [(1, [None, "y"]), 2.5]]:
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

    def test_sets_and_dicts_are_refused_without_hashing(self):
        """Building a set or dict from numbers chosen to collide is quadratic; decode must not."""
        import time
        for value in ({"k": 1}, {1, 2}, frozenset({"a"}), [1, {"k": 2}]):
            self.assertFalse(_util.outcome_value({"v": self._encode(value)})[0])
        colliding = [{"i": str(k * (2 ** 61 - 1))} for k in range(1, 20001)]
        started = time.perf_counter()
        for tag in ("S", "F"):
            self.assertFalse(_util.outcome_value({"v": {tag: colliding}})[0])
        self.assertFalse(_util.outcome_value({"v": {"d": [[c, None] for c in colliding]}})[0])
        ok, value = _util.outcome_value({"v": {"l": colliding}})
        self.assertTrue(ok)
        self.assertEqual(len(value), 20000)
        self.assertLess(time.perf_counter() - started, 1.0)

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
        """The script sent into the sandbox is RUNNER, one data line holding exactly the inputs,
        and the family's fixed body: nothing else, so no expected result."""
        import ast
        seen = {}

        def spy(script, cwd, timeout_s):
            seen["script"] = script
            return RUN(script, cwd, timeout_s)

        def data_lines(script, body):
            self.assertTrue(script.endswith(body))
            middle = script[:len(script) - len(body)]
            return [ln for ln in middle[middle.rindex("os._exit(0)") + len("os._exit(0)"):].splitlines() if ln.strip()]

        folder, truth = self._instance(spec, 5)
        spec.solve_from_files(folder)
        self.assertEqual(spec.check(folder, truth, spy), 1.0)
        lines = data_lines(seen["script"], spec.TEST_BODY)
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], f"FUNC = {truth['func']!r}")
        name, _, call = lines[1].partition(" = ")
        self.assertEqual(name, "CALLS")
        self.assertEqual(json.loads(ast.literal_eval(call[len("json.loads("):-1])),
                         [case["args"] for case in truth["tests"]])

        folder, truth = self._instance(bugfix, 5)
        bugfix.check(folder, truth, spy)
        lines = data_lines(seen["script"], bugfix.TEST_BODY)
        self.assertEqual(len(lines), 1)
        name, _, call = lines[0].partition(" = ")
        self.assertEqual(name, "MODULES")
        self.assertEqual(json.loads(ast.literal_eval(call[len("json.loads("):-1])),
                         [{"module": m["spec"], "exprs": [e for e, _ in m["tests"]]} for m in truth["modules"]])

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

        def flood(script, cwd, timeout_s):
            rc, out = RUN(script, cwd, timeout_s)
            return rc, " " * (_util.MAX_STDOUT_BYTES + 1) + out

        self.assertEqual(spec.check(folder, truth, drop_nonce), 0.0)
        self.assertEqual(spec.check(folder, truth, drop_one), 0.0)
        self.assertEqual(spec.check(folder, truth, flood), 0.0)



class Block2Commands(unittest.TestCase):
    def setUp(self):
        import hashlib
        import importlib
        self.run = importlib.import_module("run")
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="gc-appr-"))
        self.saved_plan = self.run.PLAN_FILE
        frozen = hashlib.sha256((self.run.HERE / "run.py").read_bytes()).hexdigest()
        self.plan = self.tmp / "PLAN.md"
        self.plan.write_text(f"# plan\n\n## Frozen files\n\n```\n{frozen}  run.py\n```\n\n## After\n")
        self.run.PLAN_FILE = self.plan
        self.root = self.tmp / "root"

    def tearDown(self):
        self.run.PLAN_FILE = self.saved_plan
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _approval(self, **over):
        import hashlib
        body = {"plan_sha256": hashlib.sha256(self.run.PLAN_FILE.read_bytes()).hexdigest(),
                "tag": "partA", "root": str(self.root.resolve()), "cap_usd": 20,
                "approved_by": "owner", "date": "2026-11-24"}
        body.update(over)
        path = self.tmp / "approval.json"
        path.write_text(json.dumps(body))
        return str(path)

    def test_approval_is_bound_to_plan_tag_root_and_cap(self):
        self.assertEqual(self.run.check_approval(self._approval(), "partA", str(self.root)), 20.0)
        for over in ({"plan_sha256": "0" * 64}, {"tag": "partB"}, {"cap_usd": 0}, {"cap_usd": 51},
                     {"cap_usd": "lots"}, {"root": "/elsewhere"}, {"approved_by": ""}, {"date": " "}):
            with self.assertRaises(SystemExit, msg=str(over)):
                self.run.check_approval(self._approval(**over), "partA", str(self.root))
        for bad in (None, str(self.tmp / "missing.json")):
            with self.assertRaises(SystemExit):
                self.run.check_approval(bad, "partA", str(self.root))

    def test_frozen_files_must_match(self):
        self.plan.write_text(self.plan.read_text().replace("run.py", "seed/agent.py"))  # wrong hash for it
        with self.assertRaises(SystemExit):
            self.run.check_approval(self._approval(), "partA", str(self.root))
        self.plan.write_text("# plan without frozen files\n")
        with self.assertRaises(SystemExit):
            self.run.check_approval(self._approval(), "partA", str(self.root))

    def test_assay2_refuses_before_any_backend_exists(self):
        import types
        made = []
        saved = self.run.ClaudeCLI
        self.run.ClaudeCLI = lambda *a, **k: made.append(1)
        try:
            args = types.SimpleNamespace(root=str(self.root), source=str(self.tmp), tag="partA",
                                         approval=self._approval(tag="other"), slots="A,B", reps=1,
                                         seed_reps=0, shard="0/1")
            with self.assertRaises(SystemExit):
                self.run.cmd_assay2(args)
        finally:
            self.run.ClaudeCLI = saved
        self.assertEqual(made, [])

    def test_assay_order_is_balanced_shuffled_and_spread(self):
        runs = ["solo-pair-r0", "twin-free-collective-r0", "twin-fixed-builder-r0"]
        plan = self.run.assay2_plan(runs, ["A", "B"], 3, 12, "partA")
        self.assertEqual(len(plan), 3 * 2 * 3 + 12)
        self.assertEqual(len(set(plan)), len(plan))
        self.assertEqual(plan, self.run.assay2_plan(runs, ["A", "B"], 3, 12, "partA"))   # reproducible
        self.assertNotEqual(plan, self.run.assay2_plan(runs, ["A", "B"], 3, 12, "other"))
        block = 6 + 4
        for rep in range(3):                    # each repeat: every harness once, four seed assays
            rows = plan[rep * block:(rep + 1) * block]
            self.assertEqual(sorted((r, s) for _, r, s in rows if r), sorted((r, s) for r in runs for s in "AB"))
            self.assertEqual(sum(1 for _, r, _ in rows if r is None), 4)
        first = [r for _, r, _ in plan[:6] if r]
        self.assertGreater(len(set(first)), 1)  # arms are not run in blocks
        for cut in range(len(plan) + 1):
            counts = {}
            for _, run, slot in plan[:cut]:
                if run is not None:
                    counts[(run, slot)] = counts.get((run, slot), 0) + 1
            if len(counts) == 6:
                self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)


class PlanFreeze(unittest.TestCase):
    def test_plan_freezes_the_current_code(self):
        """block2/PLAN.md lists the hash of every file part A runs with. If this fails, a file
        changed after the plan was frozen: run block2/freeze.py, and any approval is void."""
        import subprocess
        here = pathlib.Path(__file__).resolve().parents[1]
        out = subprocess.run([sys.executable, "-I", "-B", str(here / "block2" / "freeze.py"), "--check"],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


class Faults(unittest.TestCase):
    def test_usage_limit_reruns_do_not_use_up_hard_cap_reruns(self):
        from referee.bench import Bench
        b = Bench(pathlib.Path(tempfile.mkdtemp(prefix="gc-faults-")), None, {})
        b._wait_for_backend = lambda: None
        state = b._new_state()
        self.assertTrue(b._backend_fault({"limit_hit": True}, state))
        self.assertTrue(b._backend_fault({"limit_hit": True}, state))
        self.assertEqual((state["limit_reruns"], state["reruns"]), (2, 0))
        for _ in range(b.hard_cap_reruns):
            self.assertTrue(b._backend_fault({"limit_hit": False, "timed_out": "hard_cap",
                                              "kill": {"by": "hard_cap"}}, state))
        last = {"limit_hit": False, "timed_out": "hard_cap"}
        self.assertFalse(b._backend_fault(last, state))
        self.assertTrue(last["referee_fault"])
        self.assertEqual(len(state["attempts"]), 2 + b.hard_cap_reruns)
        self.assertEqual(b.hard_cap_events, b.hard_cap_reruns + 1)
        own = {"limit_hit": False, "timed_out": "own_time"}
        self.assertFalse(b._backend_fault(own, b._new_state()))
        self.assertNotIn("referee_fault", own)


class AnalysisA(unittest.TestCase):
    def test_fault_rule(self):
        import importlib.util
        path = pathlib.Path(__file__).resolve().parents[1] / "block2" / "analyze_a.py"
        spec_ = importlib.util.spec_from_file_location("analyze_a", path)
        mod = importlib.util.module_from_spec(spec_)
        spec_.loader.exec_module(mod)
        clean = {"outcome": "commit", "inc": 0.5, "cand": 0.75, "boot": {"referee_fault": False},
                 "inc_report": {"episodes": [{"referee_fault": False, "reruns": 1}]}}
        self.assertFalse(mod.fault(clean))
        self.assertEqual(mod.gain(clean), 0.25)
        self.assertEqual(mod.reruns(clean), 1)
        self.assertTrue(mod.fault(dict(clean, build_referee_fault=True)))
        self.assertTrue(mod.fault(dict(clean, boot={"referee_fault": True})))
        self.assertTrue(mod.fault(dict(clean, base_report={"episodes": [{"referee_fault": True}]})))
        self.assertEqual(mod.gain({"outcome": "noop"}), 0.0)
        self.assertEqual(mod.gain({"outcome": "regress", "inc": 0.5, "cand": 0.25}), -0.25)

if __name__ == "__main__":
    unittest.main()
