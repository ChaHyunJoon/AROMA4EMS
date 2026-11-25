# AROMA sequential v3 (total operating cost)

AROMA is multi-objective energy management whose goal is the total operating cost of the drive: hydrogen cost + FC degradation cost + battery degradation cost, in USD per 100 km at fixed prices (context.cost_model). The core levers are FC degradation and FC hydrogen consumption: FC wear is usually the largest share of the total, so a policy that burns slightly more hydrogen but wears the FC much less can win. Adoption: total operating cost MUST be strictly below the standing champion's. Guard bands, fixed in advance (context.cost_model.guards): CHARGE SUSTAINING, |SOC_final - SOC_initial| of the ep399 rollout at most soc_drift_abs_max (absolute, the same for every seed, so a baseline that drifts further does not loosen it); SOC-corrected equivalent hydrogen at most the baseline's times (1 + max fuel increase); and battery SOH loss at most the baseline's times (1 + max battery increase), so FC wear cannot be bought by charging the battery with idling FC power, by shifting load onto the battery or by unbounded hydrogen. FC SOH loss has no cap of its own; it is priced in the total. The search keeps the Pareto front of total cost versus SOC-corrected fuel among guard-feasible rewards; the champion is its lowest-cost point, and a reward that is cheaper but fails a guard is kept as a repair target. A tie in total cost is rejected. Compare final ep399 policies at the same seed, cycle, initial state and 400-episode training budget. Tail statistics are diagnostics. Keep physical tracking feasible and SOC within the specified operating band. Reward coefficients and cost shares are not measurements of policy performance. State causal explanations as hypotheses; actual post-training measurements decide adoption.

Status: completed

Costs in USD per 100 km (operating_cost.py, same prices as paper_figs_multi_seed.ipynb).

| Iteration | Edit mode | Parent | Decision | vs champion | Total cost | H2 cost | FC cost | Battery cost | g/km (ep399) | raw H2 g/km | SOC corr. g/km | ΔSOC final | FC SOH loss | Battery SOH loss |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | — | — | baseline_trained | — | 73.16 | 7.258 | 62.15 | 3.758 | 10.368679466188617 | 10.35 | 0.01796 | -0.009605 | 0.0004929689999854103 | 0.00047805274582957136 |
| 2 | champion_improve | 17afbf80420c | replace_champion | cost_tradeoff | 65.08 | 7.504 | 53.91 | 3.666 | 10.719725613624318 | 10.76 | -0.03576 | 0.01855 | 0.00042764349997015394 | 0.00046634978763171464 |
| 3 | fuel_leader | 17afbf80420c | retain_champion | objective_tradeoff | 146.2 | 7.169 | 136 | 3.001 | 10.24202396144441 | 10.27 | -0.0295 | 0.01576 | 0.0010790744999871205 | 0.00038181256555258614 |
| 4 | champion_improve | 660d8570c3e7 | retain_champion | objective_tradeoff | 209 | 7.324 | 198.6 | 3.075 | 10.463364130309108 | 10.45 | 0.0125 | -0.006487 | 0.0015751849999776635 | 0.000391178978461193 |
| 5 | champion_improve | 660d8570c3e7 | retain_champion | objective_tradeoff | 168.8 | 7.355 | 158.4 | 3.083 | 10.50696798935275 | 10.54 | -0.03334 | 0.01788 | 0.0012565244999741543 | 0.0003922906127208359 |
| 6 | fuel_leader | f75cd9a11d01 | replace_champion | strict_pareto | 39.52 | 7.421 | 28.71 | 3.386 | 10.601284212689079 | 10.56 | 0.04313 | -0.02245 | 0.00022771999996729075 | 0.00043079659906930523 |

Champion: 3f252a1af6ae59e8f9b7596d8c75990b445be217b5d6d05b1e60837fa4114a62

Each iter_NNN/summary.md explains the measured decision. Raw artifacts live under trials/.
Compact mode retains all scalar evaluation records but only the final raw policy/trajectory.

## Deployment (L1/L6)
Total operating cost below baseline with SOC drift, fuel and battery inside the guards: **True**
Claim: lower total operating cost of the ep399 actor at the search seed/cycle/initial state
[Final reward](results/aroma_runs/seed61_obscur_20261016_033314_316752822/search/20261016_033314_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed61_obscur_seq_v3_catalog_iter6/final_reward.py)
[Final ep399 actor](results/aroma_runs/seed61_obscur_20261016_033314_316752822/search/20261016_033314_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmopenai_gpt-5p2+gpt-5-mini_multiagent_seed61_obscur_seq_v3_catalog_iter6/trials/368baf256a445cf433030eb4/models/iter_001/Standard_WLTC_WVUINTER/net_params/actor_iter001_ep399.pkl)

## Reward confirmation (L4)
Status: not_run
Reason: separate step: --resume_run_root <run> --run_confirmation [--confirmation_seed_list ...]

No unseen-cycle generalization is claimed.

Compute: {"trained_episodes": 2400, "llm_calls": 31, "reported_tokens": 804223, "note": "Persisted trials and reported usage only; interrupted work or missing provider usage may be absent."}
