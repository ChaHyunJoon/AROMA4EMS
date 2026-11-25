import sys
from pathlib import Path

import numpy as np
import pytest

sys.path[:0] = [str(Path(__file__).resolve().parents[2]), str(Path(__file__).resolve().parents[1])]
from agentEMS_pure_h2_consumption import EMS


def agent(ramp=0., soc=.6):
    a = EMS(200., soc, 'CS', 40., 5., ramp_limit_kw=ramp)
    a.reset_obs()
    return a


def drive(a, demand_kw, action=-1.):
    # Keep a consistent shaft point while isolating dispatch from vehicle load.
    rpm, eta = 3000., .9
    mechanical = demand_kw * (eta if demand_kw >= 0 else 1/eta)
    torque = mechanical * 1000 / (rpm * 2*np.pi/60)
    a.FCHEV.T_W_axle = lambda v, acc: (torque, rpm, mechanical*1000)
    a.FCHEV.run_motor = lambda t, w, p: (t, w, eta, t*w*2*np.pi/60*(eta if t < 0 else 1/eta))
    a.execute([action], 20., 0.)
    return a.info


def test_demand_beyond_battery_is_clamped_and_recorded():
    """The shortfall is dropped and recorded, and the drive carries on."""
    a = agent()
    info = drive(a, 80.)
    assert not a.done                      # a power-balance violation is never terminal
    assert info['fc_requested_kw'] == info['fc_applied_kw'] == 0   # never projected up
    assert info['P_dcdc'] == 0 and info['h2_fcs'] == 0
    assert info['battery_requested_kw'] == pytest.approx(80.)
    assert info['battery_delivered_kw'] == pytest.approx(40.)   # run_battery's own clamp
    assert info['unserved_power_kw'] == pytest.approx(40.)
    assert info['power_constraint_failed'] == 1
    assert info['power_failure_reason'] == 'unserved_power'
    assert a.travel == 20.                 # the clamped step still counts distance
    assert a.get_reward() < 0


def test_ramp_limited_shortfall_is_clamped_not_terminal():
    a = agent(19.)
    info = drive(a, 80.)
    assert not a.done and info['power_failure_reason'] == 'unserved_power'
    assert info['P_fc'] == 0               # one ramp step from rest cannot reach the demand
    assert info['unserved_power_kw'] == pytest.approx(40.)
    assert a.travel == 20.
    drive(a, 80.)                          # and the episode continues through it
    assert a.travel == 40. and not a.done


def test_feasible_request_is_unchanged():
    a = agent()
    info = drive(a, 40., action=0.)
    assert info['P_fc'] == 47.5
    assert info['fc_applied_kw'] == info['fc_requested_kw']   # the plant never projects
    assert not a.done


def test_fc_overproduction_is_clamped_and_recorded():
    a = agent()
    info = drive(a, 0., action=1.)
    assert info['P_fc'] == 95              # the stack is never projected down
    assert info['P_dcdc'] > 40
    assert info['battery_delivered_kw'] == pytest.approx(-40.)
    assert info['unaccepted_power_kw'] == pytest.approx(info['P_dcdc'] - 40.)
    assert not a.done and info['power_failure_reason'] == 'unaccepted_fc_power' 


def test_regen_overflow_is_clamped_not_absorbed_by_friction():
    """There is no friction path here: excess regeneration is simply dropped."""
    a = agent()
    info = drive(a, -80.)
    assert not a.done
    assert info['motor_requested_kw'] == pytest.approx(-80.)
    assert info['P_mot'] == pytest.approx(-80.)     # motor torque is never re-solved
    assert info['unaccepted_power_kw'] == pytest.approx(40.)


def test_fc_surplus_is_recorded_not_silently_absorbed():
    a = agent(19.)
    a.P_FCS = a.FCHEV.P_FC_old = 95.
    info = drive(a, 0.)
    assert info['P_fc'] == 76.
    assert not a.done and info['power_failure_reason'] == 'unaccepted_fc_power'
    assert info['unaccepted_power_kw'] == pytest.approx(info['P_dcdc'] - 40.)


@pytest.mark.parametrize('soc', [.010001, .6, .999999])
def test_battery_limits_respect_rint_and_next_soc(soc):
    a = agent(soc=soc)
    b = a.Battery
    low, high = b.power_limits(a.paras_list)
    voc, r = a.paras_list[2], float(b.r0_func(soc))
    assert -40000 <= low <= 0 <= high <= 40000
    for power in [low, high]:
        i = 2*power/(voc + np.sqrt(max(0., voc*voc-4*r*power)))
        next_soc = soc - i*b.timestep/(3600*b.Cn)
        assert b.soc_min-1e-12 <= next_soc <= b.soc_max+1e-12
        assert voc*i-r*i*i == pytest.approx(power)


def test_nexo_net_power_is_monotone_in_stack_power():
    a = agent()
    grid = np.linspace(0., 95., 10001)
    assert np.all(np.diff(a.FCHEV.run_fuel_cell(grid)[0]) >= 0)


@pytest.mark.parametrize('soc,demand', [(1., -80.), (.01, 20.)])
def test_soc_boundary_is_the_only_terminal_failure(soc, demand):
    """Nothing holds the battery inside its range, so the clamp drives it out.

    run_battery applies a flat +-batt_maxpower clamp that ignores the SOC-aware
    power_limits, so contact with the boundary overshoots it. This is the one
    failure the pre-constraint EMS also terminated on, and the only one that
    still sets done; power_failure_reason must name it over any balance
    violation recorded on the same step.
    """
    a = agent(soc=soc)
    info = drive(a, demand)
    assert a.done and info['power_failure_reason'] == 'battery_soc_limit'
    assert info['battery_soc_clamped'] == 1
    assert a.SOC == pytest.approx(soc)


def test_actual_battery_soc_overshoot_is_still_a_failure():
    a = agent(soc=.999999)
    _, _, _, failed, info = a.Battery.run_battery(-40000., a.paras_list)
    assert failed and info['battery_soc_clamped'] == 1
    assert info['soc_unclamped'] > 1.


def test_baseline_and_aroma_use_identical_physics_and_reward_cannot_edit_failure_reason(monkeypatch):
    from arguments_ldri import get_ldri_args
    from env_ldri import make_env_ldri
    from candidate_validation import checked_reward
    monkeypatch.setattr(sys, 'argv', ['test'])
    args = get_ldri_args()
    args.ramp_limit_kw = 0.
    env, _ = make_env_ldri(args)
    env.reset()
    baseline = EMS(args.w_soc, args.soc0, args.MODE, env.abs_spd_MAX, env.abs_acc_MAX,
                   w_h2=args.w_h2, w_fc=args.w_fc, w_batt=args.w_batt,
                   eq_h2_batt_coef=args.eq_h2_batt_coef, soc_target=args.soc_target,
                   soc_bounds=(args.soc_low, args.soc_high))
    baseline.reset_obs()
    for step in range(60):
        a = [.3]
        # The env adds only observation timing: obs[5], obs[6] of the step the next action serves.
        x = env.drive_observation(baseline.execute(a, env.speed_list[step], env.acc_list[step]), step + 1)
        y, _, done, _ = env.step(a, step)
        np.testing.assert_array_equal(x, y)
        assert baseline.info['P_dcdc'] == env.agent.info['P_dcdc']
        assert not done
    reward_fn = type(env.agent).get_reward
    checked_reward(reward_fn, env.agent)  # Text metadata must be supported.
    def corrupt(state):
        r = reward_fn(state)
        state.info['power_failure_reason'] = 'changed'
        return r
    with pytest.raises(ValueError, match='physical telemetry'):
        checked_reward(corrupt, env.agent)


def test_runner_completes_clamped_drive_and_never_ranks_a_violating_one(monkeypatch, tmp_path):
    import torch
    from arguments_ldri import get_ldri_args
    from env_ldri import make_env_ldri
    from runner_ldri import RunnerLDRI
    torch.set_num_threads(1)
    monkeypatch.setattr(sys, 'argv', ['test'])
    args = get_ldri_args()
    args.cuda, args.ramp_limit_kw = False, 19.
    args.save_dir = str(tmp_path/'models')
    env, args = make_env_ldri(args)
    args.episode_steps = 3
    env.speed_list = np.array([20., 20., 20.])
    env.acc_list = np.array([2., 2., 2.])
    runner = RunnerLDRI(args, env, tmp_path)
    metrics = runner._run_one_episode_sac(0, tmp_path)
    assert metrics['ep_len'] == runner.buffer.currentSize == 3  # the clamp never stops the drive
    assert metrics['travel'] > 0.
    # The demand outruns the ramp on every step, so the last one still violates
    # the balance and the drive must not be ranked as a completed fuel result.
    assert not metrics['tracking_success']
    assert np.isnan(metrics['g_per_km'])
    assert np.isnan(metrics['paper_fuel']['equivalent_g_per_km'])
    metrics = runner._evaluate_policy_sac()
    assert metrics['ep_len'] == 3
    assert not metrics['tracking_success']
    assert runner.buffer.currentSize == 3
