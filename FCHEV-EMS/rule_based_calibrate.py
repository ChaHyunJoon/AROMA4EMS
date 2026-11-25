"""Charge-balance the rule-based baseline.

The rule-based controller must be SOC-balanced on every test cycle, otherwise the
reported fuel economy is meaningless (energy is silently borrowed from / dumped
into the battery). A single scalar knob is enough:

  * `soc_balance_offset` (default) - shifts the SOC set-point that the
    battery-only / recovery-charge logic switches on. Negative -> stop charging
    earlier -> lower final SOC. Leaves the FC average-power reference (and hence
    the FC operating point / Fig. 11 semantics) untouched.
  * `p_avg_scale` - scales the route-average FC power reference. Also balances,
    but it collapses `p_avg` toward the FC-off corner, so it changes what the
    baseline *is*.

For a given cycle we wrap "run one episode -> final SOC" in a scalar objective
and hand it to `scipy.optimize.minimize_scalar`.
"""

import argparse
import json
import os

import numpy as np
from scipy.optimize import minimize_scalar

from rule_based_controller import EfficientBandRuleEMS, RuleBasedFCEMS

DEFAULT_SCENARIOS = [
    "Standard_LA92_US06",
    "Standard_WVUCITY_UDDS",
    "Standard_WVUSUB_HWFET",
]

KNOB_BOUNDS = {
    # scale of the route-average FC reference; 1.0 == untuned baseline
    "p_avg_scale": (0.02, 3.0),
    # additive shift of the SOC set-point the charge/discharge logic balances around
    "soc_balance_offset": (-0.25, 0.10),
}


def set_knob(controller, knob, value):
    if knob == "p_avg_scale":
        controller.set_p_avg_scale(value)
    elif knob == "soc_balance_offset":
        controller.set_soc_balance_offset(value)
    else:
        raise ValueError("unknown knob: %s" % knob)


def run_episode(env, controller, episode_steps):
    """Run one full cycle and return (final_soc, soc_min, soc_max, h2_100km)."""
    controller.reset()
    env.reset()
    socs = []
    h2 = 0.0
    travel_m = 0.0
    for step in range(episode_steps):
        car_spd = float(env.speed_list[step])
        car_acc = float(env.acc_list[step])
        soc = float(env.agent.SOC)
        action, _ = controller.select_action(soc=soc, car_spd=car_spd, car_acc=car_acc)
        _, _, done, info = env.step(action, step)
        socs.append(float(info["SOC"]))
        h2 += float(info["h2_fcs"])
        travel_m = float(info["travel"])
        if done:
            # The battery left its physical SOC range: this knob value is
            # infeasible, so report the truncated episode rather than stepping
            # a terminal plant.
            break
    travel_km = travel_m / 1000.0
    h2_100 = h2 / travel_km * 100.0 if travel_km > 1e-9 else float("nan")
    soc_arr = np.asarray(socs, dtype=np.float64)
    return float(soc_arr[-1]), float(soc_arr.min()), float(soc_arr.max()), h2_100


def solve_soc_balance(
    env,
    controller,
    episode_steps,
    soc_target,
    knob="soc_balance_offset",
    knob_min=None,
    knob_max=None,
    xatol=1e-4,
    grid_points=13,
    verbose=True,
    tag="",
):
    """Find the knob value whose episode ends at `soc_target`.

    Coarse grid scan (to bracket and to expose the response shape), then
    `minimize_scalar` on the squared final-SOC error inside that bracket.
    The controller is left set to the winning value.
    """
    target = float(soc_target)
    lo_b, hi_b = KNOB_BOUNDS[knob]
    if knob == "soc_balance_offset" and hasattr(controller, "SOC_BALANCE_BOUNDS"):
        lo_b, hi_b = controller.SOC_BALANCE_BOUNDS
    if knob_min is not None:
        lo_b = float(knob_min)
    if knob_max is not None:
        hi_b = float(knob_max)

    n_evals = [0]

    def final_soc_for(value):
        set_knob(controller, knob, value)
        n_evals[0] += 1
        return run_episode(env, controller, episode_steps)[0]

    def wrapper(value):
        return (final_soc_for(value) - target) ** 2

    grid = np.linspace(lo_b, hi_b, int(grid_points))
    grid_soc = [final_soc_for(float(v)) for v in grid]
    if verbose:
        print("\n[%s] SOC-balance scan, knob=%s" % (tag, knob))
        for v, fs in zip(grid, grid_soc):
            print("   %s %+.4f -> final SOC %.4f" % (knob, v, fs))

    err = np.abs(np.asarray(grid_soc) - target)
    k = int(np.argmin(err))
    lo = float(grid[max(0, k - 1)])
    hi = float(grid[min(len(grid) - 1, k + 1)])
    if hi - lo < 1e-9:
        lo, hi = lo_b, hi_b

    res = minimize_scalar(wrapper, bounds=(lo, hi), method="bounded", options={"xatol": float(xatol)})
    best = float(res.x)
    set_knob(controller, knob, best)
    final_soc, soc_min, soc_max, h2_100 = run_episode(env, controller, episode_steps)

    if verbose:
        print(
            "[%s] -> %s %+.5f | final SOC %.4f (target %.2f, err %+.4f) | SOC %.4f..%.4f (swing %.4f) | H2 %.1f g/100km | %d evals"
            % (tag, knob, best, final_soc, target, final_soc - target,
               soc_min, soc_max, soc_max - soc_min, h2_100, n_evals[0])
        )

    return {
        "knob": knob,
        "value": best,
        "bracket": [lo, hi],
        "p_avg_base_kw": getattr(controller, "p_avg_base_kw", None),
        "p_avg_kw": getattr(controller, "p_avg_kw", None),
        "p_avg_scale": getattr(controller, "p_avg_scale", None),
        "soc_balance_offset": float(controller.soc_balance_offset),
        "final_soc": final_soc,
        "soc_target": target,
        "soc_error": final_soc - target,
        "soc_min": soc_min,
        "soc_max": soc_max,
        "soc_swing": soc_max - soc_min,
        "h2_100km_g": h2_100,
        "n_evals": n_evals[0],
        "grid": [{"value": float(v), "final_soc": float(fs)} for v, fs in zip(grid, grid_soc)],
    }


def build_controller(env, args):
    """Build the baseline controller exactly as rule_based_eval.py does."""
    if getattr(args, "rb_policy", "fig11") == "efficient_band":
        return EfficientBandRuleEMS(
            fchev=env.agent.FCHEV,
            p_off_kw=args.rb_p_off_kw,
            min_off_s=args.rb_min_off_s,
            band_eff_ratio=args.rb_band_eff_ratio,
            p_band_hi_kw=args.rb_p_band_hi_kw,
            soc_gain_kw_per_soc=args.rb_soc_gain_kw_per_soc,
            soc_force_on_band=args.rb_soc_force_on_band,
            soc_initial=args.soc0,
            soc_balance_offset=getattr(args, "rb_soc_balance_offset", 0.0),
            ramp_limit_kw=getattr(args, "ramp_limit_kw", 0.0),
        )
    return RuleBasedFCEMS(
        fchev=env.agent.FCHEV,
        speed_list=env.speed_list,
        acc_list=env.acc_list,
        soc_target=args.soc_target,
        soc_turn_on=args.rb_soc_turn_on,
        soc_turn_off=args.rb_soc_turn_off,
        soc_force_charge=args.rb_soc_force_charge,
        demand_turn_on_kw=args.rb_demand_turn_on,
        demand_turn_off_kw=args.rb_demand_turn_off,
        min_fc_on_kw=args.rb_min_fc_on_kw,
        ramp_up_kw_per_s=args.rb_ramp_up,
        ramp_down_kw_per_s=args.rb_ramp_down,
        min_on_steps=args.rb_min_on_steps,
        min_off_steps=args.rb_min_off_steps,
        reserve_kw=args.rb_reserve_kw,
        charge_bias_gain_kw_per_soc=args.rb_charge_bias_gain,
        auto_calibrate=True,
        soc_initial=args.soc0,
        soc_deep_charge=args.rb_soc_deep_charge,
        soc_recovery_floor=args.rb_soc_recovery_floor,
        soc_recovery_ceiling=args.rb_soc_recovery_ceiling,
        average_power_floor_kw=args.rb_average_power_floor_kw,
        average_power_quantile=args.rb_average_power_quantile,
        average_hold_tolerance_kw=args.rb_average_hold_tolerance_kw,
        p_avg_scale=getattr(args, "rb_p_avg_scale", 1.0),
        soc_balance_offset=getattr(args, "rb_soc_balance_offset", 0.0),
        stop_speed_mps=args.rb_stop_speed_mps,
        ramp_limit_kw=getattr(args, "ramp_limit_kw", 0.0),
    )


def add_efficient_band_args(parser):
    """CLI of the efficient-band rule (Liu et al. 2020); shared by the calibrator and the evaluator."""
    parser.add_argument("--rb_policy", type=str, default="fig11", choices=["fig11", "efficient_band"])
    parser.add_argument("--rb_p_off_kw", type=float, default=7.7)
    parser.add_argument("--rb_min_off_s", type=float, default=0.0)
    parser.add_argument("--rb_band_eff_ratio", type=float, default=0.95)
    parser.add_argument("--rb_p_band_hi_kw", type=float, default=None)
    parser.add_argument("--rb_soc_gain_kw_per_soc", type=float, default=200.0)
    parser.add_argument("--rb_soc_force_on_band", type=float, default=0.08)


def get_args():
    parser = argparse.ArgumentParser("Rule-based baseline SOC-balance calibrator")
    parser.add_argument("--scenarios", type=str, nargs="+", default=DEFAULT_SCENARIOS)
    parser.add_argument("--out_json", type=str, default="./eva_rule_based/soc_balance_calibration.json")

    parser.add_argument("--w_soc", type=float, default=300.0)
    parser.add_argument("--soc0", type=float, default=0.6)
    parser.add_argument("--soc_target", type=float, default=0.6)
    parser.add_argument("--MODE", type=str, default="CS")
    parser.add_argument("--eq_h2_batt_coef", type=float, default=0.0164)

    # Required by the shared clamp plant in common/env.py; defaults match
    # common/arguments.py and rule_based_eval.py.
    parser.add_argument("--gamma", type=float, default=0.995)
    parser.add_argument("--failure_cost_per_step", type=float, default=1000.0)
    parser.add_argument("--ramp_limit_kw", type=float, default=0.0)

    parser.add_argument("--knob", type=str, default="soc_balance_offset", choices=sorted(KNOB_BOUNDS))
    parser.add_argument("--knob_min", type=float, default=None)
    parser.add_argument("--knob_max", type=float, default=None)
    parser.add_argument("--xatol", type=float, default=1e-4)
    parser.add_argument("--grid_points", type=int, default=13)

    # Controller defaults mirror rule_based_eval.py so the calibrated value transfers directly.
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
    return parser.parse_args()


def main():
    from common.env import make_env  # local import: keeps this module importable from rule_based_eval

    args = get_args()
    results = []
    for scenario_name in args.scenarios:
        args.scenario_name = scenario_name
        env, args = make_env(args)
        controller = build_controller(env, args)
        record = solve_soc_balance(
            env,
            controller,
            args.episode_steps,
            args.soc_target,
            knob=args.knob,
            knob_min=args.knob_min,
            knob_max=args.knob_max,
            xatol=args.xatol,
            grid_points=args.grid_points,
            verbose=True,
            tag=scenario_name,
        )
        record["scenario_name"] = scenario_name
        results.append(record)

    print("\n===== calibrated %s =====" % args.knob)
    for r in results:
        print(
            "  %-24s %+.5f | final SOC %.4f (err %+.4f) | swing %.4f | H2 %.1f g/100km"
            % (r["scenario_name"], r["value"], r["final_soc"], r["soc_error"], r["soc_swing"], r["h2_100km_g"])
        )

    os.makedirs(os.path.dirname(os.path.abspath(args.out_json)), exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump({"knob": args.knob, "soc_target": args.soc_target, "soc0": args.soc0, "results": results}, f, indent=2)
    print("saved: %s" % args.out_json)


if __name__ == "__main__":
    main()
