"""Step 8 (R3): identify the measurement plane of each zone's PR reference using the documented station geometry
(two thermopile pyranometers per zone: horizontal and 45° south-facing). Compares the seasonal shape of each
zone's implied insolation with clear-sky GHI and clear-sky 45°-south POA, and with the array's own yield envelope."""
import pandas as pd, numpy as np, pvlib, json, warnings
warnings.filterwarnings('ignore')
LAT, LON, ALT = 20.0, 100.0, 400        # regional grid point (exact site withheld)
H = pd.read_pickle('H.pkl'); d = pd.read_pickle('d_clean.pkl')
Y = d.pivot(index='date', columns='z', values='equivalent_hours').where(~d.pivot(index='date', columns='z', values='outage').fillna(True).astype(bool))
times = pd.date_range(H.index.min(), H.index.max() + pd.Timedelta(days=1), freq='10min', tz='Asia/Bangkok')
loc = pvlib.location.Location(LAT, LON, 'Asia/Bangkok', ALT); cs = loc.get_clearsky(times, model='ineichen'); sp = loc.get_solarposition(times)
def daily(x): s = x.resample('D').sum() * (10 / 60) / 1000; s.index = s.index.tz_localize(None); return s
Hcs = {'GHI (0°)': daily(cs.ghi)}
for tilt in [10, 20, 45]:
    poa = pvlib.irradiance.get_total_irradiance(tilt, 180, sp.apparent_zenith, sp.azimuth, cs.dni, cs.ghi, cs.dhi, albedo=0.2, model='isotropic')['poa_global']
    Hcs[f'POA {tilt}° S'] = daily(poa)
pre = slice('2023-05-01', '2025-02-28')
doy = lambda idx: idx.dayofyear.values
def season_amp(s):
    s = s.dropna(); t = 2 * np.pi * doy(s.index) / 365.25
    X = np.column_stack([np.ones(len(s)), np.sin(t), np.cos(t), np.sin(2 * t), np.cos(2 * t)]); b, *_ = np.linalg.lstsq(X, s.values, rcond=None)
    g = np.linspace(0, 2 * np.pi, 366); f = b[0] + b[1] * np.sin(g) + b[2] * np.cos(g) + b[3] * np.sin(2 * g) + b[4] * np.cos(2 * g)
    return round(float((f.max() - f.min()) / 2 / b[0] * 100), 1), int(np.argmax(f) + 1)
out = {'model_ratio_amp_pct': {}, 'envelope_amp_pct': {}, 'rmse_vs_model_shape': {}}
# modelled clear-sky ratio POA45/GHI seasonal amplitude
for k in ['POA 10° S', 'POA 20° S', 'POA 45° S']:
    out['model_ratio_amp_pct'][f'{k} / GHI'] = season_amp(Hcs[k] / Hcs['GHI (0°)'])
# observed: 31-day P95 envelope of each zone's implied insolation (pre-drift period) divided by each clear-sky plane
series = {f'H{z} (sensor)': H[z] for z in [1, 2, 3]}
series.update({f'Yf{z} (array)': Y[z] for z in [1, 2, 3]})
for nm, s in series.items():
    for k, hc in Hcs.items():
        env = (s / hc.reindex(s.index)).rolling(31, center=True, min_periods=12).quantile(0.95)[pre]
        out['envelope_amp_pct'][f'{nm} vs {k}'] = season_amp(env)
# monthly envelope table for the figure
mon = {}
for nm, s in series.items():
    e = (s / Hcs['GHI (0°)'].reindex(s.index)).rolling(31, center=True, min_periods=12).quantile(0.95)[pre]
    mon[nm] = e.groupby(e.index.month).median().round(3).to_dict()
for k in ['POA 45° S', 'POA 20° S', 'POA 10° S']:
    r = (Hcs[k] / Hcs['GHI (0°)']); mon[f'clear-sky {k}/GHI'] = r.groupby(r.index.month).mean().round(3).to_dict()
out['monthly_envelope_vs_GHI'] = mon
json.dump(out, open('res_plane.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
