import pandas as pd, numpy as np, json, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from scipy import stats
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': '#e6e5e0', 'grid.linewidth': 0.6, 'axes.edgecolor': '#8a8984',
                     'axes.labelcolor': '#0b0b0b', 'xtick.color': '#52514e', 'ytick.color': '#52514e', 'legend.frameon': False})
ZC = {1: '#2a78d6', 2: '#eb6834', 3: '#1baf7a'}; INK2 = '#52514e'; MUTED = '#9b9a95'; VIO = '#4a3aa7'
DPI = 600
d = pd.read_pickle('d_clean.pkl'); PRc = pd.read_pickle('PRc.pkl'); H = pd.read_pickle('H.pkl'); env = pd.read_pickle('env.pkl')
Rq = json.load(open('res_qc.json')); Rs = json.load(open('res_soiling.json')); Re = json.load(open('res_ext.json'))
Rg = json.load(open('res_grid.json')); Rc = json.load(open('res_econ.json')); es = pd.read_csv('event_study.csv')
pv = lambda c: d.pivot(index='date', columns='z', values=c)
Y = pv('equivalent_hours'); PRown = pv('pr_percent'); OUT = pv('outage').fillna(True).astype(bool); CEN = pv('cens').fillna(False).astype(bool)
EV = [('C1', '2023-05-06'), ('C2', '2024-03-09'), ('C3', '2024-06-23'), ('M1', '2024-06-25'), ('C4', '2025-04-25'),
      ('C5', '2025-12-26'), ('C6', '2026-03-23'), ('T1', '2026-06-11'), ('C7', '2026-09-05')]
def evlines(ax, labels=False, y=None):
    for k, v in EV:
        c = MUTED if k[0] == 'C' else VIO
        ax.axvline(pd.Timestamp(v), color=c, lw=0.8, ls='-' if k[0] == 'C' else '--', zorder=0)
        if labels:
            off = 6 if k == 'M1' else (-6 if k == 'C3' else 0)
            ax.annotate(k, (pd.Timestamp(v), y), xytext=(off, 0), textcoords='offset points', ha='center', fontsize=7, color=INK2)
def save(fig, n):
    fig.savefig(f'figs/Fig{n}.png', dpi=DPI, bbox_inches='tight'); fig.savefig(f'figs/Fig{n}_preview.png', dpi=110, bbox_inches='tight'); plt.close(fig)
import os; os.makedirs('figs', exist_ok=True)

# ---------- Fig 1 framework ----------
fig, ax = plt.subplots(figsize=(7.2, 4.0)); ax.axis('off'); ax.set_xlim(0, 10); ax.set_ylim(0, 6)
def box(x, y, w, h, t, fc='#f4f3ef', ec='#8a8984', fs=7.6, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.04,rounding_size=0.12', fc=fc, ec=ec, lw=0.8))
    ax.text(x + w / 2, y + h / 2, t, ha='center', va='center', fontsize=fs, color='#0b0b0b', wrap=True, fontweight='bold' if bold else 'normal')
def arr(x1, y1, x2, y2): ax.annotate('', (x2, y2), (x1, y1), arrowprops=dict(arrowstyle='-|>', color=INK2, lw=0.9))
box(0.1, 4.5, 2.9, 1.3, 'Inputs\n3 zones × 1,283 days\nY$_f$, PR, T$_{amb}$, status\n+ 9 O&M log entries', fc='#eaf1fb', fs=7)
box(3.45, 4.5, 3.0, 1.3, 'Layer 1 – Metrological audit\nPR truncation (90 %), bias vs divergence\ncross-zone ratios H$_i$/H$_3$\nclear-sky envelope, change points', fc='#fbeee8', fs=7)
box(6.9, 4.5, 3.0, 1.3, 'Layer 2 – Re-referencing\ncommon-ref. PR$_c$ = Y$_{f,i}$/H$_3$\nsensor-free ratio Y$_{f,i}$/Y$_{f,3}$\nthermal correction', fc='#e8f6f0', fs=7)
box(0.1, 2.3, 3.0, 1.6, 'Layer 3 – Log-anchored\nevent study\nseasonal permutation null,\nblock bootstrap, pre-trends,\nwindow & control sensitivity', fs=7)
box(3.45, 2.3, 3.0, 1.6, 'Layer 4 – Channel\nattribution\narray (yield ratio) vs\nsensor (H ratio) vs grid\n(DOW-adjusted TOST ±3 %)', fs=7)
box(6.9, 2.3, 3.0, 1.6, 'Layer 5 – Loss & decision\nSRR soiling ratio, YoY PLR\ncleaning objective J(T)\nMonte-Carlo 95 % UI', fs=7)
box(0.6, 0.3, 8.8, 1.2, 'Outputs: verified / null / unexplained O&M effects · sensor-health verdicts\nKPI false-compliance flags · season-adaptive cleaning calendar', fc='#ffffff', fs=7.5, bold=True)
arr(3.0, 5.15, 3.45, 5.15); arr(6.45, 5.15, 6.9, 5.15)
for xx in [1.6, 4.95, 8.4]: arr(8.4 if xx==8.4 else 8.0, 4.5, xx, 3.9)
for xx in [1.6, 4.95, 8.4]: arr(xx, 2.3, xx if xx==4.95 else (2.2 if xx<4 else 7.8), 1.5)
save(fig, 1)

# ---------- Fig 2 data overview ----------
fig, axs = plt.subplots(3, 1, figsize=(7.2, 6.4), sharex=True, gridspec_kw={'height_ratios': [2.2, 1.6, 0.7]})
for z in [1, 2, 3]:
    s = Y[z].where(~OUT[z]); axs[0].plot(s.rolling(7, center=True, min_periods=3).median(), color=ZC[z], lw=1.2, label=f'Zone {z} ({Rq["kwp"][str(z)]:.0f} kWp)')
axs[0].set_ylabel('Y$_f$ (kWh kWp$^{-1}$ d$^{-1}$)'); axs[0].legend(ncol=3, loc='lower left', fontsize=7.5)
evlines(axs[0], True, 5.6); axs[0].set_ylim(1.5, 5.9); axs[0].text(0.005, 0.97, '(a)', transform=axs[0].transAxes, va='top', fontweight='bold')
for z in [1, 2, 3]:
    s = PRown[z].where(~OUT[z]); axs[1].plot(s.rolling(7, center=True, min_periods=3).median(), color=ZC[z], lw=1.0)
axs[1].axhline(90, color='#0b0b0b', lw=0.8, ls=':'); axs[1].text(pd.Timestamp('2023-05-10'), 91, 'vendor PR cap = 90 %', fontsize=7, color=INK2)
axs[1].set_ylabel('Reported PR (%)'); evlines(axs[1]); axs[1].set_ylim(40, 95); axs[1].text(0.005, 0.97, '(b)', transform=axs[1].transAxes, va='top', fontweight='bold')
for i, z in enumerate([1, 2, 3]):
    o = OUT[z][OUT[z]].index; c = CEN[z][CEN[z]].index
    axs[2].plot(c, np.full(len(c), i + 0.15), '|', color=ZC[z], ms=6, mew=0.6); axs[2].plot(o, np.full(len(o), i - 0.2), 'x', color='#0b0b0b', ms=3, mew=0.6)
axs[2].set_yticks([0, 1, 2]); axs[2].set_yticklabels(['Z1', 'Z2', 'Z3']); axs[2].set_ylim(-0.6, 2.6); axs[2].grid(False)
axs[2].text(0.005, 1.05, '(c) | censored PR day   × outage/invalid day', transform=axs[2].transAxes, fontsize=7.5, fontweight='bold')
fig.align_ylabels(); save(fig, 2)

# ---------- Fig 3 sensor audit ----------
fig, axs = plt.subplots(2, 2, figsize=(7.2, 5.6))
ax = axs[0, 0]
r13 = (H[1] / H[3]).rolling(7, center=True, min_periods=4).median(); r23 = (H[2] / H[3]).rolling(7, center=True, min_periods=4).median()
ax.plot(r13, color=ZC[1], lw=1, label='H$_1$/H$_3$'); ax.plot(r23, color=ZC[2], lw=1, label='H$_2$/H$_3$')
bks = [pd.Timestamp(x) for x in Rq['sensor']['H1H3_breaks']]; segs = Rq['sensor']['H1H3_segment_medians']
edges = [r13.dropna().index[0]] + bks + [r13.dropna().index[-1]]
for i in range(len(segs)): ax.hlines(segs[i], edges[i], edges[i + 1], color='#0b0b0b', lw=1.4)
ax.set_ylabel('Insolation ratio (7-d median)'); ax.legend(fontsize=7, loc='lower left'); evlines(ax); ax.set_title('(a) Cross-zone reference ratios + PELT segments', fontsize=8.5, loc='left')
ax.tick_params(axis='x', labelsize=7, rotation=30)
ax = axs[0, 1]
for z in [1, 2, 3]:
    s = env[z].dropna(); ax.plot(s, color=ZC[z], lw=1, label=f'Zone {z}: {Rq["sensor"][f"env_trend_z{z}_pct_per_yr"][0]:+.1f} % yr$^{{-1}}$')
    t = (s.index - s.index[0]).days.values / 365.25; r = stats.theilslopes(s.values, t); ax.plot(s.index, r.intercept + r.slope * t, color=ZC[z], lw=0.8, ls='--')
ax.set_ylabel('Clear-sky envelope index (P95 of H/H$_{cs}$)'); ax.legend(fontsize=7, loc='lower left'); ax.set_title('(b) Clear-sky envelope trend (Theil–Sen)', fontsize=8.5, loc='left')
ax.tick_params(axis='x', labelsize=7, rotation=30)
ax = axs[1, 0]
mc = CEN.resample('MS').mean() * 100; rr = (H[1] / H[3]).resample('MS').median()
ax.bar(mc.index, mc[1], width=20, color=ZC[1], label='Zone 1'); ax.set_ylabel('Share of PR-censored days, Zone 1 (%)')
ax2 = ax.twinx(); ax2.plot(rr.index, rr.values, color='#0b0b0b', lw=1, marker='o', ms=2.5); ax2.set_ylabel('Monthly median H$_1$/H$_3$'); ax2.grid(False); ax2.spines['right'].set_visible(True)
ax.set_title(f'(c) Truncation tracks inter-zone divergence (ρ = {Rq["sensor"]["corr_cens_z1_vs_ratio_spearman"]:.2f})', fontsize=8.5, loc='left'); ax.tick_params(axis='x', labelsize=7, rotation=30)
ax = axs[1, 1]
labs = ['Zone 1', 'Zone 2', 'Zone 3']; x = np.arange(3); w = 0.36
own = [Re['yoy_degradation_pct_per_yr'][f'z{z}_own'] for z in [1, 2, 3]]; com = [Re['yoy_degradation_pct_per_yr'][f'z{z}_common'] for z in [1, 2, 3]]
ax.bar(x - w / 2 - 0.01, [o[0] for o in own], w, color='#c3c2b7', yerr=[[o[0] - o[1] for o in own], [o[2] - o[0] for o in own]], capsize=2, label='own sensor (reported)')
ax.bar(x + w / 2 + 0.01, [c[0] for c in com], w, color=[ZC[1], ZC[2], ZC[3]], yerr=[[c[0] - c[1] for c in com], [c[2] - c[0] for c in com]], capsize=2, label='common reference (H$_3$)')
for i in range(3):
    ax.text(x[i] - w / 2, (own[i][2] + 0.25) if own[i][0] > 0 else (own[i][1] - 0.7), f'{own[i][0]:+.1f}', ha='center', fontsize=7)
    ax.text(x[i] + w / 2, com[i][1] - 0.7, f'{com[i][0]:+.1f}', ha='center', fontsize=7)
ax.axhline(0, color='#0b0b0b', lw=0.8); ax.set_xticks(x); ax.set_xticklabels(labs); ax.set_ylabel('YoY performance-loss rate (% yr$^{-1}$, 95 % CI)')
ax.legend(fontsize=7, loc='upper right'); ax.set_title('(d) PLR sign reversal under re-referencing', fontsize=8.5, loc='left'); ax.set_ylim(-6.5, 7)
fig.tight_layout(); save(fig, 3)

# ---------- Fig 4 own vs common PR, monthly, zone 1 ----------
fig, ax = plt.subplots(figsize=(7.2, 3.0))
m_own = (PRown[1].where(~OUT[1]) / 100).resample('MS').median(); m_com = PRc[1].resample('MS').median(); m3 = PRc[3].resample('MS').median()
ax.plot(m_own.index, m_own * 100, color='#8a8984', marker='s', ms=3, lw=1, label='Zone 1, reported PR (own sensor)')
ax.plot(m_com.index, m_com * 100, color=ZC[1], marker='o', ms=3, lw=1.4, label='Zone 1, common-reference PR$_c$ (thermally corrected)')
ax.plot(m3.index, m3 * 100, color=ZC[3], marker='^', ms=3, lw=1, label='Zone 3, PR$_c$ (reference zone)')
ax.axhline(80, color='#0b0b0b', lw=0.7, ls=':'); ax.text(pd.Timestamp('2024-08-15'), 88.5, 'dotted line: illustrative 80 % PR guarantee', fontsize=7, color=INK2)
for t in Rc['false_compliance_list']:
    tt = pd.Timestamp(t + '-01'); ax.axvspan(tt, tt + pd.offsets.MonthEnd(1), color='#eda100', alpha=0.25, lw=0)
ax.set_ylabel('Monthly median PR (%)'); ax.legend(fontsize=7, loc='lower left', ncol=1); evlines(ax)
ax.text(0.99, 0.04, 'shaded: false-compliance months', transform=ax.transAxes, ha='right', fontsize=7, color=INK2)
save(fig, 4)

# ---------- Fig 5 event-study forest ----------
fig, axs = plt.subplots(1, 2, figsize=(7.2, 4.0), sharey=True)
order = ['C1', 'C2', 'C3', 'M1', 'C4', 'C5', 'C6', 'T1']
nulls = pd.read_pickle('nulls.pkl')
for j, z in enumerate([1, 2]):
    ax = axs[j]
    for i, code in enumerate(order):
        row = es[(es.event == code) & (es.zone == z) & (es.metric == 'yield-ratio')].iloc[0]
        row2 = es[(es.event == code) & (es.zone == z) & (es.metric == 'common-ref')].iloc[0]
        nl = nulls.get((code, z), np.array([]))
        if len(nl) > 10: ax.plot([np.quantile(nl, .025), np.quantile(nl, .975)], [i, i], color='#d9d8d2', lw=6, solid_capstyle='round', zorder=1)
        if pd.notna(row.delta_pct):
            sig = row.p_one < 0.05
            ax.plot(row.delta_pct, i - 0.12, 'o', ms=6, mfc=ZC[z] if sig else 'white', mec=ZC[z], mew=1.2, zorder=3)
        if pd.notna(row2.delta_pct): ax.plot(row2.delta_pct, i + 0.14, 'D', ms=4, mfc='#52514e' if row2.p_one < 0.05 else 'white', mec='#52514e', zorder=3)
    ax.axvline(0, color='#0b0b0b', lw=0.7); ax.set_title(f'Zone {z} (vs Zone 3)', fontsize=9, loc='left')
    if z == 2: ax.set_xlim(-20, 80)
    else: ax.set_xlim(-12, 22)
axs[0].set_yticks(range(len(order))); axs[0].set_yticklabels(['C1 06/05/23', 'C2 09/03/24', 'C3 23/06/24', 'M1 25/06/24 (meter cal.)', 'C4 25/04/25', 'C5 26/12/25', 'C6 23/03/26', 'T1 11/06/26 (TX PM)'], fontsize=7.5)
axs[0].invert_yaxis()
from matplotlib.lines import Line2D
h = [Line2D([], [], marker='o', ls='', mfc=ZC[1], mec=ZC[1], label='yield ratio, p<0.05'), Line2D([], [], marker='o', ls='', mfc='white', mec=ZC[1], label='yield ratio, n.s.'),
     Line2D([], [], marker='D', ls='', mfc='#52514e', mec='#52514e', ms=4, label='common-ref PR$_c$, p<0.05'), Line2D([], [], color='#d9d8d2', lw=6, label='seasonal permutation null, 95 %')]
fig.supxlabel('Δ median, post (d+4…+17) − pre (d−14…−1), log-% points', fontsize=8.5, y=0.07); fig.legend(handles=h, loc='lower center', ncol=4, fontsize=7, bbox_to_anchor=(0.5, -0.02)); fig.tight_layout(rect=(0, 0.08, 1, 1)); save(fig, 5)

# ---------- Fig 6 lag & persistence ----------
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0))
ax = axs[0]
cols = {'C2': '#2a78d6', 'C4': '#1baf7a', 'C5': '#eda100', 'C6': '#4a3aa7'}
for c, col in cols.items():
    v = Rs['lag_profile'][f'{c}_z1']; ax.plot(range(len(v)), v, marker='o', ms=3, color=col, lw=1.2, label=c)
ax.axhline(0, color='#0b0b0b', lw=0.7); ax.axvspan(-0.3, 3.5, color='#f4f3ef', zorder=0); ax.text(1.6, -12.5, 'campaign\nwindow', ha='center', fontsize=7, color=INK2)
ax.set_xlabel('Days after logged cleaning date'); ax.set_ylabel('Zone 1 PR$_c$ vs pre-median (log-%)'); ax.legend(fontsize=7, ncol=2, loc='lower right'); ax.set_title('(a) Recovery lag', fontsize=8.5, loc='left')
ax = axs[1]
ev4 = ['C2', 'C5', 'C6', 'T1']; win = ['d4-17', 'd18-45', 'd46-90']; wl = ['d4–17', 'd18–45', 'd46–90']; wc = ['#2a78d6', '#7fb0ea', '#c7dcf6']
x = np.arange(len(ev4)); w = 0.26
for k in range(3):
    vals = [Re['persistence_z1_yield_ratio'][e][win[k]] for e in ev4]
    ax.bar(x + (k - 1) * (w + 0.02), vals, w, color=wc[k], label=wl[k])
ax.axhline(0, color='#0b0b0b', lw=0.7); ax.set_xticks(x); ax.set_xticklabels(ev4); ax.set_ylabel('Δ log(Y$_{f,1}$/Y$_{f,3}$) vs pre (log-%)'); ax.legend(fontsize=7, title='post window', title_fontsize=7)
ax.set_title('(b) Persistence of Zone 1 gains', fontsize=8.5, loc='left'); fig.tight_layout(); save(fig, 6)

# ---------- Fig 7 sawtooth + monthly slopes ----------
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0), gridspec_kw={'width_ratios': [1.7, 1]})
ax = axs[0]; yr1 = (Y[1] / Y[3]).where(PRc[1].reindex(Y.index).notna() & PRc[3].reindex(Y.index).notna())
s = yr1['2025-04-01':]; ax.plot(s.index, s.values, '.', ms=2, color='#9fc3ee'); ax.plot(s.rolling(7, center=True, min_periods=3).median(), color=ZC[1], lw=1.3)
for ii, row in enumerate(Re['interval_rates_pct_per_day'][-3:-1] + Re['interval_rates_split_T1']):
    a, b = pd.Timestamp(row['from']) + pd.Timedelta(days=5), pd.Timestamp(row['to']) - pd.Timedelta(days=1)
    q = np.log(yr1[a:b].dropna()); t = (q.index - q.index[0]).days.values; r = stats.theilslopes(q.values, t)
    ax.plot(q.index, np.exp(r.intercept + r.slope * t), color='#0b0b0b', lw=1.1, ls='--')
    ax.text(q.index[len(q) // 2], 1.13 if row['yr1'][0] > -0.1 else (0.72 if ii % 2 else 0.65), f'{row["yr1"][0]:+.2f} % d$^{{-1}}$', fontsize=7, ha='center', bbox=dict(fc='white', ec='none', pad=0.5))
ax.set_ylim(0.6, 1.25); ax.set_ylabel('Y$_{f,1}$/Y$_{f,3}$'); evlines(ax, True, 1.21); ax.set_xlim(pd.Timestamp('2025-04-01'), pd.Timestamp('2026-09-15')); ax.set_title('(a) Relative soiling saw-tooth, Zone 1', fontsize=8.5, loc='left'); ax.tick_params(axis='x', labelsize=7, rotation=30)
ax = axs[1]; ms = Re['monthly_median_slope_yr1']; mm = np.arange(1, 13); vals = [ms[str(m)] for m in mm]
ax.bar(mm, vals, color=['#eb6834' if m in [12, 1, 2, 3, 4] else '#2a78d6' for m in mm], width=0.7)
ax.axhline(0, color='#0b0b0b', lw=0.7); ax.set_xticks(mm); ax.set_xticklabels(list('JFMAMJJASOND')); ax.set_ylabel('Median within-month slope (% d$^{-1}$)')
ax.set_title('(b) Seasonality of relative slope', fontsize=8.5, loc='left'); fig.tight_layout(); save(fig, 7)

# ---------- Fig 8 grid-side equivalence ----------
fig, ax = plt.subplots(figsize=(5.2, 2.8))
rows = [('M1 load', 'M1_load_DOWadj_4wk'), ('M1 grid purchase', 'M1_purchased_DOWadj_4wk'), ('T1 load', 'T1_load_DOWadj_4wk'), ('T1 grid purchase', 'T1_purchased_DOWadj_4wk'),
        ('C3 load', 'C3_load_DOWadj_4wk'), ('C3 grid purchase', 'C3_purchased_DOWadj_4wk')]
for i, (lab, k) in enumerate(rows):
    v = Rg[k]; ok = v['p_TOST_3pct'] < 0.05
    ax.plot(v['ci95'], [i, i], color=VIO if ok else '#8a8984', lw=2); ax.plot(v['diff_pct'], i, 'o', ms=6, color=VIO if ok else '#8a8984', mfc=VIO if ok else 'white')
    ax.text(5.6, i, f"p$_{{TOST}}$={v['p_TOST_3pct']:.3f}", va='center', fontsize=7)
ax.axvspan(-3, 3, color='#f4f3ef', zorder=0); ax.axvline(0, color='#0b0b0b', lw=0.7)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=7.5); ax.invert_yaxis(); ax.set_xlim(-6, 8)
ax.set_xlabel('DOW-adjusted 28-d post − pre (%), 95 % CI\n(shaded: ±3 % equivalence margin)'); save(fig, 8)

# ---------- Fig 9 economics ----------
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0))
ax = axs[0]; Cs = np.linspace(30e3, 200e3, 60)
Edry = [g['E_day'] for g in Rc['optimal_interval'] if 'dry' in g['season']][0]; Ewet = [g['E_day'] for g in Rc['optimal_interval'] if 'wet' in g['season']][0]
for lab, r, E, col in [('dry season (r = 0.31 % d$^{-1}$)', 0.3085, Edry, '#eb6834'), ('wet/transition (r = 0.044 % d$^{-1}$)', 0.0439, Ewet, '#2a78d6')]:
    for p, ls in [(3.5, ':'), (4.2, '-'), (5.0, '--')]:
        ax.plot(Cs / 1e3, np.sqrt(2 * Cs / (r / 100 * E * p)), color=col, ls=ls, lw=1.2, label=lab if p == 4.2 else None)
ax.set_xlabel('Cleaning cost per campaign (kTHB)'); ax.set_ylabel('Optimal interval T* (days)'); ax.legend(fontsize=7, loc='upper left')
ax.text(0.98, 0.04, 'line style: 3.5 / 4.2 / 5.0 THB kWh$^{-1}$', transform=ax.transAxes, ha='right', fontsize=6.8, color=INK2)
ax.set_title('(a) Season-adaptive cleaning interval', fontsize=8.5, loc='left')
ax = axs[1]; ks = ['C2', 'C5', 'C6', 'T1']; vals = [Rc['recovered'][k]['E_recovered_MWh_90d'] for k in ks]
b = ax.bar(ks, vals, color=[ZC[1], ZC[1], ZC[1], VIO], width=0.6)
for i, k in enumerate(ks): ax.text(i, vals[i] + 1, f"{vals[i]:.0f} MWh\n{Rc['recovered'][k]['value_kTHB']:.0f} kTHB", ha='center', fontsize=7)
ax.set_ylabel('Recovered energy in 90 d (MWh)'); ax.set_ylim(0, max(vals) * 1.35); ax.set_title('(b) Value of verified recoveries', fontsize=8.5, loc='left')
fig.tight_layout(); save(fig, 9)
print('ok')
