"""Step 10 (R5): sensitivity to the unverified logger scaling coefficients, and a test of whether the Zone 1 divergence
looks like a one-off coefficient change (single step) or a progressive loss (trend).
Each logger is assumed to convert the thermopile voltage with S_logger = 11.513 uV/(W m-2); an unverified entry
S_logger,i = k_i * 11.513 multiplies that zone's recorded insolation by 1/k_i (constant in time)."""
import pandas as pd, numpy as np, json, warnings, rdtools
from scipy import stats
warnings.filterwarnings('ignore')
d = pd.read_pickle('d_clean.pkl'); H = pd.read_pickle('H.pkl'); PRc = pd.read_pickle('PRc.pkl'); Tmod = pd.read_pickle('Tmod.pkl')
idx = PRc.index; H = H.reindex(idx)
Y = d.pivot(index='date', columns='z', values='equivalent_hours').reindex(idx)
PRrep = d.pivot(index='date', columns='z', values='pr_percent').reindex(idx)
OUT = d.pivot(index='date', columns='z', values='outage').reindex(idx).fillna(True).astype(bool)
ftemp = 1 + (-0.0035) * (Tmod.reindex(idx) - 25)
K = [0.80, 0.90, 1.00, 1.10, 1.20]
def ts(s):
    s = s.dropna(); t = (s.index - s.index[0]).days.values / 365.25; r = stats.theilslopes(s.values, t); return 100 * r.slope / s.mean()
def yoy(s):
    q = s.dropna(); q = q[(q > 0.2) & (q < 1.6)]; q.index = q.index.tz_localize('Asia/Bangkok'); np.random.seed(0)
    return rdtools.degradation_year_on_year(q, recenter=True, confidence_level=95)[0]
rows = []
for k3 in K:
    for k1 in K:
        H3s = H[3] / k3; H1s = H[1] / k1
        prc1 = (Y[1] / H3s / ftemp).where(~OUT[1]); prc3 = (Y[3] / H3s / ftemp).where(~OUT[3])
        # reported PR of Zone 1 recomputed with scaled own sensor, then re-truncated at 90 %; only untruncated days carry H1
        pr1 = (PRrep[1] * k1).where(PRrep[1] < 89.95)
        r13 = (H1s / H3s).rolling(31, center=True, min_periods=10).median()
        rows.append(dict(k1=k1, k3=k3, PRc1_median_pct=round(float(prc1.median() * 100), 1), PRc3_median_pct=round(float(prc3.median() * 100), 1),
                         trend_R13_pct_yr=round(ts(np.log(r13).loc['2025-03-24':]) if False else ts(r13.loc['2025-03-24':]), 2),
                         PLR_z1_common=round(yoy(prc1), 2), PLR_z1_own=round(yoy(pr1 / 100), 2),
                         share_own_PR1_above_90=round(float((pr1 >= 90).mean() * 100), 1),
                         S_eff_z1_pre2025=round(11.513 * k1 / k3 * float(np.exp(np.log(H[1] / H[3])['2023-05-01':'2025-02-28'].median())), 2)))
S = pd.DataFrame(rows); S.to_csv('scaling_sensitivity.csv', index=False)
out = {'grid': rows}
out['invariant_ranges'] = {c: [float(S[c].min()), float(S[c].max())] for c in ['trend_R13_pct_yr', 'PLR_z1_common']}
out['scaled_ranges'] = {c: [float(S[c].min()), float(S[c].max())] for c in ['PRc1_median_pct', 'PRc3_median_pct', 'S_eff_z1_pre2025']}
# step vs progressive: on deseasonalised daily ln R13 from 2024-07-01 to 2026-09-07 compare (a) single step at best date,
# (b) continuous piecewise-linear with one knot, (c) two-knot piecewise-linear; BIC
lr = np.log(H[1] / H[3]); doy = idx.dayofyear.values
Xh = np.column_stack([f(2 * np.pi * k * doy / 365.25) for k in (1, 2) for f in (np.sin, np.cos)])
m = lr.notna().values & (idx < pd.Timestamp('2025-03-01')); X = np.column_stack([np.ones(len(idx)), Xh]); b, *_ = np.linalg.lstsq(X[m], lr.values[m], rcond=None)
y = (lr - Xh @ b[1:])['2024-07-01':].dropna(); t = (y.index - y.index[0]).days.values.astype(float); n = len(y)
def bic(X):
    bb, *_ = np.linalg.lstsq(X, y.values, rcond=None); rss = ((y.values - X @ bb) ** 2).sum(); return n * np.log(rss / n) + X.shape[1] * np.log(n), bb
cand = np.arange(30, n - 30, 2)
best_step = min(((bic(np.column_stack([np.ones(n), (t >= t[i]).astype(float)]))[0], i) for i in cand))
best_k1 = min(((bic(np.column_stack([np.ones(n), t, np.maximum(0, t - t[i])]))[0], i) for i in cand))
best_k2 = min(((bic(np.column_stack([np.ones(n), t, np.maximum(0, t - t[i]), np.maximum(0, t - t[j])]))[0], i, j) for i in cand[::3] for j in cand[::3] if j - i >= 60))
best_stepramp = min(((bic(np.column_stack([np.ones(n), t, (t >= t[i]).astype(float)]))[0], i) for i in cand))
out['step_vs_trend_BIC'] = {'single_step': [round(best_step[0], 1), str(y.index[best_step[1]].date())],
                           'step_plus_linear': [round(best_stepramp[0], 1), str(y.index[best_stepramp[1]].date())],
                           'piecewise_linear_1knot': [round(best_k1[0], 1), str(y.index[best_k1[1]].date())],
                           'piecewise_linear_2knot': [round(best_k2[0], 1), str(y.index[best_k2[1]].date()), str(y.index[best_k2[2]].date())]}
# largest single-day change of the 7-day median vs typical (a coefficient change would appear as one abrupt jump)
s7 = y.rolling(7, center=True, min_periods=4).median(); dd = s7.diff().abs()
out['max_daily_change_7d_median_pct'] = round(float(dd.max() * 100), 2); out['p99_daily_change_pct'] = round(float(dd.quantile(0.99) * 100), 2)
out['date_of_max_change'] = str(dd.idxmax().date())
json.dump(out, open('res_scaling.json', 'w'), indent=1)
print(S.to_string()); print(json.dumps({k: v for k, v in out.items() if k != 'grid'}, indent=1))
