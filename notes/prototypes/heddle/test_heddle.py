#!/usr/bin/env python3
"""Tests for the heddle prototype's reference implementation.

Run from the repository root:
    python3 -m unittest discover -s notes/prototypes/heddle -p 'test_*.py'

Each test states what it checks. A property that holds by construction is marked as such:
it tests the code, not an idea.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import heddle as hd  # noqa: E402

REPO = HERE.parents[2]
CBC = REPO / "experiments" / "committed-behaviour-change-2026-11-15" / "cbc.py"
SPECIAL = {"Inf": math.inf, "-Inf": -math.inf, "NaN": math.nan}


def decode(x):
    return SPECIAL[x] if isinstance(x, str) and x in SPECIAL else x


class Host(unittest.TestCase):
    def setUp(self):
        self.w = hd.init_host(7)
        self.flat = hd.flatten(self.w)
        self.fit = hd.grid(hd.FIT_GRID)

    def test_weight_count_and_round_trip(self):
        self.assertEqual(hd.P, 467)
        again = hd.flatten(hd.unflatten(self.flat))
        self.assertTrue(np.array_equal(again, self.flat))

    def test_generator_is_the_published_mulberry32(self):
        # Reference values for seed 12345 are pinned in vectors.json and re-derived in JavaScript.
        vec = json.loads((HERE / "vectors.json").read_text())
        draw = hd.mulberry32(12345)
        self.assertEqual([draw() for _ in range(8)], vec["exact"]["mulberry32_12345"])

    def test_jacobian_matches_finite_differences(self):
        rng = np.random.default_rng(0)
        pts = rng.random((6, 2))
        J = hd.jacobian(self.w, pts)
        for _ in range(4):
            d = rng.standard_normal(hd.P)
            d /= np.linalg.norm(d)
            eps = 1e-6
            up = hd.forward(hd.unflatten(self.flat + eps * d), pts)
            dn = hd.forward(hd.unflatten(self.flat - eps * d), pts)
            self.assertLess(np.max(np.abs((up - dn).ravel() / (2 * eps) - J @ d)), 1e-7)

    def test_weight_root_is_the_cbc_weight_root(self):
        # The instrument roots its fells with the CBC v1 scheme. Import the record's own code
        # and compare, so a pick's roots are valid w0_root / w1_root fields of a CBC record.
        if not CBC.is_file():
            self.skipTest("the committed-behaviour-change record is not in this checkout")
        spec = importlib.util.spec_from_file_location("cbc_record", CBC)
        cbc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cbc)
        self.assertEqual(hd.weight_root(self.w), cbc.weight_root(self.w))
        moved = hd.unflatten(self.flat + 1e-3)
        self.assertEqual(hd.weight_root(moved), cbc.weight_root(moved))
        self.assertNotEqual(hd.weight_root(moved), hd.weight_root(self.w))


class Shafts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = hd.init_host(7)
        cls.fit = hd.grid(hd.FIT_GRID)
        cls.th = hd.Threading(cls.w, cls.fit)
        y = hd.forward(cls.w, cls.fit)
        cls.patterns = {n: hd.treadle_pattern(n, cls.fit, y.ravel()) for n in hd.TREADLE_NAMES}

    def test_shafts_are_orthonormal_and_ordered(self):
        V = self.th.V[:, :32]
        self.assertLess(np.max(np.abs(V.T @ V - np.eye(32))), 1e-10)
        self.assertTrue(np.all(np.diff(self.th.lam) <= 1e-12))

    def test_silent_dimensions_are_p_minus_the_output_rows(self):
        # THEORY.md section 2: J has at most n m independent rows. Here n m = 300 < P = 467.
        self.assertEqual(self.th.rows, 300)
        self.assertEqual(self.th.silent_dimensions(), hd.P - 300)

    def test_travel_is_measured_in_behaviour(self):
        # By construction: a move of travel t along shaft i has first-order change |t|.
        for i in (0, 5, 15):
            for t in (0.2, -0.7):
                self.assertAlmostEqual(self.th.predicted_change(self.th.shaft_move(i, t)), abs(t), places=10)

    def test_worst_and_typical_directions_differ_by_kappa(self):
        # THEORY.md section 2: the worst direction changes behaviour sqrt(lam_max) per unit of
        # weight length, a random one sqrt(trace(G)/P) on average.
        rng = np.random.default_rng(1)
        d = rng.standard_normal((400, hd.P))
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        typical = math.sqrt(np.mean([self.th.predicted_change(x) ** 2 for x in d]))
        self.assertAlmostEqual(typical, math.sqrt(np.sum(self.th.lam) / hd.P), delta=0.03 * typical)
        self.assertGreater(math.sqrt(self.th.lam[0]) / typical, 4.0)

    def test_tie_up_delivers_the_realizable_share(self):
        for K in (4, 16, 64):
            tie = hd.TieUp(self.th, self.patterns, K)
            for name in hd.TREADLE_NAMES:
                rho = tie.realizable[name]
                self.assertGreaterEqual(rho, 0.0)
                self.assertLessEqual(rho, 1.0 + 1e-12)
                t = 0.37
                dy = self.th.J @ tie.move({name: t})
                c = self.patterns[name]
                # gain along the pattern is t * rho; what is missing has RMS t * sqrt(1 - rho)
                self.assertAlmostEqual(hd.gain_along(dy, c), t * rho, places=10)
                missing = t * c - dy
                self.assertAlmostEqual(math.sqrt(np.mean(missing ** 2)), t * math.sqrt(max(0.0, 1 - rho)), places=9)

    def test_more_shafts_never_carry_less(self):
        last = {n: 0.0 for n in hd.TREADLE_NAMES}
        for K in (2, 4, 8, 16, 32, 64, 128, 300):
            tie = hd.TieUp(self.th, self.patterns, K)
            for n in hd.TREADLE_NAMES:
                self.assertGreaterEqual(tie.realizable[n], last[n] - 1e-12)
                last[n] = tie.realizable[n]

    def test_a_treadling_is_a_weaving_draft(self):
        # The identity the note is built on. To first order,
        #     output change  =  threading  x  tie-up  x  treadling
        # with threading = the shaft pictures U sqrt(n m), tie-up = alpha, treadling = travels.
        K = 16
        tie = hd.TieUp(self.th, self.patterns, K)
        treadling = {"warm": 0.3, "tilt": -0.2, "check": 0.5, "light": 0.0, "contrast": 0.1}
        travels = np.array([treadling[n] for n in tie.names])
        threading = self.th.U[:, :K] * math.sqrt(self.th.rows)
        drawdown = threading @ tie.matrix() @ travels
        self.assertLess(np.max(np.abs(self.th.J @ tie.move(treadling) - drawdown)), 1e-10)


class ShedAndPins(unittest.TestCase):
    def setUp(self):
        self.w = hd.init_host(7)
        self.flat = hd.flatten(self.w)
        self.pins = [100, 2000, 3000, 3001]
        self.shed = hd.Shed(self.w, self.pins)
        self.rng = np.random.default_rng(2)

    def test_projection_leaves_the_pins_alone_to_first_order(self):
        d = self.rng.standard_normal(hd.P)
        p = self.shed.project(d)
        self.assertLess(np.max(np.abs(self.shed.J @ p)), 1e-10)
        self.assertLess(np.max(np.abs(self.shed.project(p) - p)), 1e-10)   # idempotent
        self.assertEqual(self.shed.open_dimensions, hd.P - np.linalg.matrix_rank(self.shed.J))

    def test_gram_schmidt_basis_spans_the_same_rows_as_numpy(self):
        Q = hd.row_space_basis(self.shed.J)
        self.assertLess(np.max(np.abs(Q @ Q.T - np.eye(Q.shape[0]))), 1e-10)
        q, _ = np.linalg.qr(self.shed.J.T)
        self.assertLess(np.max(np.abs(Q.T @ Q - q @ q.T)), 1e-9)   # same projector

    def test_what_reaches_the_pins_is_second_order(self):
        # THEORY.md section 6, point 1: a move in the null space of the keep set changes the
        # kept outputs by about c2 r^2. Halving the move should quarter the leak.
        d = self.shed.project(self.rng.standard_normal(hd.P))
        d /= np.linalg.norm(d)
        pts = hd.pin_points(self.pins)
        leak = [float(np.max(hd.change(self.w, hd.unflatten(self.flat + r * d), pts))) for r in (0.02, 0.01)]
        self.assertGreater(leak[0] / leak[1], 3.5)
        self.assertLess(leak[0] / leak[1], 4.5)
        raw = self.rng.standard_normal(hd.P)
        raw /= np.linalg.norm(raw)
        unprojected = float(np.max(hd.change(self.w, hd.unflatten(self.flat + 0.01 * raw), pts)))
        self.assertGreater(unprojected, 20 * leak[1])

    def test_threading_around_the_pins(self):
        # With heddles raised the shafts are those of G restricted to the shed. Every shaft
        # then leaves the pins alone to first order, and pins never add reach.
        fit = hd.grid(hd.FIT_GRID)
        y = hd.forward(self.w, fit)
        patterns = {n: hd.treadle_pattern(n, fit, y.ravel()) for n in hd.TREADLE_NAMES}
        free = hd.Threading(self.w, fit)
        inside = hd.Threading(self.w, fit, self.shed)
        self.assertLess(np.max(np.abs(self.shed.J @ inside.V[:, :16])), 1e-9)
        self.assertTrue(np.all(inside.lam[:16] <= free.lam[:16] + 1e-12))
        # Tied to every shaft in the shed, a treadle's share is the best fidelity any move
        # in the shed can reach: the squared cosine between its output change and the
        # pattern. The old move pushed through the shed is one such move, so it cannot beat it.
        tie_all = hd.TieUp(inside, patterns, inside.rows)
        tie_free = hd.TieUp(free, patterns, free.rows)
        for name in hd.TREADLE_NAMES:
            c = patterns[name]
            dy = free.J @ self.shed.project(tie_free.unit_move[name])
            fidelity = float(np.dot(dy, c) ** 2 / (np.dot(dy, dy) * np.dot(c, c)))
            self.assertGreaterEqual(tie_all.realizable[name], fidelity - 1e-9)
            self.assertLessEqual(tie_all.realizable[name], tie_free.realizable[name] + 1e-9)

    def test_no_pins_is_the_whole_space(self):
        shed = hd.Shed(self.w, [])
        d = self.rng.standard_normal(hd.P)
        self.assertTrue(np.array_equal(shed.project(d), d))
        self.assertEqual(shed.open_dimensions, hd.P)


class Selvedge(unittest.TestCase):
    def test_gate_port_agrees_with_wefts_vectors(self):
        vec = json.loads((HERE / "vendor" / "weft-invariants-vectors.json").read_text())
        ran = 0
        for v in vec["weight_update_vectors"]:
            if v.get("locked_mask") is not None:
                continue   # the masked path is not ported: the instrument never passes a mask
            got = hd.verify_weight_update_safety(
                [decode(x) for x in v["baseline"]], [decode(x) for x in v["candidate"]],
                decode(v["r_invariant"]), decode(v["budget"]), decode(v["cost"]))
            self.assertEqual(got[0], v["expected_accepted"], v["name"])
            self.assertEqual(got[3], v["expected_reason"], v["name"])
            want = decode(v["expected_distance"])
            if math.isfinite(want):
                self.assertAlmostEqual(got[1], want, delta=1e-9 * max(1.0, abs(want)), msg=v["name"])
            else:
                self.assertEqual(got[1], want, v["name"])
            want_b = decode(v["expected_remaining_budget"])
            if math.isnan(want_b):
                self.assertTrue(math.isnan(got[2]), v["name"])
            else:
                self.assertAlmostEqual(got[2], want_b, places=9, msg=v["name"])
            ran += 1
        self.assertGreaterEqual(ran, 10)

    def test_vendored_files_are_unchanged(self):
        manifest = json.loads((HERE / "VENDORED.json").read_text())
        for f in manifest["files"]:
            digest = hashlib.sha256((HERE / f["path"]).read_bytes()).hexdigest()
            self.assertEqual(digest, f["sha256"], f["path"])

    def test_the_proved_bound_is_never_exceeded(self):
        # Theorem 1 of the calibration theory, gamma = 1. A check of the bound and of the
        # port, on moves of several kinds and sizes. It is a proved bound: a failure here
        # would be a bug, not a finding.
        pts = hd.grid(24)
        rng = np.random.default_rng(3)
        for seed in (1, 7, 11):
            w = hd.init_host(seed)
            flat = hd.flatten(w)
            th = hd.Threading(w, hd.grid(hd.FIT_GRID))
            for radius in (0.01, 0.1, 0.5, 2.0):
                moves = [rng.standard_normal(hd.P) for _ in range(3)] + [th.V[:, 0], -th.V[:, 1]]
                bound = hd.certified_bound(w, pts, radius)
                for d in moves:
                    d = radius * d / np.linalg.norm(d)
                    out = hd.forward(hd.unflatten(flat + d), pts) - hd.forward(w, pts)
                    self.assertTrue(np.all(np.linalg.norm(out, axis=1) <= bound))


class Commitments(unittest.TestCase):
    def setUp(self):
        self.w = hd.init_host(7)
        self.flat = hd.flatten(self.w)
        self.root = hd.weight_root(self.w)

    def test_probes_follow_the_commitment(self):
        a = hd.fresh_probes(self.root, "c" * 64, 32)
        self.assertTrue(np.array_equal(a, hd.fresh_probes(self.root, "c" * 64, 32)))
        self.assertTrue(np.all((a >= 0.0) & (a < 1.0)))
        other = hd.weight_root(hd.unflatten(self.flat + 1e-9))
        self.assertFalse(np.array_equal(a, hd.fresh_probes(other, "c" * 64, 32)))   # one weight changes them
        self.assertFalse(np.array_equal(a, hd.fresh_probes(self.root, "d" * 64, 32)))

    def test_dispute_search_is_at_least_the_lattice_reading(self):
        th = hd.Threading(self.w, hd.grid(hd.FIT_GRID))
        w1 = hd.unflatten(self.flat + th.shaft_move(0, 0.4))
        worst, witness, rows = hd.dispute_search(self.w, w1)
        lattice = float(np.max(hd.change(self.w, w1, hd.grid(hd.DISPUTE_GRID))))
        self.assertGreaterEqual(worst, lattice)
        self.assertTrue(0.0 <= witness[0] <= 1.0 and 0.0 <= witness[1] <= 1.0)
        seen = float(hd.change(self.w, w1, np.array([witness]))[0])
        self.assertAlmostEqual(seen, worst, places=12)   # one input is the whole evidence
        self.assertEqual(rows, hd.DISPUTE_GRID ** 2 + 4 * hd.DISPUTE_REFINE * hd.DISPUTE_STEPS)

    def test_a_move_can_hide_from_probes_it_knows(self):
        # THEORY.md section 5: a proposer who sees the probes can search the directions the
        # probes cannot see. First order only; what the probes do see is second order.
        known, elsewhere = hd.grid(4), hd.grid(24)
        d = hd.hidden_move(self.w, known, elsewhere, 0.3)
        self.assertAlmostEqual(float(np.linalg.norm(d)), 0.3, places=12)
        self.assertLess(np.max(np.abs(hd.jacobian(self.w, known) @ d)), 1e-9)
        w1 = hd.unflatten(self.flat + d)
        self.assertGreater(hd.behaviour_change(self.w, w1, elsewhere), 3 * hd.behaviour_change(self.w, w1, known))


class Draft(unittest.TestCase):
    def setUp(self):
        self.draft = json.loads((HERE / "sample-draft.json").read_text())

    def test_the_recorded_session_replays(self):
        self.assertEqual(hd.replay_draft(self.draft), [])
        kinds = [e["kind"] for e in self.draft["events"]]
        self.assertIn("snap", kinds)
        self.assertIn("unpick", kinds)

    def test_a_changed_move_is_caught(self):
        d = copy.deepcopy(self.draft)
        ev = d["events"][1]
        move = hd.move_from_b64(ev["move_b64"]).copy()
        move[0] += 1e-9
        ev["move_b64"] = hd.move_to_b64(move)
        problems = hd.replay_draft(d)
        self.assertTrue(any("move bytes" in p for p in problems))
        self.assertTrue(any("weight root" in p for p in problems))

    def test_a_reordered_or_relabelled_event_is_caught(self):
        d = copy.deepcopy(self.draft)
        d["events"][2]["gesture"] = "knot"
        self.assertTrue(any("identifier" in p for p in hd.replay_draft(d)))
        d = copy.deepcopy(self.draft)
        d["events"][1], d["events"][2] = d["events"][2], d["events"][1]
        self.assertTrue(any("chain broken" in p for p in hd.replay_draft(d)))

    @staticmethod
    def _rechain(draft, start):
        """Recompute identifiers from `start` on, as someone rewriting the record would."""
        for i in range(start, len(draft["events"])):
            ev = draft["events"][i]
            if i > 0:
                ev["prev"] = draft["events"][i - 1]["id"]
            ev["id"] = hd.event_id(ev)

    def test_a_snap_needs_a_witness_that_refutes(self):
        # A dispute is one input. Point the recorded witness at the input that changed least
        # and the snap no longer stands, even with every identifier consistent.
        d = copy.deepcopy(self.draft)
        at = next(i for i, e in enumerate(d["events"]) if e["kind"] == "snap")
        snap = d["events"][at]
        w0 = hd.init_host(d["host"]["seed"])
        fell = hd.flatten(w0)
        for e in d["events"][:at]:
            if e["kind"] == "pick":
                fell = fell + hd.move_from_b64(e["move_b64"])
        cand = fell + hd.move_from_b64(snap["move_b64"])
        lattice = hd.grid(hd.DISPUTE_GRID)
        ch = hd.change(hd.unflatten(fell), hd.unflatten(cand), lattice)
        self.assertGreater(float(ch.max()), float(snap["tau"]))
        self.assertLess(float(ch.min()), float(snap["tau"]))
        snap["claim"]["witness"] = lattice[int(np.argmin(ch))].tolist()
        self.assertTrue(any("does not refute" in p for p in hd.replay_draft(d)))

    def test_a_light_gesture_on_a_tense_pick_is_caught(self):
        # Even with the chain recomputed, the gesture must match the tension the replay finds.
        d = copy.deepcopy(self.draft)
        at = next(i for i, e in enumerate(d["events"]) if e["kind"] == "pick" and e["reading"]["zone"] == "shared")
        d["events"][at]["gesture"] = "release"
        self._rechain(d, at)
        problems = hd.replay_draft(d)
        self.assertTrue(any("too light" in p for p in problems))
        self.assertFalse(any("chain" in p or "identifier" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
