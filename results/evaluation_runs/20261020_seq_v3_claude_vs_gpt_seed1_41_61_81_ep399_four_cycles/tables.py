"""One-glance table: Claude vs GPT AROMA (seq_v3_catalog) seeds 1/41/61/81, iter1-6 ep399, + DP / rule-based.

No new rollouts: collects the per-cycle results already stored in
  20261017_* (GPT s41/61/81), 20261018_* (Claude s41/61/81), 20261019_* (s1 Claude/GPT iter1-5 + iter6).
Held-out set = UDDS, WVUSUB, LA92, HWFET (distance-weighted fuel/cost, SOH losses summed over the 4 cycles).
"""
from pathlib import Path
import json
import pandas as pd

OUT = Path(__file__).resolve().parent
ER = OUT.parent
HELD = ['UDDS', 'WVUSUB', 'LA92', 'HWFET']
CS_TOL = 0.05

gpt = pd.DataFrame(json.loads((ER / '20261017_seq_v3_catalog_seed41_61_81_iter1to6_ep399_four_cycles/results_with_fc_events.json').read_text()))
gpt['agent'] = 'GPT'
cl = pd.read_csv(ER / '20261018_seq_v3_catalog_claude_seed41_61_81_iter1to6_ep399_four_cycles/metrics.csv'); cl['agent'] = 'Claude'
d19 = ER / '20261019_seq_v3_catalog_claude_vs_gpt_seed1_21_iter1to5_ep399_four_cycles'
s1 = pd.concat([pd.read_csv(d19 / 'metrics.csv'), pd.read_csv(d19 / 'metrics_iter6.csv')], ignore_index=True)
s1 = s1[s1.seed == 1]
base1 = s1[s1.agent == 'baseline']
s1 = pd.concat([s1[s1.agent != 'baseline'], base1.assign(agent='claude'), base1.assign(agent='gpt')])
s1['agent'] = s1.agent.map({'claude': 'Claude', 'gpt': 'GPT'})
rl = pd.concat([gpt, cl, s1], ignore_index=True)

# sanity: shared baselines (iter1) must be identical between the Claude and GPT tables
b = rl[rl.iteration == 1].pivot_table(index=['seed', 'cycle'], columns='agent', values='total_usd')
assert (b.Claude - b.GPT).abs().max() < 1e-9, b

def agg(df):
    w = df.distance_km / df.distance_km.sum()
    return pd.Series(dict(
        eq_gkm=(df.equivalent_h2_g_per_km * w).sum(),
        cs_pass=int((df.soc_drift.abs() <= CS_TOL).sum()), max_abs_dsoc=df.soc_drift.abs().max(),
        fc_soh_pct=100 * df.fc_soh_loss.sum(), batt_soh_pct=100 * df.battery_soh_loss.sum(),
        h2_usd=(df.h2_usd * w).sum(), fc_usd=(df.fc_usd * w).sum(), batt_usd=(df.batt_usd * w).sum(),
        total_usd=(df.total_usd * w).sum(), fc_starts=int(df.fc_starts.sum()),
        valid=int((df.valid_delivery.astype(bool) & df.completed.astype(bool)).sum()) if 'completed' in df else int(df.valid_delivery.sum())))

held = rl[rl.cycle.isin(HELD)]
A = held.groupby(['agent', 'seed', 'iteration', 'adoption_decision']).apply(agg, include_groups=False).reset_index()
tr = rl[rl.cycle == 'WLTC_WVUINTER'][['agent', 'seed', 'iteration', 'total_usd', 'equivalent_h2_g_per_km', 'soc_drift']]
A = A.merge(tr.rename(columns=dict(total_usd='train_total_usd', equivalent_h2_g_per_km='train_eq_gkm', soc_drift='train_dsoc')),
            on=['agent', 'seed', 'iteration'])
base = A[A.iteration == 1].set_index(['agent', 'seed'])
for c, n in [('total_usd', 'dtotal_pct'), ('eq_gkm', 'dfuel_pct'), ('fc_soh_pct', 'dfc_pct'), ('batt_soh_pct', 'dbatt_pct')]:
    A[n] = [100 * (r[c] / base.loc[(r.agent, r.seed), c] - 1) for _, r in A.iterrows()]
A['heldout_gate'] = (A.iteration > 1) & (A.dtotal_pct < 0) & (A.dfuel_pct <= 5) & (A.dbatt_pct <= 10) & (A.cs_pass == 4)  # same gate as 20261018 aggregate (valid reported separately)
# final adopted iteration per run = last replace_champion (else baseline)
fin = (A[A.adoption_decision.isin(['baseline_trained', 'replace_champion'])].groupby(['agent', 'seed']).iteration.max())
A['final'] = [fin[(r.agent, r.seed)] == r.iteration for _, r in A.iterrows()]
A = A.sort_values(['seed', 'agent', 'iteration'])
A.to_csv(OUT / 'table_all_iters.csv', index=False)

ref = pd.read_csv(ER / '20261017_seq_v3_catalog_seed41_61_81_iter1to6_ep399_four_cycles/comparison_with_dp_rb.csv')
ref = ref[ref.method.isin(['DP', 'Rule-based'])].rename(columns=dict(delta_soc='soc_drift'))
ref['fc_soh_loss'] = ref.fc_soh_loss_pct / 100; ref['battery_soh_loss'] = ref.battery_soh_loss_pct / 100
R = ref.groupby('method').apply(agg, include_groups=False)
R.to_csv(OUT / 'table_dp_rb.csv')

# per-cycle table for the finally adopted agents + references
F = A[A.final][['agent', 'seed', 'iteration']]
pc = held.merge(F, on=['agent', 'seed', 'iteration'])
pc['method'] = pc.agent + ' s' + pc.seed.astype(str) + ' it' + pc.iteration.astype(str)
cols = ['method', 'cycle', 'equivalent_h2_g_per_km', 'soc_drift', 'fc_soh_loss', 'battery_soh_loss', 'total_usd', 'fc_starts', 'valid_delivery']
pcr = ref.assign(fc_soh_loss=ref.fc_soh_loss, battery_soh_loss=ref.battery_soh_loss)
P = pd.concat([pcr[cols], pc[cols]])
P.to_csv(OUT / 'table_per_cycle_final.csv', index=False)

pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
print(R.round(4).to_string())
print(A[['agent', 'seed', 'iteration', 'adoption_decision', 'final', 'train_total_usd', 'train_dsoc', 'eq_gkm', 'cs_pass',
         'max_abs_dsoc', 'fc_soh_pct', 'batt_soh_pct', 'total_usd', 'fc_starts', 'valid', 'dtotal_pct', 'dfuel_pct',
         'dbatt_pct', 'heldout_gate']].round(4).to_string())

# ---- markdown report ----
def fmt_row(r, label, n=4):
    return (f"| {label} | {r.eq_gkm:.3f} | {int(r.cs_pass)}/{n} ({r.max_abs_dsoc:.3f}) | {r.fc_soh_pct:.4f} | {r.batt_soh_pct:.4f} | "
            f"{r.total_usd:.1f} | {r.fc_starts:.0f} | {int(r.valid)}/{n} |")
def mean_row(df):
    r = df.mean(numeric_only=True)
    r['cs_pass'], r['valid'], r['max_abs_dsoc'] = df.cs_pass.sum(), df.valid.sum(), df.max_abs_dsoc.max()
    return r
H = ("| | eq. H2 g/km | CS pass (max abs dSOC) | FC SOH loss % | Batt SOH loss % | Total USD/100km | FC starts | valid |\n"
     "|---|---:|---:|---:|---:|---:|---:|---:|")
L = ['# Held-out 4-cycle (UDDS, WVUSUB, LA92, HWFET) - ep399 actors', '',
     'Fuel/cost distance-weighted; SOH losses summed over the 4 cycles; CS = |SOC_end - 0.6| <= 0.05.', '',
     '## Final adopted agent per seed (training-cycle gate) vs DP / rule-based', '', H]
for m, r in R.iterrows():
    L.append(fmt_row(r, m))
for seed in sorted(A.seed.unique()):
    for ag in ['Claude', 'GPT']:
        r = A[(A.seed == seed) & (A.agent == ag) & A.final].iloc[0]
        L.append(fmt_row(r, f"{ag} s{seed} it{r.iteration}" + (' (=baseline)' if r.iteration == 1 else '')))
for ag in ['Claude', 'GPT']:
    L.append(fmt_row(mean_row(A[(A.agent == ag) & A.final]), f"**{ag} 4-seed mean**", 16))
L.append(fmt_row(mean_row(A[(A.agent == 'Claude') & (A.iteration == 1)]), '**Baseline (SAC) 4-seed mean**', 16))
L.append('')
L.append('Mean rows: CS / valid counted over 16 seed-cycle pairs; abs dSOC = worst case.')
L += ['', '## All iterations', '',
      '| run | it | train decision | train total USD | train dSOC | eq g/km | CS | FC SOH % | Batt SOH % | Total USD | dTotal % | dFuel % | dBatt % | starts | held-out gate |',
      '|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
for _, r in A.iterrows():
    L.append(f"| {r.agent} s{r.seed} | {r.iteration}{' **(final)**' if r.final else ''} | {r.adoption_decision} | {r.train_total_usd:.1f} | {r.train_dsoc:+.3f} | "
             f"{r.eq_gkm:.3f} | {int(r.cs_pass)}/4 | {r.fc_soh_pct:.4f} | {r.batt_soh_pct:.4f} | {r.total_usd:.1f} | {r.dtotal_pct:+.1f} | "
             f"{r.dfuel_pct:+.1f} | {r.dbatt_pct:+.1f} | {int(r.fc_starts)} | {'PASS' if r.heldout_gate else ''} |")
(OUT / 'report.md').write_text('\n'.join(L) + '\n')
