"""Failure-learning attribution, controlled ablations and development selection regressions."""
import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main_ldri_refine as main
import sequential_workflow as sw
from arguments_ldri import get_ldri_args
from development_validation import HELD_OUT_CYCLES, compare_development, validate_options
from policy_evidence import operating_regimes
from prompt_builder import extract_method_source
from test_sequential_v2 import trial, _evaluator_factory


@pytest.fixture
def args(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["test"])
    a = get_ldri_args()
    a.seed, a.skip_patch, a.search_plan = 41, True, "fuel_diagnostics_v1"
    return a


@pytest.fixture
def source():
    return extract_method_source(main._resolve_input_path("agentEMS_val_base.py"), "EMS", "get_reward")


def test_regime_energies_noncontiguous_soc_and_missing_data():
    d = {"speed_m_s": [0, 25, 4, 5], "acceleration_m_s2": [0, .2, -.5, -.1],
         "P_mot": [0, 30, -5, -2], "P_fce": [1, 25, 3, 1], "h2_fcs": [.1, 1, .2, .1],
         "SOC": [.601, .599, .600, .601], "P_batt_req": [-1, 5, -8, -3],
         "P_batt_loss_kw": [.01, .1, .2, .02]}
    result = operating_regimes(d, soc0=.6, dt_s=1.)
    g = result["groups"]
    assert g["regeneration"]["fc_energy_kwh"] == pytest.approx(4/3600)
    assert g["regeneration"]["battery_throughput_kwh"] == pytest.approx(11/3600)
    assert g["regeneration"]["battery_ohmic_loss_kwh"] == pytest.approx(.22/3600)
    assert g["regeneration"]["soc_delta"] == pytest.approx(.002)
    assert g["high_speed"]["steps"] == 1
    assert g["low_load"]["steps"] == 1  # regeneration is not low positive demand
    json.dumps(result, allow_nan=False)
    del d["P_batt_loss_kw"]
    missing = operating_regimes(d, soc0=.6, dt_s=1.)
    assert not missing["available"] and "P_batt_loss_kw" in missing["missing_sensors"]


def test_rejected_candidate_physics_and_deltas_reach_next_proposal(args):
    base = sw._entry(trial(rid="base", physical_evidence={"scalars": {"battery_throughput_kwh": 4.}}), 1, None)
    bad = sw._brief(trial(11., rid="rejected", physical_evidence={
        "scalars": {"battery_throughput_kwh": 5.}, "regimes": {"available": True}}))
    s = {"iterations": [{"iteration": 2, "decision": "retain_champion", "candidate": bad}]}
    ctx = sw._context(args, base, base, base, "champion_improve", s)
    prev = ctx["previous_experiments"][0]
    assert prev["candidate"]["physics"]["battery_throughput_kwh"] == 5.
    assert prev["candidate"]["regimes"]["available"]
    assert prev["physics_delta_vs_baseline"] == {"reference_reward_id": "base",
        "candidate_reward_id": "rejected", "deltas": {"battery_throughput_kwh": 1.}}


def test_ablations_preserve_other_components_and_enforce_battery_range(args, source):
    battery = source.replace("batt_soh_cost = self.w_batt", "batt_soh_cost = 1.1 * self.w_batt")
    assert sw.verify_experiment(battery, source, args, 2)["status"] == "pass"
    for bad in (battery.replace("1.1 * self.w_batt", "1.5 * self.w_batt"),
                battery.replace("h2_cost = self.w_h2", "h2_cost = 1.2 * self.w_h2")):
        assert sw.verify_experiment(bad, source, args, 2)["status"] == "fail"
    soc = source.replace("self.w_soc * 10, self.w_soc)", "self.w_soc * 10, .9 * self.w_soc)")
    assert sw.verify_experiment(soc, source, args, 3)["status"] == "pass"
    assert sw.verify_experiment(battery, source, args, 3)["status"] == "fail"
    linear = source.replace("(np.abs(soc - self.SOC_target)) ** 2", "np.abs(soc - self.SOC_target)")
    # Keep the baseline's OOB formula, so only the anchor-shape check rejects it.
    linear = linear.replace("soc_cost = w_soc * soc_err", "soc_cost = w_soc * soc_err if soc_low < soc < soc_high else w_soc * soc_err ** 2")
    assert sw.verify_experiment(linear, source, args, 3)["status"] == "fail"


def test_development_gate_applies_to_full_search_and_final_selection(args, source, monkeypatch, tmp_path):
    args.search_plan, args.ldri_iterations = "archive", 3
    args.development_cycles = ["Standard_WLTC", "Standard_WVUINTER"]
    bad = source.replace("h2_cost = self.w_h2", "h2_cost = 1.1 * self.w_h2")
    good = source.replace("h2_cost = self.w_h2", "h2_cost = 1.2 * self.w_h2")
    class Development:
        def __init__(self, *a):
            pass
        def __call__(self, t):
            fuels = (10., 20.) if t["reward_source"] == source else (8., 21.) if t["reward_source"] == bad else (9., 19.)
            return {**t, "development_validation": dev_trial(args, fuels)["development_validation"]}
    monkeypatch.setattr(sw, "DevelopmentEvaluator", Development)
    monkeypatch.setattr(main, "_init_llm_client", lambda a: object())
    proposals, calls = iter([bad, good]), []
    result = sw.run_sequential_workflow(args, tmp_path, False, api=main,
        trial_factory=_evaluator_factory(tmp_path, lambda src, seed: (10 if src == source else 9, 1e-4, 2e-4), calls),
        proposal_fn=lambda **kw: next(proposals))
    assert [r["decision"] for r in result["iterations"]] == ["baseline_trained", "retain_champion", "replace_champion"]
    assert result["final_selection"]["verdict"]["development"]["status"] == "pass"
    assert result["final_selection"]["improvement_confirmed"]


def dev_trial(args, fuels=(10., 20.), **kwargs):
    t = trial(**kwargs)
    t["development_validation"] = {"status": "complete", "conditions_id": "same_dev",
        "role": "training_constituents_development_not_held_out", "cycles": args.development_cycles,
        "results": {c: {"valid": True, "fuel_gkm": f, "fc_loss": 1e-4, "batt_loss": 2e-4, "distance_km": 50.,
                        "fuel_breakdown": {"soc_final_minus_initial": 0.}}
                    for c, f in zip(args.development_cycles, fuels)}}
    return t


def test_development_gate_requires_charge_sustaining_on_every_cycle(args):
    args.development_cycles = ["Standard_WLTC", "Standard_WVUINTER"]
    b, c = dev_trial(args), dev_trial(args, (9., 19.), fuel=9.)
    c["development_validation"]["results"]["Standard_WVUINTER"]["fuel_breakdown"]["soc_final_minus_initial"] = -.08
    gate = sw.compare_policies(c, b, args)
    assert gate["status"] == "fail" and gate["development"]["checks"]["charge_sustaining"] is False
    assert gate["development"]["checks"]["mean_cost_improved"]


def test_development_mean_worst_cycle_and_degradation_gates(args):
    args.development_cycles = ["Standard_WLTC", "Standard_WVUINTER"]
    b = dev_trial(args)
    c = dev_trial(args, (9., 19.), fuel=9.)
    gate = sw.compare_policies(c, b, args)
    assert gate["status"] == "pass"
    cost = lambda f: .7 * f + 121600 * 1e-4 + 7581.6 * 2e-4   # 50 km, fc 1e-4, batt 2e-4
    assert gate["development"]["mean_cost_ratio"] == pytest.approx((cost(9) / cost(10) + cost(19) / cost(20)) / 2)
    # Average improves, but hiding a cost regression in the other cycle is forbidden.
    worse = dev_trial(args, (8., 21.), fuel=9.)
    assert sw.compare_policies(worse, b, args)["status"] == "fail"
    # Battery loss past the baseline guard on one cycle fails even though that cycle is cheaper.
    worse = copy.deepcopy(c)
    worse["development_validation"]["results"]["Standard_WLTC"]["batt_loss"] = 2.21e-4
    assert compare_development(worse, b, b, args)["status"] == "fail"
    worse["development_validation"]["results"]["Standard_WLTC"]["batt_loss"] = 2.19e-4
    assert compare_development(worse, b, b, args)["status"] == "pass"
    # A better development mean must not override the existing training gate.
    assert sw.compare_policies(dev_trial(args, (9., 19.), fuel=11.), b, args)["status"] == "fail"


@pytest.mark.parametrize("damage", ["missing", "invalid", "nan", "conditions"])
def test_development_incomplete_evidence_cannot_pass(args, damage):
    args.development_cycles = ["Standard_WLTC", "Standard_WVUINTER"]
    b, c = dev_trial(args), dev_trial(args, (9., 19.))
    r = c["development_validation"]
    if damage == "missing":
        del r["results"]["Standard_WLTC"]
    elif damage == "invalid":
        r["results"]["Standard_WLTC"]["valid"] = False
    elif damage == "nan":
        r["results"]["Standard_WLTC"]["fuel_gkm"] = float("nan")
    else:
        r["conditions_id"] = "other"
    assert compare_development(c, b, b, args)["status"] == "fail"


@pytest.mark.parametrize("cycle", HELD_OUT_CYCLES)
def test_final_evaluation_cycles_cannot_enter_development(args, cycle):
    args.development_cycles = [cycle]
    with pytest.raises(ValueError, match="final evaluation"):
        validate_options(args)


def test_legacy_resume_does_not_silently_adopt_new_training_defaults(args):
    main._apply_resume_run_config(args, {"seed": 41})
    assert args.obs_norm == "cycle" and args.unserved_cost_per_kw == 0.


def test_six_iteration_plan_starts_ablations_at_baseline(args, source, monkeypatch, tmp_path):
    args.ldri_iterations = 6
    battery = source.replace("batt_soh_cost = self.w_batt", "batt_soh_cost = 1.1 * self.w_batt")
    soc = source.replace("self.w_soc * 10, self.w_soc)", "self.w_soc * 10, .9 * self.w_soc)")
    later = [source.replace("h2_cost = self.w_h2", f"h2_cost = {scale} * self.w_h2") for scale in (1.1, 1.2, 1.3)]
    proposals = iter([battery, soc, *later])
    parents, calls = [], []
    def propose(**kw):
        parents.append(kw["edit_base"]["reward_source"])
        return next(proposals)
    monkeypatch.setattr(main, "_init_llm_client", lambda a: object())
    result = sw.run_sequential_workflow(args, tmp_path, False, api=main,
        trial_factory=_evaluator_factory(tmp_path, lambda src, seed: (10 if src == source else 9, 1e-4, 2e-4), calls),
        proposal_fn=propose)
    assert len(calls) == len(result["iterations"]) == 6
    assert parents[:2] == [source, source]
    assert result["workflow_status"] == "completed"
    assert result["iterations"][1]["experiment_plan"]["iteration"] == 2
