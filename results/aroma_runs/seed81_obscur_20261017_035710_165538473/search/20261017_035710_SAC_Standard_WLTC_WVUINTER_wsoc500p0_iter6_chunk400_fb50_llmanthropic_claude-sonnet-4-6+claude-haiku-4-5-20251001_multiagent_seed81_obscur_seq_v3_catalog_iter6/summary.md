# AROMA sequential v3 (total operating cost)

AROMA is multi-objective energy management whose goal is the total operating cost of the drive: hydrogen cost + FC degradation cost + battery degradation cost, in USD per 100 km at fixed prices (context.cost_model). The core levers are FC degradation and FC hydrogen consumption: FC wear is usually the largest share of the total, so a policy that burns slightly more hydrogen but wears the FC much less can win. Adoption: total operating cost MUST be strictly below the standing champion's. Guard bands, fixed in advance (context.cost_model.guards): CHARGE SUSTAINING, |SOC_final - SOC_initial| of the ep399 rollout at most soc_drift_abs_max (absolute, the same for every seed, so a baseline that drifts further does not loosen it); SOC-corrected equivalent hydrogen at most the baseline's times (1 + max fuel increase); and battery SOH loss at most the baseline's times (1 + max battery increase), so FC wear cannot be bought by charging the battery with idling FC power, by shifting load onto the battery or by unbounded hydrogen. FC SOH loss has no cap of its own; it is priced in the total. The search keeps the Pareto front of total cost versus SOC-corrected fuel among guard-feasible rewards; the champion is its lowest-cost point, and a reward that is cheaper but fails a guard is kept as a repair target. A tie in total cost is rejected. Compare final ep399 policies at the same seed, cycle, initial state and 400-episode training budget. Tail statistics are diagnostics. Keep physical tracking feasible and SOC within the specified operating band. Reward coefficients and cost shares are not measurements of policy performance. State causal explanations as hypotheses; actual post-training measurements decide adoption.

Status: completed

Costs in USD per 100 km (operating_cost.py, same prices as paper_figs_multi_seed.ipynb).

| Iteration | Edit mode | Parent | Decision | vs champion | Total cost | H2 cost | FC cost | Battery cost | g/km (ep399) | raw H2 g/km | SOC corr. g/km | ΔSOC final | FC SOH loss | Battery SOH loss |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | — | — | baseline_trained | — | 35.92 | 7.587 | 23.51 | 4.827 | 10.838062644164271 | 11.02 | -0.1774 | 0.09339 | 0.00018646449997072878 | 0.0006140980938273977 |
| 2 | champion_improve | 17afbf80420c | replace_champion | cost_tradeoff | 32.05 | 7.709 | 20.83 | 3.515 | 11.012690244020076 | 11.05 | -0.03452 | 0.01744 | 0.00016522099994698003 | 0.0004471829724568277 |
| 3 | fuel_leader | 17afbf80420c | retain_champion | objective_tradeoff | 45.93 | 7.56 | 34.98 | 3.394 | 10.799665982804488 | 10.84 | -0.04279 | 0.02205 | 0.00027744549996167045 | 0.00043181538769143657 |
| 4 | champion_improve | eb92825323ba | retain_champion | objective_tradeoff | 44.74 | 7.516 | 33.39 | 3.831 | 10.737645847987707 | 10.81 | -0.074 | 0.03864 | 0.0002648909999630744 | 0.00048737468724169286 |
| 5 | champion_improve | eb92825323ba | proposal_failed | — | — | — | — | — | — | — | — | — | — | — |
| 6 | fuel_leader | cace7bb7665b | retain_champion | objective_tradeoff | 40.13 | 7.596 | 28.97 | 3.563 | 10.851982454042885 | 10.83 | 0.02023 | -0.01035 | 0.00022982999995579956 | 0.00045328771461572437 |

Champion: eb92825323ba17b3c53a26167f4276edba0c98b8823ab4fd1114398bb4fe87c8

Each iter_NNN/summary.md explains the measured decision. Raw artifacts live under trials/.
Compact mode retains all scalar evaluation records but only the final raw policy/trajectory.

## Deployment (L1/L6)
Total operating cost below baseline with SOC drift, fuel and battery inside the guards: **True**
Claim: lower total operating cost of the ep399 actor at the search seed/cycle/initial state
[Final reward](results/aroma_runs/seed81_obscur_20261017_035710_165538473/search/20261017_035710_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed81_obscur_seq_v3_catalog_iter6/final_reward.py)
[Final ep399 actor](results/aroma_runs/seed81_obscur_20261017_035710_165538473/search/20261017_035710_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed81_obscur_seq_v3_catalog_iter6/trials/e54c41168d3541adda13c388/models/iter_001/Standard_WLTC_WVUINTER/net_params/actor_iter001_ep399.pkl)

## Reward confirmation (L4)
Status: not_run
Reason: separate step: --resume_run_root <run> --run_confirmation [--confirmation_seed_list ...]

No unseen-cycle generalization is claimed.

Compute: {"trained_episodes": 2000, "llm_calls": 47, "reported_tokens": 1310691, "note": "Persisted trials and reported usage only; interrupted work or missing provider usage may be absent."}
