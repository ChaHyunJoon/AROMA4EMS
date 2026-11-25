"""The single environment wrapper for every EMS entry point.

All of them -- SAC training and evaluation, the rule-based baseline, and the
aroma/AROMA reward search through its own `aroma/env_ldri.py` -- drive the same
plant: `agentEMS_pure_h2_consumption.EMS`, whose `execute` is
`power_constraints.execute`. The plant clamps rather than enforcing the power
balance, and publishes every shortfall and surplus through
`power_constraints.TRACE_KEYS`.

Keeping one plant here is what makes the three controllers comparable: a fuel
number is only meaningful against another number produced under the same
physics, the same action convention and the same failure accounting.
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.utils import (get_driving_cycle, get_acc_limit, observation_scales, observation_timing,
                          set_drive_observation)
from agentEMS_pure_h2_consumption import EMS
from power_constraints import DEFAULT_FAILURE_COST_PER_STEP, failure_penalty, learning_reward


class Env:
    """ environment for EMS"""

    def __init__(self, args):
        self.args = args
        # Fail here rather than mid-episode if the failure accounting is unusable.
        failure_penalty(getattr(args, "failure_cost_per_step", DEFAULT_FAILURE_COST_PER_STEP),
                        args.gamma, 0)
        self.speed_list = get_driving_cycle(cycle_name=args.scenario_name)
        self.acc_list = get_acc_limit(self.speed_list, output_max_min=False)
        self.abs_spd_MAX, self.abs_acc_MAX = observation_scales(args, self.speed_list, self.acc_list)
        self.obs_timing = observation_timing(args)

        self.agent = EMS(
            args.w_soc,
            args.soc0,
            args.MODE,
            self.abs_spd_MAX,
            self.abs_acc_MAX,
            eq_h2_batt_coef=args.eq_h2_batt_coef,
            soc_target=args.soc_target,
            ramp_limit_kw=getattr(args, "ramp_limit_kw", 0.0),
        )
        self.obs_num = self.agent.obs_num
        self.action_num = self.agent.action_num

    def _drive_observation(self, obs, step):
        # 'current': the observation returned before step `step` carries v[step], a[step].
        # Past the last step nothing is served next; the terminal observation is never
        # bootstrapped, so it keeps the last step's values.
        if self.obs_timing == "current" and step < len(self.speed_list):
            set_drive_observation(obs, self.speed_list[step], self.acc_list[step],
                                  self.abs_spd_MAX, self.abs_acc_MAX)
        return obs

    def reset(self):
        return self._drive_observation(self.agent.reset_obs(), 0)

    def step(self, action, episode_step):
        car_spd = self.speed_list[episode_step]
        car_acc = self.acc_list[episode_step]

        obs = self._drive_observation(self.agent.execute(action, car_spd, car_acc), episode_step + 1)
        reward = self.agent.get_reward()
        # `learning_reward` is what the agent optimises; EMS_reward and
        # objective_cost keep their own component accounting in info.
        reward = learning_reward(self.agent, reward, self.args, episode_step,
                                 getattr(self.args, "episode_steps", None) or len(self.speed_list))
        done = self.agent.get_done()
        info = self.agent.get_info()

        return obs, reward, done, info


def make_env(args):
    env = Env(args)
    args.obs_dim = env.agent.obs_num
    args.action_dim = env.agent.action_num
    args.fc_max_power_kw = float(env.agent.P_FCS_max)
    args.episode_steps = len(env.speed_list)   # cycle length
    args.abs_spd_MAX = env.abs_spd_MAX
    args.abs_acc_MAX = env.abs_acc_MAX
    args.obs_timing = env.obs_timing
    return env, args
