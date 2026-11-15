#!/usr/bin/env python3
"""Experiment A fix test: replay a splice from recorded discrete decisions.

Cross-host reading 43758319377: float64 CBC roots differ on every host, and
one runner's splice took a different discrete path. This script tests the
recorded-decisions fix:

  record mode: build pair 1000, splice the benign packet normally, and write
               decisions-1000.json with the ordered slot lists plus CBC roots
               over canonical float32 tensors (the v2 root defined here).
  replay mode: rebuild the pair, force the recorded slot sets through the
               protected-slots mechanism, permute the packet so its rows land
               on the recorded slots in the recorded order, splice again,
               and compare float32 roots. Exit 1 on any mismatch.

Usage: python3 replay_splice.py record|replay [pair]
"""
from __future__ import annotations

import copy
import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cbc  # noqa: E402
import expb  # noqa: E402

adm = expb.adm
lab = adm.lab
M1 = lab.M1
M2 = lab.M2


def _f32_root_of(tensors: dict) -> str:
    h = hashlib.sha256(b"WEFT-CBC-V2-F32:root:")
    for name in sorted(tensors):
        a = np.asarray(tensors[name], dtype=np.float32)
        header = json.dumps({"name": name, "shape": list(a.shape), "dtype": a.dtype.str},
                            sort_keys=True, separators=(",", ":")).encode()
        leaf = hashlib.sha256(b"WEFT-CBC-V2-F32:leaf:" + header + b":" + a.tobytes()).hexdigest()
        h.update(name.encode() + b":" + leaf.encode() + b";")
    return h.hexdigest()


def f32_root(org) -> str:
    """CBC root over canonical float32 tensors (v2 proposal, local to this test)."""
    return _f32_root_of({n: getattr(org, n) for n in cbc.TENSOR_NAMES})


def packet_f32_root(pkt) -> str:
    return _f32_root_of({n: getattr(pkt, n) for n in ("W1_p", "b1_p", "W2_p", "b2_p", "W3_p")})


def load_packet_bcpp(path: Path):
    """Rebuild a NeuralPlasmidPacket from its BCPP wire bytes, footer checked."""
    raw = path.read_bytes()
    if hashlib.sha256(raw[:-8]).digest()[:8] != raw[-8:]:
        raise SystemExit("packet footer mismatch")
    magic, _ver, skill_idx, r1, r2, _seed = struct.unpack("<4sBBBBI", raw[:12])
    assert magic == b"BCPP"
    off = 12
    out = {}
    for name, shape in (("W1_p", (r1, 24)), ("b1_p", (r1,)), ("W2_p", (r2, r1)),
                        ("b2_p", (r2,)), ("W3_p", (8, r2))):
        n = int(np.prod(shape))
        out[name] = np.frombuffer(raw, dtype=np.float16, count=n, offset=off).reshape(shape).astype(np.float64)
        off += 2 * n
    return lab.NeuralPlasmidPacket(raw_bytes=raw, skill_idx=int(skill_idx),
                                    sha256_hex=hashlib.sha256(raw).hexdigest(), **out)


def splice_with_slots(P, pkt, slot_m1, slot_m2):
    """Splice with the Fisher ranking forced to the recorded slot order.

    The protected-slots route cannot be used: it also empties the shunt target
    set. Forcing argsort touches only the two ranking calls inside the splice
    (first two size-96 calls during the call); everything else, shunt included,
    runs the lab code unchanged."""
    forced = [list(slot_m1), list(slot_m2)]
    real = np.argsort
    calls = {"n": 0}

    def fake(a, *args, **kwargs):
        out = real(a, *args, **kwargs)
        if calls["n"] < 2 and np.asarray(a).size == M1:
            head = forced[calls["n"]]
            calls["n"] += 1
            return np.array(head + [int(v) for v in out if int(v) not in head])
        return out

    np.argsort = fake
    try:
        return lab.splice_gfpt_neural_plasmid(
            P["host"], pkt, P["Xk"], P["Xs"], geodesic_retraction_steps=4, lateral_shunting=True)
    finally:
        np.argsort = real


def permuted_packet(pkt, rec_m1, run_m1, rec_m2, run_m2):
    """Relabel packet units so runner slot order reproduces recorded assignment."""
    def perm(rec, run):
        pos = {s: j for j, s in enumerate(run)}
        return [pos[s] for s in rec]  # new_row_for_old[i] = position of rec slot i in run order

    p1 = perm(rec_m1, run_m1)   # old m1 index -> new row
    p2 = perm(rec_m2, run_m2)
    inv1 = np.argsort(p1)
    inv2 = np.argsort(p2)
    q = copy.copy(pkt)
    q.W1_p = pkt.W1_p[inv1, :].copy()
    q.b1_p = pkt.b1_p[inv1].copy()
    q.W2_p = pkt.W2_p[np.ix_(inv2, inv1)].copy()
    q.b2_p = pkt.b2_p[inv2].copy()
    q.W3_p = pkt.W3_p[:, inv2].copy()
    return q


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "record"
    i = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    path = HERE / f"decisions-{i}.json"
    P = adm.build_pair(i, None)
    if mode == "record":
        (HERE / f"packet-{i}.bcpp").write_bytes(P["pkt"].raw_bytes)
        org, meta = adm.splice(P, P["pkt"])
        data = {"pair": i, "slot_m1": [int(v) for v in meta["slot_m1"]],
                "slot_m2": [int(v) for v in meta["slot_m2"]],
                "packet_f32_root": packet_f32_root(P["pkt"]),
                "packet_sha256": P["pkt"].sha256_hex,
                "host_f32_root": f32_root(P["host"]), "benign_f32_root": f32_root(org),
                "host_v1_root": cbc.weight_root(P["host"]), "benign_v1_root": cbc.weight_root(org)}
        path.write_text(json.dumps(data, indent=1))
        print(json.dumps(data, indent=1))
        return
    data = json.loads(path.read_text())
    rec_m1, rec_m2 = data["slot_m1"], data["slot_m2"]
    pkt = load_packet_bcpp(HERE / f"packet-{i}.bcpp")
    print(f"recorded packet sha {data.get('packet_sha256')} loaded {pkt.sha256_hex}")
    P = dict(P)
    P["pkt"] = pkt
    probe, meta = splice_with_slots(P, pkt, rec_m1, rec_m2)
    run_m1 = [int(v) for v in meta["slot_m1"]]
    run_m2 = [int(v) for v in meta["slot_m2"]]
    if set(run_m1) != set(rec_m1) or set(run_m2) != set(rec_m2):
        print(f"SLOT-SET-MISMATCH run={run_m1},{run_m2} rec={rec_m1},{rec_m2}")
        raise SystemExit(1)
    if run_m1 == rec_m1 and run_m2 == rec_m2:
        org = probe
    else:
        q = permuted_packet(P["pkt"], rec_m1, run_m1, rec_m2, run_m2)
        org, meta2 = splice_with_slots(P, q, rec_m1, rec_m2)
        assert [int(v) for v in meta2["slot_m1"]] == run_m1 and [int(v) for v in meta2["slot_m2"]] == run_m2
    got = {"host_f32_root": f32_root(P["host"]), "benign_f32_root": f32_root(org)}
    print(f"recorded packet {data.get('packet_f32_root')} host {data['host_f32_root']} benign {data['benign_f32_root']}")
    print(f"replayed packet {packet_f32_root(P['pkt'])} host {got['host_f32_root']} benign {got['benign_f32_root']}")
    np.save("replay_benign_flat.npy", org.flat_params())
    ok = got["host_f32_root"] == data["host_f32_root"] and got["benign_f32_root"] == data["benign_f32_root"]
    print("REPLAY-MATCH" if ok else "REPLAY-DIFFER")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
