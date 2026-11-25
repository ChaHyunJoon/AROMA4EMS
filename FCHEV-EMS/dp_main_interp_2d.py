"""2D DP (SOC x previous FC power) with a linearly interpolated value function.

dp_main_new_2d.py snaps the next SOC to the nearest grid point, so a per-step SOC change below half a grid step costs
nothing in its model, and its plan ends below the SOC target when it is run on the real plant. Here the next SOC stays
continuous: the value of the next state is interpolated linearly between the two neighbouring SOC grid points.

Other differences from dp_main_new_2d.py
- Terminal SOC: a penalty  w_terminal * |SOC_final - SOC_target|  replaces the single admissible terminal grid point
  (an infinite value cannot be interpolated). w_terminal is far above the fuel value of stored energy.
- Horizon: all N steps of the cycle are planned (dp_main_new_2d.py plans N-1 and leaves the last step uncontrolled).
- Unserved traction power costs unserved_cost_per_kw per kW and step, as in the SAC learning reward.
- The forward pass runs on the RL plant (common/env): at every step the action maximises the one-step model reward
  plus the interpolated value of the model's next state, evaluated at the plant's actual SOC.

One-step model, cost weights, ramp limit and discount are those of dp_main_new_2d.py / the SAC baseline reward.

    python dp_main_interp_2d.py --scenario_name Standard_UDDS --w_soc 500 --ramp_limit_kw 10 --file_v fc_eff_remap
"""
import json
import os
import sys
import time

import numpy as np
import scipy.io as scio

from common.arguments import get_args
from DP_env import DP_Env
from DP_EMS_agent_new import DP_EMS_agent_new

OUT_OF_GRID_COST = 1e9  # next SOC outside the SOC grid
TRACE_KEYS = ['SOC', 'SOH', 'FCS_SOH', 'FCS_De', 'h2_fcs', 'travel', 'I', 'P_fc', 'fce_eff', 'P_fce', 'P_mot', 'P_batt_req',
              'fc_applied_kw', 'fc_requested_kw', 'power_failure_code', 'power_constraint_failed', 'unserved_power_kw',
              'unaccepted_power_kw', 'battery_requested_kw', 'battery_delivered_kw', 'battery_max_kw', 'battery_min_kw',
              'motor_requested_kw', 'EMS_reward', 'soc_cost', 'h2_cost', 'fcs_soh_cost', 'batt_soh_cost']


class InterpolatedDP:
    def __init__(self, scenario, args, output_dir, soc_increment=None):
        self.args = args
        self.env = DP_Env(scenario)
        if soc_increment:
            self.env.state_increment = float(soc_increment)
            self.env.states = np.arange(self.env.state_min, self.env.state_max, self.env.state_increment)
        self.agent = DP_EMS_agent_new(w_soc=args.w_soc, soc0=args.soc0, SOC_MODE=args.MODE, eq_h2_batt_coef=args.eq_h2_batt_coef,
                                      soc_target=args.soc_target, ramp_limit_kw=args.ramp_limit_kw)
        self.gamma = float(args.gamma)
        self.w_terminal = float(args.w_terminal)
        self.unserved_rate = float(args.unserved_cost_per_kw)
        self.soc_target = float(self.agent.SOC_target)
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.states = self.env.states.astype(np.float64)
        self.steps = int(self.env.time_steps)
        cache = self.agent.prepare_backward_cache(actions=self.env.actions.astype(np.float64), speed_list=self.env.speed_list,
                                                  acc_list=self.env.acc_list, states=self.states)
        self.cache = cache
        self.fc_power = cache['P_FCS']                       # kW per action
        self.prev_fc = cache['prev_fc_states']               # kW per previous-FC state
        self.next_prev_id = cache['next_prev_fc_ids']        # previous-FC state reached by each action
        assert np.allclose(self.prev_fc[self.next_prev_id], self.fc_power)
        self.cycle_reward = self.agent.get_fc_cycle_reward_matrix().astype(np.float64)   # [prev, action], -inf if ramp infeasible
        self.soc_min, self.soc_inc, self.n_soc = float(self.states[0]), float(self.env.state_increment), int(self.states.size)

        # Battery request before the rated-power clamp, to price unserved traction power.
        battery, plant = self.agent.Battery, self.agent.FCHEV
        dcdc_kw, _, _ = plant.run_fuel_cell(self.fc_power)
        motor_w = np.array([float(plant.run_motor(*plant.T_W_axle(float(v), float(a)))[3])
                            for v, a in zip(self.env.speed_list, self.env.acc_list)])
        request_w = motor_w[:, None] - np.asarray(dcdc_kw, dtype=np.float64).reshape(-1)[None, :] * 1000.0
        assert np.allclose(np.clip(request_w, -battery.batt_maxpower, battery.batt_maxpower), cache['p_batt_ta'])
        self.unserved_kw = np.maximum(request_w - battery.batt_maxpower, 0.0) / 1000.0     # [step, action]

        self.value_path = os.path.join(output_dir, 'value.npy')
        self.value = np.lib.format.open_memmap(self.value_path, mode='w+', dtype=np.float32,
                                               shape=(self.steps + 1, self.n_soc, self.prev_fc.size))
        self.policy = np.lib.format.open_memmap(os.path.join(output_dir, 'reward_action_id.npy'), mode='w+', dtype=np.uint8,
                                                shape=(self.steps, self.n_soc, self.prev_fc.size))

    # ---- one-step model at arbitrary (continuous) SOC ----
    def step_terms(self, step, soc):
        """soc [n] -> next SOC [n, actions], cost without the FC-degradation term [n, actions], and its parts."""
        battery, cache = self.agent.Battery, self.cache
        soc = np.asarray(soc, dtype=np.float64).reshape(-1, 1)
        voc = np.asarray(battery.ocv_func(soc), dtype=np.float64)
        r0 = np.asarray(battery.r0_func(soc), dtype=np.float64)
        p_batt = cache['p_batt_ta'][int(step)][None, :]
        delta = voc ** 2 - 4.0 * r0 * p_batt
        current = np.where(delta < 0.0, voc / (2.0 * r0), (voc - np.sqrt(np.maximum(delta, 0.0))) / (2.0 * r0))
        soc_new = np.clip(soc - battery.timestep * (current / 3600.0 / battery.Cn), battery.soc_min, battery.soc_max)

        low = soc <= battery._loss_soc_split
        c1 = np.where(low, battery._loss_c1_low, battery._loss_c1_high)
        c2 = np.where(low, battery._loss_c2_low, battery._loss_c2_high)
        step_ah = np.abs(current) * battery.timestep / 3600.0
        q_loss = (c1 * soc + c2) * np.exp((-31700.0 + 163.3 * np.abs(current) / battery.Cn) * battery._loss_inv_rt) * step_ah ** battery._loss_z
        batt_cost = self.agent.w_batt * (q_loss * battery._loss_mAh_to_Ah) / battery.Cn

        soc_low, soc_high = self.agent.soc_bounds
        w_soc = np.where((soc_new >= soc_high) | (soc_new <= soc_low), self.agent.w_soc * 10, self.agent.w_soc)
        soc_cost = w_soc * (soc_new - self.soc_target) ** 2
        h2_cost = self.agent.w_h2 * cache['h2_fcs'][None, :]
        unserved_cost = self.unserved_rate * self.unserved_kw[int(step)][None, :]
        return soc_new, soc_cost + h2_cost + batt_cost + unserved_cost, dict(soc=soc_cost, h2=np.broadcast_to(h2_cost, soc_cost.shape),
                                                                           batt=batt_cost, unserved=np.broadcast_to(unserved_cost, soc_cost.shape))

    def next_value(self, value_next, soc_new):
        """Value of the next state for every (row, action): linear interpolation along SOC at the action's FC state."""
        x = (soc_new - self.soc_min) / self.soc_inc
        outside = (x < -1e-9) | (x > self.n_soc - 1 + 1e-9)
        i0 = np.clip(np.floor(x).astype(np.int64), 0, self.n_soc - 2)
        w = np.clip(x - i0, 0.0, 1.0)
        column = np.broadcast_to(self.next_prev_id[None, :], soc_new.shape)
        v = (1.0 - w) * value_next[i0, column] + w * value_next[i0 + 1, column]
        return np.where(outside, v - OUT_OF_GRID_COST, v)

    def backward(self, chunk=128):
        value_next = np.repeat((-self.w_terminal * np.abs(self.states - self.soc_target))[:, None], self.prev_fc.size, axis=1)
        self.value[self.steps] = value_next
        t0 = time.time()
        for step in range(self.steps - 1, -1, -1):
            value_curr = np.empty_like(value_next)
            for start in range(0, self.n_soc, chunk):
                rows = slice(start, min(start + chunk, self.n_soc))
                soc_new, cost, _ = self.step_terms(step, self.states[rows])
                base = -cost + self.gamma * self.next_value(value_next, soc_new)             # [soc, action]
                total = base[:, None, :] + self.cycle_reward[None, :, :]                     # [soc, prev, action]
                best = np.argmax(total, axis=2)
                value_curr[rows] = np.take_along_axis(total, best[:, :, None], axis=2)[:, :, 0]
                self.policy[step, rows] = best.astype(np.uint8)
            assert np.isfinite(value_curr).all()
            self.value[step] = value_curr
            value_next = value_curr
            if step % 200 == 0:
                print(f'  backward step {step}, {time.time() - t0:.0f} s', flush=True)
        self.value.flush(); self.policy.flush()
        np.save(os.path.join(self.output_dir, 'soc_states.npy'), self.states)
        np.save(os.path.join(self.output_dir, 'prev_fc_states.npy'), self.prev_fc)
        return float(self.value[0, self.soc_index(self.args.soc0), self.prev_index(0.0)])

    def soc_index(self, soc):
        return int(np.clip(np.rint((soc - self.soc_min) / self.soc_inc), 0, self.n_soc - 1))

    def prev_index(self, power):
        i = int(np.argmin(np.abs(self.prev_fc - power)))
        assert abs(self.prev_fc[i] - power) < 1e-6, power
        return i

    def forward_on_plant(self, plant_conditions):
        """Run the DP on the RL plant; returns the trace and model-versus-plant diagnostics."""
        from common.env import make_env
        argv, sys.argv = sys.argv, [sys.argv[0]]
        plant_args = get_args()
        sys.argv = argv
        for key, val in plant_conditions.items():
            setattr(plant_args, key, val)
        plant_args.scenario_name = self.args.scenario_name
        env, plant_args = make_env(plant_args)
        env.reset()
        assert plant_args.episode_steps == self.steps
        trace = {k: [] for k in TRACE_KEYS}
        soc, model_soc_error, model_return, discount = float(plant_args.soc0), 0.0, 0.0, 1.0
        for step in range(self.steps):
            prev = float(env.agent.P_FCS)
            pi = self.prev_index(prev)
            soc_new, cost, _ = self.step_terms(step, [soc])
            value_next = np.asarray(self.value[step + 1], dtype=np.float64)
            q = -cost[0] + self.cycle_reward[pi] + self.gamma * self.next_value(value_next, soc_new)[0]
            action = int(np.argmax(q))
            target = float(self.fc_power[action])
            a = (target - prev) / plant_args.ramp_limit_kw
            assert abs(a) <= 1 + 1e-6, (step, a)
            _, _, done, info = env.step(np.array([np.clip(a, -1, 1)]), step)
            assert abs(float(info['fc_applied_kw']) - target) < 1e-5 and (not done or step == self.steps - 1)
            for k in TRACE_KEYS:
                trace[k].append(info[k])
            model_soc_error = max(model_soc_error, abs(float(info['SOC']) - float(soc_new[0, action])))
            model_return += discount * (-cost[0, action] + self.cycle_reward[pi, action])
            discount *= self.gamma
            soc = float(info['SOC'])
        model_return += discount * (-self.w_terminal * abs(soc - self.soc_target))
        return {k: np.asarray(v, dtype=float) for k, v in trace.items()}, dict(max_model_soc_error=model_soc_error, model_return=model_return)


def discounted(x, gamma):
    return float(np.sum(np.asarray(x, dtype=float) * gamma ** np.arange(len(x))))


def main():
    own = [a for a in sys.argv[1:]]
    extra = {}
    for flag in ('--dp_soc_increment', '--plant_conditions', '--out_tag'):
        if flag in own:
            i = own.index(flag); extra[flag] = own[i + 1]; del own[i:i + 2]
    sys.argv = [sys.argv[0]] + own
    args = get_args()
    inc = float(extra.get('--dp_soc_increment', 0)) or None
    tag = extra.get('--out_tag', '')
    out = './DP_result/%s_w%d_%s_dR%g_interp%s' % (args.scenario_name, args.w_soc, args.file_v, args.ramp_limit_kw, tag)
    start = time.time()
    dp = InterpolatedDP(args.scenario_name, args, out, soc_increment=inc)
    print(f'{args.scenario_name}: steps {dp.steps}, SOC states {dp.n_soc} (step {dp.soc_inc:g}), FC states {dp.prev_fc.size}, '
          f'gamma {dp.gamma}, w_soc {args.w_soc}, w_terminal {dp.w_terminal:g}, unserved {dp.unserved_rate:g}/kW', flush=True)
    value0 = dp.backward(chunk=int(args.dp_soc_chunk_size))
    conditions = json.loads(open(extra['--plant_conditions']).read())['conditions']
    trace, diag = dp.forward_on_plant(conditions)
    os.makedirs(os.path.join(out, 'episode_data'), exist_ok=True)
    scio.savemat(os.path.join(out, 'episode_data', 'data_ep0.mat'), trace)
    fc = trace['fc_applied_kw']
    plant_return = discounted(trace['EMS_reward'], dp.gamma) - dp.unserved_rate * discounted(trace['unserved_power_kw'], dp.gamma)
    summary = dict(scenario=args.scenario_name, soc_increment=dp.soc_inc, gamma=dp.gamma, w_soc=float(args.w_soc), w_terminal=dp.w_terminal,
                   final_soc=float(trace['SOC'][-1]), h2_g=float(trace['h2_fcs'].sum()), value_at_start=value0,
                   plant_discounted_return=plant_return, model_discounted_return_incl_terminal=diag['model_return'],
                   plant_undiscounted_cost=float(-trace['EMS_reward'].sum()), max_model_soc_error=diag['max_model_soc_error'],
                   unserved_steps=int((trace['unserved_power_kw'] > 0).sum()), max_abs_dPfc_kw=float(np.abs(np.diff(np.r_[0, fc])).max()),
                   fc_soh_loss=float(1 - trace['FCS_SOH'][-1]), battery_soh_loss=float(1 - trace['SOH'][-1]), seconds=time.time() - start)
    open(os.path.join(out, 'summary.json'), 'w').write(json.dumps(summary, indent=2))
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
