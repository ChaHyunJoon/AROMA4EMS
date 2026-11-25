import argparse

from llm_presets import get_agent_preset, get_agent_type_choices


def str2bool(v):
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean value: {v}")


def get_ldri_args():
    parser = argparse.ArgumentParser("AROMA-style LLM reward refinement for FCEV")

    # Environment / task
    parser.add_argument("--scenario_name", type=str, default="Standard_WLTC_WVUINTER")
    parser.add_argument("--MODE", type=str, default="CS", help="CS or CD")
    parser.add_argument("--soc0", type=float, default=0.6)
    parser.add_argument("--soc_target", type=float, default=0.6)
    parser.add_argument("--training_initial_states", choices=["fixed", "balanced"], default="fixed",
                        help="Training-only initial SOC/FC intervention; evaluation stays at soc0/FC off")
    parser.add_argument("--w_soc", type=float, default=200.0)
    parser.add_argument("--failure_cost_per_step", type=float, default=1000.0,
                        help="Fixed absorbing failure cost per remaining discounted step; not editable by reward search")
    parser.add_argument("--unserved_cost_per_kw", type=float, default=50.0,
                        help="Learning cost per kW of unserved traction power per step; outside the EMS reward, "
                             "the plant still clamps")
    parser.add_argument("--obs_norm", choices=["fixed", "cycle"], default="fixed",
                        help="fixed: speed/acc observations divided by --obs_speed_scale/--obs_acc_scale on every "
                             "cycle; cycle: legacy per-cycle maximum (actors trained before 2026-09-25)")
    parser.add_argument("--obs_speed_scale", type=float, default=40.0, help="m/s, with --obs_norm fixed")
    parser.add_argument("--obs_timing", choices=["current", "lagged"], default="current",
                        help="current: speed/acc observation is the step the action serves; lagged: previous step "
                             "(actors trained before 2026-09-25)")
    parser.add_argument("--obs_acc_scale", type=float, default=4.0, help="m/s2, with --obs_norm fixed")
    parser.add_argument("--w_h2", type=float, default=10.0)
    parser.add_argument("--search_plan", choices=["archive", "fuel_diagnostics_v1"], default="archive",
                        help="fuel_diagnostics_v1: baseline-controlled battery/SOC ablations, then evidence-led refinement")
    parser.add_argument("--development_cycles", nargs="*", default=[],
                        help="Training constituents only: Standard_WLTC Standard_WVUINTER; never the six held-out cycles")
    parser.add_argument("--development_max_regression", type=float, default=0.0,
                        help="Maximum per-development-cycle total-operating-cost regression fraction versus "
                             "baseline (default zero)")
    parser.add_argument("--critic_layernorm", action="store_true",
                        help="Q-network hidden layers 에 LayerNorm (baseline SAC 와 맞추려면 필요)")
    parser.add_argument("--actor_layernorm", action="store_true")
    parser.add_argument("--ramp_limit_kw", type=float, default=0.0,
                        help="0: absolute FC power. >0: normalized dP/ramp with state-dependent "
                             "FC output bounds for fresh SAC policies; also sets the physical ramp limit")
    parser.add_argument("--per", action="store_true",
                        help="uniform replay 대신 Prioritized Experience Replay")
    parser.add_argument("--per_alpha", type=float, default=0.6)
    parser.add_argument("--per_beta0", type=float, default=0.4)
    parser.add_argument("--per_beta_steps", type=int, default=0,
                        help="beta annealing 스텝 수. <=0 이면 beta=1.0 고정")
    parser.add_argument("--per_eps", type=float, default=1e-6)
    parser.add_argument("--w_fc", type=float, default=4.275e6)
    parser.add_argument("--w_batt", type=float, default=1.116e6)
    parser.add_argument("--eq_h2_batt_coef", type=float, default=0.0164)

    # DRL
    parser.add_argument("--DRL", type=str, default="SAC", choices=["SAC"])
    parser.add_argument("--policy", type=str, default="Gaussian", choices=["Gaussian", "Beta"])
    parser.add_argument("--max_episodes", type=int, default=500)
    parser.add_argument("--start_episode", type=int, default=0)
    parser.add_argument("--episode_steps", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=256)
    parser.add_argument("--buffer_size", type=int, default=int(1e6))
    parser.add_argument("--gamma", type=float, default=0.995)
    parser.add_argument("--tau", type=float, default=0.005)
    parser.add_argument("--alpha", type=float, default=1.0)
    parser.add_argument("--auto_tune", type=str2bool, default=True)
    parser.add_argument("--policy_delay", type=int, default=1,
                        help="TD3-style delayed policy updates: actor/temperature updated every N critic updates (1 = standard SAC)")

    # Match the historical seed-61 baseline bands, for both controls and candidates.
    parser.add_argument("--lr_critic", type=float, default=3e-4)
    parser.add_argument("--lr_critic_min", type=float, default=1e-4)
    parser.add_argument("--lr_actor", type=float, default=1e-4)
    parser.add_argument("--lr_actor_min", type=float, default=2e-5)
    parser.add_argument("--lr_alpha", type=float, default=2e-4)
    parser.add_argument(
        "--target_entropy_scale",
        type=float,
        default=1.0,
        help="multiplier on SAC target entropy (-action_dim * scale); passed through to sac.SAC",
    )
    parser.add_argument(
        "--lr_alpha_min",
        type=float,
        default=5e-5,
        help="floor learning rate of alpha; alpha LR follows the same cosine schedule as critic/actor",
    )
    parser.add_argument(
        "--const_lr",
        action="store_true",
        help="bypass the cosine LR schedulers and train actor/critic/alpha at constant "
             "lr_actor/lr_critic/lr_alpha (standard SAC baseline); lr_*_min and warmup/restart args are ignored",
    )
    parser.add_argument(
        "--lr_schedule_episodes",
        type=int,
        default=0,
        help="scheduler horizon in episodes; <=0 uses chunk_episodes if present, else max_episodes",
    )
    parser.add_argument(
        "--lr_restart_cycles",
        type=int,
        default=4,
        help="number of warm-restart cosine cycles within the scheduler horizon; <=1 disables restarts",
    )
    parser.add_argument(
        "--lr_warmup_ratio",
        type=float,
        default=0.10,
        help="fraction of each scheduler cycle spent linearly warming up actor/critic learning rates",
    )
    parser.add_argument(
        "--auto_lr_on_reward_patch",
        type=str2bool,
        default=False,
        help="automatically retune actor/critic LR bands after each accepted reward patch; OFF by "
             "default (2026-09-18) so iterations differ only in the reward — with it on, iter_002 and "
             "iter_005 of 20260917_120329 trained the SAME reward at x0.75/x0.70 LR and their tail fuel "
             "differed by 2.9%%, swamping the ~1%% effect of a reward change",
    )
    parser.add_argument(
        "--lr_auto_scale_floor",
        type=float,
        default=0.55,
        help="minimum LR scale factor relative to the initial run config allowed by auto LR tuning",
    )
    parser.add_argument(
        "--lr_auto_scale_ceiling",
        type=float,
        default=1.10,
        help="maximum LR scale factor relative to the initial run config allowed by auto LR tuning",
    )
    parser.add_argument(
        "--lr_auto_warmup_min",
        type=float,
        default=0.10,
        help="minimum warmup ratio allowed when auto LR tuning adjusts the scheduler",
    )
    parser.add_argument(
        "--lr_auto_warmup_max",
        type=float,
        default=0.20,
        help="maximum warmup ratio allowed when auto LR tuning adjusts the scheduler",
    )
    parser.add_argument(
        "--lr_auto_warmup_gain",
        type=float,
        default=0.10,
        help="extra warmup ratio added as LR scale factors are reduced by auto tuning",
    )

    # Device / seed
    parser.add_argument("--cuda", type=str2bool, default=True)
    parser.add_argument("--random_seed", type=str2bool, default=True)
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="explicit random seed; when set, overrides --random_seed",
    )

    # Loading prior checkpoint (optional)
    parser.add_argument("--load_or_not", type=str2bool, default=False)
    parser.add_argument("--load_episode", type=int, default=0)
    parser.add_argument("--load_scenario_name", type=str, default="")
    parser.add_argument("--load_dir", type=str, default="")

    # AROMA outer-loop
    parser.add_argument("--ldri_iterations", type=int, default=3,
                        help="baseline plus refinement rounds; each selected reward is fully trained")
    parser.add_argument("--refinement_protocol", choices=["sequential", "validated"], default="sequential",
                        help="sequential: one unrestricted proposal per round; validated: legacy candidate pool/pilot protocol")
    parser.add_argument("--proposal_attempts", type=int, default=10,
                        help="sequential only: total code-generation attempts, including repairs; no candidate pool")
    parser.add_argument("--cost_scale_max_ratio", type=float, default=1.0,
                        help="sequential only: replay the proposal on the baseline ep399 rollout and reject it when "
                             "its non-SOC objective (objective_cost - soc_cost) deviates from the operating cost at "
                             "the selection prices by more than this multiple of that cost (per-step mean |dev|); "
                             "multipliers on logged terms and extra terms count alike; soc_cost's own per-step "
                             "mean is bounded by the same multiple; <=0 disables")
    parser.add_argument("--fork_from_run_root", type=str, default="",
                        help="sequential only: start a new run whose iteration 1 is the measured baseline of this "
                             "earlier sequential run (no retraining). Allowed only when training conditions and "
                             "training-side code are identical; proposal-side code may differ")
    parser.add_argument("--artifact_detail", choices=["compact", "full"], default="compact",
                        help="sequential only: compact keeps metrics for every episode and raw artifacts for ep399 only")
    parser.add_argument("--scenario_validation", type=str2bool, default=True,
                        help="Required for validated adoption: frozen training-cycle scenarios on ep399; requires chunk_episodes=400, CS target=0.6")
    parser.add_argument("--cycle_segment_validation", type=str2bool, default=True,
                        help="Required for validated adoption: original-cycle ep399 segment comparisons; requires chunk_episodes=400")
    parser.add_argument("--baseline_reward_file", default="./agentEMS_val_base.py")
    parser.add_argument("--candidate_pool_size", type=int, default=3)
    parser.add_argument("--candidate_attempts", type=int, default=9)
    parser.add_argument("--pilot_episodes", type=int, default=100)
    parser.add_argument("--unreviewed_candidate_policy", choices=["record", "pilot_only", "block"], default="record",
                        help="Candidate whose four reviews were ALL withheld by the fact check: record = train as usual "
                             "but label the missing coverage; pilot_only = pilot but never promote to full training; "
                             "block = exclude from the pool")
    parser.add_argument("--confirmation_seeds", type=int, default=1,
                        help="final baseline comparison seed count: 1 uses --seed only (default); >1 also uses successive seeds")
    parser.add_argument("--confirmation_seed_list", type=int, nargs="*", default=[],
                        help="sequential only: seeds, disjoint from --seed, for post-search fresh paired "
                             "baseline-vs-final-reward training (L4). Frozen once given (run start or first "
                             "--run_confirmation); never fed back to the proposer")
    parser.add_argument("--run_confirmation", action="store_true",
                        help="sequential only: run L4 on a completed search (use with --resume_run_root). "
                             "Afterwards the search can no longer be extended, unless L4 was skipped "
                             "(no champion change, so no confirmation seed was trained)")
    parser.add_argument("--cost_max_fuel_increase", type=float, default=0.05,
                        help="sequential only: guard band, fixed before the search. A candidate's SOC-corrected "
                             "fuel may exceed the baseline's by at most this fraction (adoption is on total "
                             "operating cost)")
    parser.add_argument("--cost_max_batt_increase", type=float, default=0.10,
                        help="sequential only: guard band, fixed before the search. A candidate's battery SOH "
                             "loss may exceed the baseline's by at most this fraction, so FC wear cannot be "
                             "shifted onto the battery")
    parser.add_argument("--reward_term_catalog", type=str2bool, default=True,
                        help="sequential archive search only: proposals must add or reshape a REWARD TERM CATALOG "
                             "term (reward_terms.py), verified on probes and replay; False = free-form ablation")
    parser.add_argument("--cost_max_soc_drift", type=float, default=0.05,
                        help="sequential only: charge-sustaining guard, fixed before the search. The ep399 "
                             "rollout's |SOC_final - SOC_initial| (absolute SOC fraction) may be at most this, "
                             "so FC wear cannot be bought by idling the FC into the battery")
    parser.add_argument("--edit_base_max_stale", type=int, default=2,
                        help="sequential only: skip an archived edit base after this many consecutive children "
                             "that neither replaced the champion nor entered the Pareto front")
    parser.add_argument("--validation_min_improvement_gkm", type=float, default=0.0)
    parser.add_argument("--validation_min_improvement_fraction", type=float, default=0.001,
                        help="validated only: required fuel reduction >= max(absolute margin, abs(control fuel)*fraction), with strictly lower fuel; default 0.1%%")
    parser.add_argument("--validation_terminal_soc_error", type=float, default=0.02,
                        help="Charge-sustaining TARGET for original-cycle final target error and SOC drift; "
                             "recorded in targets, never blocking. Blocking uses the run baseline as reference")
    parser.add_argument("--validation_scenario_soc_error", type=float, default=0.02,
                        help="Charge-sustaining TARGET for scenario final target error and low-SOC observation-half "
                             "mean error; recorded in targets, never blocking")
    parser.add_argument("--validation_unaccepted_energy_kwh", type=float, default=0.0,
                        help="Unaccepted power residual energy TARGET; recorded, never blocking")
    parser.add_argument("--validation_unaccepted_peak_kw", type=float, default=0.0,
                        help="Unaccepted power residual peak TARGET; recorded, never blocking")
    parser.add_argument("--validation_unaccepted_peak_slack_kw", type=float, default=0.5,
                        help="Blocking allowance above the run baseline's unaccepted power peak (seed-independent)")
    parser.add_argument("--validation_unaccepted_energy_slack_kwh", type=float, default=0.001,
                        help="Blocking allowance above the run baseline's unaccepted residual energy (seed-independent)")
    parser.add_argument("--validation_condition_soc_tolerance", type=float, default=0.005,
                        help="Maximum increase in matched group/scenario SOC target error (SOC fraction)")
    parser.add_argument("--validation_condition_fuel_regression", type=float, default=0.05,
                        help="Maximum matched group/scenario fuel increase fraction, with fixed small absolute tolerances")
    parser.add_argument("--validation_max_degradation_ratio", type=float, default=2.0,
                        help="maximum physical FC and battery SOH loss ratio, each relative to paired control (pilot and full; default: 2.0)")
    parser.add_argument("--validation_min_in_bounds", type=float, default=98.0)
    parser.add_argument(
        "--resume_run_root",
        type=str,
        default="",
        help="existing AROMA run root to resume; append iterations in-place",
    )
    parser.add_argument(
        "--resume_additional_iterations",
        type=int,
        default=0,
        help="extra iterations to run when resuming (if >0, overrides --ldri_iterations target)",
    )
    parser.add_argument(
        "--resume_use_saved_config",
        type=str2bool,
        default=True,
        help="when resuming, reuse run_config.json values to keep the original run conditions",
    )
    parser.add_argument(
        "--seed_chunk_dir",
        type=str,
        default="",
        help=(
            "existing training run dir (train_log.log, episode_data/, net_params/) used AS "
            "iteration 1: no scratch bootstrap, no retraining. Requires --seed_reward_file "
            "(e.g. the baseline SAC run + aroma/agentEMS_val_base.py)"
        ),
    )
    parser.add_argument(
        "--seed_reward_file",
        type=str,
        default="",
        help="module file whose EMS.get_reward trained --seed_chunk_dir; patched into --reward_file",
    )
    parser.add_argument("--chunk_episodes", type=int, default=400)
    parser.add_argument("--feedback_process_episodes", type=int, default=50)
    parser.add_argument(
        "--reset_agent_on_patch",
        type=str2bool,
        default=True,
        help="reset RL model parameters/optimizers after each successful reward patch",
    )

    # Reward module and prompt template
    parser.add_argument("--reward_module", type=str, default="agentEMS_for_feedback")
    parser.add_argument("--reward_file", type=str, default="./agentEMS_for_feedback.py")

    # LLM client
    parser.add_argument(
        "--agent_type",
        type=str,
        default="",
        choices=get_agent_type_choices(),
        help=(
            "optional preset shortcut for the LLM stack; applies only when "
            "--llm_provider/--llm_model/--llm_api_key_env are not explicitly set"
        ),
    )
    parser.add_argument(
        "--llm_provider",
        type=str,
        default="",
        choices=["openai", "anthropic", "huggingface"],
    )
    parser.add_argument("--llm_model", type=str, default="")
    parser.add_argument("--llm_api_key", type=str, default=None)
    parser.add_argument("--llm_api_key_env", type=str, default="")
    parser.add_argument("--llm_temperature", type=float, default=0.2)
    parser.add_argument("--llm_max_tokens", type=int, default=7000)
    parser.add_argument("--llm_timeout_sec", type=int, default=240)
    parser.add_argument("--skip_llm", action="store_true")
    parser.add_argument("--skip_patch", action="store_true")
    parser.add_argument(
        "--multi_agent_review",
        type=str2bool,
        default=True,
        help=(
            "sequential: 4 compact specialist reviews, combined mediation/orchestration and one proposal; "
            "False requests one direct proposal. validated always uses its full review pipeline"
        ),
    )
    parser.add_argument(
        "--debate_rounds",
        type=int,
        default=1,
        help=(
            "number of reviewer debate rounds; 1=round 0 only (no rebuttal), "
            "2=one rebuttal round for fuel_soc/battery_degradation/fc_durability"
            " (MAD-style peer rebuttal, bidirectional Condition 1)"
        ),
    )

    # Bootstrap (scratch reward generation before first training chunk)
    # Aligned gate parameters
    parser.add_argument(
        "--parse_retries",
        type=int,
        default=10,
        help="extra retries reserved for parse failures before giving up",
    )
    parser.add_argument("--tpe_retries", type=int, default=20)
    parser.add_argument(
        "--tpe_soc_in_bounds_floor",
        type=float,
        default=98.0,
        help="minimum in_bounds_rate(%%) required when selecting both preferred and dispreferred episodes for TPE",
    )
    parser.add_argument(
        "--tpe_fp_pool_size",
        type=int,
        default=6,
        help="reward_lr_tuner (--auto_lr_on_reward_patch): feasible-episode pool size",
    )
    parser.add_argument(
        "--tpe_fp_topk",
        type=int,
        default=2,
        help="reward_lr_tuner (--auto_lr_on_reward_patch): number of top feasible episodes",
    )
    parser.add_argument(
        "--tpe_fp_bottomk",
        type=int,
        default=2,
        help="reward_lr_tuner (--auto_lr_on_reward_patch): number of bottom feasible episodes",
    )

    # Two-layer aligned gate
    parser.add_argument(
        "--aligned_min_tac",
        type=float,
        default=0.12,
        help=("diagnostic-only Kendall tau reference threshold; TAC never blocks a "
              "reward candidate. Candidate acceptance uses structural checks only"),
    )
    parser.add_argument(
        "--aligned_w_fcs_gt",
        type=float,
        default=0.5,
        help=(
            "aligned gate layer 1: weight of FC-stack SOH-loss rank in the physical "
            "ground truth (secondary co-objective; fuel stays primary at 1.0). 0 = exclude"
        ),
    )
    parser.add_argument(
        "--aligned_w_batt_gt",
        type=float,
        default=0.5,
        help=(
            "aligned gate layer 1: weight of battery SOH-loss rank in the physical "
            "ground truth (secondary co-objective). 0 = exclude"
        ),
    )
    parser.add_argument(
        "--aligned_tac_tail_fraction",
        type=float,
        default=0.1,
        help=(
            "aligned gate layer 1 episode window: the last fraction of the chunk (min 3 "
            "episodes) = the converged policy. Also the tail window of the review packet's "
            "SOC stats / diagnostic oob_rate. The old in_bounds>=floor pool picked "
            "early-exploration episodes (2026-09-16)"
        ),
    )
    parser.add_argument(
        "--aligned_dominance_threshold",
        type=float,
        default=0.95,  # keep in sync with ldri_aligned_gate._DEFAULTS["dominance_threshold"]
        help=(
            "aligned gate layer 2: no single cost term may contribute more than "
            "this fraction of the mean objective_cost"
        ),
    )
    parser.add_argument(
        "--aligned_soc_dominance_threshold",
        type=float,
        default=0.85,
        help=(
            "aligned gate layer 2: soc_cost may not contribute more than "
            "this fraction of the mean objective_cost"
        ),
    )
    parser.add_argument(
        "--aligned_min_h2_fraction",
        type=float,
        default=0.25,
        help=(
            "aligned gate layer 2: h2_cost must contribute at least this "
            "fraction of the mean objective_cost"
        ),
    )
    parser.add_argument(
        "--aligned_h2_perturbation_ratio",
        type=float,
        default=0.2,
        help="aligned gate layer 2: h2_fcs perturbation ratio for monotonicity check",
    )
    parser.add_argument("--aligned_mt_envelope_quantile", type=float, default=0.01,
        help="layer 2 (metamorphic): per-variable [q, 1-q] quantile box for the reachable state space")
    parser.add_argument("--aligned_mt_seed", type=int, default=0,
        help="layer 2 (metamorphic): RNG seed for reproducible falsification search")
    parser.add_argument("--aligned_mt_sobol", type=int, default=2048,
        help="layer 2 (metamorphic): Sobol coverage samples per relation")
    parser.add_argument("--aligned_mt_top_k", type=int, default=5,
        help="layer 2 (metamorphic): top-k Sobol seeds refined with Nelder-Mead")
    parser.add_argument("--aligned_mt_de_maxiter", type=int, default=60,
        help="layer 2 (metamorphic): differential_evolution maxiter (global search)")
    parser.add_argument("--aligned_mt_de_popsize", type=int, default=15,
        help="layer 2 (metamorphic): differential_evolution popsize")
    parser.add_argument("--aligned_mt_eps_up", type=float, default=0.01,
        help="layer 2 (metamorphic): up-check tolerance; a monotone MR is violated if reward RISES by more than this (normalized) when the cause increases")
    parser.add_argument("--aligned_mt_min_sensitivity_h2", type=float, default=0.5,
        help="layer 2 (metamorphic): MR-H2 sensitivity - a full-range h2_fcs increase must drop reward by >= this (normalized). Calibrated for WVUINTER/w_soc=100/CS (baseline margin ~2.5-3.3); recompute if scenario/weights change")
    parser.add_argument("--aligned_mt_min_sensitivity_fcs", type=float, default=0.25,
        help="layer 2 (metamorphic): MR-FCS sensitivity - a full-range dSOH_FCS increase must drop reward by >= this (normalized). Calibrated for WVUINTER/w_soc=100/CS (baseline margin ~0.7-1.6)")
    parser.add_argument("--aligned_mt_min_sensitivity_batt", type=float, default=0.1,
        help="layer 2 (metamorphic): MR-BATT sensitivity - a full-range dSOH_batt increase must drop reward by >= this (normalized). Lower than FCS because w_batt < w_fc (battery is the binding term; baseline margin ~0.28-0.58, tightest headroom)")
    parser.add_argument("--aligned_mt_min_sensitivity_soc", type=float, default=0.2,
        help="layer 2 (metamorphic): MR-SOC min normalized reward gap between an out-of-bounds SOC and SOC_target (baseline margin ~0.7-1.5). Coupled with --aligned_mt_soc_oob_offset: the gap is measured at that OOB distance, NOT at the boundary knife-edge (where a wide-deadband reward's gap decays to ~0 and false-fails)")
    parser.add_argument("--aligned_mt_soc_oob_offset", type=float, default=0.05,
        help="layer 2 (metamorphic): MR-SOC certifies the OOB barrier at this distance beyond soc_low/soc_high (default 0.05 ~= the k_oob term's working range). Probing nearer the boundary is a false positive for any continuous reward and creates a TAC<->MR-SOC deadlock; raise toward 0.07 if scale is large, lower toward 0.03 for a stricter near-boundary check")
    parser.add_argument("--soc_low", type=float, default=0.4)
    parser.add_argument("--soc_high", type=float, default=0.8)

    # Output roots (separate from baseline)
    parser.add_argument("--ldri_root", type=str, default="./ldri_runs")
    parser.add_argument("--file_v", type=str, default="v_ldri")

    args = parser.parse_args()

    provider_default_model = {
        "openai": "gpt-5.2",
        "anthropic": "claude-sonnet-4-6",
        "huggingface": "meta-llama/Llama-3.1-70B-Instruct",
    }
    provider_default_api_env = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "huggingface": "HF_TOKEN",
    }

    if args.agent_type and not any([args.llm_provider, args.llm_model, args.llm_api_key_env]):
        preset = get_agent_preset(args.agent_type)
        args.llm_provider = preset.provider
        args.llm_model = preset.model
        args.llm_api_key_env = preset.api_key_env

    if not args.llm_provider:
        args.llm_provider = "openai"
    if not args.llm_model:
        args.llm_model = provider_default_model[args.llm_provider]
    if not args.llm_api_key_env:
        args.llm_api_key_env = provider_default_api_env[args.llm_provider]

    return args
