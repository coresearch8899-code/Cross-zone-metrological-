"""Step 6 (revision): robustness and uncertainty analyses requested in the pre-submission review.
A sensor comparability & reference-zone sensitivity; B change-point sensitivity (PELT grid, BinSeg, BottomUp,
segmented regression, Bayesian single change point, block-bootstrap date CI); C event-study robustness (windows,
pre-trends, moving-block bootstrap CIs, test size, cloudy-day exclusion, alternative control zone, with/without T1);
D PR truncation evidence; E Monte-Carlo uncertainty propagation and explicit cleaning objective."""
import pandas as pd, numpy as np, json, warnings
from scipy import stats
import ruptures as rpt, rdtools
warnings.filterwarnings('ignore')
RNG = np.random.default_rng(2026)
d = pd.read_pickle('d_clean.pkl'); PRc = pd.read_pickle('PRc.pkl'); H = pd.read_pickle('H.pkl')
idx = PRc.index
pv = lambda c: d.pivot(index='date', columns='z', values=c).reindex(idx)
Y, PRown, E = pv('equivalent_hours'), pv('pr_percent'), pv('daily_production_kwh')
H = H.reindex(idx); H3 = H[3]
EV = [('C1', '2023-05-06'), ('C2', '2024-03-09'), ('C3', '2024-06-23'), ('M1', '2024-06-25'), ('C4', '2025-04-25'),
      ('C5', '2025-12-26'), ('C6', '2026-03-23'), ('T1', '2026-06-11'), ('C7', '2026-09-05')]
evd = [pd.Timestamp(v) for _, v in EV]
R = {}
def ts(s):
    s = s.dropna(); t = (s.index - s.index[0]).days.values / 365.25; r = stats.theilslopes(s.values, t, 0.95)
    return [round(100 * r.slope, 3), round(100 * r.low_slope, 3), round(100 * r.high_slope, 3)]

# ---------------- A. sensor comparability ----------------
A = {}
lr13 = np.log(H[1] / H[3]); lr23 = np.log(H[2] / H[3]); lr12 = np.log(H[1] / H[2])
doy = idx.dayofyear.values
def harm(n=2):
    return np.column_stack([f(2 * np.pi * k * doy / 365.25) for k in range(1, n + 1) for f in (np.sin, np.cos)])
X_h = harm()
def decompose(lr, breaks):
    """ln R = a + seasonal(2 harmonics) + piecewise-linear trend with knots at breaks; returns bias, seasonal amplitude, slopes."""
    t = (idx - idx[0]).days.values / 365.25
    cols = [np.ones(len(t)), t] + [np.maximum(0, t - (pd.Timestamp(b) - idx[0]).days / 365.25) for b in breaks]
    X = np.column_stack(cols + [X_h]); m = lr.notna().values
    beta, *_ = np.linalg.lstsq(X[m], lr.values[m], rcond=None)
    res = lr.values[m] - X[m] @ beta
    seas = X_h @ beta[-X_h.shape[1]:]
    slopes = np.cumsum(beta[1:2 + len(breaks)]) * 100
    return dict(bias_pct=round((np.exp(beta[0]) - 1) * 100, 2), seasonal_amp_pct=round((seas.max() - seas.min()) / 2 * 100, 2),
                slopes_pct_per_yr=[round(x, 2) for x in slopes], resid_sd_pct=round(res.std() * 100, 2), n=int(m.sum()))
A['decomp_H1H3_knot_2025-03-24'] = decompose(lr13, ['2025-03-24'])
A['decomp_H2H3_linear'] = decompose(lr23, [])
# pre-drift stability (before first major 2025 break)
pre = slice('2023-05-01', '2025-02-28'); post = slice('2025-03-24', '2026-09-07')
A['H1H3_trend_pre_2025_pct_yr'] = ts(lr13[pre].rolling(31, center=True, min_periods=10).median())
A['H1H3_trend_post_2025_pct_yr'] = ts(lr13[post].rolling(31, center=True, min_periods=10).median())
A['H2H3_trend_pre_2025_pct_yr'] = ts(lr23[pre].rolling(31, center=True, min_periods=10).median())
A['H2H3_trend_post_2025_pct_yr'] = ts(lr23[post].rolling(31, center=True, min_periods=10).median())
# deseasonalised YoY of ln R (same-DOY comparisons cancel geometry/spectral seasonality)
for nm, lr in [('H1H3', lr13), ('H2H3', lr23), ('H1H2', lr12)]:
    m31 = lr.rolling(31, center=True, min_periods=10).median()
    yoy = (m31 - m31.shift(365)).dropna() * 100
    yy = yoy.groupby(yoy.index.year).median()
    A[f'{nm}_yoy_median_by_year_pct'] = {int(k): round(v, 2) for k, v in yy.items()}
# reference-zone sensitivity of PLR: each zone's yield normalised by each candidate reference sensor
plr = {}
for z in [1, 2, 3]:
    for ref in [1, 2, 3]:
        q = (Y[z] / H[ref]).dropna(); q = q[(q > 0.3) & (q < 1.3)]
        q.index = q.index.tz_localize('Asia/Bangkok')
        np.random.seed(0)
        try:
            rd, ci, _ = rdtools.degradation_year_on_year(q, recenter=True, confidence_level=95)
            plr[f'Y{z}/H{ref}'] = [round(rd, 2), round(ci[0], 2), round(ci[1], 2)]
        except Exception as e:
            plr[f'Y{z}/H{ref}'] = str(e)[:60]
    # sensor-free: yield ratio trend vs other zones
for a, b in [(1, 3), (2, 3), (1, 2)]:
    q = (Y[a] / Y[b]).where(PRc[a].notna() & PRc[b].notna()).dropna(); q = q[(q > 0.5) & (q < 1.5)]
    q.index = q.index.tz_localize('Asia/Bangkok'); np.random.seed(0)
    rd, ci, _ = rdtools.degradation_year_on_year(q, recenter=True, confidence_level=95)
    plr[f'Y{a}/Y{b} (sensor-free)'] = [round(rd, 2), round(ci[0], 2), round(ci[1], 2)]
A['plr_reference_matrix'] = plr
R['A_sensor'] = A

# ---------------- B. change-point sensitivity ----------------
B = {}
s7 = lr13.rolling(7, center=True, min_periods=4).median().dropna()
# deseasonalise using harmonics fitted on the pre-2025 stable period
m = lr13.notna().values & (idx < pd.Timestamp('2025-03-01'))
Xs = np.column_stack([np.ones(len(idx)), X_h]); bh_, *_ = np.linalg.lstsq(Xs[m], lr13.values[m], rcond=None)
lr13_ds = (lr13 - X_h @ bh_[1:]); s7d = lr13_ds.rolling(7, center=True, min_periods=4).median().dropna()
def brk(sig, algo, pen=None, n_bkps=None, model='l2', ms=60):
    x = sig.values.reshape(-1, 1)
    a = {'pelt': rpt.Pelt, 'binseg': rpt.Binseg, 'bottomup': rpt.BottomUp}[algo](model=model, min_size=ms).fit(x)
    b = a.predict(pen=pen) if pen is not None else a.predict(n_bkps=n_bkps)
    return [str(sig.index[min(i, len(sig) - 1)].date()) for i in b[:-1]]
grid = []
for series_nm, sig in [('raw', s7), ('deseasonalised', s7d)]:
    v = np.var(sig.values)
    for k in [5, 10, 15, 25, 40]:
        for ms in [30, 60, 90]:
            for model in ['l2', 'l1']:
                grid.append(dict(series=series_nm, algo='PELT', model=model, pen_mult=k, min_size=ms, breaks=brk(sig, 'pelt', pen=(v * k if model == 'l2' else np.sqrt(v) * k), model=model, ms=ms)))
    for algo in ['binseg', 'bottomup']:
        for nb in [2, 3, 5]:
            grid.append(dict(series=series_nm, algo=algo, model='l2', pen_mult=None, min_size=60, breaks=brk(sig, algo, n_bkps=nb, ms=60)))
G = pd.DataFrame(grid); G['n_breaks'] = G.breaks.apply(len)
# frequency of a break inside the two key windows
def inwin(bl, a, b): return any(pd.Timestamp(a) <= pd.Timestamp(x) <= pd.Timestamp(b) for x in bl)
G['break_Feb_Apr_2025'] = G.breaks.apply(lambda bl: inwin(bl, '2025-02-01', '2025-04-30'))
G['break_Jul_Sep_2025'] = G.breaks.apply(lambda bl: inwin(bl, '2025-07-01', '2025-09-30'))
G.to_csv('cp_sensitivity.csv', index=False)
B['n_configs'] = len(G)
B['share_with_break_Feb_Apr_2025'] = round(G.break_Feb_Apr_2025.mean() * 100, 1)
B['share_with_break_Jul_Sep_2025'] = round(G.break_Jul_Sep_2025.mean() * 100, 1)
B['share_with_any_2025_break'] = round((G.break_Feb_Apr_2025 | G.break_Jul_Sep_2025).mean() * 100, 1)
# segmented regression (continuous piecewise-linear, 1 and 2 knots, grid search) on deseasonalised daily ln R13
y = lr13_ds.dropna(); t = (y.index - y.index[0]).days.values.astype(float)
cand = np.arange(60, len(t) - 60, 3)
def sse_knots(ks):
    X = np.column_stack([np.ones_like(t), t] + [np.maximum(0, t - t[k]) for k in ks]); b, *_ = np.linalg.lstsq(X, y.values, rcond=None)
    r = y.values - X @ b; return (r ** 2).sum(), b
best1 = min(cand, key=lambda k: sse_knots([k])[0])
best2 = None; bs = np.inf
for i in cand[::3]:
    for j in cand[::3]:
        if j - i < 90: continue
        s_, _ = sse_knots([i, j])
        if s_ < bs: bs, best2 = s_, (i, j)
# refine
for di in range(-6, 7, 3):
    for dj in range(-6, 7, 3):
        ii, jj = best2[0] + di, best2[1] + dj
        if 60 <= ii < jj - 90 and jj < len(t) - 60:
            s_, _ = sse_knots([ii, jj])
            if s_ < bs: bs, best2 = s_, (ii, jj)
_, b1 = sse_knots([best1]); _, b2 = sse_knots(list(best2))
B['segmented_1knot'] = {'knot': str(y.index[best1].date()), 'slope_before_pct_yr': round(b1[1] * 36525, 2), 'slope_after_pct_yr': round((b1[1] + b1[2]) * 36525, 2)}
B['segmented_2knot'] = {'knots': [str(y.index[k].date()) for k in best2],
                        'slopes_pct_yr': [round(b2[1] * 36525, 2), round((b2[1] + b2[2]) * 36525, 2), round((b2[1] + b2[2] + b2[3]) * 36525, 2)]}
# moving-block bootstrap of residuals for the 1-knot date
_, bb = sse_knots([best1]); X1 = np.column_stack([np.ones_like(t), t, np.maximum(0, t - t[best1])]); fit = X1 @ bb; res = y.values - fit
L = 14; nb = int(np.ceil(len(res) / L)); kdates = []
for rep in range(300):
    starts = RNG.integers(0, len(res) - L, nb); rr = np.concatenate([res[s:s + L] for s in starts])[:len(res)]
    ystar = fit + rr
    def sse_star(k):
        X = np.column_stack([np.ones_like(t), t, np.maximum(0, t - t[k])]); b, *_ = np.linalg.lstsq(X, ystar, rcond=None); return ((ystar - X @ b) ** 2).sum()
    kk = min(cand[::2], key=sse_star); kdates.append(y.index[kk])
kd = pd.Series(kdates)
B['segmented_1knot_block_bootstrap_95CI'] = [str(kd.quantile(0.025).date()), str(kd.quantile(0.975).date())]
# Bayesian single change point in the mean of deseasonalised weekly-median ln R13 (conjugate normal, unknown variance, flat location prior)
w = lr13_ds.resample('W').median().dropna(); x = w.values; n = len(x); logp = np.full(n, -np.inf)
for k in range(8, n - 8):
    a, b_ = x[:k], x[k:]
    ss = ((a - a.mean()) ** 2).sum() + ((b_ - b_.mean()) ** 2).sum()
    logp[k] = -0.5 * np.log(len(a)) - 0.5 * np.log(len(b_)) - (n - 2) / 2 * np.log(ss)
post_ = np.exp(logp - logp.max()); post_ /= post_.sum()
cdf = np.cumsum(post_)
B['bayes_single_cp'] = {'map': str(w.index[post_.argmax()].date()), 'cred95': [str(w.index[np.searchsorted(cdf, 0.025)].date()), str(w.index[np.searchsorted(cdf, 0.975)].date())],
                        'mean_before': round(float(np.exp(x[:post_.argmax()].mean())), 3), 'mean_after': round(float(np.exp(x[post_.argmax():].mean())), 3)}
pd.Series(post_, index=w.index).to_csv('bayes_cp_posterior.csv')
R['B_changepoint'] = B

# ---------------- C. event-study robustness ----------------
yr1 = np.log(Y[1] / Y[3]).where(PRc[1].notna() & PRc[3].notna())
yr12 = np.log(Y[1] / Y[2]).where(PRc[1].notna() & PRc[2].notna())
yr2 = np.log(Y[2] / Y[3]).where(PRc[2].notna() & PRc[3].notna())
def delta(s, t0, pre=14, gap=3, post=14):
    a = s[t0 - pd.Timedelta(days=pre): t0 - pd.Timedelta(days=1)].dropna(); b = s[t0 + pd.Timedelta(days=gap + 1): t0 + pd.Timedelta(days=gap + post)].dropna()
    if len(a) < max(4, pre // 3) or len(b) < max(4, post // 3): return np.nan
    return (np.median(b) - np.median(a)) * 100
def cands(s, t0, excl=20, doyw=45):
    c = [t for t in s.index[30:-30] if all(abs((t - e).days) > excl for e in evd)]
    return [t for t in c if min(abs(t.dayofyear - t0.dayofyear), 365 - abs(t.dayofyear - t0.dayofyear)) <= doyw]
def perm_p(s, t0, **kw):
    obs = delta(s, t0, **kw)
    if np.isnan(obs): return np.nan, np.nan
    nl = np.array([delta(s, t, **kw) for t in cands(s, t0)]); nl = nl[~np.isnan(nl)]
    return obs, (np.sum(nl >= obs) + 1) / (len(nl) + 1)
test_events = ['C2', 'C3', 'M1', 'C4', 'C5', 'C6', 'T1']
EVd = dict(EV)
# C1 window sensitivity
win = []
for code in test_events:
    t0 = pd.Timestamp(EVd[code])
    for pre_, post_, gap in [(7, 7, 3), (14, 14, 3), (21, 21, 3), (28, 28, 3), (14, 14, 1), (14, 14, 5)]:
        o, p = perm_p(yr1, t0, pre=pre_, post=post_, gap=gap)
        win.append(dict(event=code, pre=pre_, post=post_, gap=gap, delta=round(o, 2) if not np.isnan(o) else None, p=round(p, 3) if not np.isnan(p) else None))
W = pd.DataFrame(win); W.to_csv('es_window_sensitivity.csv', index=False)
# C2 pre-trend diagnostic: Theil-Sen slope of ln rho1 over [-28,-1] vs seasonal placebo distribution of same statistic
def preslope(s, t0, L=28):
    q = s[t0 - pd.Timedelta(days=L): t0 - pd.Timedelta(days=1)].dropna()
    if len(q) < 12: return np.nan
    return stats.theilslopes(q.values, (q.index - q.index[0]).days.values).slope * 100
pt = {}
for code in test_events:
    t0 = pd.Timestamp(EVd[code]); o = preslope(yr1, t0)
    nl = np.array([preslope(yr1, t) for t in cands(yr1, t0)]); nl = nl[~np.isnan(nl)]
    p2 = (np.sum(np.abs(nl - np.median(nl)) >= abs(o - np.median(nl))) + 1) / (len(nl) + 1)
    pt[code] = {'pre_slope_pct_per_day': round(o, 3), 'null_median': round(float(np.median(nl)), 3), 'p_two': round(p2, 3)}
# C3 moving-block bootstrap CIs of effect size (block = 7 d) within pre and post windows, plus lag-1 autocorrelation
def mbb_ci(s, t0, B_=2000, L=7, pre=14, gap=3, post=14):
    a = s[t0 - pd.Timedelta(days=pre): t0 - pd.Timedelta(days=1)].dropna().values; b = s[t0 + pd.Timedelta(days=gap + 1): t0 + pd.Timedelta(days=gap + post)].dropna().values
    if len(a) < 6 or len(b) < 6: return None
    def rs(x):
        nb = int(np.ceil(len(x) / L)); st = RNG.integers(0, max(1, len(x) - L + 1), nb); return np.concatenate([x[s_:s_ + L] for s_ in st])[:len(x)]
    bs = np.array([(np.median(rs(b)) - np.median(rs(a))) * 100 for _ in range(B_)])
    return [round(float(np.quantile(bs, .025)), 2), round(float(np.quantile(bs, .975)), 2)]
mbb = {code: mbb_ci(yr1, pd.Timestamp(EVd[code])) for code in test_events}
mbb2 = {code: mbb_ci(yr2, pd.Timestamp(EVd[code])) for code in ['C4', 'C6']}
resid = (yr1 - yr1.rolling(29, center=True, min_periods=10).median()).dropna()
ac1 = float(pd.Series(resid.values).autocorr(1)); ac7 = float(pd.Series(resid.values).autocorr(7))
# C4 empirical test size: random placebo dates tested against their own seasonal null (leave-self-out)
pl_dates = [t for t in yr1.index[40:-40] if all(abs((t - e).days) > 20 for e in evd)]
sel = RNG.choice(len(pl_dates), 250, replace=False); rej = 0; tot = 0
for i in sel:
    t0 = pl_dates[i]; o = delta(yr1, t0)
    if np.isnan(o): continue
    nl = np.array([delta(yr1, t) for t in cands(yr1, t0) if abs((t - t0).days) > 20]); nl = nl[~np.isnan(nl)]
    p = (np.sum(nl >= o) + 1) / (len(nl) + 1); rej += p < 0.05; tot += 1
size = rej / tot
# C5 cloudy-day exclusion and alternative control zone
alt = {}
yr1_clear = yr1.where(H3 >= 3.0)
for code in test_events:
    t0 = pd.Timestamp(EVd[code])
    o1, p1 = perm_p(yr1_clear, t0); o2, p2 = perm_p(yr12, t0)
    alt[code] = {'clear_days_H3>=3': [None if np.isnan(o1) else round(o1, 2), None if np.isnan(p1) else round(p1, 3)],
                 'control_Zone2 (Y1/Y2)': [None if np.isnan(o2) else round(o2, 2), None if np.isnan(p2) else round(p2, 3)]}
# negative-control outcome: sensor ratio H1/H3 should not move at pure array events (already in res_ext); grid side already tested
R['C_event'] = {'pre_trend': pt, 'mbb_ci_yield_ratio_z1': mbb, 'mbb_ci_yield_ratio_z2': mbb2, 'resid_autocorr_lag1': round(ac1, 3),
                'resid_autocorr_lag7': round(ac7, 3), 'empirical_size_alpha05': round(size, 3), 'n_size_tests': tot, 'alternatives': alt,
                'window_summary': {code: {'min_delta': float(W[W.event == code].delta.min()), 'max_delta': float(W[W.event == code].delta.max()),
                                          'share_p_lt_05': round(float((W[W.event == code].p < 0.05).mean()), 2)} for code in test_events}}

# ---------------- D. PR truncation evidence ----------------
Dd = {}
for z in [1, 2, 3]:
    p = d[(d.z == z) & ~d.outage].pr_percent
    Dd[f'z{z}'] = {'n_exactly_90.00': int((p.round(2) == 90.0).sum()), 'n_in_(89.0,89.99)': int(((p > 89.0) & (p < 89.99)).sum()),
                   'n_in_(88.0,89.0]': int(((p > 88.0) & (p <= 89.0)).sum()), 'max': float(p.max())}
# implied PR from common reference on censored Z1 days (what the uncapped value would be under H3 scaled by pre-drift ratio)
c1 = d[(d.z == 1) & d.cens].set_index('date')
Dd['z1_censored_days_PRc_median'] = round(float(PRc[1].reindex(c1.index).median() * 100), 1)
R['D_truncation'] = Dd

# ---------------- E. uncertainty propagation & explicit cleaning objective ----------------
Rext = json.load(open('res_ext.json')); Rc = json.load(open('res_econ.json'))
iv = Rext['interval_rates_pct_per_day']; sp = Rext['interval_rates_split_T1']
def norm_from_ci(c): return c[0], (c[2] - c[1]) / 3.92
r_dry_ci = iv[4]['yr1']; r_wet_ci = iv[3]['yr1']; r_premon_ci = sp[0]['yr1']
E1 = d[d.z == 1].set_index('date').daily_production_kwh
Edry = E1[E1.index.month.isin([12, 1, 2, 3])].mean(); Ewet = E1[E1.index.month.isin([5, 6, 7, 8, 9, 10])].mean()
N = 10000
mu, sd = norm_from_ci(r_dry_ci); r_dry = -RNG.normal(mu, sd, N) / 100
mu, sd = norm_from_ci(r_wet_ci); r_wet = -RNG.normal(mu, sd, N) / 100
r_dry = np.clip(r_dry, 1e-5, None); r_wet = np.clip(r_wet, 1e-5, None)
TJ = json.load(open('res_tariff.json')); TW = TJ['energy_weighted_price_THB_kWh']; TAR = pd.read_pickle('tariff_daily.pkl')
pf_ = RNG.triangular(TW['low'] / TW['central'], 1.0, TW['high'] / TW['central'], N)   # TOU class / morning-share uncertainty
p_ = TJ['dry_DecMar_central'] * pf_
C1 = 10000 / 31490 * 2256.3e3                                    # literature unit cost scaled to Zone 1
C_ = RNG.uniform(C1 * 0.7, C1 * 1.3, N)                          # +-30 % around the literature-based cost
eta = RNG.uniform(0.70, 1.00, N)                                 # cleaning efficacy (fraction of deposit removed)
meter = RNG.normal(1.0, 0.005, N)                                # revenue/PV meter uncertainty (~class 0.5-1)
delta_days = RNG.uniform(0.0, 0.3, N)                            # downtime, day-equivalents of Zone 1 output per campaign
def Tstar(r, E, p, C, eta, dd):
    k = 1 + 2 * (1 - eta) / eta                                   # steady-state residual-soiling multiplier
    Ceff = C + p * E * dd
    return np.sqrt(2 * Ceff / (r * E * p * k)), k, Ceff
Td, kd_, Cd = Tstar(r_dry, Edry * meter, p_, C_, eta, delta_days); Tw, kw_, Cw = Tstar(r_wet, Ewet * meter, TJ['wet_MayOct_central'] * pf_, C_, eta, delta_days)
q = lambda a: [round(float(np.quantile(a, .5)), 1), round(float(np.quantile(a, .025)), 1), round(float(np.quantile(a, .975)), 1)]
Eo = {'T_dry_days': q(Td), 'T_wet_days': q(Tw), 'C1_THB': round(C1)}
for sc in [0.25, 0.5]:
    Eo[f'T_dry_days_cost{sc}'] = q(Tstar(r_dry, Edry * meter, p_, C_ * sc, eta, delta_days)[0]); Eo[f'T_wet_days_cost{sc}'] = q(Tstar(r_wet, Ewet * meter, TJ['wet_MayOct_central'] * pf_, C_ * sc, eta, delta_days)[0])
# daily cost curves J(T) = C_eff/T + p E r T k / 2 with 95 % band (for figure)
Tg = np.arange(10, 501, 2)
def Jband(r, E, k, Ceff):
    J = np.array([Ceff / T + p_ * E * meter * r * T * k / 2 for T in Tg])  # shape (len(Tg), N)
    return np.quantile(J, [0.025, 0.5, 0.975], axis=1)
Jd = Jband(r_dry, Edry, kd_, Cd); Jw = Jband(r_wet, Ewet, kw_, Cw)  # (price differences dry/wet < 0.2 %)
np.save('Jcurves.npy', np.stack([Jd, Jw])); np.save('Tgrid.npy', Tg)
# range of T within 5 % of the minimum (flatness of the optimum), central curve
for nm, J in [('dry', Jd[1]), ('wet', Jw[1])]:
    ok = Tg[J <= J.min() * 1.05]; Eo[f'T_within_5pct_{nm}'] = [int(ok.min()), int(ok.max())]
# haze-season policy (120 d) n cleanings vs 1, MC
W_ = 120
def season_cost(n, r, E, p, C, k):
    T = W_ / n; return E * r * k * T / 2 * W_ * p + C * (n - 1)
sav = []; best_n = []
for i in range(N):
    costs = [season_cost(n, r_dry[i], Edry * meter[i], p_[i], Cd[i], kd_[i]) for n in range(1, 7)]
    best_n.append(int(np.argmin(costs)) + 1); sav.append(costs[0] - min(costs))
for sc in [0.25, 0.5]:
    bn = []; sv = []
    for i in range(N):
        cc = [season_cost(n, r_dry[i], Edry * meter[i], p_[i], C_[i] * sc + p_[i] * Edry * meter[i] * delta_days[i], kd_[i]) for n in range(1, 7)]
        bn.append(int(np.argmin(cc)) + 1); sv.append(cc[0] - min(cc))
    Eo[f'haze_season_cost{sc}_best_n_share'] = {int(k): round(v, 3) for k, v in pd.Series(bn).value_counts(normalize=True).sort_index().items()}
    Eo[f'haze_season_cost{sc}_saving_kTHB'] = q(np.array(sv) / 1e3)
Eo['haze_season_saving_kTHB'] = q(np.array(sav) / 1e3); Eo['haze_season_best_n_mode'] = int(pd.Series(best_n).mode()[0])
Eo['haze_season_best_n_share'] = {int(k): round(v, 3) for k, v in pd.Series(best_n).value_counts(normalize=True).sort_index().items()}
# energy recovery MC: gains drawn from MBB CIs (normal approx) for d4-17; later windows scaled by observed persistence ratio
rec = {}
pers = Rext['persistence_z1_yield_ratio']
for code in ['C2', 'C5', 'C6', 'T1']:
    lo, hi = mbb[code]; g0 = pers[code]['d4-17']; sdg = (hi - lo) / 3.92
    g = RNG.normal(g0, sdg, N)
    ratio2 = max(pers[code]['d18-45'], 0) / g0; ratio3 = max(pers[code]['d46-90'], 0) / g0
    t0 = pd.Timestamp(EVd[code]); Eb = E1[t0 - pd.Timedelta(days=30): t0 + pd.Timedelta(days=60)].mean() * meter
    frac = lambda x: 1 - np.exp(-np.clip(x, 0, None) / 100)
    Erec = Eb * (frac(g) * 14 + frac(g * ratio2) * 28 + frac(g * ratio3) * 45)
    pw = float(TAR['central'][t0 + pd.Timedelta(days=4): t0 + pd.Timedelta(days=90)].mean())
    rec[code] = {'E_MWh': q(Erec / 1e3), 'value_kTHB': q(Erec * pw * pf_ / 1e3), 'tCO2e': q(Erec * 0.5562 / 1e3),
                 'payback_share_of_C': q(Erec * pw * pf_ / C_)}
Eo['recovered_MC'] = rec
# SRR soiling-loss value with tariff uncertainty and SRR CI (triangular on SR)
S = json.load(open('res_soiling.json'))['srr']
Ez = d.groupby('z').daily_production_kwh.sum()
srr_mc = {}
for z in ['1', '2', '3']:
    sr = RNG.triangular(S[z]['CI95'][0], S[z]['insolation_weighted_SR'], S[z]['CI95'][1], N)
    loss = Ez[int(z)] * meter * (1 / sr - 1)
    srr_mc[z] = {'MWh': q(loss / 1e3), 'MTHB': [round(x / 1e3, 3) for x in q(loss * TW['central'] * pf_ / 1e3)]}
Eo['srr_loss_MC'] = srr_mc
# PLR with reference-sensor drift uncertainty: Z3 envelope trend (-0.47, CI -0.89..-0.04) is an upper bound on residual reference drift
Rq = json.load(open('res_qc.json'))
mu, sd = norm_from_ci(Rq['sensor']['env_trend_z3_pct_per_yr'])
drift3 = RNG.normal(mu, sd, N)
plr_c = Rext['yoy_degradation_pct_per_yr']['z1_common']; mu2, sd2 = norm_from_ci([plr_c[0], plr_c[1], plr_c[2]])
plr_mc = RNG.normal(mu2, sd2, N) + drift3 * RNG.uniform(0, 1, N)     # 0-100 % of envelope trend attributed to sensor
Eo['PLR_z1_with_ref_uncertainty'] = q(plr_mc)
# economic scenarios (+-30 % cost, +-20 % tariff) for central T*
scen = []
for cf in [0.25, 0.5, 1.0]:
    for pf in [TW['low'], TW['central'], TW['high']]:
        C0, p0 = C1 * cf, pf
        scen.append(dict(cost_kTHB=round(C0 / 1e3), price=round(p0, 2), T_dry=round(np.sqrt(2 * C0 / (0.003085 * Edry * p0))), T_wet=round(np.sqrt(2 * C0 / (0.000439 * Ewet * p0)))))
Eo['scenarios'] = scen
# without-T1 robustness: soiling rate for the long C6->C7 interval and totals excluding T1
Eo['without_T1_recovered_total_MWh'] = round(sum(Rc['recovered'][k]['E_recovered_MWh_90d'] for k in ['C2', 'C5', 'C6']), 1)
Eo['with_T1_recovered_total_MWh'] = round(sum(Rc['recovered'][k]['E_recovered_MWh_90d'] for k in ['C2', 'C5', 'C6', 'T1']), 1)
Eo['Edry_kWh'] = round(Edry); Eo['Ewet_kWh'] = round(Ewet)
R['E_uncertainty'] = Eo
json.dump(R, open('res_robust.json', 'w'), indent=1, default=float)
print(json.dumps({k: v for k, v in R.items()}, indent=1, default=float)[:12000])
print(W.pivot_table(index='event', columns=['pre', 'gap'], values='delta').round(1))
