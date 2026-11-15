"""Functional re-implementation of the host forward pass with head-level access (ablation, repurposing, extra head).
Parity with the nn.MultiheadAttention forward is checked and the check raises SystemExit on mismatch."""
import math

from tf_common import *  # noqa

DH = D // H  # 32


class Graft(nn.Module):
    """One attention head: q,k,v : D->DH (with bias), o : DH->D (no bias). 16,480 parameters."""

    def __init__(self):
        super().__init__()
        self.q, self.k, self.v = nn.Linear(D, DH), nn.Linear(D, DH), nn.Linear(D, DH)
        self.o = nn.Linear(DH, D, bias=False)

    def forward(self, hh, mask):
        q, k, v = self.q(hh), self.k(hh), self.v(hh)
        s = torch.einsum("bld,bmd->blm", q, k) / math.sqrt(DH) + mask
        p = torch.softmax(s, -1)
        return self.o(torch.einsum("blm,bmd->bld", p, v)), p

    @staticmethod
    def from_head(b, h):
        g = Graft()
        W, Bi = b.attn.in_proj_weight, b.attn.in_proj_bias
        sl = slice(h * DH, (h + 1) * DH)
        with torch.no_grad():
            g.q.weight.copy_(W[sl]); g.q.bias.copy_(Bi[sl])
            g.k.weight.copy_(W[D + h * DH:D + (h + 1) * DH]); g.k.bias.copy_(Bi[D + h * DH:D + (h + 1) * DH])
            g.v.weight.copy_(W[2 * D + h * DH:2 * D + (h + 1) * DH]); g.v.bias.copy_(Bi[2 * D + h * DH:2 * D + (h + 1) * DH])
            g.o.weight.copy_(b.attn.out_proj.weight[:, sl])
        return g

    def write_into(self, b, h):
        """Overwrite head h of block b with this graft (no width added)."""
        W, Bi = b.attn.in_proj_weight, b.attn.in_proj_bias
        sl = slice(h * DH, (h + 1) * DH)
        with torch.no_grad():
            W[sl] = self.q.weight; Bi[sl] = self.q.bias
            W[D + h * DH:D + (h + 1) * DH] = self.k.weight; Bi[D + h * DH:D + (h + 1) * DH] = self.k.bias
            W[2 * D + h * DH:2 * D + (h + 1) * DH] = self.v.weight; Bi[2 * D + h * DH:2 * D + (h + 1) * DH] = self.v.bias
            b.attn.out_proj.weight[:, sl] = self.o.weight


def mha_heads(b, hh, mask, ablate=()):
    W, Bi = b.attn.in_proj_weight, b.attn.in_proj_bias
    B_, L_, _ = hh.shape
    q = F.linear(hh, W[:D], Bi[:D]).view(B_, L_, H, DH)
    k = F.linear(hh, W[D:2 * D], Bi[D:2 * D]).view(B_, L_, H, DH)
    v = F.linear(hh, W[2 * D:], Bi[2 * D:]).view(B_, L_, H, DH)
    s = torch.einsum("blhd,bmhd->bhlm", q, k) / math.sqrt(DH) + mask
    p = torch.softmax(s, -1)
    ctx = torch.einsum("bhlm,bmhd->blhd", p, v)
    if ablate:
        keep = torch.ones(H)
        for h in ablate:
            keep[h] = 0.0
        ctx = ctx * keep.view(1, 1, H, 1)
    return b.attn.out_proj(ctx.reshape(B_, L_, D))


def fwd(model, x, graft=None, graft_block=2, ablate=None, packet=None, ret_p=False, packet_block=2):
    """ablate: dict {block_index: [heads]}; graft added to block graft_block's attention output; packet at last MLP."""
    ablate = ablate or {}
    mask = torch.full((L, L), float("-inf")).triu(1)
    h = model.emb(x) + model.pos(torch.arange(L))
    pg = None
    for bi, b in ((1, model.b1), (2, model.b2)):
        hh = b.ln1(h)
        a = mha_heads(b, hh, mask, tuple(ablate.get(bi, ())))
        if graft is not None and graft_block == bi:
            ga, pg = graft(hh, mask)
            a = a + ga
        h = h + a
        m = b.ln2(h)
        h = h + b.mlp(m)
        if packet is not None and bi == packet_block:
            h = h + packet(m)
    out = model.head(model.lnf(h))
    return (out, pg) if ret_p else out


def parity_check(model, x):
    model.eval()
    with torch.no_grad():
        d = float((model(x) - fwd(model, x)).abs().max())
    if d > 1e-4:
        die("functional forward differs from nn.MultiheadAttention forward by %g" % d)
    return d


@torch.no_grad()
def acc_f(model, xy, **kw):
    model.eval()
    out = {}
    for t, (x, y) in xy.items():
        logits = fwd(model, x, **kw)
        pred = logits[:, 7:13].argmax(-1)
        out[t] = round(float((pred == y[:, 8:14]).float().mean()), 4)
    return out
