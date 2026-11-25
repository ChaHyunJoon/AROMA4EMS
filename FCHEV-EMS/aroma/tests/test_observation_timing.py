"""obs[5], obs[6] carry the speed/acceleration of the step the next action serves."""
import sys

import numpy as np
import pytest


def make(monkeypatch, *flags):
    from arguments_ldri import get_ldri_args
    from env_ldri import make_env_ldri
    monkeypatch.setattr(sys, 'argv', ['test', '--ramp_limit_kw', '0', *flags])
    env, _ = make_env_ldri(get_ldri_args())
    return env


def drive(env, step):
    return np.float32([env.speed_list[step] / env.abs_spd_MAX, env.acc_list[step] / env.abs_acc_MAX])


def test_current_timing_observes_the_step_the_action_serves(monkeypatch):
    env = make(monkeypatch)
    assert env.obs_timing == 'current'
    obs = env.reset()
    np.testing.assert_array_equal(obs[5:], drive(env, 0))
    for step in range(60):
        obs, _, done, _ = env.step([.3], step)
        assert not done
        np.testing.assert_array_equal(obs[5:], drive(env, step + 1))
    # Past the last step nothing is served next: the terminal observation (never
    # bootstrapped) is left as the plant returned it, without indexing past the cycle.
    n = len(env.speed_list)
    last = np.arange(7, dtype=np.float32)
    np.testing.assert_array_equal(env.drive_observation(last.copy(), n), last)


def test_lagged_timing_reproduces_pre_2026_09_25_observations(monkeypatch):
    env = make(monkeypatch, '--obs_timing', 'lagged')
    obs = env.reset()
    assert obs[5] == obs[6] == 0
    for step in range(30):
        obs, _, _, _ = env.step([.3], step)
        np.testing.assert_array_equal(obs[5:], drive(env, step))


def test_plant_state_is_independent_of_observation_timing(monkeypatch):
    current, lagged = make(monkeypatch), make(monkeypatch, '--obs_timing', 'lagged')
    current.reset(), lagged.reset()
    for step in range(60):
        a = [.3 + .05 * np.sin(step / 7.)]
        x, rx, dx, _ = current.step(a, step)
        y, ry, dy, _ = lagged.step(a, step)
        assert not dx and not dy
        np.testing.assert_array_equal(x[:5], y[:5])
        assert rx == ry


def test_resume_of_a_run_without_obs_timing_stays_lagged():
    from main_ldri_refine import _apply_resume_run_config
    import argparse
    args = argparse.Namespace(obs_timing='current')
    _apply_resume_run_config(args, {})
    assert args.obs_timing == 'lagged'


def test_invalid_timing_rejected():
    import argparse
    from common.utils import observation_timing
    with pytest.raises(ValueError):
        observation_timing(argparse.Namespace(obs_timing='future'))
