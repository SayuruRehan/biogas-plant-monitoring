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
python verify_submission.py --reproduce --run-tests
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
| `robustness.py` | Worked HMM step, utility margins, analytical switch threshold and one-factor parameter sweeps |
| `verify_submission.py` | Rerunnable input, numerical, report-table and PDF-freshness audit |
| `report_contract.py` | Shared report word-count, table and provenance contracts |
| `generate_report_tables.py` | Generates the Section 3 comparison from `analysis.json` and Appendix D from the three result CSVs |
| `plot_results.py` | State probability plots with inferred-state strips, action timeline and expected-utility plots |
| `build_report.py` | Rebuilds the PDF from Markdown and generated figures |
| `tests/test_inference.py` | Ten numerical and validation checks, including independent hidden-path enumeration |
| `tests/test_robustness.py` | Six checks of the worked step, margins, threshold and sweeps |
| `tests/test_verification.py` | Twenty-six end-to-end checks, including corruption detection, report budgets, generated-table provenance and all 90 appendix steps |
| `tests/test_plot_data.py` | Two checks that the inferred-state strip encodes state labels rather than observations |
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
- `worked_hmm_step.csv`: previous belief, each state's contribution to the
  prediction, likelihood, unnormalised weight and posterior at A's second step.
- `decision_margins.csv` and `closest_decisions.csv`: every winning action,
  runner-up, utility difference and the closest choice in each scenario.
- `parameter_sweep_summary.csv` and `parameter_sweep_details.csv`: 42
  scenario-setting summaries and 1,260 complete per-step evaluations.
- `robustness.json`: full-precision derived results and the analytical
  Continue/Reduce Feed switching threshold at B, t=28.
- Three probability plots, one action timeline, one expected-utility chart,
  and one parameter-sweep comparison,
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

The extended one-factor sweeps are separate from those original experiments:

| Family | Tested settings | Meaning |
| --- | --- | --- |
| Sensor uncertainty | 0, 0.10, 0.25, 0.50 | Emissions become `(1-alpha)*baseline + alpha/3` |
| State persistence | 0, 0.25, 0.50, 0.75 | Transitions become `(1-lambda)*T + lambda*identity` |
| Critical failure utility | -20, -25, -30, -35, -40, -50 | Replace only `U(Continue, Critical)` |

Every family includes a baseline anchor. Sweep results never feed into the
baseline beliefs or actions. A decision margin is the best expected utility
minus the second best; it is not a probability of correctness. A pairwise
utility tie is a global decision boundary only after checking that the third
action does not dominate. The B, t=28 calculation performs that check.

## Repeatable verification

```bash
python verify_submission.py
python verify_submission.py --reproduce --run-tests
```

The default command checks original SHA-256 input hashes, exactly 30 steps per
dataset, every baseline prediction/posterior/state/utility/action, all sweep
outputs, every report table, key worked calculations and the word limit.
It also validates the complete title block and PDF Author metadata against
the submission details, and excludes the title block from the word count.
Each numbered section must meet its own brief target, the main body must
stay within the tighter 1,950-2,100 safety margin, and the sensitivity
subsection and Table 6 must appear in Appendix C.
The PDF records fingerprints of its Markdown source, numerical JSON outputs
and embedded figures; the audit rejects a PDF that predates an edit to any
of these inputs. It exits with status 1 and a specific `FAIL` message when
an audit fails, making it suitable for automated checks.

`--reproduce` runs the analysis in an isolated temporary directory and checks
that all 13 numerical CSV/JSON files and six PNG figures reproduce byte for
byte. It compares freshly generated artifacts to the checked-in outputs,
so strict image reproduction uses the pinned rendering environment. The
ordinary audit compares numbers with a 1e-12 tolerance and requires no plotting
dependencies. `--run-tests` also runs the complete 44-test suite. GitHub Actions
runs the suite and audit on pushes to `dev` and pull requests targeting `dev`.

After an intentional change, use this order: regenerate analysis, review and
update the report's narrative/tables, rebuild the PDF, then verify. Updating the
PDF metadata alone cannot repair stale CSVs or mismatched report tables.

## Report and final review

The report stays within the recommended 1,800-2,200 main-body words, including
its body tables and headings and excluding the title block, references,
captions, display equations, generation markers and appendices. The main body is 1,961 words;
the exact total and section counts are printed by `build_report.py` and
checked by `verify_submission.py`.

The PDF is typeset in 14 pages, including three new pages for Appendix D.
Tables stay with their captions and immediate
lead-ins, figures stay with captions and their immediate headings, and each
appendix starts on a fresh page. Equations use DejaVu Serif math to match the
body font. The build prints the page count; the visual review is recorded in
`docs/PDF_LAYOUT_REVIEW.md`.

| Section | Brief target | Current count |
| --- | ---: | ---: |
| 1 Introduction | 150-200 | 189 |
| 2 Bayesian inference | 400-450 | 446 |
| 3 HMM estimation | 550-650 | 648 |
| 4 Expected utility | 400-500 | 487 |
| 5 Conclusion | 150-200 | 191 |

The sensitivity subsection, its original Table 6 and all full sweeps are in
Appendix C. Section 4 retains a short pointer; its decision examples remain
in the main body. All 12 original computed-table checks remain. The generated
comparison and three complete scenario tables increase the audit to 16 tables.

`build_report.py` refreshes the marked Markdown regions before typesetting.
The comparison in Section 3 (Table 3a) reads `results/analysis.json`, including
observation/state counts, the peak Critical probability and earliest peak step,
and the final posterior. Appendix D reads `results/scenario_*_results.csv` and
shows all 90 observations, posterior vectors, most probable states and actions.
Probabilities are displayed to six decimals; no result file is changed.
Regenerate these tables without plotting or building a PDF using
`python generate_report_tables.py`. Do not hand-edit the marked regions.
The audit compares every cell with independently recomputed baseline results.

Belief figures distinguish observed N/W/A readings from a thin MAP strip below
them. The strip encodes the most probable posterior state at each step, using
the state colours and a separate legend row. It represents inference, not a
measured hidden-state label or the recommended action.

Section 2 explicitly identifies its Stable/Stressed/Critical digester examples
as the student's interpretation rather than definitions from the brief. It
interprets the Alarm posterior operationally and discusses red-meat processing
loads, ammonia inhibition, pH probe fouling/drift and correlated sensor errors.
Section 3 addresses the delay between loading changes and sensor response.
Reference [2] is the Russell and Norvig fourth-edition textbook, Chapter 16;
two peer-reviewed digestion papers supply domain context. Verified bibliographic
details, source links and the US/Global edition distinction are recorded in
`docs/REFERENCE_VERIFICATION.md`. These contextual edits reduce the body count
by three words and leave all numerical results, tables and audit checks intact.

The Markdown and PDF title block identify unit COMP6009, Assignment Part B,
student Sayuru Bopitiya, student ID 24071158 and date 26 October 2026.
`build_report.py` sets the PDF Author metadata to `Sayuru Bopitiya`.
The dated title block is fixed submission information, so rebuilding does
not silently replace its date with the build date. The exact title block
is defined in `report_contract.py` and delimited by HTML comments in the
Markdown. If the submission details change, update the Markdown and shared
contract together, update the PDF author setting and its audit if needed,
then rebuild and verify. Review the interpretation and ensure you can explain
the calculation and code before submitting.

`results/verification.txt` records the checks run while preparing this package.
