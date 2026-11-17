"""ledger: per-account totals from multi-file transaction data with instance-specific rules.

Quirks drawn per instance: delimiter, column order, timestamp pattern, amount style,
excluded statuses, base currency with rate direction, rounding mode; duplicate ids where
the latest row wins; messy account ids. Level 1 has a single currency and plain amounts,
level 3 adds a quoted free-text `memo` column that can contain the delimiter.
"""

import csv
import io
import json
import pathlib
import re
from decimal import ROUND_HALF_UP, Decimal

from . import _util

FAMILY = "ledger"
DELIMS = [",", ";", "|", "\t"]
COLUMNS = ["id", "timestamp", "account", "amount", "currency", "status"]
STATUSES = ["posted", "settled", "cleared", "pending", "void", "reversed", "failed", "hold"]
SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CHF": "Fr", "CAD": "C$"}
CENT = Decimal("0.01")
SPAN = 90 * 86400

TASK = """# Task: account totals

`data/` holds transaction files. Work out, for every account, the total of its
transactions in the base currency.

The data is messy on purpose and the rules are specific to this instance: delimiter,
column order, timestamp pattern, amount style, which statuses are excluded, how duplicate
ids are resolved, currency conversion and rounding. All of it is stated in `FORMAT.md`.
Read it before writing any code.

## Output

Write `answer.json` in this directory (next to this file): one JSON object that maps each
normalised account id to its total, a JSON number rounded to 2 decimals. Shape:

    {"ACCOUNT-A": 1520.25, "ACCOUNT-B": -80.1}

## Check your work

`example/` is a tiny dataset with the same layout and exactly the same rules
(`example/data/...`). Its correct answer is in `example/expected.json`. Run your solver
on `example/` first and compare, then run it on `data/`.

## Scoring

Fraction of accounts whose total is within 0.01 of the correct value. Extra keys are
ignored; an answer that is not a JSON object scores 0.
"""


def _draw_params(rng, level):
    """Draw the rule parameters of one instance."""
    delim = rng.choice(DELIMS)
    columns = COLUMNS + (["memo"] if level >= 3 else [])
    rng.shuffle(columns)
    used = rng.sample(STATUSES, 5)
    excluded = sorted(rng.sample(used, 1 if level == 1 else rng.choice([2, 3])))
    style = {"thousands": "", "decimal": ".", "negative": "minus", "decoration": "none"}
    rates, direction = {}, "none"
    base = rng.choice(sorted(SYMBOLS))
    if level >= 2:
        style["decimal"] = rng.choice([mark for mark in ".," if mark != delim])
        options = [sep for sep in ["", ",", ".", " ", "'"] if sep not in (delim, style["decimal"])]
        style["thousands"] = rng.choice(options)
        style["negative"] = rng.choice(["minus", "parentheses", "trailing-minus"])
        style["decoration"] = rng.choice(["none", "symbol-prefix", "code-prefix", "code-suffix"])
        for currency in rng.sample([c for c in sorted(SYMBOLS) if c != base], 3):
            rates[currency] = round(rng.uniform(0.2, 4.0), 4)
        direction = rng.choice(["multiply", "divide"])
    return {
        "delim": delim, "columns": columns, "ts": rng.choice(_util.TS_FORMATS),
        "statuses": used, "excluded": excluded, "style": style, "base": base, "rates": rates,
        "direction": direction, "rounding": rng.choice(["per-row", "per-total"]),
    }


def _dataset(rng, P, n_accounts, n_rows, taken=()):
    """Logical rows of one dataset. About half of the accounts get ids with several
    versions, half get excluded statuses and half get foreign-currency rows."""
    accounts = []
    while len(accounts) < n_accounts:
        name = "-".join([rng.choice(["ACC", "OPS", "TR", "FIN", "RSV"]),
                         rng.choice(["EU", "US", "AP", "X"]), str(rng.randrange(10, 99))])
        if name not in accounts and name not in taken:
            accounts.append(name)
    half = max(1, n_accounts // 2)
    with_versions = rng.sample(accounts, half)
    with_excluded = rng.sample(accounts, half)
    with_fx = rng.sample(accounts, half) if P["rates"] else []
    allowed = [status for status in P["statuses"] if status not in P["excluded"]]
    t0 = _util.EPOCH_2026 + rng.randrange(200) * 86400
    rows = []
    serial = rng.randrange(1000, 5000)
    while len(rows) < n_rows:
        account = rng.choice(accounts)
        serial += rng.randrange(1, 9)
        versions = rng.choice([2, 2, 3]) if account in with_versions and rng.random() < 0.3 else 1
        for when in sorted(rng.sample(range(t0, t0 + SPAN), versions)):
            foreign = account in with_fx and rng.random() < 0.4
            bad = account in with_excluded and rng.random() < 0.25
            rows.append({
                "id": f"TX{serial:06d}", "ts": when, "account": account,
                "cents": rng.randrange(100, 400000) * rng.choice([1, 1, -1]),
                "currency": rng.choice(sorted(P["rates"])) if foreign else P["base"],
                "status": rng.choice(P["excluded"] if bad else allowed),
            })
    rng.shuffle(rows)
    return rows


def _latest(rows):
    """The surviving row of every id (latest timestamp)."""
    best = {}
    for row in rows:
        if row["id"] not in best or row["ts"] > best[row["id"]]["ts"]:
            best[row["id"]] = row
    return list(best.values())


def _to_base(value, currency, P, rates):
    """Convert a Decimal amount to the base currency following the instance rules."""
    if currency != P["base"]:
        rate = Decimal(str(rates[currency]))
        value = value * rate if P["direction"] == "multiply" else value / rate
    return value.quantize(CENT, ROUND_HALF_UP) if P["rounding"] == "per-row" else value


def _totals(rows, P, latest_only=True, drop_excluded=True):
    """Exact per-account totals of the logical rows. With the default flags this is the
    hidden truth; the flags switch single rules off to test that they matter."""
    totals = {account: Decimal(0) for account in sorted({row["account"] for row in rows})}
    for row in _latest(rows) if latest_only else rows:
        if not drop_excluded or row["status"] not in P["excluded"]:
            totals[row["account"]] += _to_base(Decimal(row["cents"]) / 100, row["currency"], P, P["rates"])
    return {account: float(total.quantize(CENT, ROUND_HALF_UP)) + 0.0 for account, total in totals.items()}


def _covers_quirks(rows, P):
    """True when every rule changes the result of this dataset (latest version, status
    filter, conversion direction) and negative and four-digit amounts both occur."""
    answer = _totals(rows, P)
    wrong = [_totals(rows, P, latest_only=False), _totals(rows, P, drop_excluded=False)]
    if P["rates"]:
        wrong.append(_totals(rows, dict(P, direction="divide" if P["direction"] == "multiply" else "multiply")))
    kept = _latest(rows)
    return (answer not in wrong and any(row["cents"] < 0 for row in kept)
            and any(abs(row["cents"]) >= 100000 for row in kept))


def _amount_text(cents, currency, style):
    """Render integer cents in the instance amount style."""
    whole, frac = divmod(abs(cents), 100)
    text = f"{whole:,}".replace(",", style["thousands"]) + style["decimal"] + f"{frac:02d}"
    if style["decoration"] == "symbol-prefix":
        text = SYMBOLS[currency] + text
    elif style["decoration"] == "code-prefix":
        text = f"{currency} {text}"
    elif style["decoration"] == "code-suffix":
        text = f"{text} {currency}"
    if cents >= 0:
        return text
    return {"minus": f"-{text}", "parentheses": f"({text})", "trailing-minus": f"{text}-"}[style["negative"]]


def _messy(rng, name):
    """An account id with random letter case and surrounding spaces."""
    name = rng.choice([name, name.lower(), name.title(), "".join(rng.choice([c, c.lower()]) for c in name)])
    return rng.choice(["", "", " ", "  "]) + name + rng.choice(["", "", " ", "  "])


def _memo(rng, P):
    """Free text for the level 3 memo column; often contains the delimiter or a quote."""
    words = ["invoice", "refund", "batch", "fee", "transfer", "correction", "payroll"]
    text = f"{rng.choice(words)} {rng.randrange(100, 999)}"
    roll = rng.random()
    if roll < 0.35:
        text += f"{P['delim']} see {rng.choice(words)}"
    elif roll < 0.45:
        text = f'"{text}" {rng.choice(words)}'
    return text


def _write_dataset(root, rng, rows, P, n_files):
    """Write the transaction files (and rates.json) of one dataset under root/data."""
    chunks = [[] for _ in range(n_files)]
    for row in rows:
        chunks[rng.randrange(n_files)].append(row)
    for number, chunk in enumerate(chunks, 1):
        out = io.StringIO()
        writer = csv.writer(out, delimiter=P["delim"], lineterminator="\n")
        writer.writerow(P["columns"])
        for row in chunk:
            cells = {
                "id": row["id"], "timestamp": _util.fmt_ts(row["ts"], P["ts"]),
                "account": _messy(rng, row["account"]), "currency": row["currency"],
                "amount": _amount_text(row["cents"], row["currency"], P["style"]),
                "status": row["status"], "memo": _memo(rng, P),
            }
            writer.writerow([cells[column] for column in P["columns"]])
        _util.write_text(root / "data" / f"part-{number:02d}.txt", out.getvalue())
    if P["rates"]:
        rates = {P["base"]: 1.0, **P["rates"]}
        _util.write_text(root / "data" / "rates.json", json.dumps(rates, indent=1) + "\n")


def _format_md(P):
    """FORMAT.md text: the data format and every rule parameter of the instance."""
    style, memo = P["style"], "memo" in P["columns"]
    lines = [
        "# FORMAT: ledger files (this instance)", "",
        "Every parameter below belongs to this instance only. `example/` uses exactly the same rules.", "",
        "## Files",
        "- `data/part-NN.txt`: transaction rows, UTF-8, one row per line. The first line of every file"
        " is a header naming the columns; the column order is the same in all files.",
        f"- Delimiter (JSON string): {json.dumps(P['delim'])}",
    ]
    if memo:
        lines.append("- A field that contains the delimiter or a double quote is wrapped in double quotes,"
                     " CSV style (a double quote inside such a field is doubled). Only `memo` needs this.")
    if P["rates"]:
        lines.append("- `data/rates.json`: one JSON object mapping currency code to exchange rate (rule 3).")
    lines += [
        "", "## Columns",
        "- `id`: transaction id. The same id can occur on several rows, in one file or across files (rule 1).",
        "- `timestamp`: UTC, see Timestamp.",
        "- `account`: account id, written with random letter case and spaces around it. Normalise it:"
        " strip the spaces, then upper-case. ` acc-eu-12 ` is account `ACC-EU-12`.",
        "- `amount`: signed amount in the row's currency, always with 2 decimals, see Amount style.",
        "- `currency`: currency code of the amount.",
        "- `status`: lower-case word.",
    ]
    if memo:
        lines.append("- `memo`: free text. Ignore it.")
    lines += [
        "", "## Timestamp",
        f"- Timestamp pattern: {P['ts']}",
        "",
        "Python strptime notation (`epoch` means integer seconds since 1970-01-01T00:00:00Z)."
        f" Example: `{_util.fmt_ts(_util.EPOCH_2026 + 6254813, P['ts'])}` is 2026-03-14T09:26:53Z."
        " Compare timestamps as points in time, not as text.",
        "", "## Amount style",
        f"- Thousands separator (JSON string): {json.dumps(style['thousands'])}",
        f"- Decimal mark (JSON string): {json.dumps(style['decimal'])}",
        f"- Negative style: {style['negative']}",
        f"- Currency decoration: {style['decoration']}",
        "",
        "Negative styles: `minus` = leading `-`; `parentheses` = the whole field in `( )`;"
        " `trailing-minus` = `-` at the end. Decorations: `none`; `symbol-prefix` = currency symbol"
        " before the number; `code-prefix` / `code-suffix` = currency code and one space before / after"
        " the number. A decoration only repeats the `currency` column."
        f" Examples: 1234.56 is written `{_amount_text(123456, P['base'], style)}` and -987.05 is written"
        f" `{_amount_text(-98705, P['base'], style)}`.",
        "", "## Rules (apply in this order)",
        "1. Latest version wins. Among all rows that share an id (all files together) keep only the row"
        " with the latest timestamp and discard the others completely. Rows with the same id never have"
        " equal timestamps.",
        "2. Status filter. After rule 1, drop every kept row whose status is excluded. If the latest row"
        " of an id is excluded, that id counts nothing, even when an older row had another status.",
        "- Excluded statuses: " + ", ".join(f"`{status}`" for status in P["excluded"]),
        "3. Currency conversion to the base currency.",
        f"- Base currency: {P['base']}",
        f"- Rate direction: {P['direction']}",
        "",
        "`multiply`: base amount = amount * rates[currency]. `divide`: base amount = amount /"
        " rates[currency]. `none`: every row is already in the base currency and there is no rates"
        " file. Rows in the base currency are never converted.",
        "4. Rounding.",
        f"- Rounding: {P['rounding']}",
        "",
        "`per-row`: round every converted amount to 2 decimals, then add up. `per-total`: add up the"
        " unrounded converted amounts, then round each account total to 2 decimals. Halves round away"
        " from zero.",
        "5. Totals. Add up the base amounts of the remaining rows per normalised account. Every account"
        " that occurs in the data gets an entry (0.0 when none of its rows remain).",
    ]
    return "\n".join(lines) + "\n"


def generate(seed, workdir, level=2):
    """Write one ledger instance into workdir and return the hidden truth."""
    workdir, level = pathlib.Path(workdir), _util.clamp_level(level)
    P = _draw_params(_util.make_rng(FAMILY, seed, level, "params"), level)
    accounts, size, files = {1: ((6, 7), (150, 180), (4, 4)), 2: ((7, 9), (190, 250), (4, 6)),
                             3: ((9, 10), (250, 298), (5, 6))}[level]
    for attempt in range(200):
        rng = _util.make_rng(FAMILY, seed, level, f"main{attempt}")
        rows = _dataset(rng, P, rng.randint(*accounts), rng.randint(*size))
        if _covers_quirks(rows, P):
            break
    answer = _totals(rows, P)
    for attempt in range(500):
        ex_rng = _util.make_rng(FAMILY, seed, level, f"example{attempt}")
        ex_rows = _dataset(ex_rng, P, 3, 16, tuple(answer))
        if _covers_quirks(ex_rows, P):
            break
    _write_dataset(workdir, rng, rows, P, rng.randint(*files))
    _write_dataset(workdir / "example", ex_rng, ex_rows, P, 2)
    _util.write_text(workdir / "example" / "expected.json", json.dumps(_totals(ex_rows, P), indent=1) + "\n")
    _util.write_text(workdir / "FORMAT.md", _format_md(P))
    _util.write_text(workdir / "TASK.md", TASK)
    return {"family": FAMILY, "level": level, "answer": answer, "params": P}


def check(workdir, truth, run_py=None):
    """Fraction of truth accounts whose answered total is within 0.011."""
    try:
        answer = _util.load_json_file(pathlib.Path(workdir) / "answer.json")
        expected = truth["answer"]
        if not isinstance(answer, dict) or not expected:
            return 0.0
        good = sum(1 for account, total in expected.items()
                   if _util.real_number(answer.get(account)) and abs(answer[account] - total) <= 0.011)
        return good / len(expected)
    except Exception:
        return 0.0


def _read_params(text):
    """Recover the rule parameters from FORMAT.md."""
    return {
        "delim": json.loads(_util.grab(text, "Delimiter (JSON string)")),
        "ts": _util.grab(text, "Timestamp pattern"),
        "decimal": json.loads(_util.grab(text, "Decimal mark (JSON string)")),
        "excluded": re.findall(r"`([^`]+)`", _util.grab(text, "Excluded statuses")),
        "base": _util.grab(text, "Base currency"),
        "direction": _util.grab(text, "Rate direction"),
        "rounding": _util.grab(text, "Rounding"),
    }


def _solve(workdir, sloppy=False):
    """Solve from the files alone. The sloppy variant skips the latest-version rule."""
    workdir = pathlib.Path(workdir)
    P = _read_params((workdir / "FORMAT.md").read_text(encoding="utf-8"))
    rates = {}
    if P["direction"] != "none":
        rates = json.loads((workdir / "data" / "rates.json").read_text(encoding="utf-8"), parse_float=Decimal)
    rows = []
    for path in sorted((workdir / "data").glob("part-*.txt")):
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle, delimiter=P["delim"])
            header = next(reader)
            for record in reader:
                row = dict(zip(header, record))
                row["ts"] = _util.parse_ts(row["timestamp"], P["ts"])
                row["account"] = row["account"].strip().upper()
                rows.append(row)
    totals = {row["account"]: Decimal(0) for row in rows}
    for row in rows if sloppy else _latest(rows):
        if row["status"] in P["excluded"]:
            continue
        text = row["amount"]
        digits = "".join(ch for ch in text if ch.isdigit() or ch == P["decimal"])
        value = Decimal(digits.replace(P["decimal"], "."))
        if "(" in text or "-" in text:
            value = -value
        totals[row["account"]] += _to_base(value, row["currency"], P, rates)
    answer = {account: float(total.quantize(CENT, ROUND_HALF_UP)) for account, total in totals.items()}
    _util.write_text(workdir / "answer.json", json.dumps(answer, indent=1) + "\n")


def solve_from_files(workdir):
    """Reference solver: reads FORMAT.md and data/, writes the correct answer.json."""
    _solve(workdir)


def sloppy_solve(workdir):
    """Careless solver: parses everything but sums every row, ignoring the latest-version rule."""
    _solve(workdir, sloppy=True)
