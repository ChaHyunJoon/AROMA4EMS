"""Re-solve DP and recalibrate/evaluate the rule baseline with current motor losses.

Usage from repository root: .venv/bin/python FCHEV-EMS/evaluation_runs/20261013_motor_efficiency_ramp10/run.py
Existing experiment outputs are never overwritten.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
from zoneinfo import ZoneInfo

OUT = Path(__file__).resolve().parent
PROJECT = (OUT.parents[2] / 'FCHEV-EMS')
ROOT = PROJECT.parent
CYCLES = ['UDDS', 'WVUSUB', 'LA92', 'HWFET']
TAG = '_ss_per_cycle_motor_eff_20261013'
SOURCES = ['FCHEV_SOH.py', 'Battery.py', 'power_constraints.py', 'agentEMS_pure_h2_consumption.py',
           'DP_env.py', 'DP_EMS_agent_new.py', 'dp_main_interp_2d.py', 'rule_based_eval.py',
           'rule_based_calibrate.py', 'rule_based_controller.py', 'common/arguments.py',
           'common/env.py', 'common/utils.py', 'common/paper_fuel_economy.py']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dp_dir(cycle):
    return PROJECT / f'DP_result/Standard_{cycle}_w500_fc_eff_remap_dR10_interp{TAG}'


def command(method, cycle):
    common = ['--scenario_name', f'Standard_{cycle}', '--w_soc', '500', '--ramp_limit_kw', '10',
              '--soc0', '0.6', '--soc_target', '0.6', '--MODE', 'CS', '--gamma', '0.995']
    if method == 'DP':
        return [sys.executable, '-u', 'dp_main_interp_2d.py', *common,
                '--file_v', 'fc_eff_remap', '--w_terminal', '1000000', '--unserved_cost_per_kw', '50',
                '--dp_soc_increment', '0.0001', '--plant_conditions', str(OUT / 'plant_conditions.json'),
                '--out_tag', TAG]
    return [sys.executable, '-u', 'rule_based_eval.py', *common,
            '--rb_save_dir', str(OUT / 'rule_based_ramp10'), '--rb_auto_soc_balance', '1']


def run_case(method, cycle):
    print(f'START {method} {cycle}', flush=True)
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    with (OUT / 'logs' / f'{method}_{cycle}.log').open('w') as f:
        result = subprocess.run(command(method, cycle), cwd=PROJECT, env=env, stdout=f, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'{method} {cycle} failed with {result.returncode}; see log')
    if method == 'DP':
        src = dp_dir(cycle)
        dst = OUT / f'Standard_{cycle}/DP_dR10_reoptimized'
        dst.mkdir(parents=True)
        shutil.copytree(src / 'episode_data', dst / 'episode_data')
        shutil.copy2(src / 'summary.json', dst / 'source.json')
    print(f'DONE {method} {cycle}', flush=True)
    return dict(method=method, cycle=cycle, returncode=result.returncode)


def run_group(method, workers):
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return [f.result() for f in as_completed([pool.submit(run_case, method, c) for c in CYCLES])]


def main():
    if (OUT / 'manifest.json').exists():
        raise FileExistsError('This run already has a manifest; preserve it and use a new output directory.')
    for c in CYCLES:
        if dp_dir(c).exists():
            raise FileExistsError(dp_dir(c))
    (OUT / 'logs').mkdir(exist_ok=True)
    conditions = dict(w_soc=500., soc0=.6, soc_target=.6, MODE='CS', gamma=.995,
                      ramp_limit_kw=10., eq_h2_batt_coef=.0164, obs_norm='fixed',
                      obs_speed_scale=40., obs_acc_scale=4., obs_timing='current',
                      failure_cost_per_step=1000., unserved_cost_per_kw=50.)
    (OUT / 'plant_conditions.json').write_text(json.dumps({'conditions': conditions}, indent=2) + '\n')
    hashes = {s: sha(PROJECT / s) for s in SOURCES}
    for source in SOURCES:
        target = OUT / 'source_snapshot' / source
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT / source, target)
    maps = list((ROOT / 'project-data/FCHEV_data').glob('*.mat')) + list((ROOT / 'project-data/Battery_data').glob('*.pkl'))
    manifest = dict(created_at=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
                    description='Current motor efficiency and driveline torque loss, current per-start FC wear; DP solved anew and rule SOC calibration repeated.',
                    conditions=conditions, cycles=CYCLES, source_hashes=hashes,
                    source_data_hashes={str(p.relative_to(ROOT)): sha(p) for p in maps},
                    cycle_hashes={c: sha(ROOT / f'project-data/standard_driving_cycles/mat-data/Standard_{c}.mat') for c in CYCLES},
                    commands={f'{m}_{c}': command(m, c) for m in ['DP', 'Rule-based'] for c in CYCLES},
                    dp_output_dirs={c: str(dp_dir(c)) for c in CYCLES},
                    reference=str(OUT.parent / '20261013_fc_startstop_per_cycle/metrics_rb_dp.csv'),
                    dp=dict(soc_increment=.0001, soc_states=4000, fc_states=96, terminal_soc_weight=1e6),
                    python=sys.version, git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    with ThreadPoolExecutor(max_workers=2) as groups:
        futures = [groups.submit(run_group, 'DP', 2), groups.submit(run_group, 'Rule-based', 1)]
        completed = [case for f in as_completed(futures) for case in f.result()]
    assert hashes == {s: sha(PROJECT / s) for s in SOURCES}, 'Source changed during run'
    (OUT / 'completion.json').write_text(json.dumps(dict(cases=completed, source_hashes_unchanged=True), indent=2) + '\n')
    print('All 8 evaluations complete', flush=True)


if __name__ == '__main__':
    main()
