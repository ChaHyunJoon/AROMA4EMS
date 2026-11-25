"""One free reward proposal -> 400 episodes -> total-operating-cost deployment gate (v3).

The champion is the measured ep399 actor with the lowest total operating cost (hydrogen + FC wear +
battery wear, USD per 100 km, priced as in visualization/paper_figs_multi_seed.ipynb; see
operating_cost.py) whose fuel and battery loss stay inside guard bands fixed in advance against the
baseline (L1). FC wear has no cap: with fuel it is the lever the search is meant to pull. The search
starts each proposal from an archived edit base that may be a tradeoff candidate (L3); tail
statistics are diagnostics only (L2). After the search, the deployed reward is re-checked
against the baseline with a real rollback (L6) and optionally re-trained on pre-specified
unused seeds (L4) whose results are never fed back to the proposer. L4 is a separate, explicit
step (`--resume_run_root <run> --run_confirmation`), so the search can be inspected and extended first.
Spec: docs/aroma-sequential-v2-spec-2026-09-24.md (v3 replaces its fuel-first L1 with total cost)
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
import math
from pathlib import Path

from candidate_validation import (REQUIRED_KEYS, COST_KEYS, candidate_id, measure_cost_scale, verify_candidate,
                                  verify_cost_scale)
from feedback_parser import DETERMINISTIC_FUEL_BASIS
from operating_cost import USD_PER_FC_LOSS, USD_PER_H2_G, operating_cost, price_alignment, price_model
from prompt_builder import extract_method_source
from reward_patcher import PatchError, ensure_logging_contract, extract_method_from_llm_response, patch_method_in_file
from validated_workflow import TrialEvaluator, _digest, _manifest, write_json
from reward_terms import (TERMS, catalog_prompt, drift_facts, efficiency_facts, spec_family_conflict,
                          verify_catalog_terms)
from development_validation import (DevelopmentEvaluator, brief_development, compare_development,
                                    manifest_fields, validate_options)

PROTOCOL_VERSION = "sequential_total_cost_v3"
OBJECTIVE = (
    "AROMA is multi-objective energy management whose goal is the total operating cost of the drive: "
    "hydrogen cost + FC degradation cost + battery degradation cost, in USD per 100 km at fixed prices "
    "(context.cost_model). The core levers are FC degradation and FC hydrogen consumption: FC wear is "
    "usually the largest share of the total, so a policy that burns slightly more hydrogen but wears the FC "
    "much less can win. Adoption: total operating cost MUST be strictly below the standing champion's. "
    "Guard bands, fixed in advance (context.cost_model.guards): CHARGE SUSTAINING, |SOC_final - SOC_initial| "
    "of the ep399 rollout at most soc_drift_abs_max (absolute, the same for every seed, so a baseline that "
    "drifts further does not loosen it); SOC-corrected equivalent hydrogen at most the baseline's times "
    "(1 + max fuel increase); and battery SOH loss at most the baseline's times (1 + max battery increase), "
    "so FC wear cannot be bought by charging the battery with idling FC power, by shifting load onto the "
    "battery or by unbounded hydrogen. FC SOH loss has no cap of its own; it is priced in the total. "
    "The search keeps the Pareto front of total cost versus SOC-corrected fuel among guard-feasible rewards; "
    "the champion is its lowest-cost point, and a reward that is cheaper but fails a guard is kept as a "
    "repair target. A tie in total cost is rejected. Compare final ep399 policies at the same seed, cycle, initial state "
    "and 400-episode training budget. Tail statistics are diagnostics. Keep physical tracking feasible "
    "and SOC within the specified operating band. Reward coefficients and cost shares are not measurements "
    "of policy performance. State causal explanations as hypotheses; actual post-training measurements "
    "decide adoption."
)
METRIC_KEYS = ("fuel_gkm", "fc_loss", "batt_loss", "soc_in_bounds", "soc_min", "soc_max")
OBJECTIVE_KEYS = ("fuel_gkm", "fc_loss", "batt_loss")
GUARD_KEYS = ("charge_sustaining", "fuel_within_guard", "battery_within_guard")
PHYSICS_KEYS = ("soc_initial", "soc_final", "soc_final_minus_initial", "soc_swing", "fc_power_kw_mean",
                "fc_abs_ramp_kw_s_mean", "fc_on_pct", "fc_energy_efficiency", "fc_start_stop_soh_loss",
                "fc_low_power_soh_loss", "fc_high_power_soh_loss", "fc_load_change_soh_loss",
                "fc_start_stop_count", "fc_low_power_count", "fc_load_change_count",
                "battery_throughput_kwh", "battery_ohmic_loss_kw_integral_kwh", "soc_mean",
                "fc_low_output_pct", "fc_regeneration_energy_kwh")
TAIL_WINDOW = 40
LUCKY_FRACTION = 0.9
EDIT_MODES = ("champion_improve", "fuel_leader", "guard_repair")
BATTERY_PROTECTION = (
    "BATTERY PROTECTION: cutting FC wear usually moves work onto the battery. Fewer FC starts, longer FC-off "
    "periods and slower FC power changes make the battery cover the transients, which raises battery "
    "throughput, ohmic loss, SOC swing and batt_loss. Treat battery degradation as a cost to protect, not a free "
    "buffer: an FC saving that pushes batt_loss past cost_model.guards.batt_loss_max is rejected, and battery "
    "cost counts in the total. The reward already prices battery wear relative to hydrogen below the selection "
    "prices (cost_model.reward_weight_alignment), so raising the FC price alone makes the battery look even "
    "cheaper to the policy; when you raise the FC price, keep the battery price in proportion or say why not. "
    "Before proposing, read the measured battery_throughput_kwh, battery_ohmic_loss_kw_integral_kwh, soc_swing "
    "and batt_loss of the edit base and of previous candidates, and state the battery effect you expect."
)
CHARGE_SUSTAINING = (
    "CHARGE SUSTAINING: measured on earlier runs, the cheapest rewards cut FC start-stop wear by keeping the "
    "FC on for the whole drive at low output; the surplus energy charges the battery and SOC ends 0.05-0.18 "
    "above its initial value. The SOC correction credits that surplus at FC efficiency, so it does not show "
    "up as fuel, but the policy is not charge sustaining and is rejected by "
    "cost_model.guards.soc_drift_abs_max whatever its cost. Every entry's fuel_breakdown.soc_final_minus_initial "
    "and guard_checks show where it stands. The reward is stateless and the episode is ~3441 steps, so a "
    "terminal-only SOC penalty is discounted to nothing: drift has to be priced per step from SOC and "
    "SOC_target/SOC_init. The SOC cost is the lever that sets where the start-stop-versus-hydrogen tradeoff "
    "lands: too weak and the FC idles into the battery, too strong and the FC follows the load with more "
    "starts and load changes. For the reward you propose, state the terminal drift you expect and why, "
    "and size any SOC term change from the measured soc_cost and the drift of the edit base."
)
MODE_GOALS = {
    "champion_improve": "Edit the deployment champion: lower the total operating cost below the champion's, "
                        "mainly through FC wear and FC hydrogen, with terminal SOC drift, fuel and battery "
                        "loss inside the guards.",
    "fuel_leader": "Edit the lowest-fuel reward on the cost-fuel front: keep its hydrogen advantage and cut its "
                   "FC wear (start-stop, load change, low/high power) until the total cost is below the "
                   "champion's, with terminal SOC drift and battery loss inside their guards.",
    "guard_repair": "Edit the cheapest trained reward that FAILED a guard (edit_base.guard_checks says which): it "
                    "already shows how far FC wear can fall. Repair the failed guard - usually terminal SOC "
                    "drift or fuel - while giving up as little of its cost advantage as possible, so that the "
                    "total cost stays below the champion's with every guard passing.",
    "fallback_least_stale": "Every ranked edit base is stale; edit the least-used archived reward and aim to "
                            "beat the champion on total cost with terminal SOC drift, fuel and battery loss "
                            "inside the guards.",
}


def _signature(source):
    import textwrap
    return ast.dump(ast.parse(textwrap.dedent(source)), include_attributes=False)


def _finite(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def _rid(trial):
    return trial.get("candidate_id") or candidate_id(trial["reward_source"])


def policy_metrics(trial):
    """Never substitute tail means for the final checkpoint being installed."""
    return trial.get("final_metrics") or {}


def drive_distance_km(trial):
    return ((policy_metrics(trial).get("paper_fuel") or {}).get("drive_mileage_km"))


def policy_cost(trial):
    """Total operating cost of the ep399 rollout (USD per 100 km), or None without full evidence."""
    m = policy_metrics(trial)
    return operating_cost(m.get("fuel_gkm"), m.get("fc_loss"), m.get("batt_loss"), drive_distance_km(trial))


def guard_limits(baseline, args):
    """Pre-specified guard bands: absolute fuel and battery-loss limits derived from the fixed baseline,
    and an absolute terminal-SOC drift limit that does not depend on the baseline."""
    b = policy_metrics(baseline)
    fuel, batt = float(args.cost_max_fuel_increase), float(args.cost_max_batt_increase)
    return {"reference": "baseline", "max_fuel_increase_fraction": fuel, "max_batt_increase_fraction": batt,
            "fuel_gkm_max": b["fuel_gkm"] * (1 + fuel) if _finite(b.get("fuel_gkm")) else None,
            "batt_loss_max": b["batt_loss"] * (1 + batt) if _finite(b.get("batt_loss")) else None,
            "soc_drift_abs_max": float(args.cost_max_soc_drift)}


def soc_drift(trial):
    """SOC_final - SOC_initial of the ep399 rollout, or None without evidence."""
    m = policy_metrics(trial)
    drift = ((m.get("physical_evidence") or {}).get("scalars") or {}).get("soc_final_minus_initial")
    return drift if _finite(drift) else None


def guard_checks(trial, guards):
    """The three guards of one valid ep399 actor; missing evidence fails closed."""
    m, drift = policy_metrics(trial), soc_drift(trial)
    within = lambda value, limit: _finite(value) and _finite(limit) and value <= limit
    return {"charge_sustaining": drift is not None and within(abs(drift), guards["soc_drift_abs_max"]),
            "fuel_within_guard": within(m.get("fuel_gkm"), guards["fuel_gkm_max"]),
            "battery_within_guard": within(m.get("batt_loss"), guards["batt_loss_max"])}


def validity_failures(trial, args):
    """Why the ep399 actor cannot be compared; empty when it can. Fed back to the proposer."""
    m = policy_metrics(trial)
    if trial.get("status") != "complete":
        return [f"trial_{trial.get('status')}: {trial.get('error', '')}"[:300]]
    if trial.get("episodes") != 400 or m.get("episode") != 399:
        return ["final_checkpoint_is_not_ep399"]
    power = m.get("power_violations") or {}
    if m.get("incomplete_drive", False):
        return [f"incomplete_drive: {m.get('failure_reason') or 'terminated'} (ep_len {m.get('ep_len')})"]
    out = []
    # Whole drive, not the last step: under-delivered work cannot buy fuel or degradation.
    from power_constraints import shortfall_steps
    shortfall = shortfall_steps(power)
    if shortfall is None:
        out.append("missing_whole_drive_power_evidence")
    elif shortfall:
        out.append(f"requested_power_not_delivered: steps {shortfall}, "
                   f"unserved {power.get('unserved_kwh', 0):.4g} kWh (peak {power.get('unserved_peak_kw', 0):.4g} kW)")
    if m.get("fuel_metric_basis") != DETERMINISTIC_FUEL_BASIS:
        out.append("fuel_metric_basis_mismatch")
    if not all(_finite(m.get(k)) for k in METRIC_KEYS):
        return out + ["nonfinite_final_metrics"]
    if m["fuel_gkm"] < 0 or m["fc_loss"] < 0 or m["batt_loss"] < 0:
        out.append("negative_fuel_or_soh_loss")
    if not 0 <= m["soc_min"] <= m["soc_max"] <= 1:
        out.append("soc_outside_physical_range")
    distance = drive_distance_km(trial)
    if not _finite(distance) or distance <= 0:
        out.append("missing_drive_distance_for_operating_cost")
    if m["soc_in_bounds"] < args.validation_min_in_bounds:
        out.append(f"soc_in_bounds {m['soc_in_bounds']:.2f}% < {args.validation_min_in_bounds}%")
    return out


def policy_valid(trial, args):
    return not validity_failures(trial, args)


def fuel_breakdown(trial):
    """Raw H2, SOC correction and terminal drift behind the corrected g/km (reporting, not a gate).

    SOC in-bounds is not charge sustaining: a large terminal drift is shown next to the fuel it corrects.
    """
    m = policy_metrics(trial)
    paper, power = m.get("paper_fuel") or {}, m.get("power_violations") or {}
    distance = paper.get("drive_mileage_km")
    if not all(_finite(paper.get(k)) for k in ("equivalent_fuel_g", "batt_eq_h2_g")) or not _finite(distance) \
            or distance <= 0:
        return {}
    scalars = (m.get("physical_evidence") or {}).get("scalars", {})
    return {"raw_h2_gkm": (paper["equivalent_fuel_g"] - paper["batt_eq_h2_g"]) / distance,
            "soc_correction_gkm": paper["batt_eq_h2_g"] / distance,
            "soc_final": paper.get("soc_f"), "soc_final_minus_initial": scalars.get("soc_final_minus_initial"),
            "unaccepted_fc_kwh": power.get("unaccepted_fc_kwh"),
            "unaccepted_regen_kwh": power.get("unaccepted_regen_kwh")}


def compare_policies(candidate, champion, args, degradation_cap=None):
    """L1 deployment gate on ep399 actors: total operating cost strictly below `champion`'s, charge
    sustaining, and fuel and battery loss inside the guard bands of `degradation_cap` (the fixed
    baseline; defaults to `champion` for the L6/L4 baseline comparisons).

    The guards are fixed against the baseline, so the champion is always the lowest-cost guard-feasible
    actor found so far; a champion that used less fuel than the baseline does not shrink the band.
    """
    cap = champion if degradation_cap is None else degradation_cap
    refs = [champion] if cap is champion else [champion, cap]
    if not policy_valid(candidate, args) or not all(policy_valid(r, args) for r in refs):
        return {"status": "fail", "reason": "invalid_or_missing_final_policy_evidence", "checks": {},
                "invalid_reasons": {"candidate": validity_failures(candidate, args),
                                    "reference": validity_failures(champion, args)}}
    if any(candidate.get(k) != r.get(k) for r in refs for k in ("seed", "episodes", "conditions_id")):
        return {"status": "fail", "reason": "unpaired_conditions", "checks": {}}
    c, b, d = policy_metrics(candidate), policy_metrics(champion), policy_metrics(cap)
    cc, bc, dc = policy_cost(candidate), policy_cost(champion), policy_cost(cap)
    guards = guard_limits(cap, args)
    checks = {"total_cost_strictly_improved": cc["total_usd"] < bc["total_usd"], **guard_checks(candidate, guards)}
    out = {"status": "pass" if all(checks.values()) else "fail", "checks": checks,
           "checkpoint_episode": 399, "cost_unit": cc["unit"],
           "total_cost_delta_usd": cc["total_usd"] - bc["total_usd"],
           "cost_delta_usd": {k: cc[k] - bc[k] for k in ("h2_usd", "fc_usd", "batt_usd")},
           "soc_drift": soc_drift(candidate),
           "fuel_delta_gkm": c["fuel_gkm"] - b["fuel_gkm"],
           "fc_loss_delta": c["fc_loss"] - b["fc_loss"],
           "batt_loss_delta": c["batt_loss"] - b["batt_loss"],
           "guards": guards,
           "guard_reference": "baseline" if cap is not champion else "same_as_cost_reference",
           "comparison_basis": ("historical_baseline_reevaluated_in_current_environment"
                                if any(x.get("baseline_provenance") for x in [candidate, *refs])
                                else "matched_fresh_training")}
    if cap is not champion:  # informational: how the candidate relates to the fixed baseline
        out.update(total_cost_delta_usd_vs_baseline=cc["total_usd"] - dc["total_usd"],
                   fuel_delta_gkm_vs_baseline=c["fuel_gkm"] - d["fuel_gkm"],
                   fc_loss_delta_vs_baseline=c["fc_loss"] - d["fc_loss"],
                   batt_loss_delta_vs_baseline=c["batt_loss"] - d["batt_loss"])
    development = compare_development(candidate, champion, cap, args)
    if development["status"] != "disabled":
        out["development"] = development
        out["checks"]["development_passed"] = development["status"] == "pass"
        out["status"] = "pass" if all(out["checks"].values()) else "fail"
    return out


def observed_relation(candidate, reference, args):
    """Single-run ep399 relation. An observation for search/reporting, never a reward-level verdict."""
    if not policy_valid(candidate, args) or not policy_valid(reference, args):
        return "invalid"
    c, b = policy_metrics(candidate), policy_metrics(reference)
    cheaper = policy_cost(candidate)["total_usd"] < policy_cost(reference)["total_usd"]
    lt = [c[k] < b[k] for k in OBJECTIVE_KEYS]
    le = [c[k] <= b[k] for k in OBJECTIVE_KEYS]
    if cheaper and all(lt):
        return "strict_pareto"
    if cheaper and all(le):
        return "cost_improved_noninferior"
    if cheaper:
        return "cost_tradeoff"
    return "objective_tradeoff" if any(lt) else "worse_or_equal"


def tail_diagnostics(trial):
    """L2: ep360-399 statistics of ONE training run. Not a gate and not reward reproducibility."""
    episodes = int(trial.get("episodes") or 400)
    first = episodes - TAIL_WINDOW
    out = {"basis": "single_run_tail_diagnostic_not_a_gate", "window": [first, episodes - 1], "available": False,
           "trial_tail_status": (trial.get("metrics") or {}).get("tail_status", "all_rows_valid")}
    path = trial.get("evaluation_evidence")
    if not path or not Path(path).is_file():
        return out
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if first <= int(row.get("episode", -1)) < episodes:
            rows.append(row)
    # Failed rows are counted, never dropped silently from the statistics' denominator.
    failed = [int(r["episode"]) for r in rows
              if r.get("incomplete_drive") or not all(_finite(r.get(k)) for k in OBJECTIVE_KEYS)]
    out.update(rows=len(rows), coverage=len(rows) / TAIL_WINDOW, failed_rows=len(failed),
               failed_episodes=failed[:20])
    import numpy as np
    stats = {}
    for key in OBJECTIVE_KEYS:
        points = [(int(r["episode"]), float(r[key])) for r in rows if _finite(r.get(key))]
        if len(points) < 3:
            return out
        ep, values = (np.array(x) for x in zip(*points))
        final = [v for e, v in points if e == episodes - 1]
        stats[key] = {"n": len(values), "mean": float(values.mean()), "std": float(values.std(ddof=1)),
                      "slope_per_10_episodes": float(np.polyfit(ep, values, 1)[0] * 10),
                      "ep399_better_than_fraction": float(np.mean(values > final[0])) if final else None}
    lucky = stats["fuel_gkm"]["ep399_better_than_fraction"]
    out.update(available=True, metrics=stats, lucky_checkpoint=bool(lucky is not None and lucky >= LUCKY_FRACTION))
    return out


def _entry(trial, iteration, parent_id, guards=None):
    m = policy_metrics(trial)
    scalars = m.get("physical_evidence", {}).get("scalars", {})
    return {"reward_id": _rid(trial), "parent_id": parent_id, "iteration": iteration,
            "reward_source": trial["reward_source"], "final_ep399": {k: m.get(k) for k in METRIC_KEYS},
            "operating_cost": policy_cost(trial),
            "guard_checks": guard_checks(trial, guards) if guards else None,
            "trajectory_dir": trial.get("trajectory_dir"),
            "fuel_breakdown": fuel_breakdown(trial),
            "physics": {k: scalars[k] for k in PHYSICS_KEYS if k in scalars},
            "regimes": m.get("physical_evidence", {}).get("regimes", {"available": False}),
            "development": brief_development(trial),
            "tail": tail_diagnostics(trial), "stale": 0, "children": 0}


def _total(entry):
    return (entry.get("operating_cost") or {}).get("total_usd", math.inf)


def _front_point(entry):
    return (_total(entry), entry["final_ep399"]["fuel_gkm"])


def _dominates(a, b):
    """Total operating cost versus SOC-corrected fuel (FC and battery wear are inside the cost)."""
    x, y = _front_point(a), _front_point(b)
    return all(p <= q for p, q in zip(x, y)) and any(p < q for p, q in zip(x, y))


def guard_feasible(entry):
    checks = entry.get("guard_checks")
    return bool(checks) and all(checks.get(k) for k in GUARD_KEYS)


def archive_members(summary):
    """Cost-fuel Pareto front of guard-feasible trained rewards, plus baseline and champion."""
    entries = [e for e in summary["archive"] if guard_feasible(e)]
    keep = {summary["baseline_id"], summary["champion_id"]}
    front = [e for e in entries if not any(_dominates(o, e) for o in entries if o is not e)]
    return [e for e in summary["archive"] if e["reward_id"] in keep or any(e is f for f in front)]


def repair_targets(summary):
    """Trained rewards cheaper than the champion that failed a guard, cheapest first."""
    by_id = {e["reward_id"]: e for e in summary["archive"]}
    bar = _total(by_id[summary["champion_id"]])
    return sorted((e for e in summary["archive"]
                   if e.get("guard_checks") and not guard_feasible(e) and _total(e) < bar),
                  key=_total)


def select_edit_base(summary, iteration, args):
    """Deterministic L3 rotation; adoption is still judged only against the champion."""
    by_id = {e["reward_id"]: e for e in summary["archive"]}
    champion, baseline = by_id[summary["champion_id"]], by_id[summary["baseline_id"]]
    if getattr(args, "search_plan", "archive") == "fuel_diagnostics_v1" and iteration in (2, 3):
        return "champion_improve", baseline, "controlled ablation from the fixed baseline"
    members = archive_members(summary)
    mode, note = EDIT_MODES[(iteration - 2) % len(EDIT_MODES)], ""
    if mode == "guard_repair":
        ranking = repair_targets(summary)
        if not [e for e in ranking if e["stale"] < args.edit_base_max_stale]:
            # nothing cheaper than the champion left to repair: improve the champion instead
            mode, note = "champion_improve", " (no fresh guard_repair target)"
    if mode == "champion_improve":
        ranking = [champion]
    elif mode == "fuel_leader":
        ranking = sorted(members, key=lambda e: (e["final_ep399"]["fuel_gkm"], _total(e)))
    fresh = [e for e in ranking if e["stale"] < args.edit_base_max_stale]
    if fresh:
        return mode, fresh[0], f"{mode}: rank {ranking.index(fresh[0]) + 1} of {len(ranking)}{note}"
    chosen = min(members, key=lambda e: (e["stale"], _total(e)))
    return "fallback_least_stale", chosen, f"all {mode} bases stale (>= {args.edit_base_max_stale}); least-stale member"


def _view(entry, *, source=False, physics=False):
    view = {k: entry.get(k) for k in ("reward_id", "parent_id", "iteration", "final_ep399", "operating_cost",
                                      "guard_checks", "fuel_breakdown", "tail")}
    if physics:
        view["physics"] = entry.get("physics", {})
        view["regimes"] = entry.get("regimes", {"available": False})
    view["development"] = entry.get("development")
    if source:
        view["reward_source"] = entry["reward_source"]
    return view


def _delta(entry, reference):
    a, b = entry["final_ep399"], reference["final_ep399"]
    out = {"reference_reward_id": reference["reward_id"]}
    for k in OBJECTIVE_KEYS:
        out[k] = a[k] - b[k] if _finite(a.get(k)) and _finite(b.get(k)) else None
    ca, cb = entry.get("operating_cost") or {}, reference.get("operating_cost") or {}
    for k in ("total_usd", "h2_usd", "fc_usd", "batt_usd"):
        out[k] = ca[k] - cb[k] if _finite(ca.get(k)) and _finite(cb.get(k)) else None
    return out


def _brief(trial, args=None):
    m = policy_metrics(trial)
    out = {"candidate_id": trial.get("candidate_id"), "seed": trial.get("seed"),
           "status": trial.get("status"), "final_ep399": {k: m.get(k) for k in METRIC_KEYS},
           "operating_cost": policy_cost(trial),
           "fuel_breakdown": fuel_breakdown(trial),
           "tail_mean": {k: trial.get("metrics", {}).get(k) for k in OBJECTIVE_KEYS}}
    evidence = m.get("physical_evidence") or {}
    out["physics"] = {k: v for k, v in evidence.get("scalars", {}).items() if k in PHYSICS_KEYS}
    out["regimes"] = evidence.get("regimes", {"available": False})
    out["development"] = brief_development(trial)
    if args is not None:
        failures = validity_failures(trial, args)
        if failures:  # why an invalid candidate failed, so the next proposal can learn from it
            out["invalid_reasons"] = failures
            power = m.get("power_violations") or {}
            out["power_violations"] = {k: power.get(k) for k in (
                "steps_by_reason", "unserved_kwh", "unserved_peak_kw", "unaccepted_fc_kwh", "unaccepted_regen_kwh")}
    return out


def cost_model(args, baseline_trial):
    """Prices, guard limits and how the reward's own weights compare with the selection prices."""
    return {**price_model(), "guards": guard_limits(baseline_trial, args),
            "reward_weight_alignment": price_alignment(args.w_h2, args.w_fc, args.w_batt),
            "note": "Adoption uses only these prices on the measured ep399 fuel_gkm, fc_loss and batt_loss. "
                    "The reward's weights are free to differ; reward_weight_alignment compares the settings "
                    "weights with the selection prices and is a fact, not an instruction."}


def _context(args, champion, baseline, edit_base, edit_mode, summary, baseline_trial=None):
    """Every number is tied to the reward_id that produced it (feedback-attribution guard)."""
    members = archive_members(summary) if summary.get("archive") else []
    repairs = repair_targets(summary) if summary.get("archive") and summary.get("champion_id") else []
    return {"objective": OBJECTIVE,
            "cost_model": cost_model(args, baseline_trial or summary.get("baseline") or {}),
            "evaluation_conditions": {"seed": args.seed, "scenario_name": args.scenario_name, "soc0": args.soc0,
                                      "episodes": 400, "checkpoint_episode": 399,
                                      "fuel_metric_basis": DETERMINISTIC_FUEL_BASIS},
            "edit_mode": edit_mode, "edit_goal": MODE_GOALS[edit_mode],
            "edit_base": _view(edit_base, source=True, physics=True),
            "champion": _view(champion, physics=True),
            "baseline": _view(baseline, physics=True),
            "experiment_plan": experiment_plan(args, len(summary.get("iterations", [])) + 1),
            "edit_base_vs_champion": _delta(edit_base, champion),
            "edit_base_vs_baseline": _delta(edit_base, baseline),
            "archive": [{k: e.get(k) for k in ("reward_id", "parent_id", "iteration", "final_ep399",
                                               "operating_cost", "guard_checks", "fuel_breakdown")}
                        for e in members],
            "archive_note": "archive = cost-fuel Pareto front of guard-feasible rewards plus baseline and "
                            "champion; guard_failed_cheaper_than_champion = cheaper rewards that failed a guard",
            "guard_failed_cheaper_than_champion": [
                {k: e.get(k) for k in ("reward_id", "parent_id", "iteration", "final_ep399", "operating_cost",
                                       "guard_checks", "fuel_breakdown")} for e in repairs],
            "settings": {k: getattr(args, k) for k in ("soc0", "soc_target", "soc_low", "soc_high",
                         "w_soc", "w_h2", "w_fc", "w_batt", "ramp_limit_kw", "validation_min_in_bounds")},
            "previous_experiments": [previous_experiment(row, baseline)
                                     for row in summary.get("iterations", [])[-5:]]}


def previous_experiment(row, baseline):
    out = {k: row.get(k) for k in ("iteration", "edit_base", "candidate", "decision",
                                   "verdict", "observed_relation", "reward_diff")}
    candidate = row.get("candidate") or {}
    out["physics_delta_vs_baseline"] = {
        "reference_reward_id": baseline["reward_id"],
        "candidate_reward_id": candidate.get("candidate_id"),
        "deltas": {k: v - baseline["physics"][k] for k, v in candidate.get("physics", {}).items()
                   if _finite(v) and _finite(baseline.get("physics", {}).get(k))}}
    return out


def experiment_plan(args, iteration):
    if getattr(args, "search_plan", "archive") != "fuel_diagnostics_v1":
        return {"name": "archive", "iteration": iteration}
    instructions = {
        2: "Battery-only ablation from baseline. Multiply batt_soh_cost by one constant in [1.05, 1.25]. "
           "Keep fuel, SOC and FC cost functions exactly unchanged. Test throughput/loss reduction; "
           "watch for increased low-output FC operation. The range is a hypothesis, not an optimum.",
        3: "SOC-only ablation from baseline. Keep fuel and both degradation costs unchanged, and preserve "
           "out-of-bounds SOC cost. Use measured SOC and regime evidence to change only in-bounds tracking. "
           "Retain a nonnegative quadratic anchor without a deadband; do not assume stronger centering saves fuel.",
        4: "Use measured low-load and regeneration diagnostics to address avoidable FC generation and battery "
           "losses. Select one causal mechanism. Raw H2 or FC efficiency alone cannot establish an improvement.",
    }
    return {"name": "fuel_diagnostics_v1", "iteration": iteration,
            "instruction": instructions.get(iteration,
                "Refine the measured best available base, targeting the worst development cycle/regime. "
                "Prefer one interpretable change; preserve demonstrated gains. Do not repeat failed "
                "weight directions without new physical evidence."),
            "data_policy": "Only training-route evidence and registered training-constituent development cycles; "
                           "the six final evaluation cycles are excluded.",
            "interpretation": "Each candidate trains fresh for 400 episodes; iterations are experiments, not continued SAC training."}


def verify_experiment(source, parent, args, iteration):
    """Probe-based ablation enforcement, in addition to the executable reward contract."""
    if getattr(args, "search_plan", "archive") != "fuel_diagnostics_v1" or iteration not in (2, 3):
        return {"status": "pass"}
    from candidate_validation import verify_direction, compile_reward, checked_reward, _probe_state
    from multi_agent_review import _reward_behavior_grid
    role = {"name": "battery_only" if iteration == 2 else "soc_only",
            "cost_key": "batt_soh_cost" if iteration == 2 else "soc_cost"}
    result = verify_direction(source, parent, role, args)
    if result["status"] != "pass":
        return result
    new_fn, old_fn = compile_reward(source), compile_reward(parent)
    ratios = []
    for case in _reward_behavior_grid():
        new, old = _probe_state(case, args), _probe_state(case, args)
        checked_reward(new_fn, new)
        checked_reward(old_fn, old)
        if iteration == 2 and old.info["batt_soh_cost"] > 0:
            ratios.append(new.info["batt_soh_cost"] / old.info["batt_soh_cost"])
        if iteration == 3 and (new.info["soc_cost"] < 0 or
                (abs(new.SOC - new.SOC_target) > 1e-6 and new.info["soc_cost"] <= 0)):
            return {"status": "fail", "reason": "SOC-only ablation requires a positive anchor away from target"}
    if iteration == 2 and (not ratios or min(ratios) < 1.05 - 1e-8 or max(ratios) > 1.25 + 1e-8
                          or max(ratios) - min(ratios) > 1e-8):
        return {"status": "fail", "reason": "Battery-only ablation requires one constant multiplier in [1.05, 1.25]"}
    if iteration == 3:
        # Check quadratic scaling on both sides of target, including close-to-target
        # points missing from the general behavior grid. Asymmetric coefficients are allowed.
        case = _reward_behavior_grid()[0]
        state = _probe_state(case, args)
        state.SOC = state.SOC_target
        checked_reward(new_fn, state)
        if abs(state.info["soc_cost"]) > 1e-9:
            return {"status": "fail", "reason": "SOC anchor must be zero at target"}
        for boundary in (args.soc_low, args.soc_high):
            coefficients = []
            for fraction in (.025, .1, .25, .5, .75):
                state = _probe_state(case, args)
                error = (boundary - state.SOC_target) * fraction
                state.SOC = state.SOC_target + error
                checked_reward(new_fn, state)
                coefficients.append(state.info["soc_cost"] / error ** 2)
            if min(coefficients) <= 0 or not all(math.isclose(c, coefficients[0], rel_tol=1e-6)
                                                 for c in coefficients):
                return {"status": "fail", "reason": "SOC-only ablation must retain a quadratic anchor without deadband"}
    return {"status": "pass", "basis": "behavioral_probe_grid_not_a_formal_proof"}


def _baseline_rollout(trial):
    """The stored ep399 deterministic rollout of a trial, if compact artifacts kept it."""
    directory = (trial or {}).get("trajectory_dir")
    if not directory:
        return None
    path = Path(directory) / f"episode_{int((trial or {}).get('episodes', 400)) - 1:05d}.npz"
    return path if path.is_file() else None


def _measured_signal_note(trial):
    """Measured battery/FC signal magnitudes, so penalty coefficients on them are not sized from guesses."""
    path = _baseline_rollout(trial)
    if path is None:
        return ""
    import numpy as np
    d = np.load(path)
    loss, current = np.asarray(d["P_batt_loss_kw"], float), np.asarray(d["I"], float)
    p_batt, p_fc = np.abs(np.asarray(d["battery_delivered_kw"], float)), np.asarray(d["fc_applied_kw"], float)
    loaded = np.abs(current) > 1.0
    r0 = loss[loaded] * 1000 / current[loaded] ** 2 if loaded.any() else np.array([np.nan])
    q = lambda x, k: float(np.quantile(x, k))
    return ("MEASURED SIGNALS (baseline ep399 deterministic rollout, 1-s steps; use these, do not estimate):\n"
            f"P_batt_loss_kw (instantaneous kW, = r0*I_batt^2/1000): mean {loss.mean():.4g}, p95 {q(loss, .95):.4g}, "
            f"max {loss.max():.4g}; its energy over the drive is sum/3600 = {loss.sum() / 3600:.4g} kWh\n"
            f"I_batt (A, signed): RMS {np.sqrt(np.mean(current ** 2)):.4g}, mean |I| {np.abs(current).mean():.4g}, "
            f"p95 |I| {q(np.abs(current), .95):.4g}, max |I| {np.abs(current).max():.4g}; "
            f"so mean I_batt^2 = {np.mean(current ** 2):.4g} A^2\n"
            f"pack resistance r0 = P_batt_loss_kw*1000/I^2: {np.nanmin(r0):.4g}-{np.nanmax(r0):.4g} ohm\n"
            f"|P_batt| (kW): mean {p_batt.mean():.4g}, p95 {q(p_batt, .95):.4g}; "
            f"P_FCS (kW): mean {p_fc.mean():.4g}, p95 {q(p_fc, .95):.4g}\n")


def _fc_degradation_note(entry):
    """Measured start-versus-low-output tradeoff of one policy; adoption prices total fc_loss."""
    p = entry.get("physics") or {}
    starts, start_loss = p.get("fc_start_stop_count"), p.get("fc_start_stop_soh_loss")
    total = (entry.get("final_ep399") or {}).get("fc_loss")
    if not starts or not _finite(start_loss) or not _finite(total) or total <= 0:
        return ""
    per_start = start_loss / starts
    text = (f" FC DEGRADATION (measured, reward_id {entry['reward_id']}, ep399 rollout): {starts} FC starts at "
            f"{per_start:.3g} SOH loss each are {100 * start_loss / total:.0f}% of fc_loss {total:.3g}.")
    low_steps, low_loss = p.get("fc_low_power_count"), p.get("fc_low_power_soh_loss")
    if low_steps and _finite(low_loss) and low_loss > 0:
        text += (f" One start costs as much FC SOH as {per_start / (low_loss / low_steps):.0f} steps of "
                 "low-power operation.")
    return text + (" Switching the FC off to save hydrogen adds a start when it comes back on; keeping it on "
                   "at low output avoids the start but burns hydrogen. Adoption prices the TOTAL fc_loss "
                   "(start-stop + load-change + low-power + high-power SOH loss) in the operating cost, not the "
                   "start count: fc_start_stop_count is a diagnostic. More starts can pass if the other "
                   "components fall by more, and fewer starts can still fail. The stateless reward cannot detect "
                   "a start itself: starts are priced only through dSOH_FCS.")


def _start_economics_note(trial, guards):
    """Unit-consistent start-versus-hydrogen facts measured on the baseline ep399 rollout.

    A start's SOH loss converted to grams of H2 at the selection prices is a price, not hydrogen that has
    to be burned; reviewers compared it with the fuel-guard headroom (and mixed per-drive grams with
    per-100 km grams). This note gives the physical hydrogen cost of avoiding starts in the guard's units.
    """
    import numpy as np
    path = _baseline_rollout(trial)
    if path is None:
        return ""
    d = np.load(path)
    if not {"h2_fcs", "d_s_s", "travel"} <= set(d.files):
        return ""
    h2, d_ss = np.asarray(d["h2_fcs"], float), np.asarray(d["d_s_s"], float)
    dt = float(d["dt_s"]) if "dt_s" in d.files else 1.0
    distance_km = float(np.asarray(d["travel"], float)[-1]) / 1000.0
    starts = int(np.sum(d_ss > 0))
    if starts == 0 or distance_km <= 0 or not np.any(h2 > 0):
        return ""
    off = h2 <= 0
    edges = np.diff(np.r_[0, off.astype(int), 0])
    begins, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    # Only an off interval inside the drive is followed by a start that staying on would avoid; the
    # reset start (FC off before step 0) and an interval running to the end of the drive are not.
    inside = (begins > 0) & (ends < len(h2))
    lengths = (ends - begins)[inside] * dt
    off_s = float(lengths.sum())
    n_avoidable = int(inside.sum())
    rate = float(np.min(h2[~off])) / dt  # g/s at the lowest on-power this policy used
    loss = float(np.mean(d_ss[d_ss > 0])) * 1e-5  # run_FC_SOH: d_s_s % * 1e-3 / 100
    usd_drive = loss * USD_PER_FC_LOSS
    per_100 = 100.0 / distance_km
    bridge_g = rate * off_s
    text = (f" FC START ECONOMICS (measured on the baseline ep399 rollout, reward_id {_rid(trial)}; one drive = "
            f"{distance_km:.4g} km): {starts} starts; {n_avoidable} of them follow an FC-off interval inside the "
            f"drive, totalling {off_s:.0f} s off (lengths in s: {sorted(int(x) for x in lengths)[:30]}); the "
            f"drive begins with the FC off, so a policy that uses the FC has at least one start. Price of one "
            f"start: SOH loss {loss:.3g} = {usd_drive:.3g} USD per drive = {usd_drive * per_100:.3g} USD per 100 km. "
            f"Physical hydrogen to avoid a start: keeping the FC on at the lowest on-power of this rollout burns "
            f"{rate:.3g} g H2 per s, so bridging an off interval of t s burns at most {rate:.3g}*t g raw H2. "
            f"Bridging all {n_avoidable} intervals burns at most {bridge_g:.3g} g per drive = "
            f"{bridge_g / distance_km:.3g} g/km raw H2 (an upper bound for fuel_gkm: that energy charges the battery "
            f"and returns through the SOC correction) and avoids up to {n_avoidable} starts = "
            f"{n_avoidable * usd_drive * per_100:.3g} USD per 100 km.")
    eff = ((policy_metrics(trial) or {}).get("paper_fuel") or {}).get("fc_efficiency")
    if _finite(eff) and eff > 0 and guards and _finite(guards.get("soc_drift_abs_max")):
        from operating_cost import BATT_KWH
        kwh = bridge_g / 1000.0 * 33.33 * eff  # H2 LHV 33.33 kWh/kg, FC system efficiency of this rollout
        text += (f" Charge-sustaining side: unless FC output is lowered elsewhere, that bridging energy "
                 f"({bridge_g:.3g} g x 33.33 kWh/kg x FC efficiency {eff:.3g} = {kwh:.3g} kWh) goes into the "
                 f"{BATT_KWH} kWh battery, up to {kwh / BATT_KWH:+.3g} SOC by the end of the drive (before "
                 f"charging losses), against the guard |SOC_final - SOC_initial| <= "
                 f"{guards['soc_drift_abs_max']:.3g}.")
    fuel = (policy_metrics(trial) or {}).get("fuel_gkm")
    if guards and _finite(guards.get("fuel_gkm_max")) and _finite(fuel):
        head = guards["fuel_gkm_max"] - fuel
        text += (f" Fuel-guard headroom of this rollout: {guards['fuel_gkm_max']:.4g} - {fuel:.4g} = {head:.3g} g/km "
                 f"= {head * distance_km:.3g} g per drive.")
    return text + (" UNIT RULES (apply in every hypothesis): compare g/km only with g/km and grams per drive only "
                   "with grams per drive (g/km x drive km = g per drive). Converting an SOH loss into grams of H2 at "
                   "the selection prices is a PRICE comparison, never hydrogen that must be burned: do not compare "
                   "it with the fuel-guard headroom. The fuel guard limits only SOC-corrected fuel_gkm; FC wear is "
                   "judged in USD through the total cost.")


def _plant_model_note(args):
    """Modeling assumptions behind every measurement (motor/regen efficiency, clamp, FC event sizes)."""
    from env_physics_facts import render_plant_model_note
    return " " + render_plant_model_note(float(args.w_fc))


def _imported_baseline_note(trial):
    """A reused baseline was trained elsewhere; only its evaluation is known to use the current plant."""
    if not (trial or {}).get("baseline_provenance"):
        return ""
    return (" IMPORTED BASELINE: the baseline actor was trained in an earlier run whose plant model is not "
            "verified to match the current one, and was only re-evaluated here without training. Its listed "
            "measurements are current-plant values, but its behavior (FC starts, low-output operation, "
            "regeneration use) was learned under the earlier physics and pricing: do not read it as what the "
            "current plant rewards, and expect freshly trained candidates to differ for that reason alone.")


def _replayed_cost_lines(trial, args):
    """Per-step cost means of the trial's own reward on its current-plant ep399 rollout."""
    from candidate_validation import measure_cost_scale
    measured = measure_cost_scale(trial["reward_source"], _baseline_rollout(trial), args)
    if measured["status"] != "measured":
        return []
    t = measured["term_mean_per_step"]
    return ["epi %d [current-plant replay]: mean_cost soc %.3f, h2 %.3f, fcs %.3f, batt %.3f, obj %.3f"
            % (int(trial.get("episodes", 400)) - 1, t["soc_cost"], t["h2_cost"], t["fcs_soh_cost"],
               t["batt_soh_cost"], t["objective_cost"])]


def _cost_scale_note(trial, args=None):
    """Measured per-step cost magnitudes, so extra penalty coefficients are sized, not guessed."""
    chunk = (trial or {}).get("chunk") or {}
    log = Path(chunk.get("log_path", ""))
    lines = []
    if (trial or {}).get("baseline_provenance"):
        # The copied train_log holds costs from the run that trained the actor (possibly an older
        # plant model); mixing them with current-plant signals would mis-size every penalty.
        lines = _replayed_cost_lines(trial, args) if args is not None else []
    elif log.is_file():
        prefix = f"epi {chunk.get('end_episode')}"
        lines = [line.strip() for line in log.read_text(encoding="utf-8", errors="replace").splitlines()
                 if line.startswith(prefix) and ("mean_cost" in line or "P_fc min" in line)]
    signals = _measured_signal_note(trial)
    if not lines and not signals:
        return ""
    scale = ("PENALTY SCALE (baseline, measured per-step means; costs are per step):\n" + "\n".join(lines) + "\n"
             if lines else "")
    return (scale + signals + _price_deviation_note(trial, args) +
            "Size every change from the measured means above (for a quadratic term use mean I_batt^2, not "
            "(mean |I|)^2) and show that arithmetic in your hypothesis. Before training, the candidate is replayed "
            "on this rollout and rejected if its non-SOC objective (objective_cost - soc_cost) deviates from the "
            "operating cost at the selection prices by more than the configured multiple of that cost (per-step "
            "mean |deviation|). Multipliers on the logged terms and extra terms count alike: moving the FC/battery "
            "weights toward the selection prices (cost_model.reward_weight_alignment) shrinks the deviation, a "
            "penalty orders of magnitude above the operating cost grows it and can make the policy starve the FC "
            "or drain/overcharge the battery.\n")


def _price_deviation_note(trial, args):
    """How far the trial's own reward sits from the selection-priced operating cost on its ep399 rollout."""
    if args is None or not (trial or {}).get("reward_source"):
        return ""
    measured = measure_cost_scale(trial["reward_source"], _baseline_rollout(trial), args)
    if measured["status"] != "measured":
        return ""
    total, dev = measured["selection_cost_mean"], measured["price_deviation_mean_abs"]
    return ("SELECTION-PRICED COST (same rollout, reward units = w_h2 per g H2): mean per step %.4g; this reward's "
            "non-SOC objective deviates from it by a mean |deviation| of %.4g per step = %.3gx.\n"
            % (total, dev, dev / max(total, 1e-12)))


CHANGE_SPEC_INSTRUCTION = (
    "End with a CHANGE_SPEC JSON code block (```json ... ```) that states your instructions as the reward change "
    "the proposal must implement; the proposed code is replayed together with edit_base on the baseline ep399 "
    "rollout and rejected if it does not match. Form: {\"term_ratio\": {\"soc_cost\": R, \"h2_cost\": R, "
    "\"fcs_soh_cost\": R, \"batt_soh_cost\": R}, \"extra_terms\": \"unchanged\"|\"none\"|\"added\"}. R is "
    "the expected ratio of the candidate's per-step mean of that logged term to edit_base's on the same rollout: a "
    "number for a constant multiplier (5 for a weight x5; 1 for unchanged), or \"changed\" for any other change "
    "of that term. A term you omit must stay unchanged. extra_terms covers objective_cost minus the four logged "
    "terms: \"unchanged\" keeps edit_base's extra terms, \"none\" removes them all, \"added\" adds or changes "
    "extra terms. Add \"catalog_terms\": [\"<id>\", ...], the REWARD TERM CATALOG ids the change adds or "
    "reshapes (at least one; a charge-sustaining id when edit_base fails the charge-sustaining guard); "
    "charge-sustaining terms change soc_cost, price terms change extra_terms.")
SPEC_RATIO_TOLERANCE = 0.10


def parse_change_spec(text):
    """The last JSON object in the orchestrator text that is a valid CHANGE_SPEC, normalized; else None."""
    import re
    candidates = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text or "", flags=re.S)
    start = (text or "").rfind('{"term_ratio"')
    if start >= 0:
        candidates.append(text[start:text.rfind("}") + 1])
    for raw in reversed(candidates):
        try:
            spec = json.loads(raw)
        except ValueError:
            continue
        ratios = spec.get("term_ratio") if isinstance(spec, dict) else None
        if not isinstance(ratios, dict) or not set(ratios) <= set(COST_KEYS):
            continue
        if not all(r == "changed" or (_finite(r) and r >= 0) for r in ratios.values()):
            continue
        extra = spec.get("extra_terms", "unchanged")
        if extra not in ("unchanged", "none", "added"):
            continue
        catalog = spec.get("catalog_terms", [])
        if not isinstance(catalog, list) or not all(t in TERMS for t in catalog):
            continue
        out = {"term_ratio": {k: (float(v) if v != "changed" else v) for k, v in ratios.items()},
               "extra_terms": extra}
        if catalog:
            out["catalog_terms"] = list(dict.fromkeys(catalog))
        return out
    return None


def verify_change_spec(source, parent_source, spec, trajectory_path, args):
    """Does the proposal implement the orchestrator's CHANGE_SPEC? Measured on the baseline rollout."""
    cand = measure_cost_scale(source, trajectory_path, args)
    base = measure_cost_scale(parent_source, trajectory_path, args)
    if cand["status"] != "measured" or base["status"] != "measured":
        return {"status": "unavailable", "reason": cand.get("reason") or base.get("reason")}
    mismatches, measured = [], {}
    for key in COST_KEYS:
        expected = spec["term_ratio"].get(key, 1.0)
        c, b = cand["term_mean_per_step"][key], base["term_mean_per_step"][key]
        same = math.isclose(c, b, rel_tol=1e-6, abs_tol=1e-12)
        if abs(b) <= 1e-12:
            measured[key] = {"candidate_mean": c, "edit_base_mean": b, "ratio": None}
            ok = same if expected == 1.0 else True  # a zero base mean cannot verify a multiplier
        else:
            ratio = c / b
            measured[key] = {"candidate_mean": c, "edit_base_mean": b, "ratio": ratio}
            ok = (not same if expected == "changed"
                  else same if expected == 1.0
                  else abs(ratio - expected) <= SPEC_RATIO_TOLERANCE * expected)
        if not ok:
            mismatches.append(f"{key}: spec {expected}, measured ratio {measured[key]['ratio']}")
    c_extra, b_extra = cand["extra_cost_mean_abs"], base["extra_cost_mean_abs"]
    measured["extra_terms"] = {"candidate_mean_abs": c_extra, "edit_base_mean_abs": b_extra}
    expected = spec["extra_terms"]
    same = math.isclose(c_extra, b_extra, rel_tol=1e-6, abs_tol=1e-12)
    if (expected == "unchanged" and not same) or (expected == "none" and c_extra > 1e-12) \
            or (expected == "added" and same):
        mismatches.append(f"extra_terms: spec {expected}, measured mean |extra| {c_extra:.4g} "
                          f"(edit_base {b_extra:.4g})")
    out = {"status": "fail" if mismatches else "pass", "spec": spec, "measured": measured,
           "basis": "candidate and edit_base replayed on the baseline ep399 rollout",
           "ratio_tolerance": SPEC_RATIO_TOLERANCE}
    if mismatches:
        out["reason"] = ("orchestrator_conformance: the proposal does not implement the orchestrator CHANGE_SPEC "
                         + json.dumps(spec) + ". Mismatches: " + "; ".join(mismatches)
                         + ". Implement the orchestrator's change exactly, without other edits.")
    return out


def propose_reward(*, args, client, champion, summary, iter_dir, edit_base=None, edit_mode="champion_improve"):
    """Six bounded calls normally; repair retries reuse the same review context."""
    from multi_agent_review import _tracked_complete
    from llm_presets import get_agent_model
    guards = guard_limits(summary.get("baseline", champion), args)
    champion_entry = _entry(champion, None, None, guards)
    baseline_entry = _entry(summary.get("baseline", champion), None, None, guards)
    edit_base = edit_base or champion_entry
    context = _context(args, champion_entry, baseline_entry, edit_base, edit_mode, summary,
                       baseline_trial=summary.get("baseline", champion))
    context_id = hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()
    path = iter_dir / "review.json"
    review = json.loads(path.read_text()) if path.exists() else {
        "context_id": context_id, "context": context, "stages": {}, "attempts": []}
    if review.get("context_id") != context_id:
        raise RuntimeError("Saved proposal context differs from the current champion/edit base; start a new run")
    usage_path = iter_dir / "llm_usage.json"
    usage = json.loads(usage_path.read_text()).get("records", []) if usage_path.exists() else []

    def call(stage, prompt, limit, role):
        if stage not in review["stages"]:
            raw = _tracked_complete(client=client, usage_records=usage, usage_path=usage_path,
                                    stage=stage, prompt=prompt, temperature=args.llm_temperature,
                                    max_tokens=min(args.llm_max_tokens, limit), timeout_sec=args.llm_timeout_sec,
                                    model=get_agent_model(client.provider, role, client.model))
            review["stages"][stage] = {"response": raw}
            if args.artifact_detail == "full":
                review["stages"][stage]["prompt"] = prompt
            write_json(path, review)
        # Bound downstream advice even when a provider exceeds its requested limit.
        return review["stages"][stage]["response"][:4000]

    provenance = ("Every measurement is labelled with the reward_id that produced it; never attribute a "
                  "number to a different reward. edit_base is the code to modify; adoption is judged ONLY "
                  "against the champion, at the stated evaluation_conditions, on total operating cost "
                  "(operating_cost.total_usd) with the charge-sustaining, fuel and battery guards of "
                  "cost_model.guards. "
                  "Read each operating_cost breakdown before choosing a lever: FC wear (fc_usd) and FC "
                  "hydrogen (h2_usd) are the core levers; battery wear (batt_usd) is counted and guarded. "
                  "Tail data are single-run diagnostics, not evidence of reward reproducibility. "
                  + BATTERY_PROTECTION + " " + CHARGE_SUSTAINING)
    provenance += (" Registered development cycles, when enabled, must also pass mean-normalized fuel, "
                   "worst-cycle regression and fixed baseline degradation checks. Use previous candidates' "
                   "physics and baseline deltas, including rejected candidates. Inspect battery throughput, "
                   "ohmic loss, FC start count, low-output FC operation, regeneration FC energy and SOC drift "
                   "together. Regime groups overlap: never sum them or call raw-H2 reductions charge-sustaining "
                   "gains. Unmeasured causal mechanisms are hypotheses, not observed facts.")
    provenance += _fc_degradation_note(baseline_entry)
    provenance += _start_economics_note(summary.get("baseline", champion), context["cost_model"]["guards"])
    provenance += _imported_baseline_note(summary.get("baseline", champion))
    provenance += _plant_model_note(args)
    # Archive search builds rewards from the term catalog; controlled ablation plans keep their own rules.
    catalog_on = context["experiment_plan"]["name"] == "archive" and getattr(args, "reward_term_catalog", True)
    baseline_rollout = _baseline_rollout(summary.get("baseline", champion))
    edit_rollout = _baseline_rollout({"trajectory_dir": edit_base.get("trajectory_dir"), "episodes": 400})
    require_cs = catalog_on and (edit_base.get("guard_checks") or {}).get("charge_sustaining") is False
    if catalog_on:
        facts_rollout = edit_rollout or baseline_rollout
        provenance += ("\n" + catalog_prompt(guards["soc_drift_abs_max"])
                       + f"(Facts below: ep399 rollout of reward_id {edit_base['reward_id'] if edit_rollout else baseline_entry['reward_id']}.)\n"
                       + drift_facts(facts_rollout, args, guards["soc_drift_abs_max"], reference_rollout=baseline_rollout)
                       + efficiency_facts(facts_rollout))
        if require_cs:
            provenance += ("EDIT BASE FAILS THE CHARGE-SUSTAINING GUARD (edit_base.guard_checks): this proposal must "
                           "add or reshape a charge-sustaining catalog term sized inside the DRIFT FACTS range.\n")
    compact_context = json.dumps(context, ensure_ascii=False)
    advice = {}
    if args.multi_agent_review:
        for role, focus in (("fuel_soc", "FC hydrogen cost and charge sustaining: SOC-corrected fuel, terminal "
                                         "SOC drift against its guard, and how much hydrogen a lower FC wear "
                                         "may cost inside the fuel guard (where the cost-fuel tradeoff lands)"),
                            ("fc_durability", "FC degradation cost, usually the largest share of the total: FC "
                                              "start count versus low-output operation, then power changes"),
                            ("battery_degradation", "battery degradation cost and its guard: physical battery "
                                                    "loss, cycling and SOC, and whether FC wear is being shifted "
                                                    "onto the battery"),
                            ("reward_hacking", "reward exploits, misleading proxies and simulator state writes")):
            print(f"[review] {role}", flush=True)
            advice[role] = call(role, f"Review {focus}. Give at most 3 concise hypotheses and their tradeoffs. "
                                "Use only the supplied measurements, distinguish final from tail data, "
                                "and do not claim an untrained proposal improves anything. " + provenance
                                + "\n" + compact_context, 700, role)
        advice["orchestrator"] = call("orchestrator", "Mediate the reviewer tradeoffs and synthesize ONE "
            "coherent change to the edit_base reward that serves edit_goal. At most 5 concise instructions. "
            "Honor context.experiment_plan, including controlled ablations when specified. Total operating cost "
            "below the champion's is mandatory, with terminal SOC drift, fuel and battery loss inside "
            "cost_model.guards; state which cost share (fc_usd, h2_usd, batt_usd) the change targets and what it "
            "may cost in the others and in fuel (where the candidate should land on the cost-fuel front), "
            "including one instruction that keeps the terminal SOC drift inside its guard and one that keeps "
            "battery degradation inside its guard. "
            + CHANGE_SPEC_INSTRUCTION + " " + provenance + "\n" + _cost_scale_note(summary.get("baseline", champion), args)
            + "\n" + compact_context + "\nReviewer hypotheses:\n" + json.dumps(advice), 1200, "orchestrator")
        spec = parse_change_spec(review["stages"]["orchestrator"]["response"])  # untruncated
        if catalog_on and spec is not None and not spec.get("catalog_terms"):
            spec = None  # the catalog ids are part of the spec in archive search
        # A spec that contradicts its own catalog ids cannot be implemented; ask once instead of 10 proposals.
        conflict = spec_family_conflict(spec) if catalog_on and spec is not None else None
        if spec is None or conflict:  # one bounded repair: the instructions stand, only the JSON is requested
            if conflict:
                review["change_spec_conflict"] = {"spec": spec, "reason": conflict}
            spec = parse_change_spec(call("orchestrator_spec", "Return ONLY the CHANGE_SPEC JSON code block that "
                                          "states these orchestrator instructions exactly. " + CHANGE_SPEC_INSTRUCTION
                                          + ("\nYour previous CHANGE_SPEC contradicts the catalog: " + conflict
                                             + ". State it consistently." if conflict else "")
                                          + "\nOrchestrator instructions:\n" + advice["orchestrator"], 400,
                                          "orchestrator"))
            if catalog_on and spec is not None and spec_family_conflict(spec):
                spec = None  # still contradictory: no binding spec rather than an unimplementable one
        review["change_spec"] = spec if spec is not None else {"status": "unavailable"}
        write_json(path, review)
    spec = review.get("change_spec") if isinstance(review.get("change_spec"), dict) else None
    spec = spec if spec and "term_ratio" in spec else None
    plan = context["experiment_plan"]
    scope = (plan["instruction"] if plan["name"] != "archive" else
             "Build the change from the REWARD TERM CATALOG: add a catalog term the edit base lacks or reshape one "
             "it has, and log every catalog term as self.info['term_<id>']. Weights may also change, but a "
             "weight change alone is rejected. Prefer one interpretable mechanism supported by measured failures."
             if catalog_on else
             "You may jointly change ANY of the fuel, SOC, FC and battery cost functions and weights. "
             "Prefer one interpretable mechanism supported by measured failures.")
    base_prompt = (
        "Generate ONE complete def get_reward(self) in a Python code block, starting from "
        "edit_base.reward_source and serving edit_goal. Briefly explain your hypothesis, including its "
        "expected effect on terminal SOC drift against cost_model.guards.soc_drift_abs_max, on fuel against "
        "cost_model.guards.fuel_gkm_max, and on battery throughput and batt_loss against "
        "cost_model.guards.batt_loss_max. "
        + scope + " " + provenance + " Return reward = -objective_cost. objective_cost MAY include extra penalty terms beyond "
        "soc_cost/h2_cost/fcs_soh_cost/batt_soh_cost; keep those four logs truthful for their own terms. "
        "Read inputs only as plain self.<name> attributes: no getattr(), no self.info.get(), no names "
        "starting with '_'. The reward is stateless per step: no previous-step memory (e.g. no prev FC power). "
        "Use pure scalar arithmetic and numeric numpy/math functions; no imports, loops, helper functions "
        "or writes to simulator state. self.info logging is allowed. Keep required log keys: "
        + ", ".join(REQUIRED_KEYS) + ". "
        "Available inputs include SOC, SOC_target, SOC_init, soc_bounds, h2_fcs (g per step), "
        "h2_batt/h2_equal (logging), dSOH_FCS, dSOH_batt, P_FCS (kW), P_batt (W), "
        "P_batt_loss_kw, I_batt, P_mot (W, motor electrical power), w_soc, w_h2, w_fc, w_batt. "
        "The reward must change executable behavior. Do not repeat a previously trained reward. "
        "One verified proposal will be trained from scratch for 400 episodes; no pilot or candidate competition.\n"
        + _cost_scale_note(summary.get("baseline", champion), args)
        + (("BINDING ORCHESTRATOR CHANGE_SPEC (the candidate is replayed with edit_base on the baseline ep399 rollout "
            "and rejected unless it matches; implement the orchestrator's change exactly, nothing else): "
            + json.dumps(spec) + "\n") if spec else "")
        + compact_context + "\nAdvice (hypotheses only):\n" + json.dumps(advice, ensure_ascii=False)
    )
    history = {_signature(t["reward_source"]) for t in [summary.get("baseline", champion), champion]}
    history.add(_signature(edit_base["reward_source"]))
    history.update(_signature(e["reward_source"]) for e in summary.get("archive", []))
    history.update(summary.get("trained_signatures", []))
    attempts = []
    for attempt in range(1, args.proposal_attempts + 1):
        prompt = base_prompt + "\nRepair only these previous verification errors:\n" + json.dumps(attempts)
        stage = f"proposal_{attempt}"
        call(stage, prompt, 4000, "proposer")
        raw = review["stages"][stage]["response"]
        try:
            source = ensure_logging_contract(extract_method_from_llm_response(raw), REQUIRED_KEYS)
            if _signature(source) in history:
                raise ValueError("Executable reward duplicates a previously trained reward")
            verification = verify_candidate(source, args)
            if verification["status"] != "pass":
                raise ValueError(json.dumps(verification))
            scale = verify_cost_scale(source, _baseline_rollout(summary.get("baseline", champion)), args)
            if scale["status"] == "fail":
                raise ValueError(scale["reason"])
            verification["cost_scale"] = scale
            if spec:
                conformance = verify_change_spec(source, edit_base["reward_source"], spec,
                                                 _baseline_rollout(summary.get("baseline", champion)), args)
                if conformance["status"] == "fail":
                    raise ValueError(conformance["reason"])
                verification["orchestrator_conformance"] = conformance
            design = verify_experiment(source, edit_base["reward_source"], args, plan["iteration"])
            if design["status"] != "pass":
                raise ValueError(json.dumps(design))
            if catalog_on:
                catalog = verify_catalog_terms(source, edit_base["reward_source"], args,
                                               guard=guards["soc_drift_abs_max"], rollout=baseline_rollout,
                                               require_cs=require_cs, edit_rollout=edit_rollout,
                                               declared=(spec or {}).get("catalog_terms"))
                if catalog["status"] != "pass":
                    raise ValueError(catalog["reason"])
                verification["catalog"] = catalog
            (iter_dir / "candidate.py").write_text(source, encoding="utf-8")
            review.update(attempts=attempts, verification=verification, selected_attempt=attempt)
            write_json(path, review)
            return source
        except (PatchError, ValueError, SyntaxError, TypeError, ArithmeticError) as exc:
            message = f"{type(exc).__name__}: {exc}" if isinstance(exc, ArithmeticError) else str(exc)
            attempts.append({"attempt": attempt, "error": message[:1600]})
            review["attempts"] = attempts
            write_json(path, review)
    return None


def _configure(args):
    validate_options(args)
    if getattr(args, "search_plan", "archive") == "fuel_diagnostics_v1" and not args.soc_low < args.soc_target < args.soc_high:
        raise ValueError("Controlled SOC ablation requires the target strictly inside SOC bounds")
    if args.chunk_episodes != 400:
        raise ValueError("Sequential AROMA requires chunk_episodes=400 (ep399)")
    if args.ldri_iterations < 1 or args.proposal_attempts < 1:
        raise ValueError("iterations and proposal_attempts must be positive")
    if args.confirmation_seeds != 1:
        raise ValueError("Sequential AROMA searches on one seed; use --confirmation_seed_list for "
                         "post-search confirmation on additional seeds")
    if not args.reset_agent_on_patch:
        raise ValueError("Sequential comparisons require reset_agent_on_patch=True")
    if not math.isfinite(args.validation_min_in_bounds) or not 0 <= args.validation_min_in_bounds <= 100:
        raise ValueError("Invalid SOC in-bounds threshold")
    if args.seed_chunk_dir and not args.seed_reward_file:
        raise ValueError("--seed_chunk_dir requires --seed_reward_file")
    if getattr(args, "fork_from_run_root", "") and args.seed_chunk_dir:
        raise ValueError("--fork_from_run_root and --seed_chunk_dir both supply the baseline; use one")
    if int(args.edit_base_max_stale) < 1:
        raise ValueError("edit_base_max_stale must be >= 1")
    for key in ("cost_max_fuel_increase", "cost_max_batt_increase", "cost_max_soc_drift"):
        value = getattr(args, key)
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"{key} must be a finite nonnegative fraction")
    args.seed = 93 if args.seed is None else args.seed
    seeds = [int(s) for s in (args.confirmation_seed_list or [])]
    if len(set(seeds)) != len(seeds):
        raise ValueError("confirmation_seed_list must be unique")
    if args.seed in seeds:
        raise ValueError("confirmation_seed_list must not contain the search seed")
    args.confirmation_seed_list = seeds
    # Persist effective options, so old pool/scenario/LR defaults cannot describe this run.
    args.candidate_pool_size, args.candidate_attempts, args.pilot_episodes = 1, args.proposal_attempts, 0
    args.scenario_validation = args.cycle_segment_validation = False
    args.auto_lr_on_reward_patch = False
    args.validation_min_improvement_gkm = args.validation_min_improvement_fraction = 0.
    args.validation_max_degradation_ratio = 1.
    args.lr_schedule_episodes = args.lr_schedule_episodes or 400


def _actor_path(trial):
    return str(Path(trial["chunk"]["model_dir"]) / "actor_iter001_ep399.pkl")


def final_selection(summary, args, root):
    """L6: re-check the champion against the fixed baseline and really install the baseline on failure."""
    champion, baseline = summary["champion"], summary["baseline"]
    changed = _rid(champion) != _rid(baseline)
    verdict = (compare_policies(champion, baseline, args) if changed
               else {"status": "fail", "reason": "champion_is_baseline", "checks": {}})
    rolled_back = changed and verdict["status"] != "pass"
    selected = baseline if rolled_back else champion
    actor = _actor_path(selected)
    if not Path(actor).is_file():
        raise RuntimeError("Selected ep399 actor is missing; reward was not installed")
    final_file = Path(root) / "final_reward.py"
    final_file.write_text(selected["reward_source"], encoding="utf-8")
    return {"candidate": _brief(selected), "final_actor": actor, "final_reward_file": str(final_file),
            "improvement_confirmed": verdict["status"] == "pass", "verdict": verdict,
            "rolled_back_to_baseline": rolled_back,
            "claim": ("lower total operating cost of the ep399 actor at the search seed/cycle/initial state"
                      if verdict["status"] == "pass"
                      else "no verified improvement; baseline deployed"),
            "reward_verdict": "inconclusive_single_run"}


def register_confirmation_seeds(summary, args, when):
    """Freeze the confirmation seeds once; they can be given at run start or right before L4."""
    seeds = list(args.confirmation_seed_list or [])
    registered = summary.get("confirmation_registration")
    if registered:
        if seeds and seeds != registered["seeds"]:
            raise RuntimeError(f"Confirmation seeds are already registered as {registered['seeds']}; "
                               "they cannot be changed for this run")
        return registered["seeds"]
    if seeds:
        summary["confirmation_registration"] = {"seeds": seeds, "registered_at": when}
    return seeds


def run_confirmation(summary, args, evaluate, save, seeds):
    """L4: fixed final reward vs baseline, fresh paired training on pre-specified unused seeds."""
    if not seeds:
        raise ValueError("--run_confirmation requires --confirmation_seed_list (seeds not used by the search)")
    selection = summary["final_selection"]
    if selection["rolled_back_to_baseline"] or _rid(summary["champion"]) == _rid(summary["baseline"]):
        # No seed is trained, so the search may still be extended afterwards (the skip is kept in history).
        return {"status": "skipped", "reason": "no_champion_change", "iterations_at_skip": len(summary["iterations"])}
    reward, baseline_source = summary["champion"]["reward_source"], summary["baseline"]["reward_source"]
    summary["confirmation"] = {"status": "started", "seeds": seeds, "reward_id": _rid(summary["champion"])}
    save()  # From here on the confirmation seeds count as seen: the search cannot be extended.
    pairs = []
    for seed in seeds:
        base, cand = evaluate(baseline_source, 400, seed), evaluate(reward, 400, seed)
        verdict = compare_policies(cand, base, args)
        pairs.append({"seed": seed, "baseline": _brief(base, args), "candidate": _brief(cand, args),
                      "status": verdict["status"], "reason": verdict.get("reason"), "checks": verdict["checks"],
                      "deltas": {k: verdict.get(k) for k in ("total_cost_delta_usd", "fuel_delta_gkm",
                                                             "fc_loss_delta", "batt_loss_delta")}})
    count = lambda key: sum(bool(p["checks"].get(key)) for p in pairs)
    counts = {"n_seeds": len(pairs), "cost_improved": count("total_cost_strictly_improved"),
              "charge_sustaining": count("charge_sustaining"),
              "fuel_within_guard": count("fuel_within_guard"),
              "battery_within_guard": count("battery_within_guard"),
              "all_checks": sum(p["status"] == "pass" for p in pairs)}
    label = ("observed_on_all_prespecified_seeds" if counts["all_checks"] == len(pairs)
             else "observed_on_some_prespecified_seeds" if counts["all_checks"]
             else "not_observed_on_prespecified_seeds")
    return {"status": "complete", "basis": "fresh_paired_training_on_prespecified_unused_seeds",
            "seeds": seeds, "reward_id": _rid(summary["champion"]), "pairs": pairs, "counts": counts,
            "reward_verdict": label,
            "note": "Run after the search ended and never fed back to the proposer. The deployed actor is "
                    "unchanged by this result. Claim at most: observed on these pre-specified seeds."}


def _write_overview(root, summary):
    lines = ["# AROMA sequential v3 (total operating cost)", "", OBJECTIVE, "",
             f"Status: {summary['workflow_status']}", "",
             "Costs in USD per 100 km (operating_cost.py, same prices as paper_figs_multi_seed.ipynb).", "",
             "| Iteration | Edit mode | Parent | Decision | vs champion | Total cost | H2 cost | FC cost | Battery cost "
             "| g/km (ep399) | raw H2 g/km | SOC corr. g/km | ΔSOC final | FC SOH loss | Battery SOH loss |",
             "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in summary["iterations"]:
        m = (row.get("candidate") or {}).get("final_ep399", {})
        f = (row.get("candidate") or {}).get("fuel_breakdown") or {}
        cost = (row.get("candidate") or {}).get("operating_cost") or {}
        num = lambda v: f"{v:.4g}" if _finite(v) else "—"
        base = row.get("edit_base") or {}
        rel = (row.get("observed_relation") or {}).get("vs_champion", "—")
        lines.append(f"| {row['iteration']} | {base.get('mode', '—')} | {str(base.get('parent_reward_id', '—'))[:12]} | "
                     f"{row['decision']} | {rel} | {num(cost.get('total_usd'))} | {num(cost.get('h2_usd'))} | "
                     f"{num(cost.get('fc_usd'))} | {num(cost.get('batt_usd'))} | "
                     f"{m.get('fuel_gkm', '—')} | {num(f.get('raw_h2_gkm'))} | "
                     f"{num(f.get('soc_correction_gkm'))} | {num(f.get('soc_final_minus_initial'))} | {m.get('fc_loss', '—')} | "
                     f"{m.get('batt_loss', '—')} |")
    lines += ["", "Champion: " + str(summary["champion"]["candidate_id"]), "",
              "Each iter_NNN/summary.md explains the measured decision. Raw artifacts live under trials/.",
              "Compact mode retains all scalar evaluation records but only the final raw policy/trajectory."]
    final = summary.get("final_selection")
    if final:
        lines += ["", "## Deployment (L1/L6)",
                  f"Total operating cost below baseline with SOC drift, fuel and battery inside the guards: "
                  f"**{final['improvement_confirmed']}**"
                  + (" (rolled back to baseline)" if final["rolled_back_to_baseline"] else ""),
                  f"Claim: {final['claim']}",
                  f"[Final reward]({Path(final['final_reward_file']).resolve()})",
                  f"[Final ep399 actor]({Path(final['final_actor']).resolve()})"]
    conf = summary.get("confirmation")
    if conf:
        lines += ["", "## Reward confirmation (L4)", f"Status: {conf['status']}"]
        if conf.get("counts"):
            c, n = conf["counts"], conf["counts"]["n_seeds"]
            lines += [f"Seeds: {conf['seeds']} (pre-specified, unused in search)", "```text",
                      f"cost_improved:        {c['cost_improved']}/{n}",
                      f"charge_sustaining:    {c.get('charge_sustaining', '—')}/{n}",
                      f"fuel_within_guard:    {c['fuel_within_guard']}/{n}",
                      f"battery_within_guard: {c['battery_within_guard']}/{n}", f"all_checks: {c['all_checks']}/{n}",
                      "```",
                      f"Reward verdict: {conf['reward_verdict']}"]
        elif conf.get("reason"):
            lines.append(f"Reason: {conf['reason']}")
    lines += ["", "No unseen-cycle generalization is claimed."]
    if summary.get("development_spec", {}).get("cycles"):
        lines += ["", "## Training-constituent development validation",
                  "Final held-out cycles never enter feedback or selection.",
                  "Cycles: " + ", ".join(summary["development_spec"]["cycles"]),
                  "Mean baseline-normalized total operating cost must improve; each cycle must respect the "
                  "frozen cost-regression cap, physical feasibility, the SOC-drift guard and the baseline fuel/battery guards.",
                  "| Iteration | Mean cost ratio | Worst cost regression | Gate |",
                  "|---|---:|---:|---|"]
        for row in summary["iterations"]:
            gate = row.get("verdict", {}).get("development", {})
            if gate:
                lines.append(f"| {row['iteration']} | {gate.get('mean_cost_ratio', '—')} | "
                             f"{gate.get('worst_cost_regression_fraction', '—')} | "
                             f"{gate['status']} {gate.get('reason', '')} |")
    if summary.get("compute_usage"):
        lines += ["", "Compute: " + json.dumps(summary["compute_usage"])]
    (root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_iteration(directory, row, trial):
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "result.json", row)
    lines = [f"# Iteration {row['iteration']}", "", f"Decision: **{row['decision']}**", "",
             "```json", json.dumps(row, ensure_ascii=False, indent=2), "```", ""]
    if trial and trial.get("chunk"):
        lines += [f"[Training log]({Path(trial['chunk']['log_path']).resolve()})",
                  f"[Evaluation records]({Path(trial.get('evaluation_evidence', '')).resolve()})", ""]
    (directory / "summary.md").write_text("\n".join(lines), encoding="utf-8")


# Proposal/selection-side only: they shape what the LLM proposes, how proposals are screened before
# training and how trained actors are judged, never how a reward is trained or measured. A fork may
# differ in these, nothing else.
FORK_PROPOSAL_SIDE_FILES = ("sequential_workflow.py", "candidate_validation.py", "reward_terms.py")
FORK_PROPOSAL_SIDE_ARGS = ("extra_cost_max_h2_ratio", "cost_scale_max_ratio", "reward_term_catalog",
                           # adoption guards: they judge trained actors, never change training
                           "cost_max_fuel_increase", "cost_max_batt_increase", "cost_max_soc_drift")


def _fork_comparable(manifest):
    """Training/evaluation identity of a manifest: campaign-specific reward_file path and proposal-side parts removed."""
    import copy
    m = copy.deepcopy(manifest)
    m.pop("selection_policy", None)  # the adoption rule's text: it judges trained actors, never trains them
    conditions = m.get("conditions", {})
    reward_file = conditions.pop("reward_file", None)
    for key in FORK_PROPOSAL_SIDE_ARGS:
        conditions.pop(key, None)
    # Without development cycles the development module never evaluates anything for this run.
    tolerated = FORK_PROPOSAL_SIDE_FILES + (() if (m.get("development_validation") or {}).get("cycles")
                                            else ("development_validation.py",))
    hashes = {}
    for path, digest in m.get("source_hashes", {}).items():
        if Path(path).name in tolerated:
            continue
        hashes["<reward_file>" if reward_file and path == str(Path(reward_file)) else path] = digest
    m["source_hashes"] = hashes
    return m


def fork_baseline(source_root, root, manifest, args):
    """Iteration 1 of a new run = the measured baseline of an earlier run with identical training conditions.

    The baseline trial is copied (paths rewritten) and re-stamped with this run's conditions_id, so that new
    candidates pair with it; the original id and the exact differences are recorded in `forked_from`.
    """
    import shutil
    source_root, root = Path(source_root).resolve(), Path(root).resolve()
    old = json.loads((source_root / "run_summary.json").read_text())
    old_manifest = json.loads((source_root / "validation_manifest.json").read_text())
    if old.get("protocol_version") != PROTOCOL_VERSION:
        raise RuntimeError(f"--fork_from_run_root needs a {PROTOCOL_VERSION} run")
    rows = old.get("iterations") or []
    if not rows or rows[0].get("decision") not in ("baseline_trained", "baseline_reused") or "baseline" not in old:
        raise RuntimeError("--fork_from_run_root: the source run has no measured baseline")
    a, b = _fork_comparable(old_manifest), _fork_comparable(manifest)
    if a != b:
        diff = sorted({k for k in set(a["conditions"]) | set(b["conditions"])
                       if a["conditions"].get(k) != b["conditions"].get(k)}
                      | {k for k in set(a["source_hashes"]) | set(b["source_hashes"])
                         if a["source_hashes"].get(k) != b["source_hashes"].get(k)}
                      | {k for k in set(a) | set(b) if k not in ("conditions", "source_hashes") and a.get(k) != b.get(k)})
        raise RuntimeError("--fork_from_run_root: training conditions or training-side code differ: " + ", ".join(diff))
    baseline = old["baseline"]
    if not policy_valid(baseline, args):
        raise RuntimeError("--fork_from_run_root: the source baseline is not a valid ep399 policy")
    trial_dir = Path(baseline["evaluation_evidence"]).parent
    target = root / "trials" / trial_dir.name
    if not target.exists():
        shutil.copytree(trial_dir, target, symlinks=True)
    new_id = _digest(manifest)
    moved = lambda value: json.loads(json.dumps(value).replace(str(source_root), str(root)))
    baseline = moved(baseline)
    baseline["forked_conditions_id"] = baseline["conditions_id"]
    baseline["conditions_id"] = new_id
    if isinstance(baseline.get("identity"), dict):
        baseline["identity"]["conditions_id"] = new_id
    write_json(target / "trial_result.json", baseline)
    old_hashes, new_hashes = old_manifest["source_hashes"], manifest["source_hashes"]
    forked = {"run_root": str(source_root), "iteration": 1, "baseline_id": _rid(baseline),
              "source_conditions_id": baseline["forked_conditions_id"],
              "differing_proposal_side_sources": sorted(
                  Path(k).name for k in set(old_hashes) | set(new_hashes)
                  if Path(k).name in FORK_PROPOSAL_SIDE_FILES + ("development_validation.py",)
                  and old_hashes.get(k) != new_hashes.get(k)),
              "selection_policy_changed": old_manifest.get("selection_policy") != manifest.get("selection_policy"),
              "differing_proposal_side_args": {
                  k: [old_manifest["conditions"].get(k), manifest["conditions"].get(k)]
                  for k in FORK_PROPOSAL_SIDE_ARGS
                  if old_manifest["conditions"].get(k) != manifest["conditions"].get(k)}}
    row = {**moved(rows[0]), "forked_from": forked}
    summary = {"protocol_version": PROTOCOL_VERSION, "iterations": [row], "trained_signatures": [],
               "development_spec": manifest["development_validation"],
               "search_plan": getattr(args, "search_plan", "archive"), "workflow_status": "running",
               "baseline": baseline, "champion": baseline, "baseline_id": _rid(baseline),
               "champion_id": _rid(baseline), "archive": [_entry(baseline, 1, None, guard_limits(baseline, args))], "forked_from": forked}
    _write_iteration(root / "iter_001", row, baseline)
    return summary


def run_sequential_workflow(args, run_root, resume_mode, *, api, trial_factory=None, proposal_fn=None):
    _configure(args)
    root = Path(run_root)
    root.mkdir(parents=True, exist_ok=True)
    args.reward_file = api._resolve_input_path(args.reward_file)
    args.baseline_reward_file = api._resolve_input_path(args.seed_reward_file or args.baseline_reward_file)
    if args.seed_chunk_dir:
        args.seed_chunk_dir = api._resolve_input_path(args.seed_chunk_dir)
        args.seed_reward_file = api._resolve_input_path(args.seed_reward_file)
    manifest = _manifest(args)
    manifest.pop("adoption_policy")  # This protocol does not use the scenario acceptance policy.
    for key in ("confirmation_seed_list", "run_confirmation", "fork_from_run_root"):
        manifest["conditions"].pop(key, None)  # L4/fork controls: recorded in run_summary, not training conditions
    manifest["protocol_version"] = PROTOCOL_VERSION
    manifest["selection_policy"] = OBJECTIVE
    manifest["development_validation"] = manifest_fields(args)
    for name in ("development_validation.py", "operating_cost.py", "reward_terms.py"):
        module = Path(__file__).with_name(name)
        manifest["source_hashes"][str(module.resolve())] = hashlib.sha256(module.read_bytes()).hexdigest()
    manifest["source_hashes"][str(Path(__file__).resolve())] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    summary_path, manifest_path = root / "run_summary.json", root / "validation_manifest.json"
    fork = str(getattr(args, "fork_from_run_root", "") or "").strip()
    if fork and resume_mode:
        raise RuntimeError("--fork_from_run_root starts a new run; it cannot be combined with --resume_run_root")
    if resume_mode:
        summary = json.loads(summary_path.read_text())
        if summary.get("protocol_version") != PROTOCOL_VERSION:
            raise RuntimeError("Cannot convert an existing run to sequential v2; start a new run")
        if json.loads(manifest_path.read_text()) != manifest:
            raise RuntimeError("Sequential conditions/code changed; start a new run")
    elif fork:
        summary = fork_baseline(fork, root, manifest, args)
        write_json(manifest_path, manifest)
        write_json(summary_path, summary)
    else:
        summary = {"protocol_version": PROTOCOL_VERSION, "iterations": [], "trained_signatures": [],
                   "development_spec": manifest["development_validation"],
                   "search_plan": getattr(args, "search_plan", "archive"),
                   "archive": [], "workflow_status": "running"}
        write_json(manifest_path, manifest)
    # ldri_iterations is not restored on resume; the run's own target is (an interrupted 4-iteration
    # run must not silently "complete" at the CLI default of 3).
    if args.resume_additional_iterations:
        total = len(summary["iterations"]) + args.resume_additional_iterations
    elif resume_mode:
        total = summary.get("target_iterations", args.ldri_iterations)
    else:
        total = args.ldri_iterations
    if summary.get("confirmation", {}).get("status") in ("started", "complete") and total > len(summary["iterations"]):
        raise RuntimeError("Confirmation seeds were already used for this run; extending the search would "
                           "adapt to them. Start a new run")
    # L4 is a separate step on a finished search: refuse before any LLM call, training or config write.
    if args.run_confirmation:
        if not resume_mode:
            raise RuntimeError("--run_confirmation is a separate step: run the search first, then "
                               "--resume_run_root <run> --run_confirmation")
        if args.resume_additional_iterations:
            raise RuntimeError("--run_confirmation cannot be combined with --resume_additional_iterations")
        if len(summary["iterations"]) < total or "final_selection" not in summary:
            raise RuntimeError(f"--run_confirmation requires a completed search "
                               f"({len(summary['iterations'])}/{total} iterations); resume it without "
                               "--run_confirmation first")
    config = api._build_run_config(args)
    config.pop("llm_api_key", None)
    config["ldri_iterations"] = summary["target_iterations"] = total
    seeds = register_confirmation_seeds(summary, args, "before_confirmation" if resume_mode else "run_start")
    write_json(root / "run_config.json", config)
    client = api._init_llm_client(args) if total > max(1, len(summary["iterations"])) and not args.skip_llm else None
    train_trial = (trial_factory or TrialEvaluator)(args, root, api, manifest)
    development = DevelopmentEvaluator(args, root, manifest) if getattr(args, "development_cycles", []) else None

    def evaluate(source, episodes, seed):
        trial = train_trial(source, episodes, seed)
        return development(trial) if development is not None else trial
    propose = proposal_fn or propose_reward

    def save():
        write_json(summary_path, summary)
        _write_overview(root, summary)

    if not summary["iterations"]:
        source = ensure_logging_contract(extract_method_source(args.baseline_reward_file, "EMS", "get_reward"), REQUIRED_KEYS)
        baseline = evaluate(source, 400, args.seed)
        if not policy_valid(baseline, args):
            raise RuntimeError("Baseline final ep399 evaluation is incomplete or violates physical/SOC requirements: "
                               + "; ".join(validity_failures(baseline, args)))
        if development is not None:
            results = baseline.get("development_validation", {}).get("results", {})
            invalid = [c for c in args.development_cycles if not results.get(c, {}).get("valid")]
            if invalid:
                raise RuntimeError("Baseline is invalid on development cycles: " + ", ".join(invalid)
                                   + "; inspect development_evaluations before spending candidate training budget")
        summary.update(baseline=baseline, champion=baseline, baseline_id=_rid(baseline), champion_id=_rid(baseline),
                       archive=[_entry(baseline, 1, None, guard_limits(baseline, args))])
        row = {"iteration": 1, "decision": "baseline_reused" if baseline.get("baseline_provenance") else "baseline_trained",
               "candidate": _brief(baseline)}
        summary["iterations"].append(row)
        _write_iteration(root / "iter_001", row, baseline)
        save()
    for iteration in range(len(summary["iterations"]) + 1, total + 1):
        if args.skip_llm:
            break
        champion, baseline = summary["champion"], summary["baseline"]
        mode, parent, reason = select_edit_base(summary, iteration, args)
        directory = root / f"iter_{iteration:03d}"
        directory.mkdir(exist_ok=True)
        source = propose(args=args, client=client, champion=champion, summary=summary, iter_dir=directory,
                         edit_base=parent, edit_mode=mode)
        trial, success = None, False
        row = {"iteration": iteration, "control": _brief(champion), "decision": "proposal_failed",
               "experiment_plan": experiment_plan(args, iteration),
               "edit_base": {"mode": mode, "parent_reward_id": parent["reward_id"], "selection_reason": reason}}
        if source is not None:
            verification = verify_candidate(source, args)
            if verification["status"] != "pass":
                raise ValueError("Proposal failed the executable reward contract")
            design = verify_experiment(source, parent["reward_source"], args, iteration)
            if design["status"] != "pass":
                raise ValueError("Proposal failed the experiment design: " + design.get("reason", ""))
            trial = evaluate(source, 400, args.seed)
            verdict = compare_policies(trial, champion, args, degradation_cap=baseline)
            row.update(candidate=_brief(trial, args), verdict=verdict, decision="retain_champion",
                       observed_relation={"vs_champion": observed_relation(trial, champion, args),
                                          "vs_baseline": observed_relation(trial, baseline, args)},
                       reward_verdict="inconclusive_single_run",
                       tail=tail_diagnostics(trial),
                       reward_diff="".join(difflib.unified_diff(
                           parent["reward_source"].splitlines(True), source.splitlines(True),
                           fromfile=f"parent:{parent['reward_id'][:12]}", tofile="candidate"))[:4000])
            summary["trained_signatures"].append(_signature(source))
            if policy_valid(trial, args):
                entry = _entry(trial, iteration, parent["reward_id"], guard_limits(baseline, args))
                summary["archive"].append(entry)
            if verdict["status"] == "pass":
                summary["champion"], summary["champion_id"] = trial, _rid(trial)
                row["decision"] = "replace_champion"
                success = True
            elif policy_valid(trial, args):
                success = any(e is entry for e in archive_members(summary) + repair_targets(summary))
        parent["children"] += 1
        parent["stale"] = 0 if success else parent["stale"] + 1
        summary["iterations"].append(row)
        summary["workflow_status"] = "running"
        _write_iteration(directory, row, trial)
        save()
        print(f"[iteration {iteration}] {mode} from {parent['reward_id'][:12]}: {row['decision']}", flush=True)
    completed = len(summary["iterations"]) >= total
    summary["final_selection"] = final_selection(summary, args, root)
    summary["workflow_status"] = "completed" if completed else "paused_skip_llm"
    previous = summary.get("confirmation", {})
    if args.run_confirmation:
        if previous.get("status") != "complete":
            summary["confirmation"] = run_confirmation(summary, args, evaluate, save, seeds)
            write_json(root / "confirmation.json", summary["confirmation"])
    elif previous.get("status") not in ("started", "complete"):
        if previous.get("status") == "skipped":
            # A skip trains/evaluates no confirmation seed, so extending afterwards adapts to nothing;
            # keep the record instead of silently overwriting it.
            summary.setdefault("confirmation_history", []).append(previous)
        summary["confirmation"] = {
            "status": "not_run", "registered_seeds": seeds,
            "reason": "separate step: --resume_run_root <run> --run_confirmation [--confirmation_seed_list ...]"}
    if summary["confirmation"].get("reward_verdict"):
        summary["final_selection"]["reward_verdict"] = summary["confirmation"]["reward_verdict"]
    trials = [json.loads(p.read_text()) for p in (root / "trials").glob("*/trial_result.json")]
    usage = [json.loads(p.read_text()) for p in root.glob("iter_*/llm_usage.json")]
    summary["compute_usage"] = {
        "trained_episodes": sum(t.get("trained_episodes", 0) for t in trials),
        "llm_calls": sum(len(u["records"]) for u in usage),
        "reported_tokens": sum(u.get("totals", {}).get("total_tokens", 0) for u in usage),
        "note": "Persisted trials and reported usage only; interrupted work or missing provider usage may be absent.",
    }
    selected = summary["baseline"] if summary["final_selection"]["rolled_back_to_baseline"] else summary["champion"]
    if not args.skip_patch and completed:
        patch_method_in_file(args.reward_file, selected["reward_source"], required_info_keys=REQUIRED_KEYS,
                             backup=True, insert_if_missing=True)
    save()
    print(f"AROMA {summary['workflow_status']}: {root / 'summary.md'}; "
          f"final actor: {summary['final_selection']['final_actor']}")
    return summary
