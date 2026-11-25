"""Frozen, training-cycle-only closed-loop validation of fixed ep399 actors.

Scenario construction accepts physics and a drive trace, never policy outcomes.
Results are diagnostic evidence; this module does not invent a new adoption gate.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def acceleration(speed):
    return np.r_[np.diff(speed), 0.0]


def initialize_state(agent, profile, case, normalization, target):
    """Snapshot at start-1. The returned observation carries the start-1 speed/acceleration
    (the 'lagged' convention); `rollout` replaces them under 'current' timing."""
    agent.SOC_init = float(case["initial_soc"])
    agent.SOC_target = float(target)
    agent.OCV_initial = float(agent.Battery.ocv_func(agent.SOC_init))
    agent.abs_spd_MAX, agent.abs_acc_MAX = normalization["speed"], normalization["acceleration"]
    agent.reset_obs()
    agent.P_FCS = float(case["initial_fc_kw"])
    agent.FCHEV.P_FC_old = agent.P_FCS
    agent.car_spd, agent.car_acc = profile["previous_speed"], profile["previous_acceleration"]
    bus, _, _ = agent.FCHEV.run_fuel_cell(agent.P_FCS)
    agent.P_batt = (profile["previous_demand_kw"] - bus) * 1000
    if profile["previous_demand_kw"] < 0 and bus <= agent.Battery.batt_maxpower / 1000:
        agent.P_batt = max(agent.P_batt, -agent.Battery.batt_maxpower)
    agent.P_mot = agent.P_batt + bus * 1000
    voc, resistance = float(agent.paras_list[2]), float(agent.Battery.r0_func(agent.SOC))
    agent.I_batt = (voc - math.sqrt(max(0., voc * voc - 4 * resistance * agent.P_batt))) / (2 * resistance)
    # Battery is Rint: no uninitialized polarization state; SOC/SOH/OCV agree.
    return np.array([agent.SOC, agent.SOH_batt, agent.SOH_FCS,
                     agent.P_FCS / agent.P_FCS_max, agent.P_batt / agent.P_batt_max,
                     agent.car_spd / agent.abs_spd_MAX, agent.car_acc / agent.abs_acc_MAX], dtype=np.float32)
