"""Sweep the efficient-band rule (Liu et al. 2020) at p_off = 0.95 kW (the plant's FC-off level) over minimum off time.

Every case is `rule_based_eval.py --rb_policy efficient_band`, SOC-balanced per cycle,
under the plant conditions of 20261013_motor_efficiency_ramp10 (ramp 10 kW/s, w_soc 500),
so the rows are comparable with the DP and Fig. 11 rule-based rows of that run.

Usage from repository root: .venv/bin/python FCHEV-EMS/evaluation_runs/20261021_rb_efficient_band_poff095/run.py
Existing experiment outputs are never overwritten; `--analyze_only` recomputes the tables.
"""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import argparse
import hashlib
import itertools
import json
import os
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd
import scipy.io as sio

OUT = Path(__file__).resolve().parent
PROJECT = (OUT.parents[2] / 'FCHEV-EMS')
ROOT = PROJECT.parent
sys.path.insert(0, str(PROJECT))
from common.paper_fuel_economy import compute_paper_style_fuel_economy, fc_operating_efficiency
from power_constraints import shortfall_steps, summarize_power_violations

REFERENCE = OUT.parent / '20261013_motor_efficiency_ramp10'
CYCLES = ['UDDS', 'WVUSUB', 'LA92', 'HWFET']
P_OFF_KW = [0.95]                               # off only when demand is below the plant's FC-off level
MIN_OFF_S = [0, 15, 30, 45, 60, 75, 90, 120, 150, 180, 240, 300]
# Operating-cost constants of visualization/paper_figs_multi_seed.ipynb (mean of per-cycle per-km rates)
H2_PRICE, FC_COST, BATT_COST, FC_EOL_LOSS, BATT_EOL_LOSS = 7.0, 80.0 * 76.0, 1.56 * 486.0, 0.10, 0.20
SOURCES = ['FCHEV_SOH.py', 'Battery.py', 'power_constraints.py', 'agentEMS_pure_h2_consumption.py',
           'rule_based_eval.py', 'rule_based_calibrate.py', 'rule_based_controller.py',
           'common/arguments.py', 'common/env.py', 'common/utils.py', 'common/paper_fuel_economy.py']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def case_name(p_off, min_off):
    return f'poff{p_off:g}_minoff{min_off:g}'


def command(cycle, p_off, min_off):
    return [sys.executable, '-u', 'rule_based_eval.py', '--scenario_name', f'Standard_{cycle}',
            '--w_soc', '500', '--ramp_limit_kw', '10', '--soc0', '0.6', '--soc_target', '0.6',
            '--MODE', 'CS', '--gamma', '0.995', '--rb_auto_soc_balance', '1',
            '--rb_policy', 'efficient_band', '--rb_p_off_kw', str(p_off), '--rb_min_off_s', str(min_off),
            '--rb_save_dir', str(OUT / 'runs' / case_name(p_off, min_off)), '--rb_name', 'efficient_band']


def run_case(cycle, p_off, min_off):
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    log = OUT / 'logs' / f'{case_name(p_off, min_off)}_{cycle}.log'
    with log.open('w') as f:
        result = subprocess.run(command(cycle, p_off, min_off), cwd=PROJECT, env=env,
                                stdout=f, stderr=subprocess.STDOUT)
    return dict(cycle=cycle, p_off_kw=p_off, min_off_s=min_off, returncode=result.returncode)


def trace_metrics(path, cycle):
    """Same definitions as 20261013_motor_efficiency_ramp10/analyze.py."""
    data = sio.loadmat(path)
    a = lambda key: np.asarray(data[key], dtype=float).reshape(-1)
    p_fc = a('P_fc')
    dpfc = np.abs(np.diff(np.r_[0., p_fc]))
    eff = fc_operating_efficiency(data)
    fuel = compute_paper_style_fuel_economy(a('travel'), a('h2_fcs'), np.r_[.6, a('SOC')],
                                           dt_s=1., fc_efficiency=eff)
    power = summarize_power_violations(data, 1.)
    on = p_fc >= .95
    starts = int(np.sum(on & ~np.r_[False, on[:-1]]))
    # off stretches between two FC-on steps; the minimum off time should bound these
    edges = np.flatnonzero(np.diff(on.astype(int)))
    off_runs = [e2 - e1 for e1, e2 in zip(edges[:-1], edges[1:]) if not on[e1 + 1]]
    return dict(cycle=cycle, distance_km=fuel['drive_mileage_km'],
                equivalent_h2_g_per_km=fuel['equivalent_g_per_km'],
                raw_h2_g_per_km=float(a('h2_fcs').sum() / fuel['drive_mileage_km']),
                final_soc=float(a('SOC')[-1]), delta_soc=float(a('SOC')[-1] - .6),
                soc_min=float(a('SOC').min()), soc_max=float(a('SOC').max()),
                fc_soh_loss=float(1. - a('FCS_SOH')[-1]), battery_soh_loss=float(1. - a('SOH')[-1]),
                fc_starts=starts, load_change_events=int((dpfc > 9.5).sum()),
                start_share=starts * 1.96e-5 / max(float(1. - a('FCS_SOH')[-1]), 1e-30),
                fc_on_pct=float(on.mean() * 100.), fc_efficiency=eff,
                min_off_run_s=int(min(off_runs)) if off_runs else None,
                override_steps=int(a('rb_override').sum()) if 'rb_override' in data else None,
                delivery_failure_steps=int(sum(shortfall_steps(power).values())),
                unserved_kwh=power['unserved_kwh'], trace_path=str(path))


def analyze():
    rows = []
    for p_off, min_off in itertools.product(P_OFF_KW, MIN_OFF_S):
        for cycle in CYCLES:
            case = OUT / 'runs' / case_name(p_off, min_off) / f'Standard_{cycle}' / 'efficient_band'
            row = trace_metrics(case / 'episode_data/data_ep0.mat', cycle)
            cal = json.loads((case / 'soc_balance_calibration.json').read_text())
            row.update(method='Efficient-band', p_off_kw=p_off, min_off_s=min_off,
                       rb_soc_balance_offset=cal['soc_balance_offset'])
            rows.append(row)
    ref = pd.read_csv(REFERENCE / 'metrics_rb_dp.csv')
    ref['start_share'] = ref.fc_starts * 1.96e-5 / ref.fc_soh_loss
    metrics = pd.concat([ref.assign(p_off_kw=np.nan, min_off_s=np.nan), pd.DataFrame(rows)],
                        ignore_index=True, sort=False)
    metrics.to_csv(OUT / 'metrics.csv', index=False)

    keys = ['equivalent_h2_g_per_km', 'fc_soh_loss', 'battery_soh_loss', 'fc_starts',
            'load_change_events', 'delivery_failure_steps']
    eb = metrics[metrics.method == 'Efficient-band']
    mean = eb.groupby(['p_off_kw', 'min_off_s'])[keys].mean()
    costs = lambda d: pd.DataFrame(dict(
        h2_cost=d.equivalent_h2_g_per_km / 1000. * H2_PRICE * 100.,
        fc_cost=FC_COST * d.fc_soh_loss / d.distance_km / FC_EOL_LOSS * 100.,
        bt_cost=BATT_COST * d.battery_soh_loss / d.distance_km / BATT_EOL_LOSS * 100.))
    usd = costs(eb).join(eb[['p_off_kw', 'min_off_s']]).groupby(['p_off_kw', 'min_off_s']).mean()
    mean = mean.join(usd.assign(total_cost=usd.sum(axis=1)))
    mean['max_abs_dsoc'] = eb.groupby(['p_off_kw', 'min_off_s']).delta_soc.apply(lambda s: s.abs().max())
    dp = ref[ref.method == 'DP'][keys].mean()
    mean['fc_loss_vs_dp'] = mean.fc_soh_loss / dp.fc_soh_loss
    mean['fuel_vs_dp_pct'] = (mean.equivalent_h2_g_per_km / dp.equivalent_h2_g_per_km - 1.) * 100.
    mean.reset_index().to_csv(OUT / 'summary_four_cycle_mean.csv', index=False)

    pd.set_option('display.width', 200)
    print('four-cycle mean, reference rows (20261013_motor_efficiency_ramp10):')
    ref_usd = costs(ref).join(ref.method).groupby('method').mean()
    print(ref.groupby('method')[keys].mean().join(ref_usd.assign(total_cost=ref_usd.sum(axis=1))).to_string())
    print('\nefficient-band sweep, four-cycle mean:')
    print(mean.to_string(float_format=lambda v: f'{v:.4g}'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--analyze_only', action='store_true')
    parser.add_argument('--workers', type=int, default=20)
    args = parser.parse_args()
    if args.analyze_only:
        return analyze()
    if (OUT / 'manifest.json').exists():
        raise FileExistsError('This run already has a manifest; preserve it and use a new output directory.')
    (OUT / 'logs').mkdir(exist_ok=True)
    hashes = {s: sha(PROJECT / s) for s in SOURCES}
    for source in SOURCES:
        target = OUT / 'source_snapshot' / source
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT / source, target)
    grid = list(itertools.product(CYCLES, P_OFF_KW, MIN_OFF_S))
    manifest = dict(created_at=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
                    description='Efficient-band rule (Liu et al. 2020, Energy 118212) at p_off 0.95 kW (plant FC-off level) swept over '
                                'minimum off time; plant conditions as 20261013_motor_efficiency_ramp10.',
                    reference=str(REFERENCE), cycles=CYCLES, p_off_kw=P_OFF_KW, min_off_s=MIN_OFF_S,
                    source_hashes=hashes,
                    commands={f'{case_name(p, m)}_{c}': command(c, p, m) for c, p, m in grid},
                    python=sys.version,
                    git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        completed = [f.result() for f in as_completed([pool.submit(run_case, *g) for g in grid])]
    failed = [c for c in completed if c['returncode']]
    assert hashes == {s: sha(PROJECT / s) for s in SOURCES}, 'Source changed during run'
    (OUT / 'completion.json').write_text(json.dumps(dict(cases=completed, failed=failed,
                                                         source_hashes_unchanged=True), indent=2) + '\n')
    if failed:
        raise RuntimeError(f'{len(failed)} cases failed; see logs/')
    print(f'All {len(completed)} evaluations complete', flush=True)
    analyze()


if __name__ == '__main__':
    main()
