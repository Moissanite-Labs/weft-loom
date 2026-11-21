"""Token ids for the paid path, with the chat markers as special tokens.

The role and end markers of the Mini chat layout are special tokens, not text.
Encoding the literal text "<|end_message|>" with encode_ordinary gives seven
ordinary tokens, so a model trained on that text would learn to write it. This
module builds ids by splicing the special ids between the ordinary ids of each
message, the same layout tml_renderers.Inkling2 produces (checked against that
renderer in tests/test_layout_real.py when the package is importable):

    system  : MESSAGE_SYSTEM CONTENT <ordinary ids of the system line> END
    message : ROLE CONTENT <ordinary ids of the text> END       (user, model)
    prompt  : system, then every message, ending at the last END
    target  : MESSAGE_MODEL CONTENT <ordinary ids of the reply> END

The prompt ends where the renderer's completion prompt ends, and the model
writes its own turn opening, as the renderer expects. The target is that
whole model message, so training teaches the opening and the end marker too.
Loss in training is on the target ids only (the renderer's own SFT weights
also put loss on earlier model turns, here the failed attempt, which is not
wanted).

tok is any object with encode_ordinary(text), encode_special(name) and
decode(ids): the tokenizer carried by tml_renderers, or a fake in tests.
"""

SYSTEM_LINE = "Thinking effort level: 0"      # what Inkling2 renders for effort 0.0

ROLE_NAMES = {"user": "message_user", "assistant": "message_model", "system": "message_system"}
CONTENT_NAME = "content_text"
END_NAME = "end_message"
EOS_NAME = "content_model_end_sampling"       # Inkling2.stop() is this token

# Tokens a message adds around its text: the role id, the content id and the end id.
MARKERS_PER_MESSAGE = 3
# The model's turn opening (role id and content id) before a reply, and the end
# marker after it. A sampled reply is these plus the reply's own tokens.
REPLY_HEADER_TOKENS = 2
END_TOKENS = 1
REPLY_OVERHEAD = REPLY_HEADER_TOKENS + END_TOKENS


class CodecError(Exception):
    pass


class Codec:
    def __init__(self, tok, system_line=SYSTEM_LINE):
        self.tok = tok
        self.system_line = system_line
        self.role = {role: self._special(name) for role, name in ROLE_NAMES.items()}
        self.content = self._special(CONTENT_NAME)
        self.end = self._special(END_NAME)
        self.eos = self._special(EOS_NAME)
        ids = list(self.role.values()) + [self.content, self.end, self.eos]
        if len(set(ids)) != len(ids):
            raise CodecError("two markers share one id")

    def _special(self, name):
        got = self.tok.encode_special(name)
        if isinstance(got, (list, tuple)):
            if len(got) != 1:
                raise CodecError("marker %s is not one token" % name)
            got = got[0]
        if not isinstance(got, int) or isinstance(got, bool):
            raise CodecError("marker %s has no integer id" % name)
        return got

    def _ordinary(self, text):
        ids = list(self.tok.encode_ordinary(text))
        if any(i in self.role.values() or i in (self.content, self.end, self.eos) for i in ids):
            raise CodecError("ordinary text produced a marker id")
        return ids

    def message_ids(self, role, text):
        if role not in self.role:
            raise CodecError("unknown role %r" % (role,))
        return [self.role[role], self.content] + self._ordinary(text) + [self.end]

    def prompt_ids(self, messages):
        ids = self.message_ids("system", self.system_line)
        for m in messages:
            ids += self.message_ids(m["role"], m["content"])
        return ids

    def target_ids(self, text):
        return [self.role["assistant"], self.content] + self._ordinary(text) + [self.end]

    def train_ids(self, messages, target_text):
        """(prompt ids, target ids): loss goes on the second part only."""
        return self.prompt_ids(messages), self.target_ids(target_text)

    def has_opening(self, ids):
        """True if sampled ids begin with the model's turn opening (role id,
        then content id), which the prompt leaves for the model to write."""
        return list(ids[:2]) == [self.role["assistant"], self.content]

    def stop_ids(self):
        return [self.end, self.eos]

    def reply(self, ids, cap):
        """Text and token count of the reply in sampled ids. The reply is what
        comes before the first stop id, without the turn opening, and is cut at
        cap tokens (the opening and the end marker do not count against the
        cap). Returns (text, count, was_cut)."""
        out = []
        for i in ids:
            if i in (self.end, self.eos):
                break
            out.append(i)
        if out[:2] == [self.role["assistant"], self.content]:
            out = out[2:]
        elif out[:1] == [self.content]:
            out = out[1:]
        was_cut = len(out) > cap
        out = out[:cap]
        return self.tok.decode(out), len(out), was_cut
