#!/usr/bin/env python3
"""Mechanical diff of every edited build turn (standard library only).

Usage:
  python3 -I changes.py            -> writes changes.jsonl next to this script
  python3 -I changes.py --print    -> also prints the unified diff of every edited turn
  python3 -I changes.py --print RUN[:T]  -> print only that run (and turn)

All fields written by this script are mechanical. The keyword flags are computed on the
ADDED lines only (lines present in snap/<candidate> and not in snap/<base>), case-insensitive.
"""
import difflib
import json
import os
import re
import sys

RUNS = "/srv/gc-live/runs"
OUT = os.path.dirname(os.path.abspath(__file__))
SUFFIXES = ("-r0", "-r1", "-r2")

FAMILY_WORDS = ["ledger", "logwin", "bugfix", "rates.json", "maintenance", "currency",
                "delimiter", "FORMAT.md", "SPEC.md", "expected.json"]

RE_CAP = re.compile(r"^\s*([A-Za-z_]*CAP[A-Za-z_0-9]*)\s*=\s*([0-9_]+)", re.I)
# preload: agent.py code that walks, lists or globs the task folder (to put files into the prompt)
RE_PRELOAD = re.compile(
    r"(os\.walk\(|os\.scandir\(|glob\.glob\(|os\.listdir\(\s*(cwd|\"\.\"|'\.'|os\.getcwd))", re.I)
# multi-action: code that collects or loops over several actions from one reply (.py lines only)
RE_MULTI = re.compile(r"(parse_actions|parse_all|actions\.append\(|for\s+[\w,\s]+\s+in\s+actions\b)")
RE_FENCE = re.compile(r"(```|fence|code block|backtick|strip\(\s*[\"'][\"']?`)", re.I)


def tree(path):
    out = {}
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".pyc"):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, path)
            with open(full, "rb") as fh:
                out[rel] = fh.read()
    return out


def text(b):
    return b.decode("utf-8", "replace").splitlines()


def diff_turn(base_dir, cand_dir):
    a, b = tree(base_dir), tree(cand_dir)
    files_added = sorted(set(b) - set(a))
    files_removed = sorted(set(a) - set(b))
    files_changed = sorted(f for f in set(a) & set(b) if a[f] != b[f])
    per_file = {}
    added_lines = []      # (file, line)
    removed_lines = []
    udiff = []
    for f in sorted(set(files_added) | set(files_removed) | set(files_changed)):
        la, lb = text(a.get(f, b"")), text(b.get(f, b""))
        add = rem = 0
        for line in difflib.unified_diff(la, lb, "a/" + f, "b/" + f, lineterm="", n=2):
            udiff.append(line)
            if line.startswith("+") and not line.startswith("+++"):
                add += 1
                added_lines.append((f, line[1:]))
            elif line.startswith("-") and not line.startswith("---"):
                rem += 1
                removed_lines.append((f, line[1:]))
        per_file[f] = {"added": add, "removed": rem,
                       "bytes_before": len(a.get(f, b"")), "bytes_after": len(b.get(f, b""))}
    return {
        "files_changed": files_changed, "files_added": files_added, "files_removed": files_removed,
        "per_file": per_file,
        "lines_added": sum(v["added"] for v in per_file.values()),
        "lines_removed": sum(v["removed"] for v in per_file.values()),
        "bytes_before": sum(len(v) for v in a.values()),
        "bytes_after": sum(len(v) for v in b.values()),
    }, added_lines, removed_lines, udiff


def truncated_at_marker(prompt_bytes):
    """True when prompt.md shows the '<shell commands>' example line NOT followed by an @end line."""
    lines = [l.strip() for l in text(prompt_bytes)]
    for i, l in enumerate(lines):
        if l == "<shell commands>":
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if nxt != "@end":
                return True
    return False


def structure(base_dir, cand_dir):
    """Mechanical before/after facts about protocol and structure (not judgement)."""
    a, b = tree(base_dir), tree(cand_dir)
    aa, ba = a.get("agent.py", b"").decode("utf-8", "replace"), b.get("agent.py", b"").decode("utf-8", "replace")
    ms = lambda t: (lambda m: int(m.group(1)) if m else None)(re.search(r"^MAX_STEPS\s*=\s*(\d+)", t, re.M))
    tb, ta = truncated_at_marker(a.get("prompt.md", b"")), truncated_at_marker(b.get("prompt.md", b""))
    return {
        "prompt_truncated_at_marker_before": tb, "prompt_truncated_at_marker_after": ta,
        "prompt_truncation_introduced": ta and not tb,
        "tool_loader_removed": "def load_tools" in aa and "def load_tools" not in ba,
        "prompt_md_orphaned": "prompt.md" in aa and "prompt.md" not in ba,
        "done_handling_removed": ('"done"' in aa) and ('"done"' not in ba) and ("DN" not in ba),
        "max_steps_before": ms(aa), "max_steps_after": ms(ba),
    }


def flags(added_lines, removed_lines, d):
    low = [(f, l, l.lower()) for f, l in added_lines]
    fam = sorted({w for w in FAMILY_WORDS for _, _, ll in low if w.lower() in ll})
    fam_lines = sum(1 for _, _, ll in low if any(w.lower() in ll for w in FAMILY_WORDS))
    caps_new = {}
    for _, l, _ in low:
        m = RE_CAP.match(l)
        if m:
            caps_new[m.group(1)] = int(m.group(2).replace("_", ""))
    caps_old = {}
    for _, l in removed_lines:
        m = RE_CAP.match(l)
        if m:
            caps_old[m.group(1)] = int(m.group(2).replace("_", ""))
    code = [(f, l) for f, l, _ in low if f.endswith(".py")]
    return {
        "family_words": fam,
        "family_word_lines": fam_lines,
        "cap_change": bool(caps_new),
        "caps_old": caps_old,
        "caps_new": caps_new,
        "caps_lowered": {k: [caps_old[k], v] for k, v in caps_new.items() if k in caps_old and v < caps_old[k]},
        "end_marker_workaround": any(re.search(r'"@"\s*\+\s*"end"|AT\s*\+\s*"end"|replace\([^)]*"@end"\)', l)
                                     for _, l, _ in low),
        "preload": any(RE_PRELOAD.search(l) for f, l in code if f == "agent.py"),
        "multi_action": any(RE_MULTI.search(l) for f, l in code),
        "family_name_used": sorted(w for w in ("ledger", "logwin", "bugfix") if any(w in ll for _, _, ll in low)),
        "fence_strip": any(RE_FENCE.search(l) for f, l in code),
        "new_tool_file": [f for f in d["files_added"] if f.startswith("tools" + os.sep)],
        "new_non_tool_file": [f for f in d["files_added"] if not f.startswith("tools" + os.sep)],
    }


def turns():
    for run in sorted(os.listdir(RUNS)):
        if not run.endswith(SUFFIXES):
            continue
        rows = [json.loads(l) for l in open(os.path.join(RUNS, run, "log.jsonl")) if l.strip()]
        arm = next(r for r in rows if r.get("kind") == "start")["arm"]
        for r in rows:
            if r.get("kind") == "turn":
                yield run, arm, r


def main():
    want_print = "--print" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_rows = []
    skipped = []
    for run, arm, r in turns():
        if not r.get("edited"):
            continue
        bdir = os.path.join(RUNS, run, "snap", r["base"])
        cdir = os.path.join(RUNS, run, "snap", r["candidate"])
        if not (os.path.isdir(bdir) and os.path.isdir(cdir)):
            skipped.append((run, r["t"]))
            continue
        d, added, removed, udiff = diff_turn(bdir, cdir)
        row = {"run": run, "arm": arm, "t": r["t"], "builder": r["builder"], "target": r["target"],
               "outcome": r["outcome"], "inc": r.get("inc"), "cand": r.get("cand"),
               "build_calls": r.get("build_calls"), "base": r["base"], "candidate": r["candidate"]}
        row.update(d)
        row.update(flags(added, removed, d))
        row.update(structure(bdir, cdir))
        out_rows.append(row)
        if want_print and (not only or any(o == run or o == f"{run}:{r['t']}" for o in only)):
            print("=" * 100)
            print(f"### {run} t{r['t']} arm={arm} builder={r['builder']} target={r['target']} "
                  f"outcome={r['outcome']} inc={r.get('inc')} cand={r.get('cand')} "
                  f"+{d['lines_added']}/-{d['lines_removed']} bytes {d['bytes_before']}->{d['bytes_after']}")
            print("\n".join(udiff))
    with open(os.path.join(OUT, "changes.jsonl"), "w") as f:
        for row in out_rows:
            f.write(json.dumps(row) + "\n")
    print(f"[changes.py] {len(out_rows)} edited turns written; skipped (missing snapshot): {skipped}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
