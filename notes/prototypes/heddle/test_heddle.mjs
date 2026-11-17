// Tests for the browser mirror of the heddle prototype. Run from this folder:
//     node --test test_heddle.mjs
// `vectors.json` is written by the Python reference (make_vectors.py); these tests check that
// heddle.js reproduces it, and that the loom's own invariants hold.
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import test from "node:test";
import * as hd from "./heddle.js";

const read = (name) => JSON.parse(fs.readFileSync(new URL(name, import.meta.url), "utf8"));
const vec = read("./vectors.json");
const weft = read("./vendor/weft-invariants-vectors.json");
const SPECIAL = { Inf: Infinity, "-Inf": -Infinity, NaN: NaN };
const decode = (x) => (typeof x === "string" && x in SPECIAL ? SPECIAL[x] : x);
const flatPts = (pts) => Float64Array.from(pts.flat());
const close = (got, want, { rtol = 0, atol = 0 }, label = "") =>
  assert.ok(Math.abs(got - want) <= atol + rtol * Math.abs(want), `${label} ${got} vs ${want}`);

const w = hd.initHost(vec.seed);
const fit = hd.grid(hd.FIT_GRID);
const move = Float64Array.from({ length: hd.P }, (_, i) => ((((i * 37) % 101) - 50) / 50.0) * 0.01);

test("the generator, the weights and every hash match the reference bit for bit", () => {
  const draw = hd.mulberry32(12345);
  assert.deepEqual(Array.from({ length: 8 }, () => draw()), vec.exact.mulberry32_12345);
  assert.deepEqual(Array.from(w.slice(0, 6)), vec.exact.weights_head);
  assert.deepEqual(Array.from(w.slice(-3)), vec.exact.weights_tail);
  const w1 = hd.addScaled(w, move, 1.0);
  assert.equal(hd.weightRoot(w), vec.exact.w0_root);
  assert.equal(hd.weightRoot(w1), vec.exact.w1_root);
  const cid = hd.claimId(vec.exact.w0_root, vec.exact.w1_root, "0.5", vec.pins);
  assert.equal(cid, vec.exact.claim_id);
  assert.deepEqual(Array.from(hd.freshProbes(vec.exact.w1_root, cid, 8)), vec.exact.fresh_probes.flat());
  const ev = { seq: 1, kind: "pick", prev: "genesis", parent_root: vec.exact.w0_root, root: vec.exact.w1_root, move_sha256: "00".repeat(32), pins: vec.pins, gesture: "hold", tau: "0.5" };
  assert.equal(hd.eventId(ev), vec.exact.event_id);
});

test("the built-in SHA-256 agrees with Node's", () => {
  for (const n of [0, 1, 55, 56, 63, 64, 65, 3736]) {
    const bytes = Uint8Array.from({ length: n }, (_, i) => (i * 131 + 7) & 255);
    assert.equal(hd.toHex(hd.sha256(bytes)), crypto.createHash("sha256").update(bytes).digest("hex"));
  }
});

test("forward pass and Jacobian match the reference", () => {
  const n = vec.numeric;
  const pts = flatPts(n.forward.points);
  const y = hd.forward(w, pts);
  n.forward.outputs.flat().forEach((want, i) => close(y[i], want, n.forward, "forward"));
  const Jd = hd.matVec(hd.jacobian(w, pts), (pts.length / 2) * hd.M, hd.P, move);
  n.jacobian_times_move.values.forEach((want, i) => close(Jd[i], want, n.jacobian_times_move, "J d"));
  close(hd.behaviourChange(w, hd.addScaled(w, move, 1.0), fit), n.behaviour_change.value, n.behaviour_change);
});

test("block iteration finds the shafts an exact SVD finds", () => {
  const n = vec.numeric;
  const th = hd.thread(w, fit, 16);
  n.eigenvalues_16.values.forEach((want, i) => close(th.lam[i], want, n.eigenvalues_16, `lam[${i}]`));
  close(hd.predictedChange(th, move), n.predicted_change.value, n.predicted_change);
  for (let i = 0; i < 16; i++) {
    close(hd.norm(th.V[i]), 1.0, { atol: 1e-10 });
    close(hd.predictedChange(th, hd.shaftMove(th, i, 0.37)), 0.37, { atol: 1e-9 }, "travel is behaviour");
    for (let j = 0; j < i; j++) close(hd.dot(th.V[i], th.V[j]), 0.0, { atol: 1e-8 });
  }
  const y = hd.forward(w, fit);
  const patterns = Object.fromEntries(hd.TREADLE_NAMES.map((name) => [name, hd.treadlePattern(name, fit, y)]));
  const tie = hd.tieUp(th, patterns);
  for (const name of hd.TREADLE_NAMES) {
    close(tie.realizable[name], n.realizable_16.values[name], n.realizable_16, name);
    close(hd.norm(tie.unitMove[name]), n.unit_move_length_16.values[name], n.unit_move_length_16, name);
  }
  assert.equal(vec.exact.silent_dimensions, hd.P - th.rows);
});

test("a warm start reaches the same shafts in a few iterations", () => {
  const cold = hd.thread(w, fit, 16);
  const nearby = hd.addScaled(w, move, 1.0);
  const exact = hd.thread(nearby, fit, 16);
  const warm = hd.thread(nearby, fit, 16, { iterations: 10, warm: cold });
  for (let i = 0; i < 16; i++) close(warm.lam[i], exact.lam[i], { rtol: 1e-6 }, `lam[${i}]`);
});

test("the shed leaves the pins alone to first order", () => {
  const n = vec.numeric;
  const sh = hd.shed(w, vec.pins);
  assert.equal(sh.openDimensions, vec.exact.open_dimensions);
  const proj = sh.project(move);
  close(hd.norm(proj), n.projected_move_length.value, n.projected_move_length);
  const leak = hd.matVec(hd.jacobian(w, hd.pinPoints(vec.pins)), vec.pins.length * hd.M, hd.P, proj);
  assert.ok(Math.max(...leak.map(Math.abs)) < 1e-12);
});

test("the proved bound matches the reference and is never exceeded", () => {
  const n = vec.numeric;
  const pts = flatPts(n.forward.points);
  const b = hd.certifiedBound(w, pts, 0.3);
  n.certified_bound_r03.values.forEach((want, i) => close(b[i], want, n.certified_bound_r03, "bound"));
  const lattice = hd.grid(24);
  const x = hd.features(lattice);
  const y0 = hd.forwardFeatures(w, x);
  const th = hd.thread(w, fit, 4, { iterations: 60 });
  for (const radius of [0.01, 0.1, 0.5, 2.0]) {
    const bound = hd.certifiedBound(w, lattice, radius);
    for (const dir of [th.V[0], th.V[1], move]) {
      const y1 = hd.forwardFeatures(hd.addScaled(w, dir, radius / hd.norm(dir)), x);
      for (let i = 0; i < bound.length; i++) {
        const len = Math.hypot(y1[3 * i] - y0[3 * i], y1[3 * i + 1] - y0[3 * i + 1], y1[3 * i + 2] - y0[3 * i + 2]);
        assert.ok(len <= bound[i], `radius ${radius}: ${len} above the bound ${bound[i]}`);
      }
    }
  }
  const r = hd.certifiedRadius(w, lattice, 0.5);
  assert.ok(Math.max(...hd.certifiedBound(w, lattice, r)) <= 0.5 * Math.sqrt(hd.M) * (1 + 1e-9));
});

test("dispute search and the hidden move match the reference", () => {
  const n = vec.numeric;
  const th = hd.thread(w, fit, 16);
  const found = hd.disputeSearch(w, hd.addScaled(w, hd.shaftMove(th, 0, 0.4), 1.0));
  close(found.worst, n.dispute.worst, n.dispute, "worst");
  assert.equal(found.rows, n.dispute.rows);
  const known = hd.grid(n.hidden_move.known_grid);
  const elsewhere = hd.grid(n.hidden_move.elsewhere_grid);
  const hidden = hd.hiddenMove(w, known, elsewhere, n.hidden_move.radius);
  const wh = hd.addScaled(w, hidden, 1.0);
  close(hd.behaviourChange(w, wh, known), n.hidden_move.change_on_probes, n.hidden_move, "on probes");
  close(hd.behaviourChange(w, wh, elsewhere), n.hidden_move.change_elsewhere, n.hidden_move, "elsewhere");
});

// The same deferrals as weft's own browser test (weft/runtime/aywa/test_invariant_gate.mjs):
// the published gate does not implement these cases, and the instrument never reaches them.
const BROWSER_DEFERRED = new Set([
  "reject_pre_cast_radius_boundary", "accept_huge_scale_weight_move",
  "reject_locked_mask_ulp_tamper", "accept_locked_mask_negzero_normalize", "reject_negative_cost",
]);

test("the vendored weft gate passes weft's conformance vectors", () => {
  let ran = 0;
  for (const v of weft.weight_update_vectors) {
    if (v.locked_mask != null || BROWSER_DEFERRED.has(v.name)) continue;
    const got = hd.verifyWeightUpdateSafety((v.baseline ?? []).map(decode), (v.candidate ?? []).map(decode), decode(v.r_invariant), decode(v.budget), decode(v.cost));
    assert.equal(got.accepted, v.expected_accepted, v.name);
    assert.equal(got.reason, v.expected_reason, v.name);
    const want = decode(v.expected_distance);
    if (Number.isFinite(want)) close(got.distance, want, { atol: 1e-9 }, v.name);
    else assert.equal(got.distance, want, v.name);
    ran += 1;
  }
  assert.ok(ran >= 8);
});

test("a session: light touches weave on release, tense picks need a hold, a refuted claim snaps", () => {
  const loom = new hd.Loom({ seed: vec.seed });
  const light = loom.moveFor({ warm: 0.08 });
  assert.equal(loom.assess(light).zone, "auto");
  const first = loom.commit(light, "release", { warm: 0.08 });
  assert.equal(first.kind, "pick");
  assert.equal(loom.fell.root, first.root);
  assert.equal(loom.fell.budget, 23);

  const tense = loom.moveFor({ tilt: 0.15 });
  const zone = loom.assess(tense).zone;
  assert.notEqual(zone, "auto");
  const before = loom.fell.root;
  assert.deepEqual(loom.commit(tense, "release", { tilt: 0.15 }), { needs: zone });
  assert.equal(loom.fell.root, before, "a gesture that is too light changes nothing");
  assert.equal(loom.events.length, 1);
  assert.equal(loom.commit(tense, zone === "knot" ? "knot" : "hold", { tilt: 0.15 }).kind, "pick");

  const far = loom.moveFor({}, { 0: 0.9 });
  const held = loom.fell.root;
  const snap = loom.commit(far, "knot");
  assert.equal(snap.kind, "snap");
  assert.ok(snap.claim.worst > 0.5 && snap.claim.refuted);
  assert.equal(loom.fell.root, held, "a snapped pick does not move the fell");
  assert.equal(loom.fell.budget, 21, "and its budget is spent");
  // One input is the whole evidence.
  const cand = hd.addScaled(loom.fell.w, far, 1.0);
  assert.ok(hd.change(loom.fell.w, cand, Float64Array.from(snap.claim.witness))[0] > 0.5);

  loom.unpick(first.root);
  assert.equal(loom.fell.root, first.root);
  const ids = loom.events.map((e) => e.id);
  loom.events.forEach((e, i) => {
    assert.equal(e.prev, i ? ids[i - 1] : "genesis");
    assert.equal(hd.eventId(e), e.id);
  });
});

test("weft's gate refuses a pick that leaves the ball, and spends nothing", () => {
  const loom = new hd.Loom({ seed: vec.seed, rInvariant: 0.25 });
  const d = loom.moveFor({ light: 0.6 });
  const a = loom.assess(d);
  assert.equal(a.zone, "refused");
  const out = loom.commit(d, "knot", { light: 0.6 });
  assert.equal(out.refused.reason, "baseline_distance_exceeded");
  assert.equal(loom.events.length, 0);
  assert.equal(loom.fell.budget, 24);
});

test("with heddles raised the loom is threaded around them", () => {
  const n = vec.numeric;
  const sh = hd.shed(w, vec.pins);
  const th = hd.thread(w, fit, 16, { basis: sh.Q });
  n.eigenvalues_16_in_shed.values.forEach((want, i) => close(th.lam[i], want, n.eigenvalues_16_in_shed, `lam[${i}]`));
  const pinJ = hd.jacobian(w, hd.pinPoints(vec.pins));
  for (const v of th.V) {
    // every shaft already leaves the pinned inputs alone to first order
    assert.ok(Math.max(...hd.matVec(pinJ, vec.pins.length * hd.M, hd.P, v).map(Math.abs)) < 1e-9);
  }
  const y = hd.forward(w, fit);
  const patterns = Object.fromEntries(hd.TREADLE_NAMES.map((name) => [name, hd.treadlePattern(name, fit, y)]));
  const tie = hd.tieUp(th, patterns);
  for (const name of hd.TREADLE_NAMES) close(tie.realizable[name], n.realizable_16_in_shed.values[name], n.realizable_16_in_shed, name);
});

test("raising heddles re-threads the loom, and a pick made there leaves them still", () => {
  const loom = new hd.Loom({ seed: vec.seed });
  const before = loom.tie.realizable.light;
  const lamBefore = [...loom.threading.lam];
  loom.setPins(Array.from({ length: 16 }, (_, i) => 130 + i * 241));
  assert.equal(loom.shed.openDimensions, hd.P - 48);
  loom.threading.lam.forEach((l, i) => assert.ok(l <= lamBefore[i] + 1e-9, "pins never add reach"));
  assert.ok(loom.tie.realizable.light <= before + 1e-9);
  const d = loom.moveFor({ light: 0.1, tilt: 0.1 });
  const pinJ = hd.jacobian(loom.fell.w, hd.pinPoints(loom.pins));
  assert.ok(Math.max(...hd.matVec(pinJ, 48, hd.P, d).map(Math.abs)) < 1e-9);
  const ev = loom.commit(d, "knot", { light: 0.1, tilt: 0.1 });
  assert.ok(ev.kind === "pick" || ev.kind === "snap");
  assert.ok(ev.reading.pin_leak < 0.02, `pin leak ${ev.reading.pin_leak}`);
});
