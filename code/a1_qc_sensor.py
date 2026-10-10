"""Step 1: QC, censoring diagnostics and reference-sensor audit (cross-zone + clear-sky envelope)."""
import pandas as pd, numpy as np, pvlib, json
from scipy import stats

LAT, LON, ALT = 20.0, 100.0, 400        # regional grid point (exact site withheld)
d = pd.read_csv('daily.csv'); d['date'] = pd.to_datetime(d.date); d['z'] = d.zone.str[-1].astype(int)
n_raw = len(d)
d = d.drop_duplicates(['date', 'z'], keep='last')
n_dup = n_raw - len(d)
CAP = {1: None, 2: None, 3: None}
d['cap_kwp'] = d.daily_production_kwh / d.equivalent_hours
capk = d[d.equivalent_hours > 1].groupby('z').cap_kwp.median().to_dict()
d['outage'] = (d.daily_production_kwh <= 0) | d.pr_percent.isna() | (d.equivalent_hours < 0.5)
d['cens'] = d.pr_percent >= 89.95
d['H'] = np.where(~d.outage & ~d.cens, d.equivalent_hours / (d.pr_percent / 100), np.nan)
d.to_pickle('d_clean.pkl')

qc = {'rows_raw': n_raw, 'dup_removed': n_dup, 'date_min': str(d.date.min().date()), 'date_max': str(d.date.max().date()),
      'n_days': int(d.date.nunique()), 'missing_days': [str(x.date()) for x in pd.date_range(d.date.min(), d.date.max()).difference(d.date.unique())],
      'kwp': {int(k): round(v, 1) for k, v in capk.items()}}
for z in [1, 2, 3]:
    q = d[d.z == z]
    qc[f'z{z}'] = {'outage_days': int(q.outage.sum()), 'censored_days': int(q.cens.sum()),
                  'censored_share_valid': round(q.cens.sum() / (~q.outage).sum() * 100, 1),
                  'alarm_days': int((q.statuses == 'สัญญาณเตือน').sum()), 'fault_days': int((q.statuses == 'ฟอลต์').sum()),
                  'E_total_MWh': round(q.daily_production_kwh.sum() / 1000, 1)}

# clear-sky daily GHI (Ineichen, climatological Linke turbidity)
times = pd.date_range(d.date.min(), d.date.max() + pd.Timedelta(days=1), freq='10min', tz='Asia/Bangkok')
loc = pvlib.location.Location(LAT, LON, 'Asia/Bangkok', ALT)
cs = loc.get_clearsky(times, model='ineichen')
Hcs = (cs.ghi.resample('D').sum() * (10 / 60) / 1000); Hcs.index = Hcs.index.tz_localize(None)

H = d.pivot(index='date', columns='z', values='H')
# clear-sky envelope index: rolling 30-d 95th percentile of H/Hcs
K = H.div(Hcs.reindex(H.index), axis=0)
env = K.rolling(31, center=True, min_periods=12).quantile(0.95)
env.to_pickle('env.pkl'); H.to_pickle('H.pkl'); Hcs.to_pickle('Hcs.pkl')

def ts_trend(s):
    s = s.dropna(); t = (s.index - s.index[0]).days.values / 365.25
    r = stats.theilslopes(s.values, t, 0.95)
    return r.slope, r.low_slope, r.high_slope, s.mean()

out = {}
for z in [1, 2, 3]:
    sl, lo, hi, mu = ts_trend(env[z])
    out[f'env_trend_z{z}_pct_per_yr'] = [round(100 * sl / mu, 2), round(100 * lo / mu, 2), round(100 * hi / mu, 2)]
# inter-zone sensor ratio trends (deseasonalised by same-DOY year-on-year)
for a in [1, 2]:
    r = (H[a] / H[3]).replace([np.inf, -np.inf], np.nan)
    rm = r.rolling(31, center=True, min_periods=10).median()
    sl, lo, hi, mu = ts_trend(rm)
    out[f'ratio_H{a}H3_trend_pct_per_yr'] = [round(100 * sl / mu, 2), round(100 * lo / mu, 2), round(100 * hi / mu, 2)]
    # YoY on daily ratio
    yoy = (rm / rm.shift(365) - 1).dropna() * 100
    out[f'ratio_H{a}H3_yoy_median_pct'] = round(yoy.median(), 2)
    # piecewise: first 24 months vs last 12 months medians
    out[f'ratio_H{a}H3_med_2023_24'] = round(r[:'2024-12-31'].median(), 3)
    out[f'ratio_H{a}H3_med_2026'] = round(r['2026-01-01':].median(), 3)
# changepoint on H1/H3 (PELT) to date the drift onset
import ruptures as rpt
r13 = (H[1] / H[3]).rolling(7, center=True, min_periods=4).median().dropna()
algo = rpt.Pelt(model='l2', min_size=60).fit(r13.values.reshape(-1, 1))
bk = algo.predict(pen=np.var(r13.values) * 15)
out['H1H3_breaks'] = [str(r13.index[min(b, len(r13) - 1)].date()) for b in bk[:-1]]
out['H1H3_segment_medians'] = [round(float(np.median(r13.values[s:e])), 3) for s, e in zip([0] + bk[:-1], bk)]
# censoring vs ratio: logistic-like association, z1 monthly
m = d[d.z == 1].set_index('date').resample('MS').agg({'cens': 'mean'})
rr = (H[1] / H[3]).resample('MS').median()
out['corr_cens_z1_vs_ratio_spearman'] = round(stats.spearmanr(m.cens.values[:len(rr)], rr.values, nan_policy='omit').statistic, 3)
qc['sensor'] = out
json.dump(qc, open('res_qc.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(qc, indent=1, ensure_ascii=False))
