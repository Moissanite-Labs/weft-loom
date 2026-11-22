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
        self.thinking = T.SPECIALS["content_thinking"]

    def ords(self, text):
        return [ord(ch) for ch in text]

    def test_opens_new_block_sees_a_marker_before_the_first_stop_id_only(self):
        for marker in (self.model, self.content, self.user, self.system, self.thinking):
            self.assertTrue(self.c.opens_new_block([ord("x"), marker, ord("y")]), marker)
            self.assertTrue(self.c.opens_new_block([marker]), marker)
        self.assertFalse(self.c.opens_new_block(self.ords("x0 = 1")))
        self.assertFalse(self.c.opens_new_block(self.ords("x0 = 1") + [self.end, self.thinking]))
        self.assertFalse(self.c.opens_new_block([self.eos, self.model]))
        self.assertFalse(self.c.opens_new_block([self.end]))
        self.assertFalse(self.c.opens_new_block([]))

    def test_any_special_id_of_the_tokenizer_opens_a_new_block(self):
        named = set(T.SPECIALS.values())
        unnamed = [i for i in range(1000, 1021) if i not in named]
        self.assertTrue(unnamed)
        for i in unnamed:
            self.assertTrue(self.c.is_marker(i), i)
            self.assertTrue(self.c.opens_new_block(self.ords("x0 = 1") + [i]), i)
            self.assertTrue(self.c.opens_new_block([i, self.end]), i)
            self.assertFalse(self.c.opens_new_block(self.ords("x0 = 1") + [self.end, i]), i)
        for i in (0, 65, 999, 1021, 5000):
            self.assertFalse(self.c.is_marker(i), i)

    def test_a_tokenizer_that_cannot_tell_specials_apart_counts_the_named_markers_only(self):
        class Plain(T):
            is_special_token = None
        plain = C.Codec(Plain())
        self.assertFalse(plain.is_marker(1011))
        self.assertFalse(plain.opens_new_block([1011]))
        self.assertTrue(plain.is_marker(self.thinking))
        self.assertTrue(plain.opens_new_block([ord("x"), self.thinking]))

    def test_a_message_is_role_content_text_end(self):
        self.assertEqual(self.c.message_ids("user", "hi"), [self.user, self.content] + self.ords("hi") + [self.end])
        self.assertEqual(self.c.message_ids("assistant", "x"), [self.model, self.content, ord("x"), self.end])
        self.assertEqual(self.c.message_ids("system", ""), [self.system, self.content, self.end])

    def test_the_prompt_is_system_then_messages_then_the_forced_opening(self):
        msgs = [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}, {"role": "user", "content": "f"}]
        want = ([self.system, self.content] + self.ords(C.SYSTEM_LINE) + [self.end]
                + [self.user, self.content, ord("q"), self.end]
                + [self.model, self.content, ord("a"), self.end]
                + [self.user, self.content, ord("f"), self.end]
                + [self.model, self.content])
        self.assertEqual(self.c.prompt_ids(msgs), want)
        self.assertEqual(self.c.opening_ids(), [self.model, self.content])
        self.assertEqual(self.c.prompt_ids([])[-2:], [self.model, self.content])

    def test_the_target_is_the_reply_and_one_end_marker_without_the_opening(self):
        self.assertEqual(self.c.target_ids("x0 = 1"), self.ords("x0 = 1") + [self.end])
        p, t = self.c.train_ids([{"role": "user", "content": "q"}], "x0 = 1")
        self.assertEqual(t, self.c.target_ids("x0 = 1"))
        self.assertEqual(p, self.c.prompt_ids([{"role": "user", "content": "q"}]))
        self.assertEqual(p[-2:], [self.model, self.content])
        self.assertNotIn(self.model, t)
        self.assertNotIn(self.content, t)

    def test_the_end_marker_in_the_target_is_the_special_id_not_text(self):
        ids = self.c.target_ids("x0 = 1")
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
        for name in ("message_user", "message_model", "message_system", "content_text", "content_model_end_sampling",
                     "content_thinking"):
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

    def test_a_marker_inside_the_reply_is_written_into_the_text(self):
        got = self.c.reply([self.model, self.content] + self.ords("ab") + [self.end], 96)
        self.assertEqual(got, ("<|message_model|><|content_text|>ab", 4, False))
        self.assertEqual(self.c.reply(self.ords("a") + [self.thinking] + self.ords("b"), 96),
                         ("a<|content_thinking|>b", 3, False))
        self.assertEqual(self.c.reply([self.user], 96), ("<|message_user|>", 1, False))

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
        self.assertEqual(p.count(self.content), 5)                    # four messages and the forced opening
        self.assertEqual(p[-2:], [self.model, self.content])
        self.assertEqual(t[-1], self.end)
        self.assertEqual(len(p), (len(C.SYSTEM_LINE) + C.MARKERS_PER_MESSAGE
                                  + sum(len(m["content"]) + C.MARKERS_PER_MESSAGE for m in r.messages)
                                  + C.OPENING_TOKENS))
        self.assertEqual(len(t), len(r.target_text) + C.REPLY_OVERHEAD)

    def test_the_system_line_is_what_the_renderer_writes_for_effort_zero(self):
        self.assertEqual(C.SYSTEM_LINE, "Thinking effort level: 0")
        self.assertEqual((C.ROLE_NAMES["user"], C.ROLE_NAMES["assistant"], C.ROLE_NAMES["system"]),
                         ("message_user", "message_model", "message_system"))
        self.assertEqual((C.CONTENT_NAME, C.END_NAME, C.EOS_NAME, C.THINKING_NAME),
                         ("content_text", "end_message", "content_model_end_sampling", "content_thinking"))

    def test_overhead_constants(self):
        self.assertEqual((C.MARKERS_PER_MESSAGE, C.OPENING_TOKENS, C.END_TOKENS, C.REPLY_OVERHEAD), (3, 2, 1, 1))


if __name__ == "__main__":
    unittest.main()
