import os, pickle, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ss_data import load_panel, ROOT
from ss_model import SIG, DLT, S, ARH, ARY

name = sys.argv[1] if len(sys.argv) > 1 else "main"
P = load_panel()
f = pickle.load(open(os.path.join(ROOT, "results", f"mssm_{name}.pkl"), "rb"))
X, Pd = f["XS"], f["PS_diag"]
d = P["date"]
fig, ax = plt.subplots(4, 1, figsize=(10, 12), sharex=True)
for i in range(3):
    ax[0].plot(d, X[:, SIG[i]] * 100, label=f"sig{i+1}")
    ax[0].fill_between(d, (X[:, SIG[i]] - 1.96 * np.sqrt(Pd[:, SIG[i]])) * 100, (X[:, SIG[i]] + 1.96 * np.sqrt(Pd[:, SIG[i]])) * 100, alpha=.2)
    ax[1].plot(d, X[:, DLT[i]] * 36525, label=f"dlt{i+1} %/yr")
    ax[2].plot(d, X[:, S[i]] * 100, label=f"s{i+1}")
ax[3].plot(d, (X[:, S[0]] - X[:, S[2]]) * 100, label="s1-s3")
ax[3].plot(d, (X[:, S[1]] - X[:, S[2]]) * 100, label="s2-s3")
y = P["y"]
ax[3].plot(d, (y[:, 0] - y[:, 2] - np.nanmedian(y[:400, 0] - y[:400, 2])) * 100, ".", ms=1, alpha=.4)
for k, e in P["events"].items():
    if e is not None:
        for a in ax: a.axvline(d[e], color="grey", lw=.5)
for a in ax: a.legend(fontsize=7); a.grid(alpha=.3)
fig.savefig(os.path.join(ROOT, "figs", f"diag_{name}.png"), dpi=90)
