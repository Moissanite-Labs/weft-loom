/-
  WeftInvariantsPureInit.lean
  Stock Lean 4 (`Init`-only) upgrade for Moissanite-Labs/weft `WeftInvariants.lean` (PR #128).

  Upgrades over initial `WeftInvariants.lean`:
  1. `6d8c96f` already removed the unused `Float` structure `OrthogonalUpdatePair` from
     `WeftInvariants.lean`. This file uses exact integer/rational scaled inner-product bounds.
  2. States `two_sided_overlap_mitosis_envelope` with two-sided overlap hypotheses
     `-ov <= inner /\ inner <= ov`. The theorem proves two conjuncts:
     `np + nc + 2 * inner <= rmax`, which follows from the upper bound `inner <= ov` and the
     budget alone, and `np + nc - 2 * ov <= np + nc + 2 * inner`, which is the lower bound
     `-ov <= inner` rewritten (`overlap_lower_conjunct_iff`). It does not give
     `np + nc - 2 * ov >= 0`; that fails at `np = nc = inner = rp = rc = 0`, `ov = 5`, `rmax = 10`.
     (Corrected 2026-11-14 after review 5907383990 on weft-loom#4.)
  3. Formalizes the division-free Mitotic Diagnostic Ratio (MDR) gate with an explicit orthogonal
     gradient floor `orthFloor <= gradOrth`, proving that sub-floor rounding dust
     (`gradOrth < orthFloor`, such as `3e-12` when `gradPar = 0`) can NEVER trigger mitosis.
-/

namespace WeftV2.PureInit

theorem pythagorean_mitosis_envelope
    (np nc inner rp rc rmax : Int)
    (h_orth : inner = 0)
    (h_p : np ≤ rp)
    (h_c : nc ≤ rc)
    (h_budget : rp + rc ≤ rmax) :
    np + nc + 2 * inner ≤ rmax := by
  subst h_orth
  omega

theorem two_sided_overlap_mitosis_envelope
    (np nc inner ov rp rc rmax : Int)
    (h_ov_lo : -ov ≤ inner)
    (h_ov_hi : inner ≤ ov)
    (h_p : np ≤ rp)
    (h_c : nc ≤ rc)
    (h_budget : rp + rc + 2 * ov ≤ rmax) :
    np + nc + 2 * inner ≤ rmax ∧ np + nc - 2 * ov ≤ np + nc + 2 * inner := by
  omega

/-- The second conjunct of `two_sided_overlap_mitosis_envelope` is the lower
    overlap hypothesis rewritten. -/
theorem overlap_lower_conjunct_iff (np nc inner ov : Int) :
    (np + nc - 2 * ov ≤ np + nc + 2 * inner) ↔ (-ov ≤ inner) := by
  omega

/-- The envelope conjunct needs only the upper overlap bound and the budget. -/
theorem overlap_envelope_from_upper_bound
    (np nc inner ov rp rc rmax : Int)
    (h_ov_hi : inner ≤ ov)
    (h_p : np ≤ rp)
    (h_c : nc ≤ rc)
    (h_budget : rp + rc + 2 * ov ≤ rmax) :
    np + nc + 2 * inner ≤ rmax := by
  omega

/-- Division-free MDR mitosis predicate over `Int`:
    triggers iff `err > errFloor`, `gradPar <= parCeil`, `gradOrth >= orthFloor`,
    `0 < mdrDen`, and `gradOrth * mdrDen >= mdrNum * gradPar`. With `0 < mdrDen`
    and `0 < gradPar`, the cross-multiplied clause is the ratio test
    `gradOrth / gradPar >= mdrNum / mdrDen` over the rationals. At `gradPar = 0`
    it reduces to `0 <= gradOrth * mdrDen`. (`0 < mdrDen` added 2026-11-14 after
    review 5907383990 on weft-loom#4; without it a negative denominator reverses
    the ratio reading.) -/
def mitosisTriggered
    (err errFloor gradPar parCeil gradOrth orthFloor mdrNum mdrDen : Int) : Prop :=
  err > errFloor ∧
  gradPar ≤ parCeil ∧
  orthFloor ≤ gradOrth ∧
  0 < mdrDen ∧
  gradOrth * mdrDen ≥ mdrNum * gradPar

/-- Proves that sub-floor rounding noise (`gradOrth < orthFloor`, e.g. `3e-12 < 1e-3`
    at `gradPar = 0`) never triggers mitosis. The proof uses the floor conjunct
    `orthFloor <= gradOrth` of `mitosisTriggered`. -/
theorem subfloor_noise_never_triggers_mitosis
    (err errFloor gradPar parCeil gradOrth orthFloor mdrNum mdrDen : Int)
    (h_dust : gradOrth < orthFloor) :
    ¬ mitosisTriggered err errFloor gradPar parCeil gradOrth orthFloor mdrNum mdrDen := by
  intro h
  rcases h with ⟨_, _, h_floor, _, _⟩
  omega

inductive ValidExecution : Nat → Nat → Prop where
  | halt (b : Nat) : ValidExecution b 0
  | step {b b' k : Nat} (h_pos : 0 < b) (h_monotone : b' < b)
      (h_rest : ValidExecution b' k) : ValidExecution b (k + 1)

theorem strict_metabolic_termination {b k : Nat} (h : ValidExecution b k) : k ≤ b := by
  induction h with
  | halt b => exact Nat.zero_le b
  | @step b b' k _ h_mono _ ih => omega

theorem stratified_arena_envelope
    (df ds dh dl rf rs rh : Int)
    (h_lock : dl = 0)
    (hf : df ≤ rf)
    (hs : ds ≤ rs)
    (hh : dh ≤ rh) :
    df + ds + dh + dl ≤ rf + rs + rh := by
  subst h_lock
  omega

end WeftV2.PureInit
