"""Revision figures: Fig 4 (truncation evidence + monthly PR), Fig 9 (cost curves with 95 % bands, MC recovered energy),
Fig 10 (robustness: change points, reference-zone matrix, window sensitivity), graphical abstract."""
import pandas as pd, numpy as np, json, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': '#e6e5e0', 'grid.linewidth': 0.6, 'axes.edgecolor': '#8a8984',
                     'xtick.color': '#52514e', 'ytick.color': '#52514e', 'legend.frameon': False})
ZC = {1: '#2a78d6', 2: '#eb6834', 3: '#1baf7a'}; INK2 = '#52514e'; MUTED = '#9b9a95'; VIO = '#4a3aa7'; DPI = 600
d = pd.read_pickle('d_clean.pkl'); PRc = pd.read_pickle('PRc.pkl')
Rr = json.load(open('res_robust.json')); Rc = json.load(open('res_econ.json')); W = pd.read_csv('es_window_sensitivity.csv'); G = pd.read_csv('cp_sensitivity.csv')
EV = [('C1', '2023-05-06'), ('C2', '2024-03-09'), ('C3', '2024-06-23'), ('M1', '2024-06-25'), ('C4', '2025-04-25'), ('C5', '2025-12-26'), ('C6', '2026-03-23'), ('T1', '2026-06-11'), ('C7', '2026-09-05')]
def save(fig, n):
    fig.savefig(f'figs/Fig{n}.png', dpi=DPI, bbox_inches='tight'); fig.savefig(f'figs/Fig{n}_preview.png', dpi=110, bbox_inches='tight'); plt.close(fig)
def evlines(ax):
    for k, v in EV: ax.axvline(pd.Timestamp(v), color=MUTED if k[0] == 'C' else VIO, lw=0.8, ls='-' if k[0] == 'C' else '--', zorder=0)

# ---------- Fig 4: truncation evidence + monthly PR ----------
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0), gridspec_kw={'width_ratios': [1, 2.1]})
ax = axs[0]; bins = np.arange(60, 92.01, 0.5)
for z in [1, 2, 3]:
    p = d[(d.z == z) & ~d.outage].pr_percent.dropna()
    ax.hist(p.clip(upper=91.9), bins=bins, histtype='step', lw=1.2, color=ZC[z], label=f'Zone {z}')
ax.axvline(90, color='#0b0b0b', lw=0.7, ls=':'); ax.set_yscale('log'); ax.set_xlabel('Reported daily PR (%)'); ax.set_ylabel('Days (log scale)')
ax.legend(fontsize=6.3, loc='lower left', bbox_to_anchor=(-0.02, 0.99), ncol=3, handlelength=1.2, columnspacing=0.8); ax.set_title('(a) Upper truncation at 90.00 %', fontsize=8.5, loc='left', pad=16)
z1 = Rr['D_truncation']['z1']; z2 = Rr['D_truncation']['z2']
ax.text(0.03, 0.97, f"exactly 90.00 %:\nZ1 {z1['n_exactly_90.00']} d, Z2 {z2['n_exactly_90.00']} d\n89.0–89.99 %:\nZ1 {z1['n_in_(89.0,89.99)']} d, Z2 {z2['n_in_(89.0,89.99)']} d", transform=ax.transAxes, fontsize=6.5, color=INK2, va='top')
ax = axs[1]
own = d[d.z == 1].set_index('date').pr_percent.where(~d[d.z == 1].set_index('date').outage)
m_own = (own / 100).resample('MS').median(); m_com = PRc[1].resample('MS').median(); m3 = PRc[3].resample('MS').median()
ax.plot(m_own.index, m_own * 100, color='#8a8984', marker='s', ms=3, lw=1, label='Zone 1, reported PR (own sensor, truncated)')
ax.plot(m_com.index, m_com * 100, color=ZC[1], marker='o', ms=3, lw=1.4, label='Zone 1, common-reference PR$_c$')
ax.plot(m3.index, m3 * 100, color=ZC[3], marker='^', ms=3, lw=1, label='Zone 3, PR$_c$ (reference zone)')
ax.axhline(80, color='#0b0b0b', lw=0.7, ls=':')
for t in Rc['false_compliance_list']:
    tt = pd.Timestamp(t + '-01'); ax.axvspan(tt, tt + pd.offsets.MonthEnd(1), color='#eda100', alpha=0.25, lw=0)
evlines(ax); ax.set_ylabel('Monthly median PR (%)'); ax.set_ylim(55, 100); ax.legend(fontsize=6.5, loc='upper left', ncol=2)
ax.set_title('(b) Reported vs re-referenced PR, Zone 1 (shaded: false-compliance months)', fontsize=8.5, loc='left'); ax.tick_params(axis='x', labelsize=7, rotation=30)
fig.tight_layout(); save(fig, 4)

# ---------- Fig 9: cost curves with 95 % band + MC recovered energy ----------
J = np.load('Jcurves.npy'); Tg = np.load('Tgrid.npy'); E = Rr['E_uncertainty']
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.1))
ax = axs[0]
for i, (lab, col, key) in enumerate([('dry/haze season', '#eb6834', 'T_dry_days'), ('wet/transition', '#2a78d6', 'T_wet_days')]):
    lo, mid, hi = J[i] / 1e3
    ax.fill_between(Tg, lo, hi, color=col, alpha=0.18, lw=0); ax.plot(Tg, mid, color=col, lw=1.6, label=f'{lab}: T* = {E[key][0]:.0f} d ({E[key][1]:.0f}–{E[key][2]:.0f})')
    ax.plot(Tg[np.argmin(mid)], mid.min(), 'o', color=col, ms=5)
    ax.annotate(f'{lab}\nT* = {E[key][0]:.0f} d (95 % UI {E[key][1]:.0f}–{E[key][2]:.0f})', (Tg[np.argmin(mid)], mid.min()), xytext=(15, 30) if i == 0 else (-40, 20), textcoords='offset points', fontsize=6.8, color=col)
ax.set_xlabel('Cleaning interval T (days)'); ax.set_ylabel('Daily cost of soiling + cleaning (kTHB d$^{-1}$)'); ax.set_ylim(0, float(max(J[0][1].min(), J[1][1].min())) / 1e3 * 2.6)
ax.set_title('(a) Objective J(T) with 95 % uncertainty band', fontsize=8.5, loc='left')
ax = axs[1]; ks = ['C2', 'C5', 'C6', 'T1']; rec = E['recovered_MC']
v = [rec[k]['E_MWh'][0] for k in ks]; lo = [rec[k]['E_MWh'][0] - rec[k]['E_MWh'][1] for k in ks]; hi = [rec[k]['E_MWh'][2] - rec[k]['E_MWh'][0] for k in ks]
ax.bar(ks, v, yerr=[lo, hi], capsize=3, color=[ZC[1], ZC[1], ZC[1], '#c3c2b7'], width=0.6, hatch=[None, None, None, '//'], edgecolor='white')
for i, k in enumerate(ks): ax.text(i, rec[k]['E_MWh'][2] + 2, f"{rec[k]['value_kTHB'][0]:.0f} kTHB\n({rec[k]['value_kTHB'][1]:.0f}–{rec[k]['value_kTHB'][2]:.0f})", ha='center', fontsize=6.5)
ax.set_ylabel('Recovered energy in 90 d (MWh)'); ax.set_ylim(0, 100); ax.set_title('(b) Recoveries, median and 95 % UI', fontsize=8.5, loc='left')
ax.text(3, 2, 'unexplained', ha='center', fontsize=6.5, color=INK2, rotation=90, va='bottom')
fig.tight_layout(); save(fig, 9)

# ---------- Fig 10: robustness ----------
fig = plt.figure(figsize=(7.2, 6.0)); gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.05])
ax = fig.add_subplot(gs[0, :])
post = pd.read_csv('bayes_cp_posterior.csv', index_col=0, parse_dates=True).iloc[:, 0]
allb = pd.to_datetime(pd.Series([b for bl in G.breaks.apply(eval) for b in bl]))
cnt = allb.dt.to_period('M').value_counts().sort_index(); cnt.index = cnt.index.to_timestamp()
ax.bar(cnt.index, cnt.values / len(G) * 100, width=25, color='#c3c2b7', label=f'share of {len(G)} detector configurations with a break in month (%)')
ax2 = ax.twinx(); ax2.plot(post.index, post.values, color=VIO, lw=1.3, label='Bayesian single-change-point posterior'); ax2.set_yticks([]); ax2.grid(False); ax2.set_ylim(0, post.max() * 1.05); ax2.spines['right'].set_visible(False)
B = Rr['B_changepoint']
for k in B['segmented_2knot']['knots']: ax.axvline(pd.Timestamp(k), color=ZC[1], ls='--', lw=1)
ax.axvspan(pd.Timestamp(B['segmented_1knot_block_bootstrap_95CI'][0]), pd.Timestamp(B['segmented_1knot_block_bootstrap_95CI'][1]), color=ZC[1], alpha=0.08, lw=0)
ax.set_ylabel('Configurations (%)'); ax.set_title('(a) Change points in H$_1$/H$_3$: PELT/BinSeg/BottomUp grid, segmented regression (dashed knots;\n     shaded = 95 % block-bootstrap CI of 1-knot onset) and Bayesian posterior (violet)', fontsize=8, loc='left')
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, fontsize=6.8, loc='upper left')
ax = fig.add_subplot(gs[1, 0])
M = Rr['A_sensor']['plr_reference_matrix']; mat = np.array([[M[f'Y{z}/H{r}'][0] for r in [1, 2, 3]] for z in [1, 2, 3]])
im = ax.imshow(mat, cmap='RdBu', vmin=-8, vmax=8)
for i in range(3):
    for j in range(3): ax.text(j, i, f'{mat[i, j]:+.1f}', ha='center', va='center', fontsize=8, color='#0b0b0b')
ax.set_xticks(range(3)); ax.set_xticklabels(['H$_1$', 'H$_2$', 'H$_3$']); ax.set_yticks(range(3)); ax.set_yticklabels(['Y$_{f,1}$', 'Y$_{f,2}$', 'Y$_{f,3}$']); ax.grid(False)
ax.set_xlabel('Reference sensor'); ax.set_title('(b) YoY PLR (% yr$^{-1}$) by reference', fontsize=8.5, loc='left'); cb = fig.colorbar(im, ax=ax, fraction=0.046); cb.ax.tick_params(labelsize=7)
ax = fig.add_subplot(gs[1, 1])
cfg = [(7, 3), (14, 1), (14, 3), (14, 5), (21, 3), (28, 3)]; evs = ['C2', 'C3', 'M1', 'C4', 'C5', 'C6', 'T1']
D = np.array([[W[(W.event == e) & (W.pre == a) & (W.gap == g)].delta.iloc[0] for (a, g) in cfg] for e in evs])
P = np.array([[W[(W.event == e) & (W.pre == a) & (W.gap == g)].p.iloc[0] for (a, g) in cfg] for e in evs])
im = ax.imshow(D, cmap='Blues', vmin=-5, vmax=20, aspect='auto')
for i in range(len(evs)):
    for j in range(len(cfg)): ax.text(j, i, f'{D[i, j]:.0f}' + ('*' if P[i, j] < 0.05 else ''), ha='center', va='center', fontsize=7, color='white' if D[i, j] > 12 else '#0b0b0b')
ax.set_xticks(range(len(cfg))); ax.set_xticklabels([f'{a}/{g}' for a, g in cfg], fontsize=7); ax.set_yticks(range(len(evs))); ax.set_yticklabels(evs); ax.grid(False)
ax.set_xlabel('window length / gap (days)'); ax.set_title('(c) Yield-ratio effect by window (* p<0.05)', fontsize=8.5, loc='left')
fig.tight_layout(); save(fig, 10)

# ---------- Graphical abstract ----------
fig, ax = plt.subplots(figsize=(8, 3.6)); ax.axis('off'); ax.set_xlim(0, 12); ax.set_ylim(0, 5)
def box(x, y, w, h, title, body, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.05,rounding_size=0.15', fc=fc, ec='#8a8984', lw=0.8))
    ax.text(x + w / 2, y + h - 0.3, title, ha='center', va='top', fontsize=9, fontweight='bold'); ax.text(x + w / 2, y + h - 0.75, body, ha='center', va='top', fontsize=7.4, linespacing=1.35)
box(0.1, 0.6, 3.6, 3.9, 'Problem', '3-zone, 2.5 MWp rooftop PV\n1,283 days, 9 O&M log entries\n\nPR trusted, but:\n• 3 identical pyranometers,\n  never recalibrated\n• PR truncated at 90 %\n• cleaning procedure unrecorded', '#eaf1fb')
box(4.2, 0.6, 3.6, 3.9, 'CZMR framework', 'cross-zone sensor audit\n(ratios, clear-sky, change points)\n↓\nre-referenced PR + sensor-free\nyield ratio\n↓\nseasonal permutation event study,\nblock bootstrap, FDR, TOST\n↓\nMonte-Carlo cost model', '#e8f6f0')
box(8.3, 0.6, 3.6, 3.9, 'Findings', 'Zone 1 reference: progressive\ninter-zone divergence −8.9 % yr⁻¹\n(consistent with sensitivity loss;\ninvariant to logger scaling)\nPLR +4.5 → −4.1 % yr⁻¹ (sign flip)\n2 of 6 cleanings FDR-verified\nhaze-season soiling 0.31 % d⁻¹\nT* ≈ 110 d dry (lit. cost),\n56 d at ¼ cost; no wet-season case', '#fbeee8')
for x in [3.75, 7.85]: ax.annotate('', (x + 0.4, 2.55), (x, 2.55), arrowprops=dict(arrowstyle='-|>', color=INK2, lw=1.4))
fig.savefig('figs/Graphical_abstract.png', dpi=DPI, bbox_inches='tight'); fig.savefig('figs/Graphical_abstract_preview.png', dpi=110, bbox_inches='tight')
print('ok')
