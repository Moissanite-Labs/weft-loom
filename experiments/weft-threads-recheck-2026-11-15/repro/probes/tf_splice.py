"""Tiny-transformer splice probe (E14-mini), 2026-11-15.

Host: 2-layer decoder (d=128, MLP 256) trained on COPY + ADD3.
Donor: same shape, different init, trained on COPY + ADD3 + REVERSE.
Packet: 128->32->128 GELU MLP distilled at the host last-MLP boundary
(frozen host, task-2 sequences, true labels as donor proxy; donor acc printed).
Arms: host alone | packet as external residual adapter | packet spliced into
the 32 lowest-Fisher intermediate neurons of the last MLP (rows/cols overwritten).
Pre-stated bar: spliced REVERSE acc >= donor - 10 pts and native drop <= 2 pts
on at least 2 of 3 seeds. No shunt in v1 (A3 analogue); interference is measured.
Run: .venv-torch/bin/python tf_splice.py
"""
import json
from pathlib import Path
import math
import copy

import torch
import torch.nn as nn
import torch.nn.functional as F

V, L, D, H, FF, NDATA = 21, 14, 128, 4, 256, 16
TOK = {0: 1, 1: 2, 2: 3}
SEP = 4


def batch(tasks, n, g):
    xs, ys = [], []
    for _ in range(n):
        t = tasks[int(torch.randint(len(tasks), (1,), generator=g))]
        x = torch.randint(0, NDATA, (6,), generator=g) + 5
        if t == 0:
            y = x.clone()
        elif t == 1:
            y = 5 + ((x - 5 + 3) % NDATA)
        else:
            y = torch.flip(x, [0])
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

    def forward(self, x, packet=None, splice_slots=None):
        mask = torch.full((L, L), float("-inf")).triu(1)
        h = self.emb(x) + self.pos(torch.arange(L))
        h = self.b1(h, mask)
        # second block inline so the packet can sit at its MLP boundary
        b = self.b2
        hh = b.ln1(h)
        a, _ = b.attn(hh, hh, hh, attn_mask=mask, need_weights=False)
        h = h + a
        m = b.ln2(h)
        h = h + b.mlp(m)
        if packet is not None:
            h = h + packet(m)
        return self.head(self.lnf(h))


class Packet(nn.Module):
    def __init__(self, r=32):
        super().__init__()
        self.l1, self.l2 = nn.Linear(D, r), nn.Linear(r, D)

    def forward(self, m):
        return self.l2(F.gelu(self.l1(m)))


def train(model, tasks, steps, g, packet=None, lr=2e-3):
    params = list(packet.parameters()) if packet is not None else list(model.parameters())
    opt = torch.optim.AdamW(params, lr=lr)
    model.train()
    for _ in range(steps):
        x, y = batch(tasks, 64, g)
        logits = model(x, packet=packet)
        pred = logits[:, :-1].reshape(-1, V)
        tgt = torch.where(y[:, 1:] >= 0, y[:, 1:], x[:, 1:])
        mask = (y[:, 1:] >= 0).reshape(-1)
        loss = F.cross_entropy(pred[mask], tgt.reshape(-1)[mask])
        opt.zero_grad(); loss.backward(); opt.step()
    return model


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


def run_seed(seed):
    torch.manual_seed(100 + seed)
    g = torch.Generator().manual_seed(1000 + seed)
    host = train(TF(), [0, 1], 1200, g)
    torch.manual_seed(200 + seed)
    donor = train(TF(), [0, 1, 2], 1400, g)
    ge = torch.Generator().manual_seed(9000 + seed)
    base = acc(host, [0, 1, 2], ge)
    dref = acc(donor, [2], ge)[2]

    packet = Packet()
    for p in host.parameters():
        p.requires_grad_(False)
    train(host, [2], 800, g, packet=packet, lr=3e-3)
    ext = acc(host, [0, 1, 2], ge, packet=packet)

    # dormant slots: lowest activation-energy x down-col norm on native batches
    host.eval()
    with torch.no_grad():
        acts = []
        for _ in range(8):
            x, _ = batch([0, 1], 64, ge)
            mask = torch.full((L, L), float("-inf")).triu(1)
            h = host.emb(x) + host.pos(torch.arange(L))
            h = host.b1(h, mask)
            b = host.b2
            hh = b.ln1(h)
            a, _ = b.attn(hh, hh, hh, attn_mask=mask, need_weights=False)
            h = h + a
            acts.append(F.gelu(b.up(b.ln2(h))).pow(2).mean(dim=(0, 1)))
        fisher = torch.stack(acts).mean(0) * b.down.weight.pow(2).sum(0)
        slots = torch.argsort(fisher)[:32]

    spliced = copy.deepcopy(host)
    with torch.no_grad():
        b = spliced.b2
        b.up.weight[slots] = packet.l1.weight
        b.up.bias[slots] = packet.l1.bias
        b.down.weight[:, slots] = packet.l2.weight
        b.down.bias += packet.l2.bias
    spl = acc(spliced, [0, 1, 2], ge)
    npar = sum(p.numel() for p in host.parameters())
    wire = sum(p.numel() for p in packet.parameters()) * 2  # fp16 bytes
    res = {"seed": seed, "params": npar, "wire_bytes_fp16": wire, "donor_rev": dref,
           "host": base, "external": ext, "spliced": spl,
           "native_drop": round(min(base[0] - spl[0], base[1] - spl[1]) * -1, 4)}
    print(json.dumps(res), flush=True)
    return res


all_res = [run_seed(s) for s in range(3)]
ok = sum(1 for r in all_res if r["spliced"][2] >= r["donor_rev"] - 0.10
         and r["host"][0] - r["spliced"][0] <= 0.02 and r["host"][1] - r["spliced"][1] <= 0.02)
print(f"BAR: {ok}/3 seeds (need >=2)")
with open(str(Path(__file__).resolve().parents[1] / "out" / "tf-splice-results.json"), "w") as fh:
    json.dump({"seeds": all_res, "bar": f"{ok}/3"}, fh, indent=1)
