"""stock: final on-hand and reserved quantities from an out-of-order inventory event log.

Quirks drawn per instance: JSON field names, the rule for a ship that exceeds on-hand
(reject or clamp), which of several lines with the same event id survives (first line or
lowest sequence); events must be sorted by a sequence field; SKU ids have messy case and
spaces. Level 1 has unique event ids; level 3 adds an optional pack multiplier field.
"""

import json
import pathlib

from . import _util

FAMILY = "stock"
FIELD_NAMES = {
    "id": ["id", "event_id", "eid", "uuid", "ref"],
    "seq": ["seq", "sequence", "lsn", "pos", "n"],
    "type": ["type", "kind", "op", "action", "event"],
    "sku": ["sku", "item", "product", "part", "sku_id"],
    "qty": ["qty", "quantity", "units", "count", "amount"],
    "pack": ["pack", "per_pack", "multiplier", "case_size"],
}
LABELS = {"id": "Event id field", "seq": "Sequence field", "type": "Type field", "sku": "SKU field",
          "qty": "Quantity field", "pack": "Pack field"}
# Quantity range and relative frequency per event type. The mix keeps stock low enough for
# ships and reservations to overflow now and then, without draining everything to zero.
QTY_RANGE = {"receive": (8, 40), "reserve": (5, 30), "release": (1, 8), "ship": (1, 22),
             "adjust": (1, 15), "audit": (1, 9)}
WEIGHTS = [22, 36, 6, 26, 10, 3]

TASK = """# Task: final stock levels

`data/events.jsonl` is a log of inventory events (receive, reserve, release, ship,
adjust). Replay it and report the final state of every SKU.

The log is messy on purpose and the rules are specific to this instance: the JSON field
names, how lines with a duplicate event id are resolved, the order in which events apply
(the file is not in order) and what happens when a ship asks for more than is on hand.
All of it is stated in `FORMAT.md`. Read it before writing any code.

## Output

Write `answer.json` in this directory (next to this file): one JSON object with one entry
per normalised SKU id, integers only. Shape:

    {"ITEM-A": {"on_hand": 37, "reserved": 5}, "ITEM-B": {"on_hand": 0, "reserved": 0}}

## Check your work

`example/` is a tiny log with the same layout and exactly the same rules
(`example/data/events.jsonl`). Its correct answer is in `example/expected.json`. Run your
solver on `example/` first and compare, then run it on `data/`.

## Scoring

Per SKU: half a point for the right `on_hand`, half for the right `reserved`. The score
is the mean over all SKUs.
"""


def _draw_params(rng, level):
    """Draw the rule parameters of one instance."""
    fields = {role: rng.choice(names) for role, names in FIELD_NAMES.items() if role != "pack" or level >= 3}
    return {"fields": fields, "ship_rule": rng.choice(["reject", "clamp"]),
            "dup_rule": "none" if level == 1 else rng.choice(["first-line", "lowest-seq"])}


def _apply(state, kind, q, ship_rule):
    """Apply one event to state = [on_hand, reserved]; return 1 when a ship overflowed."""
    on_hand, reserved = state
    overflow = 0
    if kind == "receive":
        on_hand += q
    elif kind == "reserve":
        if q <= on_hand - reserved:
            reserved += q
    elif kind == "release":
        reserved = max(0, reserved - q)
    elif kind == "ship":
        if q <= on_hand:
            on_hand, reserved = on_hand - q, max(0, reserved - q)
        else:
            overflow = 1
            if ship_rule == "clamp":
                on_hand, reserved = 0, 0
    elif kind == "adjust":
        on_hand = max(0, on_hand + q)
        reserved = min(reserved, on_hand)
    state[:] = [on_hand, reserved]
    return overflow


def _replay(lines, dup_rule, ship_rule, in_file_order=False, use_pack=True):
    """Final state per SKU and the number of overflowing ships. `lines` are event dicts in
    file order with keys id, seq, type, sku, qty and optionally pack."""
    kept = {}
    for index, event in enumerate(lines):
        key = index if dup_rule == "keep-all" else event["id"]
        if key not in kept or (dup_rule == "lowest-seq" and event["seq"] < kept[key]["seq"]):
            kept[key] = event
    events = list(kept.values())
    if not in_file_order:
        events.sort(key=lambda event: event["seq"])
    states, overflows = {}, 0
    for event in events:
        q = event["qty"] * (event.get("pack", 1) if use_pack else 1)
        overflows += _apply(states.setdefault(event["sku"], [0, 0]), event["type"], q, ship_rule)
    answer = {sku: {"on_hand": s[0], "reserved": s[1]} for sku, s in sorted(states.items())}
    return answer, overflows


def _events(rng, P, n_skus, n_events, taken=()):
    """Event lines in file order. About 40% of the SKUs are 'clean': their own events stay
    in sequence order in the file, have no duplicates and no pack field, so even a careless
    replay gets them right. About 30% carry duplicate event ids; the rest are merely out of
    order."""
    skus = []
    while len(skus) < n_skus:
        name = f"{rng.choice(['SKU', 'WID', 'PRT', 'BX'])}-{rng.randrange(1000, 9999)}{rng.choice('ABCDEFGH')}"
        if name not in skus and name not in taken:
            skus.append(name)
    n_clean = max(1, round(0.4 * n_skus))
    n_dup = 0 if P["dup_rule"] == "none" else max(1, round(0.3 * n_skus))
    per_sku = {sku: [("receive", rng.randrange(20, 80))] for sku in skus}
    for _ in range(n_events - n_skus):
        kind = rng.choices(list(QTY_RANGE), weights=WEIGHTS)[0]
        qty = rng.randrange(*QTY_RANGE[kind])
        if kind == "adjust" and rng.random() < 0.65:
            qty = -qty
        per_sku[rng.choice(skus)].append((kind, qty))
    stream = []
    for sku in skus:
        marks = sorted(rng.random() for _ in per_sku[sku])
        stream += [(mark, sku, kind, qty) for mark, (kind, qty) in zip(marks, per_sku[sku])]
    stream.sort()
    events, seq, ids = [], rng.randrange(100, 900), set()
    for _, sku, kind, qty in stream:
        seq += rng.randrange(1, 8)
        ident = None
        while ident is None or ident in ids:
            ident = f"ev-{rng.randrange(16 ** 6):06x}"
        ids.add(ident)
        event = {"id": ident, "seq": seq, "type": kind, "sku": sku, "qty": qty}
        if "pack" in P["fields"] and sku not in skus[:n_clean] and rng.random() < 0.45:
            event["pack"] = rng.choice([2, 3, 4, 6, 10, 12])
        events.append(event)
    lines = events[:]
    rng.shuffle(lines)
    for sku in skus[:n_clean]:
        slots = [index for index, event in enumerate(lines) if event["sku"] == sku]
        ordered = sorted((lines[index] for index in slots), key=lambda event: event["seq"])
        for slot, event in zip(slots, ordered):
            lines[slot] = event
    used = {event["seq"] for event in events}
    for sku in skus[n_clean:n_clean + n_dup]:
        own = [event for event in events if event["sku"] == sku]
        for original in rng.sample(own, min(3, len(own))):
            twin = dict(original)
            if rng.random() < 0.6:
                twin["seq"] = rng.choice([s for s in range(min(used), max(used) + 40) if s not in used])
                used.add(twin["seq"])
                twin["qty"] += rng.randrange(1, 6) * (1 if twin["qty"] > 0 else -1)
            lines.insert(rng.randrange(len(lines) + 1), twin)
    return lines


def _covers_quirks(lines, P, is_example):
    """True when every rule of the instance changes the result of this dataset: the ship
    rule, the duplicate rule, the sort order and the pack field. The example must also end
    with some stock left, so that it is a useful test for a solver."""
    dup, ship = P["dup_rule"], P["ship_rule"]
    answer, overflows = _replay(lines, dup, ship)
    wrong = [_replay(lines, dup, "clamp" if ship == "reject" else "reject")[0],
             _replay(lines, dup, ship, in_file_order=True)[0]]
    if dup != "none":
        wrong.append(_replay(lines, "lowest-seq" if dup == "first-line" else "first-line", ship)[0])
        wrong.append(_replay(lines, "keep-all", ship)[0])
    if "pack" in P["fields"]:
        wrong.append(_replay(lines, dup, ship, use_pack=False)[0])
    if is_example:
        stocked = sum(1 for state in answer.values() if state["on_hand"])
        return stocked >= 2 and any(state["reserved"] for state in answer.values()) and answer not in wrong
    return overflows >= 3 and answer not in wrong


def _write_events(root, rng, lines, P):
    """Write data/events.jsonl under root with the instance field names."""
    names, out = P["fields"], []
    for event in lines:
        sku = rng.choice([event["sku"], event["sku"].lower(), event["sku"].title()])
        sku = rng.choice(["", "", " ", "  "]) + sku + rng.choice(["", "", " "])
        record = [(names["id"], event["id"]), (names["seq"], event["seq"]), (names["type"], event["type"]),
                  (names["sku"], sku), (names["qty"], event["qty"])]
        if "pack" in event:
            record.append((names["pack"], event["pack"]))
        rng.shuffle(record)
        out.append(json.dumps(dict(record)))
    _util.write_text(root / "data" / "events.jsonl", "\n".join(out) + "\n")


def _format_md(P):
    """FORMAT.md text: field names and every rule of the instance."""
    names = P["fields"]
    lines = [
        "# FORMAT: inventory events (this instance)", "",
        "Every parameter below belongs to this instance only. `example/` uses exactly the same rules.", "",
        "## File",
        "`data/events.jsonl`: one JSON object per line, one event per object. The order of the keys"
        " inside an object is random and means nothing.",
        "", "## Fields",
        f"- {LABELS['id']}: `{names['id']}`",
        f"- {LABELS['seq']}: `{names['seq']}` (integer)",
        f"- {LABELS['type']}: `{names['type']}`",
        f"- {LABELS['sku']}: `{names['sku']}`",
        f"- {LABELS['qty']}: `{names['qty']}` (integer; negative only for `adjust`)",
    ]
    if "pack" in names:
        lines += [f"- {LABELS['pack']}: `{names['pack']}` (optional integer)", "",
                  "The quantity counts packs. Effective quantity q = quantity * pack. An event without"
                  " the pack field has pack 1."]
    else:
        lines += ["", "Effective quantity q = the quantity field."]
    lines += [
        "", "SKU ids are written with random letter case and spaces around them. Normalise them: strip"
        " the spaces, then upper-case (` wid-4821c ` is `WID-4821C`).",
        "", "## Step 1: duplicate event ids",
        f"- Duplicate rule: {P['dup_rule']}",
        "",
        "Several lines can carry the same event id; they can differ in sequence and quantity. Keep"
        " exactly one line per event id and drop the others completely. `first-line`: keep the line"
        " that comes first in the file. `lowest-seq`: keep the line with the smallest sequence value"
        " (if those are equal, the earlier line). `none`: event ids are unique in this instance.",
        "", "## Step 2: order",
        "The file is NOT in order. Sort the kept events by the sequence field, ascending. Kept events"
        " have distinct sequence values.",
        "", "## Step 3: apply",
        "Every SKU starts with on_hand = 0 and reserved = 0. Apply the events one by one:",
        "- `receive`: on_hand += q",
        "- `reserve`: if q <= on_hand - reserved then reserved += q; otherwise ignore the event (there"
        " is no partial reservation)",
        "- `release`: reserved = max(0, reserved - q)",
        "- `ship`: if q <= on_hand then on_hand -= q and reserved = max(0, reserved - q); otherwise the"
        " ship overflow rule applies",
        "- `adjust`: q may be negative. on_hand = max(0, on_hand + q); then, if reserved > on_hand,"
        " reserved = on_hand",
        "- any other type: ignore the event",
        f"- Ship overflow rule: {P['ship_rule']}",
        "",
        "`reject`: the ship event is ignored, nothing changes. `clamp`: everything on hand is shipped:"
        " on_hand = 0 and reserved = 0.",
        "", "## Result",
        "One entry per SKU that occurs in the file (normalised id), with its final `on_hand` and"
        " `reserved`.",
    ]
    return "\n".join(lines) + "\n"


def generate(seed, workdir, level=2):
    """Write one stock instance into workdir and return the hidden truth."""
    workdir, level = pathlib.Path(workdir), _util.clamp_level(level)
    P = _draw_params(_util.make_rng(FAMILY, seed, level, "params"), level)
    for attempt in range(200):
        rng = _util.make_rng(FAMILY, seed, level, f"main{attempt}")
        n_skus = rng.randint(*{1: (8, 9), 2: (8, 14), 3: (11, 14)}[level])
        n_events = rng.randint(*{1: (200, 280), 2: (300, 440), 3: (360, 440)}[level])
        lines = _events(rng, P, n_skus, n_events)
        if _covers_quirks(lines, P, is_example=False):
            break
    answer = _replay(lines, P["dup_rule"], P["ship_rule"])[0]
    for attempt in range(500):
        ex_rng = _util.make_rng(FAMILY, seed, level, f"example{attempt}")
        ex_lines = _events(ex_rng, P, 3, 24, tuple(answer))
        if _covers_quirks(ex_lines, P, is_example=True):
            break
    _write_events(workdir, rng, lines, P)
    _write_events(workdir / "example", ex_rng, ex_lines, P)
    expected = _replay(ex_lines, P["dup_rule"], P["ship_rule"])[0]
    _util.write_text(workdir / "example" / "expected.json", json.dumps(expected, indent=1) + "\n")
    _util.write_text(workdir / "FORMAT.md", _format_md(P))
    _util.write_text(workdir / "TASK.md", TASK)
    return {"family": FAMILY, "level": level, "answer": answer, "params": P}


def check(workdir, truth, run_py=None):
    """Mean over truth SKUs of 0.5 per correct field (on_hand, reserved)."""
    try:
        answer = _util.load_json_file(pathlib.Path(workdir) / "answer.json")
        return _util.score_fields(answer, truth["answer"], ("on_hand", "reserved"))
    except Exception:
        return 0.0


def _solve(workdir, sloppy=False):
    """Solve from the files alone. The sloppy variant replays the lines as they come: no
    duplicate handling, no sorting, no pack multiplier."""
    workdir = pathlib.Path(workdir)
    text = (workdir / "FORMAT.md").read_text(encoding="utf-8")
    names = {}
    for role, label in LABELS.items():
        try:
            names[role] = _util.grab(text, label).split("`")[1]
        except KeyError:
            pass
    lines = []
    for raw in (workdir / "data" / "events.jsonl").read_text(encoding="utf-8").split("\n"):
        if raw.strip():
            record = json.loads(raw)
            event = {role: record[name] for role, name in names.items() if name in record}
            event["sku"] = event["sku"].strip().upper()
            lines.append(event)
    if sloppy:
        answer = _replay(lines, "keep-all", _util.grab(text, "Ship overflow rule"), True, False)[0]
    else:
        answer = _replay(lines, _util.grab(text, "Duplicate rule"), _util.grab(text, "Ship overflow rule"))[0]
    _util.write_text(workdir / "answer.json", json.dumps(answer, indent=1) + "\n")


def solve_from_files(workdir):
    """Reference solver: reads FORMAT.md and data/events.jsonl, writes the correct answer.json."""
    _solve(workdir)


def sloppy_solve(workdir):
    """Careless solver: replays the file top to bottom, keeping duplicates and ignoring packs."""
    _solve(workdir, sloppy=True)
