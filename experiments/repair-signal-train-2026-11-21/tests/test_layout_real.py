"""Checks the chat layout against the tml_renderers Inkling2 renderer, id for id.

Needs the tml_renderers package, which is not in the standard library. Without
it every test here is skipped. Run it with an interpreter that has the package:

    /path/to/venv/bin/python -I -B -m unittest discover -s tests -p test_layout_real.py

Nothing here touches the network or a key: the tokenizer and the renderer are
compiled into the package.
"""
import unittest

import _setup  # noqa: F401
import codec as C
import cost
import episodes as E

try:
    from tml_renderers import chat, renderers
except ImportError:           # pragma: no cover
    renderers = None


def _tokenizer(r):
    tk = r.tokenizer
    return tk() if callable(tk) else tk


def _ids(spans):
    out = []
    for s in spans:
        sp = s.span if hasattr(s, "span") else s
        out += list(sp.int_tokens)
    return out


@unittest.skipIf(renderers is None, "tml_renderers is not importable here")
class RealLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = renderers.Inkling2()
        cls.tk = _tokenizer(cls.r)
        cls.c = C.Codec(cls.tk)
        cls.eps = E.build_set("train", {"S": 12, "M": 12}).episodes
        kinds = {"user": chat.AuthorKind.User, "assistant": chat.AuthorKind.Model, "system": chat.AuthorKind.System}
        cls.msg = staticmethod(lambda role, text: chat.Message(chat.Text(text), chat.Author(kinds[role])))

    def test_marker_ids_are_special_and_distinct(self):
        c = self.c
        ids = [c.role["user"], c.role["assistant"], c.role["system"], c.content, c.end, c.eos]
        self.assertEqual(len(set(ids)), 6)
        self.assertTrue(all(self.tk.is_special_token(i) for i in ids))
        self.assertEqual(self.r.stop(), [c.eos])

    def test_literal_marker_text_is_not_the_special_id(self):
        ordinary = self.tk.encode_ordinary("<|end_message|>")
        self.assertNotIn(self.c.end, ordinary)
        self.assertGreater(len(ordinary), 1)

    def test_prompt_ids_equal_the_renderers_completion_prompt(self):
        for arm in E.ARMS:
            for ep in self.eps:
                rd = E.render(ep, arm)
                msgs = [self.msg(m["role"], m["content"]) for m in rd.messages]
                spans, _parser = self.r.render_for_completion_with_effort(msgs, 0.0)
                self.assertEqual(self.c.prompt_ids(rd.messages), _ids(spans), (arm, ep.id))

    def test_training_ids_equal_the_renderers_sft_ids_with_loss_on_the_reply(self):
        for arm in E.TRAIN_ARMS:
            for ep in self.eps:
                rd = E.render(ep, arm)
                msgs = [self.msg("system", C.SYSTEM_LINE)] + [self.msg(m["role"], m["content"]) for m in rd.messages]
                ex = self.r.render_for_sft(msgs + [self.msg("assistant", rd.target_text)])
                self.assertEqual(len(ex), 1)
                want = _ids(ex[0].input_token_spans)
                prompt_ids, target_ids = self.c.train_ids(rd.messages, rd.target_text)
                self.assertEqual(prompt_ids + target_ids, want)
                # the renderer puts loss on the last model message, opening and end marker included, as the
                # target does (it also puts loss on the failed attempt, which the datum does not)
                weights = ex[0].per_token_loss_weight_unshifted
                self.assertEqual(weights[-len(target_ids):], [1.0] * len(target_ids))

    def test_the_parser_reads_a_reply_the_way_the_codec_does(self):
        spans, parser = self.r.render_for_completion([self.msg("user", "hi")])
        sampled = self.c.target_ids("x0 = 1\nx1 = 2")            # a model turn: opening, reply, end marker
        parsed = parser.parse_tokens(sampled)
        self.assertEqual(parsed.messages[0].content.text, "x0 = 1\nx1 = 2")
        self.assertEqual(self.c.reply(sampled, 96)[0], "x0 = 1\nx1 = 2")

    def test_cost_counts_equal_the_real_id_counts(self):
        counter = cost.Counter()
        self.assertEqual(counter.source, "tokenizer")
        eset = E.EpisodeSet("train", {"S": 12, "M": 12}, self.eps)
        for arm in E.ARMS:
            got = cost._tokens(counter, eset, arm)
            for ep, (prompt_tokens, target_tokens) in zip(self.eps, got):
                rd = E.render(ep, arm)
                prompt_ids, target_ids = self.c.train_ids(rd.messages, rd.target_text)
                self.assertEqual((prompt_tokens, target_tokens), (len(prompt_ids), len(target_ids)))


if __name__ == "__main__":
    unittest.main()
