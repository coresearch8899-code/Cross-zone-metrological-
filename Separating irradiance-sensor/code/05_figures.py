# -*- coding: utf-8 -*-
"""Step 5: manuscript figures (16 cm wide, 8 pt, 600 dpi)."""
import json, os, pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from ss_data import load_panel, ROOT
from ss_model import SIG, DLT, S, envelope_blocks

RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figs")
plt.rcParams.update({"font.size": 8, "font.family": "DejaVu Sans", "axes.linewidth": 0.6, "lines.linewidth": 1.0,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False})
CM = 1 / 2.54
ZC = ["#0072B2", "#E69F00", "#009E73"]          # zone colours
P = load_panel(); d = P["date"]; n = P["n"]
R = json.load(open(os.path.join(RES, "results_main.json")))
X = np.load(os.path.join(RES, "smoothed_main.npy")); V = np.load(os.path.join(RES, "smoothed_main_var.npy"))
EVC = {k: v for k, v in P["events"].items() if v is not None and k != "C7"}


def evlines(ax, label=False):
    for k, e in EVC.items():
        ax.axvline(d[e], color="0.6" if k.startswith("C") else "#CC79A7", lw=0.5, ls="-" if k.startswith("C") else "--", zorder=0)
        if label and k != "M1":
            ax.text(d[e], 1.0, "C3/M1" if k == "C3" else k, transform=ax.get_xaxis_transform(), fontsize=6, ha="center", va="bottom", color="0.35")


def datefmt(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))


def panel(ax, s):
    ax.set_title(s, fontsize=8, loc="center", pad=3)


def save(fig, name):
    fig.savefig(os.path.join(FIG, name), dpi=600, bbox_inches="tight")
    _tiff(fig, name)
    plt.close(fig)


# ---------------- Fig 1: framework ----------------
def fig1():
    fig, ax = plt.subplots(figsize=(16 * CM, 8.2 * CM)); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 52)
    def box(x, y, w, h, title, body, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fc, ec="0.3", lw=0.6))
        ax.text(x + w / 2, y + h - 2.2, title, ha="center", va="top", fontsize=7.5, weight="bold")
        ax.text(x + w / 2, y + h - 6.2, body, ha="center", va="top", fontsize=6.5, linespacing=1.35)
    box(1, 30, 30, 21, "Platform data (per zone)", "final yield $Y_{f,i}$\nreported PR (truncated at 0.90)\n→ own-sensor insolation $H_i$\nor censoring bound\nclear-sky $H_{cs}$, $T_{amb}$, O&M log", "#eef3fa")
    box(35, 30, 30, 21, "Theory (Section 2)", "P1 gauge: what is identifiable\nP2 anchoring: envelope vs mean\nP3 isolation needs N ≥ 3\nP4 minimum detectable drift\nP5 recalibration interval", "#f6efe6")
    box(69, 30, 30, 21, "Estimator (Section 3)", "MSSM state space: $\\sigma_i$, $\\delta_i$, $s_i$,\nsky $a+L$, AR(1) deviations\nTobit Kalman update (censoring)\nRTS smoother + MLE\nauxiliary residuals", "#eaf5ee")
    box(8, 2, 26, 21, "Validation", "semi-synthetic injection:\nknown drift and jumps,\nreal sky, 90 % truncation\nbias, RMSE, coverage", "#f2f2f2")
    box(37, 2, 26, 21, "Diagnosis", "sensor sensitivity paths\narray condition, soiling rates\ncleaning effects (posterior)\nunlogged events", "#f2f2f2")
    box(66, 2, 26, 21, "Decisions", "online drift alarm\ndetection time vs design\nredundancy-aware\nrecalibration policy", "#f2f2f2")
    for x0, x1 in ((31.5, 34.5), (65.5, 68.5)):
        ax.annotate("", (x1, 40), (x0, 40), arrowprops=dict(arrowstyle="-|>", lw=0.7, color="0.3"))
    ax.plot([84, 84], [29.6, 26.8], color="0.3", lw=0.7); ax.plot([21, 79], [26.8, 26.8], color="0.3", lw=0.7)
    for x in (21, 50, 79):
        ax.annotate("", (x, 23.6), (x, 26.8), arrowprops=dict(arrowstyle="-|>", lw=0.7, color="0.3"))
    save(fig, "Figure_01.png")


# ---------------- Fig 2: data ----------------
def fig2():
    fig, ax = plt.subplots(2, 1, figsize=(16 * CM, 9 * CM), sharex=True)
    for i in range(3):
        y = pd.Series(np.exp(P["y"][:, i]), index=d).rolling(7, min_periods=3, center=True).median()
        ax[0].plot(d, y, color=ZC[i], label=f"Zone {i+1}")
    ax[0].set_ylabel("Final yield (h d$^{-1}$)\n7-day median"); ax[0].legend(ncol=3, loc="lower left"); evlines(ax[0], True); panel(ax[0], "(a)")
    for i in range(3):
        pr = np.exp(P["y"][:, i] - P["h"][:, i]) * 100
        ax[1].plot(d, pr, ".", ms=1.2, color=ZC[i], alpha=0.6)
        tr = np.isfinite(P["hc"][:, i])
        ax[1].plot(d[tr], np.full(tr.sum(), 90 + 1.2 * (i + 1)), "|", ms=3, color=ZC[i])
    ax[1].axhline(90, color="k", lw=0.5, ls=":"); ax[1].set_ylabel("Reported PR (%)"); ax[1].set_ylim(40, 95)
    ax[1].text(d[5], 93.6, "truncated days (|)", fontsize=6.5); evlines(ax[1]); datefmt(ax[1]); panel(ax[1], "(b)")
    save(fig, "Figure_02.png")


# ---------------- Fig 3: validation ----------------
def fig3():
    df = pd.read_csv(os.path.join(RES, "validation_semisynthetic.csv")); vs = json.load(open(os.path.join(RES, "validation_summary.json")))
    fig, ax = plt.subplots(1, 3, figsize=(16 * CM, 5.6 * CM), gridspec_kw=dict(width_ratios=[1.2, 1, 1]))
    lab = {"tobit": "MSSM-Tobit", "drop": "MSSM-drop", "naive": "MSSM-naive", "ratio": "Ratio OLS"}
    col = {"tobit": "#0072B2", "drop": "#E69F00", "naive": "#9c9c9c", "ratio": "#D55E00"}
    for k in ("ratio", "naive", "drop", "tobit"):
        yv = df["ratio"] if k == "ratio" else df[f"drift_lvl_{k}"]
        ax[0].plot(df.drift_true * 100, yv * 100, "o", ms=2, color=col[k], label=lab[k], alpha=0.8)
    lim = [-16, 0]; ax[0].plot(lim, lim, "k-", lw=0.5); ax[0].set_xlim(lim)
    ax[0].set_xlabel("True drift (% yr$^{-1}$)"); ax[0].set_ylabel("Estimated drift (% yr$^{-1}$)"); ax[0].legend(fontsize=6); panel(ax[0], "(a)")
    keys = ["tobit", "drop", "naive", "ratio_ols"]
    bias = [vs[k]["drift_bias_pct_yr"] for k in keys]; rmse = [vs[k]["drift_rmse_pct_yr"] for k in keys]
    xx = np.arange(4)
    ax[1].bar(xx - 0.18, bias, 0.36, color="#56B4E9", label="bias"); ax[1].bar(xx + 0.18, rmse, 0.36, color="#0072B2", label="RMSE")
    ax[1].set_xticks(xx); ax[1].set_xticklabels(["Tobit", "drop", "naive", "ratio"], fontsize=7); ax[1].axhline(0, color="k", lw=0.5)
    ax[1].set_ylabel("Drift error (% yr$^{-1}$)"); ax[1].legend(fontsize=6)
    for j, k in enumerate(keys[:3]):
        ax[1].text(j, max(bias[j], rmse[j]) + 0.15, f"{vs[k]['drift_cover95']*100:.0f}%", ha="center", fontsize=6)
    panel(ax[1], "(b)")
    jr = [vs["tobit"]["jump_rmse_logpct"], vs["drop"]["jump_rmse_logpct"], vs["window_median"]["jump_rmse_logpct"]]
    ax[2].bar(range(3), jr, color=["#0072B2", "#E69F00", "#D55E00"]); ax[2].set_xticks(range(3)); ax[2].set_xticklabels(["MSSM\nTobit", "MSSM\ndrop", "window\nmedian"], fontsize=7)
    ax[2].set_ylabel("Cleaning-effect RMSE (log-%)"); panel(ax[2], "(c)")
    fig.tight_layout(w_pad=1.2); save(fig, "Figure_03.png")


# ---------------- Fig 4: sensors ----------------
def fig4():
    fig, ax = plt.subplots(3, 1, figsize=(16 * CM, 14 * CM), sharex=True)
    E = envelope_blocks(P, P["h"], P["hc"], P["y"])
    for i in range(3):
        mu, sd = X[:, SIG[i]] * 100, np.sqrt(V[:, SIG[i]]) * 100
        ax[0].fill_between(d, mu - 1.96 * sd, mu + 1.96 * sd, color=ZC[i], alpha=0.18, lw=0)
        ax[0].plot(d, mu, color=ZC[i], label=f"Sensor {i+1}")
    ax[0].set_ylabel("Log sensitivity $\\sigma_i$ (%)\nrel. to sensor 3 at start"); ax[0].legend(ncol=3, loc="lower left"); evlines(ax[0], True); panel(ax[0], "(a)")
    dl = np.load(os.path.join(RES, "smoothed_dlt13.npy")); on = np.load(os.path.join(RES, "online_drift.npy"))
    ax[1].fill_between(d, dl[:, 0] - 1.96 * dl[:, 1], dl[:, 0] + 1.96 * dl[:, 1], color=ZC[0], alpha=0.2, lw=0)
    ax[1].plot(d, dl[:, 0], color=ZC[0], label="smoothed $\\delta_1-\\delta_3$")
    ax[1].plot(d, on[:, 0] * 100, color="k", lw=0.7, ls="--", label="online (filtered) $\\delta_1$")
    th = json.load(open(os.path.join(RES, "theory.json")))
    od = th["online_detection"]["first_day"]
    if od:
        ax[1].axvline(np.datetime64(od), color="#D55E00", lw=0.8); ax[1].text(np.datetime64(od), 0.05, " online alarm", color="#D55E00", fontsize=6.5, transform=ax[1].get_xaxis_transform())
    ax[1].axhline(0, color="k", lw=0.4); ax[1].set_ylabel("Drift rate (% yr$^{-1}$)"); ax[1].legend(loc="lower left", fontsize=6.5); evlines(ax[1]); panel(ax[1], "(b)")
    for name, ls in (("main", "-"), ("mean_anchor", "--"), ("no_anchor", ":")):
        fn = os.path.join(RES, f"mssm_{name}.pkl")
        if not os.path.exists(fn):
            continue
        f = pickle.load(open(fn, "rb"))
        lab = {"main": "envelope anchor", "mean_anchor": "mean-clearness anchor", "no_anchor": "no anchor"}[name]
        mu = f["XS"][:, SIG[2]] * 100; sd = np.sqrt(f["PS_diag"][:, SIG[2]]) * 100
        ax[2].plot(d, mu, color=ZC[2], ls=ls, label=lab)
        if name != "no_anchor":
            ax[2].fill_between(d, mu - 1.96 * sd, mu + 1.96 * sd, color=ZC[2], alpha=0.12 if name == "main" else 0.06, lw=0)
    ax[2].set_ylabel("Sensor 3 $\\sigma_3$ (%)"); ax[2].set_ylim(-40, 25); ax[2].legend(loc="lower left", fontsize=6.5); evlines(ax[2]); datefmt(ax[2]); panel(ax[2], "(c)")
    save(fig, "Figure_04.png")


# ---------------- Fig 5: arrays ----------------
def fig5():
    fig = plt.figure(figsize=(16 * CM, 13 * CM)); gs = fig.add_gridspec(2, 3, height_ratios=[1, 1])
    a0 = fig.add_subplot(gs[0, :]); a1 = fig.add_subplot(gs[1, :2]); a2 = fig.add_subplot(gs[1, 2])
    for i in range(3):
        mu, sd = X[:, S[i]] * 100, np.sqrt(V[:, S[i]]) * 100
        a0.fill_between(d, mu - 1.96 * sd, mu + 1.96 * sd, color=ZC[i], alpha=0.15, lw=0); a0.plot(d, mu, color=ZC[i], label=f"Zone {i+1}")
    a0.set_ylabel("Array condition $s_i$ (log-%)"); a0.legend(ncol=3, loc="lower left"); evlines(a0, True); datefmt(a0); panel(a0, "(a)")
    rr = pd.Series(P["y"][:, 0] - P["y"][:, 2], index=d)
    base = np.nanmedian(rr.values[30:120]) - (X[60, S[0]] - X[60, S[2]])
    a1.plot(d, (rr - base) * 100, ".", ms=1.3, color="0.6", label="observed ln($Y_{f,1}/Y_{f,3}$)")
    a1.plot(d, (X[:, S[0]] - X[:, S[2]]) * 100, color=ZC[0], label="smoothed $s_1-s_3$")
    a1.set_ylim(-35, 30); a1.set_ylabel("Zone 1 rel. Zone 3 (log-%)"); a1.legend(loc="lower left", fontsize=6.5); evlines(a1); datefmt(a1); panel(a1, "(b)")
    ev = R["events"]; keys = [k for k in ("C2", "C3", "C4", "C5", "C6", "T1")]
    old = {"C2": 9.7, "C3": 1.1, "C4": -0.2, "C5": 11.0, "C6": 16.4, "T1": 11.1}       # R13 window estimates, zone 1 yield ratio
    for j, k in enumerate(keys):
        m_, lo, hi = ev[k]["zone1_rel3_logpct"]
        a2.errorbar(m_, j, xerr=[[m_ - lo], [hi - m_]], fmt="o", ms=3, color=ZC[0], capsize=1.5, lw=0.8)
        a2.plot(old[k], j - 0.25, "x", ms=3.5, color="#D55E00")
    a2.set_yticks(range(len(keys))); a2.set_yticklabels(keys); a2.invert_yaxis(); a2.axvline(0, color="k", lw=0.4)
    a2.set_xlabel("Zone 1 effect rel. Zone 3 (log-%)"); a2.plot([], [], "o", color=ZC[0], ms=3, label="MSSM (95 % CI)"); a2.plot([], [], "x", color="#D55E00", label="window median")
    a2.legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2); panel(a2, "(c)")
    fig.tight_layout(h_pad=0.8); save(fig, "Figure_05.png")


# ---------------- Fig 6: auxiliary residuals ----------------
def fig6():
    A = pd.read_csv(os.path.join(RES, "aux_residuals.csv"), index_col=0, parse_dates=True)
    thr = R["aux_residuals"]["threshold_abs_t"]
    fig, a = plt.subplots(figsize=(16 * CM, 5.5 * CM))
    for i in range(3):
        a.plot(A.index, A[f"array{i+1}"], color=ZC[i], lw=0.6, label=f"Zone {i+1}")
    a.axhline(thr, color="k", ls=":", lw=0.6); a.axhline(-thr, color="k", ls=":", lw=0.6); a.set_ylabel("Array level shift $\\tau_t$")
    evlines(a, True); a.legend(ncol=3, fontsize=6.5, loc="lower left"); datefmt(a)
    save(fig, "Figure_06.png")


# ---------------- Fig 7: detectability ----------------
def fig7():
    from scipy.stats import norm
    th = json.load(open(os.path.join(RES, "theory.json")))
    mdd = th["mdd"]
    rates = np.linspace(0.5, 15, 200) / 100
    z = norm.ppf(0.975) + norm.ppf(0.8)
    fig, ax = plt.subplots(1, 3, figsize=(16 * CM, 6 * CM), gridspec_kw=dict(width_ratios=[1.1, 1, 1]))
    lab = {"contrast_h1_h3": "sensor contrast $h_1-h_3$", "anchor_h1_clearsky": "clear-sky ratio $h_1-\\ln H_{cs}$",
           "yield_ratio_y1_y3": "yield ratio $y_1-y_3$"}
    cols = {"contrast_h1_h3": "#0072B2", "anchor_h1_clearsky": "#D55E00", "yield_ratio_y1_y3": "#009E73"}
    for k in lab:
        s, phi = mdd[k]["sd"], mdd[k]["phi"]
        nd = (z ** 2 * 12 * s ** 2 * (1 + phi) / ((1 - phi) * (rates / 365.25) ** 2)) ** (1 / 3)
        ax[0].plot(rates * 100, nd / 30.44, color=cols[k], label=lab[k])
    for k, v in th["mdd_mc_check"].items():
        ax[0].plot(5, v["n_days"] / 30.44, "o", ms=3, color=cols[k])
        ax[0].text(5.3, v["n_days"] / 30.44, f"MC power {v['empirical_power']:.2f}", fontsize=6, va="center")
    ax[0].set_yscale("log"); ax[0].set_xlabel("Drift rate (% yr$^{-1}$)"); ax[0].set_ylabel("Months to detect")
    ax[0].legend(fontsize=6); panel(ax[0], "(a)")
    Ts = [1, 2, 3, 5]
    series = [("standalone", "stand-alone", "0.4", "-"), ("standalone_clearsky", "stand-alone + clear-sky", "0.4", "--"),
              ("sync_N3_noanchor", "N = 3 synchronous", "#0072B2", "-"), ("stagger_N3_noanchor", "N = 3 staggered", "#0072B2", "--"),
              ("stagger_N3_anchor", "N = 3 staggered + envelope", "#009E73", "-"), ("stagger_N5_anchor", "N = 5 staggered + envelope", "#009E73", ":")]
    for j, (pk, ttl) in enumerate((("policy_sd_mean_max", "(b) fitted dynamics"), ("policy_nominal_sd_mean_max", "(c) healthy sensor"))):
        pol = th[pk]; a = ax[j + 1]
        for key, lb, c, ls in series:
            if key in pol["T1y"]:
                a.plot(Ts, [1.96 * pol[f"T{t}y"][key][1] * 100 for t in Ts], marker="o", ms=2.5, color=c, ls=ls, label=lb)
        a.set_yscale("log"); a.axhline(3, color="k", lw=0.5, ls=":"); a.text(4.0, 3.2, "τ = 3 %", fontsize=6)
        a.set_xlabel("Interval per sensor (yr)"); panel(a, ttl)
    ax[1].set_ylabel("Max. 95 % uncertainty of $\\sigma_1$ (%)")
    ax[1].legend(fontsize=5.3, loc="upper left")
    fig.tight_layout(w_pad=1.5); save(fig, "Figure_07.png")


# ---------------- graphical abstract ----------------
def graphical_abstract():
    """plain-language, left-to-right, colour-blind-safe (Okabe-Ito + line styles + direct labels)"""
    from matplotlib.patches import Ellipse
    th = json.load(open(os.path.join(RES, "theory.json")))
    s1 = abs(R["sensors"]["zone1"]["rel3_drift_2025on_pct_yr"][0])
    md = th["mdd"]; fac = md["anchor_h1_clearsky"]["days_to_detect_89permil_yr"] / md["contrast_h1_h3"]["days_to_detect_89permil_yr"]
    fig = plt.figure(figsize=(16 * CM, 7 * CM))
    # step 1
    ax0 = fig.add_axes([0.0, 0.0, 0.29, 1.0]); ax0.axis("off"); ax0.set_xlim(0, 10); ax0.set_ylim(0, 10)
    ax0.text(5, 9.4, "1  Three rooftop zones\nunder one sky", ha="center", va="top", fontsize=7.5, weight="bold")
    ax0.add_patch(Ellipse((5, 6.7), 1.3 * 7 / 4.64, 1.3, color="#F0E442", ec="0.4", lw=0.4))
    for i, x in enumerate((1.8, 5.0, 8.2)):
        ax0.add_patch(FancyBboxPatch((x - 1.2, 2.4), 2.4, 1.2, boxstyle="round,pad=0.1", fc=ZC[i], lw=0))
        ax0.text(x, 3.0, f"Zone {i+1}", ha="center", va="center", color="w", fontsize=6.5, weight="bold")
        ax0.annotate("", (x, 3.8), (5, 6.0), arrowprops=dict(arrowstyle="-|>", lw=0.5, color="0.45"))
    ax0.text(5, 1.6, "each zone has its own\nenergy meter and sun sensor", ha="center", va="top", fontsize=6.3)
    # step 2
    ax1 = fig.add_axes([0.40, 0.17, 0.30, 0.56])
    ls = ["-", "--", ":"]
    for i in range(3):
        mu, sd = X[:, SIG[i]] * 100, np.sqrt(V[:, SIG[i]]) * 100
        ax1.fill_between(d, mu - 1.96 * sd, mu + 1.96 * sd, color=ZC[i], alpha=0.15, lw=0)
        ax1.plot(d, mu, color=ZC[i], lw=1.2, ls=ls[i])
        k = (120, 330, 200)[i]; off = (4, -6, -5)[i]
        ax1.text(d[k], mu[k] + off, f"sensor {i+1}", color=ZC[i], fontsize=6, va="center", weight="bold")
    od = np.datetime64(th["online_detection"]["first_day"])
    ax1.axvline(od, color="0.2", lw=0.7, ls="-."); ax1.text(od, 13, "alarm ", color="0.2", fontsize=6, ha="right")
    ax1.set_ylabel("Sun-sensor reading\nvs. start (%)", fontsize=6.5); ax1.tick_params(labelsize=6)
    ax1.xaxis.set_major_locator(mdates.YearLocator()); ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.text(0.50, 0.93, "2  The model separates sensor\nerror from dirty panels", ha="center", va="top", fontsize=7.5, weight="bold")
    # arrows between steps
    for x0 in (0.29, 0.725):
        fig.patches.append(FancyArrowPatch((x0, 0.86), (x0 + 0.035, 0.86), transform=fig.transFigure, arrowstyle="-|>",
                                           mutation_scale=9, lw=0.8, color="0.3"))
    # step 3
    ax2 = fig.add_axes([0.765, 0.0, 0.235, 1.0]); ax2.axis("off")
    ax2.text(0.0, 0.93, "3  What operators gain", fontsize=7.5, weight="bold", va="top")
    txt = (f"• A faulty sun sensor was found:\n  it lost about {s1:.0f} % a year\n  from 2025\n\n"
           f"• Comparing sensors found it\n  about {fac:.0f} times sooner than\n  a clear-sky check\n\n"
           "• Days hidden by the 90 %\n  reporting cap are used,\n  not thrown away\n\n"
           "• Recalibrating sensors one\n  at a time keeps all of\n  them accurate for longer")
    ax2.text(0.0, 0.80, txt, fontsize=6.2, va="top", linespacing=1.3)
    fig.savefig(os.path.join(FIG, "Graphical_Abstract.png"), dpi=600)
    _tiff(fig, "Graphical_Abstract.png")
    plt.close(fig)


def _tiff(fig, name):
    fig.savefig(os.path.join(FIG, name.replace(".png", ".tif")), dpi=600, bbox_inches="tight",
                pil_kwargs={"compression": "tiff_lzw"})


if __name__ == "__main__":
    for f in (fig1, fig2, fig3, fig4, fig5, fig6, fig7, graphical_abstract):
        try:
            f(); print("ok", f.__name__)
        except Exception as e:
            print("FAILED", f.__name__, repr(e))
