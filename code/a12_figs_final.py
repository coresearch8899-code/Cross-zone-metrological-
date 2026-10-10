"""Final figure set (R11): every figure 16 cm wide, 900 dpi, one font size (8 pt) for all text,
panel labels only — (a), (b), (c) … centred above each panel, no panel subtitles.
Files are named by manuscript figure number: figs_final/Figure_01.png … Figure_10.png, Graphical_abstract.png."""
import os, json
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch
from matplotlib.lines import Line2D
from scipy import stats

FS = 8            # single font size (pt) for all text in all figures
W = 16 / 2.54     # figure width (in) = printed width in the manuscript (16 cm)
DPI = 900
OUT = 'figs_final'; os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': FS, 'axes.titlesize': FS, 'axes.labelsize': FS,
                     'xtick.labelsize': FS, 'ytick.labelsize': FS, 'legend.fontsize': FS, 'legend.title_fontsize': FS,
                     'figure.titlesize': FS, 'figure.labelsize': FS,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': '#e6e5e0',
                     'grid.linewidth': 0.6, 'axes.edgecolor': '#8a8984', 'axes.labelcolor': '#0b0b0b',
                     'xtick.color': '#52514e', 'ytick.color': '#52514e', 'legend.frameon': False})
ZC = {1: '#2a78d6', 2: '#eb6834', 3: '#1baf7a'}; INK2 = '#52514e'; MUTED = '#9b9a95'; VIO = '#4a3aa7'

def lab(ax, s):
    """Panel label only, centred above the panel."""
    ax.set_title(f'({s})', loc='center', fontsize=FS, fontweight='bold', pad=4)
def save(fig, name):
    fig.savefig(f'{OUT}/{name}.png', dpi=DPI); fig.savefig(f'{OUT}/{name}_preview.png', dpi=110); plt.close(fig)
def new(h, **kw):
    return plt.subplots(figsize=(W, h), layout='constrained', **kw)

d = pd.read_pickle('d_clean.pkl'); PRc = pd.read_pickle('PRc.pkl'); H = pd.read_pickle('H.pkl'); env = pd.read_pickle('env.pkl')
Rq = json.load(open('res_qc.json')); Rs = json.load(open('res_soiling.json')); Re = json.load(open('res_ext.json'))
Rg = json.load(open('res_grid.json')); Rc = json.load(open('res_econ.json')); Rr = json.load(open('res_robust.json'))
es = pd.read_csv('event_study.csv'); Wsens = pd.read_csv('es_window_sensitivity.csv'); G = pd.read_csv('cp_sensitivity.csv')
pv = lambda c: d.pivot(index='date', columns='z', values=c)
Y = pv('equivalent_hours'); PRown = pv('pr_percent'); OUTG = pv('outage').fillna(True).astype(bool); CEN = pv('cens').fillna(False).astype(bool)
EV = [('C1', '2023-05-06'), ('C2', '2024-03-09'), ('C3', '2024-06-23'), ('M1', '2024-06-25'), ('C4', '2025-04-25'),
      ('C5', '2025-12-26'), ('C6', '2026-03-23'), ('T1', '2026-06-11'), ('C7', '2026-09-05')]
def evlines(ax, labels=False, y=None):
    for k, v in EV:
        ax.axvline(pd.Timestamp(v), color=MUTED if k[0] == 'C' else VIO, lw=0.8, ls='-' if k[0] == 'C' else '--', zorder=0)
        if labels:
            off = 7 if k == 'M1' else (-7 if k == 'C3' else 0)
            ax.annotate(k, (pd.Timestamp(v), y), xytext=(off, 0), textcoords='offset points', ha='center', fontsize=FS, color=INK2)

# ---------- Figure 1: framework ----------
fig, ax = new(3.9); ax.axis('off'); ax.set_xlim(0, 10); ax.set_ylim(0, 6.2)
def box(x, y, w, h, t, fc='#f4f3ef', bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.04,rounding_size=0.12', fc=fc, ec='#8a8984', lw=0.8))
    ax.text(x + w / 2, y + h / 2, t, ha='center', va='center', fontsize=FS, color='#0b0b0b', linespacing=1.3, fontweight='bold' if bold else 'normal')
X = [0.05, 3.4, 6.75]; BW = 3.2
box(X[0], 4.4, BW, 1.7, 'Inputs\n3 zones × 1,283 days\nY$_f$, PR, T$_{amb}$, status\n9 O&M log entries', fc='#eaf1fb')
box(X[1], 4.4, BW, 1.7, 'Layer 1 – Metrological audit\nPR truncation at 90 %\nbias vs divergence (H$_i$/H$_3$)\nclear-sky envelope, change points', fc='#fbeee8')
box(X[2], 4.4, BW, 1.7, 'Layer 2 – Re-referencing\nPR$_c$ = Y$_{f,i}$ / H$_3$\nsensor-free ratio Y$_{f,i}$/Y$_{f,3}$\nthermal correction', fc='#e8f6f0')
box(X[0], 2.1, BW, 1.75, 'Layer 3 – Event study\nseasonal permutation null\nblock bootstrap, pre-trends\nwindow/control sensitivity')
box(X[1], 2.1, BW, 1.75, 'Layer 4 – Channel attribution\narray: yield ratio\nsensor: H ratio\ngrid: DOW-adjusted TOST ±3 %')
box(X[2], 2.1, BW, 1.75, 'Layer 5 – Loss and decision\nSRR soiling ratio, YoY PLR\ncleaning objective J(T)\nMonte-Carlo 95 % UI')
box(0.6, 0.15, 8.8, 1.3, 'Outputs: verified / null / unexplained O&M effects · sensor-health verdicts\nKPI false-compliance flags · season-adaptive cleaning calendar', fc='#ffffff', bold=True)
def arr(x1, y1, x2, y2): ax.annotate('', (x2, y2), (x1, y1), arrowprops=dict(arrowstyle='-|>', color=INK2, lw=0.9))
arr(X[0] + BW, 5.25, X[1], 5.25); arr(X[1] + BW, 5.25, X[2], 5.25)
for xc in [X[0] + BW / 2, X[1] + BW / 2, X[2] + BW / 2]: arr(X[2] + BW / 2, 4.4, xc, 3.85)
for xc, xe in [(X[0] + BW / 2, 2.2), (X[1] + BW / 2, X[1] + BW / 2), (X[2] + BW / 2, 7.8)]: arr(xc, 2.1, xe, 1.45)
save(fig, 'Figure_01')

# ---------- Figure 2: data overview ----------
fig, axs = new(6.0, nrows=3, sharex=True, gridspec_kw={'height_ratios': [2.2, 1.6, 0.8]})
for z in [1, 2, 3]:
    s = Y[z].where(~OUTG[z]); axs[0].plot(s.rolling(7, center=True, min_periods=3).median(), color=ZC[z], lw=1.1, label=f'Zone {z} ({Rq["kwp"][str(z)]:.0f} kWp)')
axs[0].set_ylabel('Y$_f$ (kWh kWp$^{-1}$ d$^{-1}$)'); axs[0].legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
evlines(axs[0], True, 5.65); axs[0].set_ylim(1.5, 6.0); lab(axs[0], 'a')
for z in [1, 2, 3]:
    s = PRown[z].where(~OUTG[z]); axs[1].plot(s.rolling(7, center=True, min_periods=3).median(), color=ZC[z], lw=1.0)
axs[1].axhline(90, color='#0b0b0b', lw=0.8, ls=':'); axs[1].text(pd.Timestamp('2023-05-10'), 92, 'reporting-layer truncation at 90 %', fontsize=FS, color=INK2)
axs[1].set_ylabel('Reported PR (%)'); evlines(axs[1]); axs[1].set_ylim(40, 98); lab(axs[1], 'b')
for i, z in enumerate([1, 2, 3]):
    o = OUTG[z][OUTG[z]].index; c = CEN[z][CEN[z]].index
    axs[2].plot(c, np.full(len(c), i + 0.15), '|', color=ZC[z], ms=6, mew=0.6); axs[2].plot(o, np.full(len(o), i - 0.2), 'x', color='#0b0b0b', ms=3, mew=0.6)
axs[2].set_yticks([0, 1, 2]); axs[2].set_yticklabels(['Z1', 'Z2', 'Z3']); axs[2].set_ylim(-0.6, 2.6); axs[2].grid(False); lab(axs[2], 'c')
axs[2].legend(handles=[Line2D([], [], marker='|', ls='', color=INK2, ms=6, mew=0.8, label='truncated PR day'),
                       Line2D([], [], marker='x', ls='', color='#0b0b0b', ms=4, mew=0.8, label='outage/invalid day')],
              loc='center left', bbox_to_anchor=(1.0, 0.5))
fig.align_ylabels(); save(fig, 'Figure_02')

# ---------- Figure 3: sensor audit ----------
fig, axs = new(5.9, nrows=2, ncols=2)
ax = axs[0, 0]
r13 = (H[1] / H[3]).rolling(7, center=True, min_periods=4).median(); r23 = (H[2] / H[3]).rolling(7, center=True, min_periods=4).median()
ax.plot(r13, color=ZC[1], lw=1, label='H$_1$/H$_3$'); ax.plot(r23, color=ZC[2], lw=1, label='H$_2$/H$_3$')
bks = [pd.Timestamp(x) for x in Rq['sensor']['H1H3_breaks']]; segs = Rq['sensor']['H1H3_segment_medians']
edges = [r13.dropna().index[0]] + bks + [r13.dropna().index[-1]]
for i in range(len(segs)): ax.hlines(segs[i], edges[i], edges[i + 1], color='#0b0b0b', lw=1.4, label='PELT segment median' if i == 0 else None)
ax.set_ylabel('Insolation ratio (7-d median)'); ax.set_ylim(0.5, 1.25); ax.legend(loc='lower left', ncol=3, handlelength=1.2, columnspacing=0.8); evlines(ax); lab(ax, 'a'); ax.tick_params(axis='x', rotation=30)
ax = axs[0, 1]
for z in [1, 2, 3]:
    s = env[z].dropna(); ax.plot(s, color=ZC[z], lw=1, label=f'Zone {z}: {Rq["sensor"][f"env_trend_z{z}_pct_per_yr"][0]:+.1f} % yr$^{{-1}}$')
    t = (s.index - s.index[0]).days.values / 365.25; r = stats.theilslopes(s.values, t); ax.plot(s.index, r.intercept + r.slope * t, color=ZC[z], lw=0.8, ls='--')
ax.set_ylabel('Clear-sky envelope index'); ax.set_ylim(0.55, 1.3); ax.legend(loc='upper right'); lab(ax, 'b'); ax.tick_params(axis='x', rotation=30)
ax = axs[1, 0]
mc = CEN.resample('MS').mean() * 100; rr = (H[1] / H[3]).resample('MS').median()
ax.bar(mc.index, mc[1], width=20, color=ZC[1]); ax.set_ylabel('Truncated PR days, Zone 1 (%)')
ax2 = ax.twinx(); ax2.plot(rr.index, rr.values, color='#0b0b0b', lw=1, marker='o', ms=2.5); ax2.set_ylabel('Monthly median H$_1$/H$_3$'); ax2.grid(False); ax2.spines['right'].set_visible(True)
lab(ax, 'c'); ax.tick_params(axis='x', rotation=30)
ax = axs[1, 1]
x = np.arange(3); w = 0.36
own = [Re['yoy_degradation_pct_per_yr'][f'z{z}_own'] for z in [1, 2, 3]]; com = [Re['yoy_degradation_pct_per_yr'][f'z{z}_common'] for z in [1, 2, 3]]
ax.bar(x - w / 2 - 0.01, [o[0] for o in own], w, color='#c3c2b7', yerr=[[o[0] - o[1] for o in own], [o[2] - o[0] for o in own]], capsize=2, label='own sensor (reported)')
ax.bar(x + w / 2 + 0.01, [c[0] for c in com], w, color=[ZC[1], ZC[2], ZC[3]], yerr=[[c[0] - c[1] for c in com], [c[2] - c[0] for c in com]], capsize=2, label='common reference (H$_3$)')
for i in range(3):
    ax.text(x[i] - w / 2, (own[i][2] + 0.25) if own[i][0] > 0 else (own[i][1] - 0.8), f'{own[i][0]:+.1f}', ha='center', fontsize=FS)
    ax.text(x[i] + w / 2, com[i][1] - 0.8, f'{com[i][0]:+.1f}', ha='center', fontsize=FS)
ax.axhline(0, color='#0b0b0b', lw=0.8); ax.set_xticks(x); ax.set_xticklabels(['Zone 1', 'Zone 2', 'Zone 3'])
ax.set_ylabel('YoY PLR (% yr$^{-1}$, 95 % CI)'); ax.legend(loc='upper right'); lab(ax, 'd'); ax.set_ylim(-7, 7.5)
save(fig, 'Figure_03')

# ---------- Figure 4: robustness ----------
fig = plt.figure(figsize=(W, 6.0), layout='constrained'); gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.05])
ax = fig.add_subplot(gs[0, :])
post = pd.read_csv('bayes_cp_posterior.csv', index_col=0, parse_dates=True).iloc[:, 0]
allb = pd.to_datetime(pd.Series([b for bl in G.breaks.apply(eval) for b in bl]))
cnt = allb.dt.to_period('M').value_counts().sort_index(); cnt.index = cnt.index.to_timestamp()
ax.bar(cnt.index, cnt.values / len(G) * 100, width=25, color='#c3c2b7')
ax2 = ax.twinx(); ax2.plot(post.index, post.values, color=VIO, lw=1.3); ax2.set_yticks([]); ax2.grid(False); ax2.set_ylim(0, post.max() * 1.45); ax2.spines['right'].set_visible(False)
B = Rr['B_changepoint']
for k in B['segmented_2knot']['knots']: ax.axvline(pd.Timestamp(k), color=ZC[1], ls='--', lw=1)
ax.axvspan(pd.Timestamp(B['segmented_1knot_block_bootstrap_95CI'][0]), pd.Timestamp(B['segmented_1knot_block_bootstrap_95CI'][1]), color=ZC[1], alpha=0.08, lw=0)
ax.set_ylabel('Configurations (%)'); ax.set_ylim(0, 115); lab(ax, 'a')
ax.legend(handles=[Patch(color='#c3c2b7', label=f'detector configurations with a break (n = {len(G)})'), Line2D([], [], color=VIO, lw=1.3, label='Bayesian posterior'),
                   Line2D([], [], color=ZC[1], ls='--', lw=1, label='segmented-regression knots'), Patch(color=ZC[1], alpha=0.15, label='95 % CI of one-knot onset')],
          loc='upper left', ncol=1)
ax = fig.add_subplot(gs[1, 0])
M = Rr['A_sensor']['plr_reference_matrix']; mat = np.array([[M[f'Y{z}/H{r}'][0] for r in [1, 2, 3]] for z in [1, 2, 3]])
im = ax.imshow(mat, cmap='RdBu', vmin=-8, vmax=8, aspect='auto')
for i in range(3):
    for j in range(3): ax.text(j, i, f'{mat[i, j]:+.1f}', ha='center', va='center', fontsize=FS, color='#0b0b0b')
ax.set_xticks(range(3)); ax.set_xticklabels(['H$_1$', 'H$_2$', 'H$_3$']); ax.set_yticks(range(3)); ax.set_yticklabels(['Y$_{f,1}$', 'Y$_{f,2}$', 'Y$_{f,3}$']); ax.grid(False)
ax.set_xlabel('Reference sensor'); lab(ax, 'b')
ax = fig.add_subplot(gs[1, 1])
cfg = [(7, 3), (14, 1), (14, 3), (14, 5), (21, 3), (28, 3)]; evs = ['C2', 'C3', 'M1', 'C4', 'C5', 'C6', 'T1']
D = np.array([[Wsens[(Wsens.event == e) & (Wsens.pre == a) & (Wsens.gap == g)].delta.iloc[0] for (a, g) in cfg] for e in evs])
P = np.array([[Wsens[(Wsens.event == e) & (Wsens.pre == a) & (Wsens.gap == g)].p.iloc[0] for (a, g) in cfg] for e in evs])
ax.imshow(D, cmap='Blues', vmin=-5, vmax=20, aspect='auto')
for i in range(len(evs)):
    for j in range(len(cfg)): ax.text(j, i, str(int(round(D[i, j]))) + ('*' if P[i, j] < 0.05 else ''), ha='center', va='center', fontsize=FS, color='white' if D[i, j] > 12 else '#0b0b0b')
ax.set_xticks(range(len(cfg))); ax.set_xticklabels([f'{a}/{g}' for a, g in cfg], rotation=45); ax.set_yticks(range(len(evs))); ax.set_yticklabels(evs); ax.grid(False)
ax.set_xlabel('Window length / gap (days)'); lab(ax, 'c')
save(fig, 'Figure_04')

# ---------- Figure 5: truncation evidence + monthly PR ----------
fig, axs = new(3.1, ncols=2, gridspec_kw={'width_ratios': [1, 2.0]})
ax = axs[0]; bins = np.arange(60, 92.01, 0.5)
for z in [1, 2, 3]:
    p = d[(d.z == z) & ~d.outage].pr_percent.dropna(); ax.hist(p.clip(upper=91.9), bins=bins, histtype='step', lw=1.1, color=ZC[z], label=f'Zone {z}')
ax.axvline(90, color='#0b0b0b', lw=0.7, ls=':'); ax.set_yscale('log'); ax.set_xlabel('Reported daily PR (%)'); ax.set_ylabel('Days (log scale)')
ax.set_ylim(0.7, 6000); ax.legend(loc='upper left', handlelength=1.2); lab(ax, 'a')
ax = axs[1]
own1 = d[d.z == 1].set_index('date'); own1 = own1.pr_percent.where(~own1.outage)
m_own = (own1 / 100).resample('MS').median(); m_com = PRc[1].resample('MS').median(); m3 = PRc[3].resample('MS').median()
ax.plot(m_own.index, m_own * 100, color='#8a8984', marker='s', ms=3, lw=1, label='Zone 1, reported PR')
ax.plot(m_com.index, m_com * 100, color=ZC[1], marker='o', ms=3, lw=1.3, label='Zone 1, PR$_c$')
ax.plot(m3.index, m3 * 100, color=ZC[3], marker='^', ms=3, lw=1, label='Zone 3, PR$_c$')
ax.axhline(80, color='#0b0b0b', lw=0.7, ls=':')
for t in Rc['false_compliance_list']:
    tt = pd.Timestamp(t + '-01'); ax.axvspan(tt, tt + pd.offsets.MonthEnd(1), color='#eda100', alpha=0.25, lw=0)
h, l = ax.get_legend_handles_labels(); h.append(Patch(color='#eda100', alpha=0.35)); l.append('false-compliance month')
evlines(ax); ax.set_ylabel('Monthly median PR (%)'); ax.set_ylim(55, 108); ax.legend(h, l, loc='upper left', ncol=2)
lab(ax, 'b'); ax.tick_params(axis='x', rotation=30)
save(fig, 'Figure_05')

# ---------- Figure 6: event-study forest ----------
fig, axs = new(4.0, ncols=2, sharey=True)
order = ['C1', 'C2', 'C3', 'M1', 'C4', 'C5', 'C6', 'T1']; nulls = pd.read_pickle('nulls.pkl')
for j, z in enumerate([1, 2]):
    ax = axs[j]
    for i, code in enumerate(order):
        row = es[(es.event == code) & (es.zone == z) & (es.metric == 'yield-ratio')].iloc[0]
        row2 = es[(es.event == code) & (es.zone == z) & (es.metric == 'common-ref')].iloc[0]
        nl = nulls.get((code, z), np.array([]))
        if len(nl) > 10: ax.plot([np.quantile(nl, .025), np.quantile(nl, .975)], [i, i], color='#d9d8d2', lw=6, solid_capstyle='round', zorder=1)
        if pd.notna(row.delta_pct):
            sig = row.p_one < 0.05; ax.plot(row.delta_pct, i - 0.12, 'o', ms=5.5, mfc=ZC[z] if sig else 'white', mec=ZC[z], mew=1.2, zorder=3)
        if pd.notna(row2.delta_pct): ax.plot(row2.delta_pct, i + 0.14, 'D', ms=4, mfc='#52514e' if row2.p_one < 0.05 else 'white', mec='#52514e', zorder=3)
    ax.axvline(0, color='#0b0b0b', lw=0.7); lab(ax, 'ab'[j]); ax.set_xlim(*((-20, 80) if z == 2 else (-12, 22)))
axs[0].set_yticks(range(len(order))); axs[0].set_yticklabels(['C1 06/05/23', 'C2 09/03/24', 'C3 23/06/24', 'M1 25/06/24', 'C4 25/04/25', 'C5 26/12/25', 'C6 23/03/26', 'T1 11/06/26'])
axs[0].invert_yaxis()
for a_ in axs: a_.set_xlabel('Δ post − pre (log-% points)')
fig.legend(handles=[Line2D([], [], marker='o', ls='', mfc=INK2, mec=INK2, label='yield ratio, p < 0.05'), Line2D([], [], marker='o', ls='', mfc='white', mec=INK2, label='yield ratio, n.s.'),
                    Line2D([], [], marker='D', ls='', mfc='#52514e', mec='#52514e', ms=4, label='common-reference PR$_c$, p < 0.05'), Line2D([], [], color='#d9d8d2', lw=6, label='permutation null, 95 %')],
           loc='outside lower center', ncol=2)
save(fig, 'Figure_06')

# ---------- Figure 7: recovery lag & persistence ----------
fig, axs = new(3.0, ncols=2)
ax = axs[0]
for c, col in {'C2': '#2a78d6', 'C4': '#1baf7a', 'C5': '#eda100', 'C6': '#4a3aa7'}.items():
    v = Rs['lag_profile'][f'{c}_z1']; ax.plot(range(len(v)), v, marker='o', ms=3, color=col, lw=1.1, label=c)
ax.axhline(0, color='#0b0b0b', lw=0.7); ax.axvspan(-0.3, 3.5, color='#f4f3ef', zorder=0); ax.text(1.6, -18.5, 'campaign window', ha='center', fontsize=FS, color=INK2); ax.set_ylim(-20, 19)
ax.set_xlabel('Days after logged cleaning date'); ax.set_ylabel('Zone 1 PR$_c$ vs pre-median (log-%)'); ax.legend(ncol=2, loc='lower right'); lab(ax, 'a')
ax = axs[1]; ev4 = ['C2', 'C5', 'C6', 'T1']; win = ['d4-17', 'd18-45', 'd46-90']; wl = ['d4–17', 'd18–45', 'd46–90']; wc = ['#2a78d6', '#7fb0ea', '#c7dcf6']
x = np.arange(len(ev4)); w = 0.26
for k in range(3): ax.bar(x + (k - 1) * (w + 0.02), [Re['persistence_z1_yield_ratio'][e][win[k]] for e in ev4], w, color=wc[k], label=wl[k])
ax.axhline(0, color='#0b0b0b', lw=0.7); ax.set_xticks(x); ax.set_xticklabels(ev4); ax.set_ylabel('Δ ln(Y$_{f,1}$/Y$_{f,3}$) vs pre (log-%)'); ax.set_ylim(-9, 23); ax.legend(title='post window', ncol=3, loc='upper left', columnspacing=0.8); lab(ax, 'b')
save(fig, 'Figure_07')

# ---------- Figure 8: saw-tooth + monthly slopes ----------
fig, axs = new(3.0, ncols=2, gridspec_kw={'width_ratios': [1.7, 1]})
ax = axs[0]; yr1 = (Y[1] / Y[3]).where(PRc[1].reindex(Y.index).notna() & PRc[3].reindex(Y.index).notna())
s = yr1['2025-04-01':]; ax.plot(s.index, s.values, '.', ms=2, color='#9fc3ee'); ax.plot(s.rolling(7, center=True, min_periods=3).median(), color=ZC[1], lw=1.2)
for ii, row in enumerate(Re['interval_rates_pct_per_day'][-3:-1] + Re['interval_rates_split_T1']):
    a, b = pd.Timestamp(row['from']) + pd.Timedelta(days=5), pd.Timestamp(row['to']) - pd.Timedelta(days=1)
    q = np.log(yr1[a:b].dropna()); t = (q.index - q.index[0]).days.values; r = stats.theilslopes(q.values, t)
    ax.plot(q.index, np.exp(r.intercept + r.slope * t), color='#0b0b0b', lw=1.0, ls='--')
    ax.text(q.index[len(q) // 2], 1.13 if row['yr1'][0] > -0.1 else (0.72 if ii % 2 else 0.65), f'{row["yr1"][0]:+.2f} % d$^{{-1}}$', fontsize=FS, ha='center', bbox=dict(fc='white', ec='none', pad=0.5))
ax.set_ylim(0.6, 1.27); ax.set_ylabel('Y$_{f,1}$/Y$_{f,3}$'); evlines(ax, True, 1.225); ax.set_xlim(pd.Timestamp('2025-04-01'), pd.Timestamp('2026-09-15')); lab(ax, 'a'); ax.tick_params(axis='x', rotation=30)
ax = axs[1]; ms = Re['monthly_median_slope_yr1']; mm = np.arange(1, 13)
ax.bar(mm, [ms[str(m)] for m in mm], color=['#eb6834' if m in [12, 1, 2, 3, 4] else '#2a78d6' for m in mm], width=0.7)
ax.axhline(0, color='#0b0b0b', lw=0.7); ax.set_xticks(mm); ax.set_xticklabels(list('JFMAMJJASOND')); ax.set_ylabel('Median within-month slope (% d$^{-1}$)'); lab(ax, 'b')
save(fig, 'Figure_08')

# ---------- Figure 9: grid-side equivalence (single panel, no label) ----------
fig, ax = new(2.8)
rows = [('M1 load', 'M1_load_DOWadj_4wk'), ('M1 grid purchase', 'M1_purchased_DOWadj_4wk'), ('T1 load', 'T1_load_DOWadj_4wk'), ('T1 grid purchase', 'T1_purchased_DOWadj_4wk'),
        ('C3 load', 'C3_load_DOWadj_4wk'), ('C3 grid purchase', 'C3_purchased_DOWadj_4wk')]
for i, (lb, k) in enumerate(rows):
    v = Rg[k]; ok = v['p_TOST_3pct'] < 0.05
    ax.plot(v['ci95'], [i, i], color=VIO if ok else '#8a8984', lw=2); ax.plot(v['diff_pct'], i, 'o', ms=5.5, color=VIO if ok else '#8a8984', mfc=VIO if ok else 'white')
    ax.text(5.6, i, f"p$_{{TOST}}$ = {v['p_TOST_3pct']:.3f}", va='center', fontsize=FS)
ax.axvspan(-3, 3, color='#f4f3ef', zorder=0); ax.axvline(0, color='#0b0b0b', lw=0.7)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows]); ax.invert_yaxis(); ax.set_xlim(-6, 8.5)
ax.set_xlabel('DOW-adjusted 28-d post − pre (%), 95 % CI')
save(fig, 'Figure_09')

# ---------- Figure 10: cleaning objective + recovered energy ----------
J = np.load('Jcurves.npy'); Tg = np.load('Tgrid.npy'); E = Rr['E_uncertainty']
fig, axs = new(3.1, ncols=2)
ax = axs[0]
for i, (lb, col, key) in enumerate([('dry/haze season', '#eb6834', 'T_dry_days'), ('wet/transition', '#2a78d6', 'T_wet_days')]):
    lo, mid, hi = J[i] / 1e3
    ax.fill_between(Tg, lo, hi, color=col, alpha=0.18, lw=0); ax.plot(Tg, mid, color=col, lw=1.4); ax.plot(Tg[np.argmin(mid)], mid.min(), 'o', color=col, ms=4.5)
    ax.plot([], [], color=col, lw=1.4, label=f'{lb}: T* = {E[key][0]:.0f} d ({E[key][1]:.0f}–{E[key][2]:.0f})')
ax.set_xlabel('Cleaning interval T (days)'); ax.set_ylabel('Daily cost (kTHB d$^{-1}$)'); ax.set_ylim(0, float(max(J[0][1].min(), J[1][1].min())) / 1e3 * 2.6); ax.legend(loc='upper left', bbox_to_anchor=(0.1, 1.0), handlelength=1.2); lab(ax, 'a')
ax = axs[1]; ks = ['C2', 'C5', 'C6', 'T1']; rec = E['recovered_MC']
v = [rec[k]['E_MWh'][0] for k in ks]; lo = [rec[k]['E_MWh'][0] - rec[k]['E_MWh'][1] for k in ks]; hi = [rec[k]['E_MWh'][2] - rec[k]['E_MWh'][0] for k in ks]
ax.bar(ks, v, yerr=[lo, hi], capsize=3, color=[ZC[1], ZC[1], ZC[1], '#c3c2b7'], width=0.6, hatch=[None, None, None, '//'], edgecolor='white')
for i, k in enumerate(ks): ax.text(i, rec[k]['E_MWh'][2] + 2, f"{rec[k]['value_kTHB'][0]:.0f} kTHB\n({rec[k]['value_kTHB'][1]:.0f}–{rec[k]['value_kTHB'][2]:.0f})", ha='center', fontsize=FS)
ax.set_ylabel('Recovered energy in 90 d (MWh)'); ax.set_ylim(0, 105); lab(ax, 'b')
save(fig, 'Figure_10')

# ---------- Graphical abstract ----------
fig, ax = new(2.3); ax.axis('off'); ax.set_xlim(0, 12); ax.set_ylim(0, 5)
def gbox(x, y, w, h, title, body, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.05,rounding_size=0.15', fc=fc, ec='#8a8984', lw=0.8))
    ax.text(x + w / 2, y + h - 0.3, title, ha='center', va='top', fontsize=FS, fontweight='bold')
    ax.text(x + w / 2, y + h - 0.85, body, ha='center', va='top', fontsize=FS, linespacing=1.3)
gbox(0.05, 0.2, 3.75, 4.6, 'Problem', '3-zone, 2.5 MWp rooftop PV\n1,283 days, 9 O&M log entries\n\nPR trusted, but:\n3 identical pyranometers,\nnever recalibrated\nPR truncated at 90 %\ncleaning procedure unrecorded', '#eaf1fb')
gbox(4.12, 0.2, 3.75, 4.6, 'CZMR framework', 'cross-zone sensor audit\n↓\nre-referenced PR and\nsensor-free yield ratio\n↓\npermutation event study,\nbootstrap, FDR, TOST\n↓\nMonte-Carlo cost model', '#e8f6f0')
gbox(8.2, 0.2, 3.75, 4.6, 'Findings', 'Zone 1 reference diverged\n−8.9 % yr⁻¹ (relative)\nPLR +4.5 → −4.1 % yr⁻¹\n2 of 6 cleanings verified\nhaze-season soiling\n0.31 % d⁻¹\nT* ≈ 110 d (lit. cost),\n56 d at ¼ cost', '#fbeee8')
for x0 in [3.8, 7.87]: ax.annotate('', (x0 + 0.32, 2.5), (x0, 2.5), arrowprops=dict(arrowstyle='-|>', color=INK2, lw=1.2))
save(fig, 'Graphical_abstract')
print('ok')
