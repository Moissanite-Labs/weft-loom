import unittest
from fractions import Fraction

import _setup  # noqa: F401
import codec
import cost
import episodes as E
import evaluate as V
import tinker_backend as T


def rule_counter():
    return cost.Counter(rule_only=True)


def small_plan(arms=("B", "C"), train=None, seeds=2, e1=None, e2=None, cap=96, evals=None, **kw):
    e1 = e1 or {"S": 2, "M": 1}
    evals = evals if evals is not None else [cost.Eval("x", arms[0], "e1", seeds)]
    return cost.Plan("t", arms, train or {"S": 3, "M": 3}, seeds, 1, e1, e2 or {}, cap, evals, **kw)


class CostTests(unittest.TestCase):
    def test_usd_text_is_exact_integer_math(self):
        self.assertEqual(cost.usd_text(Fraction(1, 3)), "0.3333")
        self.assertEqual(cost.usd_text(Fraction(2, 3)), "0.6667")
        self.assertEqual(cost.usd_text(Fraction(3, 4), 3), "0.750")
        self.assertEqual(cost.usd_text(Fraction(5, 10**5)), "0.0001")
        self.assertEqual(cost.usd_text(Fraction(0)), "0.0000")
        self.assertEqual(cost.usd_text(Fraction(12345, 100)), "123.4500")

    def test_training_tokens_match_an_independent_count(self):
        plan = small_plan()
        totals, items = cost.plan_counts(plan, rule_counter())
        train = E.build_set("train", plan.train_counts)
        want = 0
        for arm in plan.arms:
            for ep in train.episodes:
                r = E.render(ep, arm)
                prompt = (V.count_pieces(codec.SYSTEM_LINE) + 3
                          + sum(V.count_pieces(m["content"]) + 3 for m in r.messages))
                want += prompt + V.count_pieces(r.target_text) + 3
        self.assertEqual(totals["train"], want * 2)

    def test_the_marker_counts_are_those_of_the_codec(self):
        import fakes
        c = codec.Codec(fakes.FakeTokenizer())
        self.assertEqual(len(c.message_ids("user", "ab")), 2 + codec.MARKERS_PER_MESSAGE)
        system = len(codec.SYSTEM_LINE) + codec.MARKERS_PER_MESSAGE
        user = 2 + codec.MARKERS_PER_MESSAGE
        self.assertEqual(len(c.prompt_ids([{"role": "user", "content": "ab"}])),
                         system + user)
        self.assertEqual(len(c.target_ids("ab")), 2 + codec.REPLY_OVERHEAD)

    def test_the_prompt_count_equals_the_codec_ids_with_a_character_tokenizer(self):
        import fakes
        tok = fakes.FakeTokenizer()
        c = codec.Codec(tok)

        class CharCounter(cost.Counter):
            def count(self, texts):
                return [len(t) for t in texts]
        ep = E.build_set("train", {"S": 2}).episodes[0]
        r = E.render(ep, "C")
        got = cost._tokens(CharCounter(rule_only=True), E.EpisodeSet("train", {"S": 2}, [ep]), "C")[0]
        p, t = c.train_ids(r.messages, r.target_text)
        self.assertEqual(got, (len(p), len(t)))

    def test_eval_sampling_is_the_cap_plus_the_turn_opening_and_end_marker_times_the_runs(self):
        plan = small_plan(arms=("C",), train={"S": 2}, seeds=3, e1={"S": 2, "M": 2}, e2={"S": 5}, cap=50,
                          evals=[cost.Eval("a", "C", "e1", 4), cost.Eval("b", "C", "e2", 3)])
        totals, _ = cost.plan_counts(plan, rule_counter())
        self.assertEqual(totals["sample"], 53 * (4 * 4 + 5 * 3))

    def test_prefill_is_counted_per_text_and_run(self):
        plan = small_plan(arms=("C",), train={"S": 2}, seeds=1, e1={"S": 3},
                          evals=[cost.Eval("a", "C", "e1", 2), cost.Eval("b", "A", "e1", 1)])
        totals, items = cost.plan_counts(plan, rule_counter())
        ev = E.build_set("heldout1", {"S": 3})
        c_prompts = sum(V.count_pieces(codec.SYSTEM_LINE) + 3 + sum(V.count_pieces(m["content"]) + 3 for m in E.render(ep, "C").messages) for ep in ev.episodes)
        a_prompts = sum(V.count_pieces(codec.SYSTEM_LINE) + 3 + sum(V.count_pieces(m["content"]) + 3 for m in E.render(ep, "A").messages) for ep in ev.episodes)
        self.assertEqual(totals["prefill"], 2 * c_prompts + a_prompts)

    def test_table_total_equals_backend_planned_cost(self):
        small = small_plan(arms=("C",), train={"S": 4, "M": 4}, seeds=1, e1={"S": 3, "M": 3})
        totals, total, lines = cost.table(small, rule_counter())
        self.assertEqual(total, T.planned_cost(totals))
        self.assertIn("exact total: %s dollars" % total, lines[-1])
        self.assertIn("token source: rule", lines[0])

    def test_plans_have_the_stated_shape(self):
        p = cost.pilot_plan(96)
        self.assertEqual((p.arms, sum(p.train_counts.values()), p.seeds), (("C",), 256, 1))
        f = cost.full_plan(2048, 2, 96)
        self.assertEqual(f.arms, ("A", "B", "C"))
        self.assertEqual((sum(f.train_counts.values()), f.seeds), (2048, 2))
        self.assertEqual(f.eval1_counts, {"S": 500, "M": 500})
        self.assertEqual(f.eval2_counts, {"S": 500, "M": 500})

    def test_full_plan_evaluations_are_the_registered_ones(self):
        f = cost.full_plan(2048, 2, 96)
        e1 = {(e.label, e.text_arm, e.runs) for e in f.evals if e.set_key == "e1"}
        self.assertEqual({a for _l, a, r in e1 if _l.startswith("base")}, set(E.ARMS))
        for arm in E.TRAIN_ARMS:
            self.assertIn(("adapter %s, text %s" % (arm, arm), arm, 2), e1)
        for text in "BEN":
            self.assertIn(("adapter C, text %s (control)" % text, text, 2), e1)
        e2 = sorted((e.text_arm, e.runs) for e in f.evals if e.set_key == "e2")
        self.assertEqual(e2, [("B", 1), ("C", 1), ("E", 1), ("N", 1)])      # training seed 0 only, once

    def test_pilot_shares_no_episode_with_the_full_run(self):
        p, f = cost.pilot_plan(96), cost.full_plan(2048, 2, 96)
        pilot_train = E.build_set("train", p.train_counts, p.train_offset)
        full_train = E.build_set("train", f.train_counts, f.train_offset)
        pilot_eval = E.build_set("train", p.eval1_counts, p.eval1_offset)
        seeds = lambda s: {(ep.tier, ep.seed) for ep in s.episodes}
        self.assertFalse(seeds(pilot_train) & seeds(full_train))
        self.assertFalse(seeds(pilot_eval) & seeds(full_train))
        self.assertFalse(seeds(pilot_eval) & seeds(pilot_train))

    def test_no_floats_in_the_cost_path(self):
        totals, _ = cost.plan_counts(small_plan(arms=("C",), train={"S": 2}, seeds=1, e1={"S": 2}), rule_counter())
        self.assertTrue(all(type(v) is int for v in totals.values()))


if __name__ == "__main__":
    unittest.main()
