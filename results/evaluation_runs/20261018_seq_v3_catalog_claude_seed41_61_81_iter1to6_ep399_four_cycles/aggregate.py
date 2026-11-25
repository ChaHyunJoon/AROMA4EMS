"""Aggregate Claude (this dir) vs GPT (20261017 eval) vs DP / rule-based over UDDS, WVUSUB, LA92, HWFET."""
from pathlib import Path
import json, csv
import pandas as pd
import numpy as np
OUT = Path(__file__).resolve().parent
GPT = OUT.parent / '20261017_seq_v3_catalog_seed41_61_81_iter1to6_ep399_four_cycles'
HELD = ['UDDS', 'WVUSUB', 'LA92', 'HWFET']
CS_TOL = 0.05

claude = pd.DataFrame(json.loads((OUT / 'results.json').read_text())['metrics']); claude['agent'] = 'Claude'
gpt = pd.DataFrame(json.loads((GPT / 'results_with_fc_events.json').read_text())); gpt['agent'] = 'GPT'
rl = pd.concat([claude, gpt], ignore_index=True)

# training-cycle reproducibility vs recorded ep399 cost
man = json.loads((OUT / 'manifest.json').read_text())['jobs']
tr = claude[claude.cycle == 'WLTC_WVUINTER'].set_index('policy')
repro = [(k, j['recorded_cost']['total_usd'], tr.loc[k, 'total_usd'],
          j['recorded_fuel_breakdown']['soc_final_minus_initial'], tr.loc[k, 'soc_drift']) for k, j in man.items()]
print('max |total diff| train replay vs recorded:', max(abs(a - b) for _, a, b, _, _ in repro),
      ' max |dSOC diff|:', max(abs(a - b) for *_, a, b in repro))

def agg(df):
    km = df.distance_km.sum()
    w = df.distance_km / km
    return pd.Series(dict(
        eq_gkm=(df.equivalent_h2_g_per_km * w).sum(),
        h2_usd=(df.h2_usd * w).sum(), fc_usd=(df.fc_usd * w).sum(), batt_usd=(df.batt_usd * w).sum(),
        total_usd=(df.total_usd * w).sum(),
        fc_soh_loss_pct=100 * df.fc_soh_loss.sum(), batt_soh_loss_pct=100 * df.battery_soh_loss.sum(),
        max_abs_dsoc=df.soc_drift.abs().max(), cs_pass=int((df.soc_drift.abs() <= CS_TOL).sum()),
        fc_starts=int(df.fc_starts.sum()), valid=int(df.valid_delivery.sum())))

held = rl[rl.cycle.isin(HELD)]
A = held.groupby(['agent', 'seed', 'iteration', 'adoption_decision']).apply(agg).reset_index()
base = A[A.iteration == 1].set_index(['agent', 'seed'])
for col, name in [('total_usd', 'dtotal_pct'), ('eq_gkm', 'dfuel_pct'), ('batt_soh_loss_pct', 'dbatt_pct'),
                  ('fc_soh_loss_pct', 'dfc_pct')]:
    A[name] = [100 * (r[col] / base.loc[(r.agent, r.seed), col] - 1) for _, r in A.iterrows()]
# held-out version of the v3 gate vs same-seed baseline: cheaper, fuel <= +5 %, batt <= +10 %, CS on all 4
A['heldout_gate'] = (A.dtotal_pct < 0) & (A.dfuel_pct <= 5) & (A.dbatt_pct <= 10) & (A.cs_pass == 4) & (A.iteration > 1)
# training-cycle per-cycle view (what the gate saw)
T = rl[rl.cycle == 'WLTC_WVUINTER'][['agent', 'seed', 'iteration', 'adoption_decision', 'equivalent_h2_g_per_km',
                                    'soc_drift', 'total_usd', 'fc_starts']]
A = A.merge(T.rename(columns=dict(equivalent_h2_g_per_km='train_eq', soc_drift='train_dsoc', total_usd='train_total',
                                  fc_starts='train_starts')), on=['agent', 'seed', 'iteration', 'adoption_decision'])
A.to_csv(OUT / 'aggregate_four_cycles_claude_vs_gpt.csv', index=False)

ref = pd.read_csv(GPT / 'comparison_with_dp_rb.csv')
R = ref.rename(columns=dict(method='agent', delta_soc='soc_drift', fc_soh_loss_pct='fcp', battery_soh_loss_pct='bp'))
R['fc_soh_loss'] = R.fcp / 100; R['battery_soh_loss'] = R.bp / 100; R['valid_delivery'] = R.valid_delivery.astype(bool)
RA = R.groupby('agent').apply(agg).reset_index()
RA.to_csv(OUT / 'reference_dp_rb_four_cycles.csv', index=False)

# per-cycle long table for every RL policy + references
cols = ['cycle', 'equivalent_h2_g_per_km', 'soc_drift', 'fc_soh_loss', 'battery_soh_loss', 'h2_usd', 'fc_usd',
        'batt_usd', 'total_usd', 'fc_starts', 'valid_delivery']
pc = pd.concat([held.assign(method=held.agent + '_s' + held.seed.astype(str) + '_it' + held.iteration.astype(str))[['method'] + cols],
                R.assign(method=R.agent)[['method'] + cols]])
pc.to_csv(OUT / 'per_cycle_all_methods.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
print(RA.round(3).to_string())
print(A.drop(columns=['h2_usd']).round(3).to_string())
