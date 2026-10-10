"""Step 3: sensor-channel event study, persistence, interval soiling rates, YoY degradation (own vs common reference),
alarm-fatigue test, grid-side tests for calibration and transformer PM, economics."""
import pandas as pd, numpy as np, json, warnings
from scipy import stats
import rdtools
warnings.filterwarnings('ignore')
d = pd.read_pickle('d_clean.pkl'); PRc = pd.read_pickle('PRc.pkl'); H = pd.read_pickle('H.pkl')
idx = PRc.index
pv = lambda c: d.pivot(index='date', columns='z', values=c).reindex(idx)
Y, PRown, E, L, B = pv('equivalent_hours'), pv('pr_percent'), pv('daily_production_kwh'), pv('daily_load_kwh'), pv('daily_purchased_kwh')
ST = pv('statuses'); H = H.reindex(idx)
EVENTS = [('C1', '2023-05-06', 'cleaning'), ('C2', '2024-03-09', 'cleaning'), ('C3', '2024-06-23', 'cleaning'),
          ('M1', '2024-06-25', 'meter calibration'), ('C4', '2025-04-25', 'cleaning'), ('C5', '2025-12-26', 'cleaning'),
          ('C6', '2026-03-23', 'cleaning'), ('T1', '2026-06-11', 'transformer PM'), ('C7', '2026-09-05', 'cleaning')]
evd = [pd.Timestamp(e[1]) for e in EVENTS]
R = {}

def delta(s, t0, pre=14, gap=3, post=14, post_start=None):
    a = s[t0 - pd.Timedelta(days=pre): t0 - pd.Timedelta(days=1)].dropna()
    st = gap + 1 if post_start is None else post_start
    b = s[t0 + pd.Timedelta(days=st): t0 + pd.Timedelta(days=st + post - 1)].dropna()
    if len(a) < 6 or len(b) < 6: return np.nan
    return (np.median(b) - np.median(a)) * 100

def perm(s, t0, **kw):
    obs = delta(s, t0, **kw)
    c = [t for t in s.index[20:-20] if all(abs((t - e).days) > 20 for e in evd)]
    c = [t for t in c if min(abs(t.dayofyear - t0.dayofyear), 365 - abs(t.dayofyear - t0.dayofyear)) <= 45]
    nl = np.array([delta(s, t, **kw) for t in c]); nl = nl[~np.isnan(nl)]
    if np.isnan(obs): return dict(delta=None, p_two=None, q95=None, n=len(nl))
    p2 = (np.sum(np.abs(nl - np.median(nl)) >= abs(obs - np.median(nl))) + 1) / (len(nl) + 1)
    return dict(delta=round(obs, 2), p_two=round(p2, 3), null_q025=round(np.quantile(nl, .025), 2),
                null_q975=round(np.quantile(nl, .975), 2), n=len(nl))

# A. sensor channel
A = {}
for code, dt, k in EVENTS:
    for a in [1, 2]:
        s = np.log(H[a] / H[3])
        A[f'{code}_H{a}H3'] = perm(s, pd.Timestamp(dt))
R['sensor_channel'] = A

# B. persistence of Z1 yield-ratio gains
yr1 = np.log(Y[1] / Y[3]).where(PRc[1].notna() & PRc[3].notna())
B_ = {}
for code, dt, k in EVENTS:
    t0 = pd.Timestamp(dt); row = {}
    for lab, ps, ln in [('d4-17', 4, 14), ('d18-45', 18, 28), ('d46-90', 46, 45)]:
        row[lab] = perm(yr1, t0, post_start=ps, post=ln)['delta']
    B_[code] = row
R['persistence_z1_yield_ratio'] = B_

# C. interval soiling rates (Theil-Sen on log yield ratio Z1/Z3 and on log PRc z1, z3) between consecutive cleanings
cl = [pd.Timestamp(e[1]) for e in EVENTS if e[2] == 'cleaning']
C_ = []
for i in range(len(cl) - 1):
    a, b = cl[i] + pd.Timedelta(days=5), cl[i + 1] - pd.Timedelta(days=1)
    row = {'from': str(cl[i].date()), 'to': str(cl[i + 1].date()), 'days': (cl[i + 1] - cl[i]).days}
    for nm, s in [('yr1', yr1), ('prc1', np.log(PRc[1])), ('prc3', np.log(PRc[3]))]:
        q = s[a:b].dropna()
        if len(q) < 20: row[nm] = None; continue
        t = (q.index - q.index[0]).days.values
        r = stats.theilslopes(q.values, t, 0.95)
        row[nm] = [round(r.slope * 100, 4), round(r.low_slope * 100, 4), round(r.high_slope * 100, 4)]
    # dry-season share (Nov-Apr)
    rng = pd.date_range(cl[i], cl[i + 1]); row['dry_share'] = round(np.mean(rng.month.isin([11, 12, 1, 2, 3, 4])), 2)
    C_.append(row)
R['interval_rates_pct_per_day'] = C_
# seasonal soiling rate from rolling 30-day Theil-Sen of log yield ratio, by month
mon = {}
for m in range(1, 13):
    sl = []
    for y in [2023, 2024, 2025, 2026]:
        q = yr1[(yr1.index.year == y) & (yr1.index.month == m)].dropna()
        if len(q) >= 15:
            t = (q.index - q.index[0]).days.values; sl.append(stats.theilslopes(q.values, t).slope * 100)
    mon[m] = round(float(np.median(sl)), 4) if sl else None
R['monthly_median_slope_yr1'] = mon

# D. YoY degradation: own-sensor vs common-reference
D_ = {}
for z in [1, 2, 3]:
    for nm, s in [('own', (PRown[z] / 100).where(PRown[z] < 89.95)), ('common', PRc[z])]:
        q = s.dropna(); q = q[(q > 0.3) & (q < 1.2)]
        q.index = q.index.tz_localize('Asia/Bangkok')
        try:
            np.random.seed(0); rd, ci, info = rdtools.degradation_year_on_year(q, recenter=True, confidence_level=95)
            D_[f'z{z}_{nm}'] = [round(rd, 2), round(ci[0], 2), round(ci[1], 2)]
        except Exception as e:
            D_[f'z{z}_{nm}'] = str(e)
R['yoy_degradation_pct_per_yr'] = D_

# E. alarm fatigue: Z1 alarm vs normal days, month-stratified difference in yield ratio
al = (ST[1] == 'สัญญาณเตือน')
df = pd.DataFrame({'yr': yr1, 'al': al, 'm': idx.month, 'y': idx.year}).dropna()
diffs = []
for (y, m), g in df.groupby(['y', 'm']):
    if g.al.sum() >= 3 and (~g.al).sum() >= 3:
        diffs.append(g[g.al].yr.median() - g[~g.al].yr.median())
R['alarm'] = {'alarm_share_z1': round(al.mean() * 100, 1), 'n_mixed_months': len(diffs),
              'median_within_month_diff_pct': round(np.median(diffs) * 100, 2) if diffs else None,
              'wilcoxon_p': round(stats.wilcoxon(diffs).pvalue, 3) if len(diffs) > 5 else None,
              'alarm_episode_starts': [str(x.date()) for x in idx[1:][(al.values[1:] & ~al.values[:-1])]][:40]}
# point-biserial on monthly level
mm = df.groupby([df.y, df.m]).agg(al=('al', 'mean'), yr=('yr', 'median'))
R['alarm']['monthly_spearman_alarmshare_vs_yr'] = round(stats.spearmanr(mm.al, mm.yr).statistic, 3)
R['alarm']['monthly_spearman_p'] = round(stats.spearmanr(mm.al, mm.yr).pvalue, 3)

# F. grid-side tests: purchased & load (site totals = zone 1 meter? use zone sums)
Ltot = L.sum(axis=1, min_count=3); Btot = B.sum(axis=1, min_count=3)
F_ = {}
for code in ['M1', 'T1', 'C3']:
    t0 = pd.Timestamp(dict((e[0], e[1]) for e in EVENTS)[code])
    for nm, s in [('log_load', np.log(Ltot)), ('log_purchased', np.log(Btot))]:
        F_[f'{code}_{nm}'] = perm(s, t0)
        F_[f'{code}_{nm}_day0'] = round(float((np.log(Ltot if 'load' in nm else Btot)[t0] - np.median(np.log(Ltot if 'load' in nm else Btot)[t0 - pd.Timedelta(days=7):t0 - pd.Timedelta(days=1)])) * 100), 2)
    # day-of-event production shortfall vs Z3-scaled expectation
    exp1 = Y[3][t0] * np.median((Y[1] / Y[3])[t0 - pd.Timedelta(days=7):t0 - pd.Timedelta(days=1)])
    F_[f'{code}_z1_day0_yield_vs_expected_pct'] = round(float((Y[1][t0] / exp1 - 1) * 100), 2)
R['grid_side'] = F_
# TOST equivalence for load around T1 (+-3% margin) using 14d pre vs 14d post daily log load
def tost(s, t0, margin=0.03):
    a = s[t0 - pd.Timedelta(days=14): t0 - pd.Timedelta(days=1)].dropna(); b = s[t0 + pd.Timedelta(days=1): t0 + pd.Timedelta(days=14)].dropna()
    diff = b.mean() - a.mean(); se = np.sqrt(a.var() / len(a) + b.var() / len(b)); dfree = len(a) + len(b) - 2
    p1 = 1 - stats.t.cdf((diff + margin) / se, dfree); p2 = stats.t.cdf((diff - margin) / se, dfree)
    return dict(diff_pct=round(diff * 100, 2), p_tost=round(max(p1, p2), 4), margin_pct=margin * 100)
R['tost'] = {'T1_load': tost(np.log(Ltot), pd.Timestamp('2026-06-11')), 'T1_purchased': tost(np.log(Btot), pd.Timestamp('2026-06-11')),
             'M1_load': tost(np.log(Ltot), pd.Timestamp('2024-06-25')), 'M1_purchased': tost(np.log(Btot), pd.Timestamp('2024-06-25'))}

# G. energy accounting
Etot = E.sum(axis=1)
R['energy'] = {'E_total_MWh_window': round(float(E.sum().sum() / 1000), 1),
               'E_by_zone_MWh': {int(z): round(float(E[z].sum() / 1000), 1) for z in [1, 2, 3]},
               'self_consumption_pct': round(float(100 * (1 - d.daily_exported_kwh.sum() / d.daily_production_kwh.sum())), 2),
               'self_sufficiency_pct': round(float(100 * d.daily_production_kwh.sum() / d.daily_load_kwh.sum()), 2),
               'mean_daily_E_z1_kWh': round(float(E[1].mean()), 1)}
json.dump(R, open('res_ext.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(R, indent=1, ensure_ascii=False))
