# -*- coding: utf-8 -*-
"""Build Manuscript_R14.docx and Supplementary_R14.docx from results/ and figs/."""
import json, os, re, glob, pickle
import numpy as np
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from ss_data import load_panel, ROOT
from ss_model import envelope_blocks
from omml import add_equation
import text_R14 as TX
from refs_R14 import REFS

RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figs"); OUT = os.path.join(ROOT, "manuscript")
os.makedirs(OUT, exist_ok=True)
R = json.load(open(os.path.join(RES, "results_main.json")))
TH = json.load(open(os.path.join(RES, "theory.json")))
VS = json.load(open(os.path.join(RES, "validation_summary.json")))
VAR = R["variants"]
ABSTRACT, BODY, HIGHLIGHTS = TX.build(R, TH, VS, VAR)
P = load_panel()

FIGCAP = {
 1: "Fig. 1. Framework. Daily platform data enter a measurement model whose identifiability is analysed in Section 2 (Propositions P1–P5); the metrological-soiling state-space model (MSSM, Section 3) estimates sensor and array states with a Tobit update for truncated PR; outputs are validated semi-synthetically and used for diagnosis and for detection and recalibration decisions.",
 2: "Fig. 2. Data. (a) 7-day median final yield of the three zones with logged interventions (grey: cleanings C1–C6; violet dashed: meter calibration M1 and transformer maintenance T1). (b) Reported PR; markers above the dotted 0.90 line show days on which the PR was truncated and enters the model as a censored observation.",
 3: "Fig. 3. Semi-synthetic validation (100 replicates with the real sky, fitted noise and 0.90 truncation). (a) Estimated versus true post-2025 drift of σ1 − σ3 for the MSSM with the Tobit update, with truncated days dropped or set to the bound, and for an oracle ratio regression with the true break. (b) Bias and RMSE of the drift (labels: coverage of the 95 % interval). (c) RMSE of Zone 1 cleaning effects for the MSSM and for the post-minus-pre window median.",
 4: "Fig. 4. Sensor states. (a) Smoothed log sensitivities σi relative to the initial Zone 3 sensor, with 95 % bands. (b) Smoothed relative drift rate δ1 − δ3 with 95 % band and the online (filtered) drift rate of sensor 1; the vertical line marks the online alarm. (c) Zone 3 sensitivity under the envelope anchor, the mean-clearness anchor and no anchor (Proposition 2).",
 5: "Fig. 5. Array states. (a) Smoothed array conditions si with 95 % bands. (b) Observed log yield ratio of Zones 1 and 3 (dots) and the smoothed contrast s1 − s3. (c) Posterior Zone 1 effects of the logged interventions relative to Zone 3 (95 % CI) and the corresponding post-minus-pre window medians of an event study.",
 6: "Fig. 6. Auxiliary residuals (standardised smoothed disturbances, Eq. 14) of the array states of the three zones. Dotted lines: Bonferroni threshold over all zone-days.",
 7: "Fig. 7. (a) Months needed to detect a drift (two-sided α = 0.05, power 0.8; Eq. 7) through a sensor contrast, a yield ratio and a clear-sky ratio, with Monte-Carlo checks at 5 % per year. (b) Maximum 95 % uncertainty of an absolute sensor sensitivity over steady recalibration cycles at the fitted drift dynamics, for a stand-alone sensor and for networks of three or five sensors with synchronous or staggered calibration, with and without the envelope anchor (u_c = 1 %).",
}

doc = Document()
st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.line_spacing = 2.0; st.paragraph_format.space_after = Pt(0)


def setup(d, linenum=True):
    for s in d.sections:
        s.top_margin = s.bottom_margin = Cm(2.5); s.left_margin = s.right_margin = Cm(2.5)
        if linenum:
            ln = OxmlElement("w:lnNumType"); ln.set(qn("w:countBy"), "1"); ln.set(qn("w:restart"), "continuous"); ln.set(qn("w:distance"), "360")
            s._sectPr.append(ln)
        fp = s.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = fp.add_run(); f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin"); it = OxmlElement("w:instrText"); it.text = "PAGE"
        f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "end"); r._r.append(f1); r._r.append(it); r._r.append(f2)


TOK = re.compile(r"(_\{[^}]+\}|_[A-Za-z0-9δσφτκλξβ]+(?:,[A-Za-z0-9]+)?|\^\([^)]*\)|\^[½A-Za-z0-9]+)")


def rich(p, txt, size=None, bold=False, italic=False):
    """add text with x_sub and x^sup markup converted to Word sub/superscripts"""
    txt = re.sub(r"(?<![\w.])-(?=\d)", "\u2212", txt)          # typographic minus for negative numbers
    for part in TOK.split(txt):
        if not part:
            continue
        r = None
        if part.startswith("_"):
            r = p.add_run(part[1:].strip("{}")); r.font.subscript = True
        elif part.startswith("^"):
            r = p.add_run(part[1:].strip("()")); r.font.superscript = True
        else:
            r = p.add_run(part)
        r.bold = bold; r.italic = italic
        if size: r.font.size = Pt(size)
    return p


def para(d, txt, indent=True, size=None, bold=False, italic=False, align=None, spacing=None):
    p = d.add_paragraph(); rich(p, txt, size, bold, italic)
    if align is not None: p.alignment = align
    elif indent: p.paragraph_format.first_line_indent = Cm(0.75); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if spacing: p.paragraph_format.line_spacing = spacing
    return p


def head(d, txt, lvl):
    p = d.add_paragraph(); r = p.add_run(txt); r.bold = True; r.italic = (lvl == 2); r.font.size = Pt(12)
    p.paragraph_format.space_before = Pt(12); p.paragraph_format.keep_with_next = True


def nolinenum(p):
    p._p.get_or_add_pPr().append(OxmlElement("w:suppressLineNumbers"))


def table(d, caption, header, rows, widths=None, note=None, fs=9):
    cp = para(d, caption, indent=False, size=10, spacing=1.15, bold=True); cp.paragraph_format.keep_with_next = True
    cp.paragraph_format.space_before = Pt(10)
    t = d.add_table(rows=1 + len(rows), cols=len(header)); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.style = "Table Grid"
    for j, h in enumerate(header):
        c = t.rows[0].cells[j]; c.text = ""; rich(c.paragraphs[0], h, fs, bold=True)
        sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:fill"), "EDEDED"); c._tc.get_or_add_tcPr().append(sh)
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.rows[i + 1].cells[j]; c.text = ""; rich(c.paragraphs[0], str(v), fs)
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs: p.paragraph_format.line_spacing = 1.0; nolinenum(p)
    if widths:
        for row in t.rows:
            for j, w in enumerate(widths): row.cells[j].width = Cm(w)
    if note:
        para(d, note, indent=False, size=9, spacing=1.15, italic=True)
    d.add_paragraph()


def f1(v, k=1): return f"{v[0]:+.{k}f} ({v[1]:+.{k}f}, {v[2]:+.{k}f})"


# ---------------- tables ----------------
def T1(d):
    E = envelope_blocks(P, P["h"], P["hc"], P["y"])
    kwp = ["2,256.3", "207.0", "49.9"]
    rows = []
    for i in range(3):
        rows.append([f"Zone {i+1}", kwp[i], int(np.isfinite(P["y"][:, i]).sum()), int(np.isfinite(P["h"][:, i]).sum()),
                     int(np.isfinite(P["hc"][:, i]).sum()), sum(1 for e in E if e[1] == i)])
    table(d, "Table 1. System and data used by the model (26 April 2023 – 7 September 2026, 1,231 days).",
          ["Zone", "DC capacity (kWp)", "Valid yield days", "Untruncated own-sensor days", "Truncated (censored) days", "Envelope blocks (30 d)"], rows,
          note="Logged interventions (Gregorian dates converted from the Buddhist calendar): cleanings C1 6 May 2023, C2 9 Mar 2024, C3 23 Jun 2024, C4 25 Apr 2025, "
               "C5 26 Dec 2025, C6 23 Mar 2026, C7 5 Sep 2026 (not testable); meter calibration M1 25 Jun 2024; transformer maintenance T1 11 Jun 2026. "
               "Cleaning procedure (zones covered, sensor wiping) not recorded. Envelope blocks with > 50 % truncated days were not used.")


def T2(d):
    rows = [["Sensor contrast", "σ_i − σ_j", "0 (λ_i = λ_j)", "yes", "yes"],
            ["Array contrast (sensor-free yield ratio)", "s_i − s_j", "0", "yes", "yes"],
            ["Own-sensor PR, ln PR_i", "s_i − σ_i + (λ_y − λ_i)ξ", "0", "yes", "yes"],
            ["Cross-referenced PR (sensor j)", "s_i − σ_j + (λ_y − λ_j)ξ", "0", "yes", "yes"],
            ["Absolute sensitivity", "σ_i", "−λ_i", "no", "yes, conditional on anchor"],
            ["Absolute array condition, absolute PLR", "s_i", "−λ_y", "no", "yes, conditional on anchor"],
            ["Common-mode change (sky vs sensors vs arrays)", "ξ + …", "≠ 0", "no", "yes, conditional on anchor"]]
    table(d, "Table 2. Identifiability of monitoring indicators from multi-zone data (Proposition 1, Eq. 5).",
          ["Indicator", "Linear functional c′θ", "c′v", "Identifiable without anchor", "With envelope anchor"], rows, fs=8.5,
          note="v = (1, −λ′, −λ_y 1′)′ spans the null space of the daily observation matrix (Eq. 4). Identifiable functionals satisfy c′v = 0. With λ_i ≠ λ_j the identifiable sensor contrast is σ_i − (λ_i/λ_j)σ_j.")


def T3(d):
    th = R["theta"]
    desc = [("q_dlt", "s.d. of drift-rate disturbance w^δ (per day)"), ("q_sig", "s.d. of sensitivity level disturbance (fixed)"),
            ("q_s", "s.d. of array-condition disturbance w^s"), ("q_L", "s.d. of slow sky-level random walk L"),
            ("sd_a", "s.d. of daily common sky a"), ("sd_h", "white-noise s.d. of h_i"), ("sd_y1", "white-noise s.d. of y_1"),
            ("sd_y2", "white-noise s.d. of y_2"), ("sd_y3", "white-noise s.d. of y_3"), ("phi_h", "AR(1) coefficient of sensor deviations"),
            ("sd_arh", "innovation s.d. of sensor deviations"), ("phi_y", "AR(1) coefficient of yield deviations"),
            ("sd_ary", "innovation s.d. of yield deviations"), ("sd_b", "s.d. of envelope block effect"), ("sd_env", "envelope noise s.d., dry-season blocks"),
            ("sd_envw", "envelope noise s.d., wet-season blocks"), ("lam_y", "sky loading of yields λ_y"), ("lam_h2", "sky loading of sensor 2 λ_2")]
    rows = [[k.replace("_", " "), dd, f"{th[k]:.3g}"] for k, dd in desc]
    table(d, f"Table 4. Maximum-likelihood estimates of the MSSM hyper-parameters (log-likelihood {R['ll']:.1f}; {R['n_env_obs']} envelope pseudo-observations).",
          ["Parameter", "Meaning", "Estimate"], rows, fs=8.5, note="All quantities in natural-log units of the observations (≈ fractional changes).")


def T4(d):
    rows = []
    for k, lab in (("tobit", "MSSM, Tobit update (proposed)"), ("drop", "MSSM, truncated days dropped"), ("naive", "MSSM, truncated days set to bound")):
        v = VS[k]
        rows.append([lab, f"{v['drift_bias_pct_yr']:+.2f}", f"{v['drift_rmse_pct_yr']:.2f}", f"{v['drift_cover95']*100:.0f}",
                     f"{v['sigend_bias_pct']:+.2f}", f"{v['sigend_rmse_pct']:.2f}", f"{v['sigend_cover95']*100:.0f}", f"{v['jump_rmse_logpct']:.2f}"])
    v = VS["ratio_ols"]; rows.append(["Ratio regression, true break (oracle)", f"{v['drift_bias_pct_yr']:+.2f}", f"{v['drift_rmse_pct_yr']:.2f}", "–", "–", "–", "–", "–"])
    rows.append(["Event-window median", "–", "–", "–", "–", "–", "–", f"{VS['window_median']['jump_rmse_logpct']:.2f}"])
    table(d, f"Table 3. Semi-synthetic validation ({VS['n_rep']} replicates).",
          ["Estimator", "Drift bias (% yr⁻¹)", "Drift RMSE (% yr⁻¹)", "Drift 95 % coverage (%)", "End σ_1 bias (%)", "End σ_1 RMSE (%)", "End σ_1 coverage (%)", "Cleaning-effect RMSE (log-%)"],
          rows, fs=8, note="Drift: post-2025 drift of σ_1 − σ_3. End σ_1: sensitivity of sensor 1 on the last day, where truncation is most frequent. Cleaning effects: Zone 1 relative to Zone 3, C2–C6.")


def T5(d):
    S = R["sensors"]; rows = []
    for i in range(3):
        z = S[f"zone{i+1}"]
        rows.append([f"Sensor {i+1}", f1(z["sig_start"]), f1(z["sig_end"]), f"{z['Seff_start'][0]:.2f} → {z['Seff_end'][0]:.2f}",
                     f1(z["drift_pre2025_pct_yr"]), f1(z["drift_2025on_pct_yr"]),
                     f1(z["rel3_drift_pre2025_pct_yr"]) if i < 2 else "reference", f1(z["rel3_drift_2025on_pct_yr"]) if i < 2 else "reference"])
    table(d, "Table 5. Sensor sensitivities and drift (posterior mean and 95 % CI).",
          ["Sensor", "σ at start (%)", "σ at end (%)", "S_eff (µV W⁻¹ m²)", "Drift before 2025 (% yr⁻¹)", "Drift from 2025 (% yr⁻¹)", "Rel. Zone 3, before 2025", "Rel. Zone 3, from 2025"],
          rows, fs=8, note=f"σ relative to the initial Zone 3 sensor (gauge σ_3(0) = 0); absolute values conditional on the envelope anchor, relative values (last two columns) are not (Table 2). S_eff = 11.513·exp(σ). Onset of the relative drift (δ_1 − δ_3 credibly < 0): {TX._date(S['onset_rel3_first_credible_negative'])}; online alarm: {TX._date(TH['online_detection']['first_day'])}.")


def T6(d):
    ev = R["events"]; rows = []
    for k in ("C1", "C2", "C3", "M1", "C4", "C5", "C6", "T1"):
        e = ev[k]
        rows.append([k, TX._date(e["date"]), f1(e["zone1_rel3_logpct"]), f1(e["zone2_rel3_logpct"]), f1(e["zone1_abs_logpct"]), f1(e["sens1_rel3_logpct"], 2)])
    A = R["arrays"]; sg = R["segments"]
    rows.append(["Net 2023–26", "rel. Zone 3, % yr⁻¹", f1(A["zone1"]["net_PLR_rel3_pct_yr"]), f1(A["zone2"]["net_PLR_rel3_pct_yr"]), f1(A["zone1"]["net_PLR_pct_yr"]), "–"])
    rows.append(["C5–C6 slope", "dry season, % d⁻¹", f1(sg["C5-C6_zone1_rel3_pct_d"], 3), f1(sg["C5-C6_zone2_rel3_pct_d"], 3), f1(sg["C5-C6_zone1_abs_pct_d"], 3), "–"])
    rows.append(["C4–C5 slope", "monsoon, % d⁻¹", f1(sg["C4-C5_zone1_rel3_pct_d"], 3), f1(sg["C4-C5_zone2_rel3_pct_d"], 3), f1(sg["C4-C5_zone1_abs_pct_d"], 3), "–"])
    table(d, "Table 6. Array condition: effects of logged interventions (change from day −1 to day +6, log-%), net change and inter-event slopes (posterior mean and 95 % CI).",
          ["Event", "Date / unit", "Zone 1 rel. Zone 3", "Zone 2 rel. Zone 3", "Zone 1 absolute", "Sensor 1 rel. sensor 3"], rows, fs=8,
          note="Relative effects are identifiable contrasts; absolute effects are conditional on the anchor. Sensor columns test whether an event changed the sensor contrast (e.g. dome wiping).")


def T7(d):
    md = TH["mdd"]; pol = TH["policy_sd_mean_max"]; pn = TH["policy_nominal_sd_mean_max"]
    rows = []
    for k, lab in (("contrast_h1_h3", "Sensor contrast h_1 − h_3"), ("yield_ratio_y1_y3", "Yield ratio y_1 − y_3"), ("anchor_h1_clearsky", "Clear-sky ratio h_1 − ln H_cs")):
        m = md[k]
        rows.append([lab, f"{m['sd']:.3f}", f"{m['phi']:.2f}", f"{m['days_to_detect_20permil_yr']:.0f}", f"{m['days_to_detect_50permil_yr']:.0f}", f"{m['days_to_detect_89permil_yr']:.0f}"])
    table(d, "Table 7a. Detection time (days) of a linear drift by Eq. (7) (α = 0.05, power 0.8), from pre-2025 residuals.",
          ["Monitored series", "s", "φ", "2 % yr⁻¹", "5 % yr⁻¹", "8.9 % yr⁻¹"], rows, fs=8.5)
    rows = []
    keys = [("standalone", "Stand-alone, no anchor"), ("standalone_clearsky", "Stand-alone + envelope"), ("sync_N3_noanchor", "N = 3, synchronous"),
            ("stagger_N3_noanchor", "N = 3, staggered"), ("stagger_N3_anchor", "N = 3, staggered + envelope")]
    for k, lab in keys:
        rows.append([lab] + [f"{1.96*pol[f'T{t}y'][k][1]*100:.1f}" for t in (1, 2, 5)] + [f"{1.96*pn[f'T{t}y'][k][1]*100:.1f}" for t in (1, 2, 5)])
    table(d, "Table 7b. Maximum 95 % uncertainty (%) of an absolute sensor sensitivity over steady recalibration cycles.",
          ["Policy", "Fitted, 1 yr", "Fitted, 2 yr", "Fitted, 5 yr", "Nominal, 1 yr", "Nominal, 2 yr", "Nominal, 5 yr"], rows, fs=8.5,
          note="Interval = recalibration interval per sensor. Fitted: drift dynamics estimated from the case study (includes the Zone 1 fault). Nominal: healthy sensor with 1 % (1 s.d.) drift-induced error after one year. u_c = 1 %.")


TABLES = {"T1": T1, "T2": T2, "T3": T3, "T4": T4, "T5": T5, "T6": T6, "T7": T7}
TABLE_AFTER = {"T4": ["T3"]}                      # Table 3 placed with Section 5.2 text below


# ---------------- manuscript (Progress in Photovoltaics format) ----------------
from cite_num import number
BODY, NREFS, unused, leftover = number(BODY, REFS)
AUTHORS = "Thanapon Saengsuwan¹"
AFFIL = "¹ Program in Energy Engineering and Electrical Technology, Faculty of Industrial Technology, Chiang Rai Rajabhat University, Chiang Rai 57100, Thailand"
CORR = "Correspondence: Thanapon Saengsuwan, Chiang Rai Rajabhat University, 80 Moo 9, Ban Du, Mueang Chiang Rai, Chiang Rai 57100, Thailand. Email: thanapon.sae@crru.ac.th"
FUNDING = "Funding: This research received no specific grant from funding agencies in the public, commercial or not-for-profit sectors."
COI = "Conflict of interest: The author declares no conflicts of interest."
DATA = ("Data availability statement: The curated daily dataset, the operation and maintenance log and the Python scripts that regenerate "
        "all results, tables and figures are provided as supporting information and will be deposited in a public repository "
        "[REPOSITORY NAME AND DOI TO BE ADDED] upon acceptance. The site is not identified at the request of the host institution.")
ETHICS = ("Ethics approval statement: Not applicable. The study uses anonymised technical monitoring data from a building energy system "
          "and involves no human participants, animals or personal data.")
CONSENT = "Patient consent statement: Not applicable."
PERMIT = "Permission to reproduce material from other sources: Not applicable; all figures and tables are original."
TRIAL = "Clinical trial registration: Not applicable."
INTEGRITY = ("Data access and responsibility: Thanapon Saengsuwan had full access to all the data in the study and takes responsibility for "
             "the integrity of the data and the accuracy of the data analysis.")
AI = ("Use of AI tools: An AI assistant was used to help implement code and edit language. The author reviewed all content and takes full "
      "responsibility for the work.")

setup(doc)
para(doc, TX.TITLE, indent=False, size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
para(doc, "Running title: Separating sensor drift from soiling in multi-zone PV", indent=False, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
head(doc, "Abstract", 1)
para(doc, ABSTRACT)
para(doc, "Keywords: " + TX.KEYWORDS.replace(";", ","), indent=False, italic=True)
placed = set()
for kind, val in BODY:
    if kind == "h1": head(doc, val, 1)
    elif kind == "h2": head(doc, val, 2)
    elif kind == "p": para(doc, val.replace("Figs. ", "Figures ").replace("Fig. ", "Figure "))
    elif kind == "bul": para(doc, "• " + val, indent=False)
    elif kind == "eq":
        tex, k = val; p = add_equation(doc, tex, k); nolinenum(p)
    elif kind == "fig":
        fn = os.path.join(FIG, f"Figure_{val:02d}.png")
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(fn, width=Cm(16)); nolinenum(p)
        c = para(doc, FIGCAP[val].replace("Fig. ", "Figure ", 1), indent=False, size=10, spacing=1.15); c.paragraph_format.space_after = Pt(10)
    elif kind == "tab":
        if val == "T5" and "T3" not in placed:
            TABLES["T3"](doc); placed.add("T3")
        TABLES[val](doc); placed.add(val)
head(doc, "Acknowledgements", 1)
para(doc, "The author thanks the engineering unit of the host hospital for access to the monitoring data and the maintenance log.")
head(doc, "Conflict of Interest", 1)
para(doc, COI.split(": ", 1)[1])
head(doc, "Data Availability Statement", 1)
para(doc, DATA.split(": ", 1)[1])
head(doc, "Supporting Information", 1)
para(doc, "Additional supporting information (proofs of Propositions 1–5, model variants, auxiliary-residual list, data and code) can be found online in the Supporting Information section.")
head(doc, "References", 1)
for n, ref in NREFS:
    p = para(doc, f"{n}. {ref}", indent=False, size=11, spacing=1.5)
    p.paragraph_format.left_indent = Cm(0.75); p.paragraph_format.first_line_indent = Cm(-0.75)
OUTP = os.path.join(ROOT, "manuscript", "PIP"); os.makedirs(OUTP, exist_ok=True)
fn = os.path.join(OUTP, "Manuscript_PIP.docx")
doc.save(fn)
print("saved", fn)
print("refs never cited:", unused, "| unconverted author-year:", leftover)

# ---- title page ----
tp = Document(); st2 = tp.styles["Normal"]; st2.font.name = "Times New Roman"; st2.font.size = Pt(12); st2.paragraph_format.line_spacing = 1.5
setup(tp, linenum=False)
para(tp, "Title page", indent=False, bold=True)
para(tp, TX.TITLE, indent=False, size=14, bold=True)
para(tp, "Running title: Separating sensor drift from soiling in multi-zone PV", indent=False)
para(tp, "Article type: Research Article", indent=False)
para(tp, "Authors", indent=False, bold=True)
para(tp, "Thanapon Saengsuwan¹* — ORCID: [0000-0000-0000-0000] — thanapon.sae@crru.ac.th", indent=False, size=11)
para(tp, "[Co-author name]¹ — ORCID: [ ] — [email]   (add each co-author with affiliation and e-mail, as required by the journal)", indent=False, size=11)
para(tp, AFFIL, indent=False, size=11)
para(tp, "* " + CORR, indent=False, size=11)
words_main = sum(len(v.split()) for k, v in BODY if k in ("p", "bul"))
para(tp, f"Word count (main text, excluding abstract, captions, tables and references): about {words_main:,}; abstract {len(ABSTRACT.split())} words; "
         f"{len(FIGCAP)} figures; 7 tables; {len(NREFS)} references.", indent=False, size=11)
para(tp, "Statements relating to ethics and integrity policies", indent=False, bold=True)
for s in (DATA, FUNDING, COI, ETHICS, CONSENT, PERMIT, TRIAL, INTEGRITY, AI):
    para(tp, s, indent=False, size=11)
para(tp, "Author contributions: Thanapon Saengsuwan – conceptualisation, methodology, software, formal analysis, data curation, writing (original draft, review and editing).", indent=False, size=11)
tp.save(os.path.join(OUTP, "Title_Page_PIP.docx"))

# ---- graphical abstract text ----
ga = Document(); setup(ga, linenum=False)
para(ga, "Graphical abstract", indent=False, bold=True)
para(ga, "Image file: Graphical_Abstract.tif (600 dpi, colour-blind-safe Okabe–Ito palette, read left to right)", indent=False)
para(ga, ("Text: When a PV plant has several metered zones under the same sky, their sun sensors can check one another. A new model "
          "uses this to tell a drifting sensor apart from dirty panels, keeps the days hidden by a reporting cap, and showed that one "
          "sensor of a hospital rooftop system had been losing sensitivity since 2025. Recalibrating the sensors one at a time keeps the "
          "whole network accurate for longer."), indent=False)
ga.save(os.path.join(OUTP, "Graphical_Abstract_text.docx"))
import shutil, glob as _g
for f in _g.glob(os.path.join(OUTP, "Figure_*.png")) + _g.glob(os.path.join(OUTP, "Graphical_Abstract.png")):
    os.remove(f)
shutil.copy(os.path.join(FIG, "Graphical_Abstract.tif"), os.path.join(OUTP, "Graphical_Abstract.tif"))
for k in range(1, 8):
    shutil.copy(os.path.join(FIG, f"Figure_{k:02d}.tif"), os.path.join(OUTP, f"Figure_{k}.tif"))

# ---------------- supplementary ----------------
sd = Document()
st = sd.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(11); st.paragraph_format.line_spacing = 1.3
setup(sd, linenum=False)
para(sd, "Supporting Information – " + TX.TITLE, indent=False, bold=True, size=13)
head(sd, "S1. Data preparation", 1)
para(sd, "Rows with duplicated zone-days (12) were removed; days with zero output, missing PR or Y_f < 0.5 h were treated as outages and left out; days before 26 April 2023 (commissioning) were excluded. The own-sensor insolation was computed as H_i = Y_f,i / PR_i on untruncated days. On days with a stored PR of 0.90 or more (flag R4 of the curated dataset), the bound h_i ≤ y_i − ln 0.90 was used (Eq. 3). Clear-sky insolation was the daily sum of 10-min Ineichen–Perez GHI with climatological Linke turbidity at 20.0° N, 100.0° E, 400 m. Daily mean ambient temperature was averaged over the three stations. No values were imputed.")
head(sd, "S2. Proofs", 1)
para(sd, "Proposition 1. Write θ = (ξ, σ′, s′)′ with σ, s ∈ ℝ^N. The observation matrix M (Eq. 4) has 2N rows; its last 2N columns contain I_2N up to permutation, so rank M = 2N and dim ker M = 1. Substitution gives Mv = (λ − λ, λ_y1 − λ_y1)′ = 0. A linear functional c′θ is estimable from o = Mθ + u if and only if c = M′a for some a, i.e. c ∈ row(M) = ker(M)^⊥, i.e. c′v = 0. For the own-sensor PR, c = (λ_y − λ_i, −e_i′, e_i′)′ and c′v = (λ_y − λ_i) + λ_i − λ_y = 0. For σ_i alone, c′v = −λ_i ≠ 0. □")
para(sd, "Proposition 2. Let ξ(t) = m(d) + L(t) + a(t), with a(t) zero-mean and L(t) slowly varying. The mean anchor sets E[ξ(t)] = m(d) and therefore absorbs L(t) into the common mode c(t): since the data are invariant to θ → θ + c v, the estimate of every σ_i shifts by −λ_i L(t) and every s_i by −λ_y L(t). Under the envelope anchor, K_ib depends on the 95th percentile of h_i − ln H_cs within the block, which is attained on days with a(t) close to its clear-sky upper bound; if the block contains at least 5 % cloud-free days, K_ib does not depend on the cloud distribution, and hence not on L, but only on the clear-day transmittance. L(t) then enters h_i and y_i but not K_ib and is identified as a separate state. □")
para(sd, "Proposition 3. With contrasts z = (σ_1 − σ_N, …, σ_N−1 − σ_N)′, a change of size ε in σ_k moves z by εf_k with f_k = e_k (k < N) and f_N = −1_N−1. For N = 2, f_1 = 1 and f_2 = −1 are collinear, so a fall of sensor 1 and a rise of sensor 2 are indistinguishable. For N ≥ 3, any two f_k are linearly independent, so the single faulty sensor is the unique k for which the observed change is collinear with f_k. □")
para(sd, "Proposition 4. For c(t) = α + δt + ε(t), t = 1…n, the OLS slope has variance Σ_t Σ_u w_t w_u γ(t − u) with w_t = (t − t̄)/Σ(t − t̄)². For AR(1) errors with γ(k) = s²φ^|k|, and n ≫ 1/(1 − φ), this is s²(1 + φ)/(1 − φ) / Σ(t − t̄)² ≈ 12 s²(1 + φ)/[(1 − φ)n³]. Requiring |δ|/SD ≥ z_1−α/2 + z_1−β gives Eq. (7). The Monte-Carlo check used 2,000 simulated AR(1) series per design with the empirical s and φ and a prewhitened standard error. □")
para(sd, "Proposition 5. Under the local linear trend with σ(0) known to u_c² and δ(0) = 0, σ(t) − σ̂(t) = e_0 + Σ_{k<t} w_σ,k + Σ_{j=1}^{t−1} (t − j) w_δ,j, whose variance is u_c² + q_σt + q_δ Σ_{j=1}^{t−1} j² = Eq. (8). The time-average of V_0 over a cycle of length T is u_c² + q_σT/2 + q_δT³/12 (continuous approximation); adding C/T and setting the derivative to zero gives (q_δ/4)T⁴ + (q_σ/2)T² − C/ω = 0, a quadratic in T² whose positive root is Eq. (9). For part (c), write σ_k = σ̄ + (σ_k − σ̄). Daily contrasts observe σ_k − σ̄ with bounded steady-state error; σ̄ is the mean of N independent local linear trends and is itself a local linear trend with variances q_σ/N and q_δ/N, and its calibration error after synchronous calibration is u_c²/N. Hence V_N(t) ≈ V_0(t)/N + v_track, and solving V_N(T) = (τ/1.96)² multiplies T_τ by N when q_σ dominates and by N^(1/3) when q_δ dominates. Staggered schedules and the envelope anchor were evaluated exactly with the Riccati recursion P ← TPT′ + Q, P ← P − PZ′(ZPZ′ + R)⁻¹ZP over 12 years, reporting the last two cycles. □")
head(sd, "S3. Model variants", 1)
rows = []
lab = {"main": "Main (Tobit, envelope anchor)", "drop_truncated": "Truncated days dropped", "naive_truncated": "Truncated days set to bound",
       "sensor_jump": "Sensor interventions at cleanings", "mean_anchor": "Mean-clearness anchor", "no_anchor": "No anchor"}
for k in ("main", "drop_truncated", "naive_truncated", "sensor_jump", "mean_anchor", "no_anchor"):
    if k in VAR:
        v = VAR[k]
        rows.append([lab[k], f"{v['ll']:.1f}", f"{v['sig1_end']:+.1f} ± {v['sig1_end_sd']:.1f}", f"{v['sig3_end']:+.1f} ± {v['sig3_end_sd']:.1f}",
                     f"{v['sig13_drift_2025on']:+.1f}", f"{v['s1_net_PLR']:+.1f}", f"{v['s3_net_PLR']:+.1f}"])
table(sd, "Table S1. Re-estimated model variants.", ["Variant", "log L", "σ_1 end (%)", "σ_3 end (%)", "σ_1 − σ_3 drift from 2025 (% yr⁻¹)", "s_1 net (% yr⁻¹)", "s_3 net (% yr⁻¹)"], rows, fs=8,
      note="Log-likelihoods are comparable only between variants with identical observation sets (main, sensor interventions). Values ± 1 s.d.")
head(sd, "S4. Auxiliary-residual exceedances", 1)
rows = []
for z in ("array1", "array2", "array3", "sensor1", "sensor2", "sensor3"):
    for r in R["aux_residuals"].get(z, []):
        rows.append([z.replace("array", "Array ").replace("sensor", "Sensor "), TX._date(r["date"]), f"{r['t_stat']:+.2f}", "yes" if r["near_logged_event"] else "no"])
table(sd, f"Table S2. Days on which a standardised smoothed disturbance exceeded |τ| = {R['aux_residuals']['threshold_abs_t']:.2f}.", ["State", "Date", "τ", "Within logged event window"], rows or [["–", "–", "–", "–"]], fs=9)
head(sd, "S5. Reproducibility", 1)
para(sd, "Code (folder code/): ss_data.py (panel), ss_model.py (MSSM, Tobit filter, smoother, auxiliary residuals), s1_fit.py (MLE of the main model and variants), s2_validate.py (semi-synthetic validation), s3_theory.py (detection time, online detection, recalibration policies), s4_results.py (posterior summaries), s5_figs.py (figures), build_R14.py (documents). Random seeds are fixed in the scripts.")
fn2 = os.path.join(OUTP, "Supporting_Information_PIP.docx")
sd.save(fn2)
print("saved", fn2)
