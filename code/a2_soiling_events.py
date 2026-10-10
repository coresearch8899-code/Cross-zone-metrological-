"""Step 2: common-reference PR, SRR soiling, log-anchored event study with permutation inference."""
import pandas as pd, numpy as np, json, warnings
import rdtools, rdtools.soiling
warnings.filterwarnings('ignore')
d = pd.read_pickle('d_clean.pkl')
Y = d.pivot(index='date', columns='z', values='equivalent_hours')
OUT = d.pivot(index='date', columns='z', values='outage').fillna(True).astype(bool)
PRown = d.pivot(index='date', columns='z', values='pr_percent')
T = d.pivot(index='date', columns='z', values='ambient_temp_mean_c').mean(axis=1)
H = pd.read_pickle('H.pkl')
idx = pd.date_range(Y.index.min(), Y.index.max(), freq='D')
Y, OUT, PRown, T, H = [x.reindex(idx) for x in (Y, OUT, PRown, T, H)]
H3 = H[3]
GAMMA = -0.0035; ROSS = 0.03; DT_DAY = 4.0
Gday = H3 * 1000 / 12.0
Tmod = T + DT_DAY + ROSS * Gday
ftemp = 1 + GAMMA * (Tmod - 25)
PRc = pd.DataFrame({z: Y[z] / H3 / ftemp for z in [1, 2, 3]})
for z in [1, 2, 3]:
    PRc.loc[OUT[z].fillna(True).astype(bool).values, z] = np.nan
PRc[(PRc > 1.2) | (PRc < 0.3)] = np.nan
PRc.loc[H3 < 1.0] = np.nan            # low-insolation days unreliable
PRc = PRc.loc['2023-04-26':]          # exclude commissioning (Mar-Apr 2023 outages)
PRc.to_pickle('PRc.pkl'); H3.to_pickle('H3.pkl'); Tmod.to_pickle('Tmod.pkl')

EVENTS = [('C1', '2023-05-06', 'cleaning'), ('C2', '2024-03-09', 'cleaning'), ('C3', '2024-06-23', 'cleaning'),
          ('M1', '2024-06-25', 'meter calibration'), ('C4', '2025-04-25', 'cleaning'), ('C5', '2025-12-26', 'cleaning'),
          ('C6', '2026-03-23', 'cleaning'), ('T1', '2026-06-11', 'transformer PM (250/1000/1250 kVA)'),
          ('C7', '2026-09-05', 'cleaning')]
ev_dates = [pd.Timestamp(e[1]) for e in EVENTS]
res = {}

# ---- SRR soiling per zone (RdTools stochastic rate & recovery) ----
srr = {}
for z in [1, 2, 3]:
    pm = PRc[z].dropna()
    pm = pm / pm.quantile(0.95)          # normalise to clean-state level
    ins = H3.reindex(pm.index) * 1000
    pm_full = pm.reindex(pd.date_range(pm.index.min(), pm.index.max(), freq='D'))
    ins_full = ins.reindex(pm_full.index)
    pm_full.index = pm_full.index.tz_localize('Asia/Bangkok'); ins_full.index = pm_full.index
    try:
        np.random.seed(42)
        sr, ci, info = rdtools.soiling.soiling_srr(pm_full, ins_full, reps=1000, clean_threshold='infer',
                                           max_relative_slope_error=500, max_negative_step=0.05,
                                           min_interval_length=7, recenter=True, confidence_level=95.0)
        ints = info['soiling_interval_summary']
        valid = ints[ints.valid]
        cle = info['calc_info']['rolling_median'] if 'rolling_median' in info.get('calc_info', {}) else None
        rates = valid.soiling_rate * 100
        srr[z] = {'insolation_weighted_SR': round(sr, 4), 'CI95': [round(ci[0], 4), round(ci[1], 4)],
                  'n_intervals': int(len(ints)), 'n_valid': int(len(valid)),
                  'median_rate_pct_per_day': round(float(rates.median()), 4),
                  'IQR_rate': [round(float(rates.quantile(.25)), 4), round(float(rates.quantile(.75)), 4)],
                  'interval_starts': [str(x.date()) for x in ints.start]}
        ints.to_csv(f'srr_intervals_z{z}.csv')
        info['soiling_ratio_perfect_clean'].to_csv(f'srr_ratio_z{z}.csv')
    except Exception as e:
        srr[z] = {'error': str(e)}
res['srr'] = srr

# ---- precision/recall of data-detected cleaning (SRR interval starts) vs logged cleanings ----
cl = [pd.Timestamp(e[1]) for e in EVENTS if e[2] == 'cleaning']
pr_tab = {}
for z in [1, 3]:
    if 'interval_starts' not in srr[z]: continue
    starts = pd.to_datetime(srr[z]['interval_starts'])[1:]
    hits = [c for c in cl if any(abs((s - c).days) <= 7 for s in starts)]
    tp_det = [s for s in starts if any(abs((s - c).days) <= 7 for c in cl)]
    pr_tab[z] = {'n_detected': len(starts), 'n_logged': len(cl), 'logged_recovered': len(hits),
                 'recall': round(len(hits) / len(cl), 3), 'precision': round(len(tp_det) / max(len(starts), 1), 3),
                 'unlogged_recoveries': [str(s.date()) for s in starts if s not in tp_det]}
res['log_fidelity'] = pr_tab

# ---- log-anchored event study (median post - median pre on log PRc), permutation null ----
def delta(series, t0, pre=14, gap=3, post=14):
    a = series[t0 - pd.Timedelta(days=pre): t0 - pd.Timedelta(days=1)].dropna()
    b = series[t0 + pd.Timedelta(days=gap + 1): t0 + pd.Timedelta(days=gap + post)].dropna()
    if len(a) < 6 or len(b) < 6: return np.nan
    return (np.median(b) - np.median(a)) * 100

def perm(series, t0, seasonal=True, **kw):
    obs = delta(series, t0, **kw)
    cands = [t for t in series.index[20:-20] if all(abs((t - e).days) > 20 for e in ev_dates)]
    if seasonal:
        doy0 = t0.dayofyear
        cands = [t for t in cands if min(abs(t.dayofyear - doy0), 365 - abs(t.dayofyear - doy0)) <= 45]
    null = np.array([delta(series, t, **kw) for t in cands]); null = null[~np.isnan(null)]
    p = (np.sum(null >= obs) + 1) / (len(null) + 1) if not np.isnan(obs) else np.nan   # one-sided (gain)
    p2 = (np.sum(np.abs(null - np.median(null)) >= abs(obs - np.median(null))) + 1) / (len(null) + 1) if not np.isnan(obs) else np.nan
    z = (obs - null.mean()) / null.std() if len(null) > 5 else np.nan
    return obs, p, p2, z, len(null), null

logP = np.log(PRc)
logPown = np.log(PRown.reindex(PRc.index) / 100).where(PRown.reindex(PRc.index) < 89.95)
es = []
nulls = {}
for code, dt, kind in EVENTS:
    t0 = pd.Timestamp(dt)
    for z in [1, 2, 3]:
        mets = [('common-ref', logP[z]), ('own-sensor', logPown[z])]
        if z in (1, 2): mets.append(('yield-ratio', np.log(Y[z] / Y[3]).reindex(PRc.index).where(PRc[z].notna() & PRc[3].notna())))
        for mname, ser in mets:
            obs, p, p2, zs, n, null = perm(ser, t0)
            es.append(dict(event=code, date=dt, type=kind, zone=z, metric=mname, delta_pct=round(obs, 2) if not np.isnan(obs) else None,
                           p_one=round(p, 3) if not np.isnan(obs) else None, p_two=round(p2, 3) if not np.isnan(obs) else None,
                           z=round(zs, 2) if not np.isnan(obs) else None, n_null=n))
            if mname == 'common-ref': nulls[(code, z)] = null
es = pd.DataFrame(es); es.to_csv('event_study.csv', index=False)
print(es[es.metric == 'common-ref'].to_string())
print(es[es.metric == 'own-sensor'].to_string())

# ---- lag profile: cumulative recovery by day after logged cleaning (z1, z3; common-ref) ----
lag = {}
for code, dt, kind in EVENTS:
    if kind != 'cleaning': continue
    t0 = pd.Timestamp(dt)
    for z in [1, 3]:
        s = logP[z]
        base = s[t0 - pd.Timedelta(days=14): t0 - pd.Timedelta(days=1)].median()
        post = s[t0: t0 + pd.Timedelta(days=10)]
        lag[f'{code}_z{z}'] = [None if np.isnan(v) else round((v - base) * 100, 2) for v in post.values]
res['lag_profile'] = lag
pd.to_pickle(nulls, 'nulls.pkl')
json.dump(res, open('res_soiling.json', 'w'), indent=1)
print(json.dumps(res, indent=1)[:5000])
