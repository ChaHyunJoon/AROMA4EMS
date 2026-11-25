"""The actual replay -> SAC target path must respect terminal failures."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

sys.path[:0] = [str(Path(__file__).resolve().parents[2]), str(Path(__file__).resolve().parents[1])]
from common.memory import MemoryBuffer, PrioritizedMemoryBuffer
from power_constraints import failure_penalty, learning_reward


@pytest.mark.parametrize('gamma', [0., .995, 1.])
@pytest.mark.parametrize('remaining', [0, 20, 3240])
def test_failure_cost_covers_bounded_future_cost_and_last_step(gamma, remaining):
    rate = 1000.
    penalty = failure_penalty(rate, gamma, remaining)
    # From the same prefix, stopping cannot avoid an ordinary cost tail whose
    # step costs are bounded by the configured rate (entropy is not included).
    avoided = sum(rate * gamma**i for i in range(1, remaining + 1))
    assert penalty == pytest.approx(rate + avoided)
    assert penalty > avoided
    assert penalty >= rate


@pytest.mark.parametrize('rate,gamma,remaining', [(0,.995,10), (-1,.995,10),
    (np.inf,.995,10), (1000,-.1,10), (1000,1.1,10), (1000,.995,-1)])
def test_invalid_penalty_configuration_is_rejected(rate, gamma, remaining):
    with pytest.raises(ValueError):
        failure_penalty(rate, gamma, remaining)


def test_penalty_is_separate_from_reward_components_and_zero_on_success():
    args = SimpleNamespace(gamma=.995, failure_cost_per_step=1000.)
    a = SimpleNamespace(info={'EMS_reward': -10., 'objective_cost': 10.}, get_done=lambda: True)
    reward = learning_reward(a, -10., args, 200, 3441)
    assert reward == pytest.approx(-10. - failure_penalty(1000., .995, 3240))
    assert a.info['EMS_reward'] == -10. and a.info['objective_cost'] == 10.
    assert a.info['learning_reward'] == reward
    a.get_done = lambda: False
    assert learning_reward(a, -10., args, 201, 3441) == -10.
    assert a.info['constraint_failure_penalty'] == 0.


@pytest.mark.parametrize('kind', [MemoryBuffer, PrioritizedMemoryBuffer])
def test_replay_preserves_terminal_mask_through_ring_overwrite_and_sampling(kind):
    b = kind(SimpleNamespace(buffer_size=2, batch_size=2))
    b.store([0.], [0.], -1., [1.], False)
    b.store([1.], [0.], -2., [2.], True)
    b.store([2.], [0.], -3., [3.], True)  # overwrite the nonterminal slot
    if kind is PrioritizedMemoryBuffer:
        transition, _, _, _ = b.sample_prioritized()
    else:
        transition = b.random_sample()
    assert len(transition) == 5
    np.testing.assert_array_equal(transition[4], [1., 1.])
    assert np.all(transition[2] <= -2.)


def test_sac_uses_terminal_mask_in_actual_critic_targets(monkeypatch, tmp_path):
    from arguments_ldri import get_ldri_args
    from sac import SAC
    monkeypatch.setattr(sys, 'argv', ['test'])
    args = get_ldri_args()
    args.cuda = False
    args.obs_dim, args.action_dim = 7, 1
    args.save_dir = str(tmp_path)
    args.auto_tune, args.alpha, args.policy_delay = False, 0., 999
    sac = SAC(args)
    with torch.no_grad():
        for parameter in sac.critic.parameters():
            parameter.zero_()
    monkeypatch.setattr(sac.critic_target, 'forward', lambda state, action:
                        (torch.full((len(state), 1), 777.), torch.full((len(state), 1), 777.)))
    rewards = np.array([-200000., -10.], dtype=np.float32)
    transition = (np.zeros((2,7)), np.zeros((2,1)), rewards, np.ones((2,7)), np.array([1.,0.]))
    losses = sac.learn(transition)
    expected = np.array([-200000., -10 + args.gamma * 777])
    np.testing.assert_allclose(sac.last_abs_td, abs(expected), rtol=1e-6)
    assert losses[0] == pytest.approx(np.mean(expected**2), rel=1e-6)
    assert np.isfinite(losses).all()


def test_terminal_penalty_reaches_real_runner_replay(monkeypatch, tmp_path):
    from arguments_ldri import get_ldri_args
    from env_ldri import make_env_ldri
    from runner_ldri import RunnerLDRI
    monkeypatch.setattr(sys, 'argv', ['test'])
    args = get_ldri_args()
    args.cuda, args.ramp_limit_kw, args.batch_size = False, 19., 256
    args.save_dir = str(tmp_path/'models')
    # The plant clamps power, so the battery's SOC limit is the only terminal
    # failure left: start just inside it and let a heavy demand push it out.
    args.soc0 = .011
    env, args = make_env_ldri(args)
    args.episode_steps = 3
    env.speed_list, env.acc_list = np.full(3,20.), np.full(3,2.)
    runner = RunnerLDRI(args, env, tmp_path)
    m = runner._run_one_episode_sac(0, tmp_path)
    assert m['ep_len'] == runner.buffer.currentSize == 1
    assert runner.buffer._done[0] == 1.
    assert env.agent.info['constraint_failure_penalty'] == pytest.approx(1000*(1+.995+.995**2))
    assert runner.buffer._reward[0] == pytest.approx(env.agent.info['learning_reward'], rel=1e-6)
    assert runner.buffer._reward[0] < env.agent.info['EMS_reward'] - 2900


def test_unserved_power_is_priced_outside_the_ems_reward():
    args = SimpleNamespace(gamma=.995, failure_cost_per_step=1000., unserved_cost_per_kw=50.)
    a = SimpleNamespace(info={'EMS_reward': -10., 'unserved_power_kw': 2.5}, get_done=lambda: False)
    assert learning_reward(a, -10., args, 5, 3441) == pytest.approx(-10. - 125.)
    assert a.info['unserved_power_penalty'] == pytest.approx(125.)
    assert a.info['EMS_reward'] == -10. and a.info['base_reward'] == -10.
    a.info['unserved_power_kw'] = 0.
    assert learning_reward(a, -10., args, 6, 3441) == -10.
    args.unserved_cost_per_kw = 0.
    a.info['unserved_power_kw'] = 2.5
    assert learning_reward(a, -10., args, 7, 3441) == -10.


@pytest.mark.parametrize('rate', [-1., np.inf, np.nan])
def test_invalid_unserved_cost_is_rejected(rate):
    args = SimpleNamespace(gamma=.995, failure_cost_per_step=1000., unserved_cost_per_kw=rate)
    a = SimpleNamespace(info={'unserved_power_kw': 1.}, get_done=lambda: False)
    with pytest.raises(ValueError):
        learning_reward(a, -10., args, 0, 10)


def test_real_plant_shortfall_reaches_replay_with_its_price(monkeypatch, tmp_path):
    from arguments_ldri import get_ldri_args
    from env_ldri import make_env_ldri
    from runner_ldri import RunnerLDRI
    monkeypatch.setattr(sys, 'argv', ['test'])
    args = get_ldri_args()
    args.cuda, args.ramp_limit_kw, args.batch_size = False, 10., 256
    args.save_dir = str(tmp_path/'models')
    env, args = make_env_ldri(args)
    # FC starts off and ramps at most 10 kW/s, so a hard launch exceeds FC + 40 kW battery.
    args.episode_steps = 2
    env.speed_list, env.acc_list = np.array([15., 18.]), np.array([3.5, 3.5])
    runner = RunnerLDRI(args, env, tmp_path)
    runner._run_one_episode_sac(0, tmp_path)
    info = env.agent.info
    assert info['unserved_power_kw'] > 0
    assert info['unserved_power_penalty'] == pytest.approx(args.unserved_cost_per_kw * info['unserved_power_kw'])
    assert info['learning_reward'] == pytest.approx(info['base_reward'] - info['unserved_power_penalty'])
    assert runner.buffer._reward[runner.buffer.currentSize - 1] == pytest.approx(info['learning_reward'], rel=1e-6)
