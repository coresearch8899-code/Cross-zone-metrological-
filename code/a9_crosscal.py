"""Step 9 (R4): in-situ cross-calibration. All three horizontal pyranometers carry the same labelled sensitivity
(11.513 uV per W m-2), were never recalibrated after factory calibration (2021-06), and the loggers are assumed to use the
label value. Under that assumption, the inter-zone ratio R_i3 equals the ratio of true to entered sensitivity of sensor i
relative to sensor 3, so effective sensitivities and correction factors follow directly from the data."""
import pandas as pd, numpy as np, json
H = pd.read_pickle('H.pkl'); Hcs = pd.read_pickle('Hcs.pkl'); env = pd.read_pickle('env.pkl')
S_LAB = 11.513
idx = H.index; doy = idx.dayofyear.values
Xh = np.column_stack([f(2 * np.pi * k * doy / 365.25) for k in (1, 2) for f in (np.sin, np.cos)])
out = {'S_label_uV': S_LAB}
corr = {}
for z in [1, 2]:
    lr = np.log(H[z] / H[3]); m = lr.notna().values & (idx < pd.Timestamp('2025-03-01'))
    X = np.column_stack([np.ones(len(idx)), Xh]); b, *_ = np.linalg.lstsq(X[m], lr.values[m], rcond=None)
    lr_ds = lr - Xh @ b[1:]                                    # remove repeatable geometric/obstruction cycle
    q = lr_ds.resample('QS').median(); n = lr_ds.resample('QS').count()
    r = np.exp(q)
    corr[z] = pd.DataFrame({'ratio_to_Z3': r.round(4), 'S_eff_uV': (S_LAB * r).round(3), 'correction_factor': (1 / r).round(4), 'n_days': n})
    out[f'z{z}_pre2025_ratio'] = round(float(np.exp(b[0])), 4)
    out[f'z{z}_S_eff_pre2025_uV'] = round(float(S_LAB * np.exp(b[0])), 3)
    last = lr_ds['2026-04-01':].median(); out[f'z{z}_ratio_2026Q2Q3'] = round(float(np.exp(last)), 4)
    out[f'z{z}_S_eff_2026_uV'] = round(float(S_LAB * np.exp(last)), 3); out[f'z{z}_correction_2026'] = round(float(np.exp(-last)), 4)
# absolute plausibility of each sensor: clear-sky envelope in the clearest months (Nov-Jan, before haze build-up)
for z in [1, 2, 3]:
    e = env[z]; e = e[e.index.month.isin([11, 12, 1])]
    out[f'z{z}_clear_envelope_NovJan_by_season'] = {f'{y}/{y+1}': round(float(e[f'{y}-11-01':f'{y+1}-01-31'].median()), 3) for y in [2023, 2024, 2025] if len(e[f'{y}-11-01':f'{y+1}-01-31'].dropna())}
out['years_since_factory_calibration_at_end'] = round((pd.Timestamp('2026-09-07') - pd.Timestamp('2021-06-15')).days / 365.25, 1)
tab = pd.concat({f'Zone {z}': corr[z] for z in [1, 2]}, axis=1); tab.index = [f'{d.year}Q{(d.month - 1)//3 + 1}' for d in tab.index]
tab.to_csv('crosscal_quarterly.csv')
json.dump(out, open('res_crosscal.json', 'w'), indent=1)
print(json.dumps(out, indent=1)); print(tab.to_string())
