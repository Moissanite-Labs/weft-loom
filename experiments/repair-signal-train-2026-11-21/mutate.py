"""Removes each guard by an exact single-match text substitution and requires
a test to go red.

For each entry: copy the loop folder to a temp dir, replace OLD with NEW in
one file, run the named test module there (isolated mode, fail fast). A
substitution that matches zero or several times is itself an error. The
unmutated copy must pass first. Exit 0 only if every mutant is killed.

    python3 mutate.py [--only SUBSTRING]
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
F = "False"

# (name, file, old, new, test module expected to go red)
# Not listed: "cand.passed > base.passed" in the ratchet and the whole-line
# JSON check in receipts.verify. Each is implied by a neighbouring guard
# (a p-value at or under 1/40 already means more candidate-only passes, and
# check_plain already refuses floats), so removing it changes no behaviour.
MUTATIONS = [
    ("vendor: pinned hash not enforced", "vendor_loader.py", "    if actual != expected:", "    if False:", "test_vendor"),
    ("seeds: registered ranges", "episodes.py", "        if _overlaps(lo, hi, r_lo, r_hi):", "        if False:", "test_episodes"),
    ("seeds: other kinds", "episodes.py", "        if other != kind and _overlaps(lo, hi, base, base + KIND_SPAN - 1):", "        if False:", "test_episodes"),
    ("seeds: leaving the kind range", "episodes.py", "    if lo < KIND_BASE[kind] or hi > KIND_BASE[kind] + KIND_SPAN - 1:", "    if False:", "test_episodes"),
    ("seeds: offset must be a non-negative integer", "episodes.py", "    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:", "    if False:", "test_episodes"),
    ("seeds: a tier may not run into the next tier", "episodes.py", "    if hi > KIND_BASE[kind] + TIER_OFFSET[tier] + MAX_PER_TIER - 1:", "    if False:", "test_episodes"),
    ("seeds: count limits", "episodes.py", "    if not isinstance(count, int) or isinstance(count, bool) or count < 1 or count > MAX_PER_TIER:", "    if False:", "test_episodes"),
    ("seeds: unknown kind", "episodes.py", "    if kind not in KIND_BASE:", "    if False:", "test_episodes"),
    ("seeds: unknown tier", "episodes.py", "    if tier not in TIER_OFFSET:", "    if False:", "test_episodes"),
    ("attempts: keep attempts that still pass", "episodes.py", "        if not R.check(inst, attempt):", "        if False:", "test_episodes"),
    ("attempts: planted point must pass", "episodes.py", "    if R.check(inst, list(inst.planted)):", "    if False:", "test_episodes"),
    ("render: refuse a passing attempt", "episodes.py", "    if not vios:\n        raise EpisodeError(\"episode", "    if False:\n        raise EpisodeError(\"episode", "test_episodes"),
    ("arms: unknown arm", "episodes.py", "    raise EpisodeError(\"unknown arm %r\" % (arm,))", "    return None", "test_episodes"),
    ("arms: N is not sign-flipped", "episodes.py", "        return [-v.excess for v in vios]", "        return [v.excess for v in vios]", "test_episodes"),
    ("arms: E looks at the truth", "episodes.py", "        return list(_int_rng(\"noise\", tier, seed).choice(pool))", "        return [v.excess for v in vios]", "test_episodes"),
    ("arms: C text gets a defining sentence", "episodes.py", "    lines.append(R.REPLY_TAIL)\n    return", "    lines.append(R.EXCESS_NOTE)\n    lines.append(R.REPLY_TAIL)\n    return", "test_episodes"),
    ('eval: second set without a latch token', 'evaluate.py', '            latch_mod.spend(latch_token, arm, descriptor, latch_mod.load_registry(DECISIONS_PATH))', '            pass', 'test_evaluate'),
    ("eval: latch only checked for the second set", "evaluate.py", "    if epset.kind == \"heldout2\":\n        try:", "    if False:\n        try:", "test_ratchet"),
    ("eval: unknown set kind", "evaluate.py", "    if epset.kind not in ep_mod.KIND_BASE:", "    if False:", "test_evaluate"),
    ("eval: episode of another kind", "evaluate.py", "        if ep.kind != epset.kind:", "        if False:", "test_evaluate"),
    ("eval: episode seed not checked", "evaluate.py", "            ep_mod.check_seed(ep.kind, ep.tier, ep.seed)", "            pass", "test_evaluate"),
    ("grammar: a leading plus is a format break", "evaluate.py", "([+-]?[0-9]{1,12}", "(-?[0-9]{1,12}", "test_evaluate"),
    ("seeds: check_seed unknown kind or tier", "episodes.py", "    _require_known(kind, tier)\n    # a seed that is not", "    # a seed that is not", "test_episodes"),
    ("seeds: check_seed does not use the span rules", "episodes.py", "    seed_span(kind, tier, 1, seed - (KIND_BASE[kind] + TIER_OFFSET[tier]))", "    pass", "test_episodes"),
    ("seeds: check_seed ignores where the range starts", "episodes.py", "    seed_span(kind, tier, 1, seed - (KIND_BASE[kind] + TIER_OFFSET[tier]))", "    seed_span(kind, tier, 1, abs(seed - (KIND_BASE[kind] + TIER_OFFSET[tier])))", "test_episodes"),
    ("seeds: build_episode builds any seed", "episodes.py", "    check_seed(kind, tier, seed)\n    R = rsig()", "    R = rsig()", "test_episodes"),
    ("target: a passing attempt is repaired", "episodes.py", "    if not vios:\n        raise EpisodeError(\"the attempt passes: nothing to repair\")", "    if False:\n        raise EpisodeError(\"the attempt passes: nothing to repair\")", "test_episodes"),
    ("target: a variable with two roles is moved", "episodes.py", "    order = sorted((var for var in shared if len(roles[var]) == 1), key=lambda var: (roles[var] == {\"w\"}, var))", "    order = sorted(shared)", "test_episodes"),
    ("target: second-named variables first", "episodes.py", "key=lambda var: (roles[var] == {\"w\"}, var))", "key=lambda var: (roles[var] != {\"w\"}, var))", "test_episodes"),
    ("target: wrong direction for a first-named variable", "episodes.py", "        cand[var] = cand[var] + (-top if roles[var] == {\"u\"} else top)", "        cand[var] = cand[var] + (top if roles[var] == {\"u\"} else -top)", "test_episodes"),
    ("target: the smallest excess instead of the largest", "episodes.py", "    top = max(v.excess for v in vios)", "    top = min(v.excess for v in vios)", "test_episodes"),
    ("target: max-excess not verified by the checker", "episodes.py", "        if not R.check(inst, cand):\n            return cand, \"max-excess\"", "        if True:\n            return cand, \"max-excess\"", "test_episodes"),
    ("target: search not verified by the checker", "episodes.py", "        if not R.check(inst, cand):\n            return cand, \"search\"", "        if True:\n            return cand, \"search\"", "test_episodes"),
    ("target: search takes the largest move first", "episodes.py", "    tries.sort(key=lambda t: (sum(abs(d) for _v, d in t), len(t), [(v, d) for v, d in t]))", "    tries.sort(key=lambda t: (-sum(abs(d) for _v, d in t), len(t), [(v, d) for v, d in t]))", "test_episodes"),
    ("target: search ties not broken by count", "episodes.py", "    tries.sort(key=lambda t: (sum(abs(d) for _v, d in t), len(t), [(v, d) for v, d in t]))", "    tries.sort(key=lambda t: (sum(abs(d) for _v, d in t), -len(t), [(v, d) for v, d in t]))", "test_episodes"),
    ("target: search moves one variable twice", "episodes.py", "    tries += [(a, b) for i, a in enumerate(moves) for b in moves[i + 1:] if a[0] != b[0]]", "    tries += [(a, b) for i, a in enumerate(moves) for b in moves[i + 1:]]", "test_episodes"),
    ("target: search skips single moves", "episodes.py", "    tries = [(m,) for m in moves]\n", "    tries = []\n", "test_episodes"),
    ("target: search skips pairs", "episodes.py", "    tries += [(a, b) for i, a in enumerate(moves) for b in moves[i + 1:] if a[0] != b[0]]", "    tries += []", "test_episodes"),
    ("target: no planted fallback", "episodes.py", "    return list(inst.planted), \"planted\"", "    return list(attempt), \"planted\"", "test_episodes"),
    ("target: target rule not stored", "episodes.py", "    return Episode(kind, tier, seed, inst, attempt, pert, tries, target, rule)", "    return Episode(kind, tier, seed, inst, attempt, pert, tries, target)", "test_episodes"),
    ("arms: E without a decoy for the count", "episodes.py", "        if not pool:\n            raise EpisodeError(\"no decoy amounts", "        if False:\n            raise EpisodeError(\"no decoy amounts", "test_episodes"),
    ("arms: E decoys not matched by violation count", "episodes.py", "        pool = decoy_pool(tier).get(len(vios))", "        pool = decoy_pool(tier).get(1)", "test_episodes"),
    ("arms: E decoys can be negative", "episodes.py", "            pool.setdefault(len(vios), []).append(tuple(v.excess for v in vios))", "            pool.setdefault(len(vios), []).append(tuple(-v.excess for v in vios))", "test_episodes"),
    ("eval: unknown arm", "evaluate.py", "    if arm not in ep_mod.ARMS:", "    if False:", "test_evaluate"),
    ("eval: cap must be a positive integer", "evaluate.py", "    if not isinstance(cap, int) or isinstance(cap, bool) or cap < 1:", "    if False:", "test_evaluate"),
    ("eval: reported tokens over the cap", "evaluate.py", "        elif ntok > cap:", "        elif False:", "test_evaluate"),
    ('eval: no cut at the cap', 'evaluate.py', '            text, harness_cut = cut_to_cap(text, cap)', '            harness_cut = False', 'test_evaluate'),
    ('eval: format break counted as a failed repair', 'evaluate.py', '    if cand is None:\n        return "X"', '    if cand is None:\n        return "F"', 'test_evaluate'),
    ("eval: non-text reply", "evaluate.py", "        if not isinstance(text, str):", "        if False:", "test_evaluate"),
    ("grammar: duplicate variable", "evaluate.py", "        if idx in vals:", "        if False:", "test_evaluate"),
    ("grammar: zero denominator", "evaluate.py", "        if \"/\" in num and int(num.split(\"/\")[1]) == 0:", "        if False:", "test_evaluate"),
    ("grammar: missing variable", "evaluate.py", "        if i not in vals:", "        if False:", "test_evaluate"),
    ("grammar: unknown variable", "evaluate.py", "        if idx >= n:", "        if False:", "test_evaluate"),
    ("grammar: extra text", "evaluate.py", "        if not g:", "        if False:", "test_evaluate"),
    ("grammar: empty reply", "evaluate.py", "    if not body.strip():", "    if False:", "test_evaluate"),
    ("receipts: previous hash not checked", "receipts.py", "        if rec[\"prev\"] != prev:", "        if False:", "test_receipts"),
    ("receipts: own hash not checked", "receipts.py", "        if rec[\"self\"] != _self_hash(rec[\"seq\"], rec[\"prev\"], rec[\"body\"]):", "        if False:", "test_receipts"),
    ("receipts: sequence not checked", "receipts.py", "        if rec[\"seq\"] != i:", "        if False:", "test_receipts"),
    ("receipts: expected head ignored", "receipts.py", "    if expect_head is not None and prev != expect_head:", "    if False:", "test_receipts"),
    ("receipts: missing newline accepted", "receipts.py", "    if raw and not raw.endswith(b\"\\n\"):", "    if False:", "test_receipts"),
    ("receipts: floats and bools accepted", "receipts.py", "    if isinstance(obj, bool) or obj is None or isinstance(obj, float):", "    if False:", "test_receipts"),
    ('receipts: append skips the body check', 'receipts.py', '    check_plain(body)\n    count, head = verify(path, expect_head)', '    count, head = verify(path, expect_head)', 'test_receipts'),
    ("receipts: non-string keys accepted", "receipts.py", "            if not isinstance(k, str):", "            if False:", "test_receipts"),
    ("latch: second touch allowed", "latch.py", "        if decision_id in self.touched():", "        if False:", "test_ratchet"),
    ("latch: unregistered decision id accepted", "latch.py", "        if not isinstance(decision_id, str) or decision_id not in self.registered:", "        if False:", "test_ratchet"),
    ("latch: no uses required", "latch.py", "        if not pairs or len(set(pairs)) != len(pairs):", "        if False:", "test_ratchet"),
    ("latch: use pairs not checked", "latch.py", "        if not all(len(p) == 2 and all(isinstance(x, str) and x for x in p) for p in pairs):", "        if False:", "test_ratchet"),
    ("latch: a pair outside the token accepted", "latch.py", "    if pair not in token.remaining:", "    if False:", "test_ratchet"),
    ("latch: a pair can be spent twice", "latch.py", "    token.remaining.discard(pair)", "    pass", "test_ratchet"),
    ("latch: spend skips the issued check", "latch.py", "    if not token_is_valid(token):\n        raise LatchRefused(\"the token was not issued by Latch.touch\")", "    if token is None:\n        raise LatchRefused(\"the token was not issued by Latch.touch\")", "test_ratchet"),
    ("latch: registry may be empty", "latch.py", "    if not isinstance(rows, list) or not rows or not all(isinstance(x, str) and x for x in rows):", "    if not isinstance(rows, list):", "test_ratchet"),
    ("latch: registry may repeat an id", "latch.py", "    if len(set(rows)) != len(rows):", "    if False:", "test_ratchet"),
    ("latch: forged token accepted", "latch.py", "    return any(token is t for t in _ISSUED)", "    return token is not None", "test_ratchet"),
    ("ratchet: identical candidate accepted", "ratchet.py", "        if base.descriptor == cand.descriptor or base.replies_sha256 == cand.replies_sha256:", "        if False:", "test_ratchet"),
    ("ratchet: other compute cap accepted", "ratchet.py", "        for r in (base, cand):\n            if r.cap != self.cap:", "        for r in (base, cand):\n            if False:", "test_ratchet"),
    ("ratchet: different episodes accepted", "ratchet.py", "        if base.set_kind != cand.set_kind or base.set_sha256 != cand.set_sha256:", "        if False:", "test_ratchet"),
    ("ratchet: different arms accepted", "ratchet.py", "        if base.arm != cand.arm:", "        if False:", "test_ratchet"),
    ("ratchet: different harnesses accepted", "ratchet.py", "        if base.harness != cand.harness:", "        if False:", "test_ratchet"),
    ("ratchet: harness hash not compared to the lock", "ratchet.py", "        if evaluate.harness_hashes() != locked:", "        if False:", "test_ratchet"),
    ("ratchet: missing lock accepted", "ratchet.py", "        if not os.path.exists(self.lock_path):", "        if False:", "test_ratchet"),
    ("ratchet: lock can be overwritten", "ratchet.py", "                if json.load(fh) != current:", "                if False:", "test_ratchet"),
    ("ratchet: record accepts another harness", "ratchet.py", "        if result.harness != locked:", "        if False:", "test_ratchet"),
    ('ratchet: wrong set accepted for the second-set touch', 'ratchet.py', '        if epset2.kind != "heldout2":\n            raise RatchetRefused("this is not the second held-out set")\n        self.check_lock()\n        self.latch.head', '        self.check_lock()\n        self.latch.head', 'test_ratchet'),
    ("ratchet: significance not required", "ratchet.py", "        accepted = cand.passed > base.passed and p <= self.alpha", "        accepted = cand.passed > base.passed", "test_ratchet"),
    ("ratchet: outcome lengths not compared", "ratchet.py", "    if len(base_outcomes) != len(cand_outcomes):", "    if False:", "test_ratchet"),
    ("ratchet: one-sided test counts the wrong tail", "ratchet.py", "    return Fraction(sum(comb(n, k) for k in range(cand_only, n + 1)), 2 ** n)", "    return Fraction(sum(comb(n, k) for k in range(0, cand_only + 1)), 2 ** n)", "test_ratchet"),
    ("compare_arms: other compute cap", "ratchet.py", "        for r in (first, second):\n            if r.cap != self.cap:", "        for r in (first, second):\n            if False:", "test_ratchet"),
    ("compare_arms: different episodes", "ratchet.py", "        if first.set_kind != second.set_kind or first.set_sha256 != second.set_sha256:", "        if False:", "test_ratchet"),
    ("compare_arms: different harnesses", "ratchet.py", "        if first.harness != second.harness:", "        if False:", "test_ratchet"),
    ("compare_arms: wrong direction of the test", "ratchet.py", "        first_only, second_only = paired_counts(first.outcomes, second.outcomes, test)", "        second_only, first_only = paired_counts(first.outcomes, second.outcomes, test)", "test_ratchet"),
    ('tinker: budget not compared to the ceiling', 'tinker_backend.py', '            if not budget < approval.ceiling - spent:', '        if False:', 'test_tinker_backend'),
    ("tinker: ceiling above zero", "tinker_backend.py", "            if ceiling <= 0:", "            if False:", "test_tinker_backend"),
    ("tinker: ceiling must be a string", "tinker_backend.py", "            if not isinstance(raw, str):", "            if False:", "test_tinker_backend"),
    ("tinker: any approved run id will do", "tinker_backend.py", "        if isinstance(row, dict) and row.get(\"run_id\") == run_id:", "        if isinstance(row, dict):", "test_tinker_backend"),
    ("tinker: no approvals list needed", "tinker_backend.py", "    if not isinstance(rows, list):", "    if False:", "test_tinker_backend"),
    ("tinker: a call may land on the ceiling", "tinker_backend.py", "        if self.spent + cost >= self.ceiling:", "        if self.spent + cost > self.ceiling:", "test_tinker_backend"),
    ("tinker: no stop before the ceiling", "tinker_backend.py", "        if self.spent + cost >= self.ceiling:", "        if False:", "test_tinker_backend"),
    ("tinker: many checkpoints per arm", "tinker_backend.py", "        if self.checkpoints.get(label, 0) >= 1:", "        if False:", "test_tinker_backend"),
    ("tinker: client replaced silently", "tinker_backend.py", "        if label in self.clients:", "        if False:", "test_tinker_backend"),
    ("tinker: errors not redacted", "tinker_backend.py", "    return _SECRETISH.sub(\"[REDACTED]\", str(text))[:400]", "    return str(text)[:400]", "test_tinker_backend"),
    ("tinker: error chain kept", "tinker_backend.py", "(type(exc).__name__, redact(exc))) from None", "(type(exc).__name__, redact(exc)))", "test_tinker_backend"),
    ("tinker: sample limit not reserved", "tinker_backend.py", "        meter.reserve(\"sample\", limit)                 # upper bound, settled below", "        pass", "test_tinker_backend"),
    ("tinker: sample not settled to what came back", "tinker_backend.py", "        meter.settle(\"sample\", limit, len(out))        # counted as returned, even over the limit", "        pass", "test_tinker_backend"),
    ("tinker: no stop ids", "tinker_backend.py", "                                                 stop=self.codec.stop_ids())).result())", "                                                 stop=None)).result())", "test_tinker_backend"),
    ('tinker: reply not read through the codec', 'tinker_backend.py', '        text, count, was_cut = self.codec.reply(out, self.cap)', '        text, count, was_cut = self.codec.tok.decode(out), len(out), False', 'test_tinker_backend'),
    ("tinker: prompt not built by the codec", "tinker_backend.py", "        ids = self.codec.prompt_ids(view.messages)", "        ids = [ord(c) for c in view.feedback]", "test_tinker_backend"),
    ("tinker: training counts the shifted length", "tinker_backend.py", "        tokens = sum(d.model_input.length + 1 for d in datums)", "        tokens = sum(d.model_input.length for d in datums)", "test_tinker_backend"),
    ("tinker: plan kinds not required", "tinker_backend.py", "    if not isinstance(plan_tokens, dict) or set(plan_tokens) != set(PLAN_KINDS):", "    if False:", "test_tinker_backend"),
    ("tinker: plan counts not positive integers", "tinker_backend.py", "        if not isinstance(n, int) or isinstance(n, bool) or n < 1:", "        if False:", "test_tinker_backend"),
    ("tinker: plan not checked at start", "tinker_backend.py", "        require_plan(plan_tokens)                                   # (b)\n", "", "test_tinker_backend"),
    ('tinker: overrun not counted', 'tinker_backend.py', '        self.spent += cost_usd(kind, extra)\n        self.tokens[kind] += extra\n        if self.spent >= self.ceiling:\n            raise BudgetStop("the service returned', '        if self.spent >= self.ceiling:\n            raise BudgetStop("the service returned', 'test_tinker_backend'),
    ("tinker: overrun may pass the ceiling", "tinker_backend.py", "        if self.spent >= self.ceiling:\n            raise BudgetStop(\"the service returned", "        if False:\n            raise BudgetStop(\"the service returned", "test_tinker_backend"),
    ("tinker: under-use not refunded", "tinker_backend.py", "            self.refund(kind, reserved - actual)\n            return", "            return", "test_tinker_backend"),
    ("tinker: prefill not counted", "tinker_backend.py", "        meter.reserve(\"prefill\", len(ids))", "        pass", "test_tinker_backend"),
    ("tinker: training tokens not counted", "tinker_backend.py", "        self.meter.reserve(\"train\", tokens)", "        pass", "test_tinker_backend"),
    ("tinker: prompt tokens get loss", "tinker_backend.py", "    w = [0] * len(prompt_ids) + [1] * len(target_ids)", "    w = [1] * len(prompt_ids) + [1] * len(target_ids)", "test_tinker_backend"),
    ("tinker: wrong model id", "tinker_backend.py", "MODEL_ID = \"thinkingmachines/Inkling-2-Mini\"", "MODEL_ID = \"thinkingmachines/Inkling-2-Small\"", "test_tinker_backend"),
    ("tinker: wrong train price", "tinker_backend.py", "    \"train\": Fraction(3, 4),", "    \"train\": Fraction(1, 2),", "test_tinker_backend"),
    ("cost: rounding", "cost.py", "    q = (x * scale * 2 + 1) // 2", "    q = (x * scale) // 1", "test_cost"),
    ("cost: training counts only the target", "cost.py", "        out.append((prompt, got[tgt] + codec.REPLY_OVERHEAD))", "        out.append((0, got[tgt] + codec.REPLY_OVERHEAD))", "test_cost"),
    ("cost: reply overhead dropped from the target", "cost.py", "        out.append((prompt, got[tgt] + codec.REPLY_OVERHEAD))", "        out.append((prompt, got[tgt]))", "test_cost"),
    ("cost: sample bound without the overhead", "cost.py", "        sm = (plan.cap + codec.REPLY_OVERHEAD) * len(ev) * e.runs", "        sm = plan.cap * len(ev) * e.runs", "test_cost"),
    ("cost: markers not counted per message", "cost.py", "        prompt = sys_tokens + sum(got[m] + codec.MARKERS_PER_MESSAGE for m in msgs)", "        prompt = sys_tokens + sum(got[m] for m in msgs)", "test_cost"),
    ("cost: runs not multiplied into prefill", "cost.py", "        pf = sum(p for p, _ in ev) * e.runs", "        pf = sum(p for p, _ in ev)", "test_cost"),
    ("cost: seeds not multiplied into training", "cost.py", "        n = per_run * plan.seeds", "        n = per_run", "test_cost"),
    ("cost: pilot overlaps the full run", "cost.py", "PILOT_TRAIN_OFFSET = 2000", "PILOT_TRAIN_OFFSET = 0", "test_cost"),
    ("ratchet: counts not recomputed from the outcomes", "ratchet.py", "        if (r.n, r.passed, r.failed, r.format_broken) != (len(s), s.count(\"P\"), s.count(\"F\"), s.count(\"X\")):", "        if False:", "test_ratchet"),
    ("ratchet: odd outcome letters accepted", "ratchet.py", "        if not isinstance(s, str) or not s or any(ch not in \"PFX\" for ch in s):", "        if False:", "test_ratchet"),
    ('ratchet: unrecorded result accepted', 'ratchet.py', '            if not matches:', '            if False:', 'test_ratchet'),
    ("ratchet: decide does not require receipts", "ratchet.py", "        self._require_recorded((base, cand))", "        pass", "test_ratchet"),
    ("ratchet: compare_arms does not require receipts", "ratchet.py", "        self._require_recorded((first, second))", "        pass", "test_ratchet"),
    ("ratchet: second-set results not recorded", "ratchet.py", "            self.record(out[key], decision_id, config)", "            pass", "test_ratchet"),
    ("paired: unknown test accepted", "ratchet.py", "    if test not in TESTS:", "    if False:", "test_ratchet"),
    ("paired: lengths not compared", "ratchet.py", "    if len(first_outcomes) != len(second_outcomes):", "    if False:", "test_ratchet"),
    ("paired: stratum keeps broken replies", "ratchet.py", "    if test == \"stratum\":", "    if False:", "test_ratchet"),
    ("paired: stratum drops only the first's breaks", "ratchet.py", "        pairs = [(a, b) for a, b in pairs if a != \"X\" and b != \"X\"]", "        pairs = [(a, b) for a, b in pairs if a != \"X\"]", "test_ratchet"),
    ("paired: format test counts passes", "ratchet.py", "    hit = (lambda o: o != \"X\") if test == \"format\" else (lambda o: o == \"P\")", "    hit = lambda o: o == \"P\"", "test_ratchet"),
    ("codec: two markers may share an id", "codec.py", "        if len(set(ids)) != len(ids):", "        if False:", "test_codec"),
    ("codec: a marker may be several tokens", "codec.py", "            if len(got) != 1:", "            if False:", "test_codec"),
    ("codec: a marker need not be an integer", "codec.py", "        if not isinstance(got, int) or isinstance(got, bool):", "        if False:", "test_codec"),
    ("codec: unknown role accepted", "codec.py", "        if role not in self.role:", "        if False:", "test_codec"),
    ("codec: prompt without the messages", "codec.py", "            ids += self.message_ids(m[\"role\"], m[\"content\"])", "            pass", "test_codec"),
    ("codec: prompt without the system line", "codec.py", "        ids = self.message_ids(\"system\", self.system_line)", "        ids = []", "test_codec"),
    ("codec: stop only on the end marker", "codec.py", "        return [self.end, self.eos]", "        return [self.end]", "test_codec"),
    ("codec: cut not reported", "codec.py", "        was_cut = len(out) > cap", "        was_cut = False", "test_codec"),
    ("codec: reply not cut at the cap", "codec.py", "        out = out[:cap]", "        pass", "test_codec"),
    ("codec: wrong system line", "codec.py", "SYSTEM_LINE = \"Thinking effort level: 0\"", "SYSTEM_LINE = \"Thinking effort level: 0.0\"", "test_codec"),
    ("codec: wrong marker count per message", "codec.py", "MARKERS_PER_MESSAGE = 3", "MARKERS_PER_MESSAGE = 2", "test_codec"),
    ("codec: wrong end count", "codec.py", "END_TOKENS = 1", "END_TOKENS = 0", "test_codec"),
    ("driver: partial batches trained", "driver.py", "    if n < 1 or n % batch_size != 0:", "    if False:", "test_driver"),
    ("driver: no shuffle", "driver.py", "    order = shuffled_order(n, seed, label)", "    order = list(range(n))", "test_driver"),
    ("driver: no training step sent", "driver.py", "        run.train_step(label, datums, learning_rate)", "        pass", "test_driver"),
    ("driver: plan not computed from cost", "driver.py", "    totals, _items = cost.plan_counts(plan, counter)", "    totals = {\"train\": 1, \"prefill\": 1, \"sample\": 1}", "test_driver"),
    ("driver: format gate reads the wrong way", "driver.py", "ratchet.compare_arms(\"%s-format\" % tag, b_own, c_own, \"format\")", "ratchet.compare_arms(\"%s-format\" % tag, c_own, b_own, \"format\")", "test_driver"),
    ("driver: stratum test is the pass test", "driver.py", "ratchet.compare_arms(\"%s-stratum\" % tag, c_own, b_own, \"stratum\")", "ratchet.compare_arms(\"%s-stratum\" % tag, c_own, b_own, \"pass\")", "test_driver"),
    ('driver: second set touched without both seeds', 'driver.py', '    if not all(v == "support" for v in summary["verdicts"]["set1"].values()):', '    if not any(v == "support" for v in summary["verdicts"]["set1"].values()):', 'test_driver'),
    ('driver: set 2 never decides', 'driver.py', '    summary["support"] = summary["verdict"] == "support"', '    summary["support"] = True', 'test_driver'),
    ("driver: set 2 compares the wrong adapter", "driver.py", "    entries = [(\"C\", responder(run, samplers[(\"C\", 0)], codec, cap), \"C\", c0),", "    entries = [(\"C\", responder(run, samplers[(\"C\", 1)], codec, cap), \"C\", c0),", "test_driver"),
    ("driver: tokenizer fit not checked", "driver.py", "        return codec_mod.Codec(tok)", "        return tok", "test_driver"),
    ("power: fewer than ten discordant counted", "power.py", "    if d < MIN_DISCORDANT:\n        return None", "    if False:\n        return None", "test_power"),
    ("power: threshold search does not stop", "power.py", "        if tail * alpha.denominator > alpha.numerator * 2 ** d:\n            break", "        if False:\n            break", "test_power"),
    ("power: bad parts accepted", "power.py", "    if min(p_num, q_num, r_num) < 0 or den < 1 or n < 1:", "    if False:", "test_power"),
    ("power: minimum discordant", "power.py", "MIN_DISCORDANT = 10", "MIN_DISCORDANT = 5", "test_power"),
    ('ledger: a partial last line accepted', 'tinker_backend.py', '        if raw and not raw.endswith(b"\\n"):\n            raise BudgetError("the spend ledger ends', '        if False:\n            raise BudgetError("the spend ledger ends', 'test_tinker_backend'),
    ('ledger: invalid JSON accepted', 'tinker_backend.py', '            except (ValueError, ApprovalError):', '            except ZeroDivisionError:', 'test_tinker_backend'),
    ('ledger: floats accepted', 'tinker_backend.py', 'json.loads(ln.decode("utf-8"), parse_float=_refuse_float)', 'json.loads(ln.decode("utf-8"))', 'test_tinker_backend'),
    ('ledger: malformed lines accepted', 'tinker_backend.py', '            if not isinstance(row, dict) or not isinstance(row.get("run_id"), str) or not isinstance(row.get("ev"), str):', '            if False:', 'test_tinker_backend'),
    ('ledger: other run ids counted', 'tinker_backend.py', '            if row["run_id"] != self.run_id:', '            if False:', 'test_tinker_backend'),
    ('ledger: starts not counted', 'tinker_backend.py', '                starts += 1\n                continue', '                continue', 'test_tinker_backend'),
    ('ledger: first plan id not kept', 'tinker_backend.py', '                if starts == 0:\n                    plan_id = row.get("plan_id")', '                if False:\n                    plan_id = row.get("plan_id")', 'test_tinker_backend'),
    ('ledger: malformed entries accepted', 'tinker_backend.py', '            if row["ev"] not in ("reserve", "adjust") or row.get("kind") not in PRICES_PER_MILLION \\\n                    or not isinstance(n, int) or isinstance(n, bool) or (row["ev"] == "reserve" and n < 0):', '            if False:', 'test_tinker_backend'),
    ('ledger: a negative reservation accepted', 'tinker_backend.py', 'or (row["ev"] == "reserve" and n < 0):', 'or False:', 'test_tinker_backend'),
    ('ledger: a refund beyond the reservations accepted', 'tinker_backend.py', '            if tokens[row["kind"]] < 0:', '            if False:', 'test_tinker_backend'),
    ('ledger: not flushed to disk', 'tinker_backend.py', '                os.fsync(fh.fileno())', '                pass', 'test_tinker_backend'),
    ('ledger: a failed write ignored', 'tinker_backend.py', '        except OSError:\n            raise BudgetStop("the spend ledger cannot be written', '        except OSError:\n            pass\n        else:\n            return\n        if False:\n            raise BudgetStop("the spend ledger cannot be written', 'test_tinker_backend'),
    ('meter: reservation not written', 'tinker_backend.py', '        self._log("reserve", kind, tokens)', '        pass', 'test_tinker_backend'),
    ('meter: refund not written', 'tinker_backend.py', '        self._log("adjust", kind, -tokens)', '        pass', 'test_tinker_backend'),
    ('meter: overrun not written', 'tinker_backend.py', '        self._log("adjust", kind, extra)', '        pass', 'test_tinker_backend'),
    ('meter: room check ignores what is spent', 'tinker_backend.py', '        if self.spent + planned_cost(plan_tokens) >= self.ceiling:', '        if planned_cost(plan_tokens) >= self.ceiling:', 'test_tinker_backend'),
    ('meter: room check may land on the ceiling', 'tinker_backend.py', '        if self.spent + planned_cost(plan_tokens) >= self.ceiling:', '        if self.spent + planned_cost(plan_tokens) > self.ceiling:', 'test_tinker_backend'),
    ('tinker: a started run id restarts without resume', 'tinker_backend.py', '        if starts and not resume:', '        if False:', 'test_tinker_backend'),
    ('tinker: a resume may change the plan', 'tinker_backend.py', '        if starts and first_plan != plan_id:', '        if False:', 'test_tinker_backend'),
    ('tinker: earlier spend not carried over', 'tinker_backend.py', '            self.meter = Meter(approval.ceiling, ledger, spent, tokens)', '            self.meter = Meter(approval.ceiling, ledger)', 'test_tinker_backend'),
    ('tinker: start not written', 'tinker_backend.py', '        ledger.append({"ev": "start", "plan_id": plan_id})', '        pass', 'test_tinker_backend'),
    ('tinker: cut reply not reported', 'tinker_backend.py', '        return text, count, was_cut                    # a cut reply is a format break (evaluate.py)', '        return text, count, False', 'test_tinker_backend'),
    ('tinker: cut replies not counted', 'tinker_backend.py', '        self.stats["cut"] += 1 if was_cut else 0', '        self.stats["cut"] += 0', 'test_tinker_backend'),
    ('tinker: calls not counted', 'tinker_backend.py', '        self.stats["calls"] += 1', '        self.stats["calls"] += 0', 'test_tinker_backend'),
    ('eval: a cut reply that still parses is scored', 'evaluate.py', '    if was_cut:\n        return "X"\n    cand, _why', '    if False:\n        return "X"\n    cand, _why', 'test_evaluate'),
    ('eval: a cut by the harness not a break', 'evaluate.py', '            was_cut = was_cut or harness_cut', '            was_cut = was_cut', 'test_evaluate'),
    ('eval: the responder cut flag ignored', 'evaluate.py', '            was_cut = len(got) > 2 and bool(got[2])', '            was_cut = False', 'test_evaluate'),
    ('eval: rescore ignores the episode set', 'evaluate.py', '    if epset.sha256() != entry["set_sha256"]:', '    if False:', 'test_evaluate'),
    ('eval: rescore ignores misaligned replies', 'evaluate.py', '    if not (len(ids) == len(texts) == len(cuts)) or any(c not in "01" for c in cuts):', '    if False:', 'test_evaluate'),
    ('eval: odd episode ids rebuilt', 'evaluate.py', '            if len(parts) != 3 or not parts[2].isdigit() or parts[0] not in ep_mod.KIND_BASE:', '            if False:', 'test_evaluate'),
    ('eval: an empty or mixed set rebuilt', 'evaluate.py', '        if not eps or len({ep.kind for ep in eps}) != 1:', '        if False:', 'test_evaluate'),
    ('eval: out-of-range episodes rebuilt', 'evaluate.py', '            except ep_mod.EpisodeError as exc:\n                raise EvalRefused("episode %s: %s" % (eid, exc))', '            except ZeroDivisionError as exc:\n                raise EvalRefused("episode %s: %s" % (eid, exc))', 'test_evaluate'),
    ('latch: a token for an unregistered id accepted', 'latch.py', '    if token.decision_id not in registry:', '    if False:', 'test_ratchet'),
    ('latch: touch not written to the chain', 'latch.py', '        self.head = receipts.append(self.receipts_path, {"kind": "touch", "decision_id": decision_id,\n                                                         "uses": [list(p) for p in pairs]}, self.head)', '        pass', 'test_ratchet'),
    ('latch: touches in the chain not counted', 'latch.py', '        out = [b["decision_id"] for b in receipts.bodies(self.receipts_path) if b.get("kind") == "touch"]', '        out = []', 'test_ratchet'),
    ('latch: touches in the latch file not counted', 'latch.py', '        if os.path.exists(self.path):\n            with open(self.path, "r", encoding="utf-8") as fh:\n                for line in fh:', '        if False:\n            with open(self.path, "r", encoding="utf-8") as fh:\n                for line in fh:', 'test_ratchet'),
    ('latch: every receipt counted as a touch', 'latch.py', 'if b.get("kind") == "touch"]', 'if True]', 'test_ratchet'),
    ('latch: touch appended without the expected head', 'latch.py', '"uses": [list(p) for p in pairs]}, self.head)', '"uses": [list(p) for p in pairs]})', 'test_ratchet'),
    ('ratchet: record skips the rescore', 'ratchet.py', '        self._rescored(result.replies_entry(), result)', '        pass', 'test_ratchet'),
    ('ratchet: record skips the recount', 'ratchet.py', '        self._recount(result)\n        self._rescored(', '        self._rescored(', 'test_ratchet'),
    ('ratchet: rescored outcomes not compared', 'ratchet.py', '        if again != r.outcomes:', '        if False:', 'test_ratchet'),
    ('ratchet: replies hash not compared', 'ratchet.py', '        if evaluate.canonical_sha256(entry["texts"]) != r.replies_sha256:', '        if False:', 'test_ratchet'),
    ('ratchet: replies entry may be missing or edited', 'ratchet.py', '            if entry is None or evaluate.canonical_sha256(entry) != matches[0]["replies_entry_sha256"]:', '            if False:', 'test_ratchet'),
    ('ratchet: chain head not checked on read', 'ratchet.py', '        return receipts.bodies(self.receipts_path, self.head)', '        return receipts.bodies(self.receipts_path)', 'test_ratchet'),
    ('ratchet: chain head not checked on append', 'ratchet.py', '        self.head = receipts.append(self.receipts_path, body, self.head)', '        self.head = receipts.append(self.receipts_path, body)', 'test_ratchet'),
    ('ratchet: head not handed to the latch', 'ratchet.py', '        self.latch.head = self.head\n', '', 'test_ratchet'),
    ('ratchet: head not taken back from the latch', 'ratchet.py', '        self.head = self.latch.head\n', '', 'test_ratchet'),
    ('ratchet: replies stored again and again', 'ratchet.py', '        if key not in self._stored_replies():', '        if True:', 'test_ratchet'),
    ('ratchet: replies not named in the receipt', 'ratchet.py', '"replies_entry_sha256": self._store_replies(result)', '"replies_entry_sha256": "0" * 64', 'test_ratchet'),
    ('ratchet: comparison hides the pass counts', 'ratchet.py', '"first_passed": first.passed, "second_passed": second.passed, "n": first.n,\n                "first_better"', '"first_passed": 0, "second_passed": 0, "n": 1,\n                "first_better"', 'test_ratchet'),
    ('ratchet: measurement not appended', 'ratchet.py', '        return self._append(body)\n\n    def _store_replies', '        return None\n\n    def _store_replies', 'test_ratchet'),
    ('driver: gate on discordant episodes changed', 'driver.py', 'GATES = Gates(power.MIN_DISCORDANT, Fraction(1, 20), Fraction(19, 20))', 'GATES = Gates(9, Fraction(1, 20), Fraction(19, 20))', 'test_driver'),
    ('driver: floor gate changed', 'driver.py', 'GATES = Gates(power.MIN_DISCORDANT, Fraction(1, 20), Fraction(19, 20))', 'GATES = Gates(power.MIN_DISCORDANT, Fraction(1, 10), Fraction(19, 20))', 'test_driver'),
    ('driver: ceiling gate changed', 'driver.py', 'GATES = Gates(power.MIN_DISCORDANT, Fraction(1, 20), Fraction(19, 20))', 'GATES = Gates(power.MIN_DISCORDANT, Fraction(1, 20), Fraction(9, 10))', 'test_driver'),
    ('driver: nine discordant episodes enough', 'driver.py', '    if cmp_["first_only"] + cmp_["second_only"] < g.min_discordant:', '    if cmp_["first_only"] + cmp_["second_only"] <= g.min_discordant:', 'test_driver'),
    ('driver: no discordant minimum', 'driver.py', '    if cmp_["first_only"] + cmp_["second_only"] < g.min_discordant:', '    if False:', 'test_driver'),
    ('driver: the floor itself is testable', 'driver.py', '        if rate <= g.rate_low or rate >= g.rate_high:', '        if rate < g.rate_low or rate >= g.rate_high:', 'test_driver'),
    ('driver: the ceiling itself is testable', 'driver.py', '        if rate <= g.rate_low or rate >= g.rate_high:', '        if rate <= g.rate_low or rate > g.rate_high:', 'test_driver'),
    ('driver: no rate gates', 'driver.py', '        if rate <= g.rate_low or rate >= g.rate_high:', '        if False:', 'test_driver'),
    ('driver: only the first adapter checked for rates', 'driver.py', '    for passed in (cmp_["first_passed"], cmp_["second_passed"]):', '    for passed in (cmp_["first_passed"],):', 'test_driver'),
    ('driver: only the second adapter checked for rates', 'driver.py', '    for passed in (cmp_["first_passed"], cmp_["second_passed"]):', '    for passed in (cmp_["second_passed"],):', 'test_driver'),
    ('driver: the stratum is not judged', 'driver.py', '    for name, label in (("pass", "all episodes"), ("stratum", "the format stratum")):', '    for name, label in (("pass", "all episodes"),):', 'test_driver'),
    ('driver: testability not required', 'driver.py', '        if not testable(cmp_[name], gates):', '        if False:', 'test_driver'),
    ('driver: a win not required', 'driver.py', '        if not cmp_[name]["first_better"]:', '        if False:', 'test_driver'),
    ('driver: format harm not judged', 'driver.py', '    if cmp_["format_harm"]["first_better"]:\n        return "not_supported"', '    if False:\n        return "not_supported"', 'test_driver'),
    ('driver: conditions_met reads the wrong verdict', 'driver.py', '    return judge(cmp_)[0] == "support"', '    return judge(cmp_)[0] != "cannot_test"', 'test_driver'),
    ('driver: overall verdict needs only one support', 'driver.py', '    if all(v == "support" for v in verdicts):', '    if any(v == "support" for v in verdicts):', 'test_driver'),
    ('driver: a failed item is not reported as not_supported', 'driver.py', '    if any(v == "not_supported" for v in verdicts):', '    if False:', 'test_driver'),
    ('driver: control readings take every comparison', 'driver.py', '            if name.startswith("control_")}', '            if True}', 'test_driver'),
    ('driver: the set-2 bound drops the overhead', 'driver.py', '(plan.cap + codec_mod.REPLY_OVERHEAD)}', 'plan.cap}', 'test_driver'),
    ('driver: the set-2 bound drops a text', 'driver.py', '    for text in ("C", "B", "E", "N"):', '    for text in ("C", "B", "E"):', 'test_driver'),
    ('driver: no headroom check before the touch', 'driver.py', '    run.meter.require_room(set2_bound(plan, codec, h2))', '    pass', 'test_driver'),
    ('driver: any plan name runs', 'driver.py', '    if plan.name != name:', '    if False:', 'test_driver'),
    ('driver: a run for another plan is accepted', 'driver.py', '    if run.plan_id != fingerprint:', '    if False:', 'test_driver'),
    ('driver: the run is not tied to the plan', 'driver.py', 'plan.name, fingerprint, service, types_mod, resume)', 'plan.name, None, service, types_mod, resume)', 'test_driver'),
    ('driver: the run is not marked with the plan it counted', 'driver.py', '    run.counted_plan = fingerprint', '    run.counted_plan = None', 'test_driver'),
    ('driver: a run not counted by start_run is accepted', 'driver.py', '    if getattr(run, "counted_plan", None) != fingerprint:', '    if False:', 'test_driver'),
    ('driver: the approval row names no plan', 'driver.py', '"plan": plan.name, "plan_id": plan_fingerprint(plan)}', '"plan": plan.name, "plan_id": "x"}', 'test_driver'),
    ('driver: a format harm is judged only when items 1 and 2 are testable', 'driver.py', '    if cmp_["format_harm"]["first_better"]:\n        return "not_supported", "C breaks', '    if cmp_["format_harm"]["first_better"] and testable(cmp_["pass"], gates) and testable(cmp_["stratum"], gates):\n        return "not_supported", "C breaks', 'test_driver'),
    ('driver: the full run ignores the registered plan check', 'driver.py', '    require_plan_run(run, plan, "full")', '    pass', 'test_driver'),
    ('driver: the pilot ignores the plan check', 'driver.py', '    require_plan_run(run, plan, "pilot")', '    pass', 'test_driver'),
    ('driver: the first set ignores its offset', 'driver.py', '    h1 = ep_mod.build_set("heldout1", plan.eval1_counts, plan.eval1_offset)', '    h1 = ep_mod.build_set("heldout1", plan.eval1_counts)', 'test_driver'),
    ('driver: the pilot trains on the wrong seeds', 'driver.py', '    train = ep_mod.build_set("train", plan.train_counts, plan.train_offset)\n    ev =', '    train = ep_mod.build_set("train", plan.train_counts)\n    ev =', 'test_driver'),
    ('driver: the pilot evaluates on the wrong seeds', 'driver.py', '    ev = ep_mod.build_set("train", plan.eval1_counts, plan.eval1_offset)', '    ev = ep_mod.build_set("train", plan.eval1_counts)', 'test_driver'),
    ('driver: the pilot evaluates the wrong text', 'driver.py', 'evaluate.evaluate_arm(timed, ev, "C", ratchet.cap, descriptor)', 'evaluate.evaluate_arm(timed, ev, "B", ratchet.cap, descriptor)', 'test_driver'),
    ('driver: the pilot writes no receipt', 'driver.py', '    ratchet.measure({"kind": "pilot", "run_id": run_id, "go": 1 if gates["go"] else 0, **m})', '    pass', 'test_driver'),
    ('driver: step time is not the step', 'driver.py', '            step_ns.append(clock() - t0)', '            step_ns.append(clock())', 'test_driver'),
    ('driver: call time is not the call', 'driver.py', '        self.call_ns.append(self.clock() - t0)', '        self.call_ns.append(self.clock())', 'test_driver'),
    ('driver: the pilot gate on format breaks changed', 'driver.py', 'Fraction(m["adapter_format_broken"], n) <= PILOT_MAX_FORMAT_BREAK', 'Fraction(m["adapter_format_broken"], n) < PILOT_MAX_FORMAT_BREAK', 'test_driver'),
    ('driver: the pilot floor is testable', 'driver.py', 'PILOT_RATE_LOW < rate < PILOT_RATE_HIGH', 'PILOT_RATE_LOW <= rate < PILOT_RATE_HIGH', 'test_driver'),
    ('driver: the pilot ceiling is testable', 'driver.py', 'PILOT_RATE_LOW < rate < PILOT_RATE_HIGH', 'PILOT_RATE_LOW < rate <= PILOT_RATE_HIGH', 'test_driver'),
    ('driver: the pilot time limit changed', 'driver.py', 'projected <= PILOT_MAX_HOURS * NS_PER_HOUR', 'projected < PILOT_MAX_HOURS * NS_PER_HOUR', 'test_driver'),
    ('driver: the pilot ignores training time', 'driver.py', '+ Fraction(m["train_ns"], m["steps"]) * full_steps', '', 'test_driver'),
    ('driver: plan calls ignore the runs', 'driver.py', 'calls = sum(sizes[e.set_key] * e.runs for e in plan.evals)', 'calls = sum(sizes[e.set_key] for e in plan.evals)', 'test_driver'),
    ('driver: plan steps ignore the seeds', 'driver.py', '// BATCH_SIZE * plan.epochs * plan.seeds for _arm in plan.arms)', '// BATCH_SIZE * plan.epochs for _arm in plan.arms)', 'test_driver'),
    ('driver: the pilot go not recorded', 'driver.py', '    gates["go"] = all(gates.values())', '    gates["go"] = True', 'test_driver'),
    ('power: no effect reaches the target but one is returned', 'power.py', '    if rule_power_at(n, share, hi) < target:', '    if False:', 'test_power'),
    ('power: a power equal to the target does not count', 'power.py', '        if rule_power_at(n, share, mid) >= target:', '        if rule_power_at(n, share, mid) > target:', 'test_power'),
    ('power: wrong discordant shares', 'power.py', '    return rule_power(power(n, 2 * share + halves, 2 * share - halves, 400))', '    return rule_power(power(n, 2 * share + halves, 2 * share + halves, 400))', 'test_power'),
    ('power: half points written as tenths', 'power.py', '    return "%d.%d" % (h // 2, 5 * (h % 2))', '    return "%d.%d" % (h // 2, h % 2)', 'test_power'),
    ("tinker: limit ignores the end marker", "tinker_backend.py", "        limit = self.cap + codec_mod.REPLY_OVERHEAD    # the reply and the end marker", "        limit = self.cap", "test_tinker_backend"),
    ("tinker: limit still counts the turn opening", "tinker_backend.py", "        limit = self.cap + codec_mod.REPLY_OVERHEAD    # the reply and the end marker", "        limit = self.cap + codec_mod.REPLY_OVERHEAD + codec_mod.OPENING_TOKENS", "test_tinker_backend"),
    ("tinker: accepted prompts not counted", "tinker_backend.py", '        self.stats["accepted"] += 1', "        pass", "test_tinker_backend"),
    ("tinker: new blocks not counted", "tinker_backend.py", '        self.stats["new_block"] += 1 if self.codec.opens_new_block(out) else 0', '        self.stats["new_block"] += 0', "test_tinker_backend"),
    ("tinker: several sequences accepted", "tinker_backend.py", "        if len(seqs) != 1:", "        if False:", "test_tinker_backend"),
    ("cost: system line not counted", "cost.py", "    sys_tokens = got[codec.SYSTEM_LINE] + codec.MARKERS_PER_MESSAGE + codec.OPENING_TOKENS", "    sys_tokens = codec.OPENING_TOKENS", "test_cost"),
    ("cost: forced opening not counted in the prompt", "cost.py", "    sys_tokens = got[codec.SYSTEM_LINE] + codec.MARKERS_PER_MESSAGE + codec.OPENING_TOKENS", "    sys_tokens = got[codec.SYSTEM_LINE] + codec.MARKERS_PER_MESSAGE", "test_cost"),
    ("codec: ordinary text may yield a marker", "codec.py", "        if any(i in self._marker_names for i in ids):", "        if False:", "test_codec"),
    ("codec: the thinking marker is not a marker", "codec.py", "        ids = list(self.role.values()) + [self.content, self.end, self.eos, self.thinking]", "        ids = list(self.role.values()) + [self.content, self.end, self.eos]", "test_codec"),
    ("codec: target without the end marker", "codec.py", "        return self._ordinary(text) + [self.end]", "        return self._ordinary(text)", "test_codec"),
    ("codec: target carries the turn opening", "codec.py", "        return self._ordinary(text) + [self.end]", "        return self.opening_ids() + self._ordinary(text) + [self.end]", "test_codec"),
    ("codec: prompt without the forced opening", "codec.py", "        return ids + self.opening_ids()", "        return ids", "test_codec"),
    ("codec: forced opening with the wrong role", "codec.py", "        return [self.role[\"assistant\"], self.content]", "        return [self.role[\"user\"], self.content]", "test_codec"),
    ("codec: forced opening without the content marker", "codec.py", "        return [self.role[\"assistant\"], self.content]", "        return [self.role[\"assistant\"]]", "test_codec"),
    ("codec: reply not cut at the end marker", "codec.py", "            if i in (self.end, self.eos):\n                break", "            if i == self.end:\n                break", "test_codec"),
    ("codec: a stop id does not end the new-block scan", "codec.py", "            if i in (self.end, self.eos):\n                return False", "            if i == self.end:\n                return False", "test_codec"),
    ("codec: a marker in the reply is not a new block", "codec.py", "            if self.is_marker(i):\n                return True", "            if False:\n                return True", "test_codec"),
    ("codec: the layout's own markers are not markers", "codec.py", "        return i in self._marker_names or bool(", "        return False or bool(", "test_codec"),
    ("codec: other special ids are not markers", "codec.py", "        return i in self._marker_names or bool(self._is_special is not None and self._is_special(i))", "        return i in self._marker_names", "test_codec"),
    ("codec: a tokenizer without is_special_token is not tolerated", "codec.py", "self._is_special is not None and self._is_special(i)", "self._is_special(i)", "test_codec"),
    # the run lock and the approval's plan
    ("tinker: the run lock is never taken", "tinker_backend.py", "        self.lock_fd = acquire_lock(ledger_path + \".lock\")", "        self.lock_fd = None", "test_tinker_backend"),
    ("tinker: the run lock is shared", "tinker_backend.py", "fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)", "fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)", "test_tinker_backend"),
    ("tinker: a second holder is let in", "tinker_backend.py", "        raise ApprovalError(\"another process holds this run", "        return fd\n        raise ApprovalError(\"another process holds this run", "test_tinker_backend"),
    ("tinker: a refused start keeps the lock", "tinker_backend.py", "        except BaseException:\n            self.close()\n            raise", "        except BaseException:\n            raise", "test_tinker_backend"),
    ("tinker: close does not release the lock", "tinker_backend.py", "    os.close(fd)               # closing the descriptor drops the flock", "    pass", "test_tinker_backend"),
    ("tinker: close keeps the descriptor", "tinker_backend.py", "            release_lock(self.lock_fd)\n            self.lock_fd = None", "            release_lock(self.lock_fd)", "test_tinker_backend"),
    ("tinker: a lock that cannot be opened is ignored", "tinker_backend.py", "        raise BudgetStop(\"the run lock cannot be opened", "        return None\n        raise BudgetStop(\"the run lock cannot be opened", "test_tinker_backend"),
    ("tinker: any plan name runs under an approval", "tinker_backend.py", "        if approval.plan != plan_name or approval.plan_id != plan_id:", "        if approval.plan_id != plan_id:", "test_tinker_backend"),
    ("tinker: any plan fingerprint runs under an approval", "tinker_backend.py", "        if approval.plan != plan_name or approval.plan_id != plan_id:", "        if approval.plan != plan_name:", "test_tinker_backend"),
    ("tinker: an approval needs no plan", "tinker_backend.py", "            if not isinstance(plan, str) or not plan or not isinstance(plan_id, str) or not plan_id:", "            if False:", "test_tinker_backend"),
    ("tinker: an approval with an empty plan name", "tinker_backend.py", "            if not isinstance(plan, str) or not plan or not isinstance(plan_id, str) or not plan_id:", "            if not isinstance(plan, str) or not isinstance(plan_id, str) or not plan_id:", "test_tinker_backend"),
    ("tinker: an approval with an empty fingerprint", "tinker_backend.py", "            if not isinstance(plan, str) or not plan or not isinstance(plan_id, str) or not plan_id:", "            if not isinstance(plan, str) or not plan or not isinstance(plan_id, str):", "test_tinker_backend"),
    ("tinker: the ledger sits somewhere else", "tinker_backend.py", "        ledger_path = approvals_path + \".spend.jsonl\"", "        ledger_path = approvals_path + \".other.jsonl\"", "test_tinker_backend"),
    ("codec: a marker in the reply is decoded as text", "codec.py", "        for i in out:\n            if i in self._marker_names:", "        for i in out:\n            if False:", "test_codec"),
    ("codec: wrong forced opening count", "codec.py", "OPENING_TOKENS = 2", "OPENING_TOKENS = 1", "test_codec"),
    ("codec: end marker counted twice in the reply overhead", "codec.py", "REPLY_OVERHEAD = END_TOKENS", "REPLY_OVERHEAD = END_TOKENS + 1", "test_codec"),
    ('driver: the pilot gate on new blocks changed', 'driver.py', 'Fraction(m["new_block"], m["calls"]) <= PILOT_MAX_NEW_BLOCK', 'Fraction(m["new_block"], m["calls"]) < PILOT_MAX_NEW_BLOCK', 'test_driver'),
    ('driver: the pilot gate on the accepted opening is slack', 'driver.py', 'm["accepted"] == m["calls"]', 'm["accepted"] >= 0', 'test_driver'),
    # pilot_cli.py: the runner's refusals, redaction and output guards
    ("pilot_cli: a used out directory accepted", "pilot_cli.py", "    if os.path.exists(out) and (not os.path.isdir(out) or os.listdir(out)):", "    if False:", "test_pilot_cli"),
    ("pilot_cli: real mode without the key variable", "pilot_cli.py", "    if not opts[\"fake\"] and not env.get(KEY_VAR):", "    if False:", "test_pilot_cli"),
    ("pilot_cli: any approved ceiling accepted", "pilot_cli.py", "    if approval.ceiling > PILOT_CEILING:", "    if False:", "test_pilot_cli"),
    ("pilot_cli: a request for another episode or text accepted", "pilot_cli.py", "        if view.arm != \"C\" or view.messages != want.messages:", "        if False:", "test_pilot_cli"),
    ("pilot_cli: more requests than evaluation episodes", "pilot_cli.py", "        if self.i >= len(self.expected.episodes):", "        if False:", "test_pilot_cli"),
    ("pilot_cli: a plan other than the pilot recorded", "pilot_cli.py", "    if plan.name != \"pilot\" or plan.eval2_counts:", "    if False:", "test_pilot_cli"),
    ("pilot_cli: a held-out evaluation set accepted", "pilot_cli.py", "    if expected.kind != \"train\":", "    if False:", "test_pilot_cli"),
    ("pilot_cli: a third sampling model accepted", "pilot_cli.py", "        if len(made) >= len(MODEL_ORDER):", "        if False:", "test_pilot_cli"),
    ("pilot_cli: logged replies not checked against the outcomes", "pilot_cli.py", "                    if \"\".join(rec.outcomes) != got[\"results\"][name].outcomes:", "                    if False:", "test_pilot_cli"),
    ("pilot_cli: floats allowed in the result file", "pilot_cli.py", "    receipts.check_plain(res, \"pilot-result\")          # integers and strings only", "    pass", "test_pilot_cli"),
    ("pilot_cli: the key value kept in error text", "pilot_cli.py", "    if key:\n        text = text.replace(key, \"[REDACTED]\")", "    if False:\n        text = text.replace(key, \"[REDACTED]\")", "test_pilot_cli"),
    ("pilot_cli: error text not redacted", "pilot_cli.py", "    return tinker_backend.redact(text)", "    return text", "test_pilot_cli"),
    ("pilot_cli: an interrupt is not an incomplete run", "pilot_cli.py", "    except (Exception, KeyboardInterrupt) as exc:", "    except Exception as exc:", "test_pilot_cli"),
    ("pilot_cli: a start that fails is not a refusal", "pilot_cli.py", "    except (Exception,) as exc:             # nothing was spent: the run did not start", "    except ZeroDivisionError as exc:", "test_pilot_cli"),
    ("pilot_cli: replies not flushed as they arrive", "pilot_cli.py", "        self.fh.flush()\n", "", "test_pilot_cli"),
    ("pilot_cli: fake factories left in place", "pilot_cli.py", "        tinker_backend._real_service, tinker_backend._real_types = saved", "        pass", "test_pilot_cli"),
    ("tinker: training client not taken from its future", "tinker_backend.py", "            train_unembed=train_unembed).result())", "            train_unembed=train_unembed))", "test_tinker_backend"),
    ("tinker: base sampler not taken from its future", "tinker_backend.py", "create_sampling_client(base_model=MODEL_ID).result())", "create_sampling_client(base_model=MODEL_ID))", "test_tinker_backend"),
]


def run_tests(root, module):
    # the outer interpreter's -O and -W flags go through, so the guards are tested under them too
    cmd = [sys.executable, "-I", "-B"] + ["-O"] * sys.flags.optimize
    for w in sys.warnoptions:
        cmd += ["-W", w]
    cmd += ["-m", "unittest", "discover", "-f", "-q", "-s", "tests", "-p", module + ".py"]
    return subprocess.run(cmd, cwd=root, capture_output=True, text=True,
                          env={"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"})


def fresh_copy(dest):
    shutil.copytree(HERE, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def main(argv):
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    modules = sorted({m[4] for m in MUTATIONS})
    killed = survived = errors = 0
    with tempfile.TemporaryDirectory() as tmp:
        base = os.path.join(tmp, "base")
        fresh_copy(base)
        for mod in modules:
            r = run_tests(base, mod)
            if r.returncode != 0:
                print("BASELINE RED in %s:\n%s" % (mod, r.stderr[-800:]))
                return 2
        print("baseline green in %d test modules" % len(modules))
        for i, (name, fname, old, new, mod) in enumerate(MUTATIONS):
            if only and only not in name:
                continue
            root = os.path.join(tmp, "m%d" % i)
            fresh_copy(root)
            path = os.path.join(root, fname)
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
            n = text.count(old)
            if n != 1 or old == new:
                print("ERROR   %-55s the text matches %d times" % (name, n))
                errors += 1
                continue
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text.replace(old, new))
            r = run_tests(root, mod)
            if r.returncode != 0:
                killed += 1
                print("KILLED  %-55s by %s" % (name, mod))
            else:
                survived += 1
                print("SURVIVED %-54s %s" % (name, mod))
            shutil.rmtree(root)
    print("%d mutations: %d killed, %d survived, %d errors" % (killed + survived + errors, killed, survived, errors))
    return 0 if survived == 0 and errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
