# AROMA sequential v3 (total operating cost)

AROMA is multi-objective energy management whose goal is the total operating cost of the drive: hydrogen cost + FC degradation cost + battery degradation cost, in USD per 100 km at fixed prices (context.cost_model). The core levers are FC degradation and FC hydrogen consumption: FC wear is usually the largest share of the total, so a policy that burns slightly more hydrogen but wears the FC much less can win. Adoption: total operating cost MUST be strictly below the standing champion's. Guard bands, fixed in advance (context.cost_model.guards): CHARGE SUSTAINING, |SOC_final - SOC_initial| of the ep399 rollout at most soc_drift_abs_max (absolute, the same for every seed, so a baseline that drifts further does not loosen it); SOC-corrected equivalent hydrogen at most the baseline's times (1 + max fuel increase); and battery SOH loss at most the baseline's times (1 + max battery increase), so FC wear cannot be bought by charging the battery with idling FC power, by shifting load onto the battery or by unbounded hydrogen. FC SOH loss has no cap of its own; it is priced in the total. The search keeps the Pareto front of total cost versus SOC-corrected fuel among guard-feasible rewards; the champion is its lowest-cost point, and a reward that is cheaper but fails a guard is kept as a repair target. A tie in total cost is rejected. Compare final ep399 policies at the same seed, cycle, initial state and 400-episode training budget. Tail statistics are diagnostics. Keep physical tracking feasible and SOC within the specified operating band. Reward coefficients and cost shares are not measurements of policy performance. State causal explanations as hypotheses; actual post-training measurements decide adoption.

Status: completed

Costs in USD per 100 km (operating_cost.py, same prices as paper_figs_multi_seed.ipynb).

| Iteration | Edit mode | Parent | Decision | vs champion | Total cost | H2 cost | FC cost | Battery cost | g/km (ep399) | raw H2 g/km | SOC corr. g/km | ΔSOC final | FC SOH loss | Battery SOH loss |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | — | — | baseline_trained | — | 52.94 | 7.887 | 40.52 | 4.524 | 11.267763405434842 | 11.63 | -0.364 | 0.1848 | 0.000321448999946794 | 0.0005755324677042539 |
| 2 | champion_improve | 17afbf80420c | retain_champion | strict_pareto | 50.12 | 7.662 | 38.2 | 4.255 | 10.945460379927066 | 11.05 | -0.1048 | 0.05386 | 0.00030301949995370503 | 0.0005413132853631097 |
| 3 | fuel_leader | 17afbf80420c | retain_champion | objective_tradeoff | 109.7 | 7.185 | 99.81 | 2.745 | 10.264358920782193 | 10.13 | 0.1327 | -0.07048 | 0.0007917584999849181 | 0.0003492498453881998 |
| 4 | guard_repair | fd453666c825 | retain_champion | objective_tradeoff | 152.6 | 7.377 | 142.3 | 2.952 | 10.538606940147615 | 10.5 | 0.0345 | -0.01792 | 0.001128436499971297 | 0.00037557828829659634 |
| 5 | champion_improve | 17afbf80420c | replace_champion | strict_pareto | 42.03 | 7.586 | 30.61 | 3.83 | 10.837797361445341 | 10.92 | -0.08108 | 0.04182 | 0.00024280549995714384 | 0.00048721737274892707 |
| 6 | fuel_leader | 433d2659d7a7 | retain_champion | objective_tradeoff | 164 | 7.354 | 153.8 | 2.93 | 10.505381412651984 | 10.5 | 0.007211 | -0.003775 | 0.001219710499973936 | 0.0003727963674051704 |

Champion: 59716618abe00b79a7d6c2b4128d01833745357099ab208a400a9c9d1edbcd57

Each iter_NNN/summary.md explains the measured decision. Raw artifacts live under trials/.
Compact mode retains all scalar evaluation records but only the final raw policy/trajectory.

## Deployment (L1/L6)
Total operating cost below baseline with SOC drift, fuel and battery inside the guards: **True**
Claim: lower total operating cost of the ep399 actor at the search seed/cycle/initial state
[Final reward](results/aroma_runs/seed41_obscur_20261016_033309_216122644/search/20261016_033309_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed41_obscur_seq_v3_catalog_iter6/final_reward.py)
[Final ep399 actor](results/aroma_runs/seed41_obscur_20261016_033309_216122644/search/20261016_033309_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed41_obscur_seq_v3_catalog_iter6/trials/357a0010ebb1cb54c7173bfe/models/iter_001/Standard_WLTC_WVUINTER/net_params/actor_iter001_ep399.pkl)

## Reward confirmation (L4)
Status: not_run
Reason: separate step: --resume_run_root <run> --run_confirmation [--confirmation_seed_list ...]

No unseen-cycle generalization is claimed.

Compute: {"trained_episodes": 2400, "llm_calls": 30, "reported_tokens": 762994, "note": "Persisted trials and reported usage only; interrupted work or missing provider usage may be absent."}
