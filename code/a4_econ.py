"""Step 4: recovered energy per cleaning (lower bound), season-adaptive optimal interval, KPI false-compliance, carbon."""
import pandas as pd, numpy as np, json
R = json.load(open('res_ext.json')); S = json.load(open('res_soiling.json'))
d = pd.read_pickle('d_clean.pkl'); PRc = pd.read_pickle('PRc.pkl')
E1 = d[d.z == 1].set_index('date').daily_production_kwh
TAR = pd.read_pickle('tariff_daily.pkl'); TJ = json.load(open('res_tariff.json'))
P = TJ['energy_weighted_price_THB_kWh']['central']   # PEA TOU 4.2.2 + Ft + VAT, energy-weighted over the record
EF = 0.5562    # kgCO2e/kWh, TGO CFP emission factor, grid mix 2022-2024 (update April 2026)
UNIT_COST = 10000 / 31490          # THB per W per cleaning (Mongkoldhumrongkul 2023: 10,000 THB per cleaning for 31.49 kWp)
KWP1 = 2256.3e3
C1 = UNIT_COST * KWP1              # Zone 1 campaign cost, linear scaling of the literature unit cost
out = {'price_THB_per_kWh': P, 'EF': EF, 'unit_cost_THB_per_W': round(UNIT_COST, 4), 'C1_THB': round(C1)}
rec = {}
for code, dt in [('C2', '2024-03-09'), ('C5', '2025-12-26'), ('C6', '2026-03-23'), ('T1', '2026-06-11')]:
    t0 = pd.Timestamp(dt); g = R['persistence_z1_yield_ratio'][code]
    Ebar = E1[t0 - pd.Timedelta(days=30): t0 + pd.Timedelta(days=60)].mean()
    gains = [max(g['d4-17'] or 0, 0) / 100, max(g['d18-45'] or 0, 0) / 100, max(g['d46-90'] or 0, 0) / 100]
    # gains are in log points relative to pre-event; convert to energy fraction of post level: 1-exp(-g)
    frac = [1 - np.exp(-x) for x in gains]
    Erec = Ebar * (frac[0] * 14 + frac[1] * 28 + frac[2] * 45)
    pw = float(TAR['central'][t0 + pd.Timedelta(days=4): t0 + pd.Timedelta(days=90)].mean())
    val = Erec * pw
    rec[code] = {'mean_daily_E1_kWh': round(Ebar, 0), 'E_recovered_MWh_90d': round(Erec / 1000, 1), 'window_price': round(pw, 3),
                 'value_kTHB': round(val / 1000, 0), 'CO2_t': round(Erec * EF / 1000, 1),
                 'breakeven_unit_cost_THB_per_W': round(val / KWP1, 4), 'breakeven_share_of_lit_cost': round(val / C1, 3)}
out['recovered'] = rec
# season-adaptive optimal interval (linear soiling, Kimber-type): T* = sqrt(2C/(r*E*p))
rates = {'dry (Dec-Mar, 2025/26 interval)': 0.3085, 'wet/transition (Apr-Dec 2025 interval)': 0.0439}
Edry = E1[(E1.index.month.isin([12, 1, 2, 3]))].mean(); Ewet = E1[(E1.index.month.isin([5, 6, 7, 8, 9, 10]))].mean()
grid = []
PD, PW = TJ['dry_DecMar_central'], TJ['wet_MayOct_central']
for C in [0.25 * C1, 0.5 * C1, C1]:
    for p in [TJ['energy_weighted_price_THB_kWh']['low'], P, TJ['energy_weighted_price_THB_kWh']['high']]:
        for lab, r in rates.items():
            Ed = Edry if 'dry' in lab else Ewet
            T = np.sqrt(2 * C / (r / 100 * Ed * p))
            avg_loss_frac = r / 100 * T / 2
            grid.append(dict(C_THB=C, p=p, season=lab, r_pct_day=r, E_day=round(Ed), T_opt_days=round(T, 0),
                             mean_soiling_loss_pct=round(avg_loss_frac * 100, 2)))
out['optimal_interval'] = grid
# cost per year of status quo vs adaptive in dry season (central C=100k, p=4.2): 120-day dry window
C, p = C1, PD; r = rates['dry (Dec-Mar, 2025/26 interval)'] / 100; W = 120
def season_cost(n_clean):  # n cleanings evenly spaced in W days, first at day 0 (clean start)
    T = W / n_clean; loss = Edry * r * T / 2 * W * p
    return loss + C * (n_clean - 1)   # starting cleaning counted outside window
sq = season_cost(1)
best = min(range(1, 7), key=season_cost)
out['dry_season_policy'] = {'status_quo_one_cleaning_cost_kTHB': round(sq / 1e3, 0), 'best_n': best,
                            'best_cost_kTHB': round(season_cost(best) / 1e3, 0),
                            'saving_kTHB': round((sq - season_cost(best)) / 1e3, 0),
                            'saving_MWh': round((Edry * r * W / 2 * W - Edry * r * (W / best) / 2 * W) / 1e3, 1)}
# KPI false compliance: months where own-sensor PR >= 0.80 but common-ref < 0.80 (Z1)
own = d[d.z == 1].set_index('date').pr_percent.reindex(PRc.index) / 100
m_own = own.resample('MS').median(); m_com = PRc[1].resample('MS').median()
fc = ((m_own >= 0.80) & (m_com < 0.80)); out['false_compliance_months_z1'] = int(fc.sum()); out['n_months'] = int(m_com.notna().sum())
out['false_compliance_list'] = [str(x.date())[:7] for x in fc[fc].index]
gap = (m_own - m_com) * 100
out['kpi_gap_z1_pp'] = {'2023': round(gap['2023'].mean(), 2), '2024': round(gap['2024'].mean(), 2), '2025': round(gap['2025'].mean(), 2), '2026': round(gap['2026'].mean(), 2)}
# soiling energy loss via SRR insolation-weighted SR
Ez = d.groupby('z').daily_production_kwh.sum()
out['srr_loss'] = {}
for z in ['1', '2', '3']:
    sr = S['srr'][z]['insolation_weighted_SR']; lo, hi = S['srr'][z]['CI95']
    E = Ez[int(z)]
    out['srr_loss'][z] = {'loss_MWh': round(E * (1 / sr - 1) / 1000, 0), 'range_MWh': [round(E * (1 / hi - 1) / 1000, 0), round(E * (1 / lo - 1) / 1000, 0)],
                          'value_MTHB': round(E * (1 / sr - 1) * P / 1e6, 2), 'CO2_t': round(E * (1 / sr - 1) * EF / 1000, 0)}
json.dump(out, open('res_econ.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'optimal_interval'}, indent=1))
print(pd.DataFrame(grid).to_string())
