/**
 * Heddle prototype: the steering instrument's mathematics, for the browser and for Node.
 *
 * A line-by-line mirror of `heddle.py` in this folder, which is the reference. The two are
 * pinned together by `vectors.json` (written by `make_vectors.py`, read by `test_heddle.mjs`).
 * See `README.md` here and the design note `notes/heddle-steering-instrument.md`.
 *
 * Weights are one Float64Array of length P in the order W1, b1, W2, b2, W3, b3 (row-major),
 * the order of `flatten` in the reference. No dependency beyond the vendored weft gate.
 */
import { verifyWeightUpdateSafety } from "./vendor/invariant-gate.js";

export const SCHEMA = "heddle/1";
export const F = 8;
export const H = 16;
export const M = 3;
export const TENSOR_NAMES = ["W1", "b1", "W2", "b2", "W3", "b3"];
export const SHAPES = { W1: [H, F], b1: [H], W2: [H, H], b2: [H], W3: [M, H], b3: [M] };
export const OFFSETS = (() => {
  const o = {};
  let at = 0;
  for (const name of TENSOR_NAMES) {
    const size = SHAPES[name].reduce((a, b) => a * b, 1);
    o[name] = [at, at + size];
    at += size;
  }
  return o;
})();
export const P = OFFSETS.b3[1]; // 467
export const INIT_SCALE = { W1: 1.1, b1: 0.6, W2: 0.9, b2: 0.3, W3: 0.9, b3: 0.2 };
export const GAMMA = 1.0;
export const FIT_GRID = 10;
export const PIN_LATTICE = 64;
export const DISPUTE_GRID = 96;
export const DISPUTE_REFINE = 4;
export const DISPUTE_STEPS = 24;
export const TREADLE_NAMES = ["warm", "light", "tilt", "contrast", "check"];
const CBC_DOMAIN = "WEFT-CBC-V1:";
const DOMAIN = "WEFT-HEDDLE-V1:";
const TWO_PI = 2.0 * Math.PI;

// ---------------------------------------------------------------------------------------
// Deterministic numbers
// ---------------------------------------------------------------------------------------

/** mulberry32: integer arithmetic only, so every draw matches the Python reference bit for bit. */
export function mulberry32(seed) {
  let a = seed >>> 0;
  return function draw() {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Weights uniform in [-a, a] per tensor, drawn in tensor order. */
export function initHost(seed) {
  const draw = mulberry32(seed);
  const w = new Float64Array(P);
  for (const name of TENSOR_NAMES) {
    const [lo, hi] = OFFSETS[name];
    const a = INIT_SCALE[name];
    for (let i = lo; i < hi; i++) w[i] = (2.0 * draw() - 1.0) * a;
  }
  return w;
}

// ---------------------------------------------------------------------------------------
// Inputs
// ---------------------------------------------------------------------------------------

/** Cell centres of an n x n lattice as a flat [u0, v0, u1, v1, ...]; index = row * n + column. */
export function grid(n) {
  const pts = new Float64Array(n * n * 2);
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      pts[2 * (r * n + c)] = (c + 0.5) / n;
      pts[2 * (r * n + c) + 1] = (r + 0.5) / n;
    }
  }
  return pts;
}

/** Feature vectors, flat (n * F), of points given flat as [u, v, ...]. */
export function features(pts) {
  const n = pts.length / 2;
  const x = new Float64Array(n * F);
  for (let i = 0; i < n; i++) {
    const u = pts[2 * i];
    const v = pts[2 * i + 1];
    const o = i * F;
    x[o] = 2.0 * u - 1.0;
    x[o + 1] = 2.0 * v - 1.0;
    x[o + 2] = Math.sin(TWO_PI * u);
    x[o + 3] = Math.cos(TWO_PI * u);
    x[o + 4] = Math.sin(TWO_PI * v);
    x[o + 5] = Math.cos(TWO_PI * v);
    x[o + 6] = Math.sin(TWO_PI * (u + v));
    x[o + 7] = Math.sin(TWO_PI * (u - v));
  }
  return x;
}

/** Sorted, de-duplicated pins (integer cells of the pin lattice). */
export function normalisePins(pins) {
  const out = Array.from(new Set(Array.from(pins, (p) => p | 0))).sort((a, b) => a - b);
  for (const p of out) if (p < 0 || p >= PIN_LATTICE * PIN_LATTICE) throw new Error("pin outside the lattice");
  return out;
}

export function pinPoints(pins) {
  const list = normalisePins(pins);
  const pts = new Float64Array(list.length * 2);
  list.forEach((p, i) => {
    const row = Math.floor(p / PIN_LATTICE);
    const col = p % PIN_LATTICE;
    pts[2 * i] = (col + 0.5) / PIN_LATTICE;
    pts[2 * i + 1] = (row + 0.5) / PIN_LATTICE;
  });
  return pts;
}

// ---------------------------------------------------------------------------------------
// The host
// ---------------------------------------------------------------------------------------

/**
 * Outputs for precomputed features `x` (n * F), written into `out` (n * M). The hot path of
 * the instrument: no allocation, so a picture can be drawn every frame.
 */
export function forwardFeatures(w, x, out, h1buf, h2buf) {
  const n = x.length / F;
  const y = out ?? new Float64Array(n * M);
  const h1 = h1buf ?? new Float64Array(H);
  const h2 = h2buf ?? new Float64Array(H);
  const oW1 = OFFSETS.W1[0], ob1 = OFFSETS.b1[0], oW2 = OFFSETS.W2[0], ob2 = OFFSETS.b2[0];
  const oW3 = OFFSETS.W3[0], ob3 = OFFSETS.b3[0];
  for (let i = 0; i < n; i++) {
    const xo = i * F;
    for (let j = 0; j < H; j++) {
      let a = w[ob1 + j];
      const wo = oW1 + j * F;
      for (let f = 0; f < F; f++) a += w[wo + f] * x[xo + f];
      h1[j] = Math.tanh(a);
    }
    for (let j = 0; j < H; j++) {
      let a = w[ob2 + j];
      const wo = oW2 + j * H;
      for (let k = 0; k < H; k++) a += w[wo + k] * h1[k];
      h2[j] = Math.tanh(a);
    }
    for (let c = 0; c < M; c++) {
      let a = w[ob3 + c];
      const wo = oW3 + c * H;
      for (let j = 0; j < H; j++) a += w[wo + j] * h2[j];
      y[i * M + c] = a;
    }
  }
  return y;
}

export function forward(w, pts) {
  return forwardFeatures(w, features(pts));
}

/** Derivatives of every output on every input with respect to every weight: (n * M) x P, row-major. */
export function jacobian(w, pts) {
  const x = features(pts);
  const n = pts.length / 2;
  const J = new Float64Array(n * M * P);
  const h1 = new Float64Array(H), h2 = new Float64Array(H);
  const d1 = new Float64Array(H), d2 = new Float64Array(H);
  const oW1 = OFFSETS.W1[0], ob1 = OFFSETS.b1[0], oW2 = OFFSETS.W2[0], ob2 = OFFSETS.b2[0];
  const oW3 = OFFSETS.W3[0], ob3 = OFFSETS.b3[0];
  for (let i = 0; i < n; i++) {
    const xo = i * F;
    for (let j = 0; j < H; j++) {
      let a = w[ob1 + j];
      for (let f = 0; f < F; f++) a += w[oW1 + j * F + f] * x[xo + f];
      h1[j] = Math.tanh(a);
    }
    for (let j = 0; j < H; j++) {
      let a = w[ob2 + j];
      for (let k = 0; k < H; k++) a += w[oW2 + j * H + k] * h1[k];
      h2[j] = Math.tanh(a);
    }
    for (let c = 0; c < M; c++) {
      const row = (i * M + c) * P;
      for (let j = 0; j < H; j++) d2[j] = w[oW3 + c * H + j] * (1.0 - h2[j] * h2[j]);
      for (let k = 0; k < H; k++) {
        let s = 0.0;
        for (let j = 0; j < H; j++) s += d2[j] * w[oW2 + j * H + k];
        d1[k] = s * (1.0 - h1[k] * h1[k]);
      }
      for (let k = 0; k < H; k++) {
        for (let f = 0; f < F; f++) J[row + oW1 + k * F + f] = d1[k] * x[xo + f];
        J[row + ob1 + k] = d1[k];
      }
      for (let j = 0; j < H; j++) {
        for (let k = 0; k < H; k++) J[row + oW2 + j * H + k] = d2[j] * h1[k];
        J[row + ob2 + j] = d2[j];
      }
      for (let j = 0; j < H; j++) J[row + oW3 + c * H + j] = h2[j];
      J[row + ob3 + c] = 1.0;
    }
  }
  return J;
}

/** Per-input change: root mean square over the outputs of f1 - f0. */
export function change(w0, w1, pts) {
  const x = features(pts);
  const y0 = forwardFeatures(w0, x);
  const y1 = forwardFeatures(w1, x);
  const n = pts.length / 2;
  const out = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    let s = 0.0;
    for (let c = 0; c < M; c++) {
      const d = y1[i * M + c] - y0[i * M + c];
      s += d * d;
    }
    out[i] = Math.sqrt(s / M);
  }
  return out;
}

/** D_X of the calibration theory: root mean square of all output differences on the inputs. */
export function behaviourChange(w0, w1, pts) {
  const x = features(pts);
  const y0 = forwardFeatures(w0, x);
  const y1 = forwardFeatures(w1, x);
  let s = 0.0;
  for (let i = 0; i < y0.length; i++) {
    const d = y1[i] - y0[i];
    s += d * d;
  }
  return Math.sqrt(s / y0.length);
}

// ---------------------------------------------------------------------------------------
// Small linear algebra
// ---------------------------------------------------------------------------------------

export function dot(a, b) {
  let s = 0.0;
  for (let i = 0; i < a.length; i++) s += a[i] * b[i];
  return s;
}

export function norm(a) {
  return Math.sqrt(dot(a, a));
}

export function addScaled(a, b, s) {
  const out = new Float64Array(a.length);
  for (let i = 0; i < a.length; i++) out[i] = a[i] + s * b[i];
  return out;
}

/** y = A v for a row-major (rows x cols) matrix. */
export function matVec(A, rows, cols, v, out) {
  const y = out ?? new Float64Array(rows);
  for (let r = 0; r < rows; r++) {
    let s = 0.0;
    const o = r * cols;
    for (let c = 0; c < cols; c++) s += A[o + c] * v[c];
    y[r] = s;
  }
  return y;
}

/** y = A' z for a row-major (rows x cols) matrix. */
export function matTVec(A, rows, cols, z, out) {
  const y = out ?? new Float64Array(cols);
  y.fill(0.0);
  for (let r = 0; r < rows; r++) {
    const s = z[r];
    if (s === 0.0) continue;
    const o = r * cols;
    for (let c = 0; c < cols; c++) y[c] += s * A[o + c];
  }
  return y;
}

/**
 * Eigen-decomposition of a small symmetric matrix by cyclic Jacobi rotations.
 * `S` is row-major (n x n) and is not changed. Returns eigenvalues in descending order and
 * the matching eigenvectors as the rows of `vectors`.
 */
export function symmetricEigen(S, n) {
  const A = Float64Array.from(S);
  const V = new Float64Array(n * n);
  for (let i = 0; i < n; i++) V[i * n + i] = 1.0;
  for (let sweep = 0; sweep < 60; sweep++) {
    let off = 0.0;
    for (let p = 0; p < n; p++) for (let q = p + 1; q < n; q++) off += A[p * n + q] * A[p * n + q];
    let diag = 0.0;
    for (let p = 0; p < n; p++) diag += A[p * n + p] * A[p * n + p];
    if (off <= 1e-30 * (diag + 1e-300)) break;
    for (let p = 0; p < n; p++) {
      for (let q = p + 1; q < n; q++) {
        const apq = A[p * n + q];
        if (Math.abs(apq) < 1e-300) continue;
        const theta = (A[q * n + q] - A[p * n + p]) / (2.0 * apq);
        const t = Math.sign(theta || 1.0) / (Math.abs(theta) + Math.sqrt(theta * theta + 1.0));
        const c = 1.0 / Math.sqrt(t * t + 1.0);
        const s = t * c;
        for (let k = 0; k < n; k++) {
          const akp = A[k * n + p], akq = A[k * n + q];
          A[k * n + p] = c * akp - s * akq;
          A[k * n + q] = s * akp + c * akq;
        }
        for (let k = 0; k < n; k++) {
          const apk = A[p * n + k], aqk = A[q * n + k];
          A[p * n + k] = c * apk - s * aqk;
          A[q * n + k] = s * apk + c * aqk;
        }
        for (let k = 0; k < n; k++) {
          const vkp = V[k * n + p], vkq = V[k * n + q];
          V[k * n + p] = c * vkp - s * vkq;
          V[k * n + q] = s * vkp + c * vkq;
        }
      }
    }
  }
  const order = Array.from({ length: n }, (_, i) => i).sort((a, b) => A[b * n + b] - A[a * n + a]);
  const values = new Float64Array(n);
  const vectors = new Float64Array(n * n);
  order.forEach((src, dst) => {
    values[dst] = A[src * n + src];
    for (let k = 0; k < n; k++) vectors[dst * n + k] = V[k * n + src];
  });
  return { values, vectors };
}

/** Largest singular value of a row-major (rows x cols) matrix, from the eigenvalues of A A'. */
export function largestSingularValue(A, rows, cols) {
  const S = new Float64Array(rows * rows);
  for (let i = 0; i < rows; i++) {
    for (let j = i; j < rows; j++) {
      let s = 0.0;
      for (let k = 0; k < cols; k++) s += A[i * cols + k] * A[j * cols + k];
      S[i * rows + j] = s;
      S[j * rows + i] = s;
    }
  }
  return Math.sqrt(Math.max(0.0, symmetricEigen(S, rows).values[0]));
}

/**
 * Orthonormal rows spanning the rows of A (rows x cols), by modified Gram-Schmidt run twice.
 * A row is dropped when what is left of it is below rtol times its own length. Returns an
 * array of Float64Array rows. The same algorithm as `row_space_basis` in the reference.
 */
export function rowSpaceBasis(A, rows, cols, rtol = 1e-10) {
  const basis = [];
  for (let r = 0; r < rows; r++) {
    const v = A.slice(r * cols, (r + 1) * cols);
    const scale = norm(v);
    if (scale === 0.0) continue;
    for (let pass = 0; pass < 2; pass++) {
      for (const q of basis) {
        const s = dot(q, v);
        for (let c = 0; c < cols; c++) v[c] -= s * q[c];
      }
    }
    const nv = norm(v);
    if (nv > rtol * scale) {
      for (let c = 0; c < cols; c++) v[c] /= nv;
      basis.push(v);
    }
  }
  return basis;
}

function orthonormaliseRows(vectors) {
  const kept = [];
  for (const v of vectors) {
    for (let pass = 0; pass < 2; pass++) {
      for (const q of kept) {
        const s = dot(q, v);
        for (let c = 0; c < v.length; c++) v[c] -= s * q[c];
      }
    }
    const nv = norm(v);
    if (nv > 1e-14) {
      for (let c = 0; c < v.length; c++) v[c] /= nv;
      kept.push(v);
    }
  }
  return kept;
}

// ---------------------------------------------------------------------------------------
// Shafts
// ---------------------------------------------------------------------------------------

/**
 * The linearisation of the host at `w` on the inputs `pts`: the first `shafts` eigenpairs of
 * G = J'J/(n m), by block power iteration on the Gram matrix J J' with a Rayleigh-Ritz step.
 * The reference takes an exact SVD; the test checks that the eigenvalues agree.
 *
 *   lam[i]   eigenvalue of shaft i
 *   V[i]     the shaft: a unit direction in weight space (largest entry positive)
 *   U[i]     the unit-length output direction it makes; U[i] * sqrt(rows) is its picture
 *
 * `warm` may be a previous threading: its shafts start the iteration, so re-threading after a
 * small move takes few iterations.
 *
 * `basis` may hold the orthonormal rows of a shed (raised heddles). The loom is then threaded
 * around the pins: the shafts are the eigen-directions of G restricted to the shed, so every
 * shaft already leaves the pinned inputs alone to first order. The returned `J` stays the
 * full Jacobian; for a move inside the shed the two agree.
 */
export function thread(w, pts, shafts, { iterations = 200, oversample = 8, warm = null, basis = null } = {}) {
  const full = jacobian(w, pts);
  const rows = (pts.length / 2) * M;
  let J = full;
  if (basis && basis.length) {
    J = Float64Array.from(full);
    for (let r = 0; r < rows; r++) {
      const o = r * P;
      for (const q of basis) {
        let s = 0.0;
        for (let t = 0; t < P; t++) s += full[o + t] * q[t];
        for (let t = 0; t < P; t++) J[o + t] -= s * q[t];
      }
    }
  }
  // The Gram matrix J J' (rows x rows). Its eigenvectors are the output directions u_i, and
  // it is smaller than G whenever there are fewer output rows than weights.
  const gram = new Float64Array(rows * rows);
  for (let i = 0; i < rows; i++) {
    const oi = i * P;
    for (let j = i; j < rows; j++) {
      const oj = j * P;
      let s = 0.0;
      for (let t = 0; t < P; t++) s += J[oi + t] * J[oj + t];
      gram[i * rows + j] = s;
      gram[j * rows + i] = s;
    }
  }
  const block = Math.min(shafts + oversample, rows);
  let Z = [];
  if (warm && warm.block && warm.block.length === block && warm.rows === rows) {
    Z = warm.block.map((z) => Float64Array.from(z));
  } else {
    const draw = mulberry32(0x5eed);
    for (let k = 0; k < block; k++) {
      const z = new Float64Array(rows);
      for (let i = 0; i < rows; i++) z[i] = 2.0 * draw() - 1.0;
      Z.push(z);
    }
  }
  Z = orthonormaliseRows(Z);
  for (let it = 0; it < iterations; it++) Z = orthonormaliseRows(Z.map((z) => matVec(gram, rows, rows, z)));
  // Rayleigh-Ritz: the small matrix of the Gram matrix in the block, then rotate the block
  // onto its eigenvectors.
  const k = Z.length;
  const GZ = Z.map((z) => matVec(gram, rows, rows, z));
  const S = new Float64Array(k * k);
  for (let i = 0; i < k; i++) {
    for (let j = i; j < k; j++) {
      const s = dot(Z[i], GZ[j]);
      S[i * k + j] = s;
      S[j * k + i] = s;
    }
  }
  const eig = symmetricEigen(S, k);
  const rotated = [];
  for (let i = 0; i < k; i++) {
    const u = new Float64Array(rows);
    for (let j = 0; j < k; j++) {
      const c = eig.vectors[i * k + j];
      const src = Z[j];
      for (let t = 0; t < rows; t++) u[t] += c * src[t];
    }
    rotated.push(u);
  }
  const lam = [];
  const Vout = [];
  const Uout = [];
  for (let i = 0; i < Math.min(shafts, k); i++) {
    const u = rotated[i];
    const v = matTVec(J, rows, P, u);
    const s = norm(v); // the singular value: J'u = s v
    let big = 0;
    for (let t = 1; t < P; t++) if (Math.abs(v[t]) > Math.abs(v[big])) big = t;
    const sign = v[big] < 0 ? -1.0 : 1.0;
    for (let t = 0; t < P; t++) v[t] = (sign * v[t]) / (s || 1.0);
    if (sign < 0) for (let t = 0; t < rows; t++) u[t] = -u[t];
    lam.push((s * s) / rows);
    Vout.push(v);
    Uout.push(u);
  }
  return { w: Float64Array.from(w), pts, rows, J: full, lam, V: Vout, U: Uout, block: rotated };
}

/** First-order behaviour change sqrt(d'Gd) of a move on a threading's inputs. */
export function predictedChange(threading, d) {
  const y = matVec(threading.J, threading.rows, P, d);
  return Math.sqrt(dot(y, y) / threading.rows);
}

/** First-order change of the worst single input: the largest per-input root mean square of J d. */
export function predictedWorst(threading, d) {
  const y = matVec(threading.J, threading.rows, P, d);
  let worst = 0.0;
  for (let i = 0; i < threading.rows / M; i++) {
    let s = 0.0;
    for (let c = 0; c < M; c++) s += y[i * M + c] * y[i * M + c];
    worst = Math.max(worst, Math.sqrt(s / M));
  }
  return worst;
}

/** The move along shaft i whose first-order behaviour change is |travel|. */
export function shaftMove(threading, i, travel) {
  const d = new Float64Array(P);
  const s = travel / Math.sqrt(threading.lam[i]);
  for (let t = 0; t < P; t++) d[t] = s * threading.V[i][t];
  return d;
}

// ---------------------------------------------------------------------------------------
// Treadles and the tie-up
// ---------------------------------------------------------------------------------------

function unitRms(c) {
  const r = Math.sqrt(dot(c, c) / c.length);
  if (r < 1e-300) return new Float64Array(c.length);
  return c.map((v) => v / r);
}

/** The output pattern a treadle asks for on the inputs `pts`, flat (n * M), unit root mean square. */
export function treadlePattern(name, pts, y = null) {
  const n = pts.length / 2;
  const c = new Float64Array(n * M);
  let mean = 0.0;
  if (name === "contrast") {
    if (!y) throw new Error("the contrast treadle needs the current outputs");
    for (let i = 0; i < n; i++) mean += (y[i * M] + y[i * M + 1] + y[i * M + 2]) / M;
    mean /= n;
  }
  for (let i = 0; i < n; i++) {
    const u = pts[2 * i], v = pts[2 * i + 1];
    let per;
    if (name === "warm") per = [1.0, 0.0, -1.0];
    else if (name === "light") per = [1.0, 1.0, 1.0];
    else if (name === "tilt") per = [2.0 * u - 1.0, 2.0 * u - 1.0, 2.0 * u - 1.0];
    else if (name === "contrast") {
      const light = (y[i * M] + y[i * M + 1] + y[i * M + 2]) / M;
      per = [light - mean, light - mean, light - mean];
    } else if (name === "check") {
      const s = Math.sin(2.0 * TWO_PI * u) * Math.sin(2.0 * TWO_PI * v);
      per = [s, s, s];
    } else throw new Error(`unknown treadle ${name}`);
    for (let k = 0; k < M; k++) c[i * M + k] = per[k];
  }
  return unitRms(c);
}

/**
 * Treadles tied to the shafts of a threading. For a pattern c, alpha[i] = u_i'c / sqrt(rows)
 * and the move for travel t is t * sum_i alpha[i] v_i / sqrt(lam[i]). `realizable` is the
 * share of the pattern the shafts can carry: the first-order gain along c per unit of travel.
 */
export function tieUp(threading, patterns) {
  const root = Math.sqrt(threading.rows);
  const K = threading.V.length;
  const alpha = {}, realizable = {}, unitMove = {};
  for (const [name, c] of Object.entries(patterns)) {
    const a = new Float64Array(K);
    const d = new Float64Array(P);
    let share = 0.0;
    for (let i = 0; i < K; i++) {
      a[i] = dot(threading.U[i], c) / root;
      share += a[i] * a[i];
      const s = a[i] / Math.sqrt(threading.lam[i]);
      for (let t = 0; t < P; t++) d[t] += s * threading.V[i][t];
    }
    alpha[name] = a;
    realizable[name] = share;
    unitMove[name] = d;
  }
  return { K, names: Object.keys(patterns), patterns, alpha, realizable, unitMove };
}

/** How much of `pattern` an output change contains: <dy, c> / <c, c>. */
export function gainAlong(dy, pattern) {
  return dot(dy, pattern) / dot(pattern, pattern);
}

// ---------------------------------------------------------------------------------------
// Pins and the shed
// ---------------------------------------------------------------------------------------

/** The moves that leave the pinned inputs alone to first order: project(d) removes the pins' row space. */
export function shed(w, pins) {
  const list = normalisePins(pins);
  const basis = list.length ? rowSpaceBasis(jacobian(w, pinPoints(list)), list.length * M, P) : [];
  return {
    pins: list,
    Q: basis,
    openDimensions: P - basis.length,
    project(d) {
      const out = Float64Array.from(d);
      for (const q of basis) {
        const s = dot(q, d);
        for (let t = 0; t < P; t++) out[t] -= s * q[t];
      }
      return out;
    },
  };
}

// ---------------------------------------------------------------------------------------
// The selvedge
// ---------------------------------------------------------------------------------------

export { verifyWeightUpdateSafety };

/**
 * Theorem 1 of the calibration theory with gamma = 1: for every move of length at most
 * `radius` and every input, the output change (Euclidean length) is at most the returned
 * bound. One value per input.
 */
export function certifiedBound(w0, pts, radius) {
  const x = features(pts);
  const n = pts.length / 2;
  const s2 = largestSingularValue(w0.subarray(OFFSETS.W2[0], OFFSETS.W2[1]), H, H);
  const s3 = largestSingularValue(w0.subarray(OFFSETS.W3[0], OFFSETS.W3[1]), M, H);
  const out = new Float64Array(n);
  const h1 = new Float64Array(H), h2 = new Float64Array(H);
  const oW1 = OFFSETS.W1[0], ob1 = OFFSETS.b1[0], oW2 = OFFSETS.W2[0], ob2 = OFFSETS.b2[0];
  const g = GAMMA, r = radius;
  for (let i = 0; i < n; i++) {
    let xx = 0.0, hh1 = 0.0, hh2 = 0.0;
    for (let f = 0; f < F; f++) xx += x[i * F + f] * x[i * F + f];
    for (let j = 0; j < H; j++) {
      let a = w0[ob1 + j];
      for (let f = 0; f < F; f++) a += w0[oW1 + j * F + f] * x[i * F + f];
      h1[j] = Math.tanh(a);
      hh1 += h1[j] * h1[j];
    }
    for (let j = 0; j < H; j++) {
      let a = w0[ob2 + j];
      for (let k = 0; k < H; k++) a += w0[oW2 + j * H + k] * h1[k];
      h2[j] = Math.tanh(a);
      hh2 += h2[j] * h2[j];
    }
    const a0 = Math.sqrt(xx + 1.0), a1 = Math.sqrt(hh1 + 1.0), a2 = Math.sqrt(hh2 + 1.0);
    const c = Math.sqrt((g * g * s3 * s2 * a0) ** 2 + (g * s3 * a1) ** 2 + a2 ** 2);
    const q = (g * g * (s2 + s3) * a0 + g * a1) / 2.0;
    const k = (g * g * a0) / (3.0 * Math.sqrt(3.0));
    out[i] = r * c + r * r * q + r * r * r * k;
  }
  return out;
}

/**
 * The largest radius at which the proved bound keeps every input of `pts` within `tau`
 * (per-input root mean square over the outputs), by bisection. Read on these inputs only.
 */
export function certifiedRadius(w0, pts, tau) {
  const limit = tau * Math.sqrt(M);
  const worst = (r) => certifiedBound(w0, pts, r).reduce((a, b) => Math.max(a, b), 0.0);
  let lo = 0.0, hi = 1.0;
  while (worst(hi) < limit && hi < 1e6) hi *= 2.0;
  for (let i = 0; i < 60; i++) {
    const mid = 0.5 * (lo + hi);
    if (worst(mid) <= limit) lo = mid;
    else hi = mid;
  }
  return lo;
}

// ---------------------------------------------------------------------------------------
// SHA-256 and commitments
// ---------------------------------------------------------------------------------------

const K256 = new Uint32Array([
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]);

/** SHA-256 of a Uint8Array, as a Uint8Array. Synchronous, so a pick can be rooted inside a frame. */
export function sha256(bytes) {
  const h = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
  const len = bytes.length;
  const total = ((len + 9 + 63) >> 6) << 6;
  const m = new Uint8Array(total);
  m.set(bytes);
  m[len] = 0x80;
  const view = new DataView(m.buffer);
  view.setUint32(total - 8, Math.floor(len / 0x20000000), false);
  view.setUint32(total - 4, (len << 3) >>> 0, false);
  const w = new Uint32Array(64);
  for (let o = 0; o < total; o += 64) {
    for (let i = 0; i < 16; i++) w[i] = view.getUint32(o + 4 * i, false);
    for (let i = 16; i < 64; i++) {
      const a = w[i - 15], b = w[i - 2];
      const s0 = ((a >>> 7) | (a << 25)) ^ ((a >>> 18) | (a << 14)) ^ (a >>> 3);
      const s1 = ((b >>> 17) | (b << 15)) ^ ((b >>> 19) | (b << 13)) ^ (b >>> 10);
      w[i] = (w[i - 16] + s0 + w[i - 7] + s1) >>> 0;
    }
    let [a, b, c, d, e, f, g, hh] = h;
    for (let i = 0; i < 64; i++) {
      const S1 = ((e >>> 6) | (e << 26)) ^ ((e >>> 11) | (e << 21)) ^ ((e >>> 25) | (e << 7));
      const ch = (e & f) ^ (~e & g);
      const t1 = (hh + S1 + ch + K256[i] + w[i]) >>> 0;
      const S0 = ((a >>> 2) | (a << 30)) ^ ((a >>> 13) | (a << 19)) ^ ((a >>> 22) | (a << 10));
      const maj = (a & b) ^ (a & c) ^ (b & c);
      const t2 = (S0 + maj) >>> 0;
      hh = g; g = f; f = e; e = (d + t1) >>> 0; d = c; c = b; b = a; a = (t1 + t2) >>> 0;
    }
    h[0] = (h[0] + a) >>> 0; h[1] = (h[1] + b) >>> 0; h[2] = (h[2] + c) >>> 0; h[3] = (h[3] + d) >>> 0;
    h[4] = (h[4] + e) >>> 0; h[5] = (h[5] + f) >>> 0; h[6] = (h[6] + g) >>> 0; h[7] = (h[7] + hh) >>> 0;
  }
  const out = new Uint8Array(32);
  const ov = new DataView(out.buffer);
  for (let i = 0; i < 8; i++) ov.setUint32(4 * i, h[i], false);
  return out;
}

const encoder = new TextEncoder();
const ascii = (s) => encoder.encode(s);

export function toHex(bytes) {
  let s = "";
  for (const b of bytes) s += b.toString(16).padStart(2, "0");
  return s;
}

function concatBytes(...parts) {
  const total = parts.reduce((n, p) => n + p.length, 0);
  const out = new Uint8Array(total);
  let at = 0;
  for (const p of parts) {
    out.set(p, at);
    at += p.length;
  }
  return out;
}

/** JSON with sorted keys and no spaces: the bytes Python's json.dumps(sort_keys=True, separators=(",", ":")) gives for strings, integers and lists. */
export function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${canonicalJson(value[k])}`).join(",")}}`;
  }
  if (typeof value === "number" && !Number.isInteger(value)) throw new Error("only integers and strings are hashed");
  return JSON.stringify(value);
}

/** Little-endian float64 bytes of a weight vector slice. */
function f64Bytes(values) {
  const out = new Uint8Array(values.length * 8);
  const view = new DataView(out.buffer);
  for (let i = 0; i < values.length; i++) view.setFloat64(8 * i, values[i], true);
  return out;
}

/** The weight root of committed-behaviour-change v1 (`cbc.py::weight_root`) for this host's six tensors. */
export function weightRoot(w) {
  const parts = [ascii(`${CBC_DOMAIN}root:`)];
  for (const name of [...TENSOR_NAMES].sort()) {
    const [lo, hi] = OFFSETS[name];
    const header = canonicalJson({ name, shape: SHAPES[name], dtype: "<f8" });
    const leaf = toHex(sha256(concatBytes(ascii(`${CBC_DOMAIN}leaf:`), ascii(header), ascii(":"), f64Bytes(w.subarray(lo, hi)))));
    parts.push(ascii(`${name}:${leaf};`));
  }
  return toHex(sha256(concatBytes(...parts)));
}

export function claimId(w0Root, w1Root, tau, pins) {
  const body = { schema: "heddle-claim/1", domain: "unit-square", w0_root: w0Root, w1_root: w1Root, tau: String(tau), pins: normalisePins(pins) };
  return toHex(sha256(ascii(`${DOMAIN}claim:${canonicalJson(body)}`)));
}

/** Probe inputs derived only after the candidate is committed (the probe order of CBC v1). */
export function freshProbes(w1Root, claim, n, testSet = "admission") {
  const seed = sha256(ascii(`${DOMAIN}probes:${testSet}:${w1Root}:${claim}`));
  const pts = new Float64Array(n * 2);
  const buf = new Uint8Array(36);
  buf.set(seed);
  const view = new DataView(buf.buffer);
  for (let i = 0; i < n; i++) {
    view.setUint32(32, i, false);
    const h = new DataView(sha256(buf).buffer);
    pts[2 * i] = h.getUint32(0, false) / 4294967296;
    pts[2 * i + 1] = h.getUint32(4, false) / 4294967296;
  }
  return pts;
}

/**
 * A bounded search for the one input that changes most: the dispute of CBC v1. Reads a whole
 * lattice, then climbs from the best cells with a shrinking step. A sampled reading.
 */
export function disputeSearch(w0, w1) {
  const pts = grid(DISPUTE_GRID);
  const ch = change(w0, w1, pts);
  let rows = ch.length;
  const order = Array.from(ch.keys()).sort((a, b) => ch[b] - ch[a] || a - b).slice(0, DISPUTE_REFINE);
  let bestVal = ch[order[0]];
  let bestPt = [pts[2 * order[0]], pts[2 * order[0] + 1]];
  const clip = (v) => Math.min(1.0, Math.max(0.0, v));
  for (const idx of order) {
    let p = [pts[2 * idx], pts[2 * idx + 1]];
    let val = ch[idx];
    let step = 0.5 / DISPUTE_GRID;
    for (let it = 0; it < DISPUTE_STEPS; it++) {
      const cand = new Float64Array([
        clip(p[0] + step), clip(p[1]), clip(p[0] - step), clip(p[1]),
        clip(p[0]), clip(p[1] + step), clip(p[0]), clip(p[1] - step),
      ]);
      const vals = change(w0, w1, cand);
      rows += 4;
      let j = 0;
      for (let k = 1; k < 4; k++) if (vals[k] > vals[j]) j = k;
      if (vals[j] > val) {
        p = [cand[2 * j], cand[2 * j + 1]];
        val = vals[j];
      } else step *= 0.5;
    }
    if (val > bestVal) {
      bestVal = val;
      bestPt = p;
    }
  }
  return { worst: bestVal, witness: bestPt, rows };
}

// ---------------------------------------------------------------------------------------
// The hidden move
// ---------------------------------------------------------------------------------------

/**
 * A move of length `radius` that the probes cannot see to first order and that changes as
 * much as it can elsewhere: power iteration on the elsewhere-Jacobian inside the null space
 * of the probes' Jacobian. Section 6 of the calibration theory, as a button.
 */
export function hiddenMove(w, probes, elsewhere, radius, iterations = 60) {
  const Q = rowSpaceBasis(jacobian(w, probes), (probes.length / 2) * M, P);
  const rowsE = (elsewhere.length / 2) * M;
  const Je = jacobian(w, elsewhere);
  const project = (v) => {
    for (const q of Q) {
      const s = dot(q, v);
      for (let t = 0; t < P; t++) v[t] -= s * q[t];
    }
    const nv = norm(v);
    for (let t = 0; t < P; t++) v[t] /= nv;
    return v;
  };
  const draw = mulberry32(20261117);
  let v = new Float64Array(P);
  for (let i = 0; i < P; i++) v[i] = 2.0 * draw() - 1.0;
  v = project(v);
  const z = new Float64Array(rowsE);
  for (let it = 0; it < iterations; it++) {
    matVec(Je, rowsE, P, v, z);
    v = project(matTVec(Je, rowsE, P, z));
  }
  let big = 0;
  for (let t = 1; t < P; t++) if (Math.abs(v[t]) > Math.abs(v[big])) big = t;
  const sign = v[big] < 0 ? -radius : radius;
  return v.map((x) => sign * x);
}

// ---------------------------------------------------------------------------------------
// The draft: a steering session as a record anyone can replay
// ---------------------------------------------------------------------------------------

const B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

function bytesToB64(bytes) {
  let s = "";
  for (let i = 0; i < bytes.length; i += 3) {
    const a = bytes[i], b = bytes[i + 1] ?? 0, c = bytes[i + 2] ?? 0;
    s += B64[a >> 2] + B64[((a & 3) << 4) | (b >> 4)];
    s += i + 1 < bytes.length ? B64[((b & 15) << 2) | (c >> 6)] : "=";
    s += i + 2 < bytes.length ? B64[c & 63] : "=";
  }
  return s;
}

export function moveToB64(d) {
  return bytesToB64(f64Bytes(d));
}

export function eventId(event) {
  const body = {};
  for (const k of ["seq", "kind", "prev", "parent_root", "root", "move_sha256", "pins", "gesture", "tau"]) {
    if (k in event) body[k] = event[k];
  }
  return toHex(sha256(ascii(`${DOMAIN}event:${canonicalJson(body)}`)));
}

/**
 * Autonomy zones, with the thresholds of the governor layer in the corpus's genesis dialogue:
 * tension below 0.3 the loom may weave on release, from 0.3 a deliberate hold is needed, and
 * from 0.7 a long one (the weaver's knot). Tension is a prediction, so it never refuses by
 * itself: weft's gate refuses, and a refuted claim snaps.
 */
export const ZONES = ["auto", "shared", "knot"];
export const GESTURES = ["release", "hold", "knot"];

export function zoneOf(tension) {
  if (tension < 0.3) return "auto";
  if (tension < 0.7) return "shared";
  return "knot";
}

/** Whether a gesture is deliberate enough for a zone. */
export function gestureSuffices(gesture, zone) {
  return GESTURES.indexOf(gesture) >= ZONES.indexOf(zone);
}

/**
 * One steering session. The loom holds a baseline, the lineage of fells, the pins, and the
 * events of the draft. Every pick goes through weft's gate against the baseline, is rooted,
 * and carries a claim that is checked on probes drawn after the root exists.
 */
export class Loom {
  constructor({ seed = 1, rInvariant = 2.0, budget = 24, cost = 1, tau = "0.5", shafts = 16, probes = 64 } = {}) {
    this.seed = seed;
    this.rInvariant = rInvariant;
    this.cost = cost;
    this.tau = String(tau);
    this.tauValue = Number(tau);
    this.shafts = shafts;
    this.probeCount = probes;
    this.base = initHost(seed);
    this.baseRoot = weightRoot(this.base);
    this.initialBudget = budget;
    this.lineage = [{ root: this.baseRoot, w: this.base, budget }];
    this.events = [];
    this.pins = [];
    this.fit = grid(FIT_GRID);
    this.threading = null;
    this.shed = null;
    this.rethread();
  }

  get fell() {
    return this.lineage[this.lineage.length - 1];
  }

  /** Linearise at the fell, around the raised heddles: shed, shafts, treadle patterns, tie-up. */
  rethread({ iterations } = {}) {
    const w = this.fell.w;
    this.shed = shed(w, this.pins);
    const warm = this.threading && this.threading.V.length === this.shafts ? this.threading : null;
    this.threading = thread(w, this.fit, this.shafts, { iterations: iterations ?? (warm ? 16 : 48), warm, basis: this.shed.Q });
    const y = forward(w, this.fit);
    this.outputs = y;
    const patterns = {};
    for (const name of TREADLE_NAMES) patterns[name] = treadlePattern(name, this.fit, y);
    this.tie = tieUp(this.threading, patterns);
    return this.threading;
  }

  setShafts(k) {
    this.shafts = k;
    this.threading = null;
    this.rethread();
  }

  /** Raise or lower heddles. The loom is re-threaded around them. */
  setPins(pins) {
    this.pins = normalisePins(pins);
    this.rethread({ iterations: 32 });
  }

  /** The move for treadle travels and shaft travels, passed through the shed. */
  moveFor(treadling = {}, shaftTravel = {}) {
    const d = new Float64Array(P);
    for (const [name, t] of Object.entries(treadling)) {
      if (!t) continue;
      const u = this.tie.unitMove[name];
      for (let i = 0; i < P; i++) d[i] += t * u[i];
    }
    for (const [i, t] of Object.entries(shaftTravel)) {
      if (!t) continue;
      const s = t / Math.sqrt(this.threading.lam[i]);
      const v = this.threading.V[i];
      for (let k = 0; k < P; k++) d[k] += s * v[k];
    }
    return this.shed.project(d);
  }

  /** Everything the weaver sees before beating a move in. Nothing is committed. */
  assess(d) {
    const fell = this.fell;
    const cand = addScaled(fell.w, d, 1.0);
    const gate = verifyWeightUpdateSafety(this.base, cand, this.rInvariant, fell.budget, this.cost);
    const predicted = predictedChange(this.threading, d);
    const predictedMax = predictedWorst(this.threading, d);
    const ball = gate.distance / this.rInvariant;
    const behaviour = predictedMax / this.tauValue;
    const tension = Math.max(Number.isFinite(ball) ? ball : Infinity, behaviour);
    return { cand, gate, predicted, predictedMax, ball, behaviour, tension, zone: gate.accepted ? zoneOf(tension) : "refused", length: norm(d) };
  }

  /**
   * Beat a move in. `gesture` records how the weaver committed: "release", "hold" or "knot".
   * `treadling` and `note` say what was pressed; they are kept as readings, not hashed.
   *
   *   { refused }  weft's gate said no. Nothing is recorded and no budget is spent.
   *   { needs }    the gesture was not deliberate enough for the pick's zone. Nothing happens.
   *   event        kind "pick": the gate accepted, and the bounded search found no input that
   *                changes by more than tau. The move becomes the fell. A sampled reading.
   *                kind "snap": the gate accepted, and one input refutes the claim. The fell
   *                does not move; the witness is kept as the reason; the budget is spent.
   */
  commit(d, gesture = "hold", treadling = {}, note = "") {
    const fell = this.fell;
    const a = this.assess(d);
    if (!a.gate.accepted) return { refused: a.gate };
    if (!gestureSuffices(gesture, a.zone)) return { needs: a.zone };
    const root = weightRoot(a.cand);
    const moveBytes = f64Bytes(d);
    const cid = claimId(fell.root, root, this.tau, this.pins);
    const probes = freshProbes(root, cid, this.probeCount);
    const realized = behaviourChange(fell.w, a.cand, probes);
    const dispute = disputeSearch(fell.w, a.cand);
    const refuted = dispute.worst > this.tauValue;
    let pinLeak = 0.0;
    if (this.pins.length) for (const c of change(fell.w, a.cand, pinPoints(this.pins))) pinLeak = Math.max(pinLeak, c);
    // `promised` is the first-order gain of this very move on the fit probes (so it already
    // counts the pins and the other treadles); `gain` is what the fresh probes measured.
    const delivered = {};
    const names = Object.keys(treadling).filter((k) => treadling[k]);
    if (names.length) {
      const x = features(probes);
      const y0 = forwardFeatures(fell.w, x);
      const y1 = forwardFeatures(a.cand, x);
      const dy = y1.map((v, i) => v - y0[i]);
      const first = matVec(this.threading.J, this.threading.rows, P, d);
      for (const name of names) {
        const gain = gainAlong(dy, treadlePattern(name, probes, y0));
        delivered[name] = { asked: treadling[name], promised: gainAlong(first, this.tie.patterns[name]), gain };
      }
    }
    const event = {
      seq: this.events.length + 1,
      kind: refuted ? "snap" : "pick",
      prev: this.events.length ? this.events[this.events.length - 1].id : "genesis",
      parent_root: fell.root,
      root,
      move_sha256: toHex(sha256(moveBytes)),
      move_b64: bytesToB64(moveBytes),
      pins: [...this.pins],
      gesture,
      tau: this.tau,
      gate: { accepted: true, distance: a.gate.distance, remaining_budget: a.gate.remainingBudget, reason: a.gate.reason },
      reading: { length: a.length, predicted: a.predicted, predicted_worst: a.predictedMax, tension: a.tension, zone: a.zone, pin_leak: pinLeak, treadling, delivered, note },
      claim: { id: cid, probes: this.probeCount, realized, worst: dispute.worst, witness: dispute.witness, rows: dispute.rows, refuted },
    };
    event.id = eventId(event);
    this.events.push(event);
    if (refuted) {
      // The thread snaps: the weights stay where they were, the attempt stays on the record.
      this.lineage.push({ root: fell.root, w: fell.w, budget: a.gate.remainingBudget });
    } else {
      this.lineage.push({ root, w: a.cand, budget: a.gate.remainingBudget });
      this.rethread();
    }
    return event;
  }

  /** Return to an earlier fell. The picks stay in the draft; the budget spent stays spent. */
  unpick(root) {
    let at = -1;
    for (let i = this.lineage.length - 1; i >= 0; i--) if (this.lineage[i].root === root) { at = i; break; }
    if (at < 0) throw new Error("that root was never the fell");
    const fell = this.fell;
    const event = {
      seq: this.events.length + 1,
      kind: "unpick",
      prev: this.events.length ? this.events[this.events.length - 1].id : "genesis",
      parent_root: fell.root,
      root,
      pins: [...this.pins],
      gesture: "hold",
      tau: this.tau,
    };
    event.id = eventId(event);
    this.events.push(event);
    this.lineage.push({ root, w: this.lineage[at].w, budget: fell.budget });
    this.rethread({ iterations: 48 });
    return event;
  }

  /** The draft: enough to rebuild every fell and re-check every verdict without this page. */
  exportDraft() {
    return {
      schema: "heddle-draft/1",
      host: { seed: this.seed, shape: { F, H, M }, w0_root: this.baseRoot },
      gate: { r_invariant: this.rInvariant, budget: this.initialBudget, cost: this.cost, tau: this.tau },
      events: this.events,
    };
  }
}
