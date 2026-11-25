"""Evaluate every iteration's ep399 actor of the 20261017 seq_v3_catalog runs (Claude agents) (seeds 41/61/81).

Four held-out cycles plus the training cycle (reproducibility check against the recorded ep399
metrics). Total cost uses aroma/operating_cost.py, the selection objective of sequential v3.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import contextlib
import csv
import hashlib
import json
import os
import sys
import traceback
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
PROJECT = (OUT.parents[2] / 'FCHEV-EMS')
os.chdir(PROJECT)
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / 'aroma'))
import numpy as np
import scipy.io as sio
import torch
from common.arguments import get_args
from common.env import make_env
from common.evaluate import Evaluator
from common.paper_fuel_economy import compute_paper_style_fuel_economy, fc_operating_efficiency
from common.utils import get_driving_cycle
from power_constraints import summarize_power_violations, shortfall_steps
from operating_cost import operating_cost

torch.set_num_threads(1)
torch.set_num_interop_threads(1)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


TRAIN_CYCLE = 'WLTC_WVUINTER'
CYCLES = ['UDDS', 'WVUSUB', 'LA92', 'HWFET', TRAIN_CYCLE]
SEEDS = [41, 61, 81]
ITERS = range(1, 7)


def collect_jobs():
    jobs = {}
    for seed in SEEDS:
        roots = list((PROJECT / 'aroma_baseline_matched').glob(f'seed{seed}_obscur_20261017_*'))
        assert len(roots) == 1, roots
        runs = list((roots[0] / 'search').iterdir())
        assert len(runs) == 1
        run = runs[0]
        training = json.loads((run / 'validation_manifest.json').read_text())
        trials = {}
        for p in run.glob('trials/*/trial_result.json'):
            t = json.loads(p.read_text())
            trials.setdefault(t['candidate_id'], []).append((p, t))
        for iteration in ITERS:
            result = json.loads((run / f'iter_{iteration:03d}/result.json').read_text())
            if 'candidate' not in result:  # proposal_failed: nothing trained this iteration
                print(f'skip seed{seed} iter{iteration}: {result.get("decision")}', flush=True)
                continue
            cid = result['candidate']['candidate_id']
            assert len(trials[cid]) == 1, (seed, iteration)
            trial_path, trial = trials[cid][0]
            assert trial['status'] == 'complete' and trial['chunk']['end_episode'] == 399
            actor = Path(trial['chunk']['model_dir']) / 'actor_iter001_ep399.pkl'
            assert actor.is_file()
            label = f'seed{seed}_iter{iteration:03d}_ep399'
            audit = {p: dict(training_sha256=h, evaluation_sha256=sha(p), unchanged=sha(p) == h)
                     for p, h in training['source_hashes'].items() if Path(p).is_file()}
            jobs[label] = dict(seed=seed, iteration=iteration, run=str(run), trial=str(trial_path.parent),
                               candidate_id=cid, adoption_decision=result['decision'],
                               verdict=result.get('verdict'),
                               recorded_ep399=result['candidate'].get('final_ep399'),
                               recorded_cost=result['candidate'].get('operating_cost'),
                               recorded_fuel_breakdown=result['candidate'].get('fuel_breakdown'),
                               actor_path=str(actor), actor_sha256=sha(actor),
                               conditions=training['conditions'], training_source_audit=audit)
    return jobs


def rollout(task):
    cycle, label, job = task
    case_dir = OUT / f'Standard_{cycle}' / label
    case_dir.mkdir(parents=True, exist_ok=True)
    if (case_dir / 'episode_data/data_ep0.mat').exists():
        raise FileExistsError(f'Refusing to overwrite an existing rollout: {case_dir}')
    sys.argv = [sys.argv[0]]
    args = get_args()
    for key, value in job['conditions'].items():
        setattr(args, key, value)
    args.scenario_name = f'Standard_{cycle}'
    args.episode_steps = None
    args.evaluate, args.load_or_not, args.evaluate_episode = True, False, 1
    args.cuda, args.eval_stochastic = False, False
    args.seed, args.random_seed = job['seed'], False
    args.save_dir = str(case_dir / 'model_scratch')
    args.eva_dir, args.eval_name = str(OUT), f'Standard_{cycle}/{label}'
    torch.manual_seed(job['seed'])
    np.random.seed(job['seed'])
    error = None
    with (case_dir / 'evaluation.log').open('w') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        env, args = make_env(args)
        evaluator = Evaluator(args, env)
        evaluator.DRL_agent.actor.load_state_dict(
            torch.load(job['actor_path'], map_location='cpu', weights_only=True), strict=True)
        evaluator.DRL_agent.actor.eval()
        write_json(case_dir / 'evaluation_args.json', vars(args))
        try:
            evaluator.evaluate()
        except Exception:
            error = traceback.format_exc()
            print(error)
    data_path = case_dir / 'episode_data/data_ep0.mat'
    if not data_path.exists():
        raise RuntimeError(f'No trace from {cycle}/{label}: {error}')
    data = sio.loadmat(data_path)
    a = lambda k: np.asarray(data[k], dtype=float).reshape(-1)
    required = ['SOC', 'SOH', 'FCS_SOH', 'h2_fcs', 'travel', 'power_failure_code', 'unserved_power_kw']
    assert all(np.isfinite(a(k)).all() for k in required)
    dt_s = float(env.agent.FCHEV.simtime)
    eff = fc_operating_efficiency(data)
    fuel = compute_paper_style_fuel_economy(a('travel'), a('h2_fcs'), np.r_[args.soc0, a('SOC')],
                                            dt_s=dt_s, fc_efficiency=eff)
    power = summarize_power_violations(data, dt_s)
    power['delivery_failure_steps'] = sum(shortfall_steps(power).values())
    completed = len(a('SOC')) == args.episode_steps and error is None
    valid = completed and power['trace_available'] and power['delivery_failure_steps'] == 0
    soc_full = np.r_[args.soc0, a('SOC')]
    fc_loss, batt_loss = float(1 - a('FCS_SOH')[-1]), float(1 - a('SOH')[-1])
    cost = operating_cost(fuel['equivalent_g_per_km'], fc_loss, batt_loss, fuel['drive_mileage_km'])
    row = dict(cycle=cycle, policy=label, seed=job['seed'], iteration=job['iteration'],
               adoption_decision=job['adoption_decision'], checkpoint_episode=399,
               completed=completed, valid_delivery=bool(valid), steps=len(a('SOC')),
               distance_km=fuel['drive_mileage_km'],
               equivalent_h2_g_per_km=fuel['equivalent_g_per_km'],
               raw_h2_g_per_km=float(a('h2_fcs').sum() * dt_s / fuel['drive_mileage_km']),
               soc_correction_g=fuel['batt_eq_h2_g'], fc_efficiency=eff,
               initial_soc=args.soc0, final_soc=float(a('SOC')[-1]),
               soc_drift=float(a('SOC')[-1] - args.soc0),
               soc_min=float(soc_full.min()), soc_max=float(soc_full.max()),
               soc_in_bounds_pct=float(100 * np.mean((a('SOC') >= .4) & (a('SOC') <= .8))),
               fc_soh_loss=fc_loss, battery_soh_loss=batt_loss,
               h2_usd=cost['h2_usd'], fc_usd=cost['fc_usd'], batt_usd=cost['batt_usd'],
               total_usd=cost['total_usd'],
               delivery_failure_steps=power['delivery_failure_steps'],
               unserved_kwh=power['unserved_kwh'], unaccepted_fc_kwh=power['unaccepted_fc_kwh'],
               unaccepted_regen_kwh=power['unaccepted_regen_kwh'],
               trace_path=str(data_path), error=error)
    if completed:
        assert np.isclose(fuel['drive_mileage_km'],
                          np.sum(get_driving_cycle(f'Standard_{cycle}')) * dt_s / 1000)
    row['fc_starts'] = int((a('d_s_s') > 0).sum())
    row['fc_lc_events'] = int((a('d_l_c') > 0).sum())
    row['fc_low_s'] = int((a('d_low') > 0).sum())
    write_json(case_dir / 'metrics.json', dict(metrics=row, power=power))
    return row


if __name__ == '__main__':
    jobs = collect_jobs()
    manifest = dict(checkpoint_episode=399, cycles=CYCLES, training_cycle=TRAIN_CYCLE, jobs=jobs,
                    deterministic_mean_action=True, learning=False, device='cpu',
                    metric='paper_energy_explicit_initial_soc; total cost = aroma/operating_cost.py',
                    evaluation_script_sha256=sha(__file__),
                    created_utc=datetime.now(timezone.utc).isoformat())
    write_json(OUT / 'manifest.json', manifest)
    tasks = [(c, label, job) for c in CYCLES for label, job in jobs.items()]
    rows = []
    with ProcessPoolExecutor(max_workers=12) as pool:
        for row in pool.map(rollout, tasks):
            rows.append(row)
            print(f"{row['cycle']:14s} {row['policy']:22s} eq={row['equivalent_h2_g_per_km']:.4f} "
                  f"dSOC={row['soc_drift']:+.4f} total={row['total_usd']:.2f} valid={row['valid_delivery']}",
                  flush=True)
    write_csv(OUT / 'metrics.csv', rows)
    write_json(OUT / 'results.json', dict(metrics=rows))
    manifest.update(completed_utc=datetime.now(timezone.utc).isoformat(), actual_results=len(rows))
    write_json(OUT / 'manifest.json', manifest)
    print('Saved:', OUT, flush=True)
