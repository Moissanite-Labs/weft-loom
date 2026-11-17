"""Spec pool, part B. Same entry layout as _specpool_a (func, impl, defaults, draw,
contract, examples, tests)."""

SPECS = {}


# ------------------------------------------------------------------ reverse Polish

def impl_rpn(P, expr):
    def divide(a, b):
        if b == 0:
            raise ValueError("division by zero")
        quotient = a // b
        if P["division"] == "truncate" and quotient < 0 and quotient * b != a:
            quotient += 1
        return quotient

    binary = {
        "add": lambda a, b: a + b, "sub": lambda a, b: a - b, "mul": lambda a, b: a * b,
        "div": divide, "mod": lambda a, b: a - b * divide(a, b), "max": max, "min": min,
    }
    separator = P["separator"]
    tokens = expr.split() if separator == " " else [t.strip(" ") for t in expr.split(separator)]
    stack = []
    for token in tokens:
        digits = token[1:] if token.startswith("-") else token
        if digits.isascii() and digits.isdigit():
            stack.append(int(token))
            continue
        name = P["operators"].get(token)
        if name is None:
            raise ValueError(f"unknown token {token!r}")
        if name in ("neg", "abs", "dup"):
            if not stack:
                raise ValueError("stack underflow")
            a = stack.pop()
            stack += [a, a] if name == "dup" else [-a if name == "neg" else abs(a)]
        else:
            if len(stack) < 2:
                raise ValueError("stack underflow")
            b = stack.pop()
            a = stack.pop()
            stack += [b, a] if name == "swap" else [binary[name](a, b)]
    if len(stack) != 1:
        raise ValueError("the expression must leave exactly one value")
    return stack[0]


BASIC_TOKENS = [("add", ["+", "add", "&"]), ("sub", ["-", "sub"]), ("mul", ["*", "x", "mul"]),
                ("div", ["/", "div", ":"])]
EXTRA_TOKENS = [("mod", ["%", "mod"]), ("neg", ["~", "neg"]), ("abs", ["abs", "|"]), ("max", ["max", "^"]),
                ("min", ["min", "v"]), ("dup", ["dup", "d"]), ("swap", ["swap", "s"])]


def draw_rpn(rng):
    table = {rng.choice(tokens): name for name, tokens in BASIC_TOKENS + rng.sample(EXTRA_TOKENS, 3)}
    return {"operators": table, "division": rng.choice(["floor", "truncate"]),
            "separator": rng.choice([" ", ",", ";"])}


def contract_rpn(P):
    sep = P["separator"]
    floor = P["division"] == "floor"
    split = ("Tokens are separated by one or more spaces; spaces at the start and the end of `expr`"
             " are ignored." if sep == " " else
             f"Tokens are separated by `{sep}`. Spaces around a token are ignored. An empty token (two"
             " separators in a row, or an empty `expr`) is invalid.")
    rows = [f"- token `{token}` is the operation `{name}`" for token, name in P["operators"].items()]
    return [
        "`evaluate(expr)` evaluates an integer expression in reverse Polish (postfix) notation and"
        " returns an int.",
        "",
        f"- {split}",
        "- A token of ASCII digits, optionally with one leading `-`, is an integer: push it.",
        "- Any other token must be one of this instance's operator tokens (listed below, case-"
        "sensitive); every other token is invalid.",
        "- A binary operation pops b (the top of the stack), then a, and pushes its result. A unary"
        " operation pops a.",
        "",
        "Operator tokens of this instance:",
        "",
        *rows,
        "",
        "Meaning of the operations:",
        "",
        "- `add`: a + b. `sub`: a - b. `mul`: a * b. `max` / `min`: the larger / smaller of a and b.",
        "- `div`: the integer quotient a / b, rounded toward "
        + ("negative infinity (-7 div 2 = -4)." if floor else "zero (-7 div 2 = -3)."),
        "- `mod`: a - b * (a div b), with that same div (-7 mod 2 = " + ("1)." if floor else "-1)."),
        "- `neg` (unary): -a. `abs` (unary): the absolute value of a. `dup` (unary): pushes a twice."
        " `swap` (binary): pushes b, then a.",
        "- Invalid input: an unknown token, too few values on the stack for an operation, `div` or"
        " `mod` by zero, and an expression that does not leave exactly one value on the stack (an"
        " empty expression included).",
    ]


def _rpn_tools(P):
    """Token per operation name, and a function that joins tokens into an expression."""
    tokens = {name: token for token, name in P["operators"].items()}
    return tokens, lambda *items: P["separator"].join(str(item) for item in items)


def examples_rpn(P, rng):
    T, E = _rpn_tools(P)
    extra = [name for name in T if name not in ("add", "sub", "mul", "div")]
    p, q = rng.randrange(2, 10), rng.randrange(10, 60)
    third = {"mod": E(-7, p, T.get("mod")), "neg": E(q, T.get("neg"), p, T["add"]),
             "abs": E(p, q, T["sub"], T.get("abs")), "max": E(p, q, T.get("max")),
             "min": E(p, q, T.get("min")), "dup": E(q, T.get("dup"), T["mul"]),
             "swap": E(p, q, T.get("swap"), T["sub"])}[extra[0]] if extra else E(p, T["add"])
    return [[E(p, 3, q, T["mul"], T["add"])], [E(-(2 * q + 1), 2, T["div"])], [third]]


def tests_rpn(P, rng):
    T, E = _rpn_tools(P)
    sep = P["separator"]
    x, y = rng.randrange(11, 40), rng.randrange(2, 9)
    x += 1 if x % y == 0 else 0  # keep x / y inexact so that the division mode matters
    tests = [E(x, y, T["add"]), E(x, y, T["sub"]), E(y, x, 3, T["mul"], T["sub"]), E(-x, y, T["div"]),
             E(x, -y, T["div"]), E(x, y, T["div"])]
    extras = {"mod": E(-x, y, T.get("mod")), "neg": E(x, T.get("neg"), y, T["add"]),
              "abs": E(y, x, T["sub"], T.get("abs")), "max": E(x, y, T.get("max")),
              "min": E(x, y, T.get("min")), "dup": E(y, T.get("dup"), T["mul"]),
              "swap": E(y, x, T.get("swap"), T["sub"])}
    tests += [extras[name] for name in T if name in extras]
    usual = {"add": "+", "sub": "-", "mul": "*", "div": "/"}
    tests += [E(x, y, usual[name]) for name in usual if usual[name] not in P["operators"]][:2]
    tests += [E(x, T["add"]), E(x, y), E(x, 0, T["div"]), E(x, y, "?"), "",
              f" {x}  {sep}  {y} {sep} {T['mul']} ", str(x), E(x, 1, 2, T["add"], y, T["mul"], T["add"])]
    return [[text] for text in tests]


SPECS["rpn"] = {
    "func": "evaluate", "signature": "evaluate(expr)", "impl": impl_rpn,
    "defaults": {"operators": {"+": "add", "-": "sub", "*": "mul", "/": "div"}, "division": "floor",
                 "separator": " "},
    "draw": draw_rpn, "contract": contract_rpn, "examples": examples_rpn, "tests": tests_rpn,
}


# ------------------------------------------------------------------ path normalisation

def impl_normpath(P, path):
    sep, parent, current = P["separator"], P["parent"], P["current"]
    absolute = path.startswith(sep)
    kept = []
    for part in path.split(sep):
        if part == "" or part == current:
            continue
        if part != parent:
            kept.append(part)
        elif kept and kept[-1] != parent:
            kept.pop()
        elif not absolute:
            kept.append(part)
        elif P["above_root"] == "error":
            raise ValueError("path climbs above the root")
    if not kept:
        if absolute:
            return sep
        return current if P["empty_result"] == "current" else ""
    result = (sep if absolute else "") + sep.join(kept)
    if P["keep_trailing"] and path.endswith(sep):
        result += sep
    return result


NAMES = ["usr", "lib", "bin", "opt", "srv", "etc", "home", "data", "var", "tmp", "src", "doc", "log",
         "net", "app", "pkg"]


def draw_normpath(rng):
    return {"separator": rng.choice(["/", "\\", ":", ">"]), "parent": rng.choice(["..", "^", "<<"]),
            "current": rng.choice([".", "@", "_"]), "keep_trailing": rng.random() < 0.5,
            "empty_result": rng.choice(["current", "empty"]), "above_root": rng.choice(["ignore", "error"])}


def contract_normpath(P):
    sep, parent, current = P["separator"], P["parent"], P["current"]
    above = ("dropped (you cannot go above the root)" if P["above_root"] == "ignore"
             else "invalid input (the path climbs above the root)")
    empty = f"the current-directory token `{current}`" if P["empty_result"] == "current" else "the empty string"
    trailing = ("if the input ends with the separator and at least one component remains, the result"
                " ends with exactly one separator; otherwise it has none at the end." if P["keep_trailing"]
                else "the result never ends with a separator (except when it is the root itself).")
    return [
        "`normalize(path)` simplifies a path string. Pure text processing: never touch the file system.",
        "",
        f"- Separator: `{sep}`. Parent token: `{parent}`. Current-directory token: `{current}`.",
        "- Split `path` at every separator. Drop empty components and components equal to the"
        " current-directory token.",
        "- The path is absolute when it starts with the separator, otherwise relative.",
        "- Go through the remaining components from left to right and build a list. An ordinary"
        " component is appended. A parent token removes the last list entry when the list is not empty"
        " and that entry is not itself a parent token. Otherwise: in a relative path the parent token is"
        f" appended (leading parent tokens are kept); in an absolute path it is {above}.",
        "- Result: the list joined with single separators, with one leading separator when the path"
        " is absolute.",
        f"- When the list ends up empty: an absolute path gives the separator alone; a relative path"
        f" (also the empty string) gives {empty}.",
        f"- Trailing separator: {trailing}",
        "- A component is a token only when it equals the token exactly. All other characters,"
        " including the separators of other systems, are ordinary characters.",
    ]


def examples_normpath(P, rng):
    sep, parent, current = P["separator"], P["parent"], P["current"]
    a, b, c = rng.sample(NAMES, 3)
    return [[sep + sep.join([a, current, b, parent, c]) + sep],
            [sep.join([parent, a, parent, parent, b])], [sep + sep.join([parent, c])]]


def tests_normpath(P, rng):
    sep, up, dot = P["separator"], P["parent"], P["current"]
    other = next(s for s in ["/", ":", ">", "\\"] if s != sep)
    a, b, c = rng.sample(NAMES, 3)
    join = sep.join
    return [[path] for path in [
        join([a, dot, b]), join([a, b, up, c]), join([up, up, a]), sep + join([up, a]), join([a, up]),
        join([a, b]) + sep, sep + join([a, up, up, b]) + sep, join([dot, dot]), join([a, up, up, b]),
        sep + a + sep + dot + sep, sep + sep + a + sep + sep + b, join([a + other + b, up, c]),
        join([a, up + "x", b]), join([a, b, c]), a, "", sep, join([a, b, up, up, up, c]) + sep,
    ]]


SPECS["normpath"] = {
    "func": "normalize", "signature": "normalize(path)", "impl": impl_normpath,
    "defaults": {"separator": "/", "parent": "..", "current": ".", "keep_trailing": False,
                 "empty_result": "current", "above_root": "ignore"},
    "draw": draw_normpath, "contract": contract_normpath, "examples": examples_normpath,
    "tests": tests_normpath,
}


# ------------------------------------------------------------------ byte sizes

def impl_bytesfmt(P, n):
    if n < 0:
        raise ValueError("negative size")
    base, units, places = P["base"], P["units"], P["decimals"]
    gap = " " if P["space"] else ""
    k = 0
    while k + 1 < len(units) and n >= base ** (k + 1):
        k += 1
    if k == 0:
        return f"{n}{gap}{units[0]}"
    scale = 10 ** places
    scaled = (2 * n * scale + base ** k) // (2 * base ** k)
    text = str(scaled // scale)
    if places:
        text += "." + str(scaled % scale).rjust(places, "0")
        if P["strip_zeros"]:
            text = text.rstrip("0").rstrip(".")
    return f"{text}{gap}{units[k]}"


LADDERS = [["B", "KiB", "MiB", "GiB", "TiB"], ["bytes", "K", "M", "G"], ["o", "Ko", "Mo", "Go", "To"],
           ["B", "kB", "MB", "GB", "TB", "PB"], ["B", "KB", "MB", "GB", "TB"]]


def draw_bytesfmt(rng):
    return {"base": rng.choice([1000, 1024]), "units": rng.choice(LADDERS), "decimals": rng.choice([0, 1, 2]),
            "space": rng.random() < 0.5, "strip_zeros": rng.random() < 0.5}


def contract_bytesfmt(P):
    base, units, places = P["base"], P["units"], P["decimals"]
    gap = "exactly one space" if P["space"] else "nothing (no space)"
    strip = (" Then trailing zeros after the decimal point are removed, and the point too if nothing"
             " is left after it (`1.50` -> `1.5`, `2.00` -> `2`)." if P["strip_zeros"] and places else "")
    shown = {0: "0 decimal places (an integer, without a decimal point)", 1: "1 decimal place",
             2: "2 decimal places"}[places]
    return [
        "`format_size(n)` renders a byte count (an int) as text.",
        "",
        f"- Base: {base}. Units, smallest first: " + ", ".join(f"`{unit}`" for unit in units) + ".",
        "- A negative `n` is invalid input.",
        f"- Unit index k: the largest k with {base}**k <= n, but never beyond the last unit; k = 0"
        f" when n < {base}.",
        f"- k = 0: the result is n as a plain integer, then the unit `{units[0]}`. No decimals are shown"
        " for the first unit.",
        f"- k > 0: the value is n / {base}**k, rounded to {shown} with halves rounded up; it is always"
        f" shown with exactly that many decimals.{strip}",
        "- Round exactly: 2.5 -> 3, 1.25 -> 1.3, 1.125 -> 1.13. Binary floats and round-half-even get"
        " such ties wrong.",
        "- The unit is chosen from n before rounding and never changed afterwards, so a rounded value"
        f" equal to the base (like {base} of the unit `{units[1]}`) is possible and stays as it is.",
        f"- Between the number and the unit: {gap}.",
    ]


def examples_bytesfmt(P, rng):
    base = P["base"]
    return [[base - rng.randrange(1, 100)], [rng.randrange(1, 10) * base + base // 2],
            [rng.randrange(1, 10) * base * base + base * base // 8]]


def tests_bytesfmt(P, rng):
    base, count = P["base"], len(P["units"])
    tie = {0: 5 * base // 2, 1: 5 * base // 4, 2: 9 * base // 8}[P["decimals"]]
    return [[n] for n in [
        0, base, tie, base * base - 1, 2 * base, 5 * base * base + base * base // 4, 3 * base ** count,
        7 * base ** (count - 1), -1, rng.randrange(base, base * base), rng.randrange(base * base, base ** 3),
        rng.randrange(2, base), base * base, 1, -base, tie * base, rng.randrange(base ** 3, base ** 4),
    ]]


SPECS["bytesfmt"] = {
    "func": "format_size", "signature": "format_size(n)", "impl": impl_bytesfmt,
    "defaults": {"base": 1024, "units": ["B", "KB", "MB", "GB", "TB"], "decimals": 1, "space": True,
                 "strip_zeros": False},
    "draw": draw_bytesfmt, "contract": contract_bytesfmt, "examples": examples_bytesfmt,
    "tests": tests_bytesfmt,
}


# ------------------------------------------------------------------ key/value config lines

def impl_kvline(P, line):
    assign, marker, quote = P["assign"], P["comment"], P["quote"]
    text = line.strip()
    if not text or text.startswith(marker):
        return None
    key, found, rest = text.partition(assign)
    key = key.strip()
    if not found or not key:
        raise ValueError("no key or no assignment")
    if P["key_case"] != "keep":
        key = key.lower() if P["key_case"] == "lower" else key.upper()
    rest = rest.strip()
    if not rest.startswith(quote):
        cut = rest.find(marker)
        return [key, (rest if cut < 0 else rest[:cut]).strip()]
    out = []
    i = 1
    while True:
        if i >= len(rest):
            raise ValueError("unterminated quote")
        ch = rest[i]
        if P["escape"] == "backslash" and ch == "\\":
            if i + 1 >= len(rest):
                raise ValueError("dangling backslash")
            out.append(rest[i + 1])
            i += 2
        elif ch != quote:
            out.append(ch)
            i += 1
        elif P["escape"] == "doubled" and rest[i + 1:i + 2] == quote:
            out.append(quote)
            i += 2
        else:
            break
    tail = rest[i + 1:].strip()
    if tail and not tail.startswith(marker):
        raise ValueError("text after the closing quote")
    return [key, "".join(out)]


def draw_kvline(rng):
    return {"assign": rng.choice(["=", ":", ":=", "->"]), "comment": rng.choice(["#", ";", "//", "--"]),
            "quote": rng.choice(['"', "'", "`"]), "escape": rng.choice(["backslash", "doubled"]),
            "key_case": rng.choice(["keep", "lower", "upper"])}


def contract_kvline(P):
    assign, marker, quote = P["assign"], P["comment"], P["quote"]
    case = {"keep": "kept as written", "lower": "converted to lower case",
            "upper": "converted to upper case"}[P["key_case"]]
    escape = ("a backslash makes the character after it literal and is itself dropped (backslash +"
              " quote gives a quote, two backslashes give one backslash, backslash + `n` gives the"
              " letter n); a backslash as the very last character is invalid"
              if P["escape"] == "backslash" else
              "two quote characters in a row stand for one literal quote character; a single quote"
              " character closes the value; a backslash is an ordinary character")
    quote_name = {'"': 'the double quote `"`', "'": "the single quote `'`", "`": "the backtick"}[quote]
    return [
        "`parse_line(line)` parses one line of a config file. Return `None` for a line without data,"
        " otherwise the 2-element list `[key, value]` (two strings).",
        "",
        f"- Assignment token: `{assign}`. Comment marker: `{marker}`. Quote character: {quote_name}.",
        "1. Strip leading and trailing whitespace from `line`. If nothing is left, or it starts with"
        " the comment marker, return `None`.",
        "2. The key is the text before the FIRST assignment token, stripped of whitespace. A line"
        f" without an assignment token and an empty key are invalid. The key is {case}.",
        "3. Let R be the text after that assignment token, stripped of whitespace.",
        "4. Unquoted value (R does not start with the quote character): if R contains the comment"
        " marker, drop everything from its first occurrence on. The value is what remains, stripped"
        " of whitespace; it may be empty.",
        "5. Quoted value (R starts with the quote character): the value is the text between that"
        " quote and the closing quote, kept exactly (no stripping; comment markers and assignment"
        f" tokens inside are ordinary text). Escapes: {escape}. A missing closing quote is invalid."
        " After the closing quote only whitespace may follow, optionally followed by a comment (the"
        " marker and anything after it); any other text there is invalid.",
    ]


def examples_kvline(P, rng):
    assign, marker, quote = P["assign"], P["comment"], P["quote"]
    word = rng.choice(["hi", "hello", "hey", "good day"])
    key = rng.choice(["Max.Size", "Cache.Limit", "Log.Quota", "Disk.Min", "Heap.Cap", "Queue.Len"])
    return [[f"  {key} {assign} {rng.randrange(10, 999)} {marker} in MB"],
            [f"greeting{assign} {quote}{word} {marker} there {quote}"], [f"{marker} {assign} nothing here"]]


def tests_kvline(P, rng):
    a, c, q = P["assign"], P["comment"], P["quote"]
    esc = "\\" + q if P["escape"] == "backslash" else q + q
    other = "=" if a != "=" else ":"
    n = rng.randrange(1000, 9999)
    return [[line] for line in [
        f"name {a} value", f"Server.Name{a}Alpha {n}", f"path {a} {q}/usr/local  bin {q}",
        f"msg {a} {q}keep {c} this{q}", f"say {a} {q}a {esc}big{esc} word{q}", f"port {a} {n} {c} default",
        f"title {a} {q}x{q}   {c} note", f"empty {a}", f"   {c}indented", "", "no assignment here",
        f" {a} value", f"bad {a} {q}unterminated", f"bad {a} {q}x{q} junk", f"k {other} v",
        f"dir {a} {q}C:\\\\temp\\\\new{q}", f"expr {a} a{a}b", f"blank {a} {q}{q}",
        f"  Mixed_Key  {a}   spaced value  ",
    ]]


SPECS["kvline"] = {
    "func": "parse_line", "signature": "parse_line(line)", "impl": impl_kvline,
    "defaults": {"assign": "=", "comment": "#", "quote": '"', "escape": "backslash", "key_case": "keep"},
    "draw": draw_kvline, "contract": contract_kvline, "examples": examples_kvline, "tests": tests_kvline,
}
