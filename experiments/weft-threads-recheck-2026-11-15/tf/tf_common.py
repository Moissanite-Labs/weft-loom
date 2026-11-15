"""Shared pieces copied from the committed probes/tf_splice*.py (same model, same sampler order),
with three additive options that default to the committed behaviour:
  batch(..., split=, rec=)   split 'any' (committed), 'train' (excludes held-out tuples), 'test' (only held-out)
  TF.forward(..., gate=)     optional per-example multiplier on the packet output
Held-out set: operand tuples whose six values (0..15) sum to a multiple of 7 (about 1/7 of tuples).
Task ids: 0 COPY, 1 ADD3, 2 MUL5 (position-wise), 3 REVERSE (needs attention).
"""
import copy
import math
import sys

import torch
import torch.nn as nn
import torch.nn.functional as F

torch.set_num_threads(int(__import__("os").environ.get("TF_THREADS", "2")))

V, L, D, H, FF, NDATA = 21, 14, 128, 4, 256, 16
TOK = {0: 1, 1: 2, 2: 3, 3: 3}
SEP = 4


def die(msg):
    print("INCONSISTENCY: " + msg, file=sys.stderr, flush=True)
    raise SystemExit(2)


def is_heldout(xv):
    return int(sum(xv)) % 7 == 0


def key_of(xv):
    k = 0
    for v in xv:
        k = k * 16 + int(v)
    return k


def batch(tasks, n, g, split="any", rec=None):
    xs, ys = [], []
    for _ in range(n):
        t = tasks[int(torch.randint(len(tasks), (1,), generator=g))]
        x = torch.randint(0, NDATA, (6,), generator=g) + 5
        if split != "any":
            while True:
                ho = is_heldout((x - 5).tolist())
                if (split == "train" and not ho) or (split == "test" and ho):
                    break
                x = torch.randint(0, NDATA, (6,), generator=g) + 5
        if rec is not None:
            rec.add(key_of((x - 5).tolist()))
        if t == 0:
            y = x.clone()
        elif t == 1:
            y = 5 + ((x - 5 + 3) % NDATA)
        elif t == 2:
            y = 5 + (((x - 5) * 5) % NDATA)
        elif t == 3:
            y = torch.flip(x, [0])
        else:
            die("bad task")
        seq = torch.cat([torch.tensor([TOK[t]]), x, torch.tensor([SEP]), y])
        xs.append(seq)
        tgt = torch.full((L,), -100)
        tgt[8:] = y
        ys.append(tgt)
    return torch.stack(xs), torch.stack(ys)


class Block(nn.Module):
    def __init__(self):
        super().__init__()
        self.ln1, self.ln2 = nn.LayerNorm(D), nn.LayerNorm(D)
        self.attn = nn.MultiheadAttention(D, H, batch_first=True)
        self.up, self.down = nn.Linear(D, FF), nn.Linear(FF, D)

    def mlp(self, h):
        return self.down(F.gelu(self.up(h)))

    def forward(self, x, mask):
        h = self.ln1(x)
        a, _ = self.attn(h, h, h, attn_mask=mask, need_weights=False)
        x = x + a
        x = x + self.mlp(self.ln2(x))
        return x


class TF(nn.Module):
    def __init__(self):
        super().__init__()
        self.emb = nn.Embedding(V, D)
        self.pos = nn.Embedding(L, D)
        self.b1, self.b2 = Block(), Block()
        self.lnf = nn.LayerNorm(D)
        self.head = nn.Linear(D, V, bias=False)

    def forward(self, x, packet=None, splice_slots=None, gate=None):
        mask = torch.full((L, L), float("-inf")).triu(1)
        h = self.emb(x) + self.pos(torch.arange(L))
        h = self.b1(h, mask)
        b = self.b2
        hh = b.ln1(h)
        a, _ = b.attn(hh, hh, hh, attn_mask=mask, need_weights=False)
        h = h + a
        m = b.ln2(h)
        h = h + b.mlp(m)
        if packet is not None:
            p = packet(m)
            if gate is not None:
                p = p * gate
            h = h + p
        return self.head(self.lnf(h))


class Packet(nn.Module):
    def __init__(self, r=32):
        super().__init__()
        self.l1, self.l2 = nn.Linear(D, r), nn.Linear(r, D)

    def forward(self, m):
        return self.l2(F.gelu(self.l1(m)))


def ce_loss(logits, x, y):
    pred = logits[:, :-1].reshape(-1, V)
    tgt = torch.where(y[:, 1:] >= 0, y[:, 1:], x[:, 1:])
    mk = (y[:, 1:] >= 0).reshape(-1)
    return F.cross_entropy(pred[mk], tgt.reshape(-1)[mk])


def kl_loss(student_logits, teacher_logits, y):
    mk = (y[:, 1:] >= 0)
    s = F.log_softmax(student_logits[:, :-1][mk], -1)
    t = F.softmax(teacher_logits[:, :-1][mk], -1)
    return F.kl_div(s, t, reduction="batchmean")


def train(model, tasks, steps, g, packet=None, lr=2e-3, split="any", rec=None):
    params = list(packet.parameters()) if packet is not None else list(model.parameters())
    opt = torch.optim.AdamW(params, lr=lr)
    model.train()
    for _ in range(steps):
        x, y = batch(tasks, 64, g, split, rec)
        logits = model(x, packet=packet)
        loss = ce_loss(logits, x, y)
        opt.zero_grad(); loss.backward(); opt.step()
    return model


@torch.no_grad()
def acc_on(model, xy, packet=None, gate_fn=None):
    """xy: dict task -> (x, y). Same metric as committed acc(): argmax at positions 7..12 vs y[8:14]."""
    model.eval()
    out = {}
    for t, (x, y) in xy.items():
        gate = gate_fn(x) if gate_fn is not None else None
        logits = model(x, packet=packet, gate=gate)
        pred = logits[:, 7:13].argmax(-1)
        out[t] = round(float((pred == y[:, 8:14]).float().mean()), 4)
    return out


@torch.no_grad()
def acc(model, tasks, g, packet=None, n=512):
    model.eval()
    out = {}
    for t in tasks:
        x, y = batch([t], n, g)
        logits = model(x, packet=packet)
        pred = logits[:, 7:13].argmax(-1)
        out[t] = round(float((pred == y[:, 8:14]).float().mean()), 4)
    return out


def frob_dist(a, b):
    sa, sb = dict(a.named_parameters()), dict(b.named_parameters())
    if sa.keys() != sb.keys():
        die("param name mismatch")
    tot = 0.0
    for k in sa:
        tot += float((sa[k].detach() - sb[k].detach()).pow(2).sum())
    return math.sqrt(tot)


def clopper_pearson(k, n, alpha=0.05):
    from scipy.stats import beta
    lo = 0.0 if k == 0 else beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - alpha / 2, k + 1, n - k)
    return float(lo), float(hi)
