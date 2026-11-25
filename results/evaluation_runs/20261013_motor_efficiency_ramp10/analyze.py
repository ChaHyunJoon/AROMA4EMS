"""Validate eight fresh rollouts and compare with the previous four-cycle run."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import scipy.io as sio

OUT = Path(__file__).resolve().parent
PROJECT = (OUT.parents[2] / 'FCHEV-EMS')
sys.path.insert(0, str(PROJECT))
from FCHEV_SOH import FCHEV_SOH
from common.paper_fuel_economy import compute_paper_style_fuel_economy, fc_operating_efficiency
from common.utils import get_driving_cycle, get_acc_limit
from power_constraints import shortfall_steps, summarize_power_violations

CYCLES = ['UDDS', 'WVUSUB', 'LA92', 'HWFET']


def main():
    completion = json.loads((OUT / 'completion.json').read_text())
    assert len(completion['cases']) == 8 and completion['source_hashes_unchanged']
    plant = FCHEV_SOH()
    rows, events, traces = [], [], {}
    for cycle in CYCLES:
        speed = get_driving_cycle('Standard_' + cycle)
        acceleration = get_acc_limit(speed)
        expected = np.array([plant.run_motor(*plant.T_W_axle(v, a))[3] / 1000.
                             for v, a in zip(speed, acceleration)])
        for method in ['DP', 'Rule-based']:
            case = (OUT / f'Standard_{cycle}/DP_dR10_reoptimized' if method == 'DP' else
                    OUT / f'rule_based_ramp10/Standard_{cycle}/rule_based_controller')
            path = case / 'episode_data/data_ep0.mat'
            data = sio.loadmat(path)
            # The existing DP logger omits P_dcdc. Its pre-clamp battery request
            # independently retains bus output as P_mot - battery_requested_kw.
            if 'P_dcdc' not in data:
                data['P_dcdc'] = data['P_mot'] - data['battery_requested_kw']
            a = lambda key: np.asarray(data[key], dtype=float).reshape(-1)
            for key in ['SOC', 'SOH', 'FCS_SOH', 'P_fc', 'P_dcdc', 'P_mot', 'battery_delivered_kw',
                        'unserved_power_kw', 'power_failure_code', 'h2_fcs', 'travel']:
                assert len(a(key)) == len(speed) and np.isfinite(a(key)).all(), (cycle, method, key)
            np.testing.assert_allclose(a('P_mot'), expected, atol=1e-9)
            np.testing.assert_allclose(a('P_dcdc'), plant.run_fuel_cell(a('P_fc'))[0], atol=1e-9)
            residual = a('P_mot') - a('P_dcdc') - a('battery_delivered_kw')
            np.testing.assert_allclose(np.maximum(residual, 0), a('unserved_power_kw'), atol=1e-9)
            np.testing.assert_allclose(np.maximum(-residual, 0), a('unaccepted_power_kw'), atol=1e-9)
            np.testing.assert_allclose(a('travel')[-1], speed.sum(), atol=1e-8)
            dpfc = np.abs(np.diff(np.r_[0., a('P_fc')]))
            assert dpfc.max() <= 10. + 1e-6
            assert np.max(np.abs(a('battery_delivered_kw'))) <= 40. + 1e-6
            eff = fc_operating_efficiency(data)
            fuel = compute_paper_style_fuel_economy(a('travel'), a('h2_fcs'), np.r_[.6, a('SOC')],
                                                   dt_s=1., fc_efficiency=eff)
            power = summarize_power_violations(data, 1.)
            failures = sum(shortfall_steps(power).values())
            starts = int(np.sum((a('P_fc') >= .95) & (np.r_[0., a('P_fc')[:-1]] < .95)))
            row = dict(cycle=cycle, method=method, completed=True, valid_delivery=failures==0,
                       steps=len(speed), distance_km=fuel['drive_mileage_km'],
                       equivalent_h2_g_per_km=fuel['equivalent_g_per_km'],
                       raw_h2_g_per_km=float(a('h2_fcs').sum()/fuel['drive_mileage_km']),
                       h2_g=float(a('h2_fcs').sum()), equivalent_h2_g=fuel['equivalent_fuel_g'],
                       soc_correction_h2_g=fuel['batt_eq_h2_g'], initial_soc=.6,
                       final_soc=float(a('SOC')[-1]), delta_soc=float(a('SOC')[-1]-.6),
                       soc_min=float(min(.6,a('SOC').min())), soc_max=float(max(.6,a('SOC').max())),
                       fc_soh_loss=float(1.-a('FCS_SOH')[-1]), battery_soh_loss=float(1.-a('SOH')[-1]),
                       fc_starts=starts, load_change_events=int((dpfc>9.5).sum()),
                       max_abs_dPfc_kw=float(dpfc.max()), fc_efficiency=eff,
                       delivery_failure_steps=failures, unserved_steps=int((a('unserved_power_kw')>1e-6).sum()),
                       unserved_peak_kw=power['unserved_peak_kw'], unserved_kwh=power['unserved_kwh'],
                       unaccepted_kwh=float(a('unaccepted_power_kw').sum()/3600.),
                       motor_limit_steps=int((a('power_failure_code')==2).sum()),
                       soc_limit_steps=int((a('power_failure_code')==1).sum()),
                       max_dp_model_soc_error=None, rb_soc_balance_offset=None, trace_path=str(path))
            if method == 'DP':
                diag = json.loads((case / 'source.json').read_text())
                row['max_dp_model_soc_error'] = diag['max_model_soc_error']
                assert diag['max_model_soc_error'] < 1e-10
                assert abs(row['delta_soc']) < 1e-4
            else:
                calibration = json.loads((case / 'soc_balance_calibration.json').read_text())
                row['rb_soc_balance_offset'] = calibration['soc_balance_offset']
                assert abs(calibration['final_soc'] - row['final_soc']) < 1e-10
            for step in np.flatnonzero(a('unserved_power_kw') > 1e-6):
                events.append(dict(cycle=cycle, method=method, step=int(step),
                                   speed_mps=float(speed[step]), acceleration=float(acceleration[step]),
                                   **{k:float(a(k)[step]) for k in ['SOC','P_fc','P_dcdc','P_mot',
                                        'battery_requested_kw','battery_delivered_kw','unserved_power_kw']}))
            rows.append(row)
            traces[(cycle, method)] = data
            (case / 'metrics.json').write_text(json.dumps(dict(metrics=row, power=power), indent=2) + '\n')
    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / 'metrics_rb_dp.csv', index=False)
    reference = pd.read_csv(OUT.parent / '20261013_fc_startstop_per_cycle/metrics_rb_dp.csv')
    fields = ['equivalent_h2_g_per_km','final_soc','fc_soh_loss','battery_soh_loss',
              'delivery_failure_steps','unserved_peak_kw','unserved_kwh','fc_starts']
    comparison = reference[['cycle','method',*fields]].merge(metrics[['cycle','method',*fields]],
                    on=['cycle','method'], suffixes=('_old','_new'), validate='one_to_one')
    comparison['equivalent_h2_change_pct'] = (comparison.equivalent_h2_g_per_km_new /
                                               comparison.equivalent_h2_g_per_km_old - 1.) * 100.
    comparison.to_csv(OUT / 'comparison_before_after.csv', index=False)
    pd.DataFrame(events, columns=['cycle','method','step','speed_mps','acceleration','SOC','P_fc','P_dcdc',
                                'P_mot','battery_requested_kw','battery_delivered_kw','unserved_power_kw']).to_csv(
                                    OUT / 'shortfall_events.csv', index=False)
    summary = dict(cases=len(rows), all_completed=True,
                   checks=['Expected cycle length and distance', 'Current motor demand and DC/DC output',
                           'Signed bus power residual', '10 kW/s FC ramp and 40 kW battery rating',
                           'DP model/plant SOC parity', 'Rule calibration/rollout SOC parity'],
                   valid_delivery_cases=int(metrics.valid_delivery.sum()),
                   failed_delivery_cases=metrics.loc[~metrics.valid_delivery,['cycle','method','unserved_steps','unserved_peak_kw']].to_dict('records'),
                   metric_note='Equivalent hydrogen includes initial-to-final SOC correction. A delivery-failing rollout is diagnostic and cannot establish feasible fuel economy.',
                   dp_bus_reconstruction='The original DP trace omits P_dcdc; reconstructed as P_mot - battery_requested_kw, then checked against the FC/DC-DC map.',
                   results=rows)
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(metrics[['cycle','method','equivalent_h2_g_per_km','final_soc','unserved_steps','unserved_peak_kw','max_abs_dPfc_kw']].to_string(index=False))
    print('\nPrevious -> current fuel comparison:')
    print(comparison[['cycle','method','equivalent_h2_g_per_km_old','equivalent_h2_g_per_km_new','equivalent_h2_change_pct']].to_string(index=False))
    plot(traces)


def plot(traces):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    colors = {'DP':'#1673b1','Rule-based':'#d86f22'}
    fig, axes = plt.subplots(4, 2, figsize=(13, 12), constrained_layout=True)
    for row, cycle in enumerate(CYCLES):
        for method in ['DP','Rule-based']:
            d = traces[(cycle,method)]
            soc = np.r_[.6, np.asarray(d['SOC']).ravel()]
            axes[row,0].plot(np.arange(len(soc)), soc, label=method, color=colors[method], lw=1.1)
            u = np.asarray(d['unserved_power_kw']).ravel()
            axes[row,1].plot(np.arange(len(u)),u,label=method,color=colors[method],lw=1.1)
        axes[row,0].axhline(.6,ls='--',color='gray',lw=.8)
        axes[row,0].set(title=f'{cycle}: SOC',ylabel='SOC')
        axes[row,1].set(title=f'{cycle}: unmet traction demand',ylabel='Shortfall (kW)',ylim=(-.1,None))
        for ax in axes[row]:
            ax.set_xlabel('Time (s)')
            ax.grid(alpha=.2)
    axes[0,0].legend(loc='best')
    axes[0,1].legend(loc='best')
    fig.suptitle('Current motor/driveline losses | FC ramp 10 kW/s | Re-solved DP and recalibrated rule baseline')
    fig.savefig(OUT / 'soc_and_power_shortfall.png', dpi=160)
    fig.savefig(OUT / 'soc_and_power_shortfall.pdf')
    plt.close(fig)


if __name__ == '__main__':
    main()
