"""Final tables: per method, 4-cycle (UDDS/WVUSUB/LA92/HWFET) distance-weighted + 3-cycle without LA92."""
from pathlib import Path
import json
import pandas as pd
OUT = Path(__file__).resolve().parent
REF = OUT.parent / '20261017_seq_v3_catalog_seed41_61_81_iter1to6_ep399_four_cycles' / 'comparison_with_dp_rb.csv'
d = pd.DataFrame(json.loads((OUT / 'results.json').read_text())['metrics'])
R = pd.read_csv(REF); R = R[R.method.isin(['DP', 'Rule-based'])].rename(columns=dict(delta_soc='soc_drift', method='policy'))
R['fc_soh_loss'] = R.fc_soh_loss_pct / 100; R['battery_soh_loss'] = R.battery_soh_loss_pct / 100; R['completed'] = True
cols = ['policy', 'cycle', 'distance_km', 'equivalent_h2_g_per_km', 'soc_drift', 'fc_soh_loss', 'battery_soh_loss',
        'h2_usd', 'fc_usd', 'batt_usd', 'total_usd', 'fc_starts', 'completed']
X = pd.concat([d[cols], R[cols]])


def agg(df):
    w = df.distance_km / df.distance_km.sum()
    return pd.Series({'eq g/km': (df.equivalent_h2_g_per_km * w).sum(),
                      'CS pass': f"{int((df.soc_drift.abs() <= .05).sum())}/{len(df)}",
                      'max|dSOC|': df.soc_drift.abs().max(),
                      'FC SOH loss %': 100 * df.fc_soh_loss.sum(), 'batt SOH loss %': 100 * df.battery_soh_loss.sum(),
                      'H2 $': (df.h2_usd * w).sum(), 'FC $': (df.fc_usd * w).sum(), 'batt $': (df.batt_usd * w).sum(),
                      'total $/100km': (df.total_usd * w).sum(), 'starts': int(df.fc_starts.sum()),
                      'completed': int(df.completed.sum())})


pd.set_option('display.width', 250)
for name, cyc in [('four', ['UDDS', 'WVUSUB', 'LA92', 'HWFET']), ('three_noLA92', ['UDDS', 'WVUSUB', 'HWFET'])]:
    T = X[X.cycle.isin(cyc)].groupby('policy').apply(agg)
    T.to_csv(OUT / f'table_{name}.csv')
    print(f'== {name}'); print(T.round(4).to_string())
