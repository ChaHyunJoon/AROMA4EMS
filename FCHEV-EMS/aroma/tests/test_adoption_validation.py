"""Acceptance regressions: better averages cannot hide failed charge sustaining.

v3 is seed-independent: every blocking floor is the run's own baseline plus a fixed
tolerance, and the absolute goals live in `targets` where they never block.
"""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import adoption_validation as av
import validated_workflow as vw


def policy_args(**over):
    base = dict(soc_target=.6, validation_min_improvement_gkm=0., validation_min_in_bounds=98.,
                validation_min_improvement_fraction=.03, validation_terminal_soc_error=.02,
                validation_scenario_soc_error=.02, validation_condition_soc_tolerance=.005,
                validation_condition_fuel_regression=.05, validation_unaccepted_energy_kwh=0.,
                validation_unaccepted_peak_kw=0., validation_unaccepted_peak_slack_kw=.5,
                validation_unaccepted_energy_slack_kwh=.001)
    base.update(over)
    return SimpleNamespace(**base)


_TRAJECTORY_ROOT = None


def _rollout_files(trial):
    """Zero-residual rollouts so residual_peaks() has real, hash-verified inputs."""
    import numpy as np
    from scenario_validation import file_hash
    global _TRAJECTORY_ROOT
    if _TRAJECTORY_ROOT is None:
        _TRAJECTORY_ROOT = Path(tempfile.mkdtemp(prefix="ldri_adoption_fixture_"))
    name = trial["candidate_id"]
    manifest = _TRAJECTORY_ROOT / f"{name}_manifest.json"
    manifest.write_text(json.dumps({"demand_kw": [0., 0.], "initial_ocv_v": 300.}))
    cycle = _TRAJECTORY_ROOT / f"{name}_cycle.npz"
    np.savez_compressed(cycle, pack_OCV=np.array([300., 300.]), I=np.array([0., 0.]),
                        P_batt_loss_kw=np.array([0., 0.]), P_dcdc=np.array([0., 0.]))
    scenario = _TRAJECTORY_ROOT / f"{name}_scenario.npz"
    np.savez_compressed(scenario, unaccepted_power_kw=np.array([0., 0.]))
    return (dict(trajectory_path=str(cycle), trajectory_hash=file_hash(cycle), manifest_path=str(manifest)),
            dict(trajectory_path=str(scenario), trajectory_hash=file_hash(scenario)))


# policy -----------------------------------------------------------------------

def test_policy_v3_has_no_seed_calibrated_absolute_limits():
    p = av.build_policy(policy_args())
    assert p["version"] == "post_training_acceptance_v3"
    assert "run baseline" in p["reference"]
    assert (p["condition_soc_error_increase"], p["unaccepted_peak_slack_kw"]) == (.005, .5)
    assert p["unaccepted_energy_slack_kwh"] == .001
    assert not any(k in p for k in ("terminal_soc_error", "scenario_soc_error", "unaccepted_peak_kw"))
    assert p["aspirational_targets"]["terminal_soc_error"] == .02
    assert p["aspirational_targets"]["unaccepted_peak_kw"] == 0.
    assert p["minimum_in_bounds_pct"] == 98.
    assert p["policy_hash"] != av.build_policy(policy_args(validation_unaccepted_peak_slack_kw=.4))["policy_hash"]


@pytest.mark.parametrize("field,value", [
    ("validation_unaccepted_peak_slack_kw", -1.), ("validation_unaccepted_peak_slack_kw", float("inf")),
    ("validation_unaccepted_energy_slack_kwh", float("nan")), ("validation_condition_soc_tolerance", 1.1),
    ("validation_min_improvement_fraction", -.01), ("validation_terminal_soc_error", -.01)])
def test_invalid_budgets_rejected(field, value):
    with pytest.raises(ValueError):
        av.build_policy(policy_args(**{field: value}))


# residual peaks ---------------------------------------------------------------


# acceptance -------------------------------------------------------------------


# seed independence ------------------------------------------------------------

def degrade(reports, side, **values):
    """Make one side of the evidence worse, the way a different seed's baseline is."""
    reports[side + "_segments"]["whole_cycle"].update(soc_final=values["soc_final"])
    for row in reports[side + "_scenarios"]["results"]:
        row["metrics"].update(soc_final=values["soc_final"],
                              final_target_error=values["final_target_error"],
                              mean_target_error=values["mean_target_error"],
                              recovery_half_mean_error=values["final_target_error"])


# low-SOC recovery -------------------------------------------------------------


# targets ----------------------------------------------------------------------


# fuel comparability -----------------------------------------------------------
