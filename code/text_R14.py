# -*- coding: utf-8 -*-
"""R14 manuscript text (new theory + estimator). Numbers are filled from results/*.json by build(R).
Style: passive voice in methods and results, varied sentence length, plain wording."""


def ci(v, k=1, unit=""):
    return f"{v[0]:+.{k}f}{unit} (95 % CI {v[1]:+.{k}f} to {v[2]:+.{k}f})"


def ci_s(v, k=1):
    return f"{v[0]:+.{k}f} ({v[1]:+.{k}f} to {v[2]:+.{k}f})"


TITLE = ("Separating irradiance-sensor drift from array soiling in redundant multi-zone photovoltaic systems: "
         "identifiability, a censored state-space estimator and redundancy-aware recalibration")
KEYWORDS = "Pyranometer drift; Performance ratio; State-space model; Kalman filter; Censored data; Soiling; Recalibration"


def build(R, TH, VS, VAR):
    s1, s2, s3 = R["sensors"]["zone1"], R["sensors"]["zone2"], R["sensors"]["zone3"]
    a1, a2, a3 = R["arrays"]["zone1"], R["arrays"]["zone2"], R["arrays"]["zone3"]
    ev = R["events"]; sg = R["segments"]; th = R["theta"]
    md = TH["mdd"]; on = TH["online_detection"]
    pol, poln = TH["policy_sd_mean_max"], TH["policy_nominal_sd_mean_max"]
    det_c, det_a = md["contrast_h1_h3"]["days_to_detect_89permil_yr"], md["anchor_h1_clearsky"]["days_to_detect_89permil_yr"]
    det_y = md["yield_ratio_y1_y3"]["days_to_detect_89permil_yr"]
    vt, vd, vn, vr = VS["tobit"], VS["drop"], VS["naive"], VS["ratio_ols"]
    aux = R["aux_residuals"]
    lr = VAR.get("LR_sensor_jump", {"LR": float("nan"), "p_chi2_1": float("nan")})
    vm = VAR.get("mean_anchor", {}); vna = VAR.get("no_anchor", {}); vdr = VAR.get("drop_truncated", {})
    vmain = VAR["main"]

    ABSTRACT = (
        "Field pyranometers drift, and a drifting reference cannot be told apart from a soiling array by any indicator that "
        "divides energy by insolation. This study asks what a PV system with several metered zones, each with its own sensor, can reveal "
        "about its sensors and arrays without extra instruments. A measurement model shows that daily data "
        "identify every sensor contrast, array contrast and PR, but one common-mode direction needs an anchor; a clear-sky envelope "
        "anchor is robust to year-to-year cloudiness. Closed forms are "
        "derived for the minimum detectable drift and for the recalibration interval of a redundant network. A metrological-soiling "
        "state-space model is proposed in which sensors, arrays and interventions are estimated together and PR values clipped by the "
        "platform are treated as censored observations (Tobit Kalman update). When applied to 3.4 years of a 2.51 MWp three-zone rooftop system in Thailand, a divergence of the Zone 1 "
        f"reference was dated from January 2025, at {s1['rel3_drift_2025on_pct_yr'][0]:.1f} % per year relative to Zone 3 "
        f"({s1['rel3_drift_2025on_pct_yr'][1]:.1f} to {s1['rel3_drift_2025on_pct_yr'][2]:.1f}); an online version would have raised an alarm in "
        f"{_month(on['first_day'])}. The drift was detected about {det_a / det_c:.0f} times faster through a sensor contrast than through a "
        f"clear-sky ratio. Credible gains were found for two of six cleanings (+{ev['C5']['zone1_rel3_logpct'][0]:.1f} and "
        f"+{ev['C6']['zone1_rel3_logpct'][0]:.1f} log-%), and level shifts absent from the log were detected. For a healthy sensor, rotating "
        f"recalibrations through three networked sensors kept the 95 % sensitivity uncertainty below "
        f"{1.96*poln['T5y']['stagger_N3_anchor'][1]*100:.1f} % at a five-year interval, which is better than recalibrating a stand-alone "
        f"sensor every year ({1.96*poln['T1y']['standalone'][1]*100:.1f} %).")

    B = []
    h1 = lambda t: B.append(("h1", t)); h2 = lambda t: B.append(("h2", t)); p = lambda t: B.append(("p", t))
    eq = lambda tex, k: B.append(("eq", (tex, k))); fig = lambda k: B.append(("fig", k)); tab = lambda k: B.append(("tab", k))

    # ------------------------------------------------------------------ 1
    h1("1. Introduction")
    p("Every field indicator of photovoltaic (PV) performance is normalised by a measured irradiance. The performance ratio (PR) "
      "defined in IEC 61724-1 (IEC, 2021), together with the performance-loss rate (PLR) and the soiling losses derived from it, can "
      "therefore be no more stable than the reference sensor in the denominator. Considerable effort has gone into making the numerator "
      "side robust. Year-on-year (YoY) estimators and their multi-annual extension are largely insensitive to seasonality, outliers and "
      "soiling (Jordan et al., 2018; Quest et al., 2025), soiling can be extracted from routine yield data (Deceglie et al., 2018), and "
      "data quality and workflow choices have been shown to dominate the uncertainty of PLR (Theristis et al., 2024). The denominator "
      "has received far less attention. Field pyranometers get dirty, age and lose calibration. A soiled sensor biases PR in the opposite "
      "direction to a soiled array (Fuke and Kottantharayil, 2025), nominally identical sensors have been found to differ by tens of per "
      "cent before recalibration (Alkhatib et al., 2025), and the regular recalibration that field instruments are supposed to receive "
      "(ISO, 2023) is often skipped in operating plants.")
    p("Systems with several separately metered zones carry a kind of redundancy that is seldom used. Each zone has its own yield record "
      "and, quite often, its own weather station, all under the same sky. In process engineering, redundancy of this type has long been "
      "the basis of fault detection and isolation (Gertler, 1998), and in PV practice neighbouring sensors or arrays are routinely "
      "compared through ratios. Three questions, however, have not been answered formally. What can such a network learn about its "
      "sensors and arrays from its own data, and what has to come from outside? How should drifting sensitivities, soiling, cleaning "
      "recoveries and reporting artefacts be estimated together, rather than through a chain of ratios, change-point tests and event "
      "windows that each carry their own assumptions? And how often does a networked sensor need to be recalibrated, compared with one "
      "that stands alone? A practical complication sharpens all three. Many monitoring platforms store PR only up to a plausibility "
      "ceiling. When a reference loses sensitivity its PR goes up, so the days that hold the evidence of drift are exactly the days that "
      "get clipped, and simply discarding them pulls every estimate towards stability.")
    p("Latent, slowly changing quantities seen through noisy data are the natural territory of state-space models with Kalman filtering "
      "and smoothing (Kalman, 1960; Harvey, 1989; Durbin and Koopman, 2012). Known interventions can be entered as disturbances on given "
      "dates, unlogged shocks can be picked up with auxiliary residuals (Harvey and Koopman, 1992; de Jong and Penzer, 1998), and censored "
      "observations, first handled in regression by Tobin (1958), can be assimilated through a Tobit Kalman update (Allik et al., 2016). "
      "As far as the author is aware, these tools have not yet been brought together to separate sensor drift from array condition in PV "
      "monitoring, and the identifiability of that separation has not been examined.")
    p("Four contributions are made in this paper (Fig. 1). First, an identifiability theory is developed for redundant multi-zone PV "
      "networks. It comprises a gauge result that sorts monitoring indicators into those that can and cannot be identified without "
      "external information, an anchoring result that compares mean-clearness and clear-sky-envelope anchors, an isolation result for "
      "single-sensor drift, and closed forms for the minimum detectable drift and for the recalibration interval of a networked sensor. "
      "Second, a metrological-soiling state-space model (MSSM) is formulated. Sensor sensitivities and their drift rates, array "
      "conditions, seasonal soiling rates and intervention effects are estimated jointly, clipped PR values are assimilated as censored "
      "observations, and unlogged events are screened. Third, the estimator is checked in a semi-synthetic experiment in which known "
      "drifts and cleaning gains are injected into the real sky of the case study. Fourth, the method is applied to 3.4 years of data "
      "from a 2.51 MWp, three-zone hospital rooftop system in northern Thailand, whose three horizontal pyranometers share one model and "
      "one labelled sensitivity but have never been recalibrated, and a redundancy-aware recalibration policy is derived from the fitted "
      "dynamics.")
    p("The emphasis is on method. Propositions 1–5 hold for any number of zones and do not depend on the site. The estimator needs only "
      "daily yield, reported PR and clear-sky irradiance, all of which commercial platforms already store, and the case study is used to "
      "demonstrate and test the approach rather than to characterise one installation. The same structure can be found in utility plants "
      "with several inverter blocks and weather stations, in portfolios of neighbouring rooftops, and in any monitoring variable that is "
      "clipped by a plausibility filter.")
    fig(1)

    # ------------------------------------------------------------------ 2
    h1("2. Measurement model and identifiability")
    h2("2.1. Measurement model")
    p("Consider N zones observed on day t. For zone i, the log final yield is written y_i(t) = ln Y_f,i(t) and the log insolation "
      "recorded by the zone's own sensor h_i(t) = ln H_i(t). Both are expressed relative to the clear-sky insolation H_cs(t) of the "
      "Ineichen–Perez model (Ineichen and Perez, 2002):")
    eq(r"h_i(t)=\ln H_{\mathrm{cs}}(t)+\lambda_i\,\xi(t)+\sigma_i(t)+g^{h}_i(d)+u^{h}_i(t)", 1)
    eq(r"y_i(t)=\ln H_{\mathrm{cs}}(t)+\lambda_y\,\xi(t)+\kappa_i+s_i(t)+g^{y}(d)+\beta_T\tilde{T}(t)+u^{y}_i(t)", 2)
    p("Here ξ(t) is the log clear-sky index of the common sky. The loadings λ_i and λ_y let sensors and arrays respond differently to "
      "cloud (λ_3 = 1 by convention). σ_i(t) is the log effective sensitivity of sensor i relative to its label, s_i(t) is the log "
      "condition of array i (soiling, degradation and availability), κ_i is a constant PR level, g(d) are seasonal terms in the day of "
      "year d, T̃ is the scaled ambient temperature and u are zero-mean deviations. The reported PR equals PR_i = exp(y_i − h_i), but it "
      "is stored by the platform as min(PR_i, 0.90). A stored value of 0.90 therefore tells us only that the sensor reading lies below a "
      "bound,")
    eq(r"h_i(t)\le y_i(t)-\ln(0.90)", 3)
    p("and the clipped days should be regarded as censored observations of h_i, not as missing ones.")
    h2("2.2. A gauge result: what a single day identifies")
    p("The latent quantities of one day are collected in θ = (ξ, σ_1, …, σ_N, s_1, …, s_N) and the observations in o = (h_1, …, h_N, "
      "y_1, …, y_N). Once known terms are removed, o = Mθ + u with")
    eq(r"M=\begin{pmatrix}\boldsymbol{\lambda} & I_N & 0\\ \lambda_y\mathbf{1}_N & 0 & I_N\end{pmatrix},\qquad \ker M=\mathrm{span}\{v\},\quad v=(1,\,-\boldsymbol{\lambda}^{\top},\,-\lambda_y\mathbf{1}_N^{\top})^{\top}", 4)
    p("Proposition 1 (gauge). M has rank 2N, one less than the number of latent quantities, and its null space is spanned by v. A linear "
      "functional c'θ can be identified from the data of one day if and only if c'v = 0, that is, if")
    eq(r"c_{\xi}=\sum_{i=1}^{N}\lambda_i\,c_{\sigma,i}+\lambda_y\sum_{i=1}^{N}c_{s,i}", 5)
    p("Proof. The identity blocks are independent, so rank M = 2N; Mv = 0 follows by substitution; and c'θ is estimable exactly when c "
      "lies in the row space of M, the orthogonal complement of ker M. □")
    p("Physically, the result describes a common-mode ambiguity. A brighter sky, seen by every sensor with proportionally lower "
      "sensitivity and by every array with proportionally lower efficiency, leaves the data unchanged. When Eq. (5) is applied to "
      "familiar indicators (Table 2), sensor contrasts σ_i − σ_j, array contrasts s_i − s_j (the sensor-free yield ratio), the "
      "own-sensor PR and any cross-referenced PR all turn out to be identifiable. The absolute sensitivity of a sensor, the absolute "
      "condition of an array and hence the absolute PLR are not, and neither is the attribution of a change that all zones share to the "
      "sky, the sensors or the arrays. A PLR computed with one zone's sensor as the common reference is, strictly, a contrast that "
      "quietly assumes this sensor to be stable.")
    tab("T2")
    h2("2.3. Anchoring over time")
    p("Over a whole record, the unidentified direction turns into a scalar process c(t)v. It can be pinned down only by an observation "
      "that is not invariant to it, which is what is meant here by an anchor. Two anchors are available without new hardware. A "
      "mean-clearness anchor assumes E[ξ(t)] = m(d), i.e. that the daily clear-sky index follows a stationary climatology. A clear-sky "
      "envelope anchor assumes instead that an upper quantile of h_i − ln H_cs over a block of days, a value reached on the clearest days, "
      "follows a stationary climatology,")
    eq(r"K_{ib}=Q_{0.95}\{h_i(t)-\ln H_{\mathrm{cs}}(t):t\in b\}=c_E+g^{E}(d_b)+g^{h}_i(d_b)+\sigma_i(t_b)+b_b+e_{ib}", 6)
    p("where b denotes a 30-day block with mid-day t_b, b_b a block effect shared by all sensors and e_ib noise. Proposition 2 (anchor "
      "bias). Suppose the true sky contains a slow component L(t), for example a change in cloudiness from one year to the next. Under the "
      "mean anchor the common-mode estimate is biased by −L(t), so a wetter year shows up as a shared loss of sensitivity and array "
      "efficiency. Under the envelope anchor only a change in clear-day transmittance can bias the estimate, because cloudy days do not "
      "reach the upper quantile; L(t) itself then becomes identifiable and can be carried as a state. Proof. ξ = m + L + a is substituted "
      "into Eq. (1), and block expectations (mean anchor) or block upper quantiles (envelope anchor) are taken; the latter do not depend "
      "on L as long as the 95th percentile is reached on cloud-free days. □")
    h2("2.4. Isolating a drifting sensor")
    p("Proposition 3 (isolation). In the (N − 1)-dimensional space of sensor contrasts relative to sensor N, a drift confined to sensor k "
      "leaves the signature f_k = e_k for k < N and f_N = −1. With N = 2 the signatures of a falling sensor 1 and a rising sensor 2 "
      "coincide, so a drift can be detected but not attributed. With N ≥ 3 no two signatures are collinear, and a drift confined to one "
      "sensor can be isolated without any anchor. If an anchor is available, the single-fault restriction can be dropped altogether. This "
      "is the PV counterpart of the familiar requirement of triple redundancy for fault isolation (Gertler, 1998).")
    h2("2.5. Minimum detectable drift")
    p("Let a monitored series, such as a sensor contrast, a clear-sky ratio or a yield ratio, follow c(t) = δt + ε(t), where ε is "
      "first-order autoregressive with marginal standard deviation s and lag-one autocorrelation φ. To first order, the least-squares "
      "slope over n days has variance 12s²(1 + φ)/[(1 − φ)n³]. Proposition 4 (detection time) follows directly: a drift of δ per day is "
      "detected at two-sided level α with power 1 − β after")
    eq(r"n_{d}(\delta)=\left[\frac{12\,(z_{1-\alpha/2}+z_{1-\beta})^{2}\,s^{2}\,(1+\varphi)}{(1-\varphi)\,\delta^{2}}\right]^{1/3}", 7)
    p("days, which agrees with the trend-detection result of Weatherhead et al. (1998). Since the common sky cancels in a sensor contrast "
      "but not in a clear-sky ratio, s is several times smaller for the contrast, and n_d falls with s^(2/3).")
    h2("2.6. Recalibration interval of a networked sensor")
    p("The log sensitivity is assumed to follow a local linear trend, σ(t+1) = σ(t) + δ(t) + w_σ and δ(t+1) = δ(t) + w_δ, with "
      "variances q_σ and q_δ, and each recalibration is assumed to fix σ with standard uncertainty u_c. Proposition 5. (a) For a "
      "stand-alone sensor, the prediction-error variance t days after calibration is")
    eq(r"V_0(t)=u_c^{2}+q_{\sigma}t+q_{\delta}\,\frac{t(t-1)(2t-1)}{6}\approx u_c^{2}+q_{\sigma}t+\frac{q_{\delta}t^{3}}{3}", 8)
    p("and the longest interval that keeps the 95 % uncertainty below a tolerance τ is found from V_0(T_τ) = (τ/1.96)². (b) If each "
      "calibration costs C and the loss caused by a measurement error is taken as proportional to its variance, with weight ω per day, "
      "the average cost C/T + ω[u_c² + q_σT/2 + q_δT³/12] is smallest at")
    eq(r"T^{*}=\left[\frac{-q_{\sigma}+\sqrt{q_{\sigma}^{2}+4q_{\delta}C/\omega}}{q_{\delta}}\right]^{1/2}", 9)
    p("(c) In a network of N sensors observed through daily contrasts, the deviation of each sensor from the network mean is tracked, and "
      "only the mean itself behaves as an unobserved local linear trend, with variances q/N. Under synchronous calibration the variance "
      "therefore grows roughly as V_0(t)/N, so T_τ is lengthened by a factor N when q_σ dominates and by N^(1/3) when q_δ dominates. "
      "Staggering the calibrations, one sensor every T/N, ensures that a recently calibrated member is always present, and an envelope "
      "anchor places a bound on the common mode. Part (c) is evaluated in Section 5.6 with the Riccati recursion of the Kalman filter; "
      "the proofs are given in Supplementary Section S2.")

    # ------------------------------------------------------------------ 3
    h1("3. Metrological-soiling state-space model")
    h2("3.1. State and dynamics")
    p("Eqs. (1), (2) and (6) were cast as a linear state-space model. For each zone, the state holds the log sensitivity σ_i and its drift "
      "rate δ_i, the array condition s_i, and two first-order autoregressive deviations u^h_i and u^y_i with coefficients φ_h and φ_y. The "
      "common sky a(t) and the envelope block effect b_b were included as white-noise states, the slow sky level L(t) as a random walk, and "
      "the static coefficients (two annual harmonics for each seasonal term, κ_i, β_T, c_E and the seasonal soiling rates) as constant "
      "states. The dynamics are")
    eq(r"\sigma_i(t+1)=\sigma_i(t)+\delta_i(t)+w^{\sigma}_i,\qquad \delta_i(t+1)=\delta_i(t)+w^{\delta}_i", 10)
    eq(r"s_i(t+1)=s_i(t)+r^{\mathrm{dry}}_i D(t+1)+r^{\mathrm{wet}}_i\,[1-D(t+1)]+w^{s}_i+J_i(t+1)", 11)
    p("where D(t) marks the dry, biomass-burning season (December–March). J_i is an intervention disturbance with a large variance "
      "(0.15², spread over five days), applied on the five days after each logged cleaning and after the transformer maintenance, so that "
      "the size of each recovery is left to the data. The sensitivity level noise was fixed at 10⁻⁵ per day. σ_i is thus treated as a "
      "smooth trend whose curvature is controlled by q_δ, and abrupt sensor changes at the cleanings were tested separately in a variant "
      "that also allows intervention variance on σ_i. To fix the gauge of Proposition 1, σ_3(0) = 0, s_i(0) = 0, L(0) = 0 and λ_1 = λ_3 = 1 "
      "were imposed. All sensitivities are therefore expressed relative to the Zone 3 sensor at the start of the record, and all array "
      "conditions relative to their own initial state.")
    h2("3.2. Tobit update for truncated PR")
    p("On days with an unclipped PR, h_i enters through an ordinary Kalman update. On a clipped day, the predicted observation "
      "h* ~ N(μ, S) is known only to satisfy h* ≤ c, with c taken from Eq. (3). Its conditional moments are")
    eq(r"\mathrm{E}[h^{*}\mid h^{*}\le c]=\mu-\sqrt{S}\,\Lambda,\qquad \mathrm{Var}[h^{*}\mid h^{*}\le c]=S\,(1-\alpha\Lambda-\Lambda^{2})", 12)
    p("with α = (c − μ)/√S and Λ = ϕ(α)/Φ(α), and the state is then updated by moment matching,")
    eq(r"\hat{x}^{+}=\hat{x}+k\,(\mathrm{E}[h^{*}\mid\cdot]-\mu),\qquad P^{+}=P-k\,S\,k^{\top}+k\,\mathrm{Var}[h^{*}\mid\cdot]\,k^{\top},\qquad k=PZ^{\top}/S", 13)
    p("This is the assumed-density form of the Tobit Kalman filter (Allik et al., 2016), and each clipped day adds ln Φ(α) to the "
      "log-likelihood. In this way the filter is still told that the sensor read low on that day. Discarding the day would bias the drift "
      "towards zero, and setting it to the bound would understate the drift.")
    h2("3.3. Estimation, smoothing and diagnostics")
    p("The 17 hyper-parameters (disturbance and noise variances, autoregressive coefficients and the loadings λ_y and λ_2) were estimated "
      "by maximising the prediction-error log-likelihood, with diffuse priors on the static coefficients and the first 30 days left out. "
      "The states were smoothed with the Rauch–Tung–Striebel recursions (Rauch et al., 1965). Posterior intervals for differences between "
      "two dates were obtained from the smoothed lag covariances Cov(x_t, x_t+k | data) = J_t ⋯ J_t+k−1 P_t+k|n, where J_t is the "
      "smoother gain. Level shifts in s_i that do not appear in the log were screened with standardised smoothed disturbances, the "
      "auxiliary residuals")
    eq(r"\tau_{t}=\frac{\hat{\eta}_{t}}{\sqrt{q-\mathrm{Var}(\eta_t\mid\mathrm{data})}},\qquad \hat{\eta}_t=\hat{x}_{t+1\mid n}-T_{t+1}\hat{x}_{t\mid n}", 14)
    p("using a Bonferroni threshold over all zone-days, |τ_t| > " + f"{aux['threshold_abs_t']:.2f}" + " (Harvey and Koopman, 1992; "
      "de Jong and Penzer, 1998). For real-time use, an online variant was also run, in which the filtered rather than the smoothed drift "
      "rate was monitored and an alarm was raised once its 95 % upper bound had stayed below zero for 14 consecutive days. Five variants "
      "of the model were refitted: clipped days dropped, clipped days set to the bound, sensor interventions at the cleanings, a "
      "mean-clearness anchor, and no anchor. All computations were carried out in Python with NumPy, SciPy and pvlib (Anderson et al., "
      "2023), and every number, table and figure can be regenerated from the supplied code.")

    # ------------------------------------------------------------------ 4
    h1("4. Case study and validation design")
    h2("4.1. System and data")
    p("The method was demonstrated on a 2,513.2 kWp rooftop installation at a public hospital in northern Thailand, where the climate is "
      "tropical savanna with a dry season from November to April. The installation is divided into three separately metered zones of "
      "2,256.3, 207.0 and 49.9 kWp (Table 1). The host institution asked for the site to remain anonymous, so solar geometry was computed "
      "for the grid point 20.0° N, 100.0° E. Daily final yield, reported PR and ambient temperature were used from 26 April 2023, after "
      "commissioning, to 7 September 2026 (1,231 days); 12 duplicated zone-days and all outage days (Y_f < 0.5 h or zero output) were "
      "removed beforehand. Every zone is equipped with a rooftop station of identical design. Its horizontal thermopile pyranometer is of "
      "the same model, carries the same labelled sensitivity of 11.513 µV W⁻¹ m², was factory-calibrated in June 2021 and has not been "
      "recalibrated since; an earlier audit of the system had identified the horizontal channel as the PR reference. The reported PR was "
      "clipped at exactly 0.90 on 81 days in Zone 1 and on 548 days in Zone 2, and these days enter the model through Eq. (3). Seven "
      "cleaning campaigns (C1–C7), one meter calibration (M1) and one transformer maintenance (T1) are listed in the operator's log "
      "(Table 1). Because sensitivities are expressed relative to the uncalibrated Zone 3 sensor at the start of the record, absolute "
      "values depend on the label and on the envelope anchor, whereas contrasts do not (Proposition 1).")
    tab("T1")
    fig(2)
    h2("4.2. Semi-synthetic validation")
    p("To see how well the estimator performs when the truth is known, a semi-synthetic experiment was set up. The smoothed sky (a + L), "
      "the seasonal terms and the fitted noise structure of the case study were kept, and the fitted sensitivity and array paths served "
      "as a baseline truth. In each replicate, the post-2025 divergence of sensor 1 was scaled by a random factor between 0.5 and 1.5, the "
      "Zone 1 cleaning recoveries by factors between 0 and 2, and fresh autoregressive and white noise was drawn with the fitted "
      f"parameters. Clipping at 0.90 was then applied, which produced clipped values on {VS['trunc_share_z1_post_mean']*100:.0f} % of "
      f"post-2025 Zone 1 days, close to what was observed. Over {VS['n_rep']} replicates, the MSSM with the Tobit update was compared with "
      "the same model with clipped days dropped or set to the bound, and with an oracle ratio regression of h_1 − h_3 on harmonics and a "
      "broken-stick trend placed at the true break (unclipped days only). For cleaning effects, the post-minus-pre median of the yield "
      "ratio, as used in event studies, served as the benchmark.")

    # ------------------------------------------------------------------ 5
    h1("5. Results")
    h2("5.1. Validation")
    p(f"The injected divergence was recovered with little bias (Fig. 3, Table 3). With the Tobit update, the post-2025 drift of σ_1 − σ_3 "
      f"was off by {vt['drift_bias_pct_yr']:+.2f} % per year on average (RMSE {vt['drift_rmse_pct_yr']:.2f} % per year), and the 95 % interval "
      f"contained the truth in {vt['drift_cover95']*100:.0f} % of replicates. When the clipped days were dropped, the bias grew to "
      f"{vd['drift_bias_pct_yr']:+.2f} % per year (RMSE {vd['drift_rmse_pct_yr']:.2f}); setting them to the bound gave "
      f"{vn['drift_bias_pct_yr']:+.2f} % per year (RMSE {vn['drift_rmse_pct_yr']:.2f}). The difference was largest at the end of the record, "
      f"where clipping was most frequent: the final sensitivity was estimated with an RMSE of {vt['sigend_rmse_pct']:.1f} % by the Tobit "
      f"update, {vd['sigend_rmse_pct']:.1f} % with dropped days and {vn['sigend_rmse_pct']:.1f} % with bounded days, and the corresponding "
      f"interval coverages were {vt['sigend_cover95']*100:.0f}, {vd['sigend_cover95']*100:.0f} and {vn['sigend_cover95']*100:.0f} %. Discarding "
      "clipped days thus pulled both the drift and the final sensitivity towards stability, as expected from Section 3.2.")
    p(f"Two caveats should be noted. The drift interval covered the truth less often ({vt['drift_cover95']*100:.0f} %) than its nominal "
      "level suggests. The hyper-parameters were held at their estimates, and a smooth-trend model cannot follow every bend of the injected "
      "paths, so the intervals are best read as approximate. The oracle ratio regression also reached a lower RMSE "
      f"({vr['drift_rmse_pct_yr']:.2f} % per year), but with a bias of {vr['drift_bias_pct_yr']:+.2f} % per year, and only because it was "
      "handed the true break date, which in practice would itself have to be estimated. Cleaning effects were recovered with an RMSE of "
      f"{vt['jump_rmse_logpct']:.1f} log-% by the MSSM and {VS['window_median']['jump_rmse_logpct']:.1f} log-% by the window median. The gain "
      "comes from the fact that the state-space model uses the whole trajectory between events rather than two fixed windows.")
    fig(3)
    tab("T4")
    h2("5.2. Sensor sensitivities and the timing of the divergence")
    p(f"In the fitted model (Table 4), most short-term variation was taken up by the autoregressive deviations (φ_h = {th['phi_h']:.2f}, "
      f"φ_y = {th['phi_y']:.2f}), and the drift rate was allowed to change slowly (q_δ^½ = {th['q_dlt']*1e5:.1f} × 10⁻⁵ per day). Both loadings came "
      f"out close to one (λ_y = {th['lam_y']:.2f}, λ_2 = {th['lam_h2']:.2f}). At the start of the record, sensor 1 read "
      f"{s1['sig_start'][0]:+.1f} % and sensor 2 {s2['sig_start'][0]:+.1f} % relative to sensor 3 (Fig. 4a, Table 5), even though all three "
      "carry the same label.")
    p(f"Until the end of 2024, sensor 1 kept pace with sensor 3 ({ci(s1['rel3_drift_pre2025_pct_yr'])} % per year). From 2025 onwards it "
      f"drifted away at {ci(s1['rel3_drift_2025on_pct_yr'])} % per year. The smoothed relative drift rate δ_1 − δ_3 became credibly negative "
      f"on {_date(R['sensors']['onset_rel3_first_credible_negative'])} and reached its most negative value, "
      f"{R['sensors']['dlt13_min_pct_yr'][0]:.0f} % per year, in {_month(R['sensors']['dlt13_min_pct_yr'][1])} (Fig. 4b). Under the envelope "
      f"anchor, the effective sensitivity of sensor 1 fell from {s1['Seff_start'][0]:.2f} to {s1['Seff_end'][0]:.2f} µV W⁻¹ m² "
      f"({s1['Seff_end'][1]:.2f}–{s1['Seff_end'][2]:.2f}). In real time, the alarm criterion would have been met on {_date(on['first_day'])}. "
      "The reported PR of Zone 1 gave no such warning: it rose into the 0.90 ceiling as the sensor lost sensitivity.")
    p("Because the sensitivity level noise was fixed small, sudden steps in σ_i were tested with the sensor-intervention variant rather "
      f"than with auxiliary residuals. Allowing such steps at the cleanings did not improve the fit (change in log-likelihood "
      f"{lr['LR']/2:+.1f}), so there was no sign that the campaigns had wiped the sensor domes. "
      + (f"The way clipped days are handled mattered on the real data as well. When they were discarded, the post-2025 relative divergence "
         f"shrank to {vdr['sig13_drift_2025on']:.1f} % per year, against {vmain['sig13_drift_2025on']:.1f} % in the main model, and setting them "
         f"to the bound gave {VAR['naive_truncated']['sig13_drift_2025on']:.1f} %. Both shifts point in the same direction as in the validation."
         if vdr and "naive_truncated" in VAR else ""))
    fig(4)
    tab("T5")
    h2("5.3. The anchor determines absolute but not relative results")
    p(f"Sensor 2 followed a different course. Its relative sensitivity fell by {s2['rel3_drift_pre2025_pct_yr'][0]:.1f} % per year before 2025 "
      f"and recovered by {s2['rel3_drift_2025on_pct_yr'][0]:+.1f} % per year afterwards, a pattern that fits slow deposition followed by "
      "partial cleaning and that a constant-offset view of this sensor would have missed. Sensor 3, under the envelope anchor, lost "
      f"{abs(s3['drift_pre2025_pct_yr'][0]):.1f} % per year ({s3['drift_pre2025_pct_yr'][1]:.1f} to {s3['drift_pre2025_pct_yr'][2]:.1f}) before "
      f"2025 and stayed stable afterwards ({ci_s(s3['drift_2025on_pct_yr'])} % per year), ending the record at {s3['sig_end'][0]:+.1f} % "
      f"({s3['sig_end'][1]:+.1f} to {s3['sig_end'][2]:+.1f}).")
    p("How much of this depends on the anchor? "
      + (f"With the mean-clearness anchor, the end value of σ_3 moved to {vm.get('sig3_end', float('nan')):+.1f} % "
         f"(s.d. {vm.get('sig3_end_sd', float('nan')):.1f}), and without any anchor its standard deviation grew to "
         f"{vna.get('sig3_end_sd', float('nan')):.1f} % (Fig. 4c). " if vm else "")
      + f"The relative divergence σ_1 − σ_3 after 2025, by contrast, hardly changed: {vmain['sig13_drift_2025on']:.1f} % per year in the main model"
      + (f", {vm['sig13_drift_2025on']:.1f} % with the mean anchor and {vna['sig13_drift_2025on']:.1f} % with none" if vm and vna else "")
      + ". This is what Proposition 1 predicts. Contrasts do not depend on the anchor and absolute values do, and even the envelope anchor "
      "narrows the absolute uncertainty only to a few per cent.")
    h2("5.4. Array condition, soiling and cleaning effects")
    p(f"Relative to Zone 3, the Zone 1 array lost {abs(sg['C5-C6_zone1_rel3_pct_d'][0]):.2f} % per day "
      f"({abs(sg['C5-C6_zone1_rel3_pct_d'][2]):.2f}–{abs(sg['C5-C6_zone1_rel3_pct_d'][1]):.2f}) between C5 and C6, an interval that fell "
      f"entirely in the 2026 dry season. Over the monsoon-dominated interval from C4 to C5 the loss was {abs(sg['C4-C5_zone1_rel3_pct_d'][0]):.3f} % "
      f"per day, about {sg['C5-C6_zone1_rel3_pct_d'][0] / sg['C4-C5_zone1_rel3_pct_d'][0]:.0f} times smaller (Fig. 5a, b; Table 6). The seasonal "
      f"rates pooled over all years were poorly determined (Zone 1 relative dry-season rate {ci_s(a1['rel3_r_dry_pct_d'], 3)} % per day), "
      "partly because soiling was weak in the first two dry seasons and partly because the array random walk absorbs some of the signal.")
    p(f"Cleaning C6 (March 2026) raised the Zone 1 array by {ci(ev['C6']['zone1_rel3_logpct'])} log-% relative to Zone 3, and C5 (December "
      f"2025) by {ci(ev['C5']['zone1_rel3_logpct'])} log-%. No effect could be distinguished from zero for C2 "
      f"({ev['C2']['zone1_rel3_logpct'][0]:+.1f} log-%), for the wet-season campaign C3 ({ev['C3']['zone1_rel3_logpct'][0]:+.1f}) or for C4 "
      f"({ev['C4']['zone1_rel3_logpct'][0]:+.1f}) (Fig. 5c). The clearance of the commissioning fault at C1 lifted Zone 2 by "
      f"{ev['C1']['zone2_rel3_logpct'][0]:+.0f} log-%. The meter calibration M1 left the arrays unchanged ({ev['M1']['zone1_rel3_logpct'][0]:+.1f} "
      f"log-%), and the Zone 1 recovery around the transformer maintenance T1 ({ci(ev['T1']['zone1_rel3_logpct'])} log-%) turned out smaller "
      "and less certain than an event-window estimate would suggest.")
    p(f"Over the full record, the net change of the Zone 1 array relative to Zone 3 was {ci(a1['net_PLR_rel3_pct_yr'])} % per year; once its "
      f"cleanings are counted, Zone 1 kept pace with Zone 3. The anchored absolute net PLR came to {ci(a1['net_PLR_pct_yr'])} % per year for "
      f"Zone 1 and {ci(a3['net_PLR_pct_yr'])} % per year for Zone 3. These values include soiling that was never removed and, as noted above, "
      "depend on the anchor.")
    fig(5)
    tab("T6")
    h2("5.5. Unlogged events")
    p("Several level shifts were picked up by the auxiliary residuals of the array states that have no counterpart in the operator's log "
      "(Fig. 6). " + _aux_text(aux) + " Steps in the sensor states were not screened in this way, since sensitivity is modelled as a "
      "smooth trend; steps at the logged campaigns are covered by the sensor-intervention variant (Section 5.2).")
    fig(6)
    h2("5.6. Detectability and recalibration")
    p(f"Before 2025, the daily sensor contrast h_1 − h_3 had a residual standard deviation of {md['contrast_h1_h3']['sd']:.3f} "
      f"(φ = {md['contrast_h1_h3']['phi']:.2f}), compared with {md['anchor_h1_clearsky']['sd']:.3f} (φ = {md['anchor_h1_clearsky']['phi']:.2f}) "
      f"for the clear-sky ratio h_1 − ln H_cs. According to Eq. (7), a drift of 8.9 % per year would be detected after {det_c:.0f} days "
      f"through the contrast, {det_y:.0f} days through the yield ratio and {det_a:.0f} days through the clear-sky ratio (Fig. 7a). These "
      f"predictions were checked by simulation, which gave a power of {TH['mdd_mc_check']['contrast_h1_h3']['empirical_power']:.2f} and "
      f"{TH['mdd_mc_check']['anchor_h1_clearsky']['empirical_power']:.2f} at the predicted sample sizes for 5 % per year. Redundancy, in other "
      f"words, shortens the time needed to detect a sensor drift by a factor of about {det_a / det_c:.0f}.")
    p("Recalibration policies were compared through the Riccati recursion of Eqs. (8)–(10), once with the fitted drift dynamics, which "
      "include the observed fault and are therefore pessimistic, and once with the nominal dynamics of a healthy sensor (1 % drift-induced "
      f"error after one year), with u_c = 1 % in both cases (Fig. 7b, Table 7). Under the fitted dynamics, a stand-alone sensor exceeded a "
      f"95 % uncertainty of 3 % after only {TH['admissible_interval_days_standalone']['tau_0.03']:.0f} days; no practical calendar could keep "
      "it within that tolerance, and continuous comparison is needed instead. Three networked sensors calibrated together every two years "
      f"reached a maximum 95 % uncertainty of {1.96*pol['T2y']['sync_N3_noanchor'][1]*100:.0f} %. Calibrated in rotation, the same sensors "
      f"reached {1.96*pol['T2y']['stagger_N3_noanchor'][1]*100:.0f} %, and with the envelope anchor added "
      f"{1.96*pol['T2y']['stagger_N3_anchor'][1]*100:.1f} %; with the anchor, even a five-year rotation stayed at "
      f"{1.96*pol['T5y']['stagger_N3_anchor'][1]*100:.1f} %. Under nominal dynamics, a stand-alone sensor had to be recalibrated every "
      f"{TH['admissible_interval_days_nominal']['tau_0.03']/365.25:.1f} years to stay within 3 %, whereas three sensors in rotation with the "
      f"anchor remained below {1.96*poln['T5y']['stagger_N3_anchor'][1]*100:.1f} % at a five-year interval. For the same calibration budget, "
      "rotating the calibrations through a redundant network is clearly the better choice.")
    fig(7)
    tab("T7")

    # ------------------------------------------------------------------ 6
    h1("6. Discussion")
    h2("6.1. What redundancy can and cannot certify")
    p("Proposition 1 separates PV monitoring indicators into two groups. Indicators that compare zones with one another, or a zone with "
      "its own sensor, can be identified from the system's own data. Indicators that claim an absolute sensitivity, an absolute array "
      "condition or an absolute PLR cannot; they inherit whatever anchor has been assumed, and that assumption is rarely stated. The case "
      f"study illustrates the point. The Zone 1 PR trend was {R['pr_trends']['own'][0]:+.1f} % per year with its own sensor and "
      f"{R['pr_trends']['ref3'][0]:+.1f} % per year with the Zone 3 sensor, both of them identifiable contrasts (Table 2), while the anchored "
      "absolute values remained uncertain by several per cent even after 3.4 years. Redundancy is therefore best seen as a way to detect "
      "and date sensor problems quickly (Section 5.6) and to verify relative effects such as cleaning gains. Absolute claims, for instance "
      "in performance guarantees, still need a traceable reference, although now only for one member of the network at a time.")
    h2("6.2. Truncation is informative censoring")
    p("A platform that caps PR at a plausibility ceiling removes precisely the observations that would reveal a sensor losing "
      "sensitivity. When these values were treated as censored rather than missing, an indicator that had hidden the fault began to "
      "contribute to its estimation (Section 5.1). The same Tobit update can be used for any monitoring variable that is clipped, rounded "
      "at a limit or flagged as out of range, and it costs almost nothing to implement.")
    h2("6.3. A protocol for multi-zone systems")
    p("A simple protocol can be drawn from these results. The state-space model can be run online on the daily data that the platform "
      "already stores, and a sensor alarm raised whenever a filtered drift rate is credibly different from zero. Cleanings and other logged "
      "interventions are better verified through the posterior change of the array contrast than through the own-sensor PR, and the "
      "auxiliary residuals can be screened for events that were never logged. Recalibrations should be rotated through the sensors rather "
      "than carried out all at once. Finally, if the end date, the zones covered and any sensor wiping were recorded for each campaign, the "
      "estimates would become sharper at almost no cost.")
    h2("6.4. Limitations")
    p("Several limitations should be kept in mind. The case study covers one site, three zones and daily aggregates only. The calibration "
      "chain is incomplete, so absolute sensitivities are relative to the initial Zone 3 sensor and to the envelope anchor, and a change of "
      "logger coefficient cannot be told apart from a physical loss of sensitivity without an inspection on site; constant coefficient "
      "errors, however, cancel in the contrasts. The envelope pseudo-observations reuse the daily sensor data through a different statistic "
      "and were treated as independent, which slightly overstates their information. The envelope anchor also assumes that clear-day "
      "transmittance has no trend. In a region with variable biomass-burning haze, the dry-season 95th percentile can be depressed in smoky "
      "years, which is why dry-season blocks were given their own noise variance. The model is linear-Gaussian in logs, the Tobit update is "
      "an assumed-density approximation, and three dry seasons were not enough to pin down the seasonal soiling rates. Rainfall, "
      "particulate-matter and inverter data were not used, so the unlogged shifts are reported as detections rather than explained. "
      "Lastly, Proposition 5(c) and the policy comparison assume that sensors drift independently. A shared cause, such as identical dome "
      "degradation, would leave a common mode that only an external reference can remove.")

    # ------------------------------------------------------------------ 7
    h1("7. Conclusions")
    p("An identifiability theory and a censored state-space estimator were developed for redundant multi-zone PV systems and tested on a "
      "2.51 MWp hospital rooftop system whose three pyranometers had never been recalibrated. Within the stated assumptions, the following "
      "conclusions can be drawn.")
    B.append(("bul", "Every sensor contrast, array contrast and PR can be identified from daily multi-zone data, but absolute sensitivity, "
              "absolute array condition and absolute PLR cannot. These require an anchor, and a clear-sky envelope anchor holds up against "
              "year-to-year cloudiness where a mean-clearness anchor does not. At least three sensors are needed to attribute a drift to one "
              "of them."))
    B.append(("bul", f"The Zone 1 reference drifted away from January 2025 at {s1['rel3_drift_2025on_pct_yr'][0]:.1f} % per year relative to "
              f"Zone 3, gradually rather than in a step. An online filter would have flagged the drift in {_month(on['first_day'])}, whereas "
              "the clipped reported PR concealed it."))
    B.append(("bul", "In semi-synthetic tests, treating clipped PR values as censored gave an end-of-record sensitivity RMSE of "
              f"{vt['sigend_rmse_pct']:.1f} %, compared with {vd['sigend_rmse_pct']:.1f} % when they were dropped, and cleaning effects were "
              f"estimated with an RMSE of {vt['jump_rmse_logpct']:.1f} log-%, compared with {VS['window_median']['jump_rmse_logpct']:.1f} log-% "
              "for event-window medians."))
    B.append(("bul", f"Credible Zone 1 gains were found for two of six cleanings (+{ev['C5']['zone1_rel3_logpct'][0]:.1f} and "
              f"+{ev['C6']['zone1_rel3_logpct'][0]:.1f} log-%), both in the dry season, and level shifts missing from the maintenance log "
              "were revealed by the auxiliary residuals."))
    B.append(("bul", f"Drift was detected about {det_a / det_c:.0f} times faster through a sensor contrast than through a clear-sky ratio. "
              "For a healthy sensor, rotating recalibrations through three networked sensors with an envelope anchor kept the 95 % "
              f"sensitivity uncertainty at {1.96*poln['T5y']['stagger_N3_anchor'][1]*100:.1f} % with a five-year interval, against "
              f"{1.96*poln['T1y']['standalone'][1]*100:.1f} % for a stand-alone sensor recalibrated every year."))
    p("Since only data that monitoring platforms already store are required, the theory and the estimator can be applied to any system "
      "with at least two, and preferably three, separately metered zones under a common sky. Validation on further systems equipped with "
      "traceable reference radiometers is the natural next step.")

    HIGHLIGHTS = ["A gauge theorem states which PV indicators a multi-zone system can identify.",
                  "Clear-sky envelope, not mean clearness, anchors absolute sensor sensitivity.",
                  "A Tobit Kalman filter treats truncated PR values as censored observations.",
                  f"Reference drift of {s1['rel3_drift_2025on_pct_yr'][0]:.0f} %/yr was dated and detected {det_a/det_c:.0f}× faster by redundancy.",
                  "Staggered recalibration of networked sensors beats synchronous calibration."]
    return ABSTRACT, B, HIGHLIGHTS


MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def _date(s):
    if not s:
        return "–"
    y, m, d = s.split("-")
    return f"{int(d)} {MONTHS[int(m)-1]} {y}"


def _month(s):
    if not s:
        return "–"
    y, m, d = s.split("-")
    return f"{MONTHS[int(m)-1]} {y}"


def _aux_text(aux):
    """summarise clusters of auxiliary-residual exceedances (dates within 10 days merged)."""
    out = []
    for z in ("array1", "array2", "array3"):
        hits = sorted(aux.get(z, []), key=lambda r: r["date"])
        clusters = []
        for r in hits:
            if clusters and (_dnum(r["date"]) - _dnum(clusters[-1][-1]["date"])) <= 10:
                clusters[-1].append(r)
            else:
                clusters.append([r])
        for c in clusters:
            sgn = [r["t_stat"] for r in c]
            kind = "a rise" if min(sgn) > 0 else ("a fall" if max(sgn) < 0 else "a fall followed by a recovery")
            span = _date(c[0]["date"]) if len(c) == 1 else f"{_date(c[0]['date'])} – {_date(c[-1]['date'])}"
            out.append(f"Zone {z[-1]}, {span}: {kind} (max |τ| = {max(abs(x) for x in sgn):.1f})")
    if not out:
        return "No unlogged level shift exceeded the threshold."
    return ("The threshold was exceeded in the following cases: " + "; ".join(out) + ". The Zone 2 shift in early May 2023 began "
            "several days before the logged clearance of the commissioning fault (C1, 6 May 2023), which suggests that the log records the "
            "end of the work rather than its start. The paired fall and recovery of Zone 1 in August 2025 is consistent with a temporary "
            "partial outage, the one-day fall and rebound in July 2026 behaves like an outlier, and the isolated rises could reflect "
            "unlogged cleaning or rain.")


def _dnum(s):
    import datetime as _dt
    return _dt.date.fromisoformat(s).toordinal()
