"""Token ids for the paid path, with the chat markers as special tokens.

The role and end markers of the Mini chat layout are special tokens, not text.
Encoding the literal text "<|end_message|>" with encode_ordinary gives seven
ordinary tokens, so a model trained on that text would learn to write it. This
module builds ids by splicing the special ids between the ordinary ids of each
message, the same layout tml_renderers.Inkling2 produces (checked against that
renderer in tests/test_layout_real.py when the package is importable):

    system  : MESSAGE_SYSTEM CONTENT <ordinary ids of the system line> END
    message : ROLE CONTENT <ordinary ids of the text> END       (user, model)
    prompt  : system, then every message, then the forced opening
    opening : MESSAGE_MODEL CONTENT
    target  : <ordinary ids of the reply> END

The prompt ends with the model's turn opened for an answer, the model role
marker followed by the text content marker (the forced opening). The untrained
model otherwise opens a thinking block first, and nothing here turns that off,
so every prompt that is sampled from ends this way, for every arm. The reply
cap then counts answer tokens only. In training the two opening ids are part
of the prompt (no loss on them) and the target is the reply followed by the
end marker. The renderer's completion prompt has no form that ends with the
opening, so the offline check builds its prompt from the completion prompt plus
these two ids.

Loss in training is on the target ids only (the renderer's own SFT weights
also put loss on earlier model turns, here the failed attempt, which is not
wanted, and on the opening, which is not wanted either).

tok is any object with encode_ordinary(text), encode_special(name) and
decode(ids): the tokenizer carried by tml_renderers, or a fake in tests.
"""

SYSTEM_LINE = "Thinking effort level: 0"      # what Inkling2 renders for effort 0.0

ROLE_NAMES = {"user": "message_user", "assistant": "message_model", "system": "message_system"}
CONTENT_NAME = "content_text"
END_NAME = "end_message"
EOS_NAME = "content_model_end_sampling"       # Inkling2.stop() is this token
THINKING_NAME = "content_thinking"            # the block the untrained model opens by itself

# Tokens a message adds around its text: the role id, the content id and the end id.
MARKERS_PER_MESSAGE = 3
# The forced opening that ends every prompt (the model role id and the content
# id), and the end marker that ends a reply (a target and a sampled reply).
OPENING_TOKENS = 2
END_TOKENS = 1
REPLY_OVERHEAD = END_TOKENS


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
        self.thinking = self._special(THINKING_NAME)
        ids = list(self.role.values()) + [self.content, self.end, self.eos, self.thinking]
        if len(set(ids)) != len(ids):
            raise CodecError("two markers share one id")
        self._marker_names = {i: n for n, i in zip(
            list(ROLE_NAMES.values()) + [CONTENT_NAME, END_NAME, EOS_NAME, THINKING_NAME], ids)}

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
        if any(i in self._marker_names for i in ids):
            raise CodecError("ordinary text produced a marker id")
        return ids

    def message_ids(self, role, text):
        if role not in self.role:
            raise CodecError("unknown role %r" % (role,))
        return [self.role[role], self.content] + self._ordinary(text) + [self.end]

    def opening_ids(self):
        """The forced opening: the model role id, then the text content id."""
        return [self.role["assistant"], self.content]

    def prompt_ids(self, messages):
        """Every prompt that is sampled from or trained on, ending with the forced opening."""
        ids = self.message_ids("system", self.system_line)
        for m in messages:
            ids += self.message_ids(m["role"], m["content"])
        return ids + self.opening_ids()

    def target_ids(self, text):
        return self._ordinary(text) + [self.end]

    def train_ids(self, messages, target_text):
        """(prompt ids, target ids): loss goes on the second part only."""
        return self.prompt_ids(messages), self.target_ids(target_text)

    def opens_new_block(self, ids):
        """True if the reply part of sampled ids (what comes before the first
        stop id) holds any marker id: a reply must not open a new message or
        block of its own, such as a thinking block."""
        for i in ids:
            if i in (self.end, self.eos):
                return False
            if i in self._marker_names:
                return True
        return False

    def stop_ids(self):
        return [self.end, self.eos]

    def reply(self, ids, cap):
        """Text and token count of the reply in sampled ids. The reply is what
        comes before the first stop id and is cut at cap tokens (the end marker
        does not count against the cap, and the forced opening is in the prompt,
        not in the sample). A marker id inside the reply is written into the
        text as <|name|>, so a reply that opens a new block cannot parse as an
        answer. Returns (text, count, was_cut)."""
        out = []
        for i in ids:
            if i in (self.end, self.eos):
                break
            out.append(i)
        was_cut = len(out) > cap
        out = out[:cap]
        parts, run = [], []
        for i in out:
            if i in self._marker_names:
                parts.append(self.tok.decode(run) if run else "")
                parts.append("<|%s|>" % self._marker_names[i])
                run = []
            else:
                run.append(i)
        parts.append(self.tok.decode(run) if run else "")
        return "".join(parts), len(out), was_cut
