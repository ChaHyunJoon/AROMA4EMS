import argparse

def get_args():
    parser = argparse.ArgumentParser("Soft Actor Critic Implementation")
    # Environment
    parser.add_argument("--max_episodes", type=int, default=400, help="number of episodes ")
    parser.add_argument("--start_episode", type=int, default=0,
                        help="starting episode index for continued training")
    parser.add_argument("--episode_steps", type=int, default=None, help="number of time steps in a single episode")
    # Core training parameters
    parser.add_argument("--lr_critic", type=float, default=1.5e-4)
    parser.add_argument("--lr_critic_min", type=float, default=5e-5)
    parser.add_argument("--lr_actor", type=float, default=5e-5)
    parser.add_argument("--lr_actor_min", type=float, default=5e-6)
    parser.add_argument("--lr_alpha", type=float, default=2.5e-4, help="peak learning rate of alpha (cosine-decayed to lr_alpha_min)")
    parser.add_argument("--lr_alpha_min", type=float, default=5e-5, help="floor learning rate of alpha; alpha LR follows the same cosine schedule as critic/actor")
    parser.add_argument(
        "--lr_warmup_ratio",
        type=float,
        default=0.0,
        help="fraction of the cosine cycle spent warming up from min_lr to max_lr; 0 disables warmup (LR starts at peak and only decays)",
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
        default=1,
        help="number of warm-restart cosine cycles within the scheduler horizon; <=1 disables restarts",
    )
    parser.add_argument(
        "--const_lr",
        action="store_true",
        help="bypass the cosine LR schedulers entirely and train actor/critic/alpha at constant "
             "lr_actor/lr_critic/lr_alpha (standard SAC baseline). lr_*_min and warmup/restart args are ignored.",
    )
    parser.add_argument("--gamma", type=float, default=0.995,
                        help="discount factor. 1s 스텝이라 0.99 는 유효지평 ~100초로 부하 평준화"
                             "(수백 초 스케일)에 대해 근시안적이다. 0.995 = ~200초.")
    parser.add_argument('--alpha', type=float, default=1.0,
                        help='Temperature parameter α determines the relative importance of the entropy term against the reward')
    parser.add_argument('--auto_tune', type=bool, default=True)
    parser.add_argument('--target_entropy_scale', type=float, default=1.0,
                        help='multiplier on the SAC target entropy (-action_dim * scale); '
                             '2.0 makes the target more negative -> sharper/less-exploratory policy')
    parser.add_argument('--critic_layernorm', action='store_true',
                        help='insert LayerNorm (Linear->LayerNorm->ReLU) in the Q-network hidden layers '
                             'to stabilize critic learning (recommended)')
    parser.add_argument('--actor_layernorm', action='store_true',
                        help='insert LayerNorm in the Gaussian policy hidden layers (optional; '
                             'critic_layernorm is usually the higher-value one)')
    parser.add_argument("--tau", type=float, default=0.005, help="parameter for updating the target network")
    parser.add_argument("--policy_delay", type=int, default=1, help="TD3-style delayed policy updates: actor/temperature updated every N critic updates (1 = standard SAC)")
    # memory buffer
    parser.add_argument("--buffer_size", type=int, default=int(1e6),
                        help="number of transitions can be stored in buffer")
    # 200ep: 3e4 for CLTCP_WVUSUB_WVUINTER,  1e4 for WVUCITY_HWFET
    parser.add_argument("--batch_size", type=int, default=256, help="number of episodes to optimize at the same time")
    # Prioritized Experience Replay (Schaul et al., ICLR 2016), proportional variant
    parser.add_argument("--per", action="store_true",
                        help="uniform replay 대신 PER 사용. p_i = (|TD_i|+eps)^per_alpha, "
                             "IS weight 로 편향 보정")
    parser.add_argument("--per_alpha", type=float, default=0.6,
                        help="우선순위 지수. 0 = uniform, 1 = 완전 비례")
    parser.add_argument("--per_beta0", type=float, default=0.4,
                        help="IS weight 지수의 시작값 (per_beta_steps 동안 1.0 으로 annealing)")
    parser.add_argument("--per_beta_steps", type=int, default=0,
                        help="beta annealing 스텝 수. <=0 이면 beta=1.0 고정. "
                             "보통 max_episodes*episode_steps 로 준다")
    parser.add_argument("--per_eps", type=float, default=1e-6,
                        help="TD 오차가 0 인 transition 도 뽑힐 수 있게 하는 하한")
    # random seeds
    parser.add_argument("--random_seed", type=bool, default=True)
    parser.add_argument("--seed", type=int, default=None,
                        help="explicit random seed; when set, overrides --random_seed")
    # device
    parser.add_argument("--cuda", type=bool, default=True, help="True for GPU, False for CPU")
    # method
    parser.add_argument("--DRL", type=str, default='SAC', choices=['SAC'], help="training method")
    # for SAC
    parser.add_argument("--policy", type=str, default='Gaussian', choices=['Gaussian', 'Beta'],
                        help="policy type. Beta 는 [0,1] 유계 support 라 경계 행동(FC off / 최대출력)이 "
                             "억제되지 않는다(Chou et al., ICML 2017). 체크포인트는 Gaussian 과 호환되지 않음.")
    # for DP
    parser.add_argument("--soc_tol", type=float, default=0.0, help="terminal SOC tolerance")
    parser.add_argument("--w_terminal", type=float, default=1e6, help="terminal SOC penalty weight")
    parser.add_argument(
        "--dp_soc_chunk_size",
        type=int,
        default=128,
        help="SOC chunk size for 2D DP backward recursion; larger is faster but uses more RAM",
    )
    parser.add_argument(
        "--dp_prev_fc_state_count",
        type=int,
        default=0,
        help="number of previous-FC-power states for 2D DP; <=0 uses the full action-matched grid",
    )
    # about EMS, weight coefficient
    parser.add_argument("--w_soc", type=float, default=200.0, help="weight coefficient for SOC reward")
    parser.add_argument("--failure_cost_per_step", type=float, default=1000.0,
                        help="Absorbing failure cost per remaining discounted step; applied outside the EMS reward")
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
    parser.add_argument(
        "--eq_h2_batt_coef",
        type=float,
        default=0.0164,
        help="battery power to equivalent hydrogen coefficient: h2_batt = P_batt / 1000 * coef",
    )
    parser.add_argument(
        "--ramp_limit_kw",
        type=float,
        default=0.0,
        help="0: absolute FC power. >0: normalized FC increment dP/ramp and physical ramp limit. "
             "Fresh SAC policies restrict increments to [-min(ramp,P_FC), min(ramp,P_max-P_FC)]. "
             "Existing actor checkpoints preserve their saved action mapping.",
    )
    parser.add_argument("--soc0", type=float, default=0.6, help="initial value of SOC")
    parser.add_argument("--soc_target", type=float, default=0.6, help="terminal SOC target for DP")
    parser.add_argument("--MODE", type=str, default='CS', help="CS or CD, charge-sustain or charge-depletion")
    # save model under training     # Standard_ChinaCity  Standard_IM240
    parser.add_argument("--scenario_name", type=str, default="CLTC_P_plus_Standard_WVUINTER",
                        help="name of driving cycle data")
    # CLTC_P  Standard_ChinaCity, CLTCP_WVUSUB_WVUINTER, WVUCITY_HWFET, CLTCP_WVUINTER
    parser.add_argument("--save_dir", type=str, default="./test5", help="directory in which saves training data and model")
    parser.add_argument("--log_dir", type=str, default="./logs5", help="directory in which saves logs")
    parser.add_argument("--file_v", type=str, default='v1', help="version of driving cycle data file")
    # load learned model to train new model or evaluate
    parser.add_argument("--load_or_not", type=bool, default=True)
    parser.add_argument("--load_episode", type=int, default=397)
    parser.add_argument("--load_scenario_name", type=str, default="CLTCP_WVUINTER_w100_LR1e-03_v1")
    parser.add_argument("--load_dir", type=str, default="test2_SAC_CS_Gaussian")
    # evaluate
    parser.add_argument("--evaluate", type=bool, default=False)
    parser.add_argument("--evaluate_episode", type=int, default=1)
    parser.add_argument("--eval_stochastic", type=bool, default=False,
                        help="if True, sample stochastic actions during evaluation")
    parser.add_argument(
        "--eval_iter",
        type=str,
        default="",
        help="optional AROMA iteration tag for evaluation output grouping (e.g., 1, 003, iter_003)",
    )
    parser.add_argument("--eva_dir", type=str, default="./eva")
    # checkpointing
    parser.add_argument("--save_best", type=bool, default=True, help="save best-performing episode checkpoint")
    parser.add_argument("--eval_interval", type=int, default=1,
                        help="run a deterministic (mean-action) eval rollout every N episodes to score the policy for best-checkpoint selection")
    # all above
    args = parser.parse_args()
    return args
    
