"""Static conformance of the paid backend with the installed service library.

The paid backend (tinker_backend.py) and the driver were adapted from scripts
written for an earlier model and have never met the real client library. This
check compares what they rely on with what the installed package defines. It
reads signatures and annotations with inspect, and it builds the plain data
types the backend builds (a training example, optimiser and sampling
parameters). It never builds a client, never opens a connection, never reads a
key file and does not look at the key variable's value.

Run it with a Python that has the library and tml_renderers, in isolated mode:

    PATH-TO-VENV-PYTHON -I checks/tinker_api_check.py [--old-scripts PATH ...]

--old-scripts names the earlier scripts the backend was adapted from, to list
every call they make differently. One line is printed per call: OK, MISMATCH,
UNSETTLED (cannot be settled from the installed code) or NOTE (a difference in
an earlier script, not in this record). Exit 0 when there is no
MISMATCH, 1 when there is one, 2 when the library cannot be imported.

How the call sites are found: the source of tinker_backend.py, driver.py and
pilot_cli.py is parsed (ast), every call of a watched method name is bound
against the real signature with its own positional count and keyword names, and
the fake client in fakes.py is bound the same way and must not accept a name the
real one lacks.
"""
import ast
import inspect
import os
import sys
import typing

HERE = os.path.dirname(os.path.abspath(__file__))
LOOP = os.path.dirname(HERE)
sys.path.insert(0, LOOP)

LINES = []


def say(status, name, text=""):
    LINES.append(status)
    print("%-10s %-52s %s" % (status, name, text))


def ok(name, text="matches"):
    say("OK", name, text)


def bad(name, text):
    say("MISMATCH", name, text)


def unsettled(name, text):
    say("UNSETTLED", name, text)


def note(name, text):
    say("NOTE", name, text)


try:
    import tinker
    from tinker import types as T
except ImportError as exc:
    print("cannot import the installed library: %s" % type(exc).__name__)
    sys.exit(2)

import fakes  # noqa: E402
import tinker_backend  # noqa: E402

SOURCES = ("tinker_backend.py", "driver.py", "pilot_cli.py")

# watched method name -> (real class, fake class, whether the call returns a future whose .result() is used)
WATCH = {
    "create_lora_training_client": (tinker.ServiceClient, fakes.FakeService, True),
    "create_sampling_client": (tinker.ServiceClient, fakes.FakeService, True),
    "forward_backward": (tinker.TrainingClient, fakes.FakeTrainingClient, True),
    "optim_step": (tinker.TrainingClient, fakes.FakeTrainingClient, True),
    "save_weights_and_get_sampling_client": (tinker.TrainingClient, fakes.FakeTrainingClient, True),
    "sample": (tinker.SamplingClient, fakes.FakeSampler, True),
}
# watched method name -> more fake classes whose method is bound the same way
EXTRA_FAKES = {"sample": (fakes.WindowSampler,)}
# constructor or factory name -> (real callable, fake callable)
TYPES = {
    "Datum": (T.Datum, fakes.FakeTypes.Datum),
    "AdamParams": (T.AdamParams, fakes.FakeTypes.AdamParams),
    "SamplingParams": (T.SamplingParams, fakes.FakeTypes.SamplingParams),
    "from_ints": (T.ModelInput.from_ints, fakes.FakeTypes.ModelInput.from_ints),
}


def parse(name):
    path = os.path.join(LOOP, name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return ast.parse(fh.read(), filename=name)


def call_sites(tree):
    """(watched name, positional nodes, keyword dict of nodes, the Call node)
    for direct calls and for calls routed through _guard(fn, args...)."""
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn, args, kws = node.func, list(node.args), {k.arg: k.value for k in node.keywords if k.arg}
        star = any(isinstance(a, ast.Starred) for a in args) or any(k.arg is None for k in node.keywords)
        if isinstance(fn, ast.Name) and fn.id == "_guard" and args and isinstance(args[0], ast.Attribute):
            fn, args = args[0], args[1:]
        name = fn.attr if isinstance(fn, ast.Attribute) else None
        if name in WATCH or name in TYPES:
            out.append((name, args, kws, node, star))
    return out


def bind(fn, args, kws, is_method):
    sig = inspect.signature(fn)
    pos = ([None] if is_method else []) + list(args)
    return sig.bind(*pos, **kws), sig


def check_signature(label, real, fake, args, kws, is_method):
    try:
        bound, sig = bind(real, args, kws, is_method)
    except TypeError as exc:
        bad(label, "the call does not fit the real signature: %s" % exc)
        return None
    bad_names = [k for k in kws if k not in sig.parameters]
    if bad_names:
        bad(label, "unknown argument names %s" % bad_names)
        return None
    # the fake must accept the call and must not accept a name the real one lacks
    try:
        bind(fake, args, kws, is_method)
    except TypeError as exc:
        bad(label + " (fake)", "the fake does not accept the call: %s" % exc)
        return bound
    real_names = set(sig.parameters)
    fake_sig = inspect.signature(fake)
    extra = [n for n, p in fake_sig.parameters.items()
             if n != "self" and p.kind not in (p.VAR_KEYWORD, p.VAR_POSITIONAL) and n not in real_names]
    if extra:
        bad(label + " (fake)", "the fake takes names the real one lacks: %s" % extra)
    elif any(p.kind == p.VAR_KEYWORD for p in fake_sig.parameters.values()):
        bad(label + " (fake)", "the fake takes **kwargs, so a wrong name would pass unseen")
    else:
        real_order = [n for n in sig.parameters if n != "self"][:len([p for p in fake_sig.parameters if p != "self"])]
        fake_order = [n for n in fake_sig.parameters if n != "self"]
        if real_order != fake_order[:len(real_order)] and set(fake_order) <= real_names:
            bad(label + " (fake)", "the fake's argument order %s differs from the real %s" % (fake_order, real_order))
    return bound


def future_class(real):
    """The class a method's return annotation names, looked up in the library."""
    ann = inspect.signature(real).return_annotation
    name = ann if isinstance(ann, str) else getattr(ann, "__name__", "")
    base = name.split("[")[0].strip("'\" ")
    return getattr(tinker, base, None), name


def uses_result(tree, node):
    """True if the value of this call is used through .result() (directly, or through the name it is assigned to)."""
    parents = {}
    for p in ast.walk(tree):
        for c in ast.iter_child_nodes(p):
            parents[c] = p
    cur = node
    # climb out of a _guard(...) wrapper
    while cur in parents and isinstance(parents[cur], ast.Call) and isinstance(parents[cur].func, ast.Name):
        cur = parents[cur]
    if isinstance(parents.get(cur), ast.Lambda) and isinstance(parents.get(parents[cur]), ast.Call):
        cur = parents[parents[cur]]            # _guard(lambda: ....sample(...)): the value of the _guard call
    par = parents.get(cur)
    if isinstance(par, ast.Attribute) and par.attr == "result":
        return True
    if isinstance(par, ast.Assign) and len(par.targets) == 1 and isinstance(par.targets[0], ast.Name):
        var = par.targets[0].id
        scope = cur
        while scope in parents and not isinstance(scope, (ast.FunctionDef, ast.Lambda)):
            scope = parents[scope]
        return any(isinstance(n, ast.Attribute) and n.attr == "result" and isinstance(n.value, ast.Name)
                   and n.value.id == var for n in ast.walk(scope))
    return False


def kept_in_flight_and_read(tree, node):
    """The windowed responder keeps the value of sample() in a pending list and reads it
    later, so the value is not read in the function that made it. True if the value is
    passed to _Flight(...) as its future, and the module reads a `.future.result` somewhere."""
    parents = {c: p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
    cur = node
    if isinstance(parents.get(cur), ast.Lambda) and isinstance(parents.get(parents[cur]), ast.Call):
        cur = parents[parents[cur]]
    par = parents.get(cur)
    if not (isinstance(par, ast.Assign) and len(par.targets) == 1 and isinstance(par.targets[0], ast.Name)):
        return False
    var = par.targets[0].id
    passed = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_Flight"
                 and any(isinstance(a, ast.Name) and a.id == var for a in n.args) for n in ast.walk(tree))
    read = any(isinstance(n, ast.Attribute) and n.attr == "result" and isinstance(n.value, ast.Attribute)
               and n.value.attr == "future" for n in ast.walk(tree))
    return passed and read


def check_calls():
    seen = set()
    for src in SOURCES:
        tree = parse(src)
        if tree is None:
            continue
        for name, args, kws, node, star in call_sites(tree):
            label = "%s:%d %s" % (src, node.lineno, name)
            if star:
                unsettled(label, "the call uses * or ** arguments, so its names cannot be read statically")
                continue
            if name in WATCH:
                real_cls, fake_cls, futured = WATCH[name]
                real, fake = getattr(real_cls, name), getattr(fake_cls, name)
                bound = check_signature(label, real, fake, args, kws, True)
                if bound is None:
                    continue
                msgs = []
                if name == "forward_backward":
                    lf = bound.arguments.get("loss_fn")
                    allowed = typing.get_args(T.LossFnType)
                    if isinstance(lf, ast.Constant):
                        if lf.value not in allowed:
                            bad(label, "the loss name %r is not one of %s" % (lf.value, allowed))
                            continue
                        msgs.append("loss %r is a defined loss name" % lf.value)
                fut, ann = future_class(real)
                if futured:
                    if fut is None or not hasattr(fut, "result"):
                        bad(label, "the return annotation %r has no result()" % ann)
                        continue
                    if uses_result(tree, node):
                        msgs.append("returns %s, used through .result()" % fut.__name__)
                    elif kept_in_flight_and_read(tree, node):
                        msgs.append("returns %s, kept pending in a window and read through .future.result()"
                                    % fut.__name__)
                    else:
                        bad(label, "returns %s (a future) but the code does not call .result() on it" % ann)
                        continue
                for extra in EXTRA_FAKES.get(name, ()):
                    check_signature(label + " (%s)" % extra.__name__, real, getattr(extra, name), args, kws, True)
                ok(label, "; ".join(["arguments match"] + msgs))
                seen.add(name)
            else:
                real, fake = TYPES[name]
                bound = check_signature(label, real, fake, args, kws, False)
                if bound is not None:
                    ok(label, "arguments match")
                    seen.add(name)
    for name in list(WATCH) + list(TYPES):
        if name not in seen:
            unsettled(name, "no call site found in the backend, driver or runner")


def check_sample_dispatch():
    """What the windowed responder relies on: sample() is a plain method that hands the
    request to the library's background loop when it is called and returns a pending future,
    so several calls can be in flight before the first result is read. Read from the source of
    the installed package: no client is built and nothing is sent."""
    src = inspect.getsource(tinker.SamplingClient.sample)
    if inspect.iscoroutinefunction(tinker.SamplingClient.sample):
        bad("SamplingClient.sample dispatch", "sample is a coroutine function: a call would send nothing until awaited")
    elif "run_coroutine_threadsafe(_sample_async" not in src or ".result(" in src.split("return _AwaitableFutureCompatWrapper")[-1]:
        bad("SamplingClient.sample dispatch", "the source no longer submits the request to the background loop at call time")
    else:
        ok("SamplingClient.sample dispatch", "a plain method that submits the request to the library's background loop "
           "with run_coroutine_threadsafe and returns the pending future without waiting")
    wrap = tinker.lib.public_interfaces.sampling_client._AwaitableFutureCompatWrapper \
        if hasattr(tinker, "lib") else None
    if wrap is None:
        unsettled("sample future .result", "the wrapper class could not be found")
    else:
        for fake_cls in (fakes.PendingFuture, fakes.FakeFuture):
            try:
                bind(wrap.result, [], {}, True)
                bind(fake_cls.result, [], {}, True)
            except TypeError as exc:
                bad("sample future .result (%s)" % fake_cls.__name__, "does not accept a call with no argument: %s" % exc)
                continue
            real_names = set(inspect.signature(wrap.result).parameters)
            extra = [n for n in inspect.signature(fake_cls.result).parameters if n != "self" and n not in real_names]
            if extra:
                bad("sample future .result (%s)" % fake_cls.__name__, "the fake takes names the real one lacks: %s" % extra)
            else:
                ok("sample future .result (%s)" % fake_cls.__name__, "takes no required argument and no name the library's lacks")
    unsettled("sample concurrency limit", "the request limit is server-controlled (sample_max_concurrent_requests, "
              "default 2000 in the library's own client config) and the service's real limit for this account is not observable here")
    unsettled("sample retries", "the library retries a failed or backpressured request itself with no count limit "
              "(RetryHandler, exponential backoff 0.5 s to 10 s, stuck after 120 minutes without progress), and whether "
              "a retried request that the service had already accepted is billed twice is not observable here")


def check_return_shapes():
    seq = T.SampleResponse
    if "sequences" not in {f for f in getattr(seq, "__dataclass_fields__", {})}:
        bad("SampleResponse.sequences", "the field is missing")
    else:
        ok("SampleResponse.sequences", "a field of the response (a sequence of SampledSequence)")
    if not hasattr(T.SampledSequence, "tokens"):
        bad("SampledSequence.tokens", "the attribute is missing")
    else:
        ann = typing.get_type_hints(T.SampledSequence.tokens.func).get("return")
        ok("SampledSequence.tokens", "a property returning %s" % ann)
    if not hasattr(T.ModelInput, "length"):
        bad("ModelInput.length", "the attribute is missing")
    else:
        ok("ModelInput.length", "present (the backend bills sum(length + 1))")
    for kind in ("stop",):
        ann = T.SamplingParams.model_fields[kind].annotation
        if int not in [a for arg in typing.get_args(ann) for a in typing.get_args(arg)]:
            bad("SamplingParams.stop", "ids are not an accepted type: %s" % (ann,))
        else:
            ok("SamplingParams.stop", "accepts a sequence of integer ids")
    for field, want in (("max_tokens", int), ("temperature", float)):
        ann = T.SamplingParams.model_fields[field].annotation
        if want in (ann, *typing.get_args(ann)):
            ok("SamplingParams.%s" % field, "type %s" % (want.__name__))
        else:
            bad("SamplingParams.%s" % field, "annotation %s" % (ann,))


def check_construction():
    """Builds the plain data objects the backend builds, with the backend's own function."""
    try:
        d = tinker_backend.make_datum(T, [10, 11, 12], [13, 14])
    except Exception as exc:
        bad("make_datum on the real types", "%s: %s" % (type(exc).__name__, str(exc)[:200]))
        return
    li = d.loss_fn_inputs
    got = {k: (str(v.dtype), list(v.shape), list(v.data)) for k, v in sorted(li.items())}
    want = {"target_tokens": ("int64", [4], [11, 12, 13, 14]), "weights": ("float32", [4], [0.0, 0.0, 1.0, 1.0])}
    names = {k: (v[0], v[1], v[2]) for k, v in got.items()}
    if set(names) != set(want):
        bad("Datum.loss_fn_inputs keys", "built %s, wanted %s" % (sorted(names), sorted(want)))
    elif any(str(names[k][0]) != want[k][0] or names[k][1] != want[k][1] or names[k][2] != want[k][2] for k in want):
        bad("Datum.loss_fn_inputs values", "built %s, wanted %s" % (names, want))
    else:
        ok("Datum.loss_fn_inputs", "weights float32 and target_tokens int64, shifted by one, as the backend means")
    if d.model_input.length != 4:
        bad("Datum.model_input", "length %s, wanted 4 (the last token is dropped)" % d.model_input.length)
    else:
        ok("Datum.model_input", "length 4 for 5 ids (the last token is dropped)")
    try:
        T.AdamParams(learning_rate=1e-3)
        T.SamplingParams(max_tokens=97, temperature=0.0, stop=[1, 2])
        T.ModelInput.from_ints(tokens=[1, 2, 3])
        ok("AdamParams, SamplingParams, ModelInput", "build with the backend's arguments (temperature 0.0, integer stop ids)")
    except Exception as exc:
        bad("AdamParams, SamplingParams, ModelInput", "%s: %s" % (type(exc).__name__, str(exc)[:200]))


def check_fakes_dynamic():
    svc = fakes.FakeService()
    fut = svc.create_lora_training_client(base_model="m", rank=8, seed=0, train_mlp=True, train_attn=True,
                                          train_unembed=True)
    client = fut.result() if hasattr(fut, "result") else None
    if client is None or not hasattr(client, "forward_backward"):
        bad("fake create_lora_training_client", "does not return a future of a client")
    elif not hasattr(svc.create_sampling_client(base_model="m"), "result"):
        bad("fake create_sampling_client", "does not return a future")
    elif not hasattr(client.save_weights_and_get_sampling_client(), "result"):
        bad("fake save_weights_and_get_sampling_client", "does not return a future")
    else:
        ok("fake client", "creation and saving return futures, as the library does")


def check_sampler_identity():
    """What the backend relies on to name a saved checkpoint's sampler."""
    sig = inspect.signature(tinker.SamplingClient.get_sampler_handle)
    ann = typing.get_type_hints(tinker.SamplingClient.get_sampler_handle).get("return")
    if [n for n in sig.parameters if n != "self"] or ann is not str:
        bad("SamplingClient.get_sampler_handle", "signature %s -> %s, wanted no arguments and a str" % (sig, ann))
    else:
        ok("SamplingClient.get_sampler_handle", "takes no arguments and returns a str (a credential-free handle)")
    fsig = inspect.signature(fakes.FakeSampler.get_sampler_handle)
    if [n for n in fsig.parameters if n != "self"] or not isinstance(fakes.FakeSampler().get_sampler_handle(), str):
        bad("fake get_sampler_handle", "does not match the library's")
    else:
        ok("fake get_sampler_handle", "matches the library's")
    ret = typing.get_type_hints(tinker.TrainingClient.save_weights_and_get_sampling_client).get("return")
    public = [n for n in dir(tinker.SamplingClient) if not n.startswith("_") and ("checkpoint" in n or "path" in n)]
    if public:
        unsettled("saved checkpoint identifier", "the client has public names %s: bind to one of them" % public)
    else:
        unsettled("saved checkpoint identifier", "the library returns %s with no public checkpoint id; the backend "
                  "binds by the object the run holds and by the SHA-256 of the handle"
                  % getattr(ret, "__name__", str(ret)))


def check_credentials():
    sig = inspect.signature(tinker.ServiceClient.__init__)
    if any(p.default is inspect.Parameter.empty for n, p in sig.parameters.items()
           if n != "self" and p.kind not in (p.VAR_KEYWORD, p.VAR_POSITIONAL)):
        bad("ServiceClient()", "has a required argument")
    else:
        ok("ServiceClient()", "builds with no arguments, so the backend passes none")
    # the text of the library, searched for the variable names it reads (no value is read)
    import tinker.lib.internal_client_holder as holder
    import tinker.lib._auth_token_provider as auth
    src = inspect.getsource(holder) + inspect.getsource(auth)
    if 'os.environ.get("TINKER_API_KEY")' in src:
        ok("credentials: the key variable", "TINKER_API_KEY is read when no api_key is passed")
    else:
        bad("credentials: the key variable", "TINKER_API_KEY is not read by the library")
    if "default_credentials_path()" in src and "get_default_key" in src:
        unsettled("credentials: other sources",
                  "with the variable unset, the library falls back to a stored credentials file and to "
                  "TINKER_CREDENTIAL_CMD, so the runner refuses to start unless the variable is non-empty")
    if "resolve_base_url" in inspect.getsource(holder):
        unsettled("credentials: service address", "the library also reads a base-URL variable and a config file; "
                  "the runner does not set or check them")


def check_tokenizer():
    try:
        from tml_renderers import renderers
    except ImportError:
        unsettled("tokenizer", "tml_renderers is not importable here")
        return
    rend = renderers.Inkling2()
    tk = rend.tokenizer
    tk = tk() if callable(tk) else tk
    for name, nparams in (("encode_ordinary", 1), ("encode_special", 1), ("decode", 1), ("is_special_token", 1)):
        fn = getattr(tk, name, None)
        if fn is None:
            bad("tokenizer." + name, "missing")
            continue
        n = len([p for p in inspect.signature(fn).parameters.values()
                 if p.default is inspect.Parameter.empty])
        if n != nparams:
            bad("tokenizer." + name, "takes %d required arguments, the codec passes %d" % (n, nparams))
        else:
            ok("tokenizer." + name, "takes %d argument, as the codec calls it" % nparams)
    import codec as codec_mod
    try:
        c = codec_mod.Codec(tk)
        ok("Codec on the real tokenizer", "every marker is one distinct id (end %d, eos %d)" % (c.end, c.eos))
    except Exception as exc:
        bad("Codec on the real tokenizer", "%s: %s" % (type(exc).__name__, exc))


def check_old_scripts(paths):
    """Lists the watched calls the earlier scripts make and how."""
    if not paths:
        unsettled("earlier scripts", "none were named with --old-scripts")
        return
    called = {}
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
        except (OSError, SyntaxError):
            unsettled("earlier script", "%s cannot be read" % os.path.basename(path))
            continue
        parents = {c: p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and not (isinstance(node.func.value, ast.Name) and node.func.value.id in ("rng", "random")):
                nm = node.func.attr
                if nm in WATCH or nm in TYPES:
                    par = parents.get(node)
                    direct = isinstance(par, ast.Attribute) and par.attr == "result"
                    called.setdefault(nm, []).append((os.path.basename(path), sorted(k.arg for k in node.keywords if k.arg),
                                                      len(node.args), direct))
    for nm in list(WATCH) + list(TYPES):
        rows = called.get(nm)
        if not rows:
            unsettled("earlier scripts: " + nm, "neither earlier script calls it, so it has no run against the real service behind it")
            continue
        for fname, kws, npos, direct in rows[:1]:
            if nm == "create_lora_training_client" and not direct:
                note("earlier scripts: " + nm, "%s uses the returned future as the client (no .result()); the library "
                    "marks that deprecated, and the backend now calls .result()" % fname)
            elif nm == "optim_step":
                ok("earlier scripts: " + nm, "%s passes the optimiser parameters positionally, as the backend does" % fname)
            else:
                ok("earlier scripts: " + nm, "%s calls it with %d positional and keywords %s" % (fname, npos, kws))


def main(argv):
    old = []
    if "--old-scripts" in argv:
        old = [a for a in argv[argv.index("--old-scripts") + 1:] if not a.startswith("--")]
    print("tinker %s" % getattr(tinker, "__version__", "?"))
    check_calls()
    check_return_shapes()
    check_construction()
    check_fakes_dynamic()
    check_sample_dispatch()
    check_sampler_identity()
    check_credentials()
    check_tokenizer()
    check_old_scripts(old)
    counts = {s: LINES.count(s) for s in ("OK", "MISMATCH", "UNSETTLED", "NOTE")}
    print("%d OK, %d MISMATCH, %d UNSETTLED, %d NOTE" % (counts["OK"], counts["MISMATCH"], counts["UNSETTLED"], counts["NOTE"]))
    return 1 if counts["MISMATCH"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
