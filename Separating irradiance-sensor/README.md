# Separating irradiance-sensor drift from array soiling in redundant multi-zone PV systems

Code and data for the manuscript *"Separating irradiance-sensor drift from array soiling in redundant multi-zone photovoltaic
systems: identifiability, a censored state-space estimator and redundancy-aware recalibration"*
(T. Saengsuwan, C. Naunchan; submitted to *Progress in Photovoltaics*).

The metrological-soiling state-space model (MSSM) estimates the sensitivity of each zone's pyranometer, its drift rate, the
condition of each array and the effect of logged interventions from daily final yield and reported PR. PR values clipped at
0.90 by the monitoring platform enter as censored observations through a Tobit Kalman update.

## Repository layout
```
data/      daily_zone_data.csv, om_log.csv, DATA_DICTIONARY.md   (only the variables used)
code/      ss_data.py      – builds the daily panel, clear-sky insolation, censoring bounds, event dates
           ss_model.py     – MSSM: state space, Tobit Kalman filter, RTS smoother, MLE, auxiliary residuals
           01_fit_models.py                       – maximum-likelihood fit of the main model and five variants
           02_semisynthetic_validation.py         – 100 replicates with known drift and cleaning gains (Fig. 3, Table 3)
           03_detectability_and_recalibration.py  – detection time (Eq. 7), online alarm, recalibration policies (Fig. 7, Table 7)
           04_posterior_results.py                – sensor/array posteriors, intervention effects, auxiliary residuals (Tables 4-6)
           05_figures.py                          – Figures 1-7 and the graphical abstract (PNG and 600-dpi TIFF)
           run_all.py                             – runs steps 01-05 in order
results/   reference outputs of every step, including the fitted models (mssm_*.pkl)
figs/      created by step 05
```

## How to run
```bash
pip install -r requirements.txt
cd code
python run_all.py              # full analysis; step 01 takes about 1-2 h on a laptop
python run_all.py --skip-fit   # reuse the fitted models in ../results (steps 02-05, about 30 min)
```
Single steps can be run on their own in the order above. Step 01 accepts `ONLY=main` or a comma-separated list of variants
(`drop_truncated, naive_truncated, sensor_jump, mean_anchor, no_anchor`) as an environment variable.
Random seeds are fixed inside the scripts; the maximum-likelihood fit is deterministic.

## Correspondence with the manuscript
| Manuscript | Produced by | File |
|---|---|---|
| Table 3, Figure 3 | 02 | results/validation_summary.json, validation_semisynthetic.csv |
| Table 4 | 01 | results/mssm_fit_main.json |
| Tables 5–6, Figures 4–6, Table S1–S2 | 04 | results/results_main.json, aux_residuals.csv |
| Table 7, Figure 7 | 03 | results/theory.json |

## Notes
* The pyranometers have no calibration certificate beyond their 2021 factory label; absolute sensitivities are relative to the
  initial Zone 3 sensor and to the clear-sky envelope anchor, whereas contrasts between sensors are not (see Proposition 1).
* `results/*.pkl` are Python pickles written by step 01; load them only from this repository.

## Citation and contact
Please cite the article once published. Correspondence: Thanapon Saengsuwan, Chiang Rai Rajabhat University
(thanapon.sae@crru.ac.th, ORCID 0000-0003-1283-5454).
