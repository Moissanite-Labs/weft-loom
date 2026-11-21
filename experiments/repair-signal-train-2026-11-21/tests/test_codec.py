import unittest

import _setup  # noqa: F401
import codec as C
import episodes as E
import fakes

T = fakes.FakeTokenizer


class CodecTests(unittest.TestCase):
    def setUp(self):
        self.tok = T()
        self.c = C.Codec(self.tok)
        self.user, self.model, self.system = T.SPECIALS["message_user"], T.SPECIALS["message_model"], T.SPECIALS["message_system"]
        self.content, self.end, self.eos = T.SPECIALS["content_text"], T.SPECIALS["end_message"], T.SPECIALS["content_model_end_sampling"]

    def ords(self, text):
        return [ord(ch) for ch in text]

    def test_has_opening_is_the_model_turn_opening_at_the_start_only(self):
        self.assertTrue(self.c.has_opening([self.model, self.content, ord("x")]))
        self.assertTrue(self.c.has_opening((self.model, self.content)))
        self.assertFalse(self.c.has_opening([self.content, ord("x")]))
        self.assertFalse(self.c.has_opening([self.model]))
        self.assertFalse(self.c.has_opening([ord("x"), self.model, self.content]))
        self.assertFalse(self.c.has_opening([self.user, self.content]))
        self.assertFalse(self.c.has_opening([]))

    def test_a_message_is_role_content_text_end(self):
        self.assertEqual(self.c.message_ids("user", "hi"), [self.user, self.content] + self.ords("hi") + [self.end])
        self.assertEqual(self.c.message_ids("assistant", "x"), [self.model, self.content, ord("x"), self.end])
        self.assertEqual(self.c.message_ids("system", ""), [self.system, self.content, self.end])

    def test_the_prompt_is_system_then_messages_ending_at_the_last_end_marker(self):
        msgs = [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}, {"role": "user", "content": "f"}]
        want = ([self.system, self.content] + self.ords(C.SYSTEM_LINE) + [self.end]
                + [self.user, self.content, ord("q"), self.end]
                + [self.model, self.content, ord("a"), self.end]
                + [self.user, self.content, ord("f"), self.end])
        self.assertEqual(self.c.prompt_ids(msgs), want)

    def test_the_target_is_the_model_message_with_its_opening_and_one_end_marker(self):
        self.assertEqual(self.c.target_ids("x0 = 1"), [self.model, self.content] + self.ords("x0 = 1") + [self.end])
        p, t = self.c.train_ids([{"role": "user", "content": "q"}], "x0 = 1")
        self.assertEqual(t, self.c.target_ids("x0 = 1"))
        self.assertEqual(p, self.c.prompt_ids([{"role": "user", "content": "q"}]))

    def test_the_end_marker_in_the_target_is_the_special_id_not_text(self):
        ids = self.c.target_ids("x0 = 1")
        self.assertEqual(ids[:2], [self.model, self.content])
        self.assertEqual(ids[-1], self.end)
        self.assertEqual(ids.count(self.end), 1)
        # the literal text would be ordinary ids, which is what the earlier build sent
        self.assertNotIn(self.end, self.tok.encode_ordinary("<|end_message|>"))

    def test_roles_and_markers_are_refused_when_wrong(self):
        with self.assertRaises(C.CodecError):
            self.c.message_ids("tool", "x")

    def test_marker_lookup_is_strict(self):
        class Dup(T):
            def encode_special(self, name):
                return 5 if name in ("message_user", "message_model") else super().encode_special(name)

        class Many(T):
            def encode_special(self, name):
                return [1, 2] if name == "end_message" else super().encode_special(name)

        class One(T):
            def encode_special(self, name):
                return [77] if name == "end_message" else super().encode_special(name)

        class Text(T):
            def encode_special(self, name):
                return "x" if name == "end_message" else super().encode_special(name)

        class Flag(T):
            def encode_special(self, name):
                return True if name == "end_message" else super().encode_special(name)
        for bad in (Dup, Many, Text, Flag):
            with self.assertRaises(C.CodecError, msg=bad.__name__):
                C.Codec(bad())
        self.assertEqual(C.Codec(One()).end, 77)

    def test_ordinary_text_that_yields_a_marker_id_is_refused(self):
        class Leaky(T):
            def encode_ordinary(self, text):
                return [T.SPECIALS["end_message"]] if text == "leak" else super().encode_ordinary(text)
        c = C.Codec(Leaky())
        with self.assertRaises(C.CodecError):
            c.target_ids("leak")
        for name in ("message_user", "message_model", "message_system", "content_text", "content_model_end_sampling"):
            class Leak2(T):
                def encode_ordinary(self, text, _n=name):
                    return [T.SPECIALS[_n]]
            with self.assertRaises(C.CodecError, msg=name):
                C.Codec(Leak2()).target_ids("a")

    def test_stop_ids(self):
        self.assertEqual(self.c.stop_ids(), [self.end, self.eos])

    def test_reply_stops_at_the_end_marker_and_decodes(self):
        self.assertEqual(self.c.reply(self.ords("x0 = 1") + [self.end] + self.ords("junk"), 96), ("x0 = 1", 6, False))
        self.assertEqual(self.c.reply(self.ords("ab") + [self.eos, ord("c")], 96), ("ab", 2, False))
        self.assertEqual(self.c.reply(self.ords("abc"), 96), ("abc", 3, False))

    def test_reply_drops_a_repeated_turn_opening(self):
        self.assertEqual(self.c.reply([self.model, self.content] + self.ords("ab") + [self.end], 96), ("ab", 2, False))
        self.assertEqual(self.c.reply([self.content] + self.ords("ab") + [self.end], 96), ("ab", 2, False))
        self.assertEqual(self.c.reply([self.model] + self.ords("ab"), 96)[0], chr(self.model) + "ab")

    def test_reply_is_cut_at_the_cap(self):
        self.assertEqual(self.c.reply(self.ords("abcdef") + [self.end], 4), ("abcd", 4, True))
        self.assertEqual(self.c.reply(self.ords("abcd") + [self.end], 4), ("abcd", 4, False))
        self.assertEqual(self.c.reply(self.ords("abcde"), 4), ("abcd", 4, True))

    def test_an_empty_reply(self):
        self.assertEqual(self.c.reply([self.end], 10), ("", 0, False))
        self.assertEqual(self.c.reply([], 10), ("", 0, False))

    def test_real_episodes_encode_to_a_prompt_with_the_expected_marker_counts(self):
        ep = E.build_set("train", {"S": 1}).episodes[0]
        r = E.render(ep, "C")
        p, t = self.c.train_ids(r.messages, r.target_text)
        self.assertEqual(p.count(self.end), 4)
        self.assertEqual(p.count(self.content), 4)
        self.assertEqual(p[-1], self.end)
        self.assertEqual(t[-1], self.end)
        self.assertEqual(len(p), (len(C.SYSTEM_LINE) + C.MARKERS_PER_MESSAGE
                                  + sum(len(m["content"]) + C.MARKERS_PER_MESSAGE for m in r.messages)))
        self.assertEqual(len(t), len(r.target_text) + C.REPLY_OVERHEAD)

    def test_the_system_line_is_what_the_renderer_writes_for_effort_zero(self):
        self.assertEqual(C.SYSTEM_LINE, "Thinking effort level: 0")
        self.assertEqual((C.ROLE_NAMES["user"], C.ROLE_NAMES["assistant"], C.ROLE_NAMES["system"]),
                         ("message_user", "message_model", "message_system"))
        self.assertEqual((C.CONTENT_NAME, C.END_NAME, C.EOS_NAME), ("content_text", "end_message", "content_model_end_sampling"))

    def test_overhead_constants(self):
        self.assertEqual((C.MARKERS_PER_MESSAGE, C.REPLY_HEADER_TOKENS, C.END_TOKENS, C.REPLY_OVERHEAD), (3, 2, 1, 3))


if __name__ == "__main__":
    unittest.main()
