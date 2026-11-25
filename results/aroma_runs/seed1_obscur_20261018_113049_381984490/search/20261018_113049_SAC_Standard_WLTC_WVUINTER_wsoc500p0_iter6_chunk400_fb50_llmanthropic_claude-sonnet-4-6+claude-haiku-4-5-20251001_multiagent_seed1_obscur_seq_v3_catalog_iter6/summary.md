# AROMA sequential v3 (total operating cost)

AROMA is multi-objective energy management whose goal is the total operating cost of the drive: hydrogen cost + FC degradation cost + battery degradation cost, in USD per 100 km at fixed prices (context.cost_model). The core levers are FC degradation and FC hydrogen consumption: FC wear is usually the largest share of the total, so a policy that burns slightly more hydrogen but wears the FC much less can win. Adoption: total operating cost MUST be strictly below the standing champion's. Guard bands, fixed in advance (context.cost_model.guards): CHARGE SUSTAINING, |SOC_final - SOC_initial| of the ep399 rollout at most soc_drift_abs_max (absolute, the same for every seed, so a baseline that drifts further does not loosen it); SOC-corrected equivalent hydrogen at most the baseline's times (1 + max fuel increase); and battery SOH loss at most the baseline's times (1 + max battery increase), so FC wear cannot be bought by charging the battery with idling FC power, by shifting load onto the battery or by unbounded hydrogen. FC SOH loss has no cap of its own; it is priced in the total. The search keeps the Pareto front of total cost versus SOC-corrected fuel among guard-feasible rewards; the champion is its lowest-cost point, and a reward that is cheaper but fails a guard is kept as a repair target. A tie in total cost is rejected. Compare final ep399 policies at the same seed, cycle, initial state and 400-episode training budget. Tail statistics are diagnostics. Keep physical tracking feasible and SOC within the specified operating band. Reward coefficients and cost shares are not measurements of policy performance. State causal explanations as hypotheses; actual post-training measurements decide adoption.

Status: completed

Costs in USD per 100 km (operating_cost.py, same prices as paper_figs_multi_seed.ipynb).

| Iteration | Edit mode | Parent | Decision | vs champion | Total cost | H2 cost | FC cost | Battery cost | g/km (ep399) | raw H2 g/km | SOC corr. g/km | ΔSOC final | FC SOH loss | Battery SOH loss |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | — | — | baseline_trained | — | 40.41 | 7.459 | 28.69 | 4.266 | 10.6562854090602 | 10.67 | -0.01748 | 0.009211 | 0.00022755816664343786 | 0.0005426791354884442 |
| 2 | champion_improve | 17afbf80420c | replace_champion | cost_tradeoff | 29.92 | 7.508 | 18.71 | 3.697 | 10.725808877679976 | 10.67 | 0.05753 | -0.0297 | 0.00014844199996344454 | 0.0004703077050141058 |
| 3 | fuel_leader | 17afbf80420c | retain_champion | objective_tradeoff | 56.89 | 7.578 | 45.73 | 3.577 | 10.825083492258189 | 10.85 | -0.0295 | 0.01517 | 0.0003627564999574284 | 0.00045505322881711496 |
| 4 | champion_improve | 243cb08ab6af | retain_champion | objective_tradeoff | 68.27 | 7.389 | 57.5 | 3.389 | 10.555178801660189 | 10.55 | 0.009893 | -0.005172 | 0.00045608199997138055 | 0.0004311996541510599 |
| 5 | champion_improve | 243cb08ab6af | retain_champion | objective_tradeoff | 56.08 | 7.471 | 44.94 | 3.675 | 10.672690978900759 | 10.7 | -0.02793 | 0.01456 | 0.00035644999996953253 | 0.0004675783512551046 |
| 6 | fuel_leader | 367da7530a61 | retain_champion | objective_tradeoff | 33.61 | 7.257 | 22.98 | 3.372 | 10.366560589980136 | 10.34 | 0.02303 | -0.01226 | 0.00018226749998606628 | 0.0004290074259936105 |

Champion: 243cb08ab6af4c489bb4a513e82ca38174951dc2f56886c576a0b2e2e076b4bf

Each iter_NNN/summary.md explains the measured decision. Raw artifacts live under trials/.
Compact mode retains all scalar evaluation records but only the final raw policy/trajectory.

## Deployment (L1/L6)
Total operating cost below baseline with SOC drift, fuel and battery inside the guards: **True**
Claim: lower total operating cost of the ep399 actor at the search seed/cycle/initial state
[Final reward](results/aroma_runs/seed1_obscur_20261018_113049_381984490/search/20261018_113049_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed1_obscur_seq_v3_catalog_iter6/final_reward.py)
[Final ep399 actor](results/aroma_runs/seed1_obscur_20261018_113049_381984490/search/20261018_113049_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed1_obscur_seq_v3_catalog_iter6/trials/419af57378de003361bb99a4/models/iter_001/Standard_WLTC_WVUINTER/net_params/actor_iter001_ep399.pkl)

## Reward confirmation (L4)
Status: not_run
Reason: separate step: --resume_run_root <run> --run_confirmation [--confirmation_seed_list ...]

No unseen-cycle generalization is claimed.

Compute: {"trained_episodes": 2400, "llm_calls": 36, "reported_tokens": 887930, "note": "Persisted trials and reported usage only; interrupted work or missing provider usage may be absent."}
