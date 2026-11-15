# Closure, counted: forbidden cells, coverings and rounded cells

Date: 2026-11-15
Status: idea. Not adopted.
Builds on: [closure-by-certificate](closure-by-certificate.md), called the first note below
Prototype: `notes/prototypes/closure-register/` (`closure_cells.py`, `closure_quant.py`)

## Why this note

The first note left two questions open. How much effort does a closure remove? And how often does a proposer land inside a closed ball?

On 2026-11-15 the project owner put a list of classical tools beside the closure rule: inclusion-exclusion, derangements, rook and hit polynomials, permanents, Sinkhorn scaling, the Birkhoff polytope. The owner also asked whether quantisation is a side road or meets the rule.

This note takes up both questions for proposers of a stated kind, and tests three more sectors. Nobody has measured a real proposer, so neither question is settled. The facts continue the numbering of the first note. Labels: [P] proved here, [K] known, [I] a reading.

## Closure where the paths are assignments

Match n rows one-to-one to n columns. A cell (i, j) stands for "row i takes column j". Some cells are closed. A valid assignment uses no closed cell. Hidden units matched to hidden units have this form. So do demands routed to slots and tasks given to agents, when each takes exactly one.

**6. Closed cells force other cells closed, each with a certificate.** [P] Call an open cell dead if no valid assignment uses it. For a set S of rows, write C(S) for the set of columns in which some row of S has an open cell.

*Claim.* Suppose at least one valid assignment exists. An open cell (i, j) is dead exactly when there is a set S of rows, without row i, such that C(S) has exactly |S| members and j is one of them.

[K] If no valid assignment exists, some set S has fewer than |S| columns in C(S). That is Hall's theorem, and every cell is then closed.

*Proof.* If such a set S exists, its rows take all of C(S), and j is in C(S), so row i cannot have it.

For the converse take a valid assignment M and say row r reaches row r2 if r could take the column M gives to r2. Suppose j is M's column for row i2. The cell (i, j) lies on some valid assignment exactly when i2 reaches i through a chain of such steps, because a shortest chain closes into a cycle along which each row takes the next row's column.

If i2 does not reach i, let S be the rows i2 reaches, with i2 itself. Then C(S) is the set of columns M gives to S. It has |S| members and includes j.

The set S is a certificate of the crossed-bounds kind, in whole numbers: S together with row i would need |S| + 1 columns, and C(S) has |S|. It is checked by counting.

Adding the dead cells to the closed set is a closure operator: it never removes a cell, a larger closed set gives a larger result, and doing it twice adds nothing. All three hold because the set of valid assignments only shrinks as cells close, and closing a dead cell removes no valid assignment.

`closure_cells.py` checks the dead cells and their certificates against full enumeration on 400 random boards of up to 5 rows. It checks the three properties on separate random pairs of closed sets.

- **Example.** On a 4 by 4 board, close (0,2), (0,3), (1,2), (1,3), (3,0), (3,1). Rows 0 and 1 can then only use columns 0 and 1, so cells (2,0) and (2,1) are dead, though nobody tested them. The number of valid assignments stays at 4.
- **What the runtime has.** `synaptic_flow.py` in weft proves the case where no valid routing exists, with a min-cut certificate. [I] It does not report dead cells. The same argument would give them, as the links that no full routing can use.
- **Scaling finds them only in the limit.** Scaling rows and columns to sum 1 in turn also drives a dead cell to zero. On the example the cell (2,0) holds 0.049 after 10 rounds, 0.0051 after 100 and 0.00005 after 10,000. The rule above needs one matching and a search from each row.

**7. What a set of closed cells is worth is a permanent.** Suppose proposals are assignments drawn uniformly. Let B be the closed set and N0 the number of assignments that avoid B.

- [K] N0 is the permanent of the 0/1 matrix of open cells. By inclusion-exclusion it equals the sum over k of (-1)^k r_k (n-k)!, where r_k counts the ways to place k rooks on B with no two in a row or column.
- The share of proposals that touch a closed cell is m = 1 - N0/n!. By fact 2 of the first note the closure is worth n!/N0.
- [P] Let lambda = |B|/n, let r_i be the number of closed cells in row i and c_j the number in column j. Then N0/n! differs from exp(-lambda) by at most

      ((1 - exp(-lambda)) / lambda) * (1/n) * sum over closed cells (i, j) of [ (r_i + c_j - 1)/n + (|B| - r_i - c_j + 1)/(n(n-1)) ].

*Proof.* [K] The Stein-Chen coupling theorem, in the form given by Barbour, Holst and Janson (1992), reads as follows. Let W be a sum of indicators with means p_a and total mean lambda. Suppose that for each a there are variables U with the law of W, and V with the law of W - 1 given that indicator a is 1.

Then the total variation distance from W to the Poisson law of mean lambda is at most ((1 - exp(-lambda)) / lambda) times the sum of p_a E|U - V|. The book was not opened for this note.

Here W is the number of closed cells a random assignment s uses, and each closed cell has p = 1/n. For the cell (i, j), let k be the row with s(k) = j and exchange the values of s at i and k. The new assignment s' is uniform among those that use (i, j), since each of them comes from exactly n assignments. Take U = W(s) and V = W(s') - 1.

If k = i then U - V = 1, with probability 1/n. Otherwise U - V = b(i, s(i)) + b(k, j) - b(k, s(i)), where b marks closed cells. The three terms have expectations (r_i - 1)/n, (c_j - 1)/n and (|B| - r_i - c_j + 1)/(n(n-1)). Adding 1/n gives the bracket.

The distance bounds the gap at the single value W = 0, which is N0/n! against exp(-lambda).

`closure_cells.py` checks the bound on every board up to 4 by 4.

| Closed cells | n | Share of assignments that avoid them | exp(-cells per row) | Proved bound on the gap | Worth |
|---|---|---|---|---|---|
| One per row, the diagonal | 10 | 0.3679 | 0.3679 | 0.126 | 2.72 |
| Two per row, two diagonals | 10 | 0.1212 | 0.1353 | 0.423 | 8.25 |
| Two per row, two diagonals | 40 | 0.1319 | 0.1353 | 0.108 | 7.58 |
| 36 at random | 12 | 0.0239 | 0.0498 | 0.739 | 41.9 |

The bound is additive and the worth is a ratio. At every size in the table the bound is too loose to fix the worth: for two diagonals at n = 40 it allows a share anywhere from 0.02 to 0.24. It only becomes useful when n is far larger than the number of closed cells per row.

[I] The exact counts, not the bound, show the pattern: against uniform proposals on a large board, each closed cell per row multiplies the yield by about e. On the small boards computed here the factor is larger. One closure per row is the classical count of derangements, and two per row is the ménage problem.

[K] Counting N0 exactly is #P-complete, so no fast exact method is expected. Ryser's formula takes n 2^n steps. For 0/1 matrices the Bregman-Minc bound caps N0 from above.

## Closure where the paths are points of weight space

**8. Closing by balls is a covering problem, and in many dimensions one ball closes almost nothing.** [P] Let a proposer draw moves in d dimensions from a density that is nowhere above one over the volume of a ball of radius L. The share of its proposals inside any one ball of radius rho is at most (rho/L)^d.

The uniform law on a ball of radius L is such a proposer. For the calibration hosts d is 12,488. Fact 4 of the first note gives a closed radius of 0.15 to 0.20 of the failed move's length. Take L to be that length. One closed ball then removes a share below 10^-8700.

[I] So a closed ball can remove a real share of effort only from a proposer whose proposals concentrate near the failed move, such as a line search along the failed direction. On that line the closed interval reaches 15 to 20 percent of the step to either side. Low dimension alone is not enough: a family that does not pass near the failed move misses the ball.

[K] To close a region with balls of radius rho takes at least its volume over the volume of one ball. A lattice of centres needs more by its covering thickness. The lattice A_d\*, whose cell is the permutohedron, is the thinnest lattice covering for d up to 5. In 8 dimensions its thickness is 3.67, against 64.9 for the cubic grid and 3.14 for the best lattice known.

The source for the thickness formula, the cases up to 5 and the record at 8 is Schürmann and Vallentin, "Computational approaches to lattice packing and covering problems" (2006). None of this reaches 12,488 dimensions. It applies to a proposer confined to a handful.

[I] The same lattice was proposed to the project for rounding weights. As a quantiser in 8 dimensions it is behind E8. As a covering it is far ahead of the cubic grid, and the best among lattices up to 5 dimensions.

**9. On a fixed grid the moves inside a ball can be counted.** A cell whose weights stay on a fixed grid changes by whole steps. A ball of radius R holds finitely many such moves, and only the zero move if R is under one step.

[I] This is where quantisation meets the rule. In a continuous space a closed sector has a measure, which fact 8 shows can be vanishing. On a grid it has a count. The price is in the next section: on these hosts the proved ball is smaller than one grid step up to 7 bits, and on 10 of 12 hosts at 8.

## Three more sectors, tested

The terms come from the calibration record (`experiments/gate-metric-calibration-2026-11-15`).

- A **host** is one of its 12 small MLP networks, with 12,488 weights.
- The **bar** is a drop of at most 0.025 in the host's score on its native skills. A **passing fine-tune** is 120 ordinary training steps that keep the bar and learn a new skill.
- A **breaking move** is a move found by a search that tries to do damage. Its length is the shortest tested length, 0.1 or 0.3, at which the search breaks the bar.
- **Theorem 1** of that record bounds how far the outputs can move inside a ball of weight space. The **proved ball** is the largest ball in which it keeps the RMS change over the host's 1,024 held-out inputs under 0.05. It is a statement about those inputs, not about every input.
- **Rounding to b bits** here means one scheme: each weight matrix rounded to the nearest of 2^b evenly spaced levels over its own range, biases kept as they are.

`closure_quant.py` rebuilds each host's passing fine-tune, checks it against its recorded row, and rounds each host. `check_closures.py` checks the three certificates.

| Id | Sector closed | Upper bound | Lower bound | Certified on |
|---|---|---|---|---|
| CL-5 | One radius of a ball measured after the best relabelling of hidden units, that admits the passing fine-tune and rejects a breaking move | 0.1 to 0.3 | 1.80 to 2.27 | 12 of 12 hosts |
| CL-6 | One Frobenius radius around the float cell that admits its copy rounded to 5, 6 or 7 bits by the scheme above and rejects a breaking move | 0.1 to 0.3 | 0.39 to 2.27 | 36 of 36 pairs of host and bit width |
| CL-7 | Certifying one grid step of a weight, in a cell rounded to 5, 6 or 7 bits by the scheme above, with the proved ball around that cell | 0.0026 to 0.0032 | 0.0057 to 0.040 | 36 of 36 |

- **CL-5.** Relabelling hidden units changes the weights and no output, so the first note counted it against the ball. A gate could instead measure distance after the best relabelling. That repairs one fault of the ball and leaves the other.
- **Its lower bound.** [K] By Mirsky's theorem no relabelling brings a matrix nearer than the distance between sorted singular values. The fine-tune of length 8.1 to 9.2 stays at least 1.80 to 2.27 away. The breaking move is at most 0.1 to 0.3 away, since leaving the labels alone is one relabelling.
- **What CL-5 covers.** Any distance that lies between the singular-value distance and the Frobenius distance. Other distances that ignore relabelling, such as one built on the largest singular value, are not covered.
- **Optimal transport.** A brief sent to the project proposed a transport distance between neuron sets as the cell's boundary. [P] Take a layer of width w and treat each neuron as a row of [W | b]. The transport distance between the two sets of w neurons is 1/sqrt(w) times the Frobenius distance after the best matching of rows, because with equal weights a best plan can be taken to be a matching (Birkhoff).
- **What follows for it.** That distance times sqrt(w), summed in squares over layers, lies between the two bounds and is covered. An entropy-smoothed version is not.
- **CL-6.** Rounding to 5 bits moves the weights by 1.6 to 2.3 and lowers the native score by 0.005 to 0.010, inside the bar. A searched move 5 to 23 times shorter breaks the bar. A weight radius cannot tell the two apart. A finer rounding scheme would shorten the error and is not covered.
- **CL-7.** A rounded cell keeps the bar from 5 bits. One grid step fits inside the proved ball only from 9 bits (2 of 12 hosts at 8). From 5 to 7 bits the cell is usable and a first on-grid step of a weight cannot be certified this way. The certificate is what is closed. The step itself may be harmless.
- **What CL-7 leaves out.** Biases are not on the grid, and a small change of a bias fits the ball. The grid is the one fixed at rounding. Only the ball around the first rounded cell was measured, not around later ones.

The copy is within the output tolerance of 0.05 on all hosts from 8 bits.

The numbers of the rounded cells are saved by `closure_quant.py` and read by the checker as saved. No other record holds them.

## What stays open

- A rounded cell that adapts off its grid, with a float side update judged by behaviour. Nothing here closes it.
- A gate on behaviour. The committed-behaviour-change record is that path, and none of CL-5 to CL-7 touches it.
- CL-5 to CL-7 on the transformer hosts. Only the MLP hosts were rebuilt.

## Open questions

1. What does a real proposer's distribution look like? Facts 7 and 8 give the worth of a closure only for the proposers they name.
2. Should the router report dead links as well as shortfalls? Fact 6 says what to compute.
3. Can a specific, known move such as a rounding error be bounded over a whole input domain? Theorem 1 bounds every move in a ball at once, on a fixed set of inputs, which is why it is loose for one known move.
4. Is there a grid on which closed sectors are large in count and cheap to certify? The quantisation records are kept in the siliquant repository.
