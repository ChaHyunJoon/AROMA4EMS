import argparse
import json
import os
import sys
import time

import numpy as np
import scipy.io as scio
from tqdm import tqdm

from common.env import make_env
from common.evaluate import compute_fcev_reference_mpg
from common.utils import Logger, summarize_fc_efficiency
from power_constraints import DEFAULT_FAILURE_COST_PER_STEP, TRACE_KEYS
from rule_based_calibrate import add_efficient_band_args, build_controller, solve_soc_balance


def get_args():
    parser = argparse.ArgumentParser("Rule-based FCEV EMS baseline evaluator")
    parser.add_argument("--scenario_name", type=str, default="Standard_WLTC_WVUINTER")
    parser.add_argument("--evaluate_episode", type=int, default=1)
    parser.add_argument("--rb_save_dir", type=str, default="./eva_rule_based")
    parser.add_argument("--rb_name", type=str, default="rule_based_controller")

    parser.add_argument("--w_soc", type=float, default=300.0)
    parser.add_argument("--soc0", type=float, default=0.6)
    parser.add_argument("--soc_target", type=float, default=0.6)
    parser.add_argument("--MODE", type=str, default="CS")
    parser.add_argument("--eq_h2_batt_coef", type=float, default=0.0164)

    # The baseline runs the same clamp plant as SAC/AROMA (common/env.py), which
    # accounts for a terminal SOC failure with the same discounted penalty.
    # Defaults match common/arguments.py so the three controllers stay comparable.
    parser.add_argument("--gamma", type=float, default=0.995)
    parser.add_argument("--failure_cost_per_step", type=float,
                        default=DEFAULT_FAILURE_COST_PER_STEP)
    parser.add_argument("--ramp_limit_kw", type=float, default=0.0)

    parser.add_argument("--rb_soc_turn_on", type=float, default=0.57)
    parser.add_argument("--rb_soc_turn_off", type=float, default=0.605)
    parser.add_argument("--rb_soc_force_charge", type=float, default=0.54)
    parser.add_argument("--rb_demand_turn_on", type=float, default=18.0)
    parser.add_argument("--rb_demand_turn_off", type=float, default=8.0)
    parser.add_argument("--rb_min_fc_on_kw", type=float, default=10.0)
    parser.add_argument("--rb_ramp_up", type=float, default=8.0)
    parser.add_argument("--rb_ramp_down", type=float, default=10.0)
    parser.add_argument("--rb_min_on_steps", type=int, default=15)
    parser.add_argument("--rb_min_off_steps", type=int, default=5)
    parser.add_argument("--rb_reserve_kw", type=float, default=4.0)
    parser.add_argument("--rb_charge_bias_gain", type=float, default=220.0)
    parser.add_argument("--rb_soc_deep_charge", type=float, default=0.30)
    parser.add_argument("--rb_soc_recovery_floor", type=float, default=0.30)
    parser.add_argument("--rb_soc_recovery_ceiling", type=float, default=0.45)
    parser.add_argument("--rb_average_power_floor_kw", type=float, default=8.0)
    parser.add_argument("--rb_average_power_quantile", type=float, default=0.50)
    parser.add_argument("--rb_average_hold_tolerance_kw", type=float, default=1.0)
    parser.add_argument("--rb_p_avg_scale", type=float, default=1.0)
    parser.add_argument("--rb_soc_balance_offset", type=float, default=0.0)
    parser.add_argument("--rb_stop_speed_mps", type=float, default=0.3)
    add_efficient_band_args(parser)

    # SOC balancing: solve the single scalar knob so the episode ends on soc_target.
    # Without it the baseline ends well above soc0 and its fuel economy is not comparable.
    parser.add_argument("--rb_auto_soc_balance", type=int, default=1)
    parser.add_argument("--rb_balance_knob", type=str, default="soc_balance_offset",
                        choices=["soc_balance_offset", "p_avg_scale"])
    parser.add_argument("--rb_balance_grid_points", type=int, default=13)
    parser.add_argument("--rb_balance_xatol", type=float, default=1e-4)
    return parser.parse_args()


def _episode_info_template():
    return {
        "T_mot": [],
        "W_mot": [],
        "mot_eff": [],
        "P_mot": [],
        "P_fc": [],
        "P_fce": [],
        "fce_eff": [],
        "FCS_SOH": [],
        "P_dcdc": [],
        "dcdc_eff": [],
        "FCS_De": [],
        "travel": [],
        "d_s_s": [],
        "d_low": [],
        "d_high": [],
        "d_l_c": [],
        "EMS_reward": [],
        "soc_cost": [],
        "h2_fcs": [],
        "h2_batt": [],
        "h2_equal": [],
        "objective_cost": [],
        "h2_cost": [],
        "batt_soh_cost": [],
        "fcs_soh_cost": [],
        "SOC": [],
        "SOH": [],
        "I": [],
        "I_c": [],
        "pack_OCV": [],
        "pack_Vt": [],
        "pack_power_out": [],
        "P_batt_req": [],
        "tep_a": [],
        "dsoh": [],
        "soc_in_bounds": [],
        "rb_mode_id": [],
        "rb_fc_on": [],
        "rb_p_dem": [],
        "rb_p_fc_target": [],
        "rb_p_fc_cmd": [],
        "rb_p_avg": [],
        "rb_soc_init": [],
        "rb_soc_descending": [],
        "rb_starting_from_stop": [],
        "rb_override": [],
    }


def _append_info(episode_info, info):
    # Same contract as common/evaluate.py: register the plant's power-balance
    # trace on first sight so a clamp violation is recorded, not lost.
    for key in TRACE_KEYS:
        if key in info and key not in episode_info:
            episode_info[key] = []
    for key in episode_info.keys():
        episode_info[key].append(info.get(key, np.nan))


def _summarize_episode(env, episode, episode_info, episode_reward):
    travel_m = float(episode_info["travel"][-1])
    travel_km = travel_m / 1000.0
    h2 = float(np.nansum(np.asarray(episode_info["h2_fcs"], dtype=np.float64)))
    h2_batt = float(np.nansum(np.asarray(episode_info["h2_batt"], dtype=np.float64)))
    h2_equal = float(np.nansum(np.asarray(episode_info["h2_equal"], dtype=np.float64)))
    objective_cost = float(np.nansum(np.asarray(episode_info["objective_cost"], dtype=np.float64)))

    h2_100 = h2 / travel_km * 100.0 if travel_km > 1e-9 else np.nan
    h2_batt_100 = h2_batt / travel_km * 100.0 if travel_km > 1e-9 else np.nan
    h2_equal_100 = h2_equal / travel_km * 100.0 if travel_km > 1e-9 else np.nan
    objective_100 = objective_cost / travel_km * 100.0 if travel_km > 1e-9 else np.nan

    mpg, fuel_eq_total_gal = compute_fcev_reference_mpg(
        travel_m=travel_m,
        h2_fcs_gps=episode_info["h2_fcs"],
        p_batt_kw=episode_info["P_batt_req"],
        dt_s=float(getattr(env.agent.FCHEV, "simtime", 1.0)),
    )

    soc_arr = np.asarray(episode_info["SOC"], dtype=np.float64)
    soc_min = float(np.min(soc_arr))
    soc_max = float(np.max(soc_arr))
    soc_mean = float(np.mean(soc_arr))
    soc_in_bounds_rate = float(np.mean(np.asarray(episode_info["soc_in_bounds"], dtype=np.float64))) * 100.0

    mean_soc_cost = float(np.mean(episode_info["soc_cost"]))
    mean_h2_cost = float(np.mean(episode_info["h2_cost"]))
    mean_fcs_cost = float(np.mean(episode_info["fcs_soh_cost"]))
    mean_batt_cost = float(np.mean(episode_info["batt_soh_cost"]))
    mean_objective = float(np.mean(episode_info["objective_cost"]))

    p_fc = np.asarray(episode_info["P_fc"], dtype=np.float64)
    p_batt = np.asarray(episode_info["P_batt_req"], dtype=np.float64)
    min_p_fc = float(np.min(p_fc))
    max_p_fc = float(np.max(p_fc))
    mean_p_fc = float(np.mean(p_fc))
    min_p_batt = float(np.min(p_batt))
    max_p_batt = float(np.max(p_batt))
    mean_p_batt = float(np.mean(p_batt))
    mean_fce_eff, pct_fc_on = summarize_fc_efficiency(
        p_fc,
        episode_info["fce_eff"],
        on_threshold=env.agent.FCHEV.P_FC_off,
    )

    unserved = float(np.nansum(np.asarray(episode_info.get("unserved_power_kw", [0.]), dtype=np.float64)))
    unaccepted = float(np.nansum(np.asarray(episode_info.get("unaccepted_power_kw", [0.]), dtype=np.float64)))
    clamp_steps = int(np.nansum(np.asarray(episode_info.get("power_constraint_failed", [0.]), dtype=np.float64)))

    final_soc = float(episode_info["SOC"][-1])
    final_batt_soh = float(episode_info["SOH"][-1])
    final_fcs_soh = float(episode_info["FCS_SOH"][-1])
    ep_r = float(np.sum(episode_reward)) if episode_reward else 0.0

    print(
        "\nepi %d: travel %.3fkm, SOC %.4f, Bat-SOH %.6f, FCS-SOH %.6f"
        % (episode, travel_km, final_soc, final_batt_soh, final_fcs_soh)
    )
    print(
        "epi %d: H2_100km %.1fg, H2eq_100km %.1fg (batt %.1fg), MPG %.2f, fuel_eq %.4f USgal, objective_100km %.2f"
        % (episode, h2_100, h2_equal_100, h2_batt_100, mpg, fuel_eq_total_gal, objective_100)
    )
    print(
        "epi %d: SOC[min/mean/max]=%.3f/%.3f/%.3f, in_bounds_rate=%.1f%%, len=%d"
        % (episode, soc_min, soc_mean, soc_max, soc_in_bounds_rate, len(episode_reward))
    )
    print(
        "epi %d: mean_cost soc %.3f, h2eq %.3f, fcs %.3f, batt %.3f, obj %.3f"
        % (episode, mean_soc_cost, mean_h2_cost, mean_fcs_cost, mean_batt_cost, mean_objective)
    )
    print(
        "epi %d: P_fc min/mean/max %.2f/%.2f/%.2f kW, P_batt_req min/mean/max %.2f/%.2f/%.2f kW, fce_eff mean %.3f, fc_on %.1f%%"
        % (episode, min_p_fc, mean_p_fc, max_p_fc, min_p_batt, mean_p_batt, max_p_batt, mean_fce_eff, pct_fc_on)
    )
    print(
        "epi %d: power balance -- clamp steps %d, unserved %.4f kWh, unaccepted %.4f kWh"
        % (episode, clamp_steps, unserved / 3600.0, unaccepted / 3600.0)
    )
    print("episode %d: reward %.3f" % (episode, ep_r))

    return {
        "reward": ep_r,
        "h2_100": h2_100,
        "h2_batt_100": h2_batt_100,
        "h2_equal_100": h2_equal_100,
        "mpg": mpg,
        "fuel_eq_gal": fuel_eq_total_gal,
        "objective_100": objective_100,
        "final_soc": final_soc,
        "final_batt_soh": final_batt_soh,
        "final_fcs_soh": final_fcs_soh,
        "clamp_steps": clamp_steps,
        "unserved_kwh": unserved / 3600.0,
        "unaccepted_kwh": unaccepted / 3600.0,
    }


def main():
    args = get_args()
    env, args = make_env(args)

    eval_name = args.scenario_name + "/" + args.rb_name
    save_path = os.path.join(args.rb_save_dir, eval_name)
    save_path_episode = os.path.join(save_path, "episode_data")
    os.makedirs(save_path_episode, exist_ok=True)

    sys.stdout = Logger(filepath=save_path + "/", filename="evaluate_log.log")
    print("cycle name: ", args.scenario_name)
    print("baseline name: ", args.rb_name)
    print("evaluate episodes: ", args.evaluate_episode)
    print("episode_steps: ", args.episode_steps)
    print("abs_spd_MAX: %.3f m/s" % args.abs_spd_MAX)
    print("abs_acc_MAX: %.3f m/s2" % args.abs_acc_MAX)
    print("SOC target: ", args.soc_target)
    print("initial SOC: ", args.soc0)
    print("SOC-MODE: ", args.MODE)
    print("eq_h2_batt_coef: ", args.eq_h2_batt_coef)
    print("plant: common/env.py (clamp, power_constraints.execute) -- same as SAC/AROMA")
    print("gamma: ", args.gamma)
    print("failure_cost_per_step: ", args.failure_cost_per_step)
    print("ramp_limit_kw: ", args.ramp_limit_kw)

    controller = build_controller(env, args)

    balance = None
    if int(args.rb_auto_soc_balance):
        balance = solve_soc_balance(
            env,
            controller,
            args.episode_steps,
            args.soc_target,
            knob=args.rb_balance_knob,
            xatol=args.rb_balance_xatol,
            grid_points=args.rb_balance_grid_points,
            verbose=True,
            tag=args.scenario_name,
        )
        with open(os.path.join(save_path, "soc_balance_calibration.json"), "w", encoding="utf-8") as f:
            json.dump(balance, f, indent=2)

    calibration = controller.get_calibration()
    with open(os.path.join(save_path, "rule_based_config.json"), "w", encoding="utf-8") as f:
        json.dump(calibration, f, indent=2, ensure_ascii=False)

    print("rule-based calibration:")
    for key, value in calibration.items():
        if key == "mode_names":
            continue
        print("  %s: %s" % (key, value))

    rewards = []
    h2_100_list = []
    h2_batt_100_list = []
    h2_equal_100_list = []
    mpg_list = []
    fuel_eq_gal_list = []
    objective_100_list = []
    fcs_soh_list = []
    batt_soh_list = []
    soc_list = []

    print("\n-----Start evaluating rule-based baseline!-----")
    for episode in tqdm(range(args.evaluate_episode)):
        controller.reset()
        env.reset()
        episode_info = _episode_info_template()
        episode_reward = []
        start_time = time.time()

        for step in range(args.episode_steps):
            car_spd = float(env.speed_list[step])
            car_acc = float(env.acc_list[step])
            soc = float(env.agent.SOC)
            action, rb_debug = controller.select_action(soc=soc, car_spd=car_spd, car_acc=car_acc)
            _, step_reward, done, info = env.step(action, step)
            info.update(rb_debug)
            if abs(float(info["fc_applied_kw"]) - rb_debug["rb_p_fc_cmd"]) > 1e-4:
                raise ValueError("plant FC power %.6f differs from the rule-based command %.6f at step %d"
                                 % (info["fc_applied_kw"], rb_debug["rb_p_fc_cmd"], step))
            _append_info(episode_info, info)
            episode_reward.append(step_reward)
            if done:
                datadir = os.path.join(save_path_episode, "data_ep%d.mat" % episode)
                scio.savemat(datadir, mdict=episode_info)
                raise ValueError(
                    "Rule-based episode ended at step %d: %s; partial trace saved to %s"
                    % (step, info.get("power_failure_reason", "plant_done"), datadir))

        datadir = os.path.join(save_path_episode, "data_ep%d.mat" % episode)
        scio.savemat(datadir, mdict=episode_info)

        summary = _summarize_episode(env, episode, episode_info, episode_reward)
        rewards.append(summary["reward"])
        h2_100_list.append(summary["h2_100"])
        h2_batt_100_list.append(summary["h2_batt_100"])
        h2_equal_100_list.append(summary["h2_equal_100"])
        mpg_list.append(summary["mpg"])
        fuel_eq_gal_list.append(summary["fuel_eq_gal"])
        objective_100_list.append(summary["objective_100"])
        fcs_soh_list.append(summary["final_fcs_soh"])
        batt_soh_list.append(summary["final_batt_soh"])
        soc_list.append(summary["final_soc"])

        spent_time = time.time() - start_time
        print("episode %d: time spent %.3fs" % (episode, spent_time))

    scio.savemat(os.path.join(save_path, "reward.mat"), mdict={"reward": rewards})
    scio.savemat(os.path.join(save_path, "h2.mat"), mdict={"h2": h2_100_list})
    scio.savemat(os.path.join(save_path, "h2_batt.mat"), mdict={"h2_batt": h2_batt_100_list})
    scio.savemat(os.path.join(save_path, "h2_equal.mat"), mdict={"h2_equal": h2_equal_100_list})
    scio.savemat(os.path.join(save_path, "mpg.mat"), mdict={"mpg": mpg_list})
    scio.savemat(os.path.join(save_path, "fuel_eq_gal.mat"), mdict={"fuel_eq_gal": fuel_eq_gal_list})
    scio.savemat(os.path.join(save_path, "objective.mat"), mdict={"objective_100": objective_100_list})
    scio.savemat(os.path.join(save_path, "FCS_SOH.mat"), mdict={"FCS_SOH": fcs_soh_list})
    scio.savemat(os.path.join(save_path, "Batt_SOH.mat"), mdict={"Batt_SOH": batt_soh_list})
    scio.savemat(os.path.join(save_path, "SOC.mat"), mdict={"SOC": soc_list})

    print("-----Evaluating is finished!-----")
    print("-----Data saved in: <%s>-----" % save_path)


if __name__ == "__main__":
    main()
