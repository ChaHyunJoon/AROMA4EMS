"""Speed/acceleration observations use one fixed scale on every cycle (2026-09-25)."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path[:0] = [str(Path(__file__).resolve().parents[2]), str(Path(__file__).resolve().parents[1])]
from common.utils import get_driving_cycle, get_acc_limit, observation_scales

CYCLES = ['Standard_WLTC_WVUINTER', 'Standard_UDDS', 'Standard_WVUSUB', 'Standard_LA92', 'Standard_HWFET']


def _cycle(name):
    speed = get_driving_cycle(cycle_name=name)
    return speed, get_acc_limit(speed, output_max_min=False)


@pytest.mark.parametrize('name', CYCLES)
def test_fixed_scale_is_cycle_independent_and_bounds_the_cycle(name):
    speed, acc = _cycle(name)
    assert observation_scales(SimpleNamespace(), speed, acc) == (40., 4.)
    assert max(abs(speed)) <= 40. and max(abs(np.asarray(acc))) <= 4.


def test_legacy_cycle_mode_reproduces_per_cycle_maximum():
    speed, acc = _cycle('Standard_LA92')
    spd, a = observation_scales(SimpleNamespace(obs_norm='cycle'), speed, acc)
    assert spd == pytest.approx(max(abs(speed)))
    assert a == pytest.approx(3.9339422222, rel=1e-6)


@pytest.mark.parametrize('args', [SimpleNamespace(obs_norm='bogus'),
                                  SimpleNamespace(obs_norm='fixed', obs_acc_scale=0.),
                                  SimpleNamespace(obs_norm='fixed', obs_speed_scale=np.nan)])
def test_invalid_scale_configuration_is_rejected(args):
    speed, acc = _cycle('Standard_WLTC_WVUINTER')
    with pytest.raises(ValueError):
        observation_scales(args, speed, acc)


@pytest.mark.parametrize('which', ['ldri', 'common'])
def test_train_and_eval_envs_share_the_scale(monkeypatch, which):
    monkeypatch.setattr(sys, 'argv', ['test'])
    if which == 'ldri':
        from arguments_ldri import get_ldri_args as get_args
        from env_ldri import make_env_ldri as make
    else:
        from common.arguments import get_args
        from common.env import make_env as make
    scales = set()
    for name in ('Standard_WLTC_WVUINTER', 'Standard_LA92'):
        args = get_args()
        args.scenario_name = name
        env, args = make(args)
        scales.add((env.agent.abs_spd_MAX, env.agent.abs_acc_MAX, args.abs_spd_MAX, args.abs_acc_MAX))
        obs = env.agent.execute(np.zeros(1), 20., 2.)
        assert obs[5] == pytest.approx(0.5) and obs[6] == pytest.approx(0.5)
    assert scales == {(40., 4., 40., 4.)}
