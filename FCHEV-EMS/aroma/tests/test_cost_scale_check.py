"""Extra reward terms are sized on the stored baseline rollout, not on LLM guesses of r0 or current."""
import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main_ldri_refine as main
import sequential_workflow as sw
from arguments_ldri import get_ldri_args
from candidate_validation import verify_cost_scale
from operating_cost import (USD_PER_BATT_LOSS, USD_PER_FC_LOSS, USD_PER_H2_G,
                            price_alignment)
from prompt_builder import extract_method_source
from reward_patcher import ensure_logging_contract

OBJECTIVE = "objective_cost = soc_cost + h2_cost + fcs_soh_cost + batt_soh_cost"


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


def ohmic(source, k):
    return source.replace(OBJECTIVE, f"{OBJECTIVE} + {k} * float(self.P_batt_loss_kw)")


def _rollout(path, steps=200, fc_start_steps=()):
    """Physically consistent enough for sizing: I ~ 30 A RMS, r0 0.28 ohm, h2 ~ 0.15 g per step."""
    t = np.arange(steps)
    current = 40 * np.sin(t / 7)
    loss = np.full(steps, 1e-9)
    loss[list(fc_start_steps)] += 1.96e-5  # an FC start: 1.96e-3 % SOH (FCHEV_SOH.run_FC_SOH)
    fc_soh = 1 - np.cumsum(loss)
    np.savez_compressed(path, SOC=0.6 + 0.01 * np.sin(t / 50), SOH=1 - 1e-8 * (t + 1), FCS_SOH=fc_soh,
                        dsoh=np.full(steps, 1e-8), fc_applied_kw=np.full(steps, 10.), I=current,
                        battery_delivered_kw=current * 0.247, P_batt_loss_kw=0.28 * current ** 2 / 1000,
                        P_mot=np.full(steps, 15.), h2_fcs=np.full(steps, .15), h2_batt=current * 0.247 * .0164,
                        h2_equal=.15 + current * 0.247 * .0164, speed_m_s=np.full(steps, 10.),
                        acceleration_m_s2=np.zeros(steps), travel=10. * (t + 1))
    return path


def fc_scaled(source, k):
    """Reprice FC wear by multiplying the logged term (the seed41 iter_002 shape)."""
    return source.replace("fcs_soh_cost = self.w_fc", f"fcs_soh_cost = {k} * self.w_fc")


def fc_extra(source, k):
    """The same objective written as an extra term on top of the unchanged logged term (the seed61 shape)."""
    return source.replace(OBJECTIVE, f"{OBJECTIVE} + {k - 1} * self.w_fc * float(self.dSOH_FCS)")


def test_baseline_reward_has_no_extra_cost_and_reports_its_price_deviation(args, source, tmp_path):
    result = verify_cost_scale(source, _rollout(tmp_path / "r.npz"), args)
    assert result["status"] == "pass" and result["extra_cost_mean_abs"] == pytest.approx(0, abs=1e-9)
    assert result["baseline_h2_cost_mean"] == pytest.approx(args.w_h2 * .15)
    # selection-priced cost per step: w_h2 * (h2 + g/unit FC * dSOH_FCS + g/unit batt * dSOH_batt)
    g_fc, g_batt = USD_PER_FC_LOSS / USD_PER_H2_G, USD_PER_BATT_LOSS / USD_PER_H2_G
    assert result["selection_cost_mean"] == pytest.approx(args.w_h2 * (.15 + g_fc * 1e-9 + g_batt * 1e-8), rel=1e-6)
    assert 0 < result["price_deviation_ratio"] < 0.2


def test_oversized_ohmic_term_is_rejected_with_measured_means(args, source, tmp_path):
    # 500 * mean(0.28 * I^2 / 1000) with I RMS ~28 A = ~112 per step vs operating cost ~1.6: the seed1 0929 failure
    result = verify_cost_scale(ohmic(source, 500.0), _rollout(tmp_path / "r.npz"), args)
    assert result["status"] == "fail" and result["price_deviation_ratio"] > 50
    assert "cost_scale" in result["reason"] and "selection-priced" in result["reason"]


def test_correctly_sized_ohmic_term_passes(args, source, tmp_path):
    result = verify_cost_scale(ohmic(source, 5.0), _rollout(tmp_path / "r.npz"), args)
    assert result["status"] == "pass" and 0 < result["price_deviation_ratio"] < 1


def test_ratio_limit_is_configurable_and_can_be_disabled(args, source, tmp_path):
    path = _rollout(tmp_path / "r.npz")
    args.cost_scale_max_ratio = 0.1
    assert verify_cost_scale(ohmic(source, 5.0), path, args)["status"] == "fail"
    args.cost_scale_max_ratio = 0
    assert verify_cost_scale(ohmic(source, 500.0), path, args)["status"] == "pass"


@pytest.mark.parametrize("k", [20.0, 5000.0])
def test_multiplier_and_extra_term_are_judged_by_one_yardstick(args, source, tmp_path, k):
    """2026-10-15: x20 on fcs_soh_cost passed (not 'extra') while the same repricing as an extra term failed."""
    path = _rollout(tmp_path / "r.npz", fc_start_steps=(0, 120))
    scaled, extra = verify_cost_scale(fc_scaled(source, k), path, args), verify_cost_scale(fc_extra(source, k), path, args)
    assert scaled["status"] == extra["status"]
    assert scaled["price_deviation_mean_abs"] == pytest.approx(extra["price_deviation_mean_abs"], rel=1e-9)
    assert scaled["status"] == ("pass" if k == 20.0 else "fail")


def test_repricing_fc_toward_the_selection_price_shrinks_the_deviation(args, source, tmp_path):
    path = _rollout(tmp_path / "r.npz", fc_start_steps=(0, 120))
    aligned = price_alignment(args.w_h2, args.w_fc, args.w_batt)["selection_over_reward_fc"]
    before = verify_cost_scale(source, path, args)["price_deviation_mean_abs"]
    after = verify_cost_scale(fc_scaled(source, aligned), path, args)["price_deviation_mean_abs"]
    assert after < before


def test_missing_rollout_is_unavailable_not_a_rejection(args, source, tmp_path):
    assert verify_cost_scale(ohmic(source, 500.0), tmp_path / "none.npz", args)["status"] == "unavailable"


def test_proposer_sees_measured_signals_and_repairs_an_oversized_term(args, source, tmp_path):
    traj = tmp_path / "trial" / "deterministic_rollouts"
    traj.mkdir(parents=True)
    _rollout(traj / "episode_00399.npz")
    baseline = {"status": "complete", "episodes": 400, "seed": 41, "candidate_id": "b", "reward_source": source,
                "trajectory_dir": str(traj), "metrics": {}, "final_metrics": {}}
    replies, prompts = [ohmic(source, 500.0), ohmic(source, 5.0)], []

    class Client:
        provider, model = "anthropic", "test"
        def complete(self, **kw):
            prompts.append(kw["prompt"])
            return f"```python\n{replies[len(prompts) - 1]}\n```"

    iter_dir = tmp_path / "iter"
    iter_dir.mkdir()
    result = sw.propose_reward(args=args, client=Client(), champion=baseline,
                               summary={"baseline": baseline, "iterations": []}, iter_dir=iter_dir)
    assert result == ohmic(source, 5.0)
    assert "MEASURED SIGNALS" in prompts[0] and "RMS" in prompts[0] and "ohm" in prompts[0]
    review = json.loads((iter_dir / "review.json").read_text())
    assert "cost_scale" in review["attempts"][0]["error"] and "cost_scale" in prompts[1]
    assert review["verification"]["cost_scale"]["status"] == "pass"


def test_oversized_soc_cost_is_not_exempt_from_scale(args, source, tmp_path):
    """2026-10-17 seed61: fc_surplus_charge summed into soc_cost at ~1770x h2 passed the deviation check."""
    path = _rollout(tmp_path / "r.npz")
    huge = source.replace("soc_cost = w_soc * soc_err", "soc_cost = w_soc * soc_err + 2500.0 * float(self.P_FCS)")
    result = verify_cost_scale(huge, path, args)
    assert result["status"] == "fail" and result["price_deviation_ratio"] <= 1 and result["soc_cost_ratio"] > 1
    assert "soc_cost averages" in result["reason"]
    assert verify_cost_scale(source, path, args)["soc_cost_ratio"] < 1
