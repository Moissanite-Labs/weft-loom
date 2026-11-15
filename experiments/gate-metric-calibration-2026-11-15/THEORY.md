# What a bound on weight distance can and cannot promise

15 November 2026. This note derives, from first principles, what the Weft gate `||W - W0|| <= R` says about behaviour. It was written before the confirmatory run. `PREREG.md` turns it into predictions. Marks: **[P]** proved in this note, **[K]** a known result used as stated, **[I]** inference.

## 1. Setting

A model computes `f(x, w)` from an input `x` and a weight vector `w` of length `P`. The baseline is `w0`, a candidate is `w`, and the move is `d = w - w0` with length `r = ||d||`.

The behaviour change on a set `X` of `n` inputs, each with `m` outputs, is the root mean square of the output differences:

```
D_X(d) = sqrt( sum over x in X of ||f(x, w0 + d) - f(x, w0)||^2 / (n m) )
```

The gate bounds `r`. The question is what that says about `D`.

## 2. Small moves: one matrix decides

[K] For a small move the output change is `J d`, where `J` is the matrix of derivatives of the outputs on `X` with respect to the weights. So

```
D_X(d)^2 = d' G d + (terms of third order),      G = J' J / (n m)
```

`G` is symmetric and has no negative eigenvalue. Four facts follow.

- **Worst case.** [P] Over all moves of length `r`, the largest first-order change is `r sqrt(lam_max)`, with `lam_max` the largest eigenvalue of `G`. It is reached along the top eigenvector.
- **Typical case.** [P] For a move in a uniformly random direction the mean of `d' G d` is `r^2 trace(G) / P`.
- **The gap between them.** [P] The ratio is `kappa = sqrt(lam_max P / trace(G))`. A radius set from typical moves is unsafe by that factor. A radius set from the worst case is that much too strict for typical moves.
- **Silent directions.** [P] `J` has at most `n m` independent rows, so at least `P - n m` directions of weight space change nothing on `X` to first order. This is the null space of `J`.

[I] So a ball in weight space is the wrong shape for a behaviour bound. Near `w0` the set of moves with a small behaviour change is the ellipsoid `d' G d <= tau^2`. It is long where the model does not care and short where it does.

## 3. Any move: a bound that is proved, and loose

**Theorem 1.** [P] Let `f(x, w) = W3 g(W2 g(W1 x + b1) + b2) + b3`, where `g` has slope at most `gamma` in absolute value. Let `h1 = g(W1 x + b1)` and `h2 = g(W2 h1 + b2)` at the baseline, and let `s2`, `s3` be the largest singular values of `W2`, `W3` at the baseline. Then for every move with `||d|| <= R` and every input `x`:

```
||f(x, w0 + d) - f(x, w0)|| <= R c(x) + R^2 q(x) + R^3 k(x)

A0 = sqrt(||x||^2 + 1),  A1 = sqrt(||h1||^2 + 1),  A2 = sqrt(||h2||^2 + 1)
c(x) = sqrt( (gamma^2 s3 s2 A0)^2 + (gamma s3 A1)^2 + A2^2 )
q(x) = ( gamma^2 (s2 + s3) A0 + gamma A1 ) / 2
k(x) = gamma^2 A0 / (3 sqrt(3))
```

Proof. Write `R1`, `R2`, `R3` for the lengths of the parts of `d` in layers 1, 2 and 3, biases included. Then `R1^2 + R2^2 + R3^2 <= R^2`.

Layer 1. The input to `g` moves by `dW1 x + db1`, of length at most `R1 A0` by the Cauchy-Schwarz inequality. So `e1 = ||h1' - h1|| <= gamma R1 A0`.

Layer 2. The input to `g` moves by `W2'(h1' - h1) + dW2 h1 + db2`. The largest singular value of `W2'` is at most `s2 + R2`. So `e2 = ||h2' - h2|| <= gamma ((s2 + R2) e1 + R2 A1)`.

Layer 3. The output moves by `W3'(h2' - h2) + dW3 h2 + db3`, so `e3 <= (s3 + R3) e2 + R3 A2`.

Multiply out. The terms linear in `R1`, `R2`, `R3` are `gamma^2 s3 s2 A0 R1 + gamma s3 A1 R2 + A2 R3`, at most `R c(x)` by Cauchy-Schwarz. Each product of two of them is at most `R^2 / 2`, which gives `R^2 q(x)`. The product of all three is at most `R^3 / (3 sqrt(3))`, which gives `R^3 k(x)`. End of proof.

**The slope bound.** [P] The E13 activation is `g(z) = z s(a z)` with `s` the logistic function and `a = 1.702`, made linear outside `|z| <= 20`. Its second derivative is `a s (1 - s)(2 + t (1 - 2s))` with `t = a z`. Since `s (1 - s) <= 1/4` and `|t| s (1 - s) <= |t| exp(-|t|) <= 1/e`, it is at most `1.702 (0.5 + 0.368) < 1.5` in absolute value. `calib.py` evaluates `g'` on a grid of step `1e-4` over `[-20, 20]` and adds `1.5` times half a step. Outside that range the slope lies in `[0, 1]`. The result is `gamma < 1.1`.

[I] The theorem is the statement the README sentence "bounds you can check" can honestly carry: inside radius `R`, no output moves by more than `B(x, R)`. It is loose, because it multiplies the largest gains of the layers. How loose is measured: the certified radius is compared with the radius at which a search finds a real violation.

[I] The bound grows like `R^3`. At the shipped radii of 10 and 120 it is far above the size of the outputs themselves, so there it says nothing.

## 4. Symmetry: far away and identical

[K] Reordering the hidden units of a layer, with their incoming and outgoing weights, changes the weight vector and not the function. For a net with independent random-like rows, the move has length close to `sqrt(2)` times the norm of the permuted weights.

[P] So no rule of the form "reject when `r` exceeds `R`" can be necessary for behaviour safety: for every `R` below that length there is a rejected move with `D = 0`. And by section 2 no such rule is sufficient unless `R <= tau / sqrt(lam_max)`.

[I] The matrix `G` of section 2 does not repair this. It is a local object. It predicts a large change for the permutation, which is a large move, and the true change is zero.

## 5. Probes: exact for the moves that did not see them

A behaviour check measures `D` on a finite probe set and compares it with a tolerance.

**Proposition 2.** [K] Fix the candidate first. Then draw `n` probe inputs independently from the input distribution. If the change is at most `t` on every probe, then with probability at least `1 - delta` the share of inputs with change above `t` is at most `ln(1 / delta) / n`.

Proof. If that share is `p`, all `n` probes miss it with probability `(1 - p)^n <= exp(-p n)`, which is at most `delta` when `p >= ln(1 / delta) / n`.

[P] The order matters. If the proposer can see the probes before fixing the candidate, the proposition gives nothing. Section 2 says why: there are at least `P - n m` directions the probes cannot see to first order, and the proposer can search inside them.

[I] So a probe check has two regimes. Against moves made without sight of the probes it should track held-out change closely, at any distance, symmetries and grafts included. Against a proposer who knows the probes it should fail by a large factor. Both are tested.

## 6. One subspace, two readings

Several Weft records use the null space of a set of "keep" inputs, with opposite trust.

- The null-space gate of weft issue 149 and the plasmid records E11, E12 and E13 treat it as the **safe** channel: an edit inside it leaves the kept behaviour alone.
- The E15 morphogenesis benchmark and the probe refresh of weft pull request 181 treat it as the **attack** channel: an edit inside it is invisible to the probes.

[P] Both are right, and section 2 says exactly when. Let `K` be the null space of `J` on the keep set.

1. On the keep inputs, a move in `K` of length `r` changes outputs only at second order, by about `c2 r^2`.
2. On any other input, the same move changes outputs at first order, by `||J_other d||`, which is not zero unless the keep set already determines that input's derivatives.

[I] So `K` is safe exactly as far as the keep set covers the inputs that matter, and it is the natural hiding place for anyone who knows the keep set. The difference between the two readings is who chose the direction and what they knew. The run measures both `c2` and the leak onto inputs outside the keep set.

## 7. What this predicts, in one table

| Kind of move | What limits its safe size | Expected safe size at tolerance `tau` |
|---|---|---|
| Worst case inside a ball | `lam_max` | `tau / sqrt(lam_max)` |
| Random direction | mean eigenvalue | `tau / sqrt(trace(G) / P)` |
| Inside the null space of the probes | leak onto other inputs, then curvature | larger again |
| Exact symmetry | nothing | any |
| One optimiser step | the learning rate | `lr sqrt(P)` for Adam's first step |

[I] If the first row is smaller than the last, then no radius is both a behaviour guarantee and wide enough to let the model take one training step. The gate would then have to be read as a stop on runaway change, and behaviour would have to be checked some other way. `PREREG.md` states this as a prediction that can fail.

## Not covered

- Theorem 1 is for the three-layer net of E13. No bound is proved for the transformer.
- The theorem is evaluated in double precision, not interval arithmetic. The program checks that no measured change exceeds it.
- Section 4 covers permutations only. Other symmetries, such as rescaling paired layers in a net with a homogeneous activation, are not treated. The E13 activation is not homogeneous.
- The known results are standard: the matrix `G` is the Gauss-Newton or Fisher matrix, and Proposition 2 is the usual sampling bound. They were not re-read from a source for this note.
