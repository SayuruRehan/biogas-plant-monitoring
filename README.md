# COMP6009 Assignment Part B - Biogas monitoring and decisions

This package contains a complete worked implementation and report for the
supplied assignment. All baseline results use the supplied models and all
three original, unmodified 30-step CSV datasets. The inference algorithms are
implemented explicitly using the Python standard library. Matplotlib is used
only to visualise results; ReportLab is used only to typeset the PDF.

## Quick start

Use Python 3.10 or newer (tested with Python 3.12.14). Open a terminal in this
folder. The following commands work on macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python run_analysis.py
python build_report.py
```

On Windows, create the environment with `py -m venv .venv` and activate it
with `.venv\Scripts\Activate.ps1` in PowerShell; use the same remaining
`python` commands. If activating is restricted, invoke
`.venv\Scripts\python.exe` directly instead of `python`.

The supplied outputs are already generated. Installing dependencies and
rerunning is needed only for reproduction or modification. Numerical tests
require no third-party package. No GPU, API key, HMM library, network access
at execution time, or training stage is required. Dependency installation
requires access to Python's package index.

## Files

| File or folder | Purpose |
| --- | --- |
| `report/COMP6009_Part_B_Report.pdf` | Standalone report with calculations, figures, discussion and IEEE references |
| `report/COMP6009_Part_B_Report.md` | Editable report source |
| `biogas.py` | Baseline models, generic Bayesian updating, explicit HMM filtering and reusable decision function |
| `run_analysis.py` | Dataset validation, results generation and three separate sensitivity experiments |
| `plot_results.py` | State probability, action timeline and expected-utility plots |
| `build_report.py` | Rebuilds the PDF from Markdown and generated figures |
| `tests/test_inference.py` | Ten numerical and validation checks, including independent hidden-path enumeration |
| `data/` | The three original supplied CSV datasets |
| `results/` | Full numerical outputs, audit records and sensitivity results |
| `figures/` | PNG and vector PDF charts |
| `WALKTHROUGH.md` | Plain-language explanation for understanding and discussing the work |
| `REQUIREMENTS_CHECKLIST.md` | Assignment requirements mapped to implementation and report |

## Reproduction details

`run_analysis.py` creates the following:

- `task1_bayesian_results.csv`: all three Sensor 1 posteriors plus Warning +
  Abnormal pH.
- `scenario_A_results.csv`, `scenario_B_results.csv`, `scenario_C_results.csv`:
  every prediction, unnormalised update, posterior, most probable state, expected
  utility for each action, recommended action and winning utility margin.
- `analysis.json`: baseline configuration and all results at full precision.
- `sensitivity_summary.csv` and `sensitivity_details.csv`: action differences
  and all per-step results for three separate perturbations.
- Three probability plots, one action timeline and one expected-utility chart,
  each in PNG and PDF format.

Optional paths:

```bash
python run_analysis.py --data-dir data --output-dir reproduced
```

The report uses the baseline results. Its narrative is a reviewed report, not
a dynamically generated interpretation of arbitrary replacement datasets.
Changing model values or observations requires updating the narrative and
tables as well as rerunning analysis and report generation.

All computations retain floating-point precision; only the report rounds
values. State order is Stable, Stressed, Critical. Transition rows are current
states and columns are next states. Exact ties select the first dictionary
entry: Stable before Stressed before Critical for the most probable state,
and Continue before Reduce Feed before Intervene for actions. No baseline
decision is tied.

## Important modelling convention

The brief names the supplied prior P(X0), but explicitly requires the first
observation to update that prior directly. This implementation follows that
instruction: at t=1, prediction equals the prior; at t>=2, prediction is the
previous posterior multiplied by the transition model. Each scenario resets
to the same prior. Sensor 2 is used only for Task 1.

## Sensitivity experiments

These are separate illustrative changes, with the same observations and prior:

1. Sensor 1 emission rows become `0.75 * baseline + 0.25 / 3` for each label.
2. Transition probabilities become `0.5 * T + 0.5 * identity`.
3. The utility of Continue in Critical becomes -40 instead of -20.

The altered likelihood and transition rows remain valid probability
distributions. Changed-action counts compare each variant to baseline on the
same 30 steps. They do not measure real-world accuracy or simulate the effect
of implementing actions; there are no true-state labels or action-dependent
transitions in the supplied data.

## Report and final review

The report stays within the recommended 1,800-2,200 main-body words, including
its tables and headings and excluding references, captions and appendices.
The exact count is printed by `build_report.py`. Add your student details in
the format required by your lecturer, review the interpretation, and ensure
you can explain the calculation and code before submitting.

`results/verification.txt` records the checks run while preparing this package.
