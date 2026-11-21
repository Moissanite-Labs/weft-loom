"""Attack S2: is training with real library optimisers exactly sign-equivariant per hidden unit?

Own code. Uses the real transformers Qwen3 model and torch.optim optimisers.
Model B = model A with a random sign pattern applied to the hidden units of every MLP
(rows of up_proj, columns of down_proj, plus up bias when present). Both are trained on the
same batches; afterwards B is mapped back and compared with A bit for bit.

Also: controls that must FAIL (a LayerNorm on the hidden vector, a plain GELU block, flipping
gate rows), and the "same default seed" practice (two from-scratch inits with seed 42).

Run with the venv python -I.
"""
import json
import sys

import torch
import torch.nn as nn
from transformers import Qwen3Config, Qwen3ForCausalLM

torch.set_num_threads(4)
OUT = {}


def tiny_cfg(inter=48, bias=False):
    return Qwen3Config(vocab_size=64, hidden_size=32, intermediate_size=inter, num_hidden_layers=2,
                       num_attention_heads=4, num_key_value_heads=2, head_dim=8, max_position_embeddings=64,
                       tie_word_embeddings=False, attention_bias=bias)


def make(seed, inter=48, dtype=torch.float32):
    torch.manual_seed(seed)
    m = Qwen3ForCausalLM(tiny_cfg(inter)).to(dtype)
    return m


def flip_units(model, signs):
    with torch.no_grad():
        for layer, f in zip(model.model.layers, signs):
            mlp = layer.mlp
            mlp.up_proj.weight.mul_(f[:, None].to(mlp.up_proj.weight.dtype))
            if mlp.up_proj.bias is not None:
                mlp.up_proj.bias.mul_(f.to(mlp.up_proj.bias.dtype))
            mlp.down_proj.weight.mul_(f[None, :].to(mlp.down_proj.weight.dtype))


def maxdiff(a, b):
    return max((pa.float() - pb.float()).abs().max().item() for pa, pb in zip(a.parameters(), b.parameters()))


def batches(n, seed, T=16, B=8):
    g = torch.Generator().manual_seed(seed)
    return [torch.randint(0, 64, (B, T), generator=g) for _ in range(n)]


def train(model, opt_name, data, autocast=False, clip=None, clip_value=None, tie=False):
    params = list(model.parameters())
    if opt_name == "adamw":
        opt = torch.optim.AdamW(params, lr=3e-3, weight_decay=0.1, eps=1e-8)
    elif opt_name == "adamw_bigeps":
        opt = torch.optim.AdamW(params, lr=3e-3, weight_decay=0.1, eps=1e-3)
    elif opt_name == "adamw_amsgrad":
        opt = torch.optim.AdamW(params, lr=3e-3, weight_decay=0.1, amsgrad=True)
    elif opt_name == "adamw_fused":
        opt = torch.optim.AdamW(params, lr=3e-3, weight_decay=0.1, fused=True)
    elif opt_name == "adamw_foreach_off":
        opt = torch.optim.AdamW(params, lr=3e-3, weight_decay=0.1, foreach=False)
    elif opt_name == "adam_coupled_wd":
        opt = torch.optim.Adam(params, lr=3e-3, weight_decay=0.1)
    elif opt_name == "sgd_nesterov":
        opt = torch.optim.SGD(params, lr=0.05, momentum=0.9, nesterov=True, weight_decay=1e-4)
    elif opt_name == "radam_decoupled":
        opt = torch.optim.RAdam(params, lr=3e-3, weight_decay=0.1, decoupled_weight_decay=True)
    elif opt_name == "adagrad":
        opt = torch.optim.Adagrad(params, lr=1e-2)
    elif opt_name == "muon":
        mats = [p for p in params if p.ndim == 2]
        rest = [p for p in params if p.ndim != 2]
        opt = [torch.optim.Muon(mats, lr=2e-2, weight_decay=0.1), torch.optim.AdamW(rest, lr=3e-3)]
    else:
        raise ValueError(opt_name)
    opts = opt if isinstance(opt, list) else [opt]
    for x in data:
        for o in opts:
            o.zero_grad(set_to_none=True)
        if autocast:
            with torch.autocast("cpu", dtype=torch.bfloat16):
                loss = model(input_ids=x, labels=x).loss
        else:
            loss = model(input_ids=x, labels=x).loss
        if tie:  # must-fail control: a loss term that is odd in each up_proj output (sign-tying)
            emb = model.model.embed_tokens(x)
            loss = loss + 0.1 * sum(l.mlp.up_proj(emb).mean() for l in model.model.layers)
        loss.backward()
        if clip is not None:
            torch.nn.utils.clip_grad_norm_(params, clip)
        if clip_value is not None:
            torch.nn.utils.clip_grad_value_(params, clip_value)
        for o in opts:
            o.step()
    return model


def equivariance_case(name, opt_name, dtype=torch.float32, autocast=False, clip=None, clip_value=None, steps=60, tie=False):
    A = make(1234, dtype=dtype)
    B = make(1234, dtype=dtype)
    g = torch.Generator().manual_seed(77)
    signs = [torch.randint(0, 2, (48,), generator=g) * 2 - 1 for _ in range(2)]
    flip_units(B, signs)
    x = batches(1, 5)[0]
    with torch.no_grad():
        d0 = (A(input_ids=x).logits.float() - B(input_ids=x).logits.float()).abs().max().item()
    data = batches(steps, 11)
    A0 = make(1234, dtype=dtype)
    try:
        train(A, opt_name, data, autocast, clip, clip_value, tie)
        train(B, opt_name, data, autocast, clip, clip_value, tie)
    except Exception as exc:  # optimiser not available etc.
        OUT[name] = dict(error=repr(exc)[:200])
        return
    flip_units(B, signs)  # map back (f*f = 1)
    with torch.no_grad():
        d1 = (A(input_ids=x).logits.float() - B(input_ids=x).logits.float()).abs().max().item()
    OUT[name] = dict(init_logit_diff=d0, final_param_maxdiff=maxdiff(A, B), final_logit_diff=d1, steps=steps,
                     param_movement_maxabs=maxdiff(A, A0))


def trace_flip_check():
    """trace = input of down_proj; flipping unit i must negate trace i exactly and nothing else."""
    A = make(3)
    B = make(3)
    f = torch.ones(48, dtype=torch.long)
    f[5] = -1
    flip_units(B, [f, torch.ones(48, dtype=torch.long)])
    caught = {}

    def hook(name):
        def h(mod, inp):
            caught[name] = inp[0].detach().clone()
        return h
    hA = A.model.layers[0].mlp.down_proj.register_forward_pre_hook(hook("A"))
    hB = B.model.layers[0].mlp.down_proj.register_forward_pre_hook(hook("B"))
    x = batches(1, 9)[0]
    with torch.no_grad():
        A(input_ids=x)
        B(input_ids=x)
    hA.remove(); hB.remove()
    ta, tb = caught["A"], caught["B"]
    OUT["trace_flip"] = dict(unit5_sum_equals_zero=float((ta[..., 5] + tb[..., 5]).abs().max()),
                             others_equal=float((ta[..., :5] - tb[..., :5]).abs().max() + (ta[..., 6:] - tb[..., 6:]).abs().max()))


class Block(nn.Module):
    """gated or plain MLP with optional LayerNorm/RMSNorm on the hidden vector and biases."""

    def __init__(self, d, h, kind, hidden_norm=None, bias=True):
        super().__init__()
        self.kind, self.hidden_norm = kind, hidden_norm
        self.U = nn.Linear(d, h, bias=bias)
        self.G = nn.Linear(d, h, bias=bias) if kind == "gated" else None
        self.D = nn.Linear(h, d, bias=bias)
        if hidden_norm == "layernorm":
            self.norm = nn.LayerNorm(h)
        elif hidden_norm == "rmsnorm":
            self.norm = nn.RMSNorm(h)
        else:
            self.norm = None

    def forward(self, x):
        if self.kind == "gated":
            hdn = nn.functional.silu(self.G(x)) * self.U(x)
        else:
            hdn = nn.functional.gelu(self.U(x))
        if self.norm is not None:
            hdn = self.norm(hdn)
        return self.D(hdn)


def block_controls():
    res = {}
    for name, kind, hn in [("gated_bias", "gated", None), ("gated_hidden_rmsnorm", "gated", "rmsnorm"),
                           ("gated_hidden_layernorm_MUSTFAIL", "gated", "layernorm"),
                           ("plain_gelu_MUSTFAIL", "plain", None)]:
        torch.manual_seed(0)
        blk = Block(16, 24, kind, hn)
        with torch.no_grad():
            if blk.norm is not None and isinstance(blk.norm, nn.LayerNorm):
                blk.norm.bias.normal_()  # trained LN has a bias; zero bias is a measure-zero case
            if blk.U.bias is not None:
                blk.U.bias.normal_()
        x = torch.randn(50, 16)
        y0 = blk(x)
        f = torch.ones(24)
        f[3] = -1
        with torch.no_grad():
            blk.U.weight.mul_(f[:, None])
            blk.U.bias.mul_(f)
            blk.D.weight.mul_(f[None, :])
        y1 = blk(x)
        res[name] = float((y0 - y1).detach().abs().max())
    # flip G row with D column in gated block: must fail
    torch.manual_seed(0)
    blk = Block(16, 24, "gated", None)
    x = torch.randn(50, 16)
    y0 = blk(x)
    with torch.no_grad():
        blk.G.weight[3].mul_(-1); blk.G.bias[3].mul_(-1); blk.D.weight[:, 3].mul_(-1)
    res["gated_flip_gate_MUSTFAIL"] = float((y0 - blk(x)).detach().abs().max())
    OUT["block_controls_output_change"] = res


def seed_sharing():
    """Two 'independent' from-scratch runs using the same default seed (42) share every init weight.
    Also: same seed, different intermediate_size -> how much of layer-0 gate/up is shared?"""
    a = make(42)
    b = make(42)
    same_all = maxdiff(a, b) == 0.0
    small = make(42, inter=48)
    big = make(42, inter=96)
    gs, gb = small.model.layers[0].mlp.gate_proj.weight, big.model.layers[0].mlp.gate_proj.weight
    us, ub = small.model.layers[0].mlp.up_proj.weight, big.model.layers[0].mlp.up_proj.weight
    rows_gate = int((gs == gb[:48]).all(dim=1).sum())
    rows_up = int((us == ub[:48]).all(dim=1).sum())
    # any up row of small equal (up to sign) to any up row of big anywhere?
    any_up = int(((us[:, None, :] == ub[None, :, :]).all(-1)).any(-1).sum())
    OUT["seed_sharing"] = dict(same_seed_same_config_identical=same_all,
                               diff_width_layer0_gate_rows_identical=f"{rows_gate}/48",
                               diff_width_layer0_up_rows_identical=f"{rows_up}/48",
                               diff_width_layer0_up_rows_found_anywhere=f"{any_up}/48")


def main():
    trace_flip_check()
    for name, opt in [("adamw_fp32", "adamw"), ("adamw_eps1e-3", "adamw_bigeps"), ("adamw_amsgrad", "adamw_amsgrad"),
                      ("adamw_fused_cpu", "adamw_fused"), ("adamw_foreach_off", "adamw_foreach_off"),
                      ("adam_coupled_l2", "adam_coupled_wd"), ("sgd_nesterov", "sgd_nesterov"),
                      ("radam_decoupled", "radam_decoupled"), ("adagrad", "adagrad"), ("muon", "muon")]:
        equivariance_case(name, opt)
    equivariance_case("adamw_clipnorm1", "adamw", clip=1.0)
    equivariance_case("adamw_clipvalue", "adamw", clip_value=0.01)
    equivariance_case("adamw_bf16_autocast_clip", "adamw", autocast=True, clip=1.0)
    equivariance_case("adamw_bf16_params", "adamw", dtype=torch.bfloat16, clip=1.0)
    equivariance_case("adamw_signtying_loss_MUSTFAIL", "adamw", tie=True)
    block_controls()
    seed_sharing()
    json.dump(OUT, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
