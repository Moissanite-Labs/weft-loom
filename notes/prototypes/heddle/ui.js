/**
 * Heddle prototype: the instrument. All mathematics is in heddle.js; this file draws it and
 * turns gestures into picks. The page is laid out as a weaving draft, because the first-order
 * picture of a pick is one:  output change = threading x tie-up x treadling.
 *
 * What comes from Spaceship (github.com/chuanqisun/spaceship), in this page's terms:
 *   focus monitor          the cloth dims wherever the pending move changes nothing
 *   attention lock         heddles: points pinned by hand, kept still to first order
 *   future vector steering shafts and treadles, in units of behaviour
 *   realtime re-generation futures woven ahead of the knob and discarded when stale, and unpicking
 */
import * as hd from "./heddle.js";

const TRAVEL = 0.6;                       // sliders run from -TRAVEL to +TRAVEL, in behaviour units
const FAN = [-0.6, -0.4, -0.2, 0.2, 0.4, 0.6];
const HOLD_MS = { auto: 0, shared: 450, knot: 1300 };
const LIVE = 64, SHARP = 128, THUMB = 24, SHAFT_PIC = 10;
const MAX_PINS = 32;
const $ = (id) => document.getElementById(id);
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const fmt = (v, d = 3) => (Number.isFinite(v) ? v.toFixed(d) : "–");
const signed = (v, d = 2) => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(d);
const pct = (v) => `${Math.round(100 * Math.max(0, Math.min(1, v)))}%`;

// ---------------------------------------------------------------------------------------
// Display: outputs to colour. Display only; every check reads the raw outputs.
// The three outputs are rotated into lightness, warm-cool and green-magenta, then OKLab.
// ---------------------------------------------------------------------------------------

const GAMMA_LUT = new Uint8ClampedArray(4097);
for (let i = 0; i <= 4096; i++) {
  const c = i / 4096;
  GAMMA_LUT[i] = Math.round(255 * (c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(c, 1 / 2.4) - 0.055));
}
const lut = (c) => GAMMA_LUT[c <= 0 ? 0 : c >= 1 ? 4096 : (c * 4096) | 0];

function paint(y, img) {
  const data = img.data;
  const n = y.length / 3;
  for (let i = 0; i < n; i++) {
    const y0 = y[3 * i], y1 = y[3 * i + 1], y2 = y[3 * i + 2];
    const L = 0.6 + 0.25 * Math.tanh(0.5 * (y0 + y1 + y2) * 0.5773502691896258);
    const c1 = 0.115 * Math.tanh(0.6 * (y0 - y2) * 0.7071067811865476);
    const c2 = 0.1 * Math.tanh(0.6 * (2 * y1 - y0 - y2) * 0.408248290463863);
    const a = 0.55 * c1 - 0.83 * c2, b = 0.83 * c1 + 0.55 * c2;
    const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
    const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
    const s_ = L - 0.0894841775 * a - 1.291485548 * b;
    const l = l_ * l_ * l_, m = m_ * m_ * m_, s = s_ * s_ * s_;
    data[4 * i] = lut(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s);
    data[4 * i + 1] = lut(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s);
    data[4 * i + 2] = lut(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s);
    data[4 * i + 3] = 255;
  }
}

function makeField(n) {
  const canvas = document.createElement("canvas");
  canvas.width = n;
  canvas.height = n;
  return { n, x: hd.features(hd.grid(n)), y: new Float64Array(n * n * 3), img: new ImageData(n, n), canvas, ctx: canvas.getContext("2d") };
}
const H1 = new Float64Array(hd.H), H2 = new Float64Array(hd.H);
function renderField(field, w) {
  hd.forwardFeatures(w, field.x, field.y, H1, H2);
  paint(field.y, field.img);
  field.ctx.putImageData(field.img, 0, 0);
}

// ---------------------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------------------

const live = makeField(LIVE), sharp = makeField(SHARP), thumb = makeField(THUMB);
const fellY = new Float64Array(LIVE * LIVE * 3);
const veil = document.createElement("canvas");
veil.width = veil.height = LIVE;
const veilImg = new ImageData(LIVE, LIVE);
const cloth = $("cloth"), ctx = cloth.getContext("2d");

let loom;
let treadling = {};
let shaftTravel = {};
let hidden = null;                       // a pending hidden move, or null
let active = { kind: "treadle", key: "warm" };
let lastEvent = null;
let selectedRoot = null;
let pending = null;                      // { d, a } for the current controls
let dirty = true, isSharp = false, sharpAt = 0;
let fan = { key: "", items: [] };
const spec = { woven: 0, taken: 0, discarded: 0 };
let frameMs = 0;
let weave = null;
let effShare = {};

function newLoom(seed, shafts) {
  loom = new hd.Loom({ seed, shafts });
  treadling = Object.fromEntries(hd.TREADLE_NAMES.map((n) => [n, 0]));
  shaftTravel = {};
  hidden = null;
  lastEvent = null;
  selectedRoot = null;
  $("seed-out").value = seed;
  $("r-out").textContent = fmt(loom.rInvariant, 1);
  $("tau-out").textContent = loom.tau;
  buildThreading();
  afterFellChange();
  renderPicks();
  showLamp(null);
}

const isResting = () => !hidden && Object.values(treadling).every((t) => !t) && Object.values(shaftTravel).every((t) => !t);

function pendingMove() {
  return hidden ? loom.shed.project(hidden) : loom.moveFor(treadling, shaftTravel);
}

function invalidate() {
  dirty = true;
  isSharp = false;
}

// ---------------------------------------------------------------------------------------
// Threading, tie-up, treadles: built once per shaft count, refreshed at every fell
// ---------------------------------------------------------------------------------------

function buildThreading() {
  const K = loom.shafts;
  const shafts = $("shafts");
  shafts.replaceChildren();
  for (let i = 0; i < K; i++) {
    const row = document.createElement("div");
    row.className = "shaft";
    row.innerHTML = `<span class="ix">${i + 1}</span><canvas width="${SHAFT_PIC}" height="${SHAFT_PIC}" aria-hidden="true"></canvas>
      <span class="stiff" title="Stiffness: how much the cloth changes per step of weight"><i></i></span>
      <input type="range" id="shaft-${i}" min="${-TRAVEL}" max="${TRAVEL}" step="0.01" value="0" aria-label="Travel along shaft ${i + 1}">
      <span class="val">0.00</span>`;
    row.querySelector("input").addEventListener("input", (e) => {
      hidden = null;
      shaftTravel[i] = Number(e.target.value);
      active = { kind: "shaft", key: i };
      invalidate();
    });
    shafts.append(row);
  }
  const head = $("tie-head"), cells = $("tie-cells"), thead = $("treadle-head"), sliders = $("treadles"), share = $("treadle-share");
  head.replaceChildren(document.createElement("span"));
  thead.replaceChildren(document.createElement("span"));
  share.replaceChildren(document.createElement("span"));
  sliders.replaceChildren(document.createElement("span"));
  cells.replaceChildren();
  for (const name of hd.TREADLE_NAMES) {
    for (const h of [head, thead]) {
      const s = document.createElement("span");
      s.textContent = name;
      h.append(s);
    }
    const sh = document.createElement("span");
    sh.className = "share";
    sh.id = `share-${name}`;
    sh.title = "Share of this named change the shafts and the heddles let through";
    share.append(sh);
    const t = document.createElement("div");
    t.className = "treadle";
    t.innerHTML = `<span class="throw"><input type="range" id="treadle-${name}" min="${-TRAVEL}" max="${TRAVEL}" step="0.01" value="0" aria-label="Travel of the ${name} treadle" aria-orientation="vertical"></span><span class="val">0.00</span>`;
    t.querySelector("input").addEventListener("input", (e) => {
      hidden = null;
      treadling[name] = Number(e.target.value);
      active = { kind: "treadle", key: name };
      invalidate();
    });
    sliders.append(t);
  }
  for (let i = 0; i < K; i++) {
    const ix = document.createElement("span");
    ix.className = "ixc";
    ix.textContent = i + 1;
    cells.append(ix);
    for (const name of hd.TREADLE_NAMES) {
      const c = document.createElement("span");
      c.className = "cell";
      c.id = `tie-${i}-${name}`;
      c.append(document.createElement("i"));
      cells.append(c);
    }
  }
  document.querySelectorAll("[data-shafts]").forEach((b) => b.setAttribute("aria-pressed", String(Number(b.dataset.shafts) === K)));
}

function mark(el, value, full) {
  const size = Math.abs(value) < 0.02 * full ? 0 : Math.round(3 + 13 * Math.min(1, Math.abs(value) / full));
  el.className = `mark${value < 0 ? " neg" : ""}`;
  el.style.width = el.style.height = `${size}px`;
}

/** Everything that depends on where the fell is: shaft pictures, tie-up marks, shares. */
function afterFellChange() {
  const th = loom.threading;
  const root = Math.sqrt(th.rows);
  const pic = new ImageData(SHAFT_PIC, SHAFT_PIC);
  const rows = $("shafts").children;
  for (let i = 0; i < th.V.length; i++) {
    const y = th.U[i].map((v) => 1.6 * v * root);
    paint(y, pic);
    rows[i].querySelector("canvas").getContext("2d").putImageData(pic, 0, 0);
    rows[i].querySelector(".stiff i").style.width = pct(Math.sqrt(th.lam[i] / th.lam[0]));
    rows[i].querySelector(".stiff").title = `Eigenvalue ${fmt(th.lam[i])}. One unit of travel is a weight move of length ${fmt(1 / Math.sqrt(th.lam[i]))}.`;
    for (const name of hd.TREADLE_NAMES) mark($(`tie-${i}-${name}`).firstChild, loom.tie.alpha[name][i], 0.8);
  }
  refreshShares();
  hd.forwardFeatures(loom.fell.w, live.x, fellY, H1, H2);
  const picks = loom.events.filter((e) => e.kind === "pick").length;
  $("fell-note").textContent = `the fell is ${loom.fell.root.slice(0, 10)}… · ${picks} ${picks === 1 ? "pick" : "picks"} beaten in`;
  $("draft-out").value = JSON.stringify(loom.exportDraft());
  syncControls();
  invalidate();
}

/** The share of each named change that the shafts and the raised heddles let through. */
function refreshShares() {
  const th = loom.threading;
  for (const name of hd.TREADLE_NAMES) {
    const through = hd.matVec(th.J, th.rows, hd.P, loom.shed.project(loom.tie.unitMove[name]));
    effShare[name] = hd.gainAlong(through, loom.tie.patterns[name]);
    $(`share-${name}`).textContent = pct(effShare[name]);
  }
  $("f-pins").textContent = `${loom.pins.length} raised · ${loom.shed.openDimensions} ways open`;
}

function syncControls() {
  for (const name of hd.TREADLE_NAMES) {
    const input = $(`treadle-${name}`);
    input.value = treadling[name] || 0;
    const cell = input.closest(".treadle");
    cell.querySelector(".val").textContent = signed(treadling[name] || 0);
    cell.classList.toggle("live", !!treadling[name]);
  }
  for (let i = 0; i < loom.shafts; i++) {
    const input = $(`shaft-${i}`);
    input.value = shaftTravel[i] || 0;
    input.parentElement.querySelector(".val").textContent = signed(shaftTravel[i] || 0);
    input.parentElement.classList.toggle("live", !!shaftTravel[i]);
  }
}

// ---------------------------------------------------------------------------------------
// The cloth
// ---------------------------------------------------------------------------------------

function sizeCloth() {
  const side = Math.round(cloth.clientWidth * Math.min(2, window.devicePixelRatio || 1));
  if (side > 0 && cloth.width !== side) {
    cloth.width = cloth.height = side;
    weave = null;
  }
}

/** A plain-weave relief: each cell of the 64 x 64 picture is one crossing of warp and weft. */
function weavePattern(cell) {
  const t = document.createElement("canvas");
  t.width = t.height = Math.max(2, Math.round(cell * 2));
  const c = t.getContext("2d");
  const s = t.width / 2;
  for (let i = 0; i < 2; i++) {
    for (let j = 0; j < 2; j++) {
      const across = (i + j) % 2 === 0;
      const g = across ? c.createLinearGradient(0, j * s, 0, (j + 1) * s) : c.createLinearGradient(i * s, 0, (i + 1) * s, 0);
      g.addColorStop(0, "rgba(0,0,0,0.26)");
      g.addColorStop(0.5, "rgba(255,255,255,0.10)");
      g.addColorStop(1, "rgba(0,0,0,0.26)");
      c.fillStyle = g;
      c.fillRect(i * s, j * s, s, s);
    }
  }
  return ctx.createPattern(t, "repeat");
}

function drawCloth(field) {
  const S = cloth.width;
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = "high";
  ctx.globalAlpha = 1;
  ctx.drawImage(field.canvas, 0, 0, S, S);
  weave ??= weavePattern(S / LIVE);
  ctx.fillStyle = weave;
  ctx.fillRect(0, 0, S, S);

  const ink = css("--ink"), paper = css("--paper");
  // Focus: dim what the pending move leaves alone, so the eye goes where the weft will land.
  if ($("show-focus").checked && !isResting()) {
    let top = 0;
    const ch = new Float64Array(LIVE * LIVE);
    for (let i = 0; i < ch.length; i++) {
      const a = live.y[3 * i] - fellY[3 * i], b = live.y[3 * i + 1] - fellY[3 * i + 1], c = live.y[3 * i + 2] - fellY[3 * i + 2];
      ch[i] = Math.sqrt((a * a + b * b + c * c) / 3);
      if (ch[i] > top) top = ch[i];
    }
    if (top > 1e-4) {
      const rgb = paper.startsWith("#") ? [1, 3, 5].map((k) => parseInt(paper.slice(k, k + 2), 16)) : [128, 128, 128];
      for (let i = 0; i < ch.length; i++) {
        const quiet = 1 - Math.min(1, ch[i] / top);
        veilImg.data[4 * i] = rgb[0];
        veilImg.data[4 * i + 1] = rgb[1];
        veilImg.data[4 * i + 2] = rgb[2];
        veilImg.data[4 * i + 3] = Math.round(175 * quiet * quiet);
      }
      veil.getContext("2d").putImageData(veilImg, 0, 0);
      ctx.drawImage(veil, 0, 0, S, S);
    }
  }
  const px = S / 640;
  const dot = (u, v, r, fill, stroke) => {
    ctx.beginPath();
    ctx.arc(u * S, v * S, r * px, 0, 2 * Math.PI);
    if (fill) { ctx.fillStyle = fill; ctx.fill(); }
    if (stroke) { ctx.lineWidth = 2 * px; ctx.strokeStyle = stroke; ctx.stroke(); }
  };
  if ($("show-probes").checked) {
    for (let i = 0; i < loom.fit.length; i += 2) dot(loom.fit[i], loom.fit[i + 1], 2.2, ink);
    if (lastEvent?.claim) {
      const fresh = hd.freshProbes(lastEvent.root, lastEvent.claim.id, lastEvent.claim.probes);
      ctx.strokeStyle = ink;
      ctx.lineWidth = 1.5 * px;
      for (let i = 0; i < fresh.length; i += 2) {
        const x = fresh[i] * S, y = fresh[i + 1] * S, r = 4 * px;
        ctx.beginPath();
        ctx.moveTo(x - r, y - r); ctx.lineTo(x + r, y + r); ctx.moveTo(x - r, y + r); ctx.lineTo(x + r, y - r);
        ctx.stroke();
      }
    }
  }
  if (hidden) {
    const known = hd.grid(4);
    ctx.fillStyle = ink;
    for (let i = 0; i < known.length; i += 2) ctx.fillRect(known[i] * S - 4 * px, known[i + 1] * S - 4 * px, 8 * px, 8 * px);
  }
  const pins = hd.pinPoints(loom.pins);
  for (let i = 0; i < pins.length; i += 2) {
    dot(pins[i], pins[i + 1], 7, paper, ink);
    dot(pins[i], pins[i + 1], 2, ink);
  }
  if (lastEvent?.claim && isResting()) {
    const [u, v] = lastEvent.claim.witness;
    dot(u, v, 11, null, css(lastEvent.kind === "snap" ? "--madder" : "--woad"));
  }
}

// ---------------------------------------------------------------------------------------
// The pending pick: readouts, the beat, the shed
// ---------------------------------------------------------------------------------------

const ZONE_WORD = { auto: "light", shared: "deliberate", knot: "knot", refused: "refused" };
const REASON = {
  baseline_distance_exceeded: "it would leave the gate's radius",
  insufficient_metabolic_budget: "no picks are left in the budget",
  non_positive_budget_or_cost: "no picks are left in the budget",
};

function showPending() {
  const { a } = pending;
  const resting = isResting();
  $("f-length").textContent = fmt(a.length);
  $("f-pred").textContent = fmt(a.predicted);
  $("f-worst").textContent = `${fmt(a.predictedMax)} of ${loom.tau}`;
  $("f-tension").textContent = fmt(a.tension, 2);
  const zone = $("f-zone");
  zone.dataset.zone = resting ? "auto" : a.zone;
  zone.textContent = resting ? "rest" : ZONE_WORD[a.zone];
  $("f-budget").textContent = `${loom.fell.budget} of ${loom.initialBudget}`;
  const ball = $("selv-ball"), beh = $("selv-beh");
  const frac = Math.min(1, a.ball);
  ball.firstElementChild.style.height = pct(frac);
  ball.dataset.zone = a.gate.accepted ? (a.ball < 0.3 ? "auto" : "shared") : "refused";
  ball.lastElementChild.style.bottom = pct(certified / loom.rInvariant);
  beh.firstElementChild.style.height = pct(Math.min(1, a.behaviour));
  beh.dataset.zone = a.behaviour > 1 ? "over" : a.behaviour < 0.3 ? "auto" : "shared";
  const beat = $("beat"), label = $("beat-label");
  beat.dataset.zone = resting ? "auto" : a.zone;
  beat.disabled = resting || !a.gate.accepted;
  label.textContent = resting ? "Press a treadle, then beat"
    : !a.gate.accepted ? `The gate refuses: ${REASON[a.gate.reason] ?? a.gate.reason}`
    : a.zone === "auto" ? "Beat"
    : a.zone === "shared" ? "Hold to beat"
    : "Hold longer: tie the knot";
  $("frame-note").textContent = `Redraw ${fmt(frameMs, 1)} ms of script time, in a 16.7 ms frame. Futures woven ahead ${spec.woven}, taken ${spec.taken}, discarded ${spec.discarded}.`;
}

function fanKey() {
  const rest = hd.TREADLE_NAMES.map((n) => (active.kind === "treadle" && active.key === n ? "*" : treadling[n] || 0));
  const sh = Array.from({ length: loom.shafts }, (_, i) => (active.kind === "shaft" && active.key === i ? "*" : shaftTravel[i] || 0));
  return [loom.fell.root, loom.pins.join("."), loom.shafts, active.kind, active.key, rest.join(","), sh.join(",")].join("|");
}

function buildFan() {
  const box = $("fan");
  box.replaceChildren();
  fan.items = FAN.map((t) => {
    const b = document.createElement("button");
    b.innerHTML = `<canvas width="${THUMB}" height="${THUMB}" aria-hidden="true"></canvas><span>${signed(t)}</span>`;
    b.setAttribute("aria-label", `Set ${active.kind} ${active.kind === "shaft" ? active.key + 1 : active.key} to ${signed(t)}`);
    const item = { t, button: b, woven: false, taken: false };
    b.addEventListener("click", () => {
      hidden = null;
      if (active.kind === "treadle") treadling[active.key] = t;
      else shaftTravel[active.key] = t;
      if (item.woven && !item.taken) {
        item.taken = true;
        spec.taken += 1;
      }
      syncControls();
      invalidate();
    });
    box.append(b);
    return item;
  });
}

/** Weave one future per idle frame. A future that is stale before it is taken is discarded. */
function tendFan() {
  const key = hidden ? "hidden" : fanKey();
  if (key !== fan.key) {
    spec.discarded += fan.items.filter((it) => it.woven && !it.taken).length;
    fan.key = key;
    buildFan();
    $("shed-note").textContent = hidden ? "none while a hidden move is pending"
      : `along ${active.kind === "shaft" ? `shaft ${active.key + 1}` : `the ${active.key} treadle`}, woven ahead of you`;
    return true;
  }
  if (hidden) return false;
  const item = fan.items.find((it) => !it.woven);
  if (!item) return false;
  const tr = { ...treadling }, sh = { ...shaftTravel };
  if (active.kind === "treadle") tr[active.key] = item.t;
  else sh[active.key] = item.t;
  const d = loom.moveFor(tr, sh);
  const a = loom.assess(d);
  renderField(thumb, a.cand);
  item.button.querySelector("canvas").getContext("2d").putImageData(thumb.img, 0, 0);
  item.button.dataset.zone = a.zone;
  item.button.title = a.gate.accepted ? `Tension ${fmt(a.tension, 2)}: a ${ZONE_WORD[a.zone]} pick` : "The gate would refuse this one";
  item.woven = true;
  spec.woven += 1;
  return true;
}

// ---------------------------------------------------------------------------------------
// Beating, unpicking, the lamp, the list of picks
// ---------------------------------------------------------------------------------------

function describePending() {
  const parts = hd.TREADLE_NAMES.filter((n) => treadling[n]).map((n) => `${n} ${signed(treadling[n])}`);
  for (const [i, t] of Object.entries(shaftTravel)) if (t) parts.push(`shaft ${Number(i) + 1} ${signed(t)}`);
  return hidden ? "hidden move" : parts.join(", ");
}

function beat(gesture) {
  if (!pending || isResting()) return;
  const pressed = Object.fromEntries(Object.entries(treadling).filter(([, t]) => t));
  const result = loom.commit(pending.d, gesture, hidden ? {} : pressed, describePending());
  if (result.refused || result.needs) {
    showLamp({ kind: "refused", text: result.needs ? "That pick needs a longer hold." : `The gate refused: ${REASON[result.refused.reason] ?? result.refused.reason}.` });
    return;
  }
  lastEvent = result;
  for (const n of hd.TREADLE_NAMES) treadling[n] = 0;
  shaftTravel = {};
  hidden = null;
  selectedRoot = null;
  afterFellChange();
  renderPicks();
  showLamp(result);
}

function showLamp(ev) {
  const box = $("lamp");
  const p = (html) => `<p>${html}</p>`;
  if (!ev) {
    box.dataset.kind = "none";
    box.innerHTML = p("Nothing has been beaten in yet.");
    return;
  }
  box.dataset.kind = ev.kind;
  if (ev.text) {
    box.innerHTML = p(ev.text);
    return;
  }
  if (ev.kind === "unpick") {
    box.innerHTML = p(`<strong>Unpicked.</strong> The fell is back at ${ev.root.slice(0, 10)}…. The picks you undid stay in the draft, and the budget they spent stays spent.`);
    return;
  }
  const c = ev.claim, r = ev.reading;
  const lines = [];
  if (ev.kind === "snap") {
    lines.push(p(`<strong>Pick ${ev.seq} snapped.</strong> One point of the cloth would have moved by ${fmt(c.worst)}, over the limit of ${ev.tau}. It is ringed on the cloth. The cloth stays where it was and the attempt stays on the record.`));
  } else {
    lines.push(p(`<strong>Pick ${ev.seq} admitted.</strong> A search of ${c.rows.toLocaleString("en")} points found none that moved more than ${fmt(c.worst)}, under the limit of ${ev.tau}. That is a sampled reading: a larger search could still find one.`));
  }
  lines.push(p(`Predicted change ${fmt(r.predicted)} on the fit probes. Measured ${fmt(c.realized)} on ${c.probes} probes drawn after the pick was fixed.`));
  for (const [name, d] of Object.entries(r.delivered)) {
    lines.push(p(`<span class="mono">${name}</span>: asked ${signed(d.asked)}, promised ${signed(d.promised, 3)}, delivered ${signed(d.gain, 3)}.`));
  }
  if (ev.pins.length) lines.push(p(`${ev.pins.length} ${ev.pins.length === 1 ? "heddle" : "heddles"} raised. The most a pinned point moved: ${fmt(r.pin_leak, 4)}.`));
  lines.push(p(`Gesture: ${ev.gesture}, for tension ${fmt(r.tension, 2)}. Distance from baseline ${fmt(ev.gate.distance)} of ${fmt(loom.rInvariant, 1)}.`));
  box.innerHTML = lines.join("");
}

/** Which picks are in the cloth now: walk the draft as the replay does. */
function picksInCloth() {
  const roots = [loom.baseRoot], seqs = [];
  for (const ev of loom.events) {
    if (ev.kind === "pick") {
      roots.push(ev.root);
      seqs.push(ev.seq);
    } else if (ev.kind === "unpick") {
      const at = roots.lastIndexOf(ev.root);
      roots.length = at + 1;
      seqs.length = at;
    }
  }
  return { roots, seqs: new Set(seqs) };
}

function renderPicks() {
  const box = $("picks");
  const { roots, seqs } = picksInCloth();
  box.replaceChildren();
  const row = (cls, ix, root) => {
    const r = document.createElement("div");
    r.className = `pick ${cls}`;
    const i = document.createElement("span");
    i.className = "ix";
    i.textContent = ix;
    r.append(i);
    if (root && roots.includes(root) && root !== loom.fell.root) {
      r.tabIndex = 0;
      r.setAttribute("role", "button");
      const pick = () => {
        selectedRoot = selectedRoot === root ? null : root;
        renderPicks();
      };
      r.addEventListener("click", pick);
      r.addEventListener("keydown", (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), pick()));
    }
    if (root && root === selectedRoot) r.setAttribute("aria-current", "true");
    return r;
  };
  const wide = (r, text) => {
    const w = document.createElement("span");
    w.className = "wide";
    w.textContent = text;
    r.append(w);
  };
  const base = row("", "0", loom.baseRoot);
  wide(base, "baseline (the warp)");
  box.append(base);
  for (const ev of loom.events) {
    const inCloth = ev.kind === "pick" && seqs.has(ev.seq);
    const r = row(ev.kind === "pick" ? (inCloth ? "" : "gone") : ev.kind, ev.seq, inCloth ? ev.root : null);
    const tr = ev.reading?.treadling ?? {};
    if (ev.kind === "unpick") wide(r, `unpicked to ${ev.root === loom.baseRoot ? "the baseline" : ev.root.slice(0, 8) + "…"}`);
    else if (!Object.keys(tr).length) wide(r, `${ev.reading.note}${ev.kind === "snap" ? " · snapped" : ""}`);
    else {
      for (const name of hd.TREADLE_NAMES) {
        const c = document.createElement("span");
        c.className = "cell";
        const m = document.createElement("i");
        mark(m, tr[name] || 0, TRAVEL);
        c.append(m);
        c.title = tr[name] ? `${name} ${signed(tr[name])}` : "";
        r.append(c);
      }
    }
    r.title = ev.kind === "snap" ? "Snapped: the claim was refuted" : ev.kind === "pick" && !inCloth ? "Unpicked" : r.title;
    box.append(r);
  }
  box.scrollTop = box.scrollHeight;
  const un = $("unpick");
  un.hidden = !selectedRoot;
  if (selectedRoot) {
    const ev = loom.events.find((e) => e.kind === "pick" && e.root === selectedRoot);
    un.firstChild.textContent = `Hold to unpick back to ${ev ? `pick ${ev.seq}` : "the baseline"}`;
  }
}

/** Press and hold. `ms()` says how long the hold must be now; 0 means a plain click does it. */
function holdable(el, ms, done) {
  let raf = 0, started = 0, need = 0, down = false;
  const stop = () => {
    cancelAnimationFrame(raf);
    el.style.removeProperty("--fill");
    down = false;
  };
  const tick = () => {
    const f = Math.min(1, (performance.now() - started) / need);
    el.style.setProperty("--fill", f);
    if (f >= 1) {
      stop();
      done(need);
    } else raf = requestAnimationFrame(tick);
  };
  const start = () => {
    if (el.disabled || down) return;
    need = ms();
    if (need <= 0) return;      // a click will do it
    down = true;
    started = performance.now();
    raf = requestAnimationFrame(tick);
  };
  el.addEventListener("pointerdown", (e) => { if (e.button === 0) start(); });
  for (const type of ["pointerup", "pointerleave", "pointercancel", "blur"]) el.addEventListener(type, stop);
  el.addEventListener("keydown", (e) => { if ((e.key === " " || e.key === "Enter") && !e.repeat) start(); });
  el.addEventListener("keyup", stop);
  el.addEventListener("click", (e) => {
    if (ms() <= 0 && !el.disabled) done(0);
    else e.preventDefault();
  });
  el.addEventListener("contextmenu", (e) => e.preventDefault());
}

// ---------------------------------------------------------------------------------------
// Wiring
// ---------------------------------------------------------------------------------------

let certified = 0;

function frame(now) {
  const t0 = performance.now();
  if (dirty) {
    dirty = false;
    sizeCloth();
    const d = pendingMove();
    pending = { d, a: loom.assess(d) };
    renderField(live, pending.a.cand);
    drawCloth(live);
    syncControls();
    showPending();
    sharpAt = now + 220;
    frameMs = frameMs ? 0.8 * frameMs + 0.2 * (performance.now() - t0) : performance.now() - t0;
  } else if (!tendFan() && !isSharp && now >= sharpAt) {
    // At rest: one sharper picture, the same weights at twice the lattice.
    renderField(sharp, pending.a.cand);
    drawCloth(sharp);
    isSharp = true;
    showPending();
  }
  requestAnimationFrame(frame);
}

function start() {
  newLoom(7, 16);
  certified = hd.certifiedRadius(loom.base, hd.grid(32), loom.tauValue);
  $("selv-ball").title += `. The mark is the radius, ${fmt(certified, 3)}, inside which the limit is proved for every point checked.`;

  cloth.addEventListener("click", (e) => {
    const box = cloth.getBoundingClientRect();
    const col = Math.min(hd.PIN_LATTICE - 1, Math.max(0, Math.floor(((e.clientX - box.left) / box.width) * hd.PIN_LATTICE)));
    const row = Math.min(hd.PIN_LATTICE - 1, Math.max(0, Math.floor(((e.clientY - box.top) / box.height) * hd.PIN_LATTICE)));
    // A click near a raised heddle lowers it.
    const near = loom.pins.find((p) => Math.abs((p % hd.PIN_LATTICE) - col) <= 1 && Math.abs(Math.floor(p / hd.PIN_LATTICE) - row) <= 1);
    const pins = near !== undefined ? loom.pins.filter((p) => p !== near) : [...loom.pins, row * hd.PIN_LATTICE + col];
    if (pins.length > MAX_PINS) return;
    loom.setPins(pins);       // the loom re-threads around the raised heddles
    afterFellChange();
  });
  $("clear-pins").addEventListener("click", () => {
    loom.setPins([]);
    afterFellChange();
  });
  $("rest").addEventListener("click", () => {
    for (const n of hd.TREADLE_NAMES) treadling[n] = 0;
    shaftTravel = {};
    hidden = null;
    invalidate();
  });
  $("hide").addEventListener("click", () => {
    for (const n of hd.TREADLE_NAMES) treadling[n] = 0;
    shaftTravel = {};
    const known = hd.grid(4), elsewhere = hd.grid(24);
    hidden = hd.hiddenMove(loom.fell.w, known, elsewhere, 0.6, 40);
    const cand = hd.addScaled(loom.fell.w, loom.shed.project(hidden), 1.0);
    const seen = hd.behaviourChange(loom.fell.w, cand, known);
    const between = hd.change(loom.fell.w, cand, elsewhere).reduce((a, b) => Math.max(a, b), 0);
    showLamp({ kind: "none", text: `<strong>A move built to hide.</strong> It was chosen to change nothing, to first order, at 16 probes it knows about (the squares). At those probes the outputs move by ${fmt(seen)}. Between them, one point moves by ${fmt(between)}. Beat it in and see what probes it has not seen make of it.` });
    invalidate();
  });
  holdable($("beat"), () => HOLD_MS[pending?.a.zone] ?? 0, (ms) => beat(ms >= HOLD_MS.knot ? "knot" : ms >= HOLD_MS.shared ? "hold" : "release"));
  const un = $("unpick");
  un.innerHTML = "<span></span>";
  un.className = "beat";
  holdable(un, () => HOLD_MS.shared, () => {
    if (!selectedRoot) return;
    const ev = loom.unpick(selectedRoot);
    selectedRoot = null;
    lastEvent = null;
    afterFellChange();
    renderPicks();
    showLamp(ev);
  });
  $("seed-prev").addEventListener("click", () => newLoom(Math.max(1, loom.seed - 1), loom.shafts));
  $("seed-next").addEventListener("click", () => newLoom(loom.seed + 1, loom.shafts));
  document.querySelectorAll("[data-shafts]").forEach((b) => b.addEventListener("click", () => {
    loom.setShafts(Number(b.dataset.shafts));
    shaftTravel = {};
    buildThreading();
    afterFellChange();
  }));
  for (const id of ["show-focus", "show-probes"]) $(id).addEventListener("change", invalidate);
  $("copy-draft").addEventListener("click", async () => {
    const text = JSON.stringify(loom.exportDraft());
    const out = $("draft-out");
    out.value = text;
    try {
      await navigator.clipboard.writeText(text);
      $("copy-note").value = `copied, ${loom.events.length} events`;
    } catch {
      out.focus();
      out.select();
      $("copy-note").value = "selected: copy it from the box";
    }
  });
  new ResizeObserver(invalidate).observe(cloth);
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", invalidate);
  new MutationObserver(invalidate).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  // A handle for the curious and for tests.
  window.heddle = { hd, get loom() { return loom; }, get pending() { return pending; }, get spec() { return spec; }, beat };
  requestAnimationFrame(frame);
}

start();
