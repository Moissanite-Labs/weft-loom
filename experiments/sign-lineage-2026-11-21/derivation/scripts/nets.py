"""Small networks trained from scratch, many at once (batched over models).

Sampled evidence only. Run with an interpreter that has torch (2.15 was used):
  python -I nets.py ...

Model (per network): two-token context (t1, t2) -> next token t3, vocabulary V.
  r = E1[t1] + E2[t2]                      (d dims)
  for each of L blocks: n = rmsnorm(r) * gain;  r = r + block(n)
     gated:  block(n) = D (act(G n) * (U n))   act = SiLU   (SwiGLU form)
     plain:  block(n) = D act(U n)             act = ReLU, GELU or tanh
  logits = W rmsnorm(r) * gain_f
Hidden trace of unit i in block l = the vector multiplied by D (the input of D).
Training: AdamW (decoupled weight decay), constant learning rate, cross-entropy.
The data stream is fixed by (teacher seed, stream seed) and shared by every
network trained on it. All inits are i.i.d. zero-mean normal (sign and
permutation invariant law).
"""
import numpy as np
import torch

V = 48
D_MODEL = 32
N_LAYERS = 2
BATCH = 256


def teacher_table(teacher_seed):
    """P(t3 | t1, t2) from a fixed random tanh network; returns float64 [V,V,V]."""
    rng = np.random.default_rng(teacher_seed)
    e1 = rng.normal(size=(V, 24))
    e2 = rng.normal(size=(V, 24))
    W1 = rng.normal(size=(24, 24)) / np.sqrt(24)
    Wo = rng.normal(size=(24, V)) * 1.6
    bias = rng.normal(size=V) * 1.0
    z = np.tanh((e1[:, None, :] + e2[None, :, :]) @ W1)  # [V,V,24]
    logits = z @ Wo + bias
    logits -= logits.max(axis=-1, keepdims=True)
    p = np.exp(logits)
    return p / p.sum(axis=-1, keepdims=True)


def stream(teacher_seed, stream_seed, steps, batch=BATCH):
    """Fixed data stream: `batch` parallel order-2 chains; returns int64 [steps, batch, 3]."""
    P = teacher_table(teacher_seed)
    cdf = np.cumsum(P, axis=-1)
    rng = np.random.default_rng(stream_seed)
    t1 = rng.integers(0, V, size=batch)
    t2 = rng.integers(0, V, size=batch)
    # burn in 50 steps
    out = np.empty((steps, batch, 3), dtype=np.int64)
    for s in range(-50, steps):
        u = rng.random(batch)
        t3 = (cdf[t1, t2] < u[:, None]).sum(axis=1)
        t3 = np.minimum(t3, V - 1)
        if s >= 0:
            out[s, :, 0], out[s, :, 1], out[s, :, 2] = t1, t2, t3
        t1, t2 = t2, t3
    return out


def probe_set(n=4096, teacher_seed=0, stream_seed=987654):
    """Fixed probe tokens (the 'shared corpus'), drawn from teacher 0 by a held-out stream."""
    s = stream(teacher_seed, stream_seed, steps=n // 256, batch=256)
    return s.reshape(-1, 3)[:, :2]


def act_fn(kind):
    return {"silu": torch.nn.functional.silu, "relu": torch.relu,
            "gelu": torch.nn.functional.gelu, "tanh": torch.tanh}[kind]


def init_params(seeds, block, h, d=D_MODEL, L=N_LAYERS):
    """One independent init per seed; returns dict of tensors with leading model axis."""
    ps = {k: [] for k in ["E1", "E2", "W", "gf"] + ["G%d" % l for l in range(L)] +
          ["U%d" % l for l in range(L)] + ["D%d" % l for l in range(L)] + ["g%d" % l for l in range(L)]}
    for sd in seeds:
        rng = np.random.default_rng(int(sd))
        ps["E1"].append(rng.normal(size=(V, d)))
        ps["E2"].append(rng.normal(size=(V, d)))
        ps["W"].append(rng.normal(size=(V, d)) / np.sqrt(d))
        ps["gf"].append(np.ones(d))
        for l in range(L):
            ps["G%d" % l].append(rng.normal(size=(h, d)) / np.sqrt(d))
            ps["U%d" % l].append(rng.normal(size=(h, d)) / np.sqrt(d))
            ps["D%d" % l].append(rng.normal(size=(d, h)) / np.sqrt(h))
            ps["g%d" % l].append(np.ones(d))
    out = {k: torch.tensor(np.stack(v), dtype=torch.float32) for k, v in ps.items()}
    if block != "gated":
        for l in range(L):
            out.pop("G%d" % l)
    return out


def rms(x, g):
    return x * torch.rsqrt((x * x).mean(-1, keepdim=True) + 1e-6) * g[:, None, :]


def forward(P, t1, t2, block, act, L=N_LAYERS, want_traces=False):
    r = P["E1"][:, t1, :] + P["E2"][:, t2, :]  # [M,B,d]
    traces, resid = [], []
    for l in range(L):
        n = rms(r, P["g%d" % l])
        u = torch.einsum("mbd,mhd->mbh", n, P["U%d" % l])
        if block == "gated":
            hid = act(torch.einsum("mbd,mhd->mbh", n, P["G%d" % l])) * u
        else:
            hid = act(u)
        r = r + torch.einsum("mbh,mdh->mbd", hid, P["D%d" % l])
        if want_traces:
            traces.append(hid)
            resid.append(r)
    logits = torch.einsum("mbd,mvd->mbv", rms(r, P["gf"]), P["W"])
    if want_traces:
        return logits, traces, resid
    return logits


def train(P, data, block, actname, lr=3e-3, wd=0.01, log_every=0, snap_at=()):
    """Train all models in P in place on the data stream [steps, B, 3].
    Returns (final loss per model, {step: param copy} for steps in snap_at)."""
    act = act_fn(actname)
    params = [p.requires_grad_(True) for p in P.values()]
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=wd, betas=(0.9, 0.99), eps=1e-8)
    data_t = torch.from_numpy(data)
    M = next(iter(P.values())).shape[0]
    losses = None
    snaps = {}
    for s in range(data.shape[0]):
        b = data_t[s]
        logits = forward(P, b[:, 0], b[:, 1], block, act)
        lp = torch.log_softmax(logits, -1)
        nll = -lp.gather(-1, b[:, 2][None, :, None].expand(M, -1, 1)).squeeze(-1).mean(-1)  # [M]
        loss = nll.sum()
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if s >= data.shape[0] - min(50, data.shape[0]):
            losses = nll.detach() if losses is None else losses + nll.detach()
        if log_every and s % log_every == 0:
            print("step", s, "mean nll", float(nll.detach().mean()), flush=True)
        if (s + 1) in snap_at:
            snaps[s + 1] = {k: v.detach().clone() for k, v in P.items()}
    for p in params:
        p.requires_grad_(False)
    n_last = min(50, data.shape[0])
    return (losses / n_last).numpy(), snaps


def traces_of(P, block, actname, probe):
    with torch.no_grad():
        t = torch.from_numpy(probe)
        _, tr, rs = forward(P, t[:, 0], t[:, 1], block, act_fn(actname), want_traces=True)
    return [x.numpy().astype(np.float64) for x in tr], [x.numpy().astype(np.float64) for x in rs]


def save(path, P, meta):
    np.savez_compressed(path, **{k: v.detach().numpy() for k, v in P.items()},
                        meta=np.array(repr(meta)))


def load(path):
    z = np.load(path, allow_pickle=False)
    P = {k: torch.tensor(z[k]) for k in z.files if k != "meta"}
    return P, str(z["meta"])
