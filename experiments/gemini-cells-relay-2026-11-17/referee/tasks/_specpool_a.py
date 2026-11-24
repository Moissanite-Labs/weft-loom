"""Spec pool, part A. Each entry describes one function to implement from scratch:

func      name of the function the cell must define in solution.py
impl      reference implementation impl(P, *args); self-contained (its source text is what
          the reference solver writes), raises ValueError for invalid input
defaults  the "usual" parameter values (what a careless solver would assume)
draw      draw(rng) -> full parameter dict for an instance
contract  contract(P) -> markdown lines stating the behaviour for these parameters
examples  examples(P, rng) -> three argument lists for the worked examples
tests     tests(P, rng) -> candidate argument lists for the hidden tests
"""

SPECS = {}


# ------------------------------------------------------------------ cron field

def impl_cron(P, expr):
    lo, hi = P["lo"], P["hi"]

    def number(text):
        if not (text.isascii() and text.isdigit()):
            raise ValueError("not a number")
        value = int(text)
        if not lo <= value <= hi:
            raise ValueError("out of range")
        return value

    values = set()
    for part in expr.split(","):
        body, slash, step_text = part.partition("/")
        step = 1
        if slash:
            if not (step_text.isascii() and step_text.isdigit()) or int(step_text) < 1:
                raise ValueError("bad step")
            step = int(step_text)
        if body == "*":
            sequence = list(range(lo, hi + 1))
        elif "-" in body:
            first, _, last = body.partition("-")
            a, b = number(first), number(last)
            if a <= b:
                sequence = list(range(a, b + 1))
            elif P["wrap"]:
                sequence = list(range(a, hi + 1)) + list(range(lo, b + 1))
            else:
                raise ValueError("descending range")
        else:
            value = number(body)
            if slash and not P["single_step"]:
                raise ValueError("a step needs a range")
            sequence = list(range(value, hi + 1)) if slash else [value]
        values.update(sequence[::step])
    return sorted(values)


def draw_cron(rng):
    lo, hi = rng.choice([(0, 23), (1, 31), (1, 12), (0, 6), (1, 7), (0, 99)])
    return {"lo": lo, "hi": hi, "wrap": rng.random() < 0.6, "single_step": rng.random() < 0.6}


def contract_cron(P):
    wrap = ("the range wraps around: the sequence is A, A+1, ..., HI, LO, LO+1, ..., B."
            if P["wrap"] else "invalid.")
    single = ("`N/S` means the same as `N-HI/S`." if P["single_step"]
              else "invalid (a step needs `*` or a range).")
    return [
        "`expand_field(expr)` expands one cron-style field. `expr` is a str; return the list of"
        " distinct ints it denotes, in ascending order.",
        "",
        f"- Allowed values are the integers LO..HI inclusive, with LO = {P['lo']} and HI = {P['hi']}.",
        "- `expr` is one or more parts joined by `,`. The result is the union of all parts.",
        "- A part is a body, optionally followed by `/S`, where the step S is an integer >= 1.",
        "- Body `*`: the sequence LO, LO+1, ..., HI.",
        "- Body `A-B` with A <= B: the sequence A, A+1, ..., B.",
        f"- Body `A-B` with A > B: {wrap}",
        f"- Body `N` (one number): without a step it is just N. With a step: {single}",
        "- A step S keeps the 1st, (1+S)th, (1+2S)th, ... element of the body's sequence.",
        "- Numbers are one or more ASCII digits (leading zeros are fine). Spaces and any other"
        " characters are not allowed anywhere.",
        "- Invalid input: an empty `expr` or empty part, a malformed number or step, a step of 0, any"
        " number outside LO..HI, and every case called invalid above.",
    ]


def examples_cron(P, rng):
    lo, hi = P["lo"], P["hi"]
    mid = (lo + hi) // 2
    low, high = rng.randint(lo, mid), rng.randint(mid + 1, hi)
    return [[f"{low}-{high}/{rng.randint(2, 3)},{rng.randint(lo, hi)}"],
            [f"{rng.randint(mid + 1, hi)}-{rng.randint(lo, mid)}"], [f"{rng.randint(mid, hi - 2)}/2"]]


def tests_cron(P, rng):
    lo, hi = P["lo"], P["hi"]
    mid = (lo + hi) // 2
    a, b, step = rng.randint(lo, mid), rng.randint(mid + 1, hi), rng.randint(2, 4)
    return [[expr] for expr in [
        "*", f"*/{step}", f"{hi}-{lo}", f"{b}-{a}/2", f"{a}/{step}", str(hi + 1), f"{lo}-{hi + 1}",
        f"{lo}-{hi}/{step}", str(a), f"{a}-{b}", f"{b},{a},{a}-{mid}", "", f"{a},,{b}", f"{a}/0",
        f"{a}-", f" {a}", f"0{b}", f"{a}-{b}-{hi}", "*/x", f"{mid}-{mid}",
    ]]


SPECS["cron"] = {
    "func": "expand_field", "signature": "expand_field(expr)", "impl": impl_cron,
    "defaults": {"lo": 0, "hi": 59, "wrap": False, "single_step": False},
    "draw": draw_cron, "contract": contract_cron, "examples": examples_cron, "tests": tests_cron,
}


# ------------------------------------------------------------------ version ranges

def impl_vrange(P, versions, expr):
    def key(text):
        pieces = text.split(".")
        if not 1 <= len(pieces) <= 4 or not all(p.isascii() and p.isdigit() for p in pieces):
            raise ValueError("bad version")
        return tuple([int(p) for p in pieces] + [0] * (4 - len(pieces)))

    compat = P["compat_op"]
    operators = sorted(["==", "!=", ">=", "<=", ">", "<", compat], key=len, reverse=True)
    alternatives = []
    for alternative in expr.split(P["or_sep"]):
        clauses = []
        for clause in alternative.strip(" ").split(P["and_sep"]):
            clause = clause.strip(" ")
            op = next((o for o in operators if clause.startswith(o)), None)
            if op is None:
                raise ValueError("unknown operator")
            clauses.append((op, key(clause[len(op):])))
        alternatives.append(clauses)

    def holds(v, op, t):
        if op == compat:
            keep = P["compat_keep"]
            upper = list(t[:keep]) + [0] * (4 - keep)
            upper[keep - 1] += 1
            return t <= v < tuple(upper)
        return {"==": v == t, "!=": v != t, ">=": v >= t, "<=": v <= t, ">": v > t, "<": v < t}[op]

    best = None
    for text in versions:
        v = key(text)
        if any(all(holds(v, op, t) for op, t in clauses) for clauses in alternatives):
            if best is None or v > best[0]:
                best = (v, text)
    return best[1] if best else None


def draw_vrange(rng):
    return {"and_sep": rng.choice([",", "&", ";"]), "or_sep": rng.choice(["||", "|", " or "]),
            "compat_op": rng.choice(["~", "^", "~="]), "compat_keep": rng.choice([1, 2])}


def contract_vrange(P):
    op, keep = P["compat_op"], P["compat_keep"]
    bump = "the first component (major)" if keep == 1 else "the second component (minor)"
    sample = "2.0" if keep == 1 else "1.5"
    return [
        "`max_satisfying(versions, expr)`: `versions` is a list of version strings and `expr` a range"
        " expression. Return the highest version in the list that satisfies `expr` (the original"
        " string), or `None` when none does.",
        "",
        "- A version is 1 to 4 non-negative integers (ASCII digits) joined by `.`. Versions compare"
        " component by component as numbers; missing components count as 0 (`1.2` equals `1.2.0`).",
        f"- `expr` is one or more alternatives separated by `{P['or_sep']}` (OR). An alternative is one"
        f" or more clauses separated by `{P['and_sep']}` (AND). A version satisfies `expr` when it"
        " satisfies every clause of at least one alternative.",
        "- Spaces around an alternative and around a clause are ignored. A clause is an operator"
        " directly followed by a version.",
        f"- Operators: `>=`, `<=`, `>`, `<`, `==`, `!=` with their usual meaning, and `{op}`"
        " (compatible with). Where two operators fit the start of a clause, the longer one is meant.",
        f"- `{op}V` means: version >= V and version < U, where U is V with {bump} raised by 1 and all"
        f" later components set to 0. Example: `{op}1.4.2` means >= 1.4.2 and < {sample}.",
        "- Invalid input: an empty clause, a clause without a known operator, a malformed version in"
        " `expr` or in `versions`. Other separators are not recognised, so they make a clause"
        " malformed.",
        "- No two versions in the list are equal.",
    ]


def _versions(rng):
    """Nine distinct versions of mixed lengths: (ascending list, shuffled list, pivot).
    The pivot is a `major.minor` that has a later minor of the same major in the list, so
    that the compatible-with operator gives different answers for different settings."""
    while True:
        found = {}
        while len(found) < 9:
            parts = [rng.randrange(0, 4), rng.randrange(0, 13), rng.randrange(0, 10), rng.randrange(1, 5)]
            parts = parts[:rng.choice([2, 3, 3, 3, 4])]
            found.setdefault(tuple(parts + [0] * (4 - len(parts))), ".".join(str(p) for p in parts))
        keys = sorted(found)
        pivots = [k for k in keys if any(o[0] == k[0] and o[1] > k[1] for o in keys)]
        if pivots:
            ordered = [found[k] for k in keys]
            return ordered, rng.sample(ordered, len(ordered)), f"{pivots[0][0]}.{pivots[0][1]}"


def examples_vrange(P, rng):
    low = f"1.4.{rng.randrange(0, 5)}"
    listing = [low, f"1.4.{rng.randrange(5, 10)}", "1.5", f"2.0.{rng.randrange(1, 10)}", f"0.{rng.randrange(1, 10)}"]
    a, o, c = P["and_sep"], P["or_sep"], P["compat_op"]
    return [[listing, f">=1.4{a}<2.0"], [listing, f"{c}{low}"], [listing, f"<1.0{o}=={listing[2]}.0"]]


def tests_vrange(P, rng):
    a, o, c = P["and_sep"], P["or_sep"], P["compat_op"]
    ordered, listing, pivot = _versions(rng)
    low, mid, high, top = ordered[1], ordered[4], ordered[6], ordered[8]
    other_and = next(s for s in [",", "&", ";"] if s != a)
    other_or = next(s for s in ["||", " or ", "|"] if s != o and o not in s and s not in o)
    exprs = [
        f">={low}{a}<{high}", f">{low}{a}<={high}{a}!={high}", f"<{low}{o}=={mid}",
        f">={low}{a}<{mid}{o}>{top}", f"{c}{pivot}", f"{c}{mid}", f">={low}{a}{c}{low}",
        f">={low}{other_and}<{high}", f"<{low}{other_or}>={high}", f" <{high} ", f"!={top}",
        f">{top}", f"=={low}", f">={mid}{a}", f"=>{low}", ">=1.x", f"<={mid}", f"{c}{top}{o}<{low}",
    ]
    return [[listing, expr] for expr in exprs]


SPECS["vrange"] = {
    "func": "max_satisfying", "signature": "max_satisfying(versions, expr)", "impl": impl_vrange,
    "defaults": {"and_sep": ",", "or_sep": "||", "compat_op": "~", "compat_keep": 2},
    "draw": draw_vrange, "contract": contract_vrange, "examples": examples_vrange, "tests": tests_vrange,
}


# ------------------------------------------------------------------ tokenizer

def impl_tokenize(P, text):
    operators = sorted(P["operators"], key=len, reverse=True)
    extra, comment = P["ident_extra"], P["comment"]
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    digits = "0123456789"
    tokens = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in " \t":
            i += 1
        elif comment and text.startswith(comment, i):
            break
        elif ch in digits:
            j = i
            while j < len(text) and text[j] in digits:
                j += 1
            if P["decimals"] and text[j:j + 1] == "." and text[j + 1:j + 2] in tuple(digits):
                j += 1
                while j < len(text) and text[j] in digits:
                    j += 1
            tokens.append(["NUM", text[i:j]])
            i = j
        elif ch in letters or ch in extra:
            j = i
            while j < len(text) and (text[j] in letters or text[j] in digits or text[j] in extra):
                j += 1
            tokens.append(["ID", text[i:j]])
            i = j
        elif ch in "()":
            tokens.append(["LP" if ch == "(" else "RP", ch])
            i += 1
        else:
            op = next((o for o in operators if text.startswith(o, i)), None)
            if op is None:
                raise ValueError(f"unexpected character at {i}")
            tokens.append(["OP", op])
            i += len(op)
    return tokens


EXTRA_OPERATORS = ["**", "//", "%", "^", "<=", ">=", "==", "!=", "<", ">", "=", "->", "<<", "&&", "||",
                   "!", ":="]


def draw_tokenize(rng):
    operators = ["+", "-", "*", "/"] + rng.sample(EXTRA_OPERATORS, 4)
    comments = [c for c in ["#", ";", "//", "--"] if not any(o.startswith(c) for o in operators)]
    return {"operators": operators, "ident_extra": rng.choice(["$", "_$", "@_", ""]),
            "decimals": rng.random() < 0.5, "comment": rng.choice(comments)}


def contract_tokenize(P):
    extra = P["ident_extra"]
    comment = (f"if the text at this position starts with `{P['comment']}`, stop: the rest of the"
               " input is ignored." if P["comment"] else "this instance has no comments (skip this rule).")
    number = ("the longest run of digits; if that run is directly followed by `.` and at least one"
              " digit, the `.` and the following run of digits belong to the number too (`3.25` is one"
              " NUM; in `3.` and `3.x` the `.` is not part of it)" if P["decimals"]
              else "the longest run of digits. There are no decimal numbers: `.` is never part of a NUM")
    start = f"a letter or one of the characters `{extra}`" if extra else "a letter"
    more = f"letters, digits and the characters `{extra}`" if extra else "letters and digits"
    return [
        "`tokenize(text)` splits an expression into tokens. Return a list of `[kind, text]` pairs"
        " (2-element lists) in input order. Scan left to right; at each position apply the FIRST rule"
        " that matches:",
        "",
        "1. Space or tab: skip it.",
        f"2. Comment: {comment}",
        f"3. A digit starts a `NUM` token: {number}.",
        f"4. {start[0].upper() + start[1:]} starts an `ID` token: the longest run of {more}.",
        "5. `(` gives `[\"LP\", \"(\"]` and `)` gives `[\"RP\", \")\"]`.",
        "6. Operator: the LONGEST operator from the list below that starts at this position gives an"
        " `OP` token.",
        "7. Anything else is invalid input.",
        "",
        "- Operators: " + " ".join(f"`{op}`" for op in P["operators"]),
        "- Letters and digits are ASCII only. An empty or all-blank text gives `[]`.",
    ]


def examples_tokenize(P, rng):
    multi = max(P["operators"], key=len)
    name = rng.choice(["rate", "sum", "idx"]) + (P["ident_extra"][:1] + "1" if P["ident_extra"] else "2")
    tail = f" {P['comment']} note" if P["comment"] else ""
    return [[f"({rng.choice('abcd')} + {rng.randrange(10, 99)})*{name}"],
            [f"{rng.choice('xyz')}{multi}{rng.randrange(1, 9)}.5{tail}"], [f"{rng.choice('pqr')} ? b"]]


def tests_tokenize(P, rng):
    extra, comment = P["ident_extra"], P["comment"]
    multi = sorted((o for o in P["operators"] if len(o) > 1), key=len, reverse=True)
    singles = [o for o in P["operators"] if len(o) == 1]
    mark = extra[:1] or "_"
    probe = multi[0][0] if multi else "<"
    tests = [f"a{op}b" for op in multi[:3]]
    tests += [
        f"{mark}tmp{mark}1 + 2", f"total - 1 {comment or '#'} minus one", "7.25*(x - 0.5)",
        f"n{rng.choice(singles)}{rng.randrange(10, 99)}", "p_q + r$s", "3.x", f"{rng.randrange(100)} . 4",
        f"a {probe} b", "2**8 // 3", "a<=b != c", "x -- y", "left ; right", "   ", "f(g(1),2)",
        f"({rng.randrange(1, 9)}+{rng.randrange(1, 9)})*k9",
    ]
    return [[text] for text in tests]


SPECS["tokenize"] = {
    "func": "tokenize", "signature": "tokenize(text)", "impl": impl_tokenize,
    "defaults": {"operators": ["+", "-", "*", "/"], "ident_extra": "_", "decimals": True, "comment": ""},
    "draw": draw_tokenize, "contract": contract_tokenize, "examples": examples_tokenize,
    "tests": tests_tokenize,
}


# ------------------------------------------------------------------ column labels

def impl_colabel(P, value):
    alphabet, first = P["alphabet"], P["first"]
    size = len(alphabet)
    if isinstance(value, str):
        text = value.upper() if P["fold_case"] else value
        if not text or any(ch not in alphabet for ch in text):
            raise ValueError("bad label")
        number = 0
        for ch in text:
            number = number * size + alphabet.index(ch) + 1
        return number - 1 + first
    number = value - first + 1
    if number < 1:
        raise ValueError("below the first column")
    letters = []
    while number > 0:
        number, rest = divmod(number - 1, size)
        letters.append(alphabet[rest])
    return "".join(reversed(letters))


ALPHABETS = ["ABCDEFGHJKLMNPQRSTUVWXYZ", "ABCDEF", "ACGT", "XYZ", "ZYXWVUTSRQPONMLKJIHGFEDCBA",
             "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]


def draw_colabel(rng):
    return {"alphabet": rng.choice(ALPHABETS), "first": rng.choice([0, 1]), "fold_case": rng.random() < 0.5}


def contract_colabel(P):
    alphabet, first = P["alphabet"], P["first"]
    a, b, z = alphabet[0], alphabet[1], alphabet[-1]
    fold = ("lower-case letters in a label are accepted and mean the same as upper case."
            if P["fold_case"] else "labels are case-sensitive; lower-case letters are invalid.")
    return [
        "`convert(value)` converts between column numbers and column labels, spreadsheet style.",
        "",
        f"- Alphabet, in order: `{alphabet}` ({len(alphabet)} letters).",
        f"- The first column has number {first}.",
        f"- Labels in column order: first all one-letter labels in alphabet order (`{a}`, `{b}`, ...,"
        f" `{z}`), then all two-letter labels (`{a}{a}`, `{a}{b}`, ..., `{a}{z}`, `{b}{a}`, ...,"
        f" `{z}{z}`), then the three-letter labels (`{a}{a}{a}`, ...), and so on. So column {first} is"
        f" `{a}`, column {first + len(alphabet) - 1} is `{z}` and column {first + len(alphabet)} is"
        f" `{a}{a}`.",
        "- If `value` is an int: return the label (str) of that column. A number below the first"
        " column is invalid.",
        "- If `value` is a str: return the number (int) of that column. The empty string and a string"
        " with any character outside the alphabet are invalid.",
        f"- Letter case: {fold}",
    ]


def examples_colabel(P, rng):
    alphabet, first = P["alphabet"], P["first"]
    return [[first + len(alphabet) + rng.randrange(1, len(alphabet))], [rng.choice(alphabet[1:]) + rng.choice(alphabet)],
            [(rng.choice(alphabet) + rng.choice(alphabet)).lower()]]


def tests_colabel(P, rng):
    alphabet, first = P["alphabet"], P["first"]
    size = len(alphabet)
    word = "".join(rng.choice(alphabet) for _ in range(3))
    outside = next((ch for ch in "IOZQB" if ch not in alphabet), "-")
    return [[value] for value in [
        first, first + 1, first + size - 1, first + size, first + size * size + size - 1,
        first + size * size + size, rng.randrange(1000, 50000), alphabet[0], alphabet[-1],
        alphabet[-1] * 2, word, word.lower(), alphabet[0] + alphabet[2].lower(), first - 1, "",
        alphabet[0] + "1", alphabet[1] + outside, rng.randrange(60, 600),
    ]]


SPECS["colabel"] = {
    "func": "convert", "signature": "convert(value)", "impl": impl_colabel,
    "defaults": {"alphabet": "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "first": 1, "fold_case": False},
    "draw": draw_colabel, "contract": contract_colabel, "examples": examples_colabel,
    "tests": tests_colabel,
}
