"""Bugfix pool, part A. Each entry describes one small module:

source    correct module text
bugs      list of (old, new) text replacements; each plants one realistic bug
contract  the SPEC.md paragraph for the module
examples  worked examples for SPEC.md as (expression, expected literal)
tests     hidden assertions as (expression, expected literal)

An expected literal of "ValueError" means the expression must raise ValueError.
"""

SPECS = {}

SPECS["intervals"] = {
    "source": '''def merge_intervals(intervals):
    """Merge overlapping or touching intervals; see SPEC.md."""
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
''',
    "bugs": [
        ("start <= merged[-1][1]", "start < merged[-1][1]"),
        ("merged[-1][1] = max(merged[-1][1], end)", "merged[-1][1] = end"),
        ("in sorted(intervals):", "in intervals:"),
    ],
    "contract": (
        "`merge_intervals(intervals)`: `intervals` is a list of `[start, end]` pairs of ints with"
        " start <= end, in any order, possibly empty. Return a new list of `[start, end]` lists sorted"
        " by start, in which intervals that overlap or touch (one ends exactly where another starts)"
        " are merged into one."),
    "examples": [
        ("merge_intervals([[1, 3], [2, 6], [8, 10]])", "[[1, 6], [8, 10]]"),
        ("merge_intervals([[1, 2], [2, 3]])", "[[1, 3]]"),
        ("merge_intervals([[6, 8], [1, 9]])", "[[1, 9]]"),
    ],
    "tests": [
        ("merge_intervals([[1, 3], [2, 6], [8, 10]])", "[[1, 6], [8, 10]]"),
        ("merge_intervals([[1, 2], [2, 3]])", "[[1, 3]]"),
        ("merge_intervals([[1, 5], [5, 5], [5, 9]])", "[[1, 9]]"),
        ("merge_intervals([[0, 0], [0, 0]])", "[[0, 0]]"),
        ("merge_intervals([[1, 10], [2, 3]])", "[[1, 10]]"),
        ("merge_intervals([[1, 10], [2, 3], [9, 12]])", "[[1, 12]]"),
        ("merge_intervals([[1, 9], [2, 4], [3, 5]])", "[[1, 9]]"),
        ("merge_intervals([[8, 10], [1, 3], [2, 6]])", "[[1, 6], [8, 10]]"),
        ("merge_intervals([[5, 6], [1, 2], [2, 5]])", "[[1, 6]]"),
        ("merge_intervals([[2, 3], [1, 10]])", "[[1, 10]]"),
        ("merge_intervals([[1, 4], [0, 2], [3, 5]])", "[[0, 5]]"),
        ("merge_intervals([[4, 5], [1, 2]])", "[[1, 2], [4, 5]]"),
    ],
}

SPECS["rle"] = {
    "source": '''def rle_encode(text):
    """Run-length encode text; see SPEC.md."""
    out = []
    run = 0
    previous = ""
    for ch in text:
        if ch == previous:
            run += 1
        else:
            if run:
                out.append(f"{run}{previous}")
            previous = ch
            run = 1
    if run:
        out.append(f"{run}{previous}")
    return "".join(out)


def rle_decode(code):
    """Inverse of rle_encode; see SPEC.md."""
    out = []
    count = ""
    for ch in code:
        if ch.isdigit():
            count += ch
        else:
            out.append(ch * int(count))
            count = ""
    return "".join(out)
''',
    "bugs": [
        ("            count += ch\n", "            count = ch\n"),
        ("    if run:\n        out.append(f\"{run}{previous}\")\n    return",
         "    if run > 1:\n        out.append(f\"{run}{previous}\")\n    return"),
    ],
    "contract": (
        "`rle_encode(text)`: `text` has no digits. Every run of n equal characters c becomes the"
        " decimal count n followed by c; the count is always written, also when it is 1. The empty"
        " string encodes to the empty string. `rle_decode(code)` is the exact inverse; counts can"
        " have several digits."),
    "examples": [
        ("rle_encode('aaabcc')", "'3a1b2c'"),
        ("rle_decode('3a1b2c')", "'aaabcc'"),
        ("rle_decode('12x')", "'xxxxxxxxxxxx'"),
    ],
    "tests": [
        ("rle_encode('aaabcc')", "'3a1b2c'"),
        ("rle_encode('a')", "'1a'"),
        ("rle_encode('aab')", "'2a1b'"),
        ("rle_encode('abc')", "'1a1b1c'"),
        ("rle_encode('x' * 12)", "'12x'"),
        ("rle_encode('aa' + 'b' * 11 + 'c')", "'2a11b1c'"),
        ("rle_decode('3a1b2c')", "'aaabcc'"),
        ("rle_decode('12x')", "'x' * 12"),
        ("rle_decode('10a1b')", "'a' * 10 + 'b'"),
        ("rle_decode('100q')", "'q' * 100"),
        ("rle_decode(rle_encode('z' * 20 + 'y'))", "'z' * 20 + 'y'"),
    ],
}

SPECS["roman"] = {
    "source": '''_NUMERALS = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
    (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]
_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def to_roman(number):
    """Roman numeral of an int in 1..3999; see SPEC.md."""
    if not 1 <= number <= 3999:
        raise ValueError("number out of range")
    out = []
    for value, symbol in _NUMERALS:
        while number >= value:
            out.append(symbol)
            number -= value
    return "".join(out)


def from_roman(text):
    """Value of a valid Roman numeral; see SPEC.md."""
    total = 0
    for index, ch in enumerate(text):
        value = _VALUES[ch]
        if index + 1 < len(text) and _VALUES[text[index + 1]] > value:
            total -= value
        else:
            total += value
    return total
''',
    "bugs": [
        ("    (50, \"L\"), (40, \"XL\"), (10, \"X\"),", "    (50, \"L\"), (10, \"X\"),"),
        ("_VALUES[text[index + 1]] > value", "_VALUES[text[index + 1]] >= value"),
    ],
    "contract": (
        "`to_roman(number)`: standard Roman numeral (upper case, subtractive forms IV, IX, XL, XC, CD,"
        " CM) of an int in 1..3999; any other int raises `ValueError`. `from_roman(text)`: the int"
        " value of a valid numeral as produced by `to_roman`."),
    "examples": [
        ("to_roman(1994)", "'MCMXCIV'"),
        ("to_roman(49)", "'XLIX'"),
        ("from_roman('XIV')", "14"),
    ],
    "tests": [
        ("to_roman(1994)", "'MCMXCIV'"),
        ("to_roman(3999)", "'MMMCMXCIX'"),
        ("to_roman(40)", "'XL'"),
        ("to_roman(44)", "'XLIV'"),
        ("to_roman(1949)", "'MCMXLIX'"),
        ("to_roman(248)", "'CCXLVIII'"),
        ("to_roman(0)", "ValueError"),
        ("from_roman('MCMXCIV')", "1994"),
        ("from_roman('III')", "3"),
        ("from_roman('XXVII')", "27"),
        ("from_roman('MMXXVI')", "2026"),
        ("from_roman('CCCLXXX')", "380"),
    ],
}

SPECS["duration"] = {
    "source": '''_UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
_ORDER = "dhms"


def parse_duration(text):
    """Seconds of a duration such as '1h30m'; see SPEC.md."""
    total = 0
    digits = ""
    last = -1
    for ch in text:
        if ch.isdigit():
            digits += ch
            continue
        position = _ORDER.find(ch)
        if position <= last or not digits:
            raise ValueError(f"bad duration: {text!r}")
        total += int(digits) * _UNIT_SECONDS[ch]
        digits = ""
        last = position
    if digits or last < 0:
        raise ValueError(f"bad duration: {text!r}")
    return total
''',
    "bugs": [
        ("            digits += ch\n", "            digits = ch\n"),
        ("if position <= last or not digits:", "if position < last or not digits:"),
        ("    if digits or last < 0:\n", "    if last < 0:\n"),
    ],
    "contract": (
        "`parse_duration(text)`: `text` is one or more parts, each a non-negative decimal integer"
        " followed by a unit `d` (86400 s), `h` (3600 s), `m` (60 s) or `s`. Units must appear in the"
        " order d, h, m, s and each at most once. Return the total number of seconds. Raise"
        " `ValueError` for anything else: empty text, unknown unit, unit without a number, number"
        " without a unit, repeated or out-of-order unit."),
    "examples": [
        ("parse_duration('1d2h3m4s')", "93784"),
        ("parse_duration('1h30m')", "5400"),
        ("parse_duration('2h2h')", "ValueError"),
    ],
    "tests": [
        ("parse_duration('1h30m')", "5400"),
        ("parse_duration('45s')", "45"),
        ("parse_duration('90m')", "5400"),
        ("parse_duration('12h5s')", "43205"),
        ("parse_duration('1h1h')", "ValueError"),
        ("parse_duration('5x')", "ValueError"),
        ("parse_duration('3m4m')", "ValueError"),
        ("parse_duration('9d9d')", "ValueError"),
        ("parse_duration('1h30')", "ValueError"),
        ("parse_duration('7m7')", "ValueError"),
        ("parse_duration('2d5')", "ValueError"),
        ("parse_duration('3s9')", "ValueError"),
    ],
}

SPECS["spiral"] = {
    "source": '''def spiral_order(matrix):
    """Elements of a rectangular matrix in clockwise spiral order; see SPEC.md."""
    result = []
    if not matrix or not matrix[0]:
        return result
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        for col in range(left, right + 1):
            result.append(matrix[top][col])
        for row in range(top + 1, bottom + 1):
            result.append(matrix[row][right])
        if top < bottom:
            for col in range(right - 1, left - 1, -1):
                result.append(matrix[bottom][col])
        if left < right:
            for row in range(bottom - 1, top, -1):
                result.append(matrix[row][left])
        top, bottom, left, right = top + 1, bottom - 1, left + 1, right - 1
    return result
''',
    "bugs": [
        ("        if top < bottom:\n", "        if top <= bottom:\n"),
        ("        if left < right:\n", "        if left <= right:\n"),
    ],
    "contract": (
        "`spiral_order(matrix)`: `matrix` is a list of equally long rows (any number of rows and"
        " columns, possibly empty). Return its elements in clockwise spiral order starting at the top"
        " left: along the top row, down the right column, back along the bottom row, up the left"
        " column, then the same for the inner part. Every element appears exactly once."),
    "examples": [
        ("spiral_order([[1, 2, 3], [4, 5, 6], [7, 8, 9]])", "[1, 2, 3, 6, 9, 8, 7, 4, 5]"),
        ("spiral_order([[1, 2], [3, 4]])", "[1, 2, 4, 3]"),
        ("spiral_order([[1, 2, 3, 4], [5, 6, 7, 8]])", "[1, 2, 3, 4, 8, 7, 6, 5]"),
    ],
    "tests": [
        ("spiral_order([[1, 2, 3], [4, 5, 6], [7, 8, 9]])", "[1, 2, 3, 6, 9, 8, 7, 4, 5]"),
        ("spiral_order([[1, 2], [3, 4]])", "[1, 2, 4, 3]"),
        ("spiral_order([[7]])", "[7]"),
        ("spiral_order([[1, 2, 3]])", "[1, 2, 3]"),
        ("spiral_order([[1, 2]])", "[1, 2]"),
        ("spiral_order([[1, 2, 3, 4, 5]])", "[1, 2, 3, 4, 5]"),
        ("spiral_order([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])",
         "[1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]"),
        ("spiral_order([[1], [2], [3]])", "[1, 2, 3]"),
        ("spiral_order([[1], [2], [3], [4]])", "[1, 2, 3, 4]"),
        ("spiral_order([[1], [2], [3], [4], [5]])", "[1, 2, 3, 4, 5]"),
        ("spiral_order([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15]])",
         "[1, 2, 3, 6, 9, 12, 15, 14, 13, 10, 7, 4, 5, 8, 11]"),
    ],
}

SPECS["brackets"] = {
    "source": '''_PAIRS = {")": "(", "]": "[", "}": "{"}


def is_balanced(text):
    """True when every bracket in text is closed in the right order; see SPEC.md."""
    stack = []
    for ch in text:
        if ch in _PAIRS.values():
            stack.append(ch)
        elif ch in _PAIRS:
            if not stack or stack.pop() != _PAIRS[ch]:
                return False
    return not stack
''',
    "bugs": [
        ("    return not stack\n", "    return True\n"),
        ("if not stack or stack.pop() != _PAIRS[ch]:", "if stack and stack.pop() != _PAIRS[ch]:"),
    ],
    "contract": (
        "`is_balanced(text)`: return `True` when the brackets `()`, `[]` and `{}` in `text` are"
        " balanced: every opening bracket is closed by a bracket of the same type, in properly"
        " nested order, and no closing bracket comes without its opener. All other characters are"
        " ignored. Otherwise return `False`."),
    "examples": [
        ("is_balanced('([]{})')", "True"),
        ("is_balanced('(]')", "False"),
        ("is_balanced('x = (a + b) * [c]')", "True"),
    ],
    "tests": [
        ("is_balanced('([]{})')", "True"),
        ("is_balanced('(]')", "False"),
        ("is_balanced('x = (a + b) * [c]')", "True"),
        ("is_balanced('((')", "False"),
        ("is_balanced('a(b[c]d')", "False"),
        ("is_balanced('{[()]')", "False"),
        ("is_balanced('(()')", "False"),
        ("is_balanced(')')", "False"),
        ("is_balanced('())')", "False"),
        ("is_balanced('[]]')", "False"),
        ("is_balanced('()}')", "False"),
    ],
}
