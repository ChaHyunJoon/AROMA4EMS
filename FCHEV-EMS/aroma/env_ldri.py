import importlib
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.utils import (get_driving_cycle, get_acc_limit, observation_scales, observation_timing,
                          set_drive_observation)


class EnvLDRI:
    """AROMA workflow environment that can reload reward module between iterations."""

    def __init__(self, args, reward_module="agentEMS_for_feedback", force_reload_agent=False):
        self.args = args
        from power_constraints import failure_penalty, DEFAULT_FAILURE_COST_PER_STEP
        failure_penalty(getattr(args, 'failure_cost_per_step', DEFAULT_FAILURE_COST_PER_STEP), args.gamma, 0)
        self.speed_list = get_driving_cycle(cycle_name=args.scenario_name)
        self.acc_list = get_acc_limit(self.speed_list, output_max_min=False)
        self.abs_spd_MAX, self.abs_acc_MAX = observation_scales(args, self.speed_list, self.acc_list)
        self.obs_timing = observation_timing(args)

        EMS = self._load_ems_class(reward_module=reward_module, force_reload=force_reload_agent)
        self.agent = EMS(
            args.w_soc,
            args.soc0,
            args.MODE,
            self.abs_spd_MAX,
            self.abs_acc_MAX,
            w_h2=args.w_h2,
            w_fc=args.w_fc,
            w_batt=args.w_batt,
            eq_h2_batt_coef=args.eq_h2_batt_coef,
            soc_target=args.soc_target,
            soc_bounds=(args.soc_low, args.soc_high),
            ramp_limit_kw=getattr(args, "ramp_limit_kw", 0.0),
        )
        self.obs_num = self.agent.obs_num
        self.action_num = self.agent.action_num
        # Reward modules (including historical copies) cannot bypass physics.
        from types import MethodType
        from power_constraints import execute
        self.agent.execute = MethodType(execute, self.agent)

    @staticmethod
    def _load_ems_class(reward_module, force_reload=False):
        module = importlib.import_module(reward_module)
        if force_reload:
            module = importlib.reload(module)
        if not hasattr(module, "EMS"):
            raise AttributeError(f"module '{reward_module}' does not define EMS class")
        return module.EMS

    def drive_observation(self, obs, step):
        # 'current': the observation returned before step `step` carries v[step], a[step].
        # Past the last step nothing is served next; the terminal observation is never
        # bootstrapped, so it keeps the last step's values.
        if self.obs_timing == "current" and step < len(self.speed_list):
            set_drive_observation(obs, self.speed_list[step], self.acc_list[step],
                                  self.abs_spd_MAX, self.abs_acc_MAX)
        return obs

    def reset(self):
        if getattr(self.args, "training_initial_states", "fixed") == "balanced":
            # Evaluation always returns to the original reset, including OCV.
            self.agent.SOC_init = float(self.args.soc0)
            self.agent.OCV_initial = float(self.agent.Battery.ocv_func(self.agent.SOC_init))
            self.agent.SOC_target = float(self.args.soc_target)
        return self.drive_observation(self.agent.reset_obs(), 0)

    def reset_training(self, episode):
        if getattr(self.args, "training_initial_states", "fixed") == "fixed":
            return self.reset()
        if self.args.MODE != "CS" or self.args.soc0 != .6 or self.args.soc_target != .6:
            raise ValueError("Balanced initial-state experiment requires CS and soc0=target=0.6")
        from training_initial_states import initial_state_schedule, initialize_training_state
        from env_physics_facts import _fc_efficiency_facts
        if not hasattr(self, "training_schedule"):
            best = _fc_efficiency_facts(self.agent.FCHEV)["best_point_kw"]
            self.training_schedule = initial_state_schedule(self.args.chunk_episodes, self.args.seed, best)
        return self.drive_observation(initialize_training_state(self, self.training_schedule[episode]), 0)

    def step(self, action, episode_step):
        car_spd = self.speed_list[episode_step]
        car_acc = self.acc_list[episode_step]

        obs = self.drive_observation(self.agent.execute(action, car_spd, car_acc), episode_step + 1)
        reward = self.agent.get_reward()
        from power_constraints import learning_reward
        reward = learning_reward(self.agent, reward, self.args, episode_step,
                                 getattr(self.args, 'episode_steps', None) or len(self.speed_list))
        done = self.agent.get_done()
        info = self.agent.get_info()

        return obs, reward, done, info


def make_env_ldri(args, force_reload_agent=True):
    env = EnvLDRI(
        args,
        reward_module=getattr(args, "reward_module", "agentEMS_for_feedback"),
        force_reload_agent=force_reload_agent,
    )
    args.obs_dim = env.agent.obs_num
    args.action_dim = env.agent.action_num
    args.fc_max_power_kw = float(env.agent.P_FCS_max)
    args.episode_steps = len(env.speed_list)
    args.abs_spd_MAX = env.abs_spd_MAX
    args.abs_acc_MAX = env.abs_acc_MAX
    return env, args
