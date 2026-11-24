#!/usr/bin/env python3
"""Heddle prototype: reference implementation of the steering instrument's mathematics.

A prototype for the design note `notes/heddle-steering-instrument.md`. Nothing here is part
of the Weft runtime. The browser instrument (`heddle.js`, `ui.js`, `index.html`) mirrors this
file, and `vectors.json`, written by `make_vectors.py`, pins the two together.

The host is the three-layer network of Theorem 1 in
`experiments/gate-metric-calibration-2026-11-15/THEORY.md`,

    f(x, w) = W3 g(W2 g(W1 x + b1) + b2) + b3,        g = tanh  (slope at most 1),

read on the unit square: the input is a fixed feature vector of a point (u, v), and the three
outputs are shown as a colour. The whole behaviour of the host is therefore one picture, and
a set of inputs is a set of pixels.

Vocabulary (the note gives the reasons; each word names one object below):

    shaft      a unit eigenvector of G = J'J/(n m) on the fit probes, with its eigenvalue
    treadle    a named output pattern c, tied to the shafts by its coefficients on them
    tie-up     the matrix of those coefficients
    pin        an input whose outputs a move must leave alone to first order (a heddle eye)
    shed       the moves that pass the pins: the null space of the pins' Jacobian
    pick       one committed move
    fell       the last committed weights
    selvedge   the gate ||w - w0|| <= R of weft's invariants

Marks follow the calibration theory: a function's docstring says whether it computes a
proved quantity [P], a known one [K] or a reading [I].
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

SCHEMA = "heddle/1"
F, H, M = 8, 16, 3  # features, hidden units, outputs
TENSOR_NAMES = ["W1", "b1", "W2", "b2", "W3", "b3"]
SHAPES: Dict[str, Tuple[int, ...]] = {
    "W1": (H, F), "b1": (H,), "W2": (H, H), "b2": (H,), "W3": (M, H), "b3": (M,),
}
P = sum(int(np.prod(s)) for s in SHAPES.values())  # 467 weights
INIT_SCALE = {"W1": 1.1, "b1": 0.6, "W2": 0.9, "b2": 0.3, "W3": 0.9, "b3": 0.2}
GAMMA = 1.0  # largest slope of tanh

FIT_GRID = 10       # fit probes: a 10 x 10 grid, 100 inputs, 300 output rows (fewer than P)
PIN_LATTICE = 64    # pins are cells of a 64 x 64 lattice, stored as integers
DISPUTE_GRID = 96   # the dispute search first reads a 96 x 96 lattice
DISPUTE_REFINE = 4  # then climbs from this many best cells
DISPUTE_STEPS = 24  # for this many halvings-or-moves each

CBC_DOMAIN = b"WEFT-CBC-V1:"      # the weight-root domain of committed-behaviour-change v1
DOMAIN = b"WEFT-HEDDLE-V1:"       # everything else hashed here

# ---------------------------------------------------------------------------------------
# Deterministic numbers: the same bits in Python and JavaScript
# ---------------------------------------------------------------------------------------


def _imul(a: int, b: int) -> int:
    return (a * b) & 0xFFFFFFFF


def mulberry32(seed: int) -> Callable[[], float]:
    """The mulberry32 generator. Integer arithmetic only, so every draw is bit-identical
    in JavaScript and Python. Returns a function giving a float in [0, 1)."""
    state = [seed & 0xFFFFFFFF]

    def draw() -> float:
        state[0] = (state[0] + 0x6D2B79F5) & 0xFFFFFFFF
        a = state[0]
        t = _imul(a ^ (a >> 15), 1 | a)
        t = ((t + _imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF) ^ t
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

    return draw


def init_host(seed: int) -> Dict[str, np.ndarray]:
    """Weights drawn uniformly in [-a, a] per tensor, in the order of TENSOR_NAMES, row-major.
    (2u - 1) a uses only exact or correctly rounded operations, so the bytes match JavaScript."""
    draw = mulberry32(seed)
    w: Dict[str, np.ndarray] = {}
    for name in TENSOR_NAMES:
        n = int(np.prod(SHAPES[name]))
        a = INIT_SCALE[name]
        vals = [(2.0 * draw() - 1.0) * a for _ in range(n)]
        w[name] = np.array(vals, dtype=np.float64).reshape(SHAPES[name])
    return w


def flatten(w: Dict[str, np.ndarray]) -> np.ndarray:
    return np.concatenate([np.asarray(w[n], dtype=np.float64).ravel() for n in TENSOR_NAMES])


def unflatten(v: np.ndarray) -> Dict[str, np.ndarray]:
    v = np.asarray(v, dtype=np.float64)
    if v.shape != (P,):
        raise ValueError(f"expected a vector of {P} weights, got shape {v.shape}")
    out: Dict[str, np.ndarray] = {}
    at = 0
    for name in TENSOR_NAMES:
        n = int(np.prod(SHAPES[name]))
        out[name] = v[at:at + n].reshape(SHAPES[name]).copy()
        at += n
    return out


# ---------------------------------------------------------------------------------------
# Inputs: points of the unit square
# ---------------------------------------------------------------------------------------


def features(uv: np.ndarray) -> np.ndarray:
    """Feature vectors, shape (n, F), of points (u, v), shape (n, 2)."""
    uv = np.atleast_2d(np.asarray(uv, dtype=np.float64))
    u, v = uv[:, 0], uv[:, 1]
    tau = 2.0 * math.pi
    return np.stack([
        2.0 * u - 1.0, 2.0 * v - 1.0,
        np.sin(tau * u), np.cos(tau * u),
        np.sin(tau * v), np.cos(tau * v),
        np.sin(tau * (u + v)), np.sin(tau * (u - v)),
    ], axis=1)


def grid(n: int) -> np.ndarray:
    """Cell centres of an n x n lattice, row-major: index = row * n + column, u along columns."""
    c = (np.arange(n) + 0.5) / n
    uu, vv = np.meshgrid(c, c)
    return np.stack([uu.ravel(), vv.ravel()], axis=1)


def pin_points(pins: Sequence[int]) -> np.ndarray:
    """Pins are integer cells of the PIN_LATTICE lattice; this gives their centres."""
    pins = np.asarray(sorted(set(int(p) for p in pins)), dtype=np.int64)
    if pins.size and (pins.min() < 0 or pins.max() >= PIN_LATTICE * PIN_LATTICE):
        raise ValueError("pin outside the lattice")
    rows, cols = pins // PIN_LATTICE, pins % PIN_LATTICE
    return np.stack([(cols + 0.5) / PIN_LATTICE, (rows + 0.5) / PIN_LATTICE], axis=1).reshape(-1, 2)


# ---------------------------------------------------------------------------------------
# The host: forward pass and Jacobian
# ---------------------------------------------------------------------------------------


def forward(w: Dict[str, np.ndarray], uv: np.ndarray) -> np.ndarray:
    """Outputs, shape (n, M)."""
    x = features(uv)
    h1 = np.tanh(x @ w["W1"].T + w["b1"])
    h2 = np.tanh(h1 @ w["W2"].T + w["b2"])
    return h2 @ w["W3"].T + w["b3"]


def jacobian(w: Dict[str, np.ndarray], uv: np.ndarray) -> np.ndarray:
    """[K] Derivatives of every output on every input with respect to every weight.
    Shape (n * M, P). Row = input * M + output. Columns follow `flatten`."""
    x = features(uv)
    n = x.shape[0]
    h1 = np.tanh(x @ w["W1"].T + w["b1"])
    h2 = np.tanh(h1 @ w["W2"].T + w["b2"])
    g1 = 1.0 - h1 * h1
    g2 = 1.0 - h2 * h2
    J = np.zeros((n, M, P))
    o = {}
    at = 0
    for name in TENSOR_NAMES:
        size = int(np.prod(SHAPES[name]))
        o[name] = (at, at + size)
        at += size
    for c in range(M):
        d2 = w["W3"][c][None, :] * g2                 # (n, H): through the second tanh
        d1 = (d2 @ w["W2"]) * g1                      # (n, H): through the first tanh
        J[:, c, o["W1"][0]:o["W1"][1]] = (d1[:, :, None] * x[:, None, :]).reshape(n, -1)
        J[:, c, o["b1"][0]:o["b1"][1]] = d1
        J[:, c, o["W2"][0]:o["W2"][1]] = (d2[:, :, None] * h1[:, None, :]).reshape(n, -1)
        J[:, c, o["b2"][0]:o["b2"][1]] = d2
        w3 = np.zeros((n, M, H))
        w3[:, c, :] = h2
        J[:, c, o["W3"][0]:o["W3"][1]] = w3.reshape(n, -1)
        b3 = np.zeros((n, M))
        b3[:, c] = 1.0
        J[:, c, o["b3"][0]:o["b3"][1]] = b3
    return J.reshape(n * M, P)


def change(w0: Dict[str, np.ndarray], w1: Dict[str, np.ndarray], uv: np.ndarray) -> np.ndarray:
    """Per-input change: root mean square over the outputs of f1 - f0. The CBC `change(x)`."""
    d = forward(w1, uv) - forward(w0, uv)
    return np.sqrt(np.mean(d * d, axis=1))


def behaviour_change(w0: Dict[str, np.ndarray], w1: Dict[str, np.ndarray], uv: np.ndarray) -> float:
    """D_X of the calibration theory: root mean square of all output differences on X."""
    d = forward(w1, uv) - forward(w0, uv)
    return float(np.sqrt(np.mean(d * d)))


# ---------------------------------------------------------------------------------------
# Shafts: the eigen-directions of G on the fit probes
# ---------------------------------------------------------------------------------------


class Threading:
    """The linearisation of the host at one set of weights, on one set of inputs.

    J = U S V' with singular values s. G = J'J/(n m) has eigenvalues lam = s^2/(n m) on the
    columns of V. `U * sqrt(n m)` are the shaft pictures: the unit-RMS output pattern each
    shaft makes. Signs are fixed so that the largest entry of each column of V is positive.

    With a `shed` (raised heddles), the loom is threaded around the pins: the shafts are the
    eigen-directions of G restricted to the shed, so every shaft already leaves the pinned
    inputs alone to first order. `J` stays the full Jacobian; for a move inside the shed the
    two agree.
    """

    def __init__(self, w: Dict[str, np.ndarray], uv: np.ndarray, shed: Optional["Shed"] = None):
        self.w = {k: v.copy() for k, v in w.items()}
        self.uv = np.asarray(uv, dtype=np.float64)
        self.J = jacobian(w, uv)
        self.rows = self.J.shape[0]                      # n * M
        inside = self.J
        if shed is not None and shed.Q.shape[0]:
            inside = self.J - (self.J @ shed.Q.T) @ shed.Q
        U, s, Vt = np.linalg.svd(inside, full_matrices=False)
        flip = np.sign(Vt[np.arange(Vt.shape[0]), np.argmax(np.abs(Vt), axis=1)])
        flip[flip == 0] = 1.0
        self.U = U * flip[None, :]
        self.V = (Vt * flip[:, None]).T                  # (P, rank)
        self.s = s
        self.lam = s * s / self.rows

    def predicted_change(self, d: np.ndarray) -> float:
        """[K] First-order behaviour change sqrt(d'Gd) of a move d on these inputs."""
        y = self.J @ d
        return float(np.sqrt(np.mean(y * y)))

    def shaft_move(self, i: int, travel: float) -> np.ndarray:
        """The move along shaft i whose first-order behaviour change is |travel|."""
        return travel * self.V[:, i] / math.sqrt(self.lam[i])

    def silent_dimensions(self, rtol: float = 1e-10) -> int:
        """[P] Directions that change nothing here to first order: P minus the rank of J.
        With a shed, the directions the pins close are counted too."""
        return P - int(np.sum(self.s > rtol * self.s[0]))


# ---------------------------------------------------------------------------------------
# Treadles: named patterns and their tie-up to the shafts
# ---------------------------------------------------------------------------------------

TREADLE_NAMES = ["warm", "light", "tilt", "contrast", "check"]


def _unit_rms(c: np.ndarray) -> np.ndarray:
    r = float(np.sqrt(np.mean(c * c)))
    if r < 1e-300:
        return np.zeros_like(c)
    return c / r


def treadle_pattern(name: str, uv: np.ndarray, y: Optional[np.ndarray] = None) -> np.ndarray:
    """The output pattern a treadle asks for, shape (n * M,), unit root mean square.

    warm      every input: first output up, third output down
    light     every input: all outputs up
    tilt      all outputs up on the right, down on the left
    contrast  every input pushed away from the mean lightness of the current picture
    check     a two-period checkerboard on all outputs
    """
    uv = np.atleast_2d(np.asarray(uv, dtype=np.float64))
    n = uv.shape[0]
    u, v = uv[:, 0], uv[:, 1]
    ones = np.ones(M)
    if name == "warm":
        per = np.tile(np.array([1.0, 0.0, -1.0]), (n, 1))
    elif name == "light":
        per = np.tile(ones, (n, 1))
    elif name == "tilt":
        per = (2.0 * u - 1.0)[:, None] * ones[None, :]
    elif name == "contrast":
        if y is None:
            raise ValueError("the contrast treadle needs the current outputs")
        light = np.mean(np.asarray(y, dtype=np.float64).reshape(n, M), axis=1)
        per = (light - np.mean(light))[:, None] * ones[None, :]
    elif name == "check":
        tau = 2.0 * math.pi
        per = (np.sin(2.0 * tau * u) * np.sin(2.0 * tau * v))[:, None] * ones[None, :]
    else:
        raise ValueError(f"unknown treadle {name!r}")
    return _unit_rms(per.reshape(n * M))


class TieUp:
    """Treadles tied to the first K shafts of a threading.

    For a pattern c of unit root mean square, alpha_i = u_i'c / sqrt(n m) is its coefficient
    on shaft i. With travel t the move is  d = t * sum_i alpha_i v_i / sqrt(lam_i), over i < K.
    To first order the output change is then t times the projection of c on the K shafts.

    [P] `realizable` = sum_i alpha_i^2 is the share of the pattern the K shafts can carry.
    The first-order gain along c of a move with travel t is t * realizable, and the part
    of the request that is not delivered has root mean square t * sqrt(1 - realizable).
    """

    def __init__(self, threading: Threading, patterns: Dict[str, np.ndarray], shafts: int):
        self.threading = threading
        self.K = int(min(shafts, int(np.sum(threading.s > 1e-10 * threading.s[0]))))
        self.names = list(patterns)
        root = math.sqrt(threading.rows)
        self.patterns = {k: np.asarray(v, dtype=np.float64) for k, v in patterns.items()}
        self.alpha = {k: (threading.U[:, :self.K].T @ c) / root for k, c in self.patterns.items()}
        self.realizable = {k: float(a @ a) for k, a in self.alpha.items()}
        lam = threading.lam[:self.K]
        self.unit_move = {k: threading.V[:, :self.K] @ (a / np.sqrt(lam)) for k, a in self.alpha.items()}

    def move(self, treadling: Dict[str, float]) -> np.ndarray:
        """The weight move for a set of treadle travels (a treadling)."""
        d = np.zeros(P)
        for name, t in treadling.items():
            d += float(t) * self.unit_move[name]
        return d

    def matrix(self) -> np.ndarray:
        """The tie-up, shape (K, number of treadles)."""
        return np.stack([self.alpha[k] for k in self.names], axis=1)


def gain_along(y_change: np.ndarray, pattern: np.ndarray) -> float:
    """How much of `pattern` an output change contains: <dy, c> / <c, c>."""
    return float(np.dot(y_change, pattern) / np.dot(pattern, pattern))


# ---------------------------------------------------------------------------------------
# Pins and the shed: the null space of the pins' Jacobian
# ---------------------------------------------------------------------------------------


def row_space_basis(A: np.ndarray, rtol: float = 1e-10) -> np.ndarray:
    """Orthonormal rows spanning the rows of A, by modified Gram-Schmidt run twice.
    A row is dropped when what is left of it is below rtol times its own length.
    This is the algorithm the JavaScript mirror runs; numpy's QR is only the test's oracle."""
    basis: List[np.ndarray] = []
    for row in np.asarray(A, dtype=np.float64):
        v = row.copy()
        scale = float(np.linalg.norm(row))
        if scale == 0.0:
            continue
        for _ in range(2):
            for q in basis:
                v -= float(q @ v) * q
        norm = float(np.linalg.norm(v))
        if norm > rtol * scale:
            basis.append(v / norm)
    return np.array(basis).reshape(len(basis), A.shape[1])


class Shed:
    """[P] The moves that leave the pinned inputs alone to first order.

    Q holds orthonormal rows spanning the pins' Jacobian. `project` removes that span from a
    move, so J_pins @ project(d) = 0. `open_dimensions` is how much room is left: P - rank.
    """

    def __init__(self, w: Dict[str, np.ndarray], pins: Sequence[int]):
        self.pins = sorted(set(int(p) for p in pins))
        if self.pins:
            self.J = jacobian(w, pin_points(self.pins))
            self.Q = row_space_basis(self.J)
        else:
            self.J = np.zeros((0, P))
            self.Q = np.zeros((0, P))

    @property
    def open_dimensions(self) -> int:
        return P - self.Q.shape[0]

    def project(self, d: np.ndarray) -> np.ndarray:
        if self.Q.shape[0] == 0:
            return np.array(d, dtype=np.float64, copy=True)
        return d - self.Q.T @ (self.Q @ d)


# ---------------------------------------------------------------------------------------
# The selvedge: weft's gate, and the proved bound of the calibration theory
# ---------------------------------------------------------------------------------------


def verify_weight_update_safety(baseline: Iterable[float], candidate: Iterable[float],
                                r_invariant: float, budget: float, cost: float
                                ) -> Tuple[bool, float, float, str]:
    """A port of the unmasked list path of `verify_weight_update_safety_ex` in weft's
    `weft/runtime/invariants/invariants.py`, checked in `test_heddle.py` against weft's own
    conformance vectors. Returns (accepted, distance, remaining_budget, reason).

    The gate accepts when  budget >= cost > 0  and  ||candidate - baseline|| <= r_invariant.
    """
    b, c, r = float(budget), float(cost), float(r_invariant)
    if not (math.isfinite(b) and math.isfinite(c) and math.isfinite(r)):
        return False, math.inf, math.nan, "non_finite_parameters"
    if c <= 0.0:
        return False, math.inf, b, "non_positive_budget_or_cost"
    if b <= 0.0 or r < 0.0:
        return False, math.inf, b - c, "non_positive_budget_or_cost"
    if b < c:
        return False, math.inf, b - c, "insufficient_metabolic_budget"
    base = [float(v) for v in np.asarray(baseline, dtype=np.float64).ravel()]
    cand = [float(v) for v in np.asarray(candidate, dtype=np.float64).ravel()]
    if len(base) != len(cand) or len(base) == 0:
        return False, math.inf, b, "shape_mismatch"
    sq = 0.0
    for x, y in zip(base, cand):
        if not (math.isfinite(x) and math.isfinite(y)):
            return False, math.inf, b, "non_finite_weights"
        diff = y - x
        sq += diff * diff
    dist = math.sqrt(sq)
    if not math.isfinite(dist):
        return False, math.inf, b, "non_finite_weights"
    if dist > r:
        return False, dist, b, "baseline_distance_exceeded"
    return True, dist, b - c, "ok"


def certified_bound(w0: Dict[str, np.ndarray], uv: np.ndarray, radius: float) -> np.ndarray:
    """[P] Theorem 1 of the calibration theory, with gamma = 1 for tanh.

    For every move of length at most `radius` (all six tensors together) and every input x,
        ||f(x, w0 + d) - f(x, w0)||  <=  R c(x) + R^2 q(x) + R^3 k(x).
    Returns that bound per input, on the Euclidean length of the output change.
    """
    x = features(uv)
    h1 = np.tanh(x @ w0["W1"].T + w0["b1"])
    h2 = np.tanh(h1 @ w0["W2"].T + w0["b2"])
    s2 = float(np.linalg.norm(w0["W2"], 2))
    s3 = float(np.linalg.norm(w0["W3"], 2))
    a0 = np.sqrt(np.sum(x * x, axis=1) + 1.0)
    a1 = np.sqrt(np.sum(h1 * h1, axis=1) + 1.0)
    a2 = np.sqrt(np.sum(h2 * h2, axis=1) + 1.0)
    g = GAMMA
    c = np.sqrt((g * g * s3 * s2 * a0) ** 2 + (g * s3 * a1) ** 2 + a2 ** 2)
    q = (g * g * (s2 + s3) * a0 + g * a1) / 2.0
    k = g * g * a0 / (3.0 * math.sqrt(3.0))
    r = float(radius)
    return r * c + r * r * q + r ** 3 * k


# ---------------------------------------------------------------------------------------
# Commitments: weight roots, claims, and probes drawn after the candidate is fixed
# ---------------------------------------------------------------------------------------


def _canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def weight_root(w: Dict[str, np.ndarray]) -> str:
    """The weight root of committed-behaviour-change v1 (`cbc.py::weight_root`), re-stated so
    the JavaScript mirror can follow it line by line. `test_heddle.py` checks the two agree."""
    h = hashlib.sha256(CBC_DOMAIN + b"root:")
    for name in sorted(w):
        a = np.ascontiguousarray(np.asarray(w[name], dtype="<f8"))
        header = _canonical_json({"name": name, "shape": list(a.shape), "dtype": "<f8"})
        leaf = hashlib.sha256(CBC_DOMAIN + b"leaf:" + header + b":" + a.tobytes()).hexdigest()
        h.update(name.encode() + b":" + leaf.encode() + b";")
    return h.hexdigest()


def claim_id(w0_root: str, w1_root: str, tau: str, pins: Sequence[int]) -> str:
    """Identifier of the claim a pick makes. Strings and integers only, so that the same
    bytes are hashed in both languages. `tau` is a decimal string, as in CBC v1."""
    body = {"schema": "heddle-claim/1", "domain": "unit-square", "w0_root": w0_root,
            "w1_root": w1_root, "tau": str(tau), "pins": sorted(set(int(p) for p in pins))}
    return hashlib.sha256(DOMAIN + b"claim:" + _canonical_json(body)).hexdigest()


def fresh_probes(w1_root: str, claim: str, n: int, test_set: str = "admission") -> np.ndarray:
    """[K] Probe inputs derived only after the candidate is committed, as CBC v1 orders it:
    the seed hashes the candidate's root and the claim id, so a proposer cannot fit probes
    they have not seen. Proposition 2 of the calibration theory needs this order."""
    seed = hashlib.sha256(DOMAIN + b"probes:" + test_set.encode() + b":" + w1_root.encode()
                          + b":" + claim.encode()).digest()
    pts = np.zeros((n, 2))
    for i in range(n):
        h = hashlib.sha256(seed + i.to_bytes(4, "big")).digest()
        pts[i, 0] = int.from_bytes(h[0:4], "big") / 4294967296.0
        pts[i, 1] = int.from_bytes(h[4:8], "big") / 4294967296.0
    return pts


def dispute_search(w0: Dict[str, np.ndarray], w1: Dict[str, np.ndarray]
                   ) -> Tuple[float, Tuple[float, float], int]:
    """[I] A bounded search for the one input that changes most: the dispute of CBC v1.

    The input space is the unit square, so the search reads a whole lattice and then climbs
    from the best cells with a shrinking step. Returns (largest change found, its input, the
    number of inputs evaluated). It is a sampled reading: a larger budget can find more.
    """
    pts = grid(DISPUTE_GRID)
    ch = change(w0, w1, pts)
    rows = int(pts.shape[0])
    order = np.argsort(-ch, kind="stable")[:DISPUTE_REFINE]
    best_val, best_pt = float(ch[order[0]]), (float(pts[order[0], 0]), float(pts[order[0], 1]))
    for idx in order:
        p = pts[idx].copy()
        val = float(ch[idx])
        step = 0.5 / DISPUTE_GRID
        for _ in range(DISPUTE_STEPS):
            cand = np.clip(p[None, :] + step * np.array([[1, 0], [-1, 0], [0, 1], [0, -1]]), 0.0, 1.0)
            vals = change(w0, w1, cand)
            rows += 4
            j = int(np.argmax(vals))
            if float(vals[j]) > val:
                p, val = cand[j].copy(), float(vals[j])
            else:
                step *= 0.5
        if val > best_val:
            best_val, best_pt = val, (float(p[0]), float(p[1]))
    return best_val, best_pt, rows


# ---------------------------------------------------------------------------------------
# The hidden move: the same subspace read as the attack channel
# ---------------------------------------------------------------------------------------


def hidden_move(w: Dict[str, np.ndarray], probes: np.ndarray, elsewhere: np.ndarray,
                radius: float, iterations: int = 60) -> np.ndarray:
    """[K] A move of length `radius` that the probes cannot see to first order and that
    changes as much as it can elsewhere: the top direction of the elsewhere-Jacobian inside
    the null space of the probes' Jacobian, by power iteration from a fixed start.

    Section 6 of the calibration theory: the null space of a keep set is the safe channel
    when the weaver chose it and the hiding place when the proposer knows it.
    """
    Q = row_space_basis(jacobian(w, probes))
    Je = jacobian(w, elsewhere)
    draw = mulberry32(20261117)
    v = np.array([2.0 * draw() - 1.0 for _ in range(P)])

    def project(z: np.ndarray) -> np.ndarray:
        return z - Q.T @ (Q @ z)

    v = project(v)
    v /= np.linalg.norm(v)
    for _ in range(iterations):
        v = project(Je.T @ (Je @ v))
        v /= np.linalg.norm(v)
    idx = int(np.argmax(np.abs(v)))
    if v[idx] < 0:
        v = -v
    return float(radius) * v


# ---------------------------------------------------------------------------------------
# The draft: a steering session as a record anyone can replay
# ---------------------------------------------------------------------------------------


def move_to_b64(d: np.ndarray) -> str:
    return base64.b64encode(np.asarray(d, dtype="<f8").tobytes()).decode()


def move_from_b64(s: str) -> np.ndarray:
    d = np.frombuffer(base64.b64decode(s), dtype="<f8").astype(np.float64)
    if d.shape != (P,):
        raise ValueError("a move must hold one float64 per weight")
    return d


def event_id(event: dict) -> str:
    """Identifier of a draft event. It covers the exact commitments only (strings and
    integers); the readings in an event are recomputed by the verifier, not trusted."""
    body = {k: event[k] for k in ("seq", "kind", "prev", "parent_root", "root", "move_sha256",
                                  "pins", "gesture", "tau") if k in event}
    return hashlib.sha256(DOMAIN + b"event:" + _canonical_json(body)).hexdigest()


ZONES = ["auto", "shared", "knot"]
GESTURES = ["release", "hold", "knot"]


def zone_of(tension: float) -> str:
    """Autonomy zones, with the thresholds of the governor layer in the corpus's genesis
    dialogue: below 0.3, from 0.3, from 0.7."""
    if tension < 0.3:
        return "auto"
    if tension < 0.7:
        return "shared"
    return "knot"


def predicted_worst(J: np.ndarray, d: np.ndarray) -> float:
    """First-order change of the worst single fit probe: the largest per-input RMS of J d."""
    y = (J @ d).reshape(-1, M)
    return float(np.max(np.sqrt(np.mean(y * y, axis=1))))


def replay_draft(draft: dict, rtol: float = 1e-6) -> List[str]:
    """Replay a draft exported by the instrument and return a list of problems (empty when
    the draft checks out).

    Checked exactly: the baseline root, each move's hash, every weight root (the fell after
    each pick is the parent plus the recorded move, float64, so the bytes must match), the
    chain of event identifiers, the gate's verdict recomputed with the port above, and the
    witness of every snap (one input, both forward passes, as a CBC dispute is verified).
    Checked within a tolerance: the recorded distance and readings, and that the recorded
    gesture was deliberate enough for the pick's tension.

    Not checked, because it cannot be: that a person made the gesture. The draft records
    what the instrument saw.
    """
    problems: List[str] = []
    if draft.get("schema") != "heddle-draft/1":
        return [f"unknown schema {draft.get('schema')!r}"]
    gate = draft["gate"]
    r_inv, cost = float(gate["r_invariant"]), float(gate["cost"])
    budget = float(gate["budget"])
    w0 = init_host(int(draft["host"]["seed"]))
    if weight_root(w0) != draft["host"]["w0_root"]:
        problems.append("baseline root does not match the seed")
    base = flatten(w0)
    fit = grid(FIT_GRID)
    # The fell after each event, so an unpick can return to an earlier one.
    lineage: List[Tuple[str, np.ndarray, float]] = [(draft["host"]["w0_root"], base.copy(), budget)]
    prev = "genesis"
    for ev in draft["events"]:
        tag = f"event {ev.get('seq')}"
        if ev.get("prev") != prev:
            problems.append(f"{tag}: chain broken")
        if event_id(ev) != ev.get("id"):
            problems.append(f"{tag}: identifier does not match its contents")
        prev = ev.get("id")
        fell_root, fell, budget = lineage[-1]
        kind = ev.get("kind")
        if kind in ("pick", "snap"):
            if ev["parent_root"] != fell_root:
                problems.append(f"{tag}: parent is not the fell")
            raw = base64.b64decode(ev["move_b64"])
            if hashlib.sha256(raw).hexdigest() != ev["move_sha256"]:
                problems.append(f"{tag}: move bytes do not match their hash")
            d = move_from_b64(ev["move_b64"])
            cand = fell + d
            ok, dist, remaining, reason = verify_weight_update_safety(base, cand, r_inv, budget, cost)
            rec = ev["gate"]
            if bool(rec["accepted"]) != ok or rec["reason"] != reason:
                problems.append(f"{tag}: gate verdict differs ({reason}, recorded {rec['reason']})")
            if not ok:
                problems.append(f"{tag}: a move the gate refuses was recorded")
                continue
            if abs(float(rec["distance"]) - dist) > rtol * max(1.0, dist):
                problems.append(f"{tag}: recorded distance differs")
            wp, wc = unflatten(fell), unflatten(cand)
            root = weight_root(wc)
            if root != ev["root"]:
                problems.append(f"{tag}: weight root differs")
            tau = float(ev["tau"])
            tension = max(dist / r_inv, predicted_worst(jacobian(wp, fit), d) / tau)
            near = any(abs(tension - t) < 1e-6 for t in (0.3, 0.7))
            if not near and GESTURES.index(ev["gesture"]) < ZONES.index(zone_of(tension)):
                problems.append(f"{tag}: gesture {ev['gesture']!r} is too light for tension {tension:.3f}")
            cl = ev["claim"]
            cid = claim_id(ev["parent_root"], root, ev["tau"], ev["pins"])
            if cid != cl["id"]:
                problems.append(f"{tag}: claim identifier differs")
            probes = fresh_probes(root, cid, int(cl["probes"]))
            realized = behaviour_change(wp, wc, probes)
            if abs(realized - float(cl["realized"])) > rtol * max(1.0, realized):
                problems.append(f"{tag}: realized change differs ({realized:.9g})")
            if kind == "snap":
                # One input is the whole evidence.
                x = np.array([cl["witness"]], dtype=np.float64)
                inside = bool(np.all(x >= 0.0) and np.all(x <= 1.0))
                seen = float(change(wp, wc, x)[0])
                if not inside or not seen > tau:
                    problems.append(f"{tag}: the witness does not refute the claim ({seen:.9g})")
                if not cl["refuted"]:
                    problems.append(f"{tag}: a snap must carry a refuted claim")
                lineage.append((fell_root, fell, remaining))
            else:
                worst, _, _ = dispute_search(wp, wc)
                if abs(worst - float(cl["worst"])) > 1e-3 * max(1.0, worst):
                    problems.append(f"{tag}: dispute reading differs ({worst:.9g})")
                if worst > tau or cl["refuted"]:
                    problems.append(f"{tag}: a refuted claim was admitted as a pick")
                lineage.append((root, cand, remaining))
        elif kind == "unpick":
            if ev["parent_root"] != fell_root:
                problems.append(f"{tag}: parent is not the fell")
            roots = [r for r, _, _ in lineage]
            if ev["root"] not in roots:
                problems.append(f"{tag}: unpick to a root that was never the fell")
                continue
            at = len(roots) - 1 - roots[::-1].index(ev["root"])
            # Unpicking returns the weights; the budget already spent stays spent.
            lineage.append((ev["root"], lineage[at][1].copy(), budget))
        else:
            problems.append(f"{tag}: unknown kind {kind!r}")
    return problems
