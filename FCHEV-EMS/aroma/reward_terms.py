"""Catalog of reward term forms the sequential proposer must build from, and their verification.

Every proposal adds or reshapes at least one catalog term (a pure multiplier on an existing term is not
a structural change). A term is identified by its log key self.info["term_<id>"], so it can be checked
on probes and on a stored rollout without parsing the code:

- charge-sustaining family: nonnegative, logged inside soc_cost, and soc_cost must equal the sum of the
  family's term logs (soc_cost is the charge-sustaining cost, exempt from the price-deviation check but
  bounded by the same multiple of the selection-priced cost);
- price family: nonnegative, an extra objective term inside the price-deviation check.

Each term has behavioral properties checked on probe states. When the edit base fails the
charge-sustaining guard, the structural change must come from the charge-sustaining family and the
added cost must bite on the edit base's own drifting rollout (at least one FC start's price).
These checks establish that a term has the stated shape and size, never that it improves anything.
"""
from __future__ import annotations

import math
from types import SimpleNamespace

import numpy as np

from candidate_validation import COST_KEYS, _probe_state, _replay_states, compile_reward

CS_FAMILY, PRICE_FAMILY = "charge_sustaining", "price"
FC_TO_BATT_KW = "max(0, min(-P_batt, P_mot - P_batt)) / 1000"  # P_mot - P_batt = FC (DC/DC) power, W
TERMS = {
    "soc_anchor": {
        "family": CS_FAMILY,
        "form": "c_up * max(0, SOC - SOC_target)**p + c_down * max(0, SOC_target - SOC)**p, optionally x k "
                "outside soc_bounds (p >= 1; c_up may differ from c_down)",
        "purpose": "pull SOC to the target; an asymmetric anchor (c_up > c_down) prices overcharge more than "
                   "depletion. The baseline's soc_cost is a symmetric anchor (c_up = c_down = w_soc, p = 2, k = 10).",
        "checks": "zero at SOC_target, nonnegative, nondecreasing as SOC moves away from the target",
    },
    "drift_barrier": {
        "family": CS_FAMILY,
        "form": "c * max(0, abs(SOC - SOC_init) - d0)**p with 0 <= d0 < the guard soc_drift_abs_max, p >= 1 "
                "(an asymmetric version with separate c above/below SOC_init is allowed)",
        "purpose": "flat inside a band around the initial SOC, steep beyond it, so SOC swings inside the "
                   "drive stay cheap but an end-of-drive offset past the guard does not",
        "checks": "zero for |SOC - SOC_init| <= 0.01, positive at |SOC - SOC_init| = soc_drift_abs_max on both "
                  "sides, nondecreasing in |SOC - SOC_init|",
    },
    "fc_surplus_charge": {
        "family": CS_FAMILY,
        "form": "c * g(SOC) * P_fc_to_batt_kw, P_fc_to_batt_kw = " + FC_TO_BATT_KW + ", g nondecreasing, "
                "g = 0 at or below SOC_target - m (e.g. g = max(0, SOC - SOC_target + m) / m, m in [0, 0.1])",
        "purpose": "price FC power that is pushed into the battery while SOC is already high: the measured "
                   "drift mechanism (FC kept on at low load to avoid a start, surplus charges the battery). "
                   "Regeneration and discharging are never priced.",
        "checks": "zero while discharging, zero for pure regeneration (no FC power), zero at SOC_target - 0.1, "
                  "positive at SOC_target + 0.05 with FC charging, nondecreasing in SOC and in FC charging power",
    },
    "fc_peak_shave": {
        "family": CS_FAMILY,
        "form": "c * g(SOC) * max(0, P_FCS - P_cap) with P_cap >= 8 kW (top of the efficient band or above), "
                "g nondecreasing, g = 0 at or below SOC_target - m",
        "purpose": "when SOC is high, let the battery carry the high-power transients instead of the FC: the "
                   "battery discharges dynamically and returns SOC to the target, while the FC stays in its "
                   "efficient band",
        "checks": "zero at P_FCS <= 8 kW, zero at SOC_target - 0.1, positive at SOC_target + 0.05 with P_FCS = 60 kW, "
                  "nondecreasing in SOC and in P_FCS",
    },
    "fc_efficiency_gap": {
        "family": PRICE_FAMILY,
        "form": "c * h2_fcs * max(0, eta_ref - eta) / eta_ref with eta = P_FCS / (120 * h2_fcs) when h2_fcs > 0 "
                "(else 0); 120 kJ/g is the H2 LHV, 1-s steps; eta_ref from the measured efficiency curve",
        "purpose": "price hydrogen burned below the FC's efficient operating point, so the FC runs in its "
                   "efficient band or at a deliberate minimum instead of idling at low efficiency",
        "checks": "zero with the FC off (h2_fcs = 0), zero at eta >= eta_ref, nonnegative, nonincreasing in eta at "
                  "fixed hydrogen, enters objective_cost",
    },
    "batt_ohmic": {
        "family": PRICE_FAMILY,
        "form": "c * P_batt_loss_kw (kW of battery ohmic loss; c in reward units per kW-step)",
        "purpose": "price battery round-trip loss, which no other term sees; makes charge-and-discharge "
                   "cycling (and FC surplus stored for later) cost what it physically wastes",
        "checks": "zero at zero loss, nonnegative, linear in P_batt_loss_kw, enters objective_cost",
    },
}
TOL = 1e-6
CS_BITE_MAX_FRACTION = 1.0  # added CS cost on the drifted steps <= this x the drive's selection-priced cost


def term_key(term_id):
    return f"term_{term_id}"


def _run(fn, state):
    """Reward logs of one state, with the same scalar-only inputs as checked_reward."""
    inputs = {k: v for k, v in vars(state).items()
              if isinstance(v, (int, float, bool, np.number))
              or (isinstance(v, tuple) and all(isinstance(x, (int, float, np.number)) for x in v))}
    probe = SimpleNamespace(**inputs, info={})
    fn(probe)
    return {k: float(v) for k, v in probe.info.items() if isinstance(v, (int, float, np.number))}


def _probe(args, **values):
    state = _probe_state({"h2_fcs": 0.3, "P_batt": 0.0, "P_FCS": 5.0, "dSOH_FCS": 1e-8, "dSOH_batt": 1e-8,
                          "SOC": float(args.soc_target), **values}, args)
    for key, value in values.items():
        setattr(state, key, float(value))
    return state


def _grid(args):
    from multi_agent_review import _reward_behavior_grid
    return [_probe_state(case, args) for case in _reward_behavior_grid()]


def declared_terms(info):
    return sorted(k[len("term_"):] for k in info if k.startswith("term_"))


def _nondecreasing(values):
    return all(b >= a - TOL * max(1.0, abs(a)) for a, b in zip(values, values[1:]))


def _property_failures(fn, term_id, args, guard):
    key, target, init = term_key(term_id), float(args.soc_target), float(args.soc0)
    value = lambda **kw: _run(fn, _probe(args, **kw)).get(key, 0.0)
    out = []
    if term_id == "soc_anchor":
        if abs(value(SOC=target)) > TOL:
            out.append("must be zero at SOC_target")
        up = [value(SOC=target + d) for d in np.linspace(0, 1 - target, 21)]
        down = [value(SOC=target - d) for d in np.linspace(0, target, 21)]
        if not (_nondecreasing(up) and _nondecreasing(down)):
            out.append("must be nondecreasing as SOC moves away from SOC_target")
    elif term_id == "drift_barrier":
        if any(abs(value(SOC=init + d)) > TOL for d in (-0.01, 0.0, 0.01)):
            out.append("must be zero for |SOC - SOC_init| <= 0.01")
        if not (value(SOC=init + guard) > TOL and value(SOC=init - guard) > TOL):
            out.append(f"must be positive at |SOC - SOC_init| = {guard:g} (the guard) on both sides")
        for sign in (1, -1):
            if not _nondecreasing([value(SOC=init + sign * d) for d in np.linspace(0, 0.4, 41)]):
                out.append("must be nondecreasing in |SOC - SOC_init|")
                break
    elif term_id == "fc_surplus_charge":
        # P_mot - P_batt is the FC (DC/DC) power in W; a charging FC has P_batt < 0 with P_mot above it.
        charging = lambda soc, kw: value(SOC=soc, P_mot=2000.0, P_batt=-1000.0 * kw, P_FCS=2.0 + kw)
        if any(abs(value(SOC=s, P_mot=12000.0, P_batt=6000.0, P_FCS=6.0)) > TOL for s in (0.5, 0.7, 0.9)):
            out.append("must be zero while the battery discharges")
        if any(abs(value(SOC=s, P_mot=-8000.0, P_batt=-8000.0, P_FCS=0.0)) > TOL for s in (0.5, 0.7, 0.9)):
            out.append("must be zero for pure regeneration (no FC power reaches the battery)")
        if abs(charging(target - 0.1, 5.0)) > TOL:
            out.append("must be zero at SOC_target - 0.1")
        if not charging(target + 0.05, 5.0) > TOL:
            out.append("must be positive at SOC_target + 0.05 while the FC charges the battery")
        if not _nondecreasing([charging(s, 5.0) for s in np.linspace(target - 0.1, 0.95, 23)]):
            out.append("must be nondecreasing in SOC")
        if not _nondecreasing([charging(target + 0.05, kw) for kw in np.linspace(0, 30, 16)]):
            out.append("must be nondecreasing in FC charging power")
    elif term_id == "fc_peak_shave":
        peak = lambda soc, kw: value(SOC=soc, P_FCS=kw, h2_fcs=kw / 60.0, P_mot=1000.0 * kw, P_batt=0.0)
        if any(abs(peak(s, kw)) > TOL for s in (target, target + 0.1, 0.9) for kw in (0.0, 4.0, 8.0)):
            out.append("must be zero at P_FCS <= 8 kW")
        if abs(peak(target - 0.1, 60.0)) > TOL:
            out.append("must be zero at SOC_target - 0.1")
        if not peak(target + 0.05, 60.0) > TOL:
            out.append("must be positive at SOC_target + 0.05 and P_FCS = 60 kW")
        if not _nondecreasing([peak(s, 60.0) for s in np.linspace(target - 0.1, 0.95, 23)]):
            out.append("must be nondecreasing in SOC")
        if not _nondecreasing([peak(target + 0.1, kw) for kw in np.linspace(0, 90, 19)]):
            out.append("must be nondecreasing in P_FCS")
    elif term_id == "fc_efficiency_gap":
        h2 = 0.1  # g per 1-s step; eta = P_FCS / (120 * h2) spans 0..1 for P_FCS 0..12 kW
        gap = lambda kw, g=h2: value(P_FCS=kw, h2_fcs=g, P_mot=1000.0 * kw, P_batt=0.0)
        if abs(gap(0.0, 0.0)) > TOL:
            out.append("must be zero with the FC off (h2_fcs = 0)")
        if abs(gap(12.0 * 0.99)) > TOL:
            out.append("must be zero at eta = 0.99 (above any eta_ref)")
        curve = [gap(12.0 * e) for e in np.linspace(0.05, 0.99, 20)]
        if not _nondecreasing(curve[::-1]):
            out.append("must be nonincreasing in FC efficiency at fixed hydrogen")
        if not curve[0] > TOL:
            out.append("must be positive at eta = 0.05")
        base, low = _run(fn, _probe(args, P_FCS=12.0 * 0.99, h2_fcs=h2)), _run(fn, _probe(args, P_FCS=1.2, h2_fcs=h2))
        d_obj = low["objective_cost"] - base["objective_cost"]
        d_term = low.get(term_key(term_id), 0.0) - base.get(term_key(term_id), 0.0)
        d_other = sum(low[k] - base[k] for k in COST_KEYS)
        if not math.isclose(d_obj - d_other, d_term, rel_tol=1e-6, abs_tol=1e-9):
            out.append("must enter objective_cost as an extra term")
    elif term_id == "batt_ohmic":
        losses = np.linspace(0, 3, 7)
        values = [value(P_batt_loss_kw=x, I_batt=math.sqrt(x * 1000 / 0.2)) for x in losses]
        if abs(values[0]) > TOL:
            out.append("must be zero at zero loss")
        slope = np.diff(values) / np.diff(losses)
        if not (np.all(slope >= -TOL) and np.allclose(slope, slope[0], rtol=1e-6, atol=1e-12)):
            out.append("must be linear and nondecreasing in P_batt_loss_kw")
        base = _run(fn, _probe(args, P_batt_loss_kw=0.0, I_batt=0.0))
        more = _run(fn, _probe(args, P_batt_loss_kw=2.0, I_batt=100.0))
        d_obj = more["objective_cost"] - base["objective_cost"]
        d_term = more.get(term_key(term_id), 0.0) - base.get(term_key(term_id), 0.0)
        if not math.isclose(d_obj, d_term, rel_tol=1e-6, abs_tol=1e-9):
            out.append("must enter objective_cost (objective change differs from the term's change)")
    return out


def _values(fn, states, keys):
    rows = [_run(fn, s) for s in states]
    return {k: np.array([r.get(k, 0.0) for r in rows]) for k in keys}, rows


def _proportional(new, old):
    """new = k * old on every state (a pure multiplier, including k = 1)."""
    if not np.any(old):
        return not np.any(new)
    k = float(new @ old) / float(old @ old)
    return bool(np.allclose(new, k * old, rtol=1e-6, atol=1e-9 * max(1.0, float(np.max(np.abs(new))))))


def verify_catalog_terms(source, parent_source, args, *, guard, rollout=None, require_cs=False,
                         edit_rollout=None, declared=None):
    """Structural, shape and size contract of a proposal. `rollout`: baseline ep399 (replayed);
    `edit_rollout`: the edit base's own ep399 rollout (bite check when it failed the drift guard)."""
    fn, parent = compile_reward(source), compile_reward(parent_source)
    states = _grid(args) + [_probe(args, SOC=s) for s in np.linspace(0, 1, 41)]
    if rollout is not None:
        states += list(_replay_copies(rollout, args))
    first = _run(fn, states[0])
    terms = declared_terms(first)
    unknown = [t for t in terms if t not in TERMS]
    if unknown:
        return _fail(f"unknown catalog term(s) {unknown}; use only {sorted(TERMS)}")
    keys = [term_key(t) for t in terms] + COST_KEYS + ["objective_cost"]
    new, rows = _values(fn, states, keys)
    old_keys = [term_key(t) for t in TERMS] + COST_KEYS
    old, old_rows = _values(parent, states, old_keys)
    if not declared_terms(old_rows[0]):  # an uncataloged parent (the baseline): its soc_cost is an anchor
        old[term_key("soc_anchor")] = old["soc_cost"]
    failures = []
    cs = [t for t in terms if TERMS[t]["family"] == CS_FAMILY]
    cs_sum = sum((new[term_key(t)] for t in cs), np.zeros(len(states)))
    if not np.allclose(new["soc_cost"], cs_sum, rtol=1e-6, atol=1e-9):
        step = int(np.argmax(np.abs(new["soc_cost"] - cs_sum)))
        failures.append(f"soc_cost must equal the sum of the charge-sustaining term logs {[term_key(t) for t in cs]} "
                        f"(differs by {new['soc_cost'][step] - cs_sum[step]:.4g} at probe {step}); log every SOC "
                        "component as its catalog term")
    for t in terms:
        if np.any(new[term_key(t)] < -TOL) or not np.all(np.isfinite(new[term_key(t)])):
            failures.append(f"{term_key(t)} must be finite and nonnegative")
        failures += [f"{term_key(t)} {m}" for m in _property_failures(fn, t, args, guard)]
    changed = [t for t in terms if not _proportional(new[term_key(t)], old[term_key(t)])]
    removed = [t for t in TERMS if t not in terms and np.any(old[term_key(t)])]
    structural = changed + [f"removed:{t}" for t in removed]
    if not changed:
        failures.append("no structural change: add a catalog term the edit base does not have, or change the "
                        "shape of one it has (a pure multiplier on a term or weight is not enough)")
    if require_cs and not any(TERMS[t]["family"] == CS_FAMILY for t in changed):
        failures.append("the edit base fails the charge-sustaining guard: the structural change must add or "
                        "reshape a charge-sustaining term (" + ", ".join(t for t in TERMS
                                                                         if TERMS[t]["family"] == CS_FAMILY) + ")")
    if declared is not None:
        missing = [t for t in declared if t not in changed]
        if missing:
            failures.append(f"orchestrator CHANGE_SPEC catalog_terms {declared}: not added or reshaped: {missing}")
    bite = None
    if require_cs and edit_rollout is not None and not failures:
        bite = drift_bite(fn, parent, edit_rollout, args, guard, reference_rollout=rollout)
        if bite["status"] == "fail":
            failures.append(bite["reason"])
    out = {"status": "fail" if failures else "pass", "terms": terms, "structural_changes": structural,
           "basis": "probe grid + baseline ep399 replay" if rollout is not None else "probe grid"}
    if bite:
        out["drift_bite"] = bite
    if failures:
        out["reason"] = "catalog_contract: " + "; ".join(failures)
    return out


def _fail(reason):
    return {"status": "fail", "reason": "catalog_contract: " + reason}


def _replay_copies(path, args):
    import copy
    for state in _replay_states(path, args):
        yield copy.copy(state)


def avoidable_starts(rollout):
    """FC-off intervals inside the drive (each one ends in a start that staying on would avoid); the reset
    start before step 0 and an off interval running to the end of the drive do not count."""
    if rollout is None:
        return 0
    off = np.asarray(np.load(rollout)["h2_fcs"], float) <= 0
    edges = np.diff(np.r_[0, off.astype(int), 0])
    begins, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    return int(np.sum((begins > 0) & (ends < len(off))))


def starts_to_price(rollout, reference_rollout):
    """Starts a non-drifting policy needs: the baseline's in-drive FC-off intervals (a drifting edit base
    keeps the FC on, so its own count collapses toward zero), at least one."""
    return max(1, avoidable_starts(rollout), avoidable_starts(reference_rollout))


def drift_bite(fn, parent, rollout, args, guard, reference_rollout=None):
    """On the edit base's drifting rollout, the added charge-sustaining cost over the steps past half the
    guard must be at least the FC starts a non-drifting policy needs (starts_to_price) at the candidate's
    own FC price, and at most the whole drive's operating cost at the selection prices (in reward units):
    enough that drifting is dearer than switching the FC off and on as often as the load requires, not so
    much that SOC tracking swamps every other cost (an oversized term starves or floods the battery, as
    the 100x ohmic penalty of 2026-09-29 did). One start was too low: the proposer sized to it exactly."""
    from env_physics_facts import fc_event_cases
    from operating_cost import USD_PER_BATT_LOSS, USD_PER_FC_LOSS, USD_PER_H2_G
    start = next((c["dSOH_FCS"] for c in fc_event_cases() if c.get("event") == "start"), None)
    g_fc, g_batt, w_h2 = USD_PER_FC_LOSS / USD_PER_H2_G, USD_PER_BATT_LOSS / USD_PER_H2_G, float(args.w_h2)
    added, fc_cost, fc_loss, steps, drive = 0.0, 0.0, 0.0, 0, 0.0
    for state in _replay_states(rollout, args):
        new, old = _run(fn, state), _run(parent, state)
        fc_cost += new["fcs_soh_cost"]
        fc_loss += state.dSOH_FCS
        drive += w_h2 * (state.h2_fcs + g_fc * state.dSOH_FCS + g_batt * state.dSOH_batt)
        if abs(state.SOC - float(args.soc0)) > guard / 2:
            added += new["soc_cost"] - old["soc_cost"]
            steps += 1
    if start is None or fc_loss <= 0:
        return {"status": "unavailable", "reason": "no FC start price or FC wear on the rollout"}
    start_price = fc_cost / fc_loss * start
    n_starts = starts_to_price(rollout, reference_rollout)
    low, high = n_starts * start_price, CS_BITE_MAX_FRACTION * drive
    out = {"status": "pass" if low <= added <= high else "fail", "drifted_steps": steps,
           "added_cs_cost_on_drifted_steps": added, "required_range": [low, high],
           "one_fc_start_price": start_price, "starts_priced": n_starts,
           "drive_operating_cost_reward_units": drive,
           "basis": f"edit base ep399 rollout, steps with |SOC - SOC_init| > {guard / 2:g}"}
    if added < low:
        out["reason"] = (f"drift_bite: on the edit base's own rollout the added charge-sustaining cost over its "
                         f"{steps} drifted steps (|SOC - SOC_init| > {guard / 2:g}) is {added:.4g}, below {n_starts} FC "
                         f"starts (the baseline's in-drive FC-off intervals) at this reward's FC price "
                         f"({n_starts} x {start_price:.4g}): keeping the FC on to avoid those starts would still be "
                         f"cheaper than not drifting. Required range [{low:.4g}, {high:.4g}]; the lower end is a "
                         "minimum, not a target: size well inside the range from the drift facts")
    elif added > high:
        out["reason"] = (f"drift_bite: the added charge-sustaining cost over the edit base's {steps} drifted steps "
                         f"is {added:.4g}, above the whole drive's operating cost at the selection prices "
                         f"({high:.4g} reward units): SOC tracking would swamp hydrogen and wear. Required range "
                         f"[{low:.4g}, {high:.4g}]; scale the coefficient down from the drift facts")
    return out


def spec_family_conflict(spec):
    """Why a CHANGE_SPEC contradicts the families of its catalog ids (CS -> soc_cost, price -> extra); else None."""
    ids = (spec or {}).get("catalog_terms") or []
    cs = [t for t in ids if TERMS[t]["family"] == CS_FAMILY]
    price = [t for t in ids if TERMS[t]["family"] == PRICE_FAMILY]
    out = []
    if cs and spec["term_ratio"].get("soc_cost", 1.0) != "changed":
        out.append(f"charge-sustaining terms {cs} are summed into soc_cost, so term_ratio.soc_cost must be "
                   "\"changed\"")
    if price and spec.get("extra_terms") != "added":
        out.append(f"price terms {price} are extra objective terms, so extra_terms must be \"added\"")
    return "; ".join(out) or None


def catalog_prompt(guard):
    lines = ["REWARD TERM CATALOG (binding). Build the reward from these forms. Log every catalog term you use "
             "as self.info['term_<id>'] = float(value) (the plain value, before summing). Charge-sustaining "
             "terms are summed INTO soc_cost, and soc_cost must equal the sum of their logs (the baseline's "
             "soc_cost becomes term_soc_anchor); soc_cost is the charge-sustaining cost and is exempt from the "
             "price-deviation check, but its own per-step mean on the baseline rollout may not exceed the same "
             "multiple of the selection-priced cost. Price terms are extra objective terms inside that check. "
             "In the CHANGE_SPEC a charge-sustaining id means term_ratio.soc_cost = \"changed\" and a price id "
             "means extra_terms = \"added\". Every proposal "
             "must ADD a catalog term the edit base lacks or CHANGE THE SHAPE of one it has (exponent, deadband, "
             "asymmetry, SOC gate, input); multiplying a term or weight by a constant is not a structural "
             "change and is rejected. If the edit base fails the charge-sustaining guard, the structural change "
             f"must be in the charge-sustaining family, and on the edit base's own rollout its added cost over "
             f"the steps with |SOC - SOC_init| > {guard / 2:g} must lie between the price of the FC starts a "
             "non-drifting policy needs and the drive's whole operating cost at the selection prices (both stated "
             "in DRIFT FACTS). The lower end is a MINIMUM, not a target: a term sized at it barely changes the "
             "start-versus-drift tradeoff, so size well inside the range (e.g. near its geometric mean) and show "
             "the arithmetic. All "
             "terms are nonnegative. P_mot (W, motor electrical power) and P_batt (W, + = discharge) give the FC "
             "power into the battery as " + FC_TO_BATT_KW + " kW."]
    for term_id, spec in TERMS.items():
        lines.append(f"- {term_id} [{spec['family']}]: {spec['form']}. Purpose: {spec['purpose']}. "
                     f"Checked: {spec['checks']}.")
    return "\n".join(lines + [OPERATING_DIRECTION]) + "\n"


def drift_facts(rollout, args, guard, reference_rollout=None):
    """Where and how the rollout drifted, in reward units, so CS terms are sized from measurements."""
    if rollout is None:
        return ""
    data = np.load(rollout)
    soc = np.asarray(data["SOC"], float)
    p_batt = 1000 * np.asarray(data["battery_delivered_kw"], float)
    p_mot = 1000 * np.asarray(data["P_mot"], float)
    fc_to_batt = np.maximum(0, np.minimum(-p_batt, p_mot - p_batt)) / 1000
    regen = np.maximum(0, -p_batt) / 1000 - fc_to_batt
    soc0, target = float(args.soc0), float(args.soc_target)
    high = soc > target
    drift = soc - soc0
    n = len(soc)
    seg = max(1, n // 7)
    rows = []
    for a in range(0, n, seg):
        s = slice(a, min(n, a + seg))
        rows.append(f"steps {a}-{min(n, a + seg) - 1}: SOC {soc[a]:.3f}->{soc[s][-1]:.3f}, FC->battery "
                    f"{fc_to_batt[s].sum() / 3600:.3f} kWh, regen->battery {regen[s].sum() / 3600:.3f} kWh")
    past = np.abs(drift) > guard / 2
    from env_physics_facts import fc_event_cases
    from operating_cost import USD_PER_BATT_LOSS, USD_PER_FC_LOSS, USD_PER_H2_G
    start = next((c["dSOH_FCS"] for c in fc_event_cases() if c.get("event") == "start"), 0.0)
    fc_loss = -np.diff(np.r_[1.0, np.asarray(data["FCS_SOH"], float)])
    drive = float(args.w_h2) * (np.sum(data["h2_fcs"]) + USD_PER_FC_LOSS / USD_PER_H2_G * fc_loss.sum()
                                + USD_PER_BATT_LOSS / USD_PER_H2_G * np.sum(data["dsoh"]))
    n_starts = starts_to_price(rollout, reference_rollout)
    low = n_starts * float(args.w_fc) * start
    sizing = (f"Sizing range for a charge-sustaining change, summed over these {int(past.sum())} steps on this "
              f"rollout: MINIMUM {n_starts} FC starts (in-drive FC-off intervals of the baseline, the starts a "
              f"non-drifting policy needs) x {float(args.w_fc) * start:.4g} = {low:.4g} reward units at the settings "
              f"w_fc (scale it by your own fcs_soh_cost multiplier); MAXIMUM the drive's whole operating cost at the "
              f"selection prices = {drive:.4g} reward units (w_h2 = {float(args.w_h2):g} per g H2); geometric mean "
              f"{math.sqrt(max(low, 1e-12) * max(drive, 1e-12)):.4g}. The minimum is a floor, not a target.\n")
    return (f"DRIFT FACTS (edit base ep399 rollout; SOC_init {soc0:g}, target {target:g}, final drift "
            f"{drift[-1]:+.3f}, guard {guard:g}): FC->battery energy {fc_to_batt.sum() / 3600:.3f} kWh in total, "
            f"{fc_to_batt[high].sum() / 3600:.3f} kWh of it with SOC above target; mean FC->battery power while "
            f"charging above target {fc_to_batt[high & (fc_to_batt > 0)].mean() if np.any(high & (fc_to_batt > 0)) else 0:.3g} kW; "
            f"{int(past.sum())} steps have |SOC - SOC_init| > {guard / 2:g} (max |drift| {np.abs(drift).max():.3f}).\n"
            + "\n".join(rows) + "\n" + sizing)


OPERATING_DIRECTION = (
    "OPERATING DIRECTION (from the measured drift mechanism; the terms above are how to express it): FC wear "
    "is priced high, so the policies learned to keep the FC on for the whole drive at low output to avoid "
    "starts; at low load that output exceeds the demand, the surplus charges the battery and SOC ends high, and "
    "the FC spends many steps at its least efficient points. Aim instead for: (1) the FC held in its efficient "
    "band (EFFICIENCY FACTS) with slow changes, not tracking the load; (2) the battery carrying the dynamic "
    "high-power transients, discharging hard when SOC is high so SOC returns to the target (fc_peak_shave); (3) "
    "at low load the FC at a deliberate minimum or off, accepting some charging but not idling surplus into a "
    "high SOC (fc_surplus_charge, drift_barrier); (4) hydrogen burned at low efficiency priced as such "
    "(fc_efficiency_gap), which lowers SOC-corrected equivalent fuel. Battery wear rises with this split; it is "
    "priced in the total and guarded, so size the battery-side effect from the measured batt_loss."
)


def efficiency_facts(rollout):
    """Measured FC system efficiency eta = P_FCS / (120 * h2_fcs) by output band on one rollout."""
    if rollout is None:
        return ""
    data = np.load(rollout)
    p, h2 = np.asarray(data["fc_applied_kw"], float), np.asarray(data["h2_fcs"], float)
    on = h2 > 0
    if not on.any():
        return ""
    eta = np.where(on, p / (120.0 * np.maximum(h2, 1e-12)), np.nan)
    bands = [(0, 2), (2, 4), (4, 6), (6, 8), (8, 10), (10, 15), (15, 20), (20, 30), (30, 45), (45, 100)]
    rows, best = [], (0.0, None)
    for lo, hi in bands:
        m = on & (p >= lo) & (p < hi)
        if m.any():
            e = float(np.nanmean(eta[m]))
            rows.append(f"{lo}-{hi} kW: eta {e:.3f} ({int(m.sum())} steps)")
            best = max(best, (e, (lo, hi)))
    low = on & (eta < 0.9 * best[0])
    return ("EFFICIENCY FACTS (same rollout; eta = P_FCS / (120 * h2_fcs), the form fc_efficiency_gap must use): "
            + "; ".join(rows) + f". Peak eta {best[0]:.3f} at {best[1][0]}-{best[1][1]} kW; {int(low.sum())} of "
            f"{int(on.sum())} FC-on steps run below 0.9 x peak, burning {h2[low].sum():.4g} g of the "
            f"{h2[on].sum():.4g} g H2.\n")
