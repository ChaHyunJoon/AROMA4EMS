# 20261018 seq_v3_catalog — Claude vs GPT, seeds 1/21, iter 1–5, ep399

- Runs: Claude `aroma_baseline_matched/seed{1,21}_obscur_20261018_11*` (forked from GPT), GPT `seed{1,21}_obscur_20261018_0618*`.
  iter1 baseline actor is shared (sha-checked) → evaluated once as `baseline_seed*`. iter6 still training, not evaluated.
- `evaluate_all_iters.py` (copy of 20261018 script) → 18 actors × UDDS/WVUSUB/LA92/HWFET + training cycle (90 rollouts).
  Training-cycle replay matches recorded ep399 within 9.8e-4 USD/100km, dSOC 4.3e-8.
- `tables.py` → `table_four.csv` (distance-weighted 4 cycles) and `table_three_noLA92.csv`; DP (interp w500) / rule-based from
  `../20261017_.../comparison_with_dp_rb.csv`. FC/batt SOH loss columns are SUMS over the cycles (%).
- **baseline_seed21 FAILS LA92**: SOC 0.6→1.0, terminated at step 178/1435 (battery_soc_limit); its 4-cycle numbers are not valid.
- Training-cycle adoption: Claude s1 → iter2, GPT s1 → iter3, s21 both none (baseline kept).
- `aggregate.py` → `aggregate_four_cycles_claude_vs_gpt.csv` (deltas vs baseline + held-out v3 gate).
- iter6: `evaluate_iter6.py` → `results_iter6.json` / `metrics_iter6.csv` (all four iter6 rejected on training; finals unchanged).
- seed21 baseline ep0–398 actors were never saved (compact mode saves only ep399), so no earlier LA92-completing
  checkpoint can be picked; retraining was rejected by the user (10-20).
