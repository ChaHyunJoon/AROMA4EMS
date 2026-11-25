"""Compare the efficient-band rule (p_off 0.95 kW) with the methods of paper_figs_multi_seed.ipynb.

The notebook's configuration and loading cells (1, 2, 4, 6) are executed as they stand, so DP, the Fig. 11
rule-based baseline, SAC and the AROMA picks (PICKS: seed -> adopted iteration) are exactly the notebook's rows.
Costs follow the notebook: mean over cycles of per-km rates, H2 7 USD/kg, FC 80 kW x 76 USD/kW to 10 % loss,
battery 1.56 kWh x 486 USD/kWh to 20 % loss.

Usage from repository root: .venv/bin/python FCHEV-EMS/evaluation_runs/20261021_rb_efficient_band_poff095/compare_with_notebook.py
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
NOTEBOOK = OUT.parents[3] / 'visualization' / 'paper_figs_multi_seed.ipynb'
MIN_OFF_SHOWN = [0, 30, 45, 60, 90, 120, 180]

ns = {}
cells = json.loads(NOTEBOOK.read_text())['cells']
for i in [1, 2, 4, 6]:
    exec(''.join(cells[i]['source']), ns)
M, CYCLES, METHODS, SOC0 = ns['M'], ns['CYCLES'], ns['METHODS'], ns['SOC0']

sweep = pd.read_csv(OUT / 'metrics.csv')
sweep = sweep[(sweep.method == 'Efficient-band') & sweep.min_off_s.isin(MIN_OFF_SHOWN)]
rb_rows = pd.DataFrame({
    'method': [f'RB-EB min_off {int(m)} s' for m in sweep.min_off_s], 'seed': np.nan, 'cycle': sweep.cycle.values,
    'eq': sweep.equivalent_h2_g_per_km.values, 'adsoc': np.abs(sweep.final_soc.values - SOC0),
    'fc': sweep.fc_soh_loss.values, 'bt': sweep.battery_soh_loss.values})
rb_methods = [f'RB-EB min_off {m} s' for m in MIN_OFF_SHOWN]
dist = sweep.groupby('cycle').distance_km.first()

m = pd.concat([M[['method', 'seed', 'cycle', 'eq', 'adsoc', 'fc', 'bt']].astype({'cycle': str}), rb_rows],
              ignore_index=True)
m['km'] = m.cycle.map(dist)
m['h2_cost'] = m['eq'] / 1000. * ns['H2_PRICE'] * 100.
m['fc_cost'] = ns['FC_NET_KW'] * ns['FC_COST_PER_KW'] * m.fc / m.km / ns['FC_EOL_LOSS'] * 100.
m['bt_cost'] = ns['BATT_KWH'] * ns['BATT_COST_PER_KWH'] * m.bt / m.km / ns['BATT_EOL_LOSS'] * 100.
m['total_cost'] = m.h2_cost + m.fc_cost + m.bt_cost
m['fc_life_km'] = ns['FC_EOL_LOSS'] / (m.fc / m.km)
order = ['DP', 'SAC'] + [x for x in METHODS if x.startswith('AROMA')] + ['Rule-based'] + rb_methods
vals = ['eq', 'adsoc', 'fc', 'bt', 'h2_cost', 'fc_cost', 'bt_cost', 'total_cost']

# per-seed four-cycle mean, then mean +- std over seeds (as the notebook's PS / summary)
ps = m.assign(seed=m.seed.fillna(-1)).groupby(['method', 'seed'])[vals].mean().reset_index()
ps['fc_life_km'] = ns['FC_EOL_LOSS'] / m.assign(seed=m.seed.fillna(-1), r=m.fc / m.km).groupby(
    ['method', 'seed']).r.mean().values
mean = ps.groupby('method')[vals + ['fc_life_km']].mean().loc[order]
std = ps.groupby('method')[vals].std(ddof=1).loc[order]
sac = mean.loc['SAC']
table = pd.DataFrame({
    'Eq. H2 (g/km)': mean['eq'], 'max|dSOC|': m.groupby('method').adsoc.max().loc[order],
    'FC loss (1e-4)': mean.fc * 1e4, 'FC loss std': std.fc * 1e4, 'FC vs SAC (x)': mean.fc / sac.fc,
    'FC vs DP (x)': mean.fc / mean.loc['DP', 'fc'], 'Batt loss (1e-4)': mean.bt * 1e4,
    'FC life (km)': mean.fc_life_km, 'Total (USD/100km)': mean.total_cost, 'Total std': std.total_cost,
    'Total vs SAC (x)': mean.total_cost / sac.total_cost})

per_cycle = m.groupby(['method', 'cycle'])[['eq', 'fc']].mean().unstack('cycle')
per_cycle = pd.concat({'FC loss (1e-4)': per_cycle['fc'][CYCLES] * 1e4, 'Eq. H2 (g/km)': per_cycle['eq'][CYCLES]},
                      axis=1).loc[order]

picks = ns['PICKS']
seed_rows = ps[ps.method.isin(['SAC'] + [x for x in METHODS if x.startswith('AROMA')])].copy()
seed_rows['iteration'] = [1 if r.method == 'SAC' else picks[r.method.split('(')[1].rstrip(')')][int(r.seed)]
                          for r in seed_rows.itertuples()]
seed_rows = seed_rows.assign(fc_e4=seed_rows.fc * 1e4, bt_e4=seed_rows.bt * 1e4)[
    ['method', 'seed', 'iteration', 'eq', 'fc_e4', 'bt_e4', 'total_cost']].sort_values(['seed', 'method'])

pd.set_option('display.width', 250)
fmt = lambda v: f'{v:.3g}'
print('four-cycle mean (seeded methods: mean over seeds of the per-seed four-cycle mean)')
print(table.to_string(float_format=fmt))
print('\nper cycle (seed mean)')
print(per_cycle.to_string(float_format=fmt))
print('\nSAC and AROMA picks per seed (four-cycle mean)')
print(seed_rows.to_string(index=False, float_format=fmt))
table.to_csv(OUT / 'comparison_four_cycle_mean.csv')
per_cycle.to_csv(OUT / 'comparison_per_cycle.csv')
seed_rows.to_csv(OUT / 'comparison_seed_picks.csv', index=False)
