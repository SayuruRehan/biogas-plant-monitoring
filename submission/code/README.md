# COMP6009 Assignment Part B: Biogas Plant Monitoring and Decision System

Student: Sayuru Bopitiya (24071158)

This code infers the hidden condition of an anaerobic digester from uncertain
sensor readings, tracks that condition over time and recommends an operational
action:

1. **Task 1, Bayesian inference:** posterior beliefs from Sensor 1 alone and from
   Sensor 1 combined with the pH sensor.
2. **Task 2, HMM filtering:** P(X_t | e_1:t) at every step of the three supplied
   30-step scenarios, using explicit prediction, observation update and normalisation.
3. **Task 3, expected-utility decisions:** the expected utility of each action and
   the recommended action at every step, computed from the Task 2 beliefs.

All inference and decision code uses only the Python standard library. No HMM or
probabilistic inference library is used. matplotlib is used only to draw the figures.

## Requirements

- Python 3.10 or newer (tested with 3.12)
- matplotlib (see `requirements.txt`), needed only for the figures

## How to run

Run these commands from this folder (the folder that contains `main.py`).

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

`main.py` reads the three CSV files in `data/`, prints the Task 1 posteriors and a
summary of each scenario, and writes every numerical result to `results/` and every
figure to `results/figures/`. All outputs are already included, so running it is
needed only to reproduce them. To write to another folder instead, use
`python main.py --output-dir reproduced`.

To run the unit tests (no third-party packages needed):

```bash
python -m unittest discover -s tests -v
```

The tests check the posteriors against hand-calculated fractions, check the HMM
filter against brute-force enumeration of every hidden state path, and check edge
cases such as invalid tables, unknown observations and impossible evidence.

## Folder layout

| Path | Contents |
| --- | --- |
| `main.py` | Entry point: loads and validates the data, runs Tasks 1 to 3 and the sensitivity experiments, writes results and figures |
| `src/biogas_model.py` | Supplied model tables (`BASELINE`), `bayesian_update` (Task 1), `hmm_filter` (Task 2), `recommend_action(belief, utility_table)` (Task 3) and `analyse_sequence` |
| `src/sensitivity.py` | Sensitivity experiments, parameter sweeps, decision margins, the switching threshold and the worked HMM step |
| `src/report_figures.py` | Belief plots, action timeline and expected-utility charts |
| `tests/` | Unit tests |
| `data/` | The three supplied scenario datasets, unmodified |
| `results/` | Numerical outputs (CSV and JSON) |
| `results/figures/` | Figures used in the report (PNG and PDF) |

## Where each report result comes from

| Report item | File |
| --- | --- |
| Table 1 (Task 1 posteriors) | `results/task1_bayesian_results.csv` |
| Table 3 (worked HMM step, Scenario A, t = 2) | `results/worked_hmm_step.csv` |
| Table 3a, Table 4, Appendix D | `results/scenario_{A,B,C}_results.csv`, `results/analysis.json` |
| Figures 1 to 3 | `results/figures/scenario_{A,B,C}_beliefs.png` |
| Figure 4 | `results/figures/recommended_actions.png` |
| Table 5, Table C1 | `results/scenario_{A,B,C}_results.csv`, `results/closest_decisions.csv`, `results/decision_margins.csv` |
| Table 6 | `results/sensitivity_summary.csv` |
| Table C2, Figure C1 | `results/parameter_sweep_summary.csv`, `results/figures/parameter_sweeps.png` |
| Switching threshold (Appendix C, B at t = 28) | `results/robustness.json` (`switching_threshold`) |
| Figure B1 | `results/figures/expected_utilities.png` |

Each scenario results CSV has, for every step: the prediction, the unnormalised
weights, the normalising constant (`evidence_probability`), the posterior, the most
probable state, the expected utility of each action, the recommended action and the
decision margin. The `*_details.csv` files hold the full step-level results of every
sensitivity setting.

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
