# AROMA sequential v3 (total operating cost)

AROMA is multi-objective energy management whose goal is the total operating cost of the drive: hydrogen cost + FC degradation cost + battery degradation cost, in USD per 100 km at fixed prices (context.cost_model). The core levers are FC degradation and FC hydrogen consumption: FC wear is usually the largest share of the total, so a policy that burns slightly more hydrogen but wears the FC much less can win. Adoption: total operating cost MUST be strictly below the standing champion's. Guard bands, fixed in advance (context.cost_model.guards): CHARGE SUSTAINING, |SOC_final - SOC_initial| of the ep399 rollout at most soc_drift_abs_max (absolute, the same for every seed, so a baseline that drifts further does not loosen it); SOC-corrected equivalent hydrogen at most the baseline's times (1 + max fuel increase); and battery SOH loss at most the baseline's times (1 + max battery increase), so FC wear cannot be bought by charging the battery with idling FC power, by shifting load onto the battery or by unbounded hydrogen. FC SOH loss has no cap of its own; it is priced in the total. The search keeps the Pareto front of total cost versus SOC-corrected fuel among guard-feasible rewards; the champion is its lowest-cost point, and a reward that is cheaper but fails a guard is kept as a repair target. A tie in total cost is rejected. Compare final ep399 policies at the same seed, cycle, initial state and 400-episode training budget. Tail statistics are diagnostics. Keep physical tracking feasible and SOC within the specified operating band. Reward coefficients and cost shares are not measurements of policy performance. State causal explanations as hypotheses; actual post-training measurements decide adoption.

Status: completed

Costs in USD per 100 km (operating_cost.py, same prices as paper_figs_multi_seed.ipynb).

| Iteration | Edit mode | Parent | Decision | vs champion | Total cost | H2 cost | FC cost | Battery cost | g/km (ep399) | raw H2 g/km | SOC corr. g/km | ΔSOC final | FC SOH loss | Battery SOH loss |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | — | — | baseline_trained | — | 40.41 | 7.459 | 28.69 | 4.266 | 10.6562854090602 | 10.67 | -0.01748 | 0.009211 | 0.00022755816664343786 | 0.0005426791354884442 |
| 2 | champion_improve | 17afbf80420c | retain_champion | objective_tradeoff | 88.55 | 7.135 | 77.32 | 4.089 | 10.192362440466646 | 10.05 | 0.1392 | -0.07542 | 0.0006133604999949416 | 0.0005202309104312963 |
| 3 | fuel_leader | 17afbf80420c | replace_champion | strict_pareto | 28.97 | 7.415 | 17.89 | 3.66 | 10.592957563806065 | 10.55 | 0.04275 | -0.02235 | 0.00014194499997055576 | 0.0004656390750389372 |
| 4 | champion_improve | 9a1a00b2da2f | retain_champion | worse_or_equal | 41.99 | 7.765 | 29.26 | 4.956 | 11.093128412725012 | 11.26 | -0.1706 | 0.08818 | 0.00023213549995659832 | 0.0006305576218159636 |
| 5 | champion_improve | 9a1a00b2da2f | retain_champion | objective_tradeoff | 39.3 | 7.39 | 28.54 | 3.372 | 10.556665388962326 | 10.62 | -0.06478 | 0.03484 | 0.0002264129999761666 | 0.00042894649844260613 |
| 6 | fuel_leader | 187b8f1ea4ae | retain_champion | objective_tradeoff | 45.78 | 7.54 | 34.8 | 3.436 | 10.771970924700257 | 10.84 | -0.07121 | 0.03697 | 0.0002760774999639448 | 0.0004370954060959331 |

Champion: 9a1a00b2da2f4836b7563a0ad13593c767d8ae9618ae004902187c2068ca2d83

Each iter_NNN/summary.md explains the measured decision. Raw artifacts live under trials/.
Compact mode retains all scalar evaluation records but only the final raw policy/trajectory.

## Deployment (L1/L6)
Total operating cost below baseline with SOC drift, fuel and battery inside the guards: **True**
Claim: lower total operating cost of the ep399 actor at the search seed/cycle/initial state
[Final reward](results/aroma_runs/seed1_obscur_20261018_061824_704722118/search/20261018_061824_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed1_obscur_seq_v3_catalog_iter6/final_reward.py)
[Final ep399 actor](results/aroma_runs/seed1_obscur_20261018_061824_704722118/search/20261018_061824_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/f10ea050f7c8decfbe311dc2/models/iter_001/Standard_WLTC_WVUINTER/net_params/actor_iter001_ep399.pkl)

## Reward confirmation (L4)
Status: not_run
Reason: separate step: --resume_run_root <run> --run_confirmation [--confirmation_seed_list ...]

No unseen-cycle generalization is claimed.

Compute: {"trained_episodes": 2400, "llm_calls": 30, "reported_tokens": 770247, "note": "Persisted trials and reported usage only; interrupted work or missing provider usage may be absent."}
