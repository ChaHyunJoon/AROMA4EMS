"""Reference table for the paper notebooks: DP plus the efficient-band rule (p_off 0.95 kW, min_off 90 s).

`metrics_rb_dp.csv` has the schema of 20261013_motor_efficiency_ramp10/metrics_rb_dp.csv: the DP rows are copied
unchanged, the Rule-based rows are recomputed with the same checks and definitions as that run's analyze.py from
the traces of 20261021_rb_efficient_band_poff095 (case poff0.95_minoff90). `comparison_with_dp_rb.csv` has the
schema of 20261017_seq_v3_catalog_seed41_61_81_iter1to6_ep399_four_cycles/comparison_with_dp_rb.csv (costs from
aroma/operating_cost.py), restricted to DP and Rule-based.

Usage from repository root: .venv/bin/python FCHEV-EMS/evaluation_runs/20261021_rb_efficient_band_minoff90/build.py
"""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import scipy.io as sio

OUT = Path(__file__).resolve().parent
PROJECT = (OUT.parents[2] / 'FCHEV-EMS')
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / 'aroma'))
from FCHEV_SOH import FCHEV_SOH
from common.paper_fuel_economy import compute_paper_style_fuel_economy, fc_operating_efficiency
from common.utils import get_driving_cycle, get_acc_limit
from operating_cost import operating_cost
from power_constraints import shortfall_steps, summarize_power_violations

CYCLES = ['UDDS', 'WVUSUB', 'LA92', 'HWFET']
DP_SOURCE = OUT.parent / '20261013_motor_efficiency_ramp10/metrics_rb_dp.csv'
OLD_COST = OUT.parent / '20261017_seq_v3_catalog_seed41_61_81_iter1to6_ep399_four_cycles/comparison_with_dp_rb.csv'
RB_CASE = OUT.parent / '20261021_rb_efficient_band_poff095/runs/poff0.95_minoff90'
RB_CONFIG = dict(policy='efficient_band', p_off_kw=0.95, min_off_s=90.0, ramp_limit_kw=10.0)


def rb_row(cycle, plant):
    speed = get_driving_cycle('Standard_' + cycle)
    acceleration = get_acc_limit(speed)
    expected = np.array([plant.run_motor(*plant.T_W_axle(v, a))[3] / 1000. for v, a in zip(speed, acceleration)])
    case = RB_CASE / f'Standard_{cycle}/efficient_band'
    path = case / 'episode_data/data_ep0.mat'
    data = sio.loadmat(path)
    a = lambda key: np.asarray(data[key], dtype=float).reshape(-1)
    for key in ['SOC', 'SOH', 'FCS_SOH', 'P_fc', 'P_dcdc', 'P_mot', 'battery_delivered_kw',
                'unserved_power_kw', 'power_failure_code', 'h2_fcs', 'travel']:
        assert len(a(key)) == len(speed) and np.isfinite(a(key)).all(), (cycle, key)
    np.testing.assert_allclose(a('P_mot'), expected, atol=1e-9)
    np.testing.assert_allclose(a('P_dcdc'), plant.run_fuel_cell(a('P_fc'))[0], atol=1e-9)
    residual = a('P_mot') - a('P_dcdc') - a('battery_delivered_kw')
    np.testing.assert_allclose(np.maximum(residual, 0), a('unserved_power_kw'), atol=1e-9)
    np.testing.assert_allclose(np.maximum(-residual, 0), a('unaccepted_power_kw'), atol=1e-9)
    np.testing.assert_allclose(a('travel')[-1], speed.sum(), atol=1e-8)
    dpfc = np.abs(np.diff(np.r_[0., a('P_fc')]))
    assert dpfc.max() <= 10. + 1e-6
    assert np.max(np.abs(a('battery_delivered_kw'))) <= 40. + 1e-6
    config = json.loads((case / 'rule_based_config.json').read_text())
    assert all(config[k] == v for k, v in RB_CONFIG.items()), config
    eff = fc_operating_efficiency(data)
    fuel = compute_paper_style_fuel_economy(a('travel'), a('h2_fcs'), np.r_[.6, a('SOC')], dt_s=1., fc_efficiency=eff)
    power = summarize_power_violations(data, 1.)
    failures = sum(shortfall_steps(power).values())
    starts = int(np.sum((a('P_fc') >= .95) & (np.r_[0., a('P_fc')[:-1]] < .95)))
    calibration = json.loads((case / 'soc_balance_calibration.json').read_text())
    assert abs(calibration['final_soc'] - a('SOC')[-1]) < 1e-10
    return dict(cycle=cycle, method='Rule-based', completed=True, valid_delivery=failures == 0,
                steps=len(speed), distance_km=fuel['drive_mileage_km'],
                equivalent_h2_g_per_km=fuel['equivalent_g_per_km'],
                raw_h2_g_per_km=float(a('h2_fcs').sum() / fuel['drive_mileage_km']),
                h2_g=float(a('h2_fcs').sum()), equivalent_h2_g=fuel['equivalent_fuel_g'],
                soc_correction_h2_g=fuel['batt_eq_h2_g'], initial_soc=.6,
                final_soc=float(a('SOC')[-1]), delta_soc=float(a('SOC')[-1] - .6),
                soc_min=float(min(.6, a('SOC').min())), soc_max=float(max(.6, a('SOC').max())),
                fc_soh_loss=float(1. - a('FCS_SOH')[-1]), battery_soh_loss=float(1. - a('SOH')[-1]),
                fc_starts=starts, load_change_events=int((dpfc > 9.5).sum()),
                max_abs_dPfc_kw=float(dpfc.max()), fc_efficiency=eff,
                delivery_failure_steps=failures, unserved_steps=int((a('unserved_power_kw') > 1e-6).sum()),
                unserved_peak_kw=power['unserved_peak_kw'], unserved_kwh=power['unserved_kwh'],
                unaccepted_kwh=float(a('unaccepted_power_kw').sum() / 3600.),
                motor_limit_steps=int((a('power_failure_code') == 2).sum()),
                soc_limit_steps=int((a('power_failure_code') == 1).sum()),
                max_dp_model_soc_error=None, rb_soc_balance_offset=calibration['soc_balance_offset'],
                trace_path=str(path))


def cost_rows(metrics):
    rows = []
    for r in metrics.itertuples():
        cost = operating_cost(float(r.equivalent_h2_g_per_km), float(r.fc_soh_loss), float(r.battery_soh_loss),
                              float(r.distance_km))
        rows.append(dict(cycle=r.cycle, method=r.method, distance_km=r.distance_km, total_usd=cost['total_usd'],
                         h2_usd=cost['h2_usd'], fc_usd=cost['fc_usd'], batt_usd=cost['batt_usd'],
                         delta_soc=r.delta_soc, cs_pass=abs(r.delta_soc) <= 0.05,
                         equivalent_h2_g_per_km=r.equivalent_h2_g_per_km, fc_soh_loss_pct=r.fc_soh_loss * 100.,
                         battery_soh_loss_pct=r.battery_soh_loss * 100., fc_starts=r.fc_starts,
                         valid_delivery=r.valid_delivery))
    return pd.DataFrame(rows)


def main():
    old = pd.read_csv(DP_SOURCE)
    plant = FCHEV_SOH()
    rb = pd.DataFrame([rb_row(c, plant) for c in CYCLES])
    metrics = pd.concat([old[old.method == 'DP'], rb[old.columns]], ignore_index=True)
    order = {c: i for i, c in enumerate(CYCLES)}
    metrics = metrics.sort_values(['cycle', 'method'], key=lambda s: s.map(order) if s.name == 'cycle' else s,
                                  kind='stable').reset_index(drop=True)
    metrics.to_csv(OUT / 'metrics_rb_dp.csv', index=False)
    costs = cost_rows(metrics)
    # the DP costs must equal those of the table the notebooks used before
    prev = pd.read_csv(OLD_COST).set_index(['cycle', 'method']).total_usd
    dp = costs[costs.method == 'DP'].set_index(['cycle', 'method']).total_usd
    np.testing.assert_allclose(dp.values, prev.loc[dp.index].values, rtol=1e-12)
    costs.to_csv(OUT / 'comparison_with_dp_rb.csv', index=False)
    (OUT / 'manifest.json').write_text(json.dumps(dict(
        description=__doc__.strip().splitlines()[0], rule_based=RB_CONFIG, rb_source=str(RB_CASE),
        dp_source=str(DP_SOURCE), cost_schema_source=str(OLD_COST)), indent=2) + '\n')
    pd.set_option('display.width', 220)
    print(costs[['cycle', 'method', 'equivalent_h2_g_per_km', 'delta_soc', 'fc_soh_loss_pct', 'battery_soh_loss_pct',
                 'fc_starts', 'total_usd', 'valid_delivery']].to_string(index=False))


if __name__ == '__main__':
    main()
