import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from arguments_ldri import get_ldri_args
from baseline_import import inspect_learning_rates
from policy_evidence import rollout_physics, summarize_physics
import validated_workflow as vw


@pytest.fixture
def args(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["test"])
    return get_ldri_args()


def test_baseline_lr_defaults_and_import_mismatch(args):
    old = """critic warmup-restart cosine learning rate: 3.0e-04 -> 1.0e-04
actor warmup-restart cosine learning rate: 1.0e-04 -> 2.0e-05
alpha warmup-restart cosine learning rate: 2.0e-04 -> 5.0e-05
lr warmup-restart cycles: 4
lr warmup ratio: 0.10 of cosine cycle
max_episodes: 500
"""
    # A historical 500-episode schedule must be explicit with the current 400 budget.
    with pytest.raises(ValueError, match="lr_schedule_episodes"):
        inspect_learning_rates({}, old, args)
    args.lr_schedule_episodes = 500
    recorded = inspect_learning_rates({}, old, args)
    assert recorded["lr_schedule_episodes"] == 500
    for key in ("lr_critic", "lr_actor", "lr_alpha", "lr_restart_cycles"):
        altered = SimpleNamespace(**vars(args))
        setattr(altered, key, getattr(altered, key) * 2)
        with pytest.raises(ValueError, match=key):
            inspect_learning_rates({}, old, altered)
    assert inspect_learning_rates({}, "no historical metadata", args) == {}


def test_measured_counts_ramps_soc_energy_and_missing_sensors():
    data = {"SOC": [.6, .39, .82], "P_fc": [0, 9.5, 19.1], "P_batt_req": [3.6, -7.2, 0],
            "d_s_s": [0, 1.96, 0], "d_low": [0, 0, 0], "d_high": [0, 0, 0], "d_l_c": [0, 0, 5.93],
            "h2_fcs": [.0, .1, .2]}
    result = rollout_physics(data, soc0=.6, soc_target=.6, soc_bounds=(.4, .8), dt_s=1,
                             fc_off_kw=.95, ramp_threshold_kw_s=9.5)
    s = result["scalars"]
    assert s["soc_final"] == .82
    assert s["soc_below_steps"] == s["soc_above_steps"] == 1
    assert s["fc_ramp_exceed_steps"] == s["fc_load_change_count"] == 1
    assert s["fc_start_stop_count"] == 1  # count events, not sum of degradation coefficients
    assert s["fc_start_stop_soh_loss"] == pytest.approx(1.96e-5)  # per start, not per second
    assert s["fc_load_change_soh_loss"] == pytest.approx(5.93e-7)
    assert s["battery_charge_kwh"] == pytest.approx(.002)
    assert s["battery_discharge_kwh"] == pytest.approx(.001)
    assert "I" in result["missing_sensors"]
    assert "battery_current_a_mean" not in s
    assert result["dominant_fc_degradation"] == "start_stop"
    assert result["witness_steps"][-1]["step"] == 2
    summary = summarize_physics([{"episode": 90, "physical_evidence": result}, {"episode": 91}])
    assert summary["available_count"] == 1
    assert summary["scalars"]["soc_final"]["count"] == 1
    json.dumps(result, allow_nan=False)
