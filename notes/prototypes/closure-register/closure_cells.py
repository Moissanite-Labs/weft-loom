#!/usr/bin/env python3
"""Closure on an assignment space: what closed cells force, and what they are worth.

n rows are matched one-to-one to n columns. A cell (i, j) stands for "row i
takes column j". A set of cells is closed, and a valid assignment uses no closed
cell. This program

1. finds every open cell that no valid assignment can use, with a certificate
   for each (facts 6 of the note), and checks that adding those cells is a
   closure operator;
2. counts the valid assignments exactly, which gives the share of uniformly
   random assignments that a set of closed cells removes, and compares it with
   the Poisson value and with a proved bound on the gap (fact 7).

Pure Python, no packages. Usage, from the root of a checkout:
  python3 notes/prototypes/closure-register/closure_cells.py > notes/prototypes/closure-register/closure_cells.out
A larger tested library for the same objects is in Moissanite-Labs/siliquant, perm/.
"""
from __future__ import annotations

import itertools
import math
import random
from fractions import Fraction


def matching(open_):
    """A perfect matching as a list col_of_row, or None. Augmenting paths."""
    n = len(open_)
    row_of_col = [-1] * n

    def grow(i, seen):
        for j in range(n):
            if open_[i][j] and j not in seen:
                seen.add(j)
                if row_of_col[j] < 0 or grow(row_of_col[j], seen):
                    row_of_col[j] = i
                    return True
        return False

    for i in range(n):
        if not grow(i, set()):
            return None
    col_of_row = [0] * n
    for j, i in enumerate(row_of_col):
        col_of_row[i] = j
    return col_of_row


def columns(open_, rows):
    return {j for i in rows for j in range(len(open_)) if open_[i][j]}


def short_set(open_):
    """Rows whose open cells lie in fewer columns than there are rows, if no valid assignment exists."""
    n = len(open_)
    for k in range(1, n + 1):
        for rows in itertools.combinations(range(n), k):
            if len(columns(open_, rows)) < k:
                return set(rows)
    return None


def dead_cells(open_):
    """Open cells on no valid assignment, each with a set of rows that proves it.

    Take one valid assignment M. Row r can reach row r2 if r could take the
    column M gives to r2. A cell (i, M[i2]) with i != i2 is on some valid
    assignment exactly when i2 reaches i. If it does not, the rows i2 reaches
    are the certificate.
    """
    n = len(open_)
    m = matching(open_)
    if m is None:
        return None
    reach = []
    for start in range(n):
        seen, todo = {start}, [start]
        while todo:
            r = todo.pop()
            for r2 in range(n):
                if r2 not in seen and open_[r][m[r2]]:
                    seen.add(r2)
                    todo.append(r2)
        reach.append(seen)
    owner = {m[r]: r for r in range(n)}
    dead = {}
    for i in range(n):
        for j in range(n):
            if open_[i][j] and m[i] != j and i not in reach[owner[j]]:
                dead[(i, j)] = set(reach[owner[j]])
    return dead


def certificate_holds(open_, cell, rows):
    """The rows need as many columns as they have, the cell's column is one of them, and its row is not among them."""
    i, j = cell
    cols = columns(open_, rows)
    return len(cols) == len(rows) and j in cols and i not in rows


def closure(board, n):
    open_ = [[0 if (i, j) in board else 1 for j in range(n)] for i in range(n)]
    dead = dead_cells(open_)
    if dead is None:
        return {(i, j) for i in range(n) for j in range(n)}
    return set(board) | set(dead)


def permanent(a):
    """Ryser's formula over column subsets in Gray-code order. Exact for integers."""
    n = len(a)
    if n == 0:
        return 1
    sums = [0] * n
    total, gray = 0, 0
    for k in range(1, 1 << n):
        bit = (k & -k).bit_length() - 1
        gray ^= 1 << bit
        sign = 1 if gray >> bit & 1 else -1
        for i in range(n):
            sums[i] += sign * a[i][bit]
        prod = 1
        for s in sums:
            prod *= s
        total += (-1) ** (n - bin(gray).count("1")) * prod
    return total


def valid_count(board, n):
    return permanent([[0 if (i, j) in board else 1 for j in range(n)] for i in range(n)])


def poisson_gap_bound(board, n):
    """Proved bound on |share of assignments that avoid the board - exp(-|board| / n)| (fact 7)."""
    if not board:
        return 0.0
    rows, cols = [0] * n, [0] * n
    for i, j in board:
        rows[i] += 1
        cols[j] += 1
    lam = len(board) / n
    total = sum((rows[i] + cols[j] - 1) / n + (len(board) - rows[i] - cols[j] + 1) / (n * (n - 1)) for i, j in board)
    return (1 - math.exp(-lam)) / lam * total / n


def derangements(n):
    d = [1, 0]
    for k in range(2, n + 1):
        d.append((k - 1) * (d[k - 1] + d[k - 2]))
    return d[n]


def menage(n):
    return sum((-1) ** k * Fraction(2 * n, 2 * n - k) * math.comb(2 * n - k, k) * math.factorial(n - k) for k in range(n + 1))


def selftest():
    rng = random.Random(3)
    for _ in range(400):
        n = rng.randint(2, 5)
        p = rng.choice([0.3, 0.5, 0.7])
        open_ = [[1 if rng.random() < p else 0 for _ in range(n)] for _ in range(n)]
        used = set()
        count = 0
        for s in itertools.permutations(range(n)):
            if all(open_[i][s[i]] for i in range(n)):
                count += 1
                used |= {(i, s[i]) for i in range(n)}
        if permanent(open_) != count:
            raise SystemExit("FAIL: Ryser's formula disagrees with enumeration")
        dead = dead_cells(open_)
        if count == 0:
            rows = short_set(open_)
            if dead is not None or rows is None or len(columns(open_, rows)) >= len(rows):
                raise SystemExit("FAIL: no valid assignment, and no short set of rows found")
            continue
        truth = {(i, j) for i in range(n) for j in range(n) if open_[i][j]} - used
        if set(dead) != truth or not all(certificate_holds(open_, c, rows) for c, rows in dead.items()):
            raise SystemExit("FAIL: dead cells or their certificates disagree with enumeration")
        cells = [(i, j) for i in range(n) for j in range(n)]
        b2 = {c for c in cells if rng.random() < 0.4}
        b1 = {c for c in b2 if rng.random() < 0.6}
        c1, c2 = closure(b1, n), closure(b2, n)
        if not (b1 <= c1 and c1 <= c2 and closure(c1, n) == c1):
            raise SystemExit("FAIL: adding the dead cells is not extensive, monotone and idempotent")
    for n in (2, 3, 4):
        cells = [(i, j) for i in range(n) for j in range(n)]
        for bits in range(1, 1 << len(cells)):
            board = {c for k, c in enumerate(cells) if bits >> k & 1}
            gap = abs(valid_count(board, n) / math.factorial(n) - math.exp(-len(board) / n))
            if gap > poisson_gap_bound(board, n) + 1e-12:
                raise SystemExit(f"FAIL: the bound of fact 7 fails on {sorted(board)}")
    return "self-test passed: 400 random boards against enumeration, and the bound of fact 7 on every board up to 4 by 4"


def main():
    print(selftest())
    print()
    print("Fact 6. Closed cells force other cells closed")
    board = {(0, 2), (0, 3), (1, 2), (1, 3), (3, 0), (3, 1)}
    open_ = [[0 if (i, j) in board else 1 for j in range(4)] for i in range(4)]
    print("   4 by 4 example, closed by hand:", sorted(board))
    for cell, rows in sorted(dead_cells(open_).items()):
        print(f"   forced closed: {cell}; rows {sorted(rows)} can only use columns {sorted(columns(open_, rows))}, so none is left for row {cell[0]}; "
              f"certificate holds: {certificate_holds(open_, cell, rows)}")
    print(f"   valid assignments before and after adding the forced cells: {valid_count(board, 4)} and {valid_count(closure(board, 4), 4)}")
    # Scaling rows and columns to sum 1 in turn also drives a forced cell to zero, but only in the limit.
    p = [[float(v) for v in row] for row in open_]
    seen = {}
    for k in range(1, 10001):
        p = [[v / sum(row) for v in row] for row in p]
        col = [sum(p[i][j] for i in range(4)) for j in range(4)]
        p = [[p[i][j] / col[j] for j in range(4)] for i in range(4)]
        if k in (10, 100, 1000, 10000):
            seen[k] = p[2][0]
    print("   the same cell (2, 0) under row and column scaling, after 10, 100, 1000 and 10000 rounds: " + ", ".join(f"{seen[k]:.2g}" for k in sorted(seen)))
    print()
    print("Fact 7. What a set of closed cells is worth against uniformly random assignments")
    print("   board | n | closed cells per row | share that avoids every closed cell | exp(-cells per row) | proved bound on the gap | worth = 1 / share")
    for n in (5, 10, 20, 40):
        share = Fraction(derangements(n), math.factorial(n))
        board = {(i, i) for i in range(n)}
        print(f"   one cell per row (diagonal) | {n} | 1 | {float(share):.6f} | {math.exp(-1):.6f} | {poisson_gap_bound(board, n):.4f} | {float(1 / share):.4f}")
    for n in (5, 10, 20, 40):
        share = menage(n) / math.factorial(n)
        board = {(i, i) for i in range(n)} | {(i, (i + 1) % n) for i in range(n)}
        print(f"   two cells per row (two diagonals) | {n} | 2 | {float(share):.6f} | {math.exp(-2):.6f} | {poisson_gap_bound(board, n):.4f} | {float(1 / share):.4f}")
    rng = random.Random(11)
    n = 12
    for cells in (12, 24, 36):
        board = set(rng.sample([(i, j) for i in range(n) for j in range(n)], cells))
        share = Fraction(valid_count(board, n), math.factorial(n))
        print(f"   {cells} random cells | {n} | {cells / n:g} | {float(share):.6f} | {math.exp(-cells / n):.6f} | {poisson_gap_bound(board, n):.4f} | {float(1 / share):.4f}")


if __name__ == "__main__":
    main()
