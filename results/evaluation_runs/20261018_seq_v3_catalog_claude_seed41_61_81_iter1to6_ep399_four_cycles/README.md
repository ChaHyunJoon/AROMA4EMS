# 20261017 seq_v3_catalog (Claude sonnet-4-6 + haiku-4-5) — seeds 41/61/81, iter 1–6, ep399

- `evaluate_all_iters.py`: copy of the 20261017 GPT eval script (glob → `seed*_obscur_20261017_*`, skips
  `proposal_failed` iterations, logs fc_starts = count(d_s_s>0)). seed81 iter5 = proposal_failed → 17 actors × 5 cycles.
- Training-cycle replay matches recorded ep399 total cost within 5.5e-4 USD/100km, ΔSOC within 1.4e-8.
- `aggregate.py` → `aggregate_four_cycles_claude_vs_gpt.csv` (distance-weighted over UDDS/WVUSUB/LA92/HWFET,
  GPT rows from `../20261017_seq_v3_catalog_seed41_61_81_iter1to6_ep399_four_cycles`),
  `reference_dp_rb_four_cycles.csv` (DP interp w500 / rule-based, same file as the GPT comparison), `per_cycle_all_methods.csv`.
- iter1 (baseline) actors are identical across the Claude and GPT runs (both forked from the same baselines).
- `heldout_gate` = v3 gate applied on the 4 held-out cycles vs same-seed baseline (cheaper, fuel ≤ +5 %, batt ≤ +10 %, CS 4/4).
- LA92 invalid delivery (3–4 steps, ≤0.0056 kWh unserved): s41 it1, s41 it4, s61 it1, s81 it4.
