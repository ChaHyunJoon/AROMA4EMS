# AROMA sequential v3 (total operating cost)

AROMA is multi-objective energy management whose goal is the total operating cost of the drive: hydrogen cost + FC degradation cost + battery degradation cost, in USD per 100 km at fixed prices (context.cost_model). The core levers are FC degradation and FC hydrogen consumption: FC wear is usually the largest share of the total, so a policy that burns slightly more hydrogen but wears the FC much less can win. Adoption: total operating cost MUST be strictly below the standing champion's. Guard bands, fixed in advance (context.cost_model.guards): CHARGE SUSTAINING, |SOC_final - SOC_initial| of the ep399 rollout at most soc_drift_abs_max (absolute, the same for every seed, so a baseline that drifts further does not loosen it); SOC-corrected equivalent hydrogen at most the baseline's times (1 + max fuel increase); and battery SOH loss at most the baseline's times (1 + max battery increase), so FC wear cannot be bought by charging the battery with idling FC power, by shifting load onto the battery or by unbounded hydrogen. FC SOH loss has no cap of its own; it is priced in the total. The search keeps the Pareto front of total cost versus SOC-corrected fuel among guard-feasible rewards; the champion is its lowest-cost point, and a reward that is cheaper but fails a guard is kept as a repair target. A tie in total cost is rejected. Compare final ep399 policies at the same seed, cycle, initial state and 400-episode training budget. Tail statistics are diagnostics. Keep physical tracking feasible and SOC within the specified operating band. Reward coefficients and cost shares are not measurements of policy performance. State causal explanations as hypotheses; actual post-training measurements decide adoption.

Status: completed

Costs in USD per 100 km (operating_cost.py, same prices as paper_figs_multi_seed.ipynb).

| Iteration | Edit mode | Parent | Decision | vs champion | Total cost | H2 cost | FC cost | Battery cost | g/km (ep399) | raw H2 g/km | SOC corr. g/km | ΔSOC final | FC SOH loss | Battery SOH loss |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | — | — | baseline_trained | — | 73.16 | 7.258 | 62.15 | 3.758 | 10.368679466188617 | 10.35 | 0.01796 | -0.009605 | 0.0004929689999854103 | 0.00047805274582957136 |
| 2 | champion_improve | 17afbf80420c | retain_champion | cost_tradeoff | 60.43 | 7.292 | 48.86 | 4.271 | 10.416938091960285 | 10.46 | -0.04101 | 0.02225 | 0.00038760849998786817 | 0.0005433898415627691 |
| 3 | fuel_leader | 17afbf80420c | retain_champion | objective_tradeoff | 87.48 | 7.501 | 77.36 | 2.622 | 10.716361215701049 | 10.65 | 0.0618 | -0.03153 | 0.000613624499961607 | 0.00033356203225598513 |
| 4 | guard_repair | dd6bf7ad68dc | retain_champion | objective_tradeoff | 102.4 | 7.208 | 92.43 | 2.782 | 10.297306956036225 | 10.16 | 0.1351 | -0.07146 | 0.0007331474999825449 | 0.00035391441612098173 |
| 5 | champion_improve | 17afbf80420c | retain_champion | objective_tradeoff | 105 | 7.188 | 94.46 | 3.321 | 10.268683146551933 | 10.25 | 0.01838 | -0.009848 | 0.0007492609999890654 | 0.0004224572740161303 |
| 6 | fuel_leader | 8a3dd1ba8361 | retain_champion | objective_tradeoff | 106.5 | 7.259 | 96.66 | 2.591 | 10.370637825038564 | 10.28 | 0.08878 | -0.0465 | 0.0007667504999778751 | 0.0003296697036827556 |

Champion: 17afbf80420cb9f947efdaac72a30bf9687444a44fa8df43fcfaa7ace533d083

Each iter_NNN/summary.md explains the measured decision. Raw artifacts live under trials/.
Compact mode retains all scalar evaluation records but only the final raw policy/trajectory.

## Deployment (L1/L6)
Total operating cost below baseline with SOC drift, fuel and battery inside the guards: **False**
Claim: no verified improvement; baseline deployed
[Final reward](results/aroma_runs/seed61_obscur_20261017_044026_162287183/search/20261017_044026_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed61_obscur_seq_v3_catalog_iter6/final_reward.py)
[Final ep399 actor](results/aroma_runs/seed61_obscur_20261017_044026_162287183/search/20261017_044026_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed61_obscur_seq_v3_catalog_iter6/trials/5dd14214c01b19b3c17022b6/models/iter_001/Standard_WLTC_WVUINTER/net_params/actor_iter001_ep399.pkl)

## Reward confirmation (L4)
Status: not_run
Reason: separate step: --resume_run_root <run> --run_confirmation [--confirmation_seed_list ...]

No unseen-cycle generalization is claimed.

Compute: {"trained_episodes": 2400, "llm_calls": 36, "reported_tokens": 876091, "note": "Persisted trials and reported usage only; interrupted work or missing provider usage may be absent."}
