# AROMA sequential v3 (total operating cost)

AROMA is multi-objective energy management whose goal is the total operating cost of the drive: hydrogen cost + FC degradation cost + battery degradation cost, in USD per 100 km at fixed prices (context.cost_model). The core levers are FC degradation and FC hydrogen consumption: FC wear is usually the largest share of the total, so a policy that burns slightly more hydrogen but wears the FC much less can win. Adoption: total operating cost MUST be strictly below the standing champion's. Guard bands, fixed in advance (context.cost_model.guards): CHARGE SUSTAINING, |SOC_final - SOC_initial| of the ep399 rollout at most soc_drift_abs_max (absolute, the same for every seed, so a baseline that drifts further does not loosen it); SOC-corrected equivalent hydrogen at most the baseline's times (1 + max fuel increase); and battery SOH loss at most the baseline's times (1 + max battery increase), so FC wear cannot be bought by charging the battery with idling FC power, by shifting load onto the battery or by unbounded hydrogen. FC SOH loss has no cap of its own; it is priced in the total. The search keeps the Pareto front of total cost versus SOC-corrected fuel among guard-feasible rewards; the champion is its lowest-cost point, and a reward that is cheaper but fails a guard is kept as a repair target. A tie in total cost is rejected. Compare final ep399 policies at the same seed, cycle, initial state and 400-episode training budget. Tail statistics are diagnostics. Keep physical tracking feasible and SOC within the specified operating band. Reward coefficients and cost shares are not measurements of policy performance. State causal explanations as hypotheses; actual post-training measurements decide adoption.

Status: completed

Costs in USD per 100 km (operating_cost.py, same prices as paper_figs_multi_seed.ipynb).

| Iteration | Edit mode | Parent | Decision | vs champion | Total cost | H2 cost | FC cost | Battery cost | g/km (ep399) | raw H2 g/km | SOC corr. g/km | ΔSOC final | FC SOH loss | Battery SOH loss |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | — | — | baseline_trained | — | 52.94 | 7.887 | 40.52 | 4.524 | 11.267763405434842 | 11.63 | -0.364 | 0.1848 | 0.000321448999946794 | 0.0005755324677042539 |
| 2 | champion_improve | 17afbf80420c | replace_champion | strict_pareto | 47.6 | 7.541 | 36.69 | 3.37 | 10.773400960778153 | 10.83 | -0.05462 | 0.02818 | 0.00029100899995571083 | 0.00042869396245737157 |
| 3 | fuel_leader | 2227859ceab7 | retain_champion | objective_tradeoff | 49.84 | 7.198 | 38.61 | 4.041 | 10.283571008481 | 10.26 | 0.02464 | -0.01333 | 0.0003062274999954262 | 0.0005140906246626775 |
| 4 | champion_improve | 2227859ceab7 | retain_champion | worse_or_equal | 49.38 | 7.55 | 38.27 | 3.556 | 10.78624236391707 | 10.87 | -0.08096 | 0.04186 | 0.00030360299996179396 | 0.000452363049353699 |
| 5 | champion_improve | 2227859ceab7 | replace_champion | cost_tradeoff | 31.71 | 7.458 | 20.61 | 3.638 | 10.65367379300568 | 10.56 | 0.09107 | -0.04722 | 0.0001634954999684135 | 0.00046283919178391475 |
| 6 | fuel_leader | a0da819909d2 | retain_champion | objective_tradeoff | 55.96 | 7.226 | 45.14 | 3.592 | 10.322597665167146 | 10.23 | 0.09608 | -0.0512 | 0.0003581024999858018 | 0.0004570410563201621 |

Champion: 452be853ae4e82e6deab124d0941a7ef0869d00ea1ce7d3db2983e0c79a61b76

Each iter_NNN/summary.md explains the measured decision. Raw artifacts live under trials/.
Compact mode retains all scalar evaluation records but only the final raw policy/trajectory.

## Deployment (L1/L6)
Total operating cost below baseline with SOC drift, fuel and battery inside the guards: **True**
Claim: lower total operating cost of the ep399 actor at the search seed/cycle/initial state
[Final reward](results/aroma_runs/seed41_obscur_20261017_035655_808241122/search/20261017_035655_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed41_obscur_seq_v3_catalog_iter6/final_reward.py)
[Final ep399 actor](results/aroma_runs/seed41_obscur_20261017_035655_808241122/search/20261017_035655_SAC_Standard_WLTC_WVUINTER_wsoc500p0_iter6_chunk400_fb50_llmanthropic_claude-sonnet-4-6+claude-haiku-4-5-20251001_multiagent_seed41_obscur_seq_v3_catalog_iter6/trials/244a2a5fa7795e87f12d6933/models/iter_001/Standard_WLTC_WVUINTER/net_params/actor_iter001_ep399.pkl)

## Reward confirmation (L4)
Status: not_run
Reason: separate step: --resume_run_root <run> --run_confirmation [--confirmation_seed_list ...]

No unseen-cycle generalization is claimed.

Compute: {"trained_episodes": 2400, "llm_calls": 36, "reported_tokens": 902415, "note": "Persisted trials and reported usage only; interrupted work or missing provider usage may be absent."}
