"""Predeclared initial-state intervention; never used by evaluation resets."""
from itertools import product

import numpy as np


def initial_state_schedule(episodes, seed, best_fc_kw):
    """50% nominal, remaining episodes balanced over eight other grid states.

    A private RNG keeps SAC's exploration/replay random stream untouched.
    Full cycles, target SOC and environment-step budgets are unchanged.
    """
    alternatives = [(soc, fc) for soc, fc in product((.5, .6, .7), (0., float(best_fc_kw), 30.))
                    if (soc, fc) != (.6, 0.)]
    if len(set(alternatives)) != 8:
        raise ValueError("Initial FC grid must contain three distinct powers")
    rng = np.random.default_rng(int(seed))
    order = []
    rows = []
    for episode in range(episodes):
        if episode % 2 == 0:
            soc, fc = .6, 0.
        else:
            if not order:
                order = rng.permutation(len(alternatives)).tolist()
            soc, fc = alternatives[order.pop()]
        rows.append(dict(episode=episode, initial_soc=soc, initial_fc_kw=fc))
    return rows


def initialize_training_state(env, case):
    from scenario_validation import initialize_state
    agent = env.agent
    soc, fc = case['initial_soc'], case['initial_fc_kw']
    if not agent.soc_bounds[0] < soc < agent.soc_bounds[1] or not 0 <= fc <= agent.P_FCS_max:
        raise ValueError("Training initial state outside physical limits")
    bus = float(agent.FCHEV.run_fuel_cell(fc)[0])
    # At the existing standstill reset, FC output must be absorbed by the battery.
    if bus * 1000 > agent.Battery.batt_maxpower:
        raise ValueError("Initial FC output exceeds battery charge power limit")
    return initialize_state(
        agent, dict(previous_speed=0., previous_acceleration=0., previous_demand_kw=0.),
        case, dict(speed=env.abs_spd_MAX, acceleration=env.abs_acc_MAX), .6)
