"""Where do FC shut-offs happen? Stop / decel / driving; SOC at shut-off; off-interval lengths."""
from pathlib import Path
import sys, numpy as np, scipy.io as sio, pandas as pd
OUT = Path(__file__).resolve().parent
GPT = OUT.parent / '20261017_seq_v3_catalog_seed41_61_81_iter1to6_ep399_four_cycles'
sys.path.insert(0, str((OUT.parents[2] / 'FCHEV-EMS')))
import os; os.chdir((OUT.parents[2] / 'FCHEV-EMS'))
from common.utils import get_driving_cycle
from FCHEV_SOH import FCHEV_SOH
P_OFF = FCHEV_SOH().P_FC_off
rows = []
for agent, root in [('Claude', OUT), ('GPT', GPT)]:
    for p in sorted(root.glob('Standard_*/seed*_iter*_ep399/episode_data/data_ep0.mat')):
        cyc = p.parts[-4].replace('Standard_', ''); pol = p.parts[-3]
        d = sio.loadmat(p); a = lambda k: np.asarray(d[k], float).ravel()
        v = np.asarray(get_driving_cycle(f'Standard_{cyc}'), float).ravel()[:len(a('SOC'))]
        pfc = a('fc_applied_kw'); on = pfc >= P_OFF; soc = np.r_[0.6, a('SOC')]
        acc = np.r_[0, np.diff(v)]
        offs = np.where(on[:-1] & ~on[1:])[0] + 1          # first off step
        starts = int((a('d_s_s') > 0).sum())
        kinds = {'stop': 0, 'decel': 0, 'drive': 0}; durs = []; socs = []
        for i in offs:
            k = 'stop' if v[i] < 0.1 else ('decel' if acc[i] < -0.1 else 'drive'); kinds[k] += 1
            j = i
            while j < len(on) and not on[j]: j += 1
            durs.append(j - i); socs.append(soc[i])
        nstops = int(((v[1:] < 0.1) & (v[:-1] >= 0.1)).sum())
        rows.append(dict(agent=agent, cycle=cyc, policy=pol, starts=starts, offs=len(offs), stops_in_cycle=nstops,
                         off_at_stop=kinds['stop'], off_at_decel=kinds['decel'], off_driving=kinds['drive'],
                         off_med_s=float(np.median(durs)) if durs else np.nan,
                         off_short_lt30s=int(sum(x < 30 for x in durs)),
                         soc_at_off_med=float(np.median(socs)) if socs else np.nan,
                         fc_on_pct=100 * on.mean(), fc_mean_kw_on=float(pfc[on].mean()) if on.any() else 0,
                         fc_lowpow_pct_on=100 * float((pfc[on] < 4.75).mean()) if on.any() else 0,
                         batt_thru_kwh=float(np.abs(a('battery_delivered_kw')).sum() / 3600)))
df = pd.DataFrame(rows); df.to_csv(OUT / 'fc_event_analysis.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
sel = df.policy.isin(['seed41_iter001_ep399', 'seed41_iter002_ep399', 'seed41_iter005_ep399', 'seed61_iter001_ep399',
                      'seed61_iter002_ep399', 'seed81_iter001_ep399', 'seed81_iter002_ep399', 'seed81_iter006_ep399',
                      'seed81_iter004_ep399', 'seed61_iter006_ep399'])
print(df[sel].sort_values(['cycle', 'policy', 'agent']).round(3).to_string(index=False))
