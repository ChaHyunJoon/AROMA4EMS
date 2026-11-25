"""Prompts and pre-training checks must describe and exercise the plant model that is actually executed."""
import json
import math
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main_ldri_refine as main
import sequential_workflow as sw
import candidate_validation as cv
import env_physics_facts as facts
from arguments_ldri import get_ldri_args
from FCHEV_SOH import FCHEV_SOH
from prompt_builder import extract_method_source
from reward_patcher import ensure_logging_contract

OBJECTIVE = "objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost"
# Finite on the old behavior grid (dSOH_FCS <= 7e-7), math range error on one FC start (1.96e-5).
OVERFLOW = OBJECTIVE + " + 1e-300 * math.exp(1e9 * float(self.dSOH_FCS))"


@pytest.fixture
def args(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["test"])
    args = get_ldri_args()
    args.seed, args.skip_patch, args.multi_agent_review = 41, True, False
    args.reward_term_catalog = False  # free-form fake proposals; the catalog is covered by test_reward_terms.py
    return args


@pytest.fixture
def source():
    src = ensure_logging_contract(extract_method_source(main._resolve_input_path("agentEMS_val_base.py"),
                                                        "EMS", "get_reward"), sw.REQUIRED_KEYS)
    assert OBJECTIVE in src
    return src


def _rollout(path, steps=200, start_step=None):
    t = np.arange(steps)
    current = 40 * np.sin(t / 7)
    loss = np.full(steps, 1e-9)
    if start_step is not None:
        loss[start_step] = 1.96e-5
    np.savez_compressed(path, SOC=0.6 + 0.01 * np.sin(t / 50), SOH=1 - 1e-8 * (t + 1), FCS_SOH=1 - np.cumsum(loss),
                        dsoh=np.full(steps, 1e-8), fc_applied_kw=np.full(steps, 10.), I=current,
                        battery_delivered_kw=current * 0.247, P_batt_loss_kw=0.28 * current ** 2 / 1000,
                        P_mot=np.full(steps, 15.), h2_fcs=np.full(steps, .15), h2_batt=current * 0.247 * .0164,
                        h2_equal=.15 + current * 0.247 * .0164, speed_m_s=np.full(steps, 10.),
                        acceleration_m_s2=np.zeros(steps), travel=10. * (t + 1))
    return path


def _baseline(tmp_path, source, **rollout):
    traj = tmp_path / "trial" / "deterministic_rollouts"
    traj.mkdir(parents=True)
    _rollout(traj / "episode_00399.npz", **rollout)
    return {"status": "complete", "episodes": 400, "seed": 41, "candidate_id": "b", "reward_source": source,
            "trajectory_dir": str(traj), "metrics": {}, "final_metrics": {}}


# ---- 1. the adoption cap is total fc_loss, not the start count ---------------------------------

def test_fc_note_names_total_fc_loss_as_the_cap():
    entry = {"reward_id": "b", "final_ep399": {"fc_loss": 2e-4},
             "physics": {"fc_start_stop_count": 5, "fc_start_stop_soh_loss": 9.8e-5,
                         "fc_low_power_count": 100, "fc_low_power_soh_loss": 3.5e-7}}
    note = sw._fc_degradation_note(entry)
    assert "TOTAL fc_loss" in note and "fc_start_stop_count is a diagnostic" in note
    assert "fc_start_stop_count against the baseline cap" not in note


def test_gate_passes_more_starts_when_total_fc_loss_is_lower(args):
    def trial(fuel, fc, starts):
        return {"status": "complete", "episodes": 400, "seed": 41, "conditions_id": "same",
                "candidate_id": f"{fuel}-{starts}", "reward_source": "src",
                "final_metrics": {"episode": 399, "fuel_metric_basis": sw.DETERMINISTIC_FUEL_BASIS,
                                  "fuel_gkm": fuel, "fc_loss": fc, "batt_loss": 2e-4, "soc_in_bounds": 100.,
                                  "soc_min": .5, "soc_max": .7,
                                  "power_violations": {"trace_available": True, "steps_by_reason": {}},
                              "paper_fuel": {"drive_mileage_km": 50.},
                                  "physical_evidence": {"scalars": {"fc_start_stop_count": starts,
                                                                    "soc_final_minus_initial": 0.}}}}
    assert sw.compare_policies(trial(9., 1.9e-4, 8), trial(10., 2e-4, 5), args)["status"] == "pass"


# ---- 2. the model assumptions reach every stage, and match the executed plant ------------------

def test_plant_note_matches_the_loaded_model():
    plant = FCHEV_SOH()
    note = facts.render_plant_model_note(4.275e6)
    plant.P_FC_old = 0.
    start, _ = plant.run_FC_SOH(7.)
    assert f"{start:.3g} = {4.275e6 * start:.4g} per start" in note
    assert "ASSUMED equal" in note and "NOT projected" in note
    # Driveline factors quoted in the note are the ones T_W_axle applies.
    speed, radius, gear, mass = 10., 0.355, 7.98, 1900.
    road = radius / gear * (mass * 9.81 * 0.012 + 0.5 * 1.226 * 2.5 * 0.32 * speed ** 2)
    inertia = radius / gear * mass
    assert plant.T_W_axle(speed, 1.)[0] == pytest.approx((road + inertia) / 0.98)
    assert plant.T_W_axle(speed, -1.)[0] == pytest.approx((road - inertia) * 0.95)
    # Shaft power / eta when motoring, * eta when regenerating, equal eta at equal speed and |torque|.
    rpm = plant.T_W_axle(speed, 0.)[1]
    _, _, eta_drive, p_drive = plant.run_motor(50., rpm, 0.)
    _, _, eta_regen, p_regen = plant.run_motor(-50., rpm, 0.)
    shaft = 2 * math.pi / 60 * 50. * rpm
    assert eta_drive == eta_regen
    assert p_drive == pytest.approx(shaft / eta_drive) and p_regen == pytest.approx(-shaft * eta_regen)


def test_every_stage_prompt_carries_the_plant_model(args, source, tmp_path):
    args.multi_agent_review = True
    baseline = _baseline(tmp_path, source)
    prompts = []

    class Client:
        provider, model = "anthropic", "test"
        def complete(self, **kw):
            prompts.append(kw["prompt"])
            reply = source.replace("h2_cost = self.w_h2", "h2_cost = 1.3 * self.w_h2")
            if "Mediate" in kw["prompt"]:
                return '```json\n{"term_ratio": {"h2_cost": 1.3}, "extra_terms": "unchanged"}\n```'
            return f"```python\n{reply}\n```" if "Generate ONE" in kw["prompt"] else "hyp"

    iter_dir = tmp_path / "iter"
    iter_dir.mkdir()
    assert sw.propose_reward(args=args, client=Client(), champion=baseline,
                             summary={"baseline": baseline, "iterations": []}, iter_dir=iter_dir)
    assert len(prompts) == 6
    for prompt in prompts:
        assert "PLANT MODEL" in prompt and "ASSUMED equal" in prompt and "per start" in prompt


def test_unused_physics_block_describes_the_clamp_model():
    block = facts.render_env_physics_block()
    assert "projected onto the feasible" not in block and "Infeasible supply terminates" not in block
    assert "NOT projected" in block and "a power shortfall does not" in block


# ---- 3. probes cover real FC start magnitudes; replay errors go to repair ----------------------

def test_event_probes_come_from_the_model_and_exceed_the_grid():
    events = {c["event"]: c["dSOH_FCS"] for c in facts.fc_event_cases()}
    assert events["start"] == pytest.approx(1.96e-5)
    assert events["start_load_change"] == pytest.approx(1.96e-5 + 5.93e-7)
    assert events["off"] == 0 and events["stop"] == pytest.approx(5.93e-7)
    from multi_agent_review import _reward_behavior_grid
    assert max(c["dSOH_FCS"] for c in _reward_behavior_grid()) < events["start"]


def test_reward_that_overflows_on_a_start_fails_verification(args, source):
    result = cv.verify_candidate(source.replace(OBJECTIVE, OVERFLOW), args)
    assert result["status"] == "fail" and result["checks"]["finite_reward"] == "fail"
    assert result["evidence"][1]["event"].startswith("start")


def test_replay_overflow_is_a_repairable_failure_not_a_crash(args, source, tmp_path, monkeypatch):
    # Probes disabled: the stored rollout is then the only place the start magnitude appears.
    monkeypatch.setattr(cv, "fc_event_probes", lambda: [])
    baseline = _baseline(tmp_path, source, start_step=50)
    bad = source.replace(OBJECTIVE, OVERFLOW)
    measured = cv.verify_cost_scale(bad, sw._baseline_rollout(baseline), args)
    assert measured["status"] == "fail" and "step 50" in measured["reason"] and "dSOH_FCS" in measured["reason"]
    good = source.replace("h2_cost = self.w_h2", "h2_cost = 1.3 * self.w_h2")
    replies, prompts = [bad, good], []

    class Client:
        provider, model = "anthropic", "test"
        def complete(self, **kw):
            prompts.append(kw["prompt"])
            return f"```python\n{replies[len(prompts) - 1]}\n```"

    iter_dir = tmp_path / "iter"
    iter_dir.mkdir()
    assert sw.propose_reward(args=args, client=Client(), champion=baseline,
                             summary={"baseline": baseline, "iterations": []}, iter_dir=iter_dir) == good
    assert "finite_reward" in json.loads((iter_dir / "review.json").read_text())["attempts"][0]["error"]
    assert "finite_reward" in prompts[1]


def test_battery_probes_come_from_the_model_and_exceed_the_grid(args, source):
    from Battery import CellModel1
    from multi_agent_review import _reward_behavior_grid
    cases = {c["event"]: c for c in facts.battery_event_cases()}
    battery = CellModel1()
    _, dsoh, current, _, _ = battery.run_battery(30_000., [0.6, 1.0, float(battery.ocv_func(0.6))])
    case = cases["battery_+30kW_soc0.60"]
    assert case["dSOH_batt"] == dsoh and case["I_batt"] == current and case["P_batt"] == 30_000.
    assert case["P_batt_loss_kw"] == pytest.approx(float(battery.r0_func(0.6)) * current ** 2 / 1000)
    assert cases["battery_+0kW_soc0.60"]["dSOH_batt"] == 0
    in_band = max(c["dSOH_batt"] for c in cases.values() if 0.4 <= c["SOC"] <= 0.8)
    assert in_band > 5 * max(c["dSOH_batt"] for c in _reward_behavior_grid())
    # The probe state uses the model's current and ohmic loss, not the grid's stand-ins.
    state = cv._probe_state(cv.battery_event_probes()[5], args)
    assert state.I_batt == cv.battery_event_probes()[5]["I_batt"]
    # Finite on the grid's dSOH_batt (<= 4e-7), overflows at the 30 kW magnitude (~1.6e-6).
    bad = source.replace(OBJECTIVE, OBJECTIVE + " + 1e-300 * math.exp(1e9 * float(self.dSOH_batt))")
    result = cv.verify_candidate(bad, args)
    assert result["status"] == "fail" and result["evidence"][1]["event"].startswith("battery_")


# ---- 4. an imported baseline is sized from its current-plant rollout, not its old log ----------

def test_imported_baseline_costs_come_from_the_replayed_rollout(args, source, tmp_path):
    baseline = _baseline(tmp_path, source)
    log = tmp_path / "train_log.log"
    log.write_text("epi 399: mean_cost soc 111.000, h2 222.000, fcs 333.000, batt 444.000, obj 1110.000\n")
    baseline["chunk"] = {"log_path": str(log), "end_episode": 399}
    fresh = sw._cost_scale_note(baseline, args)
    assert "h2 222.000" in fresh and "[current-plant replay]" not in fresh
    baseline["baseline_provenance"] = {"comparison_basis": "historical_baseline_reevaluated_in_current_environment"}
    imported = sw._cost_scale_note(baseline, args)
    assert "222.000" not in imported and "[current-plant replay]" in imported
    assert "h2 %.3f" % (args.w_h2 * .15) in imported
    assert "IMPORTED BASELINE" in sw._imported_baseline_note(baseline)
    assert sw._imported_baseline_note({"reward_source": source}) == ""
