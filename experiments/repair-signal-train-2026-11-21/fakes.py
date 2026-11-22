"""Fake service client, used by the dry run and the tests. Nothing here
touches a network, a key or a model.

The method and argument names follow the installed client library (tinker
0.39.0), and checks/tinker_api_check.py compares them with it: client creation
and checkpoint saving return a future, and the client is its .result()."""


class FakeFuture:
    def __init__(self, value=None, error=None):
        self._value, self._error = value, error

    def result(self):
        if self._error is not None:
            raise self._error
        return self._value


class FakeModelInput:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.length = len(self.tokens)

    @classmethod
    def from_ints(cls, tokens):
        return cls(tokens)


class FakeDatum:
    def __init__(self, model_input, loss_fn_inputs):
        self.model_input, self.loss_fn_inputs = model_input, loss_fn_inputs


class FakeAdam:
    def __init__(self, learning_rate=0.0001, beta1=0.9, beta2=0.95, eps=1e-12, weight_decay=0.0, grad_clip_norm=0.0):
        self.learning_rate = learning_rate


class FakeSamplingParams:
    def __init__(self, max_tokens=None, seed=None, stop=None, temperature=1, top_k=-1, top_p=1):
        self.max_tokens, self.temperature, self.stop = max_tokens, temperature, stop


class FakeTokenizer:
    """One id per character (its code point), and special ids from 1000 up."""
    SPECIALS = {"message_user": 1000, "message_model": 1001, "message_system": 1002, "content_text": 1004, "content_thinking": 1005,
                "end_message": 1010, "content_model_end_sampling": 1006}

    def encode_ordinary(self, text):
        return [ord(ch) for ch in text]

    def encode_special(self, name):
        return self.SPECIALS[name]

    def decode(self, ids):
        return "".join(chr(i) for i in ids)

    def is_special_token(self, i):
        """The named specials above and the unnamed special ids around them (1000 to 1020)."""
        return 1000 <= i <= 1020


class FakeTypes:
    ModelInput = FakeModelInput
    Datum = FakeDatum
    AdamParams = FakeAdam
    SamplingParams = FakeSamplingParams


class _Seq:
    def __init__(self, tokens):
        self.tokens = tokens


class _Resp:
    def __init__(self, tokens):
        self.sequences = [_Seq(tokens)]


class FakeSampler:
    count = 0       # handles are numbered in order of creation

    def __init__(self, reply_tokens=(1, 2, 3), overrun=False):
        FakeSampler.count += 1
        self.handle = "fake-sampler-handle-%d" % FakeSampler.count
        self.reply_tokens = list(reply_tokens)
        self.overrun = overrun      # a misbehaving server that ignores max_tokens
        self.calls, self.prompts, self.stops = [], [], []

    def get_sampler_handle(self):
        return self.handle

    def sample(self, prompt, num_samples, sampling_params, include_prompt_logprobs=False, topk_prompt_logprobs=0,
               topk_sample_logprobs=0, target_prompt_logprobs=None, prompt_alt_tokens_k=0, prompt_logprobs_last_n=None):
        self.calls.append((prompt.length, num_samples, sampling_params.max_tokens))
        self.prompts.append(list(prompt.tokens))
        self.stops.append(sampling_params.stop)
        toks = self.reply_tokens if self.overrun else self.reply_tokens[:sampling_params.max_tokens]
        return FakeFuture(_Resp(toks))


class ScriptedSampler(FakeSampler):
    """Replies with scripted texts in call order, one per call, cycling. encode
    turns a text into reply token ids (the reply and its end marker)."""

    def __init__(self, texts, encode):
        super().__init__()
        self.texts, self.encode = list(texts), encode

    def sample(self, prompt, num_samples, sampling_params, **kw):
        self.reply_tokens = list(self.encode(self.texts[len(self.calls) % len(self.texts)]))
        return super().sample(prompt, num_samples, sampling_params, **kw)


class FakeTrainingClient:
    def __init__(self, fail_with=None, sampler=None):
        self.calls, self.fail_with = [], fail_with
        self.saved = 0
        self.sampler = sampler

    def forward_backward(self, data, loss_fn, loss_fn_config=None):
        self.calls.append(("forward_backward", len(data), loss_fn))
        if self.fail_with is not None:
            raise self.fail_with
        return FakeFuture(None)

    def optim_step(self, optim_params=None, *, adam_params=None):
        adam = optim_params if optim_params is not None else adam_params
        self.calls.append(("optim_step", adam.learning_rate))
        return FakeFuture(None)

    def save_weights_and_get_sampling_client(self, name=None, retry_config=None, record_stability_info=False,
                                             kind="snapshot"):
        self.saved += 1
        return FakeFuture(self.sampler if self.sampler is not None else FakeSampler())


class FakeService:
    """checkpoint_samplers: the sampler each training client saves, in the
    order the clients are created. base: the sampler for the untrained model."""

    def __init__(self, fail_with=None, checkpoint_samplers=None, base=None):
        self.created, self.fail_with = [], fail_with
        self.clients = []
        self.checkpoint_samplers, self.base = list(checkpoint_samplers or []), base

    def create_lora_training_client(self, base_model, rank=32, seed=None, train_mlp=True, train_attn=True,
                                    train_unembed=True, user_metadata=None, optimizer=None):
        self.created.append(dict(base_model=base_model, rank=rank, seed=seed, train_mlp=train_mlp,
                                 train_attn=train_attn, train_unembed=train_unembed))
        i = len(self.clients)
        sampler = self.checkpoint_samplers[i] if i < len(self.checkpoint_samplers) else None
        client = FakeTrainingClient(self.fail_with, sampler)
        self.clients.append(client)
        return FakeFuture(client)

    def create_sampling_client(self, model_path=None, base_model=None, retry_config=None, record_stability_info=False):
        return FakeFuture(self.base if self.base is not None else FakeSampler())
