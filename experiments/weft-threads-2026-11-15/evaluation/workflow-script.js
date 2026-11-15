export default async function workflow(host) {
  const schema = {
    type: "object",
    required: ["complete", "evidence", "unresolved"],
    properties: {
      complete: { type: "boolean" },
      evidence: { type: "array", items: { type: "string" } },
      unresolved: { type: "array", items: { type: "string" } },
      thread: { type: "string" },
      verdict: { type: "string", enum: ["new-ground", "promising", "thread-to-pull", "known-art", "refuted", "unresolved"] },
      next_test: { type: "string" },
      repo_home: { type: "string" },
    },
  };
  const notesFor = (r, s) => (typeof r?.notes === "string" && r.notes.trim()) ? [{ source: s, ref: r.ref, value: r.notes }] : [];
  const synthesisNotes = [];
  const spilled = [];
  const recordSpill = (r, s) => {
    if (r?.data_spilled_for_size !== true) return false;
    spilled.push({ scope: s, ref: r.ref, bytes: r.submitted_payload_bytes, chars: r.submitted_payload_chars });
    synthesisNotes.push(s + ": large submission retained at " + r.ref + "; read via completion index before citing.");
    return !r.error_kind;
  };
  const compact = (r, scope, missing) => {
    const wasSpilled = recordSpill(r, scope);
    const failed = r === null || !!r?.error_kind || r?.kind === "not_admitted";
    const d = (!failed && r.data && typeof r.data === "object") ? r.data : null;
    const ev = Array.isArray(d?.evidence) ? d.evidence.filter(Boolean) : [];
    const un = Array.isArray(d?.unresolved) ? d.unresolved.filter(Boolean) : [];
    const complete = d?.complete === true && ev.length > 0 && un.length === 0;
    return {
      scope, ref: r?.ref ?? null, complete,
      verdict: d?.verdict ?? null, next_test: d?.next_test ?? null, repo_home: d?.repo_home ?? null,
      evidence: ev, notes: notesFor(r, scope),
      unresolved: complete ? [] : (wasSpilled ? (missing ? [missing] : []) : (un.length ? un : [missing ?? (scope + ": missing complete evidence result")])),
    };
  };

  const COMMON = [
    "FIRST-PRINCIPLES PROTOCOL. You evaluate one thread of the Weft research program (w3ft.org; GitHub Moissanite-Labs/weft and Moissanite-Labs/weft-loom). Unfamiliarity is not evidence of conjecture, and familiarity is not evidence of truth. Derive, do not pattern-match.",
    "Steps: (1) Restate the problem with no Weft vocabulary: what breaks in the world without this mechanism. (2) Derive the smallest mechanism that could solve it and what must be true for it to work. (3) OPEN every implementation and test body listed below with read_file and read them; search output only locates candidates and is never evidence. (4) Separate stated rules from checked rules: name the exact predicate the executable path enforces, with file and line. (5) Give the strongest counterexplanation: the boring reason the reported numbers could appear without the claimed mechanism, plus the nearest established technique you know. (6) Verdict, one of: new-ground (mechanism or result not in established practice, evidence holds), promising (real effect, narrow conditions), thread-to-pull (effect unproven but a cheap decisive test exists), known-art (sound but standard), refuted (evidence against), unresolved. (7) ONE decisive next test: setup, metric, explicit pass and fail thresholds, rough cost. A test that cannot fail is not a test. (8) Name who outside this project would care and why, in plain words. (9) repo_home: the one GitHub repo where follow-up work belongs. Capability id is your thread id.",
    "EVIDENCE FORMAT. Each evidence string: 'CLAIM | absolute/path:line or exact command | VERIFIED or REPORTED | decisive number or quote'. VERIFIED means you read the cited lines or ran the command in this session. You may run bounded tests (under 2 minutes, no network installs) and quote real output. If a body is missing, stale, or unreadable, put it in unresolved. Keep evidence compact: at most 14 strings, each under 400 characters. Local snapshots may lag GitHub main; note snapshot dates as a limit, do not silently treat them as current.",
    "Return complete=true only if every assigned claim has inspected evidence and unresolved is empty.",
  ].join("\n");

  const W = "/Users/kethuda/Work/weft-audit-20261108/weft";
  const L = "/Users/kethuda/Work/weft-loom-20261113";
  const THREADS = [
    { id: "WEFT-T1 safety-gate", home: "Moissanite-Labs/weft", task: "Bounded self-modification gate: commit a weight update only if ||W-W0|| <= R and budget >= cost > 0, implemented in Python, C11 and JavaScript against shared vectors. Question: is the cross-language conformance discipline or the gate semantics themselves new ground, or standard trust-region practice in new clothes? Bodies: " + W + "/weft/runtime/invariants/ (read implementation, tests, vectors, C header), " + W + "/site/assets/js/invariant-gate.js, claims M4 M6 M7 in " + W + "/docs/corpus/claims-register.md. Check defaults parity (Python radius vs C), NaN and nonfinite handling, and whether all languages run the same vector file." },
    { id: "WEFT-T2 plasm-cells", home: "Moissanite-Labs/weft", task: "Models as cells: shared-memory arena, cautious vs exploratory candidate updates kept by target score, frozen-core mask, provenance watermark. Question: does gated A/B adaptation in a shared arena beat plain fine-tuning or evolutionary search on any measured task, or is selection just min-norm decay? Bodies: " + W + "/weft/runtime/plasm/ (all), " + W + "/weft/runtime/mac/, claims M1 M2 M3 M10 M11 M12 M13 in claims-register.md. Check the selection score actually coded, mask value distribution, watermark removal cost, and any task metric beyond weight norms." },
    { id: "WEFT-T3 plasmid-splicing", home: "Moissanite-Labs/weft-loom", task: "Skill grafting between independently trained networks with no shared basis: dormant slots, one inhibitory shunting connection, geodesic fiber retraction, compact plasmid payload. Headline: 12/12 joint passes, 1456-byte graft, donor-level shifted R2 on 12488-parameter MLPs. Question: which ingredient carries the effect, what is the cheapest ablation or scale step that could kill it, and how does it differ from permutation alignment and model merging? Bodies: " + L + "/experiments/e13-geodesic-shunting-plasmid-2026-11-12/ (PREREG-E13.md, RESULTS-E13.md, e13_geodesic_plasmid.py, e13_certificates.json), plus " + L + "/experiments/weft-v2-gemini-carbon-2026-11/README.md and engine if readable. Verify preregistration discipline: were thresholds fixed before the run, and does the code do what RESULTS says (given skill_idx, donor-only scramble, alignment measured not applied)?" },
    { id: "WEFT-T4 colony-laws", home: "Moissanite-Labs/weft-loom", task: "Razi-cells colony laws: sandboxed agent cells earn energy only for scored improvement; variables include price-list visibility, score-vs-best feedback, stem cells, heredity, gate escalation. Headlines: price list moves 14/16 cells to cheapest model; hidden prices cost 2.4-3.0x energy with 7 deaths vs 0; score-vs-best raises reach; heredity saves 31% energy without compounding. Question: which laws are real behavioral effects vs harness artifacts at n=3-4 runs per arm, and what is the decisive replication (second model family, powered n)? Bodies: " + L + "/experiments/razi-cells-laws-2026-11/ (README.md, TESTS.md relevant blocks, IDEAS.md lessons, CONSULT-2026-11-10.md), outline of " + L + "/experiments/E07/. Check preregistration order, per-arm n, p-values as reported, and Exo import coupling that blocks fresh-checkout reproduction." },
    { id: "WEFT-T5 interaction-combinators", home: "Moissanite-Labs/weft", task: "Checkable computation: Lafont interaction-combinator reducer (ERA/CON/DUP), binary graph serializer (BCP), graph-committed execution record. Question: is committed, replayable graph reduction useful as verification for agent computation, or a correct toy with no consumer? What breaks first: confluence, serializer state contract, malformed input, exhaustion? Bodies: " + W + "/weft/runtime/ic/ic_vm.py, bcp_codec.py, test_ic_vm.py, test_state_contract.py, claims M8 M9 R15. Verify port discipline in code, round-trip continuation tests, and failure atomicity." },
    { id: "WEFT-T6 abios-sym2p", home: "Moissanite-Labs/abios", task: "Compact checkable agent messaging: one canonical packet per line, symbolic fields, s-expression payload, SHA-256 checked, stdlib validator with typed exit codes. Claim: 101-byte packet vs 481-byte JSON. Question: measured on what corpus, at what readability and tooling cost, and does any real consumer (Exo, Divan bus, Weft telemetry) gain enough to switch? Bodies: /Users/kethuda/work/abios/ (SPEC.md, README.md, scripts validator, tests and fixtures, bench if present), " + W + "/weft/runtime/telemetry/sym2p_codec.py, claim R2. Verify the byte comparison like-for-like, validator behavior on mutated packets, and open items O-1 to O-9 if listed." },
    { id: "WEFT-T7 eido-telemetry", home: "Moissanite-Labs/weft-eido", task: "Interfaces as fields: Eido design language (style as a point in continuous space, dependency-free ES modules), Aywa browser field, 64-byte telemetry frames. Question: is continuous style space plus hash-checked packets a transferable interface idea, or a single-site skin? What would a second consumer need? Bodies: /Users/kethuda/Work/weft-audit-20261108/weft-eido/ (README and modules), " + W + "/weft/runtime/aywa/, " + W + "/weft/runtime/telemetry/ (frame64, host_metrics, harvester, tests), claims R4 R6 R11 R12 R13. Check measured vs fixture labeling per field, circular vs linear hue mean in shipped code, WebGPU canvas sizing." },
    { id: "WEFT-T8 evidence-method", home: "Moissanite-Labs/weft-loom", task: "The evidence discipline itself as a candidate contribution: verbatim corpus, claims register with falsifiers, preregistrations with file hashes fixed before data, audits that state limits as prominently as findings, negative results kept. Question: is this a reusable method for AI-assisted research programs that others would adopt, what does it cost per claim, and where did it fail to catch error? Bodies: " + W + "/docs/corpus/claims-register.md (structure and status counts), " + W + "/docs/program/convergence-plan.md and build-program or experiment-cards if present, " + L + "/README.md rules, " + L + "/audit/review-comprehensive-2026-11-08.md, one loom PREREG vs RESULTS pair of your choice read in full. Count VERIFIED vs REPORTED vs OPEN; sample-check two register entries against code." },
    { id: "WEFT-T9 horizons-ledger-os-silicon", home: "Moissanite-Labs/siliconcordat", task: "Design branches: Solidity provenance/metering/dispute drafts plus offline gateway simulator, bare-metal OS embodiment, hardware invariant comparators and custom silicon, shared-weave governance. Question: strip each to first principles. Which branch contains a kernel worth one bounded experiment (for example compiling contracts locally against the simulator, or simulating one finite-precision comparator), and which are vision with no deciding test this year? Name the authority, consent and appeal gaps in the contracts as coded. Bodies: " + W + "/weft/runtime/ledger/, " + W + "/weft/runtime/gateway/ (gateway.py, keccak256.py, tests), " + W + "/docs/roadmap.md if present, claims L1-L10 H1-H6 G1-G8. Verify: no CI compile of Solidity, locked token supply reading, single-admin court reading." },
  ];

  phase("Thread evaluation");
  log("Evaluating 9 Weft threads from first principles; each child opens code and tests.");
  const primaries = await host.parallel(THREADS.map((t) => ({
    input: COMMON + "\n\nTHREAD " + t.id + " (default repo_home " + t.home + "; override only with evidence).\n" + t.task,
    schema, label: t.id, phase: "Thread evaluation",
  })));
  const primaryReports = primaries.map((r, i) => compact(r, THREADS[i].id));
  const primaryRefs = primaryReports.map((r) => r.ref).filter(Boolean);
  const compactJson = JSON.stringify(primaryReports);

  phase("Challenge and convergence");
  const wave2 = await host.parallel([
    {
      input: "You are the skeptic. Prior thread reports (full results by ref): " + primaryRefs.join("\n") + "\nCompact view: " + compactJson + "\nAttack every verdict of new-ground or promising and every VERIFIED headline number. For each: re-open the cited body yourself when readable, check the number, the baseline, the sample size, and whether a boring mechanism (decay to zero, given labels, fixture data, post-hoc thresholds, single model family) explains it. Downgrade or uphold each claim explicitly in evidence strings. Do not repeat claims you did not re-check; mark them unresolved. Verdict field: use refuted if most headlines fall, thread-to-pull if they narrow, promising if they hold.",
      schema, label: "skeptic", phase: "Challenge and convergence",
    },
    {
      input: "You map nearest established knowledge. Thread reports by ref: " + primaryRefs.join("\n") + "\nCompact view: " + compactJson + "\nFor each thread WEFT-T1..T9, find the closest prior art (for example trust regions and EWC and LoRA drift bounds; evolutionary strategies and quality-diversity; Git Re-Basin, model soups, model merging and adapter composition; interaction nets; agent economies and market-based routing; token-efficient agent protocols; design-token interpolation; preregistration and registered reports; smart-contract metering). Use web search and fetch at least one source per thread you classify; cite exact URLs in evidence. State the delta in one clause: what, if anything, remains new after the nearest art is subtracted. Threads you could not search go in unresolved. Shared gaps in established knowledge are findings too: name where the literature itself is thin, since a gap shared with the field is where new ground is cheapest.",
      schema, label: "prior-art", phase: "Challenge and convergence",
    },
    {
      input: "You hunt convergences. Thread reports by ref: " + primaryRefs.join("\n") + "\nCompact view: " + compactJson + "\nConsider all pairs among: safety gate budgets, Plasm A/B adaptation, plasmid splicing, colony price and score laws, interaction-combinator committed records, abios packets, telemetry frames, Eido fields, evidence method, ledger metering. Also consider consumers in the same org: Exo agent harness, exo-os, statos (apps as weights), synbios, scry and tokenpage (tokenizer research), nullmodem (below-text agent comms). Propose at most 6 convergence hypotheses. Each must be a mechanism, not a metaphor: parts combined, why the combination could do what neither part does, the cheapest combined experiment, metric, pass and fail thresholds, and what result would show mere coincidence. Serendipity is welcome only in testable form. Rank by information gained per week of work. Evidence strings cite thread evidence by thread id plus any body you open.",
      schema, label: "convergences", phase: "Challenge and convergence",
    },
  ]);
  const wave2Reports = [
    compact(wave2[0], "skeptic"),
    compact(wave2[1], "prior-art"),
    compact(wave2[2], "convergences"),
  ];

  const allSoFar = [...primaryReports, ...wave2Reports];
  const open = allSoFar.flatMap((r) => r.unresolved);
  const firstGap = open[0] ?? null;
  let followupReport = null;
  if (firstGap) {
    phase("Gap follow-up");
    const fu = await host.agent({
      input: "Resolve this ONE exact gap by opening the relevant bodies, or return it unchanged in unresolved. Gap: " + JSON.stringify(firstGap) + "\nContext reports: " + JSON.stringify(allSoFar.map((r) => ({ scope: r.scope, ref: r.ref, verdict: r.verdict }))),
      schema, label: "gap-followup", phase: "Gap follow-up",
    });
    followupReport = compact(fu, "gap: " + firstGap.slice(0, 80), firstGap);
  }

  const all = followupReport ? [...allSoFar, followupReport] : allSoFar;
  const unresolved = firstGap && followupReport ? [...open.slice(1), ...followupReport.unresolved] : open;
  const evidence = all.flatMap((r) => r.evidence.map((v) => ({ source: r.scope, ref: r.ref, value: v })));
  const refs = [...new Set(all.map((r) => r.ref).filter(Boolean))];
  const reportNotes = all.flatMap((r) => r.notes);

  phase("Synthesis");
  const synthesis = await host.agent({
    input: [
      "Synthesize the Weft thread evaluation for the team record. Use ONLY the compact evidence below plus full child results by ref. Preserve dissent: where the skeptic downgraded a claim, the synthesis carries the downgraded form and says so.",
      "Full results by ref:\n" + refs.join("\n"),
      "Compact evidence JSON: " + JSON.stringify({ reports: all.map((r) => ({ scope: r.scope, verdict: r.verdict, next_test: r.next_test, repo_home: r.repo_home, evidence: r.evidence, unresolved: r.unresolved })), unresolved, notes: [...reportNotes, ...synthesisNotes] }),
      "Deliver in evidence strings (compact, each self-contained): (A) RANKED THREAD TABLE: one string per thread WEFT-T1..T9 with final verdict, one-clause first-principles finding, delta after prior art, decisive next test with thresholds, repo home. (B) NEW GROUND: threads or sub-results that tread meaningful new ground, or the plain statement that none survives. (C) OF INTEREST TO OTHERS: who outside cares, per surviving thread. (D) CONVERGENCES: ranked combined experiments with falsifiers. (E) ISSUE DRAFTS: one string per proposed GitHub issue: 'REPO | TITLE | labels (needs decision only where A must rule) | body outline: claim, evidence pointers, decisive test, acceptance evidence, capability id and next action'. Route each issue to its own repo (weft, weft-loom, weft-eido, abios, exo, siliconcordat). Prefer few strong issues over many weak ones. Reuse existing open issues where the thread reports name them instead of duplicating. (F) COORDINATION: task rows with stable ids WEFT-T1..T9, dependencies, status from proposed/ready/blocked/deferred, next ready action, bottleneck. (G) DECISIONS FOR A: at most 3, each with options and what evidence would change the answer.",
      "Plain language. Short sentences. No announcement frames. Every number must trace to a cited evidence string. Unresolved items stay unresolved; do not fill gaps with plausible prose.",
    ].join("\n\n"),
    schema, label: "synthesis", phase: "Synthesis",
  });
  const synSpilled = recordSpill(synthesis, "synthesis");
  const synFailed = synthesis === null || !!synthesis?.error_kind || synthesis?.kind === "not_admitted";
  const synData = (!synFailed && synthesis.data && typeof synthesis.data === "object") ? synthesis.data : null;
  const synUnresolved = Array.isArray(synData?.unresolved) ? synData.unresolved.filter(Boolean) : [];
  if (!(synData?.complete === true && Array.isArray(synData.evidence) && synData.evidence.length > 0 && synUnresolved.length === 0) && !synSpilled) {
    synthesisNotes.push("synthesis unavailable or incomplete; parent must synthesize from compact evidence and say so.");
  }

  return {
    status: (unresolved.length || synUnresolved.length || synthesisNotes.length > 0) ? "partial" : "complete",
    unresolved: [...unresolved, ...synUnresolved],
    threadVerdicts: primaryReports.map((r) => ({ thread: r.scope, verdict: r.verdict, repo_home: r.repo_home, next_test: r.next_test, ref: r.ref, complete: r.complete })),
    synthesis: { ref: synthesis?.ref ?? null, data: synData, text: synthesis?.text ?? null, notes: notesFor(synthesis, "synthesis"), error_kind: synthesis?.error_kind ?? null },
    evidence,
    wave2: wave2Reports,
    spilledResults: spilled,
    notes: [...reportNotes, ...synthesisNotes],
  };
}