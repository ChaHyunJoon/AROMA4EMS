"""Regression coverage for deterministic champion fuel and diagnostic-only TAC."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

sys.path[:0] = [str(Path(__file__).resolve().parents[i]) for i in (1, 2)]
import feedback_parser as fp


def training_line(ep, h2=500):
    return (f"epi {ep}: travel 48.228km, SOC 0.4, FCS-SOH 0.999, Bat-SOH 0.999\n"
            f"epi {ep}: H2_100km {h2}g, objective_100km 1\n")


def eval_line(ep, fuel):
    row = dict(equivalent_g_per_km=fuel / 100.0, rollout_soc0=.6,
               fuel_metric_basis=fp.DETERMINISTIC_FUEL_BASIS)
    return f"epi {ep} [eval]: paper_fuel {json.dumps(row)}\n"


@pytest.fixture
def args():
    return NS(soc0=0.6, soc_target=0.6)


def test_legacy_time_mean_eval_requires_checkpoint_re_evaluation(tmp_path):
    path = tmp_path / "train_log.log"
    path.write_text(training_line(0) +
        "epi 0: P_fc min/mean/max 0/10/95 kW, P_batt_req min/mean/max -40/0/40 kW, fce_eff mean 0.2, fc_on 50%\n"
        "epi 0 [eval]: eval_r -1, H2_100km 1000g, H2eq_100km 999g (batt -1g), g/km 10, objective_100km 2\n"
        "epi 0 [eval]: SOC[min/mean/max]=0.5/0.6/0.7, final 0.65, in_bounds_rate=100%\n"
        "epi 0 [eval]: P_fc min/mean/max 0/10/95 kW, fce_eff mean 0.5, fc_on 50%\n")
    ep = fp.parse_train_log(path)[0]
    # Time-average efficiency cannot reproduce the notebook's energy mode.
    assert fp.deterministic_h2eq_corr_for_episode(ep) is None
