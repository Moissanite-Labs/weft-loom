"""checks/split_overlap.py: no puzzle is shared between the training set and a
held-out set, and the counter really finds duplicates when they exist."""
import contextlib
import importlib.util
import io
import os
import unittest
from fractions import Fraction

import _setup  # noqa: F401
import episodes as E


def load():
    path = os.path.join(_setup.LOOP, "checks", "split_overlap.py")
    spec = importlib.util.spec_from_file_location("split_overlap", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RealPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load()
        cls.sets = cls.mod.build_sets()
        cls.within, cls.across = cls.mod.tally(cls.sets)

    def test_the_sets_are_the_sizes_the_plan_states(self):
        self.assertEqual({k: len(v) for k, v in self.sets.items()},
                         {"train": 2048, "heldout1": 1000, "heldout2": 1000, "pilot_train": 256, "pilot_eval": 100})

    def test_no_training_puzzle_equals_a_held_out_puzzle(self):
        self.assertEqual(self.mod.train_vs_heldout(self.across), {"heldout1": 0, "heldout2": 0})
        for held in ("heldout1", "heldout2"):
            self.assertEqual(self.across[("train", held)]["puzzle"], (0, 0, 0))

    def test_no_training_puzzle_with_the_same_failed_attempt_equals_a_held_out_one(self):
        for held in ("heldout1", "heldout2"):
            self.assertEqual(self.across[("train", held)]["episode"], (0, 0, 0))

    def test_no_pair_of_sets_shares_a_puzzle_and_no_set_repeats_one(self):
        for pair, per in self.across.items():
            self.assertEqual(per["puzzle"], (0, 0, 0), pair)
        for name, per in self.within.items():
            n, distinct = per["puzzle"]
            self.assertEqual(n, distinct, name)

    def test_the_committed_output_is_the_output_of_the_script(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(self.mod.main(), 0)
        with open(os.path.join(_setup.LOOP, "data", "split-overlap.txt"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), out.getvalue())

    def test_every_count_printed_is_an_integer(self):
        for line in self.mod.render_report(self.within, self.across):
            for word in line.split()[2:]:
                if word not in self.mod.LEVELS and word not in self.mod.SET_NAMES and not word.endswith("_forms") \
                        and not word.startswith("episodes_of_") and word not in ("episodes", "distinct", "repeated",
                                                                                 "shared_forms"):
                    self.assertTrue(word.isdigit(), line)


class CounterTests(unittest.TestCase):
    """The counter, on sets built to contain duplicates (it must not be blind)."""

    @classmethod
    def setUpClass(cls):
        cls.mod = load()
        R = E.rsig()
        cls.R = R

    def episode(self, seed, tier="S", delta=None):
        if delta is None:
            return E.build_episode("train", tier, seed)
        return E.build_episode("train", tier, seed, _draw=lambda tries, inst: [(0, Fraction(delta))])

    def failing_delta(self, seed):
        base = self.episode(seed)
        for d in (7, -7, 11, -11, 13):
            alt = self.episode(seed, delta=d)
            if alt.attempt != base.attempt:
                return d, alt
        self.fail("no alternative failing attempt found")

    def set_of(self, kind, eps):
        return E.EpisodeSet(kind, {"S": len(eps)}, eps)

    def test_the_same_set_twice_shares_every_form_at_both_levels(self):
        s = self.set_of("train", [self.episode(300000 + i) for i in range(5)])
        _within, across = self.mod.tally({"a": s, "b": s})
        self.assertEqual(across[("a", "b")]["puzzle"], (5, 5, 5))
        self.assertEqual(across[("a", "b")]["episode"], (5, 5, 5))

    def test_the_same_puzzle_with_another_failed_attempt_shares_the_puzzle_only(self):
        _d, alt = self.failing_delta(300003)
        a = self.set_of("train", [self.episode(300003), self.episode(300004)])
        b = self.set_of("train", [alt])
        self.assertEqual(alt.instance.to_dict()["constraints"], a.episodes[0].instance.to_dict()["constraints"])
        _within, across = self.mod.tally({"a": a, "b": b})
        self.assertEqual(across[("a", "b")]["puzzle"], (1, 1, 1))
        self.assertEqual(across[("a", "b")]["episode"], (0, 0, 0))

    def test_a_repeated_episode_inside_a_set_is_counted(self):
        e = self.episode(300010)
        within, _across = self.mod.tally({"a": self.set_of("train", [e, e, self.episode(300011)])})
        self.assertEqual(within["a"]["puzzle"], (3, 2))
        self.assertEqual(within["a"]["episode"], (3, 2))

    def test_counts_are_per_episode_on_each_side(self):
        e = self.episode(300020)
        a = self.set_of("train", [e, e, e])
        b = self.set_of("train", [e, self.episode(300021)])
        _within, across = self.mod.tally({"a": a, "b": b})
        self.assertEqual(across[("a", "b")]["puzzle"], (1, 3, 1))

    def test_distinct_puzzles_share_nothing(self):
        a = self.set_of("train", [self.episode(300030 + i) for i in range(4)])
        b = self.set_of("train", [self.episode(300040 + i) for i in range(4)])
        _within, across = self.mod.tally({"a": a, "b": b})
        self.assertEqual(across[("a", "b")]["puzzle"], (0, 0, 0))

    def test_the_form_holds_the_whole_prompt_with_every_constraint(self):
        e = self.episode(300050)
        p, _ = self.mod.forms(e)
        for c in e.instance.constraints:
            self.assertIn(c.text(), p)
        self.assertIn("x0", p)

    def test_the_episode_form_holds_the_attempt_and_the_target(self):
        e = self.episode(300051)
        _p, full = self.mod.forms(e)
        r = E.render(e, "A")
        self.assertEqual(full, (r.messages[0]["content"], r.attempt_text, r.target_text))

    def test_two_tiers_never_match(self):
        s = self.set_of("train", [self.episode(300060, "S")])
        m = self.set_of("train", [self.episode(350060, "M")])
        _within, across = self.mod.tally({"a": s, "b": m})
        self.assertEqual(across[("a", "b")]["puzzle"], (0, 0, 0))

    def test_the_report_totals_a_planted_overlap(self):
        e = self.episode(300070)
        train = self.set_of("train", [e, e])                        # twice in the training set
        held1 = self.set_of("train", [e])                           # once in held-out set 1
        held2 = self.set_of("train", [self.episode(300071)])
        _w, across = self.mod.tally({"train": train, "heldout1": held1, "heldout2": held2})
        self.assertEqual(self.mod.train_vs_heldout(across), {"heldout1": 1, "heldout2": 0})


if __name__ == "__main__":
    unittest.main()
