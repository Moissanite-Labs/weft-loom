# Builds the public lab-site copies of Report 1 and the open-directions map.
# Usage: python3 build.py OUT_DIR   (OUT_DIR = <lab site>/docs/research)
import html, json, re, sys, pathlib, shutil
E = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
W101 = "https://github.com/Moissanite-Labs/weft/pull/101"
W107 = "https://github.com/Moissanite-Labs/weft/pull/107"

def shell(title, desc, slug, body, root, cur, extra_head=""):
    nav = [("Research", root + "research/"), ("Ecosystem", root + "ml/"), ("Lab", root)]
    links = "".join(f'<a href="{h}"{" aria-current=\"page\"" if n == cur else ""}>{n}</a>' for n, h in nav)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#08090a">
<title>{title} | Moissanite Labs</title>
<meta name="description" content="{html.escape(desc, quote=True)}">
<link rel="canonical" href="https://moissanite-labs.github.io/.github/research/{slug}">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{root}research/research.css">{extra_head}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="bar"><a class="brand" href="{root}" aria-label="Moissanite Labs home"><img src="{root}assets/favicon.svg" width="35" height="35" alt=""><span>MOISSANITE<span>LABS</span></span></a>
<nav aria-label="Main navigation">{links}<a href="https://github.com/Moissanite-Labs">GitHub <span aria-hidden="true">&nearr;</span></a></nav></header>
{body}
<footer class="foot"><a class="name" href="{root}">MOISSANITE LABS</a><span>&copy; 2026 Moissanite Labs</span><a href="https://github.com/Moissanite-Labs/.github">Site source <span aria-hidden="true">&nearr;</span></a></footer>
</body>
</html>
'''

def rep(s, old, new, n=None):
    c = s.count(old)
    assert c > 0 and (n is None or c == n), (old, c, n)
    return s.replace(old, new)

# ---------- report ----------
s = (E / "REPORT.html").read_text()
body = s[s.index("<main>") + 6: s.index("</main>")]
body, k = re.subn(r"Exo canary seat \([^)]*\), principal investigator A\. Arifuddin &middot; ", "Moissanite Labs &middot; ", body)
assert k == 1, k
body = rep(body, "<code>razi-tools/cells/cell.py</code>", "<code>code/cell.py</code> in the record", 1)
body = rep(body, " (needs harness fix f_a04e95fa)", " (needs a harness fix)", 1)
body = rep(body, "need his approval", "need the project lead's approval", 1)
for a, b in [(">razi, ", ">agent, "), (">razi<", ">agent<"), ("shaped by razi", "shaped by the agent"), ("and razi<", "and agent<")]:
    body = rep(body, a, b)
body = re.sub(r"\bPrincipal\b", "Project lead", body)
body = re.sub(r"\bprincipal\b", "project lead", body)
i, j = body.index('<h2 id="harness">'), body.index('<h2 id="repro">')
body = body[:i] + '''<h2 id="harness">12. Harness findings filed during the program</h2>
<table>
<tr><th>No.</th><th>Issue</th></tr>
<tr><td>1</td><td>One model route needs a session header on every call, and had no fallback route</td></tr>
<tr><td>2</td><td>gpt-6 on chat/completions rejects function tools combined with reasoning. Needs a /v1/responses transport</td></tr>
<tr><td>3</td><td>The agent is not reliably woken when a background job exits; one early wake</td></tr>
<tr><td>4</td><td>Phantom turns ran, and were billed, with no user input</td></tr>
</table>

''' + body[j:]
i = body.index("<li>Code: <code>~/Work/razi-tools/cells/</code>"); j = body.index("<li>Logs:", i)
body = body[:i] + f'''<li>Code and data: published as the E07 record in the Weft repository, under <code>docs/program/experiments/E07/razi-cells-2026-11/</code> (<code>code/</code>: <code>cell.py</code>, <code>colony.py</code>, <code>embed.py</code>, <code>perm.py</code>; <code>data/</code>: run summaries for g3, g4 and b5 to b11). <a href="{W101}">Record, under review</a>.</li>
''' + body[j:]
note = f'''<div class="note"><b>Notes added for publication, 2026-11-10</b>
This is Report 1 as written on 2026-11-09, with private paths, names and internal ids removed. It is an exploratory report. Three things are known since.
<ol>
<li>A scoring fault was found afterwards. The score reader took the last number from standard output and standard error together, so a runtime warning line was once read as a score. Taking out the one false improvement moves run b5 from 12.82 to 11.97 kept improvements per 100 calls, and the correlation in finding (3) from 0.99 to 0.986. The Fable against Argon comparison stays undetectable under every correction (Welch t between 0.29 and 0.70).</li>
<li>Section 5 says the embedding permutation tests shuffle whole runs. The code shuffles single variants, as section 6.6 describes. Read those p values as upper bounds on the evidence, because variants from one run are not independent.</li>
<li>The registered tests that followed are kept in their own records: <a href="{W101}">E07</a> and <a href="{W107}">the laws record, E11 to L1</a>. Both are under review. Several guesses there missed, and the records say so.</li>
</ol></div>
'''
body = rep(body, '<div class="abstract">', note + '<div class="abstract">', 1)
body = body.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
body = '<main class="paper" id="main">\n<p class="eyebrow"><i></i> Research / report</p>' + body + "</main>"
bad = re.findall(r"razi(?!-cells)|[Pp]rincipal|f_[0-9a-f]{8}|\$\d|~/Work|/Users/|kethuda|canary|\bseat\b|Arifuddin|[\u2013\u2014]", body)
assert not bad, bad
(OUT / "stem-cell-micro-harnesses").mkdir(exist_ok=True)
(OUT / "stem-cell-micro-harnesses/index.html").write_text(shell(
    "Stem-Cell Micro-Harnesses: Report 1",
    "Report 1 of the razi-cells program: small agent harnesses that start from a need and an empty folder, and improve by selection.",
    "stem-cell-micro-harnesses/", body, "../../", "Research"))

# ---------- map ----------
src = (E / "map/gen.py").read_text()
ns = {}
exec(src[src.index("T = ["): src.index("ROW, FS")], ns)
T = ns["T"]
S = {"now": ("#d9c7a0", "next to run"), "ready": ("#8fcfa8", "ready to run, tooling exists"),
     "build": ("#9fb4c4", "needs new tooling first"), "parked": ("#7d8082", "tested or paused, set aside"),
     "far": ("#b3a1c9", "out of reach today")}
WORD = [("Your sensor-exposure idea.", "The sensor-exposure idea from the project lead."),
        ("T-J2, your discussion 105 idea.", "T-J2, from Weft discussion 105."),
        ("Your central hypothesis.", "The central hypothesis of the program."),
        ("Weft PR 101. Paused at your word. Numbers already recomputed.", "Weft PR 101. Numbers recomputed by script. The corrections are not yet written into the record.")]
# leaves replaced or added after the map was first drawn (state on 2026-11-10, from TESTS.md and IDEAS.md)
OVER = {
 "Need sensor (SP3)": ("Need sensor (SP3)", "parked", 0, "Tested. One inward number: my body's score against the best my lineage ever recorded. With the price list and the number both shown, reach was highest (2.03 against 1.48 with the list alone), on 4 runs per arm, smallest p 0.21. 6 of 12 guesses held. A lead, on one model family."),
 "Adapter genome on Inkling 2 Small": ("Adapter genome on Inkling 2 Small", "parked", 0, "T-J3. Cell experience as training data for a small adapter; fork, train two ways, gate keeps the better. Incomplete: the plain arm did not beat the untrained base (test loss 0.904 against 0.674, median of 3 seeds) and the gated arms stopped on a storage limit. Set aside until the plain arm works."),
}
ADD = {"WHAT IS INHERITED": [
 ("Division at birth (T-L2)", "now", 1, "Each birth is a pair: one daughter keeps the inherited body, the other must change it before it may rest. The gate keeps the better. Follows from L1, where 65 of 70 heirs changed nothing."),
 ("Heredity across lives (L1)", "parked", 0, "Tested. A body passed down generations, an energy store that pays for births, a gate on the germline. Reach was level with blank newborns (2.27 against 2.28). Heirs spent 31% less energy and died less, but did not compound. 5 of 8 guesses held; the three that mattered missed."),
 ("A need longer than one life (T-L3)", "build", 0, "A need that cannot be finished in one life, so that compounding is the only way up."),
]}
known = {"LAWS OF THE CELL": "Known: cells stop at the first passing answer, pick the cheapest model when they can see prices, and never divide (0 of 12+). Colony shape is not the lever (SP2). Hiding the price list changes the choice, not the reach (SP3)."}
T2 = []
for name, sub, kn, leaves in T:
    L = []
    for leaf in ADD.get(name, []): L.append(leaf)
    for lab, st, pick, d in leaves:
        if lab in OVER: lab, st, pick, d = OVER[lab]
        if st == "now": st = "ready"
        for a, b in WORD:
            if a in d: d = d.replace(a, b)
        L.append((lab, st, pick, d))
    T2.append((name, sub, known.get(name, kn), L))
T = T2
assert sum(l[0] in OVER for b in T for l in b[3]) == len(OVER)
ROW, FS = 27, 13
left, right = T[4:], T[:4]
def side_h(bs): return sum(len(b[3]) for b in bs) * ROW + (len(bs) - 1) * 34
H = max(side_h(left), side_h(right)) + 150
W = 1640; cx, cy = W / 2, H / 2 + 20
out, det = [], []
esc = lambda x: html.escape(x, quote=True)
def node(i, x, y, w, h, fill, stroke, txt, cls, sub=None):
    tx, cut = x + w / 2, 9
    pts = f"{x+cut},{y} {x+w},{y} {x+w},{y+h-cut} {x+w-cut},{y+h} {x},{y+h} {x},{y+cut}"
    g = f'<g class="n {cls}" data-i="{i}" tabindex="0"><polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
    g += f'<text x="{tx}" y="{y+h/2+(-3 if sub else 4.5)}" text-anchor="middle" class="{cls}t">{esc(txt)}</text>'
    if sub: g += f'<text x="{tx}" y="{y+h/2+13}" text-anchor="middle" class="subt">{esc(sub)}</text>'
    return g + "</g>"
def draw(bs, sgn):
    y = cy - side_h(bs) / 2
    for name, sub, kn, leaves in bs:
        bh = len(leaves) * ROW; by = y + bh / 2
        bw, bx = 236, cx + sgn * 150 - (236 if sgn < 0 else 0)
        det.append({"t": name, "s": sub, "d": kn}); bi = len(det) - 1
        x0, x1 = cx + sgn * 96, bx + (bw if sgn < 0 else 0)
        out.append(f'<path d="M{x0},{cy} C{x0+sgn*40},{cy} {x1-sgn*40},{by} {x1},{by}" class="lk b"/>')
        ex = bx + (0 if sgn < 0 else bw)
        for j, (lab, st, pick, d) in enumerate(leaves):
            ly = y + j * ROW + ROW / 2; lx = ex + sgn * 46; col = S[st][0]
            det.append({"t": lab, "s": S[st][1] + (" \u00b7 starred" if pick else ""), "d": d}); li = len(det) - 1
            out.append(f'<path d="M{ex},{by} C{ex+sgn*26},{by} {lx-sgn*26},{ly} {lx},{ly}" class="lk" stroke="{col}"/>')
            a = "start" if sgn > 0 else "end"; tx = lx + sgn * 16
            out.append(f'<g class="n leaf" data-i="{li}" tabindex="0"><rect x="{lx-5}" y="{ly-5}" width="10" height="10" fill="{col}" transform="rotate(45 {lx} {ly})"/>'
                       f'<rect x="{tx-4 if sgn>0 else tx-330}" y="{ly-ROW/2+1}" width="334" height="{ROW-2}" fill="transparent"/>'
                       f'<text x="{tx}" y="{ly+4.5}" text-anchor="{a}" class="leaft{" pick" if pick else ""}">{esc(("\u2605 " if pick else "") + lab)}</text></g>')
        out.append(node(bi, bx, by - 23, bw, 46, "#0e1011", "#eceae4", name, "br", sub=sub))
        y += bh + 34
draw(right, 1); draw(left, -1)
det.append({"t": "RAZI CELLS", "s": "open directions, 2026-11-10",
            "d": "Core question: which laws, felt from inside by each cell, make a colony improve, divide and show restraint on its own. Select any node. Stars mark where the investigating agent judges the next real finding most likely."})
out.append(node(len(det) - 1, cx - 96, cy - 34, 192, 68, "#d9c7a0", "#d9c7a0", "RAZI CELLS", "ct", sub="what is left to explore"))
leg = "".join(f'<span class="lg"><i style="background:{c}"></i>{esc(t)}</span>' for c, t in S.values()) + '<span class="lg">\u2605 starred</span>'
n = sum(len(b[3]) for b in T)
listing = "".join(f'<h3>{esc(nm.title())}: {esc(sb)}</h3><p>{esc(kn)}</p><ul>' + "".join(
    f'<li><b>{esc(("\u2605 " if p else "") + lab)}</b> <em>{esc(S[st][1])}</em>. {esc(d)}</li>' for lab, st, p, d in lv) + "</ul>" for nm, sb, kn, lv in T)
mbody = f'''<main class="mapmain" id="main">
<div class="maphead"><div><p class="eyebrow"><i></i> Research / map</p><h1>Razi cells: open directions</h1>
<p class="lede">{len(T)} branches and {n} directions left to explore in the razi-cells program, as of 2026-11-10. Data only. Nothing here claims more than the test log and the idea log in the <a href="{W107}">laws record</a>. Hover or select a node to read it.</p></div>
<div class="legend">{leg}</div></div>
<div class="mapscroll"><svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="map-title"><title id="map-title">Mind map of open research directions. The same content follows as a text list.</title>{"".join(out)}</svg></div>
<div id="d" aria-live="polite"></div>
<details class="maplist"><summary>The same map as a text list</summary>{listing}</details>
</main>
<script>
const D={json.dumps(det)};const d=document.getElementById("d");
function show(i,el){{const x=D[i];d.replaceChildren();const b=document.createElement("b");b.textContent=x.t;const e=document.createElement("em");e.textContent=x.s;const p=document.createElement("p");p.textContent=x.d;d.append(b,e,p);
document.querySelectorAll(".n.on").forEach(n=>n.classList.remove("on"));if(el)el.classList.add("on");}}
document.querySelectorAll(".n").forEach(n=>{{for(const ev of ["click","mouseenter","focus"])n.addEventListener(ev,()=>show(+n.dataset.i,n));}});
show(D.length-1,null);
</script>'''
bad = re.findall(r"\byour\b|\bYour\b|my pick|tonight|[\u2013\u2014]|/Users/|~/Work|\$\d", mbody)
assert not bad, bad
(OUT / "open-directions").mkdir(exist_ok=True)
(OUT / "open-directions/index.html").write_text(shell(
    "Razi cells: open directions",
    "A map of the open research directions in the razi-cells program: laws of the cell, heredity, proof, growing a model.",
    "open-directions/", mbody, "../../", "Research"))
# ---------- hub ----------
HELD = [("GR1", "Toy network: does copy division pass a gate", "3 of 5"), ("GR2", "Toy network: daughters born different", "5 of 6"),
        ("GR3", "Toy network: one knob at a time", "3 of 5"), ("GR4", "Toy network: need sensor and escalation", "5 of 5"),
        ("SP1", "Stem cell that feeds its parts", "7 of 8"), ("SP2", "Colony shape: flat against stem", "6 of 8"),
        ("SP3", "Price list and need sensor", "6 of 12"), ("L1", "Heredity across generations", "5 of 8")]
rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in HELD)
hub = f'''<main class="hub" id="main">
<p class="eyebrow"><i></i> Lab / research</p>
<h1>Small harnesses,<br>under <span>selection.</span></h1>
<p class="lede">Razi cells is a research program at Moissanite Labs. A cell is a very small agent harness that starts from a need and an empty folder, writes its own tools, and is kept or dropped by a measured score. The program asks which laws, felt from inside by each cell, make a colony improve on its own. Everything here is exploratory. Guesses are written down before the data, and misses are reported.</p>
<h2>Read</h2>
<div class="cards">
<article class="card"><div class="id"><span>01 / REPORT</span><b>Exploratory</b></div>
<h3><a href="stem-cell-micro-harnesses/">Stem-Cell Micro-Harnesses <span aria-hidden="true">&rarr;</span></a></h3>
<p>Report 1. Thirteen colonies, eight coding tasks, five model conditions. Method, variables, results to date, 18 registered hypotheses and the roadmap.</p>
<div class="links"><a href="stem-cell-micro-harnesses/">Read the report</a><a href="{W101}">Record and data &nearr;</a></div></article>
<article class="card"><div class="id"><span>02 / MAP</span><b>{n} directions</b></div>
<h3><a href="open-directions/">Open directions <span aria-hidden="true">&rarr;</span></a></h3>
<p>What is left to explore, as a mind map: laws of the cell, which model, what is inherited, signals beyond text, proof, growing a model, the colony as an organism.</p>
<div class="links"><a href="open-directions/">Open the map</a></div></article>
<article class="card"><div class="id"><span>03 / RECORD</span><b>Under review</b></div>
<h3><a href="{W107}">The laws record, E11 to L1 <span aria-hidden="true">&nearr;</span></a></h3>
<p>The registered tests that followed Report 1: an energy economy for cells, toy growing networks, a stem cell, a need sensor, and heredity. Test log, idea log, code and results.</p>
<div class="links"><a href="{W107}">Weft pull request 107 &nearr;</a></div></article>
<article class="card"><div class="id"><span>04 / PAPERS</span><b>Public</b></div>
<h3><a href="https://w3ft.org">Weft papers <span aria-hidden="true">&nearr;</span></a></h3>
<p>The program is the agent-level twin of the Weft cell loop, which applies the same split, score and keep cycle to model weights.</p>
<div class="links"><a href="https://w3ft.org">w3ft.org &nearr;</a><a href="https://github.com/Moissanite-Labs/weft">Repository &nearr;</a></div></article>
</div>
<section class="held" aria-labelledby="held-title">
<h2 id="held-title">Guesses written before the data, and how many held</h2>
<p>Each experiment in the laws record states its guesses before any run and is judged as written, by script. A guess that held is not an established result: runs are few and only one model family has run the energy laws so far.</p>
<div class="tablewrap"><table><tr><th>Test</th><th>Question</th><th>Held</th></tr>{rows}</table></div>
</section>
</main>'''
assert not re.findall(r"[\u2013\u2014]|/Users/|~/Work|\$\d", hub)
(OUT / "index.html").write_text(shell("Research", "Razi cells: research at Moissanite Labs on small agent harnesses under selection. Report, map of open directions, and records.", "", hub, "../", "Research"))
shutil.copy(E / "public/research.css", OUT / "research.css")
print("report bytes", len(body), "map leaves", n, "branches", len(T), "H", H,
      {k: sum(1 for b in T for l in b[3] if l[1] == k) for k in S}, "picks", sum(l[2] for b in T for l in b[3]))
