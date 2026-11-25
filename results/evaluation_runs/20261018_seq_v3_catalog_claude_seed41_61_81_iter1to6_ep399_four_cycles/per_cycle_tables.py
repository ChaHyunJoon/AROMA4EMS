"""Markdown per-cycle tables (total, CS, eq fuel, FC/batt SOH loss, FC starts) for Claude and GPT, every iteration."""
from pathlib import Path
import json
import pandas as pd
OUT = Path(__file__).resolve().parent
d = pd.read_csv(OUT / 'per_cycle_all_methods.csv')
dec = {}
for ag, root in [('Claude', OUT), ('GPT', OUT.parent / '20261017_seq_v3_catalog_seed41_61_81_iter1to6_ep399_four_cycles')]:
    for j, v in json.loads((root / 'manifest.json').read_text())['jobs'].items():
        dec[f"{ag}_s{v['seed']}_it{v['iteration']}"] = v['adoption_decision']
short = dict(baseline_trained='baseline', replace_champion='**adopted**', retain_champion='rejected')
lines = []
for ag in ['Claude', 'GPT']:
    for s in [41, 61, 81]:
        lines += [f'\n### {ag} seed{s}\n', '| iter (train decision) | cycle | total USD/100km | ΔSOC (CS) | eq H2 g/km | FC SOH loss % | Batt SOH loss % | FC starts |',
                  '|---|---|---|---|---|---|---|---|']
        x = d[d.method.str.startswith(f'{ag}_s{s}_')]
        for m in sorted(x.method.unique(), key=lambda m: int(m.split('_it')[1])):
            for c in ['UDDS', 'WVUSUB', 'LA92', 'HWFET']:
                r = x[(x.method == m) & (x.cycle == c)].iloc[0]
                cs = '✓' if abs(r.soc_drift) <= 0.05 else '✗'
                inv = '' if r.valid_delivery else ' †'
                lines.append(f"| it{m.split('_it')[1]} ({short[dec[m]]}) | {c}{inv} | {r.total_usd:.1f} | {r.soc_drift:+.3f} {cs} | "
                             f"{r.equivalent_h2_g_per_km:.2f} | {100*r.fc_soh_loss:.4f} | {100*r.battery_soh_loss:.4f} | {int(r.fc_starts)} |")
ref = d[d.method.isin(['DP', 'Rule-based'])]
lines += ['\n### DP / Rule-based\n', '| method | cycle | total | ΔSOC | eq | FC % | Batt % | starts |', '|---|---|---|---|---|---|---|---|']
for _, r in ref.iterrows():
    lines.append(f"| {r.method} | {r.cycle}{'' if r.valid_delivery else ' †'} | {r.total_usd:.1f} | {r.soc_drift:+.4f} | {r.equivalent_h2_g_per_km:.2f} | "
                 f"{100*r.fc_soh_loss:.4f} | {100*r.battery_soh_loss:.4f} | {int(r.fc_starts)} |")
(OUT / 'per_cycle_tables.md').write_text('# Per-cycle results (ep399)\n\n† = LA92 delivery shortfall steps; CS ✓ = |ΔSOC| ≤ 0.05\n' + '\n'.join(lines) + '\n')
