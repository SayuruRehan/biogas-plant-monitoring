# COMP6009 Assignment Part B: Biogas Plant Monitoring and Decision System

Python implementation and report for Assignment Part B. The code infers the hidden
condition of an anaerobic digester from uncertain sensor readings, tracks that
condition over time, and recommends an operational action:

1. **Task 1, Bayesian inference:** posterior beliefs from Sensor 1 alone and from
   Sensor 1 combined with the pH sensor.
2. **Task 2, HMM filtering:** P(X_t | e_1:t) at every step of the three supplied
   30-step scenarios, using explicit prediction, observation update and normalisation.
3. **Task 3, expected-utility decisions:** the action with the highest expected
   utility at every step, computed from the Task 2 beliefs.

All inference code uses only the Python standard library. No HMM or probabilistic
inference library is used.

## Code submission folder

`submission/code/` is the self-contained code deliverable: zip the `submission`
folder and upload it. It contains `main.py`, the algorithms in `src/`, the unit
tests, the supplied data and all results and figures used in the report. See
`submission/code/README.md` for how to run it. Its numerical outputs are
identical to those in `results/` here.

## Requirements

- Python 3.10 or newer (tested with 3.12)
- The packages in `requirements.txt`. They are needed only for figures, the PDF
  and the Word report. The numerical code and its tests need no third-party package.

## Quick start

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_analysis.py
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run_analysis.py
```

`run_analysis.py` reads the three CSV files in `data/`, then writes every numerical
result to `results/` and every figure to `figures/`. All outputs are already included,
so this step is needed only to reproduce them.

## Reproducing the full submission

| Command | What it does |
| --- | --- |
| `python run_analysis.py` | Runs Tasks 1 to 3 and the sensitivity experiments; writes `results/` and `figures/` |
| `python build_report.py` | Rebuilds `report/COMP6009_Part_B_Report.pdf` from the Markdown source and figures |
| `python build_docx.py` | Rebuilds `report/COMP6009_Part_B_Report.docx` (Times New Roman) from the same source |
| `python -m unittest discover -s tests -v` | Runs the test suite |
| `python verify_submission.py` | Checks inputs, all numerical results and every report table against a fresh calculation |
| `python verify_submission.py --reproduce --run-tests` | Also regenerates all outputs in a temporary folder, confirms they match, and runs the tests |

To write the analysis to a different folder, use
`python run_analysis.py --data-dir data --output-dir reproduced`.

## Repository layout

| Path | Contents |
| --- | --- |
| `biogas.py` | Model tables, `bayesian_update`, `hmm_filter` and `recommend_action` |
| `run_analysis.py` | Loads and validates the datasets, runs all three tasks, writes results and figures |
| `robustness.py` | Worked HMM step, decision margins, switching threshold and parameter sweeps |
| `plot_results.py` | Belief plots, action timeline and expected-utility charts |
| `build_report.py`, `build_docx.py` | Build the PDF and Word versions of the report |
| `generate_report_tables.py`, `report_contract.py` | Generate report tables from the results and define report checks |
| `verify_submission.py` | End-to-end consistency audit |
| `tests/` | Unit and end-to-end tests |
| `data/` | The three supplied scenario datasets, unmodified |
| `results/` | Numerical outputs (CSV and JSON) |
| `figures/` | Plots in PNG and PDF |
| `report/` | Report source (Markdown), PDF and Word versions |

## Output files

| File | Contents |
| --- | --- |
| `results/task1_bayesian_results.csv` | Posteriors for Normal, Warning, Alarm, and Warning + Abnormal pH |
| `results/scenario_{A,B,C}_results.csv` | Per step: prediction, unnormalised weights, posterior, most probable state, expected utility of each action, recommended action and decision margin |
| `results/worked_hmm_step.csv` | The full calculation for Scenario A, t = 2, as shown in the report |
| `results/decision_margins.csv`, `results/closest_decisions.csv` | Winning action, runner-up and utility difference at every step |
| `results/sensitivity_*.csv`, `results/parameter_sweep_*.csv` | Sensitivity experiments and parameter sweeps |
| `results/analysis.json`, `results/robustness.json` | All results at full precision |
| `figures/scenario_{A,B,C}_beliefs.png` | P(Stable), P(Stressed) and P(Critical) over time, with observations and the most probable state |
| `figures/recommended_actions.png`, `figures/expected_utilities.png` | Recommended actions and expected utilities over time |
| `figures/parameter_sweeps.png` | Effect of sensor noise, state persistence and failure penalty on recommendations |

## Modelling conventions

- State order is Stable, Stressed, Critical. Transition rows are the current
  state and columns the next state.
- At t = 1 the supplied prior is updated directly by the first observation, with
  no transition step. From t = 2 the previous posterior is first propagated
  through the transition model. Each scenario starts again from the same prior.
- The pH sensor is used only in Task 1, as the brief specifies.
- Exact ties go to the first entry: Stable before Stressed before Critical, and
  Continue before Reduce Feed before Intervene. No baseline result is tied.
- Probabilities are kept at full floating-point precision. The report rounds
  them to six decimal places for display only.

## Sensitivity experiments

Each experiment changes one part of the model and keeps the same observations
and prior. The results count how many recommendations differ from the baseline.

| Experiment | Settings tested |
| --- | --- |
| Sensor noise: emissions become `(1 - alpha) * baseline + alpha / 3` | alpha = 0, 0.10, 0.25, 0.50 |
| State persistence: transitions become `(1 - lambda) * T + lambda * I` | lambda = 0, 0.25, 0.50, 0.75 |
| Failure penalty: replace U(Continue, Critical) | -20, -25, -30, -35, -40, -50 |

The supplied data have no true-state labels, so these experiments show how much
the recommendations depend on the model, not which version is more accurate.

## Editing the report

The report text is in `report/COMP6009_Part_B_Report.md`. The comparison table in
Section 3 and the tables in Appendix D are generated from `results/`, so do not
edit those marked regions by hand. After changing the analysis or the text, run
`python run_analysis.py`, `python build_report.py`, `python build_docx.py` and
then `python verify_submission.py`.
