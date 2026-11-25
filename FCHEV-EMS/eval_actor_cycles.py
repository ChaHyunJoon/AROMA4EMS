"""Deterministic evaluation of saved SAC/AROMA actors on arbitrary cycles, in main.py's output layout.

AROMA trial actors are saved as actor_iter001_ep*.pkl, which main.py --evaluate cannot
load; this drives the same common.env plant and common.evaluate.Evaluator instead and
writes <eva_root>/<cycle>/<label>/episode_data/data_ep0.mat.

Observation scaling must match how each actor was trained: actors trained before
2026-09-25 saw speed/acc divided by the training cycle's maximum (WLTC_WVUINTER:
36.5 m/s, 1.8560822 m/s2); pass those with --obs_speed_scale/--obs_acc_scale.

    python eval_actor_cycles.py --eva_root DIR --label SAC --actor PATH \
        --cycles Standard_WVUCITY Standard_LA92 [--obs_speed_scale 36.5 --obs_acc_scale 1.8560822340556111]
"""
import argparse
import sys

import torch


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--eva_root", required=True)
    cli.add_argument("--label", required=True)
    cli.add_argument("--actor", required=True)
    cli.add_argument("--cycles", nargs="+", required=True)
    cli.add_argument("--ramp_limit_kw", type=float, default=10.0)
    cli.add_argument("--w_soc", type=float, default=500.0)
    cli.add_argument("--obs_speed_scale", type=float, default=40.0)
    cli.add_argument("--obs_acc_scale", type=float, default=4.0)
    cli.add_argument("--obs_timing", choices=["current", "lagged"], default="current",
                     help="lagged for actors trained before 2026-09-25")
    own, _ = cli.parse_known_args()

    from common.arguments import get_args
    from common.env import make_env
    from common.evaluate import Evaluator

    for cycle in own.cycles:
        sys.argv = [sys.argv[0]]
        args = get_args()
        args.scenario_name, args.w_soc, args.ramp_limit_kw = cycle, own.w_soc, own.ramp_limit_kw
        args.obs_norm, args.obs_speed_scale, args.obs_acc_scale = "fixed", own.obs_speed_scale, own.obs_acc_scale
        args.obs_timing = own.obs_timing
        args.evaluate, args.load_or_not, args.evaluate_episode = True, False, 1
        args.cuda = False
        args.eva_dir, args.eval_name = own.eva_root, f"{cycle}/{own.label}"
        env, args = make_env(args)
        evaluator = Evaluator(args, env)
        actor = evaluator.DRL_agent.actor
        actor.load_state_dict(torch.load(own.actor, map_location="cpu", weights_only=True))
        actor.eval()
        print(f"[{own.label}] {cycle}: obs scales {env.agent.abs_spd_MAX}/{env.agent.abs_acc_MAX}, "
              f"obs_timing {env.obs_timing}, actor {own.actor}")
        evaluator.evaluate()


if __name__ == "__main__":
    main()
