# Closure, counted: forbidden cells, coverings and rounded cells

Date: 2026-11-15
Status: idea. Not adopted.
Builds on: [closure-by-certificate](closure-by-certificate.md)
Prototype: `notes/prototypes/closure-register/` (`closure_cells.py`, `closure_quant.py`)

## Why this note

The first note left two questions open. How much effort does a closure remove? And how often does a proposer land inside a closed ball?

On 2026-11-15 the project owner put a list of classical tools beside the closure rule: inclusion-exclusion, derangements, rook and hit polynomials, permanents, Sinkhorn scaling, the Birkhoff polytope. The owner also asked whether quantisation is a side road or meets the rule.

This note answers the two questions for two kinds of search space and tests three more sectors. The facts continue the numbering of the first note. Labels: [P] proved here, [K] known, [I] a reading.

## Closure where the paths are assignments

Match n rows one-to-one to n columns. A cell (i, j) stands for "row i takes column j". Some cells are closed. A valid assignment uses no closed cell. Demands routed to slots, units matched to units and tasks given to agents all have this form.

**6. Closed cells force other cells closed, each with a certificate.** [P] Call an open cell dead if no valid assignment uses it.

*Claim.* An open cell (i, j) is dead exactly when some set S of rows, without row i, has all its open cells in |S| columns, one of them column j. If there is no valid assignment at all, some set of rows has its open cells in fewer columns than it has rows. That second case is Hall's theorem.

*Proof.* If such a set S exists, its rows take all of its columns, and column j is one of them, so row i cannot have it.

For the converse take a valid assignment M and say row r reaches row r2 if r could take the column M gives to r2. Suppose j is M's column for row i2. The cell (i, j) lies on some valid assignment exactly when i2 reaches i through a chain of such steps, because the chain closes into a cycle of swaps.

If i2 does not reach i, let S be the rows i2 reaches. The open cells of S then lie in the columns M gives to S, which are |S| in number and include j.

The set S is a certificate of the crossed-bounds kind, in whole numbers: S needs |S| columns and has exactly |S|. It is checked by counting.

Adding the dead cells to the closed set is a closure operator. It never removes a cell, it gives more for a larger closed set, and doing it twice adds nothing. `closure_cells.py` checks all of this against full enumeration on 400 random boards.

- **Example.** On a 4 by 4 board, close (0,2), (0,3), (1,2), (1,3), (3,0), (3,1). Rows 0 and 1 can then only use columns 0 and 1, so cells (2,0) and (2,1) are dead, though nobody tested them. The number of valid assignments stays at 4.
- **What the runtime has.** `synaptic_flow.py` in weft proves the case where no valid routing exists, with a min-cut certificate. [I] It does not report dead cells. The same argument would give them, as the links that no full routing can use.
- **Scaling finds them only in the limit.** Scaling rows and columns to sum 1 in turn also drives a dead cell to zero. On the example the cell (2,0) holds 0.049 after 10 rounds, 0.0051 after 100 and 0.00005 after 10,000. The rule above needs one matching and one search.

**7. What a set of closed cells is worth is a permanent, and close to a Poisson value.** Suppose proposals are assignments drawn uniformly. Let B be the closed set and N0 the number of assignments that avoid B.

- [K] N0 is the permanent of the 0/1 matrix of open cells. By inclusion-exclusion it equals the sum over k of (-1)^k r_k (n-k)!, where r_k counts the ways to place k rooks on B with no two in a row or column.
- The share of proposals that touch a closed cell is m = 1 - N0/n!. By fact 2 the closure is worth n!/N0.
- [P] Let lambda = |B|/n, let r_i be the number of closed cells in row i and c_j the number in column j. Then N0/n! differs from exp(-lambda) by at most

      ((1 - exp(-lambda)) / lambda) * (1/n) * sum over closed cells (i, j) of [ (r_i + c_j - 1)/n + (|B| - r_i - c_j + 1)/(n(n-1)) ].

*Proof.* This is the Stein-Chen coupling bound for the number W of closed cells that a random assignment s uses. To condition on s using the cell (i, j), let k be the row with s(k) = j and exchange the values of s at i and k. The new assignment is uniform among those that use (i, j).

Apart from the cell (i, j) itself, the count changes by at most b(i, s(i)) + b(k, j) + b(k, s(i)), where b marks closed cells, and by 1 when k = i. Taking expectations gives the bracket.

`closure_cells.py` checks the bound on every board up to 4 by 4. The bound is of the order of the number of closed cells per row over n, so it is loose for small boards.

| Closed cells | n | Share of assignments that avoid them | exp(-cells per row) | Worth |
|---|---|---|---|---|
| One per row, the diagonal | 10 | 0.3679 | 0.3679 | 2.72 |
| Two per row, two diagonals | 10 | 0.1212 | 0.1353 | 8.25 |
| Two per row, two diagonals | 40 | 0.1319 | 0.1353 | 7.58 |
| 36 at random | 12 | 0.0239 | 0.0498 | 41.9 |

[I] So against uniform proposals, each closed cell per row multiplies the yield by about e. One closure per row is the classical count of derangements, and two per row is the ménage problem. Real proposers are not uniform, and nobody has measured one here.

[K] Counting N0 exactly is as hard as any counting problem, and Ryser's formula takes n 2^n steps. For 0/1 matrices the Bregman-Minc bound caps N0 from above.

## Closure where the paths are points of weight space

**8. Closing by balls is a covering problem, and in many dimensions one ball closes almost nothing.** [P] Let a proposer draw moves with a density at most that of the uniform law on a ball of radius L in d dimensions. The share of its proposals inside one closed ball of radius rho is at most (rho/L)^d.

For the calibration hosts d is 12,488. Fact 4 gives a closed radius of 0.15 to 0.20 of the failed move's length. Against a proposer that spreads over a ball as wide as the failed move is long, one closed ball removes a share below 10^-8700.

[I] The balls of fact 4 are worth something only against a proposer confined to a few dimensions: a line search, a short list of directions, a low-rank family. Along the line through a failed move, the closed interval reaches 15 to 20 percent of the step to either side. That answers question 2 of the first note with a bound.

[K] To close a region with balls of radius rho takes at least its volume over the volume of one ball. A lattice of centres needs more by its covering thickness. The lattice A_d\*, whose cell is the permutohedron, is the thinnest lattice covering for d up to 5. In 8 dimensions its thickness is 3.67, against 64.9 for the cubic grid and 3.14 for the best lattice known.

[I] The same lattice was proposed to the project for rounding weights. As a quantiser in 8 dimensions it is behind E8. Covering is the job it is good at, and closing a region is a covering job.

**9. On a grid every sector is a finite set.** [P] A cell rounded to b bits per weight can change only by whole steps. A ball of radius R holds finitely many of its moves: none but the zero move if R is under one step.

[I] This is where quantisation meets the rule. In a continuous space a closed sector has a measure, which fact 8 shows can be vanishing. On a grid it has a count, and the tools of fact 7 apply. The price is in the next section: on these hosts the proved ball is smaller than one grid step at every bit width where it would matter.

## Three more sectors, tested

`closure_quant.py` rebuilds the passing fine-tune of each of the 12 MLP hosts, checks it against its recorded row, and rounds each host to b bits per weight. `check_closures.py` checks the three certificates.

| Id | Sector closed | Upper bound | Lower bound | Certified on |
|---|---|---|---|---|
| CL-5 | One radius of a ball measured after the best relabelling of hidden units, that admits a passing fine-tune and rejects a breaking move | 0.1 to 0.3 | 1.81 to 2.27 | 12 of 12 hosts |
| CL-6 | One Frobenius radius around the float cell that admits its copy rounded to 5, 6 or 7 bits and rejects a breaking move | 0.1 to 0.3 | 0.40 to 2.27 | 36 of 36 host and bit-width pairs |
| CL-7 | Certifying an on-grid step of a cell rounded to 5, 6 or 7 bits with the ball of Theorem 1 | 0.0026 to 0.0031 | 0.0058 to 0.040 | 36 of 36 |

- **CL-5.** Relabelling hidden units changes the weights and no output, so the first note counted it against the ball. A gate could instead measure distance after the best relabelling. That repairs one fault of the ball and leaves the other.
- **Its lower bound.** [K] By Mirsky's theorem no relabelling brings a matrix nearer than the distance between sorted singular values. The fine-tune of length 8.1 to 9.2 stays at least 1.81 to 2.27 away. The breaking move is at most 0.1 to 0.3 away under any such distance.
- **What CL-5 covers.** Any distance between the singular-value distance and the Frobenius distance, which includes optimal-transport distances between the neuron sets of a layer. A brief sent to the project proposed such a distance as the cell's boundary. An entropy-smoothed version is not between the two bounds and is not covered.
- **CL-6.** Rounding to 5 bits moves the weights by 1.6 to 2.3 and lowers the native score by 0.005 to 0.010, inside the bar of 0.025. A move 5 to 20 times shorter breaks the bar. A weight radius cannot tell the two apart.
- **CL-7.** A rounded cell keeps the bar from 5 bits. One grid step fits inside the proved ball only from 9 bits (2 of 12 hosts at 8). Between 5 and 7 bits the cell is usable and no on-grid change can be certified this way. The certificate is what is closed. The change itself may be harmless.

The rounding scheme is the plainest one: evenly spaced levels over the range of each weight matrix, biases kept. The copy is within the output tolerance of 0.05 on all hosts from 8 bits.

## What stays open

- A rounded cell that adapts off its grid, with a float side update judged by behaviour. Nothing here closes it.
- A gate on behaviour. The committed-behaviour-change record is that path, and none of CL-5 to CL-7 touches it.
- CL-5 to CL-7 on the transformer hosts. Only the MLP hosts were rebuilt.

## Open questions

1. What does a real proposer's distribution look like? Facts 7 and 8 give the worth of a closure for uniform proposals only.
2. Should the router report dead links as well as shortfalls? Fact 6 says what to compute.
3. Can a specific, known move such as a rounding error be bounded over a whole input domain? Theorem 1 bounds every move in a ball at once, which is why it is loose for one known move.
4. Is there a grid on which closed sectors are large in count and cheap to certify? The quantisation records are kept in the siliquant repository.
