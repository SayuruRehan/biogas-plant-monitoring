# Assignment coverage

| Requirement | Evidence |
| --- | --- |
| General Bayesian inference using supplied models | `biogas.py`: `BASELINE` and `bayesian_update` |
| Normal, Warning and Alarm posteriors | Report Table 1; `results/task1_bayesian_results.csv` |
| Warning + Abnormal pH and comparison | Report Section 2, Tables 1-2 |
| Manual weights, normalisation and posterior | Report Section 2 and Table 2; two numerical tests |
| Fully worked second HMM observation | Report Section 3, Table 3; `results/worked_hmm_step.csv` |
| State versus observation distinction | Report Introduction and Section 2 |
| Illustrative operational state interpretation and Alarm posterior meaning | Report Section 2, explicitly distinguished from brief-supplied definitions |
| Conditional independence and red-meat digester limitations | Sections 2-3: variable fat/protein loading, ammonia, loading-response delay, pH probe fouling/drift and correlated errors |
| Explicit prediction, update and normalisation | `biogas.py`: `hmm_filter`; report Section 3 |
| First observation updates prior without transition | Code comment and dedicated unit test |
| All three supplied 30-step datasets; Sensor 1 only | `data/`; `run_analysis.py`; all three result CSV files |
| Every observation, posterior, most probable state and recommendation | Appendix D Tables D1-D3: all 90 steps, generated from `results/scenario_A_results.csv`, B and C equivalents |
| Clearly labelled probability plots | Report Figures 1-3, with observation row and most probable state strip; `figures/` |
| At least two notable belief changes per scenario | Each scenario subsection in report Section 3 |
| Compare scenario behaviour; discuss HMM limitation | Final paragraphs of report Section 3 |
| Compact cross-scenario comparison | Section 3 Table 3a, generated from `analysis.json` and independently audited |
| Reusable utility recommendation function | `biogas.py`: `recommend_action` |
| Every action's expected utility at every step | Three result CSV files, `results/analysis.json`, Appendix B Figure B1 |
| Recommended actions over time | Report Figure 4, Table 4 and result CSV files |
| At least two notable decisions and explanation | Section 4 Table 5 and A t=20, B t=15 and B t=22 discussions |
| Why action can differ from most probable state | Report A t=20 and B t=22 analyses |
| Utility model assumptions and limitations | Report Section 4 |
| Evaluate effects of uncertainty/modelling assumptions | Appendix C: relocated sensitivity subsection and Table 6; Section 4 retains only a pointer; original and extended sensitivity CSV files |
| Decision strength and switching threshold | Section 4 and Appendix C; `results/decision_margins.csv` and `robustness.json` |
| Parameter sweeps across plausible modelling choices | Appendix C: 42 settings/scenarios and 1,260 evaluated time steps |
| Reusable dataset, results and report audit | `verify_submission.py`; 44 tests, 16 report tables, section budgets, appendix placement and GitHub Actions for pushes/PRs to dev, master and main |
| Report PDF and recommended word range | `report/COMP6009_Part_B_Report.pdf`; 1,961 main-body words; section counts 189 / 446 / 648 / 487 / 191; title, references, captions, display equations and appendices excluded |
| IEEE-style references | Report references [1]-[6]; textbook Chapter 16 and two added peer-reviewed domain sources; verified details in `docs/REFERENCE_VERIFICATION.md` |
| Supplied model tables and additional utility plot | Appendix A model tables and Appendix B Figure B1 |
| Generative AI use declaration | README and report Appendix A contain the requested placeholder; student must complete it before submission |
| Python source and data/results | Package source, `data/`, `results/` and `figures/` |
| Reproduction instructions and recorded results | `README.md`; `results/verification.txt`; `python verify_submission.py --reproduce --run-tests` |

The package provides a worked solution and the supplied student identity in the
report title block. Check whether an additional institution-specific cover sheet
is required before submission.
