"""Offline tests of the relay mechanics. No model is called: a scripted backend plays
every cell. Needs root on Linux (the sandbox does). Run from the record folder:

    python3 -m unittest tests.test_offline -v
"""

import re
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from referee import relay  # noqa: E402
from referee.bench import Bench, inspect_harness, tree_hash  # noqa: E402
from referee.brain import BrainServer, Ledger, Scripted, SpendCapReached, clip_middle  # noqa: E402

# A toy family: the task is to copy a number. The scripted cell gets it right only when
# its harness prompt holds the word MAGIC, so "a better harness" is one that holds it.
echo = types.SimpleNamespace(FAMILY="echo")


def _gen(seed, workdir, level=2):
    Path(workdir).mkdir(parents=True, exist_ok=True)
    (Path(workdir) / "TASK.md").write_text(f"Write the number {seed % 1000} to answer.txt.\n")
    return {"n": seed % 1000}


def _check(workdir, truth, run_py):
    p = Path(workdir) / "answer.txt"
    return 1.0 if p.is_file() and p.read_text().strip() == str(truth["n"]) else 0.0


echo.generate, echo.check = _gen, _check
FAMILIES = {"echo": echo}

BUILD_MOVES = {
    "good": "@sh\necho MAGIC >> target/prompt.md\n@end",
    "break": "@write target/agent.py\nthis is not python (\n@end",
    "harm": "@sh\nsed -i s/MAGIC/plain/g target/prompt.md\n@end",
    "noop": "@done",
    "bloat": "@sh\nhead -c 70000 /dev/zero | tr '\\0' 'x' > target/big.txt\n@end",
    "symlink": "@sh\nln -s /etc/passwd target/leak.txt; echo MAGIC >> target/prompt.md\n@end",
    "delete": "@sh\nrm -rf target\n@end",
}


def make_backend(plan):
    """plan maps (cell, turn) to a key of BUILD_MOVES; missing entries are 'noop'."""
    def fn(system, prompt):
        if "--- step 1 ---" in prompt:
            return "@done"
        m = re.search(r"# Build turn (\d+) of \d+: you are cell ([AB])", prompt)
        if m:
            return BUILD_MOVES[plan.get((m.group(2), int(m.group(1))), "noop")]
        if "READY" in prompt:
            return "@write answer.txt\nREADY\n@end"
        n = int(re.search(r"Write the number (\d+)", prompt).group(1))
        return f"@write answer.txt\n{n if 'MAGIC' in system else n + 1}\n@end"
    return Scripted(fn)


def run(arm, plan, turns=2):
    root = Path(tempfile.mkdtemp(prefix="gc-test-", dir="/srv"))
    cfg = relay.Config(turns=turns, families=("echo",), heldout=(), per_family=2,
                       exam_visible_per_family=2, parallel=4)
    r = relay.Relay(arm, 0, cfg, root, make_backend(plan), FAMILIES)
    end = r.run()
    import json
    rows = [json.loads(x) for x in (r.dir / "log.jsonl").read_text().splitlines()]
    turns_ = [x for x in rows if x["kind"] == "turn"]
    exams = {x["slot"]: x["report"]["mean"] for x in rows if x["kind"] == "exam"}
    shutil.rmtree(root, ignore_errors=True)
    return end, turns_, exams, rows


class RelayMechanics(unittest.TestCase):
    def test_twin_commit_and_cross_edit(self):
        end, turns, exams, rows = run("twin-free-collective", {("A", 1): "good"})
        self.assertEqual(turns[0]["outcome"], "commit")
        self.assertEqual((turns[0]["builder"], turns[0]["target"]), ("A", "B"))
        self.assertEqual((turns[0]["inc"], turns[0]["cand"]), (0.0, 1.0))
        self.assertEqual(turns[1]["outcome"], "noop")
        self.assertNotEqual(end["harness"]["A"], end["harness"]["B"])
        self.assertEqual(exams, {"A": 0.0, "B": 1.0})
        # B built in turn 2 inside the harness A wrote for it
        self.assertEqual(turns[1]["builder_harness"], turns[0]["candidate"])

    def test_boot_failure_is_discarded(self):
        end, turns, exams, _ = run("twin-free-collective", {("A", 1): "break"})
        self.assertEqual(turns[0]["outcome"], "boot_fail")
        self.assertEqual(end["harness"]["A"], end["harness"]["B"])
        self.assertNotIn("inc", turns[0])

    def test_regression_is_discarded(self):
        end, turns, exams, _ = run("twin-free-collective", {("A", 1): "good", ("B", 2): "noop", ("A", 3): "harm"}, turns=3)
        self.assertEqual([t["outcome"] for t in turns], ["commit", "noop", "regress"])
        self.assertEqual((turns[2]["inc"], turns[2]["cand"]), (1.0, 0.0))
        self.assertEqual(turns[2]["harness_after"]["B"], turns[0]["candidate"])
        self.assertEqual(exams["B"], 1.0)

    def test_surface_cap_and_missing_target(self):
        _, turns, _, _ = run("twin-free-collective", {("A", 1): "bloat", ("B", 2): "delete"})
        self.assertEqual(turns[0]["outcome"], "invalid")
        self.assertIn("over the cap", turns[0]["reason"])
        self.assertEqual(turns[1]["outcome"], "invalid")
        self.assertEqual(turns[1]["reason"], "no agent.py")

    def test_symlink_never_reaches_a_snapshot(self):
        end, turns, _, _ = run("twin-free-collective", {("A", 1): "symlink"})
        self.assertEqual(turns[0]["outcome"], "commit")
        self.assertEqual(turns[0]["candidate_files"], 4)  # agent.py, prompt.md, two tools

    def test_stack_puts_both_cells_on_one_line(self):
        end, turns, exams, _ = run("twin-stack-collective", {("A", 1): "good"})
        # turn 2: B makes no edit, but the candidate for A starts from B's harness, so A
        # is fast-forwarded to it through the gate
        self.assertEqual(turns[1]["edited"], False)
        self.assertEqual(turns[1]["base"], turns[0]["candidate"])
        self.assertEqual(turns[1]["outcome"], "commit")
        self.assertEqual(end["harness"]["A"], end["harness"]["B"])
        self.assertEqual(exams, {"A": 1.0, "B": 1.0})

    def test_solo_edits_itself(self):
        end, turns, exams, _ = run("solo-pair", {("A", 1): "good"})
        self.assertEqual((turns[0]["builder"], turns[0]["target"]), ("A", "A"))
        self.assertEqual((turns[1]["builder"], turns[1]["target"]), ("B", "B"))
        self.assertEqual(exams, {"A": 1.0, "B": 0.0})

    def test_fixed_builder_always_runs_the_seed(self):
        end, turns, _, rows = run("twin-fixed-builder", {("A", 1): "good", ("B", 2): "good"})
        seed = rows[0]["seed_harness"]
        self.assertEqual({t["builder_harness"] for t in turns}, {seed})
        self.assertEqual([t["outcome"] for t in turns], ["commit", "commit"])

    def test_brief_differs_between_arms_only_where_stated(self):
        cfg = relay.Config()
        texts = {}
        for arm in relay.ARMS:
            r = relay.Relay.__new__(relay.Relay)
            r.cfg, r.spec = cfg, relay.ARMS[arm]
            tgt = "A" if relay.ARMS[arm]["topology"] == "solo" else "B"
            texts[arm] = r.brief(1, "A", tgt, {"A": 0.5, "B": 0.5}, [])
        self.assertEqual(texts["twin-free-collective"], texts["twin-fixed-builder"])
        self.assertIn("higher score wins", texts["twin-free-rival"])
        self.assertIn("stacked on top", texts["twin-stack-collective"])
        self.assertNotIn("twin", texts["solo-pair"])


class Limits(unittest.TestCase):
    def test_call_cap_and_prompt_clip(self):
        text, clipped = clip_middle("x" * 500, 200)
        self.assertTrue(clipped)
        self.assertLessEqual(len(text), 200)
        root = Path(tempfile.mkdtemp(prefix="gc-test-", dir="/srv"))
        calls = []
        b = Bench(root, Scripted(lambda s, p: calls.append(1) or "@sh\ntrue\n@end"), FAMILIES)
        e = b.episode(relay.SEED_DIR, "echo", 5, level=2, calls=3, prompt_chars=16000, wall_s=60)
        self.assertEqual((e["calls"], len(calls), e["score"]), (3, 3, 0.0))
        shutil.rmtree(root, ignore_errors=True)

    def test_usage_limit_pauses_and_reruns(self):
        """A model call refused for the account's usage limit must not count as a result."""
        root = Path(tempfile.mkdtemp(prefix="gc-test-", dir="/srv"))
        state = {"n": 0}

        def fn(system, prompt):
            state["n"] += 1
            if state["n"] <= 2:
                raise RuntimeError("You've hit your 5-hour limit · resets 9am (UTC)")
            if "--- step 1 ---" in prompt or "probe" in system:
                return "@done"
            n = int(re.search(r"Write the number (\d+)", prompt).group(1))
            return f"@write answer.txt\n{n}\n@end"

        b = Bench(root, Scripted(fn), FAMILIES)
        b.limit_wait_s = 0.05
        before = Bench.limit_waits
        e = b.episode(relay.SEED_DIR, "echo", 7, level=2, calls=3, prompt_chars=16000, wall_s=60)
        self.assertEqual(e["score"], 1.0)                 # the rerun, not the refused attempt
        self.assertEqual(e["model_errors"], 0)
        self.assertGreaterEqual(Bench.limit_waits - before, 1)
        self.assertNotIn("limit_hit", e)
        shutil.rmtree(root, ignore_errors=True)

    def test_spend_cap_stops_calls(self):
        d = Path(tempfile.mkdtemp(prefix="gc-test-", dir="/srv"))
        led = Ledger(d / "spend.json", cap_usd=0.01)
        led.add(0.02)
        with self.assertRaises(SpendCapReached):
            led.check()
        shutil.rmtree(d, ignore_errors=True)

    def test_tree_hash_and_surface(self):
        info = inspect_harness(relay.SEED_DIR, 60000, 24)
        self.assertTrue(info["ok"])
        self.assertEqual(info["hash"], tree_hash(relay.SEED_DIR))
        self.assertFalse(inspect_harness(relay.SEED_DIR, 100, 24)["ok"])


if __name__ == "__main__":
    unittest.main()
