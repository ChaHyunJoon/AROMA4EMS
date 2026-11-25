"""Frozen development-cycle evaluations, separate from final held-out evaluation.

The six paper evaluation cycles are deliberately forbidden here. Default experiments use
the two constituents of the training route; this is in-distribution validation, not evidence
of unseen-cycle generalization. No checkpoint search or training is performed.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path

HELD_OUT_CYCLES = tuple("Standard_" + c for c in ("LA92", "NYCC", "UDDS", "WVUCITY", "WVUSUB", "HWFET"))
TRAINING_COMPONENTS = ("Standard_WLTC", "Standard_WVUINTER")


def validate_options(args):
    cycles = getattr(args, "development_cycles", [])
    if len(set(cycles)) != len(cycles):
        raise ValueError("Duplicate development cycles")
    if set(cycles) & set(HELD_OUT_CYCLES):
        raise ValueError("The six final evaluation cycles must not enter AROMA feedback or selection")
    if any(c not in TRAINING_COMPONENTS for c in cycles):
        raise ValueError("Development cycles must be Standard_WLTC and/or Standard_WVUINTER")
    if cycles and args.scenario_name != "Standard_WLTC_WVUINTER":
        raise ValueError("Training-component validation requires Standard_WLTC_WVUINTER training")
    cap = getattr(args, "development_max_regression", 0.)
    if not math.isfinite(cap) or cap < 0:
        raise ValueError("development_max_regression must be finite and nonnegative")
    if cycles and getattr(args, "obs_norm", None) != "fixed":
        raise ValueError("Development evaluation requires fixed training/evaluation observation scales")


def manifest_fields(args):
    validate_options(args)
    directory = Path(__file__).resolve().parents[2] / "project-data/standard_driving_cycles/mat-data"
    cycles = list(getattr(args, "development_cycles", []))
    return {"cycles": cycles, "cycle_hashes": {c: hashlib.sha256((directory / (c + ".mat")).read_bytes()).hexdigest()
                                               for c in cycles},
            "role": "training_constituents_development_not_held_out",
            "held_out_cycles": list(HELD_OUT_CYCLES),
            "fuel_basis": "paper_energy_explicit_initial_soc",
            "selection_basis": "total_operating_cost_with_baseline_fuel_battery_guards",
            "max_regression_fraction": getattr(args, "development_max_regression", 0.)}


def compare_development(candidate, champion, baseline, args):
    """Mean of per-cycle baseline-normalized total operating cost must beat the champion's; the worst
    per-cycle cost regression is capped.

    All requested cycles must be valid, and fuel and battery loss stay inside the training gate's
    baseline guard bands on every cycle (FC wear is priced in the cost, not capped). Missing evidence
    fails closed; invalid references never vanish from the mean. Existing training-cycle acceptance
    remains an additional requirement.
    """
    from operating_cost import operating_cost
    cycles = list(getattr(args, "development_cycles", []))
    if not cycles:
        return {"status": "disabled", "checks": {}}
    reports = [t.get("development_validation", {}) for t in (candidate, champion, baseline)]
    if any(r.get("cycles") != cycles or r.get("status") != "complete" for r in reports):
        return {"status": "fail", "reason": "missing_or_invalid_development_evidence", "checks": {}}
    if any(r.get("conditions_id") != reports[0].get("conditions_id") for r in reports[1:]):
        return {"status": "fail", "reason": "unpaired_development_conditions", "checks": {}}
    if not reports[0].get("conditions_id"):
        return {"status": "fail", "reason": "missing_development_conditions", "checks": {}}
    fuel_guard, batt_guard = float(args.cost_max_fuel_increase), float(args.cost_max_batt_increase)
    drift_guard = float(getattr(args, "cost_max_soc_drift", math.inf))
    ratios, reference_ratios, rows = [], [], {}
    for cycle in cycles:
        c, h, b = [r.get("results", {}).get(cycle, {}) for r in reports]
        valid = all(r.get("valid") is True and all(
            isinstance(r.get(k), (float, int)) and math.isfinite(r[k]) and r[k] >= 0
            for k in ("fuel_gkm", "fc_loss", "batt_loss")) for r in (c, h, b))
        costs = [operating_cost(r.get("fuel_gkm"), r.get("fc_loss"), r.get("batt_loss"), r.get("distance_km"))
                 for r in (c, h, b)] if valid else [None]
        if not valid or any(x is None for x in costs) or costs[2]["total_usd"] <= 0:
            return {"status": "fail", "reason": "invalid_development_cycle", "cycle": cycle, "checks": {}}
        ratio, ref = costs[0]["total_usd"] / costs[2]["total_usd"], costs[1]["total_usd"] / costs[2]["total_usd"]
        ratios.append(ratio)
        reference_ratios.append(ref)
        rows[cycle] = {"cost_ratio_vs_baseline": ratio, "champion_cost_ratio_vs_baseline": ref,
                       "total_usd": costs[0]["total_usd"], "fuel_ratio_vs_baseline": c["fuel_gkm"] / b["fuel_gkm"]
                       if b["fuel_gkm"] > 0 else None,
                       "fuel_within_guard": c["fuel_gkm"] <= b["fuel_gkm"] * (1 + fuel_guard),
                       "battery_within_guard": c["batt_loss"] <= b["batt_loss"] * (1 + batt_guard),
                       "charge_sustaining": _abs_drift(c) <= drift_guard}
    mean, ref_mean = sum(ratios) / len(ratios), sum(reference_ratios) / len(ratios)
    checks = {"mean_cost_improved": mean < ref_mean,
              "worst_cycle_within_cap": max(ratios) <= 1 + getattr(args, "development_max_regression", 0.),
              "fuel_within_guard": all(r["fuel_within_guard"] for r in rows.values()),
              "battery_within_guard": all(r["battery_within_guard"] for r in rows.values()),
              "charge_sustaining": all(r["charge_sustaining"] for r in rows.values())}
    return {"status": "pass" if all(checks.values()) else "fail", "checks": checks,
            "mean_cost_ratio": mean, "champion_mean_cost_ratio": ref_mean,
            "worst_cost_regression_fraction": max(ratios) - 1, "per_cycle": rows}


def _abs_drift(result):
    """|SOC_final - SOC_initial| of one development rollout; missing evidence fails the guard."""
    drift = (result.get("fuel_breakdown") or {}).get("soc_final_minus_initial")
    return abs(drift) if isinstance(drift, (float, int)) and math.isfinite(drift) else math.inf


class DevelopmentEvaluator:
    def __init__(self, args, root, manifest):
        self.args, self.root = args, Path(root)
        self.spec = manifest_fields(args)
        self.conditions_id = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()

    def __call__(self, trial):
        if not self.spec["cycles"] or trial.get("status") != "complete":
            return trial
        if manifest_fields(self.args) != self.spec:
            raise RuntimeError("Frozen development cycle inputs/settings changed")
        actor = Path(trial["chunk"]["model_dir"]) / "actor_iter001_ep399.pkl"
        actor_hash = hashlib.sha256(actor.read_bytes()).hexdigest()
        identity = {"conditions_id": self.conditions_id, "candidate_id": trial["candidate_id"],
                    "seed": trial["seed"], "actor_hash": actor_hash, **self.spec}
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
        directory = self.root / "development_evaluations" / key
        path = directory / "report.json"
        if path.exists():
            report = json.loads(path.read_text())
            if report.get("identity") != identity:
                raise RuntimeError("Development cache identity mismatch")
            if any(not (directory / c / "trajectory.npz").is_file() for c in self.spec["cycles"]):
                raise RuntimeError("Cached development trajectories are missing")
        else:
            from validated_workflow import write_json
            results = {c: self._rollout(trial, actor, c, directory / c) for c in self.spec["cycles"]}
            report = {"identity": identity, "conditions_id": self.conditions_id,
                      "status": "complete", "cycles": self.spec["cycles"], "results": results,
                      "role": self.spec["role"]}
            write_json(path, report)
        return {**trial, "development_validation": report}

    def _rollout(self, trial, actor_path, cycle, directory):
        import numpy as np
        import torch
        from candidate_validation import bind_reward
        from common.network import GaussianPolicy, BetaPolicy
        from common.paper_fuel_economy import paper_fuel_economy
        from env_ldri import make_env_ldri
        from policy_evidence import rollout_physics
        from power_constraints import shortfall_steps, summarize_power_violations
        from runner_ldri import RunnerLDRI

        args = copy.deepcopy(self.args)
        args.scenario_name, args.cuda, args.training_initial_states = cycle, False, "fixed"
        # Actor construction initializes parameters; preserve RNGs even though inference is deterministic.
        numpy_state = np.random.get_state()
        try:
            with torch.random.fork_rng(devices=[]):
                env, args = make_env_ldri(args, force_reload_agent=True)
                bind_reward(env, trial["reward_source"])
                actor = (GaussianPolicy if args.policy == "Gaussian" else BetaPolicy)(args).to("cpu")
                actor.load_state_dict(torch.load(actor_path, map_location="cpu", weights_only=True))
                actor.eval()
                data = RunnerLDRI._episode_info_template()
                state, actions = env.reset(), []
                with torch.inference_mode():
                    for step in range(args.episode_steps):
                        action = actor.deterministic_action(torch.from_numpy(state).unsqueeze(0)).numpy()[0]
                        state, _, done, info = env.step(action, step)
                        RunnerLDRI._append_info(data, info)
                        actions.append(float(action[0]))
                        if done:
                            break
        finally:
            np.random.set_state(numpy_state)
        n, dt = len(actions), float(env.agent.FCHEV.simtime)
        data.update(speed_m_s=env.speed_list[:n], acceleration_m_s2=env.acc_list[:n], policy_action=actions)
        physics = rollout_physics(data, soc0=args.soc0, soc_target=args.soc_target,
                                  soc_bounds=(args.soc_low, args.soc_high), dt_s=dt,
                                  fc_off_kw=env.agent.FCHEV.P_FC_off,
                                  ramp_threshold_kw_s=env.agent.FCHEV.P_FC_load_change_rate_thresh)
        power = summarize_power_violations(data, dt_s=dt)
        # Explicit reset SOC; do not use the first post-step SOC as the initial state.
        fuel = paper_fuel_economy({**data, "SOC": np.r_[args.soc0, data["SOC"]]}, dt_s=dt)
        soc = np.asarray(data["SOC"])
        in_bounds = float(np.mean((soc > args.soc_low) & (soc < args.soc_high)) * 100)
        # The shared reporting helper tolerates bad sensors; an adoption gate must not.
        sensors_valid = all(len(data[k]) == n and np.isfinite(data[k]).all()
                            for k in ("h2_fcs", "P_fce", "travel", "FCS_SOH", "SOH"))
        on = np.asarray(data["P_fce"]) > 0
        efficiency = np.asarray(data["fce_eff"])
        sensors_valid = sensors_valid and bool(np.all(np.isfinite(efficiency[on]) & (efficiency[on] > 0)))
        valid = bool(n == args.episode_steps and shortfall_steps(power) == {}
                     and in_bounds >= args.validation_min_in_bounds
                     and np.isfinite(soc).all() and np.all((soc >= 0) & (soc <= 1))
                     and sensors_valid and math.isfinite(fuel["equivalent_g_per_km"]))
        directory.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(directory / "trajectory.npz", **data, soc_initial=args.soc0, dt_s=dt)
        distance = fuel["drive_mileage_km"]
        safe = lambda x: float(x) if math.isfinite(x) else None
        return {"valid": valid, "steps": n, "expected_steps": args.episode_steps,
                "fuel_gkm": fuel["equivalent_g_per_km"] if valid else None, "distance_km": safe(distance),
                "fc_loss": safe(1 - data["FCS_SOH"][-1]), "batt_loss": safe(1 - data["SOH"][-1]),
                "soc_in_bounds": in_bounds, "physical_evidence": physics,
                "power_violations": power,
                "fuel_breakdown": {"raw_h2_gkm": safe(np.sum(data["h2_fcs"]) * dt / distance) if distance > 0 else None,
                                   "soc_correction_gkm": safe(fuel["batt_eq_h2_g"] / distance) if distance > 0 else None,
                                   "soc_final": safe(soc[-1]), "soc_final_minus_initial": safe(soc[-1] - args.soc0)}}


def brief_development(trial):
    report = trial.get("development_validation")
    if not report:
        return None
    compact = {k: report[k] for k in ("cycles", "conditions_id", "status", "role")}
    compact["results"] = {}
    for cycle, row in report["results"].items():
        compact["results"][cycle] = {k: v for k, v in row.items() if k != "physical_evidence"}
        evidence = row.get("physical_evidence", {})
        compact["results"][cycle]["physics"] = evidence.get("scalars", {})
        compact["results"][cycle]["regimes"] = evidence.get("regimes", {"available": False})
    return compact
