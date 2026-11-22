import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from math import comb

import _setup  # noqa: F401

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PILOT = os.path.join(HERE, "pilot")
RUN = os.path.join(PILOT, "pilot-2026-11-22-a")
SCRIPT = os.path.join(PILOT, "summarize.py")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S = load_module(SCRIPT, "pilot_summarize")


def run_script(folder=None):
    cmd = [sys.executable, "-I", "-B", SCRIPT] + (["--dir", folder] if folder else [])
    return subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)


def read_rows(folder):
    with open(os.path.join(folder, "replies.jsonl"), "r", encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def write_rows(folder, rows):
    with open(os.path.join(folder, "replies.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n")


def rehash(folder):
    """Rewrites SHA256SUMS for the copy, as someone who edits a file and its hash would."""
    lines = []
    for name in S.FILES:
        with open(os.path.join(folder, name), "rb") as fh:
            lines.append("%s  %s\n" % (hashlib.sha256(fh.read()).hexdigest(), name))
    with open(os.path.join(folder, S.SUMS), "w", encoding="utf-8") as fh:
        fh.writelines(lines)


class Copy:
    """A temporary copy of the committed pilot folder."""

    def __enter__(self):
        self.tmp = tempfile.mkdtemp()
        self.dir = os.path.join(self.tmp, "run")
        shutil.copytree(RUN, self.dir)
        return self.dir

    def __exit__(self, *exc):
        shutil.rmtree(self.tmp)


class CommittedSummaryTests(unittest.TestCase):
    def test_the_committed_summary_equals_the_script_output(self):
        got = run_script()
        self.assertEqual(got.returncode, 0, got.stdout + got.stderr)
        with open(os.path.join(RUN, "summary.txt"), "r", encoding="utf-8") as fh:
            self.assertEqual(got.stdout, fh.read())

    def test_the_default_folder_is_the_committed_run(self):
        self.assertEqual(os.path.realpath(S.DEFAULT_DIR), os.path.realpath(RUN))

    def test_no_problems_are_reported(self):
        with open(os.path.join(RUN, "summary.txt"), "r", encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("problems found: 0", text)
        self.assertNotIn("PROBLEM", text)

    def test_the_sums_file_lists_the_pilot_files_and_they_match(self):
        with open(os.path.join(RUN, S.SUMS), "r", encoding="utf-8") as fh:
            listed = dict(reversed(ln.rstrip("\n").split("  ", 1)) for ln in fh if ln.strip())
        self.assertEqual(sorted(listed), sorted(S.FILES))
        for name, digest in listed.items():
            with open(os.path.join(RUN, name), "rb") as fh:
                self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), digest, name)

    def test_committed_files_hold_no_local_path_name_or_key(self):
        pat = re.compile(r"/Users/|/home/|tml-[A-Za-z0-9]|api[_-]?key|TINKER_API", re.I)
        for name in S.FILES + ("summary.txt", S.SUMS):
            with open(os.path.join(RUN, name), "r", encoding="utf-8") as fh:
                self.assertIsNone(pat.search(fh.read()), name)


class RescoringTests(unittest.TestCase):
    def test_the_rescoring_agrees_on_all_rows(self):
        rows, seen = S.load_rows(RUN)
        self.assertEqual(len(rows), 200)
        scored = S.rescore_all(seen)
        self.assertEqual(len(scored), 200)
        self.assertEqual([k for k, (rec, got) in scored.items() if rec != got], [])

    def test_the_rescored_counts_are_the_recorded_ones(self):
        _rows, seen = S.load_rows(RUN)
        scored = S.rescore_all(seen)
        for model, want in (("base", (31, 67, 2)), ("adapter", (50, 50, 0))):
            got = tuple(sum(1 for (m, _t, _s), (_r, g) in scored.items() if m == model and g == k) for k in "PFX")
            self.assertEqual(got, want)

    def test_a_cut_reply_is_a_format_break(self):
        _rows, seen = S.load_rows(RUN)
        key = next(k for k, r in sorted(seen.items()) if r["outcome"] == "P")
        row = dict(seen[key], cut=1)
        ep = S.ep_mod.build_episode("train", key[1], key[2])
        self.assertEqual(S.rescore_row(S.ep_mod.rsig(), ep, seen[key]), "P")
        self.assertEqual(S.rescore_row(S.ep_mod.rsig(), ep, row), "X")

    def test_a_reply_off_the_grammar_is_a_format_break_and_a_wrong_one_fails(self):
        _rows, seen = S.load_rows(RUN)
        key = next(k for k, r in sorted(seen.items()) if r["outcome"] == "P")
        ep = S.ep_mod.build_episode("train", key[1], key[2])
        R = S.ep_mod.rsig()
        self.assertEqual(S.rescore_row(R, ep, dict(seen[key], reply="the answer is seven")), "X")
        zeros = "\n".join("x%d = 0" % i for i in range(ep.instance.n))
        self.assertEqual(S.rescore_row(R, ep, dict(seen[key], reply=zeros)), "F")

    def test_a_tampered_outcome_is_caught_even_when_the_sums_are_rewritten(self):
        with Copy() as d:
            rows = read_rows(d)
            rows[0]["outcome"] = "F" if rows[0]["outcome"] == "P" else "P"
            write_rows(d, rows)
            rehash(d)
            got = run_script(d)
        self.assertEqual(got.returncode, 1, got.stdout + got.stderr)
        self.assertIn("PROBLEM: MISMATCH", got.stdout)
        self.assertIn("rows whose recorded outcome equals the rescored outcome: 199", got.stdout)

    def test_a_tampered_reply_text_is_caught(self):
        with Copy() as d:
            rows = read_rows(d)
            i = next(i for i, r in enumerate(rows) if r["outcome"] == "P")
            rows[i]["reply"] = "x0 = 1"
            write_rows(d, rows)
            rehash(d)
            got = run_script(d)
        self.assertEqual(got.returncode, 1, got.stdout + got.stderr)
        self.assertIn("MISMATCH", got.stdout)

    def test_an_edit_without_new_sums_is_caught_by_the_hash(self):
        with Copy() as d:
            rows = read_rows(d)
            rows[0]["outcome"] = "F" if rows[0]["outcome"] == "P" else "P"
            write_rows(d, rows)
            got = run_script(d)
        self.assertEqual(got.returncode, 1)
        self.assertIn("replies.jsonl does not match its SHA-256", got.stdout)


class RefusalTests(unittest.TestCase):
    def refused(self, edit, text):
        with Copy() as d:
            rows = read_rows(d)
            rows = edit(rows) or rows
            write_rows(d, rows)
            rehash(d)
            got = run_script(d)
        self.assertEqual(got.returncode, 2, got.stdout + got.stderr)
        self.assertIn(text, got.stderr)
        self.assertEqual(got.stdout, "")

    def test_a_held_out_seed_is_refused(self):
        for tier, seed in (("S", 400000), ("S", 500000), ("M", 450000), ("S", 310050), ("S", 309999), ("M", 360050),
                           ("M", 359999), ("S", 300000), ("S", 100000)):
            def edit(rows, tier=tier, seed=seed):
                rows[0].update(tier=tier, seed=seed, episode_id="train-%s-%d" % (tier, seed))
            with self.subTest(tier=tier, seed=seed):
                self.refused(edit, "outside the pilot evaluation range")

    def test_a_seed_of_the_other_tier_is_refused(self):
        def edit(rows):
            rows[0].update(tier="S", seed=360000, episode_id="train-S-360000")
        self.refused(edit, "outside the pilot evaluation range")

    def test_a_seed_that_is_not_an_integer_is_refused(self):
        for bad in ("310000", True, None, 310000.5):
            def edit(rows, bad=bad):
                rows[0]["seed"] = bad
            with self.subTest(seed=bad):
                self.refused(edit, "the seed is not an integer")

    def test_an_unknown_tier_is_refused(self):
        def edit(rows):
            rows[0]["tier"] = "L"
        self.refused(edit, "which the pilot does not use")

    def test_an_episode_id_that_does_not_name_the_seed_is_refused(self):
        def edit(rows):
            rows[0]["episode_id"] = "train-M-360001"
        self.refused(edit, "the episode id does not match")

    def test_a_repeated_puzzle_is_refused(self):
        def edit(rows):
            rows[1] = dict(rows[0])
        self.refused(edit, "repeats the puzzle")

    def test_a_missing_puzzle_is_refused(self):
        def edit(rows):
            del rows[5]
        self.refused(edit, "has no row for 1 puzzles")

    def test_an_unknown_model_is_refused(self):
        def edit(rows):
            rows[0]["model"] = "other"
        self.refused(edit, "names model")

    def test_a_row_that_is_not_a_completed_call_is_refused(self):
        def edit(rows):
            rows[0]["status"] = "raised"
        self.refused(edit, "not a completed call")

    def test_a_row_with_another_text_is_refused(self):
        def edit(rows):
            rows[0]["arm"] = "B"
        self.refused(edit, "not a completed call")

    def test_a_row_with_extra_fields_is_refused(self):
        def edit(rows):
            rows[0]["extra"] = 1
        self.refused(edit, "does not have the fields")

    def test_an_outcome_or_cut_flag_outside_the_set_is_refused(self):
        for field, bad in (("outcome", "Z"), ("cut", 2), ("cut", True)):
            def edit(rows, field=field, bad=bad):
                rows[0][field] = bad
            with self.subTest(field=field, bad=bad):
                self.refused(edit, "not allowed")

    def test_a_reply_that_is_not_text_is_refused(self):
        def edit(rows):
            rows[0]["reply"] = 5
        self.refused(edit, "the reply is not text")

    def test_returned_ids_that_do_not_add_up_are_refused(self):
        def edit(rows):
            rows[0]["returned_tokens"] += 1
        self.refused(edit, "does not match the returned ids")

    def test_returned_ids_that_are_not_sequences_are_refused(self):
        def edit(rows):
            rows[0]["returned"] = None
        self.refused(edit, "not a list of sequences")

    def test_a_missing_file_is_refused(self):
        with Copy() as d:
            os.remove(os.path.join(d, "lock.json"))
            got = run_script(d)
        self.assertEqual(got.returncode, 2)
        self.assertIn("refused", got.stderr)

    def test_a_sums_file_that_misses_a_file_is_refused(self):
        with Copy() as d:
            path = os.path.join(d, S.SUMS)
            with open(path, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
            with open(path, "w", encoding="utf-8") as fh:
                fh.writelines(lines[1:])
            got = run_script(d)
        self.assertEqual(got.returncode, 2)
        self.assertIn("does not list exactly the pilot files", got.stderr)

    def test_a_malformed_sums_line_is_refused(self):
        with Copy() as d:
            with open(os.path.join(d, S.SUMS), "a", encoding="utf-8") as fh:
                fh.write("not a sums line\n")
            got = run_script(d)
        self.assertEqual(got.returncode, 2)
        self.assertIn("malformed", got.stderr)

    def test_an_unknown_option_is_refused(self):
        got = subprocess.run([sys.executable, "-I", "-B", SCRIPT, "--bogus"], capture_output=True, text=True)
        self.assertEqual(got.returncode, 2)
        self.assertIn("usage", got.stderr)


class OtherChecksTests(unittest.TestCase):
    def edited(self, name, edit):
        with Copy() as d:
            path = os.path.join(d, name)
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(edit(text))
            rehash(d)
            return run_script(d)

    def test_a_recorded_gate_that_the_numbers_do_not_give_is_caught(self):
        def edit(text):
            res = json.loads(text)
            res["gates"]["projected_time_ok"] = "true"
            return json.dumps(res, indent=1, sort_keys=True)
        got = self.edited("pilot-result.json", edit)
        self.assertEqual(got.returncode, 1, got.stdout + got.stderr)
        self.assertIn("PROBLEM: gate projected_time_ok: recorded 'true', recomputed 'false'", got.stdout)

    def test_a_recorded_go_that_the_numbers_do_not_give_is_caught(self):
        def edit(text):
            res = json.loads(text)
            res["go"] = "true"
            return json.dumps(res, indent=1, sort_keys=True)
        got = self.edited("pilot-result.json", edit)
        self.assertEqual(got.returncode, 1)
        self.assertIn("PROBLEM: go: recorded", got.stdout)

    def test_a_recorded_measurement_that_the_rows_do_not_give_is_caught(self):
        def edit(text):
            res = json.loads(text)
            res["measurements"]["new_block"] = 3
            return json.dumps(res, indent=1, sort_keys=True)
        got = self.edited("pilot-result.json", edit)
        self.assertEqual(got.returncode, 1)
        self.assertIn("PROBLEM: measurement new_block", got.stdout)

    def test_recorded_outcome_counts_that_differ_are_caught(self):
        def edit(text):
            res = json.loads(text)
            res["outcomes"]["base"]["P"] = 30
            return json.dumps(res, indent=1, sort_keys=True)
        got = self.edited("pilot-result.json", edit)
        self.assertEqual(got.returncode, 1)
        self.assertIn("outcome counts of the base model", got.stdout)

    def test_an_incomplete_or_fake_result_is_caught(self):
        def edit(text):
            res = json.loads(text)
            res["mode"] = "fake"
            return json.dumps(res, indent=1, sort_keys=True)
        got = self.edited("pilot-result.json", edit)
        self.assertEqual(got.returncode, 1)
        self.assertIn("not a complete real run", got.stdout)

    def test_an_approval_row_for_another_run_is_caught(self):
        def edit(text):
            row = json.loads(text)
            row["ceiling_usd"] = "5.00"
            return json.dumps(row, sort_keys=True) + "\n"
        got = self.edited("approval-row.json", edit)
        self.assertEqual(got.returncode, 1)
        self.assertIn("approval row differs", got.stdout)

    def test_a_lock_that_differs_from_the_harness_is_caught(self):
        def edit(text):
            lock = json.loads(text)
            lock["episodes_py"] = "0" * 64
            return json.dumps(lock, indent=1, sort_keys=True)
        got = self.edited("lock.json", edit)
        self.assertEqual(got.returncode, 1)
        self.assertIn("harness lock of the run differs", got.stdout)

    def test_a_ledger_that_does_not_match_the_result_is_caught(self):
        def edit(text):
            lines = text.split("\n")
            i = next(i for i, ln in enumerate(lines) if '"kind":"sample"' in ln and '"ev":"reserve"' in ln)
            lines[i] = lines[i].replace('"tokens":97', '"tokens":98')
            return "\n".join(lines)
        got = self.edited("spend-ledger.jsonl", edit)
        self.assertEqual(got.returncode, 1, got.stdout + got.stderr)
        self.assertIn("PROBLEM: the total spent or the planned cost differs from the result file", got.stdout)
        self.assertIn("PROBLEM: spend of kind sample differs between the ledger and the result file", got.stdout)

    def test_sampled_tokens_above_their_upper_bound_are_caught(self):
        def edit(text):
            return text + '{"ev":"adjust","kind":"sample","run_id":"pilot-2026-11-22-a","tokens":12020}\n'
        got = self.edited("spend-ledger.jsonl", edit)
        self.assertEqual(got.returncode, 1, got.stdout + got.stderr)
        self.assertIn("PROBLEM: sampled tokens are above their upper bound", got.stdout)

    def test_a_ledger_plan_id_that_differs_is_caught(self):
        def edit(text):
            return text.replace("588a6b6c", "588a6b6d", 1)
        got = self.edited("spend-ledger.jsonl", edit)
        self.assertEqual(got.returncode, 1, got.stdout + got.stderr)
        self.assertIn("PROBLEM: the ledger's plan id differs", got.stdout)

    def test_a_result_plan_id_that_is_not_the_pilot_plan_is_caught(self):
        def edit(text):
            return text.replace("588a6b6c", "588a6b6d", 1)
        got = self.edited("pilot-result.json", edit)
        self.assertEqual(got.returncode, 1, got.stdout + got.stderr)
        self.assertIn("PROBLEM: the plan id of the run is not the fingerprint", got.stdout)

    def test_a_ledger_with_two_starts_is_caught(self):
        def edit(text):
            first = text.split("\n", 1)[0]
            return first + "\n" + text
        got = self.edited("spend-ledger.jsonl", edit)
        self.assertEqual(got.returncode, 1)
        self.assertIn("holds 2 starts", got.stdout)

    def test_returned_ids_that_differ_from_the_ledger_are_caught(self):
        with Copy() as d:
            rows = read_rows(d)
            rows[0]["returned"][0].append(7)
            rows[0]["returned_tokens"] += 1
            write_rows(d, rows)
            rehash(d)
            got = run_script(d)
        self.assertEqual(got.returncode, 1, got.stdout + got.stderr)
        self.assertIn("do not add up to the sampled tokens", got.stdout)

    def test_a_stored_reply_that_differs_is_caught(self):
        def edit(text):
            lines = text.split("\n")
            entry = json.loads(lines[0])
            e = entry.get("entry", entry)
            e["texts"][0] = e["texts"][0] + " "
            lines[0] = json.dumps(entry, sort_keys=True, separators=(",", ":"))
            return "\n".join(lines)
        got = self.edited("receipts.jsonl.replies.jsonl", edit)
        self.assertEqual(got.returncode, 1, got.stdout + got.stderr)
        self.assertIn("differs from replies.jsonl", got.stdout)

    def test_stored_replies_that_do_not_cover_the_log_are_caught(self):
        def edit(text):
            return text.split("\n", 1)[1]
        got = self.edited("receipts.jsonl.replies.jsonl", edit)
        self.assertEqual(got.returncode, 1, got.stdout + got.stderr)
        self.assertIn("PROBLEM: the stored replies cover 100 of 200", got.stdout)

    def test_a_reply_that_opens_a_block_is_counted(self):
        with Copy() as d:
            rows = read_rows(d)
            rows[0]["reply"] = rows[0]["reply"] + "<|think|>"
            write_rows(d, rows)
            rehash(d)
            got = run_script(d)
        self.assertEqual(got.returncode, 1, got.stdout + got.stderr)
        self.assertIn("PROBLEM: measurement new_block: recorded 0, recomputed 1", got.stdout)

    def test_a_call_that_returned_two_sequences_is_not_accepted(self):
        with Copy() as d:
            rows = read_rows(d)
            rows[0]["returned"].append([7])
            rows[0]["returned_tokens"] += 1
            write_rows(d, rows)
            rehash(d)
            got = run_script(d)
        self.assertEqual(got.returncode, 1, got.stdout + got.stderr)
        self.assertIn("PROBLEM: measurement accepted: recorded 200, recomputed 199", got.stdout)

    def test_a_row_file_that_is_not_json_is_refused(self):
        with Copy() as d:
            with open(os.path.join(d, "replies.jsonl"), "a", encoding="utf-8") as fh:
                fh.write("{broken\n")
            rehash(d)
            got = run_script(d)
        self.assertEqual(got.returncode, 2)
        self.assertIn("replies.jsonl line 201 is not JSON", got.stderr)

    def test_a_missing_sums_file_is_refused(self):
        with Copy() as d:
            os.remove(os.path.join(d, S.SUMS))
            got = run_script(d)
        self.assertEqual(got.returncode, 2)
        self.assertIn("SHA256SUMS cannot be read", got.stderr)

    def test_a_plan_file_without_an_exact_total_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.mkdir(os.path.join(tmp, "data"))
            with open(os.path.join(tmp, "data", "x.txt"), "w", encoding="utf-8") as fh:
                fh.write("Plan pilot (token source: rule)\nitem kind tokens $/M dollars\n"
                         "train C: 1 examples          train   5    0.750   0.0000\n\n")
            with self.assertRaises(S.SummaryError):
                S.parse_plan_tokens(tmp, "x.txt", "rule")

    def test_a_broken_receipt_chain_is_refused(self):
        def edit(text):
            return text.replace('"seq":2', '"seq":9', 1)
        got = self.edited("receipts.jsonl", edit)
        self.assertEqual(got.returncode, 2, got.stdout + got.stderr)
        self.assertIn("refused", got.stderr)


class NumbersTests(unittest.TestCase):
    def test_the_ranges_are_the_pilot_evaluation_ranges(self):
        _plan, ranges = S.pilot_ranges()
        self.assertEqual(ranges, {"M": (360000, 360049), "S": (310000, 310049)})
        base = load_module(os.path.join(HERE, "local-baseline", "check_seeds.py"), "check_seeds_for_summary")
        self.assertEqual({k: tuple(v) for k, v in base.PILOT.items()}, ranges)

    def test_the_sign_test_is_exact_and_agrees_with_the_ratchet(self):
        import ratchet
        for a, b in ((28, 9), (9, 28), (5, 5), (0, 0), (1, 0), (0, 7), (12, 3)):
            self.assertEqual(S.sign_one_sided(a, b), ratchet.sign_test_p(a, b))
        n = 37
        want = Fraction(sum(comb(n, k) for k in range(28, 38)), 2 ** 37)
        self.assertEqual(S.sign_one_sided(28, 9), want)
        self.assertEqual(S.sign_two_sided(28, 9), 2 * want)
        self.assertEqual(S.sign_two_sided(9, 28), 2 * want)
        self.assertEqual(S.sign_two_sided(5, 5), 1)
        self.assertEqual(S.sign_two_sided(0, 0), 1)
        self.assertEqual(S.sign_two_sided(6, 5), 1)

    def test_the_paired_counts_come_from_the_recorded_outcomes_alone(self):
        by = {}
        for r in read_rows(RUN):
            by.setdefault((r["tier"], r["seed"]), {})[r["model"]] = r["outcome"] == "P"
        c = {"both": 0, "adapter": 0, "base": 0, "neither": 0}
        for v in by.values():
            a, b = v["adapter"], v["base"]
            c["both" if a and b else "adapter" if a else "base" if b else "neither"] += 1
        self.assertEqual(c, {"both": 22, "adapter": 28, "base": 9, "neither": 41})
        with open(os.path.join(RUN, "summary.txt"), "r", encoding="utf-8") as fh:
            self.assertIn("all           22              28            9         41", fh.read())

    def test_the_projection_uses_the_plan_counts_of_the_code(self):
        calls, steps = S.driver.plan_calls(S.cost.full_plan(S.pilot_cli.FULL_EXAMPLES, S.pilot_cli.FULL_SEEDS,
                                                           S.evaluate.DEFAULT_CAP))
        self.assertEqual((calls, steps), (21000, 384))
        with open(os.path.join(RUN, "pilot-result.json"), "r", encoding="utf-8") as fh:
            m = json.load(fh)["measurements"]
        hours = (Fraction(m["sample_ns"], m["calls"]) * calls + Fraction(m["train_ns"], m["steps"]) * steps) / (3600 * 10 ** 9)
        self.assertGreater(hours, 12)
        self.assertEqual(S.dec(hours, 3), "15.759")

    def test_decimal_rounding_is_half_up_and_exact(self):
        self.assertEqual(S.dec(Fraction(1, 2), 1), "0.5")
        self.assertEqual(S.dec(Fraction(25, 100), 1), "0.3")
        self.assertEqual(S.dec(Fraction(2573, 1000), 2), "2.57")
        self.assertEqual(S.dec(Fraction(2575, 1000), 2), "2.58")
        self.assertEqual(S.dec(Fraction(1, 1000), 2), "0.00")
        self.assertEqual(S.dec(Fraction(3), 3), "3.000")
        self.assertEqual(S.frac_text(Fraction(4, 2)), "2")
        self.assertEqual(S.frac_text(Fraction(2, 4)), "1/2")

    def test_the_plan_tokens_are_read_from_the_committed_cost_outputs(self):
        kinds, exact = S.parse_plan_tokens(HERE, "cost-tokenizer.txt", "tokenizer")
        self.assertEqual(kinds, {"train": 96688, "prefill": 68218, "sample": 19400})
        self.assertEqual(exact, Fraction(924487, 10000000))
        kinds, exact = S.parse_plan_tokens(HERE, "cost-rule.txt", "rule")
        self.assertEqual(sum(kinds.values()), 172549)
        with self.assertRaises(S.SummaryError):
            S.parse_plan_tokens(HERE, "cost-rule.txt", "nothing")
        with self.assertRaises(S.SummaryError):
            S.parse_plan_tokens(HERE, "no-such-file.txt", "rule")


if __name__ == "__main__":
    unittest.main()
