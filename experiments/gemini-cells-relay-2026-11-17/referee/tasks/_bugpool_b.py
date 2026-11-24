"""Bugfix pool, part B. Same entry layout as _bugpool_a (source, bugs, contract, examples,
tests); an expected literal of "ValueError" means the expression must raise ValueError.
"""

SPECS = {}

SPECS["version"] = {
    "source": '''def _parts(version):
    return [int(piece) for piece in version.split(".")]


def compare_versions(a, b):
    """Compare dotted numeric versions: -1, 0 or 1; see SPEC.md."""
    left, right = _parts(a), _parts(b)
    length = max(len(left), len(right))
    left += [0] * (length - len(left))
    right += [0] * (length - len(right))
    for x, y in zip(left, right):
        if x != y:
            return -1 if x < y else 1
    return 0
''',
    "bugs": [
        ("    length = max(len(left), len(right))\n", "    length = min(len(left), len(right))\n"),
        ("    return [int(piece) for piece in version.split(\".\")]\n",
         "    return [piece for piece in version.split(\".\")]\n"),
    ],
    "contract": (
        "`compare_versions(a, b)`: `a` and `b` are version strings of one or more non-negative"
        " decimal integers separated by dots. Compare them component by component as numbers (so 10"
        " is greater than 9, and `01` equals `1`); a missing component counts as 0 (so `1.2` equals"
        " `1.2.0`). Return -1 if a < b, 0 if they are equal, 1 if a > b."),
    "examples": [
        ("compare_versions('1.2.3', '1.2.3')", "0"),
        ("compare_versions('2.0', '1.9')", "1"),
        ("compare_versions('1.2', '1.2.1')", "-1"),
    ],
    "tests": [
        ("compare_versions('1.2.3', '1.2.3')", "0"),
        ("compare_versions('1.2', '1.3')", "-1"),
        ("compare_versions('2.0', '1.9')", "1"),
        ("compare_versions('5.0.1', '5.0.0')", "1"),
        ("compare_versions('0.0.1', '0.0.1')", "0"),
        ("compare_versions('1.10', '1.9')", "1"),
        ("compare_versions('0.9', '0.10')", "-1"),
        ("compare_versions('1.2', '1.2.1')", "-1"),
        ("compare_versions('1.0.5', '1')", "1"),
        ("compare_versions('3', '3.0.0.1')", "-1"),
        ("compare_versions('4.5.6', '4.5')", "1"),
    ],
}

SPECS["wrap"] = {
    "source": '''def wrap_text(text, width):
    """Greedy word wrap into lines of at most width characters; see SPEC.md."""
    lines = []
    current = ""
    for word in text.split():
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
''',
    "bugs": [
        ("len(current) + 1 + len(word) <= width", "len(current) + 1 + len(word) < width"),
        ("len(current) + 1 + len(word) <= width", "len(current) + len(word) <= width"),
    ],
    "contract": (
        "`wrap_text(text, width)`: split `text` into words at whitespace and fill lines greedily: a"
        " word is appended to the current line, after one space, whenever the line stays at most"
        " `width` characters long (exactly `width` is allowed); otherwise it starts a new line. A"
        " word longer than `width` gets a line of its own, unbroken. Return the list of lines, without"
        " leading or trailing spaces; no words give `[]`."),
    "examples": [
        ("wrap_text('the quick brown fox', 10)", "['the quick', 'brown fox']"),
        ("wrap_text('aaa bbb ccc', 7)", "['aaa bbb', 'ccc']"),
        ("wrap_text('hello', 3)", "['hello']"),
    ],
    "tests": [
        ("wrap_text('hello', 10)", "['hello']"),
        ("wrap_text('the quick brown fox', 10)", "['the quick', 'brown fox']"),
        ("wrap_text('supercalifragilistic is long', 8)", "['supercalifragilistic', 'is long']"),
        ("wrap_text('aaa bbb ccc', 7)", "['aaa bbb', 'ccc']"),
        ("wrap_text('ab cd ef gh', 5)", "['ab cd', 'ef gh']"),
        ("wrap_text('  many   spaces here ', 11)", "['many spaces', 'here']"),
        ("wrap_text('one two three', 7)", "['one two', 'three']"),
        ("wrap_text('aaa bbb ccc', 6)", "['aaa', 'bbb', 'ccc']"),
        ("wrap_text('ab cd ef', 4)", "['ab', 'cd', 'ef']"),
        ("wrap_text('abc de fgh', 5)", "['abc', 'de', 'fgh']"),
        ("wrap_text('go to it', 4)", "['go', 'to', 'it']"),
    ],
}

SPECS["bsearch"] = {
    "source": '''def leftmost_index(items, target):
    """Smallest index of target in a sorted list, or -1; see SPEC.md."""
    low, high = 0, len(items)
    while low < high:
        mid = (low + high) // 2
        if items[mid] < target:
            low = mid + 1
        else:
            high = mid
    if low < len(items) and items[low] == target:
        return low
    return -1
''',
    "bugs": [
        ("    if low < len(items) and items[low] == target:\n", "    if items[low] == target:\n"),
        ("            high = mid\n", "            high = mid - 1\n"),
    ],
    "contract": (
        "`leftmost_index(items, target)`: `items` is a list sorted in ascending order, possibly empty"
        " and possibly with repeated values. Return the smallest index i with items[i] == target, or"
        " -1 when the target does not occur (also when it is smaller or larger than every item). Must"
        " not raise."),
    "examples": [
        ("leftmost_index([1, 2, 2, 2, 3], 2)", "1"),
        ("leftmost_index([1, 3, 5], 4)", "-1"),
        ("leftmost_index([10, 20, 30], 30)", "2"),
    ],
    "tests": [
        ("leftmost_index([1, 2, 2, 2, 3], 2)", "1"),
        ("leftmost_index([1, 3, 5], 0)", "-1"),
        ("leftmost_index([1, 2, 3, 4, 5, 6, 7, 8], 6)", "5"),
        ("leftmost_index([], 7)", "-1"),
        ("leftmost_index([1, 3, 5], 9)", "-1"),
        ("leftmost_index([10, 20, 30], 35)", "-1"),
        ("leftmost_index([5], 6)", "-1"),
        ("leftmost_index([1, 2, 3, 4, 5], 3)", "2"),
        ("leftmost_index([1, 2, 3, 4, 5, 6, 7, 8], 5)", "4"),
        ("leftmost_index([1, 1, 2, 3, 3, 3, 9], 3)", "3"),
        ("leftmost_index([2, 4, 6, 8, 10, 12], 4)", "1"),
    ],
}

SPECS["lru"] = {
    "source": '''class LRUCache:
    """Least-recently-used cache; see SPEC.md."""

    def __init__(self, capacity):
        self.capacity = capacity
        self._data = {}

    def get(self, key):
        if key not in self._data:
            return None
        value = self._data.pop(key)
        self._data[key] = value
        return value

    def put(self, key, value):
        self._data.pop(key, None)
        self._data[key] = value
        if len(self._data) > self.capacity:
            del self._data[next(iter(self._data))]

    def keys(self):
        return list(self._data)


def replay(capacity, operations):
    """Apply ("put", key, value) and ("get", key) tuples to a new cache; see SPEC.md."""
    cache = LRUCache(capacity)
    results = []
    for operation in operations:
        if operation[0] == "put":
            cache.put(operation[1], operation[2])
        else:
            results.append(cache.get(operation[1]))
    return results, cache.keys()
''',
    "bugs": [
        ("        value = self._data.pop(key)\n        self._data[key] = value\n",
         "        value = self._data[key]\n"),
        ("        self._data.pop(key, None)\n        self._data[key] = value\n",
         "        self._data[key] = value\n"),
    ],
    "contract": (
        "`LRUCache(capacity)` holds at most `capacity` (>= 1) keys. `get(key)` returns the stored"
        " value, or `None` for a missing key. `put(key, value)` inserts or overwrites. A successful"
        " `get` and every `put` (also an overwrite) make that key the most recently used. When a"
        " `put` leaves more than `capacity` keys, the least recently used key is evicted. `keys()`"
        " lists the keys from least to most recently used. `replay(capacity, operations)` applies"
        " `('put', key, value)` and `('get', key)` tuples to a new cache and returns the tuple"
        " (list of the `get` results, `keys()`)."),
    "examples": [
        ("replay(2, [('put', 'a', 1), ('put', 'b', 2), ('put', 'c', 3), ('get', 'a')])",
         "([None], ['b', 'c'])"),
        ("replay(2, [('put', 'a', 1), ('put', 'b', 2), ('get', 'a'), ('put', 'c', 3)])",
         "([1], ['a', 'c'])"),
        ("replay(1, [('put', 'a', 1), ('put', 'a', 2), ('get', 'a')])", "([2], ['a'])"),
    ],
    "tests": [
        ("replay(2, [('put', 'a', 1), ('put', 'b', 2), ('put', 'c', 3), ('get', 'a')])",
         "([None], ['b', 'c'])"),
        ("replay(1, [('put', 'a', 1), ('put', 'b', 2), ('get', 'a'), ('get', 'b')])", "([None, 2], ['b'])"),
        ("replay(2, [('put', 'a', 1), ('put', 'a', 2), ('get', 'a')])", "([2], ['a'])"),
        ("replay(2, [('put', 'a', 1), ('put', 'b', 2), ('get', 'a'), ('put', 'c', 3)])",
         "([1], ['a', 'c'])"),
        ("replay(2, [('put', 'a', 1), ('put', 'b', 2), ('get', 'a'), ('put', 'c', 3), ('get', 'b')])",
         "([1, None], ['a', 'c'])"),
        ("replay(3, [('put', 'a', 1), ('put', 'b', 2), ('put', 'c', 3), ('get', 'a'), ('get', 'b'),"
         " ('put', 'd', 4)])", "([1, 2], ['a', 'b', 'd'])"),
        ("replay(2, [('put', 'a', 1), ('put', 'b', 2), ('get', 'a')])", "([1], ['b', 'a'])"),
        ("replay(2, [('put', 'a', 1), ('put', 'b', 2), ('put', 'a', 10), ('put', 'c', 3)])",
         "([], ['a', 'c'])"),
        ("replay(2, [('put', 'a', 1), ('put', 'b', 2), ('put', 'a', 10), ('put', 'c', 3), ('get', 'a')])",
         "([10], ['c', 'a'])"),
        ("replay(3, [('put', 'a', 1), ('put', 'b', 2), ('put', 'c', 3), ('put', 'a', 9), ('put', 'd', 4)])",
         "([], ['c', 'a', 'd'])"),
        ("replay(2, [('put', 'a', 1), ('put', 'b', 2), ('put', 'a', 3)])", "([], ['b', 'a'])"),
    ],
}

SPECS["flatten"] = {
    "source": '''def flatten(items, depth=None):
    """Flatten nested lists up to depth levels (None = completely); see SPEC.md."""
    result = []
    for item in items:
        if isinstance(item, list) and (depth is None or depth > 0):
            deeper = None if depth is None else depth - 1
            result.extend(flatten(item, deeper))
        else:
            result.append(item)
    return result
''',
    "bugs": [
        ("(depth is None or depth > 0)", "(depth is None or depth >= 0)"),
        ("            deeper = None if depth is None else depth - 1\n",
         "            deeper = None if depth is None else depth\n"),
    ],
    "contract": (
        "`flatten(items, depth=None)`: `items` is a list whose elements may be lists, nested to any"
        " depth. Return a new list in which nested lists are replaced by their elements, in order."
        " `depth` limits how many levels of nesting are removed: 0 returns a shallow copy, 1 unpacks"
        " only the lists directly inside `items`, 2 also the lists inside those, and so on; `None`"
        " flattens completely. Only `list` values are unpacked."),
    "examples": [
        ("flatten([1, [2, [3, [4]]]])", "[1, 2, 3, 4]"),
        ("flatten([[1, 2], [3, 4]], 1)", "[1, 2, 3, 4]"),
        ("flatten([1, [2, [3, [4]]]], 1)", "[1, 2, [3, [4]]]"),
    ],
    "tests": [
        ("flatten([1, [2, [3, [4]]]])", "[1, 2, 3, 4]"),
        ("flatten([1, [2, [3, [4]]]], 3)", "[1, 2, 3, 4]"),
        ("flatten([[1, 2], [3, 4]], 1)", "[1, 2, 3, 4]"),
        ("flatten(['ab', ['cd']])", "['ab', 'cd']"),
        ("flatten([1, [2, [3]]], 5)", "[1, 2, 3]"),
        ("flatten([1, [2, [3, [4]]]], 0)", "[1, [2, [3, [4]]]]"),
        ("flatten([[1], [2]], 0)", "[[1], [2]]"),
        ("flatten([1, [2, [3, [4]]]], 1)", "[1, 2, [3, [4]]]"),
        ("flatten([1, [2, [3, [4]]]], 2)", "[1, 2, 3, [4]]"),
        ("flatten([[1, [2]], [[3]]], 1)", "[1, [2], [3]]"),
        ("flatten([[], [[]]], 1)", "[[]]"),
    ],
}

SPECS["basen"] = {
    "source": '''_DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"


def to_base(number, base):
    """Text of an int in the given base (2..36); see SPEC.md."""
    if not 2 <= base <= 36:
        raise ValueError("base must be in 2..36")
    if number == 0:
        return "0"
    digits = []
    value = abs(number)
    while value > 0:
        value, digit = divmod(value, base)
        digits.append(_DIGITS[digit])
    text = "".join(reversed(digits))
    return "-" + text if number < 0 else text
''',
    "bugs": [
        ("    if not 2 <= base <= 36:\n", "    if not 2 <= base < 36:\n"),
        ("    value = abs(number)\n", "    value = number\n"),
        ("    if number == 0:\n        return \"0\"\n    digits = []\n", "    digits = []\n"),
    ],
    "contract": (
        "`to_base(number, base)`: write the int `number` in the given `base` using the digits"
        " `0-9` then `a-z` (lower case), most significant digit first, without leading zeros. Zero"
        " is `'0'`. A negative number is the text of its absolute value with a leading `-`. Bases"
        " 2 to 36 inclusive are valid; any other base raises `ValueError`."),
    "examples": [
        ("to_base(255, 16)", "'ff'"),
        ("to_base(5, 2)", "'101'"),
        ("to_base(-255, 16)", "'-ff'"),
    ],
    "tests": [
        ("to_base(255, 16)", "'ff'"),
        ("to_base(0, 16)", "'0'"),
        ("to_base(35, 36)", "'z'"),
        ("to_base(36, 36)", "'10'"),
        ("to_base(1295, 36)", "'zz'"),
        ("to_base(-255, 16)", "'-ff'"),
        ("to_base(-1, 2)", "'-1'"),
        ("to_base(-1000, 10)", "'-1000'"),
        ("to_base(-36, 36)", "'-10'"),
        ("to_base(0, 2)", "'0'"),
        ("to_base(0, 10)", "'0'"),
        ("to_base(0, 36)", "'0'"),
    ],
}

SPECS["topwords"] = {
    "source": '''def top_words(words, k):
    """The k most frequent words, case-insensitively; see SPEC.md."""
    counts = {}
    for word in words:
        key = word.lower()
        counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts, key=lambda key: (-counts[key], key))
    return ranked[:k]
''',
    "bugs": [
        ("key=lambda key: (-counts[key], key))", "key=lambda key: -counts[key])"),
        ("        key = word.lower()\n", "        key = word\n"),
    ],
    "contract": (
        "`top_words(words, k)`: count the strings in the list `words` case-insensitively (`Tea` and"
        " `tea` are the same word) and return the `k` most frequent words in lower case, most"
        " frequent first. Words with the same count are ordered alphabetically (ascending). If there"
        " are fewer than `k` distinct words, return them all."),
    "examples": [
        ("top_words(['a', 'b', 'a'], 1)", "['a']"),
        ("top_words(['one', 'two', 'two', 'three', 'three', 'three'], 2)", "['three', 'two']"),
        ("top_words(['pear', 'apple', 'pear', 'apple', 'fig'], 2)", "['apple', 'pear']"),
    ],
    "tests": [
        ("top_words(['a', 'b', 'a'], 1)", "['a']"),
        ("top_words(['x', 'y', 'x', 'z', 'y'], 3)", "['x', 'y', 'z']"),
        ("top_words(['one', 'two', 'two', 'three', 'three', 'three'], 2)", "['three', 'two']"),
        ("top_words(['b', 'a'], 2)", "['a', 'b']"),
        ("top_words(['pear', 'apple', 'pear', 'apple', 'fig'], 2)", "['apple', 'pear']"),
        ("top_words(['d', 'c', 'b', 'a'], 2)", "['a', 'b']"),
        ("top_words(['z', 'y', 'z', 'y', 'x'], 5)", "['y', 'z', 'x']"),
        ("top_words(['Tea', 'tea', 'TEA', 'milk'], 1)", "['tea']"),
        ("top_words(['Go', 'go', 'stop'], 2)", "['go', 'stop']"),
        ("top_words(['b', 'B', 'a'], 2)", "['b', 'a']"),
        ("top_words(['Hi', 'hi', 'yo', 'Yo', 'YO'], 1)", "['yo']"),
    ],
}
