"""Shared plant step and power-balance instrumentation for the SAC and
reward-search EMS.

The plant clamps. The FC runs at the commanded power, the battery takes what it
can at its rated limit, and the remainder is dropped -- the behaviour that was
in place before this module existed. Nothing here enforces the balance and no
reward weights are changed.

What the module does add is measurement: every shortfall and surplus is
published through TRACE_KEYS, so a violation appears in the trace instead of
vanishing silently. The adoption gate in aroma/adoption_validation.py reads
those keys.

The learning signal (not the plant) prices unserved traction power: a clamped
shortfall burns no hydrogen, so without a price the fuel term rewards
under-supply (LA92_US06, 2026-09-25: FC left at 0-2 kW while demand climbs
past the 40 kW battery limit over 2-3 s).
"""
import math

import numpy as np

POWER_TOLERANCE_KW = 1e-6
DEFAULT_FAILURE_COST_PER_STEP = 1000.0
# Learning cost per kW of unserved traction power per 1 s step. One kW*s saved
# is worth ~0.13 reward at w_h2=10 (~0.013 g H2), so 50 outweighs it ~370x.
DEFAULT_UNSERVED_COST_PER_KW = 50.0
TRACE_KEYS = (
    'policy_action_requested', 'fc_requested_kw', 'fc_applied_kw',
    'motor_requested_kw', 'battery_requested_kw', 'battery_delivered_kw',
    'battery_min_kw', 'battery_max_kw', 'unserved_power_kw',
    'unaccepted_power_kw', 'power_constraint_failed', 'power_failure_code',
    'soc_unclamped', 'battery_soc_clamped',
    'base_reward', 'learning_reward', 'constraint_failure_penalty',
    'failure_cost_per_step', 'failure_remaining_steps', 'unserved_power_penalty',
)
# Numeric per-step cause, so whole-trajectory evidence survives float-only traces/NPZs.
FAILURE_CODES = {'': 0, 'battery_soc_limit': 1, 'traction_motor_limit': 2,
                 'unserved_power': 3, 'unaccepted_fc_power': 4}
# Causes that leave requested traction work undone. A surplus (unaccepted power)
# is not one: it wastes energy the policy already paid for and is reported apart.
SHORTFALL_REASONS = ('battery_soc_limit', 'traction_motor_limit', 'unserved_power')


def summarize_power_violations(trace, dt_s):
    """Whole-trajectory power-balance evidence of one rollout.

    Every step counts, not only the last one: a policy that under-delivers in
    mid-drive and recovers must not look like a completed drive. Unaccepted
    power is split into the part the FC could have avoided (at most its applied
    power) and the regenerative remainder the battery could not absorb.
    """
    codes = np.asarray(trace.get('power_failure_code', []), dtype=float).reshape(-1)
    if not codes.size or not np.isfinite(codes).all():
        return {'trace_available': False}
    names = {v: k for k, v in FAILURE_CODES.items()}
    steps = {names[c]: int(np.sum(codes == c)) for c in FAILURE_CODES.values() if c}

    def series(key):
        arr = np.nan_to_num(np.asarray(trace.get(key, []), dtype=float).reshape(-1), nan=0.)
        return arr if arr.size == codes.size else np.zeros_like(codes)

    unserved, unaccepted, fc = series('unserved_power_kw'), series('unaccepted_power_kw'), series('fc_applied_kw')
    fc_surplus = np.minimum(unaccepted, np.maximum(fc, 0.))
    kwh = lambda arr: float(arr.sum() * dt_s / 3600)
    return {'trace_available': True, 'steps_by_reason': steps,
            'unserved_kwh': kwh(unserved), 'unserved_peak_kw': float(unserved.max(initial=0.)),
            'unaccepted_fc_kwh': kwh(fc_surplus), 'unaccepted_regen_kwh': kwh(unaccepted - fc_surplus),
            'unaccepted_peak_kw': float(unaccepted.max(initial=0.))}


def shortfall_steps(summary):
    """Steps per cause that left requested traction work undone; None without whole-drive evidence."""
    steps = (summary or {}).get('steps_by_reason')
    if not (summary or {}).get('trace_available') or not isinstance(steps, dict):
        return None
    return {k: int(steps[k]) for k in SHORTFALL_REASONS if steps.get(k)}


def failure_penalty(cost_per_step, gamma, remaining_steps):
    """Discounted cost of an absorbing failure through the remaining horizon.

    Includes one failure cost at the current step, even on the last step.
    The rate is a fixed learning hyperparameter, not a physical fuel cost or
    an upper-bound claim for arbitrary LLM-generated rewards.
    """
    cost_per_step, gamma = float(cost_per_step), float(gamma)
    if not math.isfinite(cost_per_step) or cost_per_step <= 0:
        raise ValueError('failure_cost_per_step must be finite and positive')
    if not math.isfinite(gamma) or not 0 <= gamma <= 1:
        raise ValueError('Failure penalty requires gamma in [0, 1]')
    if int(remaining_steps) != remaining_steps or remaining_steps < 0:
        raise ValueError('remaining_steps must be a nonnegative integer')
    n = int(remaining_steps) + 1
    if gamma == 1:
        horizon = float(n)
    elif gamma == 0:
        horizon = 1.
    else:
        horizon = -math.expm1(n * math.log(gamma)) / (1 - gamma)
    return cost_per_step * horizon


def learning_reward(agent, reward, args, episode_step, episode_steps):
    """Apply immutable failure accounting after the ordinary reward contract.

    Since execute() clamps instead of failing, agent.done -- and therefore the
    absorbing penalty -- fires only when the battery SOC leaves its physical
    range. Unserved traction power is charged per step at
    `unserved_cost_per_kw` (the plant still clamps); an unaccepted surplus is
    not, since its hydrogen is already billed by the fuel term.

    EMS_reward/objective_cost retain their original component accounting;
    learning_reward is the reward returned to SAC and stored in replay.
    """
    if not 0 <= episode_step < episode_steps:
        raise ValueError('Step outside episode horizon')
    rate = getattr(args, 'failure_cost_per_step', DEFAULT_FAILURE_COST_PER_STEP)
    remaining = episode_steps - episode_step - 1
    penalty = failure_penalty(rate, args.gamma, remaining) if agent.get_done() else 0.
    unserved_rate = float(getattr(args, 'unserved_cost_per_kw', DEFAULT_UNSERVED_COST_PER_KW))
    if not math.isfinite(unserved_rate) or unserved_rate < 0:
        raise ValueError('unserved_cost_per_kw must be finite and nonnegative')
    unserved_penalty = unserved_rate * float(agent.info.get('unserved_power_kw', 0.))
    adjusted = float(reward) - penalty - unserved_penalty
    agent.info.update(base_reward=float(reward), learning_reward=adjusted,
                      constraint_failure_penalty=penalty, failure_cost_per_step=float(rate),
                      failure_remaining_steps=int(remaining), unserved_power_penalty=unserved_penalty)
    return adjusted


def execute(agent, action, car_spd, car_acc):
    """Plant step with the pre-constraint (clamp) behaviour restored.

    The fuel cell runs at the commanded power and the battery takes the
    remainder, silently clamped to its rated power by run_battery; the unmet
    part simply disappears. Only the battery's physical SOC limit ends an
    episode, exactly as the EMS did before this module existed.

    The violation is still measured and published through TRACE_KEYS. Recording
    costs nothing physically, and its absence is precisely what let the old
    silent clamp go unnoticed: power_constraint_failed marks the individual
    offending step, while agent.done stays reserved for the SOC failure.
    """
    if agent.done:
        raise RuntimeError('Reset EMS after a terminal plant failure')
    requested_action = float(np.asarray(action).reshape(-1)[0])
    if not all(math.isfinite(v) for v in (requested_action, car_spd, car_acc)):
        raise ValueError('Nonfinite action or driving input')
    agent.car_spd, agent.car_acc = car_spd, car_acc
    plant = agent.FCHEV
    previous = agent.P_FCS
    ramp = getattr(agent, 'ramp_limit_kw', 0.)
    a = float(np.clip(requested_action, -1., 1.))
    applied = (float(np.clip(previous + a * ramp, 0., plant.P_FC_max)) if ramp > 0
               else (a + 1) * plant.P_FC_max / 2)
    agent.P_FCS = applied

    ta, wa, pa = plant.T_W_axle(car_spd, car_acc)
    tm, wm, eta, motor_w = plant.run_motor(ta, wa, pa)
    demand = float(motor_w) / 1000
    agent.P_mot = float(motor_w)
    bus, agent.h2_fcs, fc_info = plant.run_fuel_cell(applied)
    agent.dSOH_FCS, health_info = plant.run_FC_SOH(applied)
    agent.SOH_FCS -= agent.dSOH_FCS

    # Rated limits are reported for diagnostics only. run_battery applies its
    # own +-batt_maxpower clamp and nothing here reacts to the shortfall.
    bmin, bmax = (v / 1000 for v in agent.Battery.power_limits(agent.paras_list))
    # Form the request in watts exactly as the pre-constraint EMS did, so the
    # rounding of this step is bit-identical to the trajectories it produced.
    battery_request_w = agent.P_mot - bus * 1000
    battery_request = battery_request_w / 1000
    resistance = float(agent.Battery.r0_func(agent.SOC))
    agent.paras_list, agent.dSOH_batt, agent.I_batt, battery_done, battery_info = agent.Battery.run_battery(
        battery_request_w, agent.paras_list)
    delivered = float(battery_info['P_batt_req'])
    residual = battery_request - delivered

    # The SOC limit comes first because it is the only terminal cause, and
    # probe/eval callers read power_failure_reason to report why done was set.
    shaft_requested = float(ta * wa * 2 * math.pi / 60 / 1000)
    failure = ''
    if battery_done:
        failure = 'battery_soc_limit'
    elif shaft_requested > 0 and (abs(float(tm) - ta) > 1e-7 or demand > plant.motor_max_power / 1000 + POWER_TOLERANCE_KW):
        failure = 'traction_motor_limit'
    elif residual > POWER_TOLERANCE_KW:
        failure = 'unserved_power'
    elif residual < -POWER_TOLERANCE_KW:
        failure = 'unaccepted_fc_power'
    agent.done = bool(battery_done)

    agent.P_batt = delivered * 1000
    agent.SOC, agent.SOH_batt = agent.paras_list[:2]
    agent.Tep_a = 20.
    agent.h2_batt = delivered * agent.eq_h2_batt_coef
    agent.h2_equal = float(agent.h2_fcs) + agent.h2_batt
    agent.P_batt_loss_kw = resistance * agent.I_batt**2 / 1000
    agent.travel += car_spd * agent.time_step
    agent.info = dict(T_axle=ta, W_axle=wa, P_axle=pa/1000,
                      T_mot=float(tm), W_mot=wm, mot_eff=eta,
                      P_mot=agent.P_mot/1000, FCS_SOH=agent.SOH_FCS, travel=agent.travel)
    agent.info.update(fc_info)
    agent.info.update(battery_info)
    agent.info.update(health_info)
    agent.info.update(
        P_batt_req=delivered, P_batt_loss_kw=agent.P_batt_loss_kw,
        policy_action_requested=requested_action, fc_requested_kw=applied,
        fc_applied_kw=applied,
        motor_requested_kw=demand, battery_requested_kw=battery_request,
        battery_delivered_kw=delivered, battery_min_kw=bmin, battery_max_kw=bmax,
        unserved_power_kw=max(0., residual), unaccepted_power_kw=max(0., -residual),
        power_constraint_failed=int(bool(failure)), power_failure_code=FAILURE_CODES[failure],
        power_failure_reason=failure)
    return np.array([agent.SOC, agent.SOH_batt, agent.SOH_FCS,
                     agent.P_FCS / agent.P_FCS_max, agent.P_batt / agent.P_batt_max,
                     car_spd / agent.abs_spd_MAX, car_acc / agent.abs_acc_MAX], dtype=np.float32)
