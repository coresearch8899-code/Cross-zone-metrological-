# -*- coding: utf-8 -*-
"""Run the full analysis in order. Usage: python run_all.py [--skip-fit]
--skip-fit reuses the fitted models in ../results (mssm_*.pkl) instead of re-estimating them (step 1 takes 1-2 h)."""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
steps = ["01_fit_models.py", "02_semisynthetic_validation.py", "03_detectability_and_recalibration.py",
         "04_posterior_results.py", "05_figures.py"]
if "--skip-fit" in sys.argv:
    steps = steps[1:]
for s in steps:
    print(f"\n=== {s} ===", flush=True)
    subprocess.run([sys.executable, os.path.join(HERE, s)], cwd=HERE, check=True)
print("\nAll steps finished. Outputs: ../results (JSON/CSV/NPY), ../figs (PNG/TIFF).")
