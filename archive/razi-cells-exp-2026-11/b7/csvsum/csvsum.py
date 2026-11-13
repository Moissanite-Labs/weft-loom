#!/usr/bin/env python3
"""Aggregate a CSV stream with header id,cat,val by cat.

Input is read from stdin.  Output is CSV rows "cat,sum" (no header), sorted
by cat; sums are printed with exactly two decimals.  Values are accumulated as
fixed-point integers (18 fractional digits) so decimal input is not distorted
by binary floating point.
"""

import csv
import io
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext

SCALE = 10 ** 18
SCALE_DEC = Decimal(SCALE)
CENT = SCALE // 100

DIGITS = "0123456789"


def parse_general(s):
    """Parse an arbitrary decimal string into SCALE-scaled units."""
    try:
        with localcontext() as ctx:
            ctx.prec = max(50, len(s) + 40)
            return int((Decimal(s) * SCALE_DEC).to_integral_value(
                rounding=ROUND_HALF_EVEN))
    except (InvalidOperation, ValueError, TypeError):
        # Last-resort support for anything the C float parser understands.
        return round(float(s) * SCALE)


def parse_scaled(s):
    """Fast exact path for the common signed NNN.NN form."""
    if len(s) >= 4 and s[-3] == "." and s[-2:].isdigit():
        whole = s[:-3]
        if whole and (whole.isdigit() or
                      (whole[0] in "+-" and whole[1:].isdigit())):
            try:
                return int(whole + s[-2:]) * CENT
            except ValueError:
                pass
    return parse_general(s)


def format_scaled(x):
    """Round a SCALE-scaled integer to cents (half-even) and format it."""
    negative = x < 0
    x = -x if negative else x
    q, r = divmod(x, CENT)
    r2 = r + r
    if r2 > CENT or (r2 == CENT and (q & 1)):
        q += 1
    if q == 0:
        return "0.00"
    sign = "-" if negative else ""
    return f"{sign}{q // 100}.{q % 100:02d}"


def main():
    try:
        inp = io.TextIOWrapper(sys.stdin.buffer,
                               encoding=sys.stdin.encoding or "utf-8",
                               newline="")
    except AttributeError:
        inp = sys.stdin

    reader = csv.reader(inp)
    header = next(reader, None)
    if header is None:
        return
    try:
        cat_i = header.index("cat")
        val_i = header.index("val")
    except (ValueError, AttributeError):
        cat_i, val_i = 1, 2

    sums = {}
    get = sums.get
    parse = parse_scaled
    needed = max(cat_i, val_i)
    for row in reader:
        if len(row) <= needed:
            continue
        cat = row[cat_i]
        sums[cat] = get(cat, 0) + parse(row[val_i])

    writer = csv.writer(sys.stdout, lineterminator="\n")
    fmt = format_scaled
    for cat in sorted(sums):
        writer.writerow((cat, fmt(sums[cat])))


if __name__ == "__main__":
    main()
