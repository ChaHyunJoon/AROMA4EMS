import copy
from collections import Counter
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2])]
from arguments_ldri import get_ldri_args
from env_ldri import make_env_ldri
from training_initial_states import initial_state_schedule, initialize_training_state


@pytest.fixture
def args(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['test'])
    a = get_ldri_args()
    a.seed, a.cuda, a.ramp_limit_kw = 41, False, 19.
    a.training_initial_states = 'balanced'
    return a


def test_schedule_balances_states_without_consuming_global_rng():
    np.random.seed(7)
    before = np.random.get_state()
    rows = initial_state_schedule(500, 41, 20.)
    after = np.random.get_state()
    assert before[0] == after[0] and np.array_equal(before[1], after[1])
    assert before[2:] == after[2:]
    counts = Counter((r['initial_soc'], r['initial_fc_kw']) for r in rows)
    assert counts.pop((.6, 0.)) == 250
    assert len(counts) == 8 and set(counts.values()) <= {31, 32}
    assert rows == initial_state_schedule(500, 41, 20.)
    assert rows != initial_state_schedule(500, 61, 20.)


def test_reset_consistency_and_fixed_evaluation_restoration(args):
    env, _ = make_env_ldri(args)
    initial = env.reset().copy()
    state = initialize_training_state(env, dict(initial_soc=.5, initial_fc_kw=30.))
    a = env.agent
    assert a.SOC == a.SOC_init == a.paras_list[0] == .5
    assert a.SOC_target == .6
    assert a.OCV_initial == a.paras_list[2] == pytest.approx(float(a.Battery.ocv_func(.5)))
    assert a.P_FCS == a.FCHEV.P_FC_old == 30.
    assert a.P_batt == pytest.approx(-a.FCHEV.run_fuel_cell(30.)[0] * 1000)
    voc, r = a.paras_list[2], float(a.Battery.r0_func(.5))
    assert voc * a.I_batt - r * a.I_batt**2 == pytest.approx(a.P_batt)
    assert state[0] == pytest.approx(.5)
    np.testing.assert_array_equal(env.reset(), initial)
    assert a.SOC == a.SOC_init == .6 and a.SOC_target == .6
    assert a.P_FCS == a.FCHEV.P_FC_old == 0.
    assert a.OCV_initial == float(a.Battery.ocv_func(.6))


def test_evaluation_calls_do_not_advance_training_schedule(args):
    env, _ = make_env_ldri(args)
    state = env.reset_training(1).copy()
    for _ in range(5):
        env.reset()
    np.testing.assert_array_equal(state, env.reset_training(1))
    assert env.agent.SOC_target == .6


def test_fixed_and_nominal_balanced_reset_have_identical_dynamics(args):
    fixed = copy.deepcopy(args)
    fixed.training_initial_states = 'fixed'
    a, _ = make_env_ldri(fixed)
    b, _ = make_env_ldri(args)
    np.testing.assert_array_equal(a.reset_training(0), b.reset_training(0))
    for step in range(20):
        action = np.array([.1 if step % 2 else -.1])
        sa, ra, da, _ = a.step(action, step)
        sb, rb, db, _ = b.step(action, step)
        np.testing.assert_array_equal(sa, sb)
        assert ra == rb and da == db


def test_invalid_mode_and_out_of_bounds_rejected(args):
    env, _ = make_env_ldri(args)
    with pytest.raises(ValueError):
        initialize_training_state(env, dict(initial_soc=.99, initial_fc_kw=30.))
    args.soc_target = .5
    with pytest.raises(ValueError, match='CS'):
        env.reset_training(1)


def test_runner_uses_training_reset_and_keeps_eval_nominal(args, tmp_path):
    import torch
    from runner_ldri import RunnerLDRI
    torch.set_num_threads(1)
    args.save_dir = str(tmp_path / 'models')
    env, args = make_env_ldri(args)
    args.episode_steps = 12
    runner = RunnerLDRI(args, env, tmp_path)
    runner._run_one_episode_sac(1, tmp_path)
    import json
    row = json.loads((tmp_path / 'training_initial_states.jsonl').read_text())
    case = env.training_schedule[1]
    assert row['initial_soc'] == case['initial_soc']
    assert row['initial_fc_kw'] == case['initial_fc_kw']
    buffer_size = runner.buffer.currentSize
    assert runner.buffer._done[buffer_size - 1] == 1  # Normal finite-horizon end also stops bootstrap.
    runner.validation_eval_hook = lambda *a: None
    metrics = runner._evaluate_policy_sac()
    assert runner.buffer.currentSize == buffer_size
    assert env.agent.SOC_init == .6
    assert metrics['physical_evidence']['scalars']['soc_initial'] == .6
