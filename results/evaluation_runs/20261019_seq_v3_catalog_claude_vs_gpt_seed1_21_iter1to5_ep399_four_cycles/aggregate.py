"""Aggregate Claude vs GPT (seeds 1/21, iter1-5, ep399) vs DP / rule-based over UDDS, WVUSUB, LA92, HWFET."""
from pathlib import Path
import json
import pandas as pd
OUT = Path(__file__).resolve().parent
REF = OUT.parent / '20261017_seq_v3_catalog_seed41_61_81_iter1to6_ep399_four_cycles' / 'comparison_with_dp_rb.csv'
HELD = ['UDDS', 'WVUSUB', 'LA92', 'HWFET']
CS_TOL = 0.05

rl = pd.DataFrame(json.loads((OUT / 'results.json').read_text())['metrics'])
# the shared baseline belongs to both agents' iteration sequences
base = rl[rl.agent == 'baseline']
rl = pd.concat([rl[rl.agent != 'baseline'], base.assign(agent='claude'), base.assign(agent='gpt')], ignore_index=True)

man = json.loads((OUT / 'manifest.json').read_text())['jobs']
tr = rl[rl.cycle == 'WLTC_WVUINTER'].drop_duplicates('policy').set_index('policy')
d = [(abs(j['recorded_cost']['total_usd'] - tr.loc[k, 'total_usd']),
      abs(j['recorded_fuel_breakdown']['soc_final_minus_initial'] - tr.loc[k, 'soc_drift']))
     for k, j in man.items() if j.get('recorded_cost')]
print('train replay vs recorded: max |total diff| %.2e, max |dSOC diff| %.2e' % (max(a for a, _ in d), max(b for _, b in d)))


def agg(df):
    w = df.distance_km / df.distance_km.sum()
    return pd.Series(dict(
        eq_gkm=(df.equivalent_h2_g_per_km * w).sum(),
        h2_usd=(df.h2_usd * w).sum(), fc_usd=(df.fc_usd * w).sum(), batt_usd=(df.batt_usd * w).sum(),
        total_usd=(df.total_usd * w).sum(),
        fc_soh_loss_pct=100 * df.fc_soh_loss.sum(), batt_soh_loss_pct=100 * df.battery_soh_loss.sum(),
        max_abs_dsoc=df.soc_drift.abs().max(), cs_pass=int((df.soc_drift.abs() <= CS_TOL).sum()),
        fc_starts=int(df.fc_starts.sum()), valid=int(df.valid_delivery.sum())))


held = rl[rl.cycle.isin(HELD)]
A = held.groupby(['agent', 'seed', 'iteration', 'adoption_decision']).apply(agg).reset_index()
b = A[A.iteration == 1].set_index(['agent', 'seed'])
for col, name in [('total_usd', 'dtotal_pct'), ('eq_gkm', 'dfuel_pct'), ('batt_soh_loss_pct', 'dbatt_pct'),
                  ('fc_soh_loss_pct', 'dfc_pct')]:
    A[name] = [100 * (r[col] / b.loc[(r.agent, r.seed), col] - 1) for _, r in A.iterrows()]
A['heldout_gate'] = (A.dtotal_pct < 0) & (A.dfuel_pct <= 5) & (A.dbatt_pct <= 10) & (A.cs_pass == 4) & (A.iteration > 1)
T = rl[rl.cycle == 'WLTC_WVUINTER'][['agent', 'seed', 'iteration', 'equivalent_h2_g_per_km', 'soc_drift', 'total_usd', 'fc_starts']]
A = A.merge(T.rename(columns=dict(equivalent_h2_g_per_km='train_eq', soc_drift='train_dsoc', total_usd='train_total',
                                  fc_starts='train_starts')), on=['agent', 'seed', 'iteration'])
A = A.sort_values(['seed', 'agent', 'iteration'])
A.to_csv(OUT / 'aggregate_four_cycles_claude_vs_gpt.csv', index=False)

R = pd.read_csv(REF).rename(columns=dict(delta_soc='soc_drift'))
R = R[R.method.isin(['DP', 'Rule-based'])]
R['fc_soh_loss'] = R.fc_soh_loss_pct / 100; R['battery_soh_loss'] = R.battery_soh_loss_pct / 100
R['valid_delivery'] = R.valid_delivery.astype(bool)
RA = R.groupby('method').apply(agg).reset_index()
RA.to_csv(OUT / 'reference_dp_rb_four_cycles.csv', index=False)

cols = ['cycle', 'equivalent_h2_g_per_km', 'soc_drift', 'fc_soh_loss', 'battery_soh_loss', 'h2_usd', 'fc_usd',
        'batt_usd', 'total_usd', 'fc_starts', 'valid_delivery']
pc = pd.concat([held.drop_duplicates(['policy', 'cycle']).assign(method=lambda x: x.policy)[['method'] + cols],
                R[['method'] + cols]])
pc.to_csv(OUT / 'per_cycle_all_methods.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
print(RA.round(3).to_string())
print(A.drop(columns=['h2_usd']).round(3).to_string())
