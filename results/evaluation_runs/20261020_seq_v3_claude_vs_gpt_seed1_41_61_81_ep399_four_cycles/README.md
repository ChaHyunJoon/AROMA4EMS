# seq_v3_catalog Claude vs GPT — seeds 1/41/61/81, iter1–6 ep399, UDDS/WVUSUB/LA92/HWFET

No new rollouts (plant code unchanged since the source evals). `tables.py` merges:
- GPT s41/61/81 ← `../20261017_seq_v3_catalog_seed41_61_81_iter1to6_ep399_four_cycles` (runs `aroma_baseline_matched/seed*_obscur_20261016_*`)
- Claude s41/61/81 ← `../20261018_seq_v3_catalog_claude_seed41_61_81_iter1to6_ep399_four_cycles` (runs `seed*_obscur_20261017_*`)
- s1 Claude/GPT iter1–6 ← `../20261019_..._seed1_21_...` (`metrics.csv` + `metrics_iter6.csv`; runs `seed1_obscur_20261018_113049_*` / `_061824_*`)
- DP (interp w500) / rule-based ← `../20261017_.../comparison_with_dp_rb.csv`
Shared iter1 baselines asserted identical between Claude and GPT tables.

Outputs: `report.md` (one-glance tables), `table_all_iters.csv`, `table_dp_rb.csv`, `table_per_cycle_final.csv`.
`final` = last `replace_champion` of the training-cycle gate (baseline if none). Claude s81 iter5 = proposal_failed (no actor).
`heldout_gate` = v3 gate on the 4 held-out cycles vs same-seed baseline (cheaper, fuel ≤ +5 %, batt ≤ +10 %, CS 4/4).
