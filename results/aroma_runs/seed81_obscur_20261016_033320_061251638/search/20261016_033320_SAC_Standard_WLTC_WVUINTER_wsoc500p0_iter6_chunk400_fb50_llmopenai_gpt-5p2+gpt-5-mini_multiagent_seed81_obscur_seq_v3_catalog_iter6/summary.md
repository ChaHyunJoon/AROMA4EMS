# AROMA sequential v3 (total operating cost)

AROMA is multi-objective energy management whose goal is the total operating cost of the drive: hydrogen cost + FC degradation cost + battery degradation cost, in USD per 100 km at fixed prices (context.cost_model). The core levers are FC degradation and FC hydrogen consumption: FC wear is usually the largest share of the total, so a policy that burns slightly more hydrogen but wears the FC much less can win. Adoption: total operating cost MUST be strictly below the standing champion's. Guard bands, fixed in advance (context.cost_model.guards): CHARGE SUSTAINING, |SOC_final - SOC_initial| of the ep399 rollout at most soc_drift_abs_max (absolute, the same for every seed, so a baseline that drifts further does not loosen it); SOC-corrected equivalent hydrogen at most the baseline's times (1 + max fuel increase); and battery SOH loss at most the baseline's times (1 + max battery increase), so FC wear cannot be bought by charging the battery with idling FC power, by shifting load onto the battery or by unbounded hydrogen. FC SOH loss has no cap of its own; it is priced in the total. The search keeps the Pareto front of total cost versus SOC-corrected fuel among guard-feasible rewards; the champion is its lowest-cost point, and a reward that is cheaper but fails a guard is kept as a repair target. A tie in total cost is rejected. Compare final ep399 policies at the same seed, cycle, initial state and 400-episode training budget. Tail statistics are diagnostics. Keep physical tracking feasible and SOC within the specified operating band. Reward coefficients and cost shares are not measurements of policy performance. State causal explanations as hypotheses; actual post-training measurements decide adoption.

Status: completed

Costs in USD per 100 km (operating_cost.py, same prices as paper_figs_multi_seed.ipynb).

| Iteration | Edit mode | Parent | Decision | vs champion | Total cost | H2 cost | FC cost | Battery cost | g/km (ep399) | raw H2 g/km | SOC corr. g/km | ΔSOC final | FC SOH loss | Battery SOH loss |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | — | — | baseline_trained | — | 35.92 | 7.587 | 23.51 | 4.827 | 10.838062644164271 | 11.02 | -0.1774 | 0.09339 | 0.00018646449997072878 | 0.0006140980938273977 |
| 2 | champion_improve | 17afbf80420c | retain_champion | objective_tradeoff | 94.76 | 7.163 | 84.68 | 2.917 | 10.233475032847547 | 10.17 | 0.05948 | -0.03174 | 0.0006716709999863291 | 0.0003711232379242091 |
| 3 | fuel_leader | efd23e530135 | retain_champion | objective_tradeoff | 158.7 | 7.151 | 149.1 | 2.524 | 10.21571403460258 | 10.15 | 0.06797 | -0.03607 | 0.0011823484999878842 | 0.0003211765847781489 |
| 4 | champion_improve | 17afbf80420c | retain_champion | objective_tradeoff | 37.38 | 7.656 | 25.85 | 3.873 | 10.937016204169574 | 10.99 | -0.04953 | 0.02585 | 0.00020503649995406992 | 0.0004926985658025851 |
| 5 | champion_improve | 17afbf80420c | retain_champion | objective_tradeoff | 41.08 | 7.311 | 29.93 | 3.836 | 10.444853555713188 | 10.37 | 0.07338 | -0.03888 | 0.00023739599998018335 | 0.00048805745747959595 |
| 6 | fuel_leader | 12d8a917f37b | retain_champion | objective_tradeoff | 37.62 | 7.427 | 26.3 | 3.887 | 10.610099680912068 | 10.62 | -0.005769 | 0.003017 | 0.0002086304999756594 | 0.00049456609334253 |

Champion: 17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083

Each iter_NNN/summary.md explains the measured decision. Raw artifacts live under trials/.
Compact mode retains all scalar evaluation records but only the final raw policy/trajectory.

## Deployment (L1/L6)
Total operating cost below baseline with SOC drift, fuel and battery inside the guards: **False**
Claim: no verified improvement; baseline deployed
[Final reward](results/aroma_runs/seed81_obscur_20261016_033320_061251638/search/20261016_033320_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed81_obscur_seq_v3_catalog_iter6/final_reward.py)
[Final ep399 actor](results/aroma_runs/seed81_obscur_20261016_033320_061251638/search/20261016_033320_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed81_obscur_seq_v3_catalog_iter6/trials/725382d53b1c924408c894ad/models/iter_001/Standard_WLTC_WVUINTER/net_params/actor_iter001_ep399.pkl)

## Reward confirmation (L4)
Status: not_run
Reason: separate step: --resume_run_root <run> --run_confirmation [--confirmation_seed_list ...]

No unseen-cycle generalization is claimed.

Compute: {"trained_episodes": 2400, "llm_calls": 30, "reported_tokens": 771205, "note": "Persisted trials and reported usage only; interrupted work or missing provider usage may be absent."}
