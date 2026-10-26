# Assignment coverage

| Requirement | Evidence |
| --- | --- |
| General Bayesian inference using supplied models | `biogas.py`: `BASELINE` and `bayesian_update` |
| Normal, Warning and Alarm posteriors | Report Table 1; `results/task1_bayesian_results.csv` |
| Warning + Abnormal pH and comparison | Report Section 2, Tables 1-2 |
| Manual weights, normalisation and posterior | Report Section 2 and Table 2; two numerical tests |
| Fully worked second HMM observation | Report Section 3, Table 3; `results/worked_hmm_step.csv` |
| State versus observation distinction | Report Introduction and Section 2 |
| Conditional independence and other model limitations | Report Section 2 |
| Explicit prediction, update and normalisation | `biogas.py`: `hmm_filter`; report Section 3 |
| First observation updates prior without transition | Code comment and dedicated unit test |
| All three supplied 30-step datasets; Sensor 1 only | `data/`; `run_analysis.py`; all three result CSV files |
| Every posterior and most probable state | `results/scenario_A_results.csv`, B and C equivalents |
| Clearly labelled probability plots | Report Figures 1-3; `figures/` |
| At least two notable belief changes per scenario | Each scenario subsection in report Section 3 |
| Compare scenario behaviour; discuss HMM limitation | Final paragraphs of report Section 3 |
| Reusable utility recommendation function | `biogas.py`: `recommend_action` |
| Every action's expected utility at every step | Three result CSV files, `analysis.json`, appendix Figure B1 |
| Recommended actions over time | Report Figure 4, Table 4 and result CSV files |
| At least two notable decisions and explanation | Report Table 5 and accompanying discussion |
| Why action can differ from most probable state | Report A t=20 and B t=22 analyses |
| Utility model assumptions and limitations | Report Section 4 |
| Evaluate effects of uncertainty/modelling assumptions | Report Table 6; Appendix C; original and extended sensitivity CSV files |
| Decision strength and switching threshold | Section 4 and Appendix C; `results/decision_margins.csv` and `robustness.json` |
| Parameter sweeps across plausible modelling choices | Appendix C: 42 settings/scenarios and 1,260 evaluated time steps |
| Reusable dataset, results and report audit | `verify_submission.py`; 35 tests, section word budgets, sensitivity appendix placement and dev-branch GitHub Actions |
| Report PDF and recommended word range | `report/COMP6009_Part_B_Report.pdf`; count printed by builder |
| IEEE-style references | Report references [1]-[4] |
| Python source and data/results | Package source, `data/`, `results/` and `figures/` |
| Reproduction instructions | `README.md` |

The package provides a worked solution and the supplied student identity in the
report title block. Check whether an additional institution-specific cover sheet
is required before submission.
