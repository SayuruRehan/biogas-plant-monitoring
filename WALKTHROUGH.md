# Understanding the assignment

The system answers three related questions:

1. **What condition is the digester probably in after one reading?** Bayesian inference.
2. **How does that belief evolve as readings arrive?** HMM filtering.
3. **Which action has the best expected consequence?** Expected utility.

## Finding the report evidence

The report's five main sections cover the introduction, Bayesian inference,
HMM estimation, expected-utility decisions and conclusion. The main body is
1,961 words, including its tables and headings; the title block, references,
captions, display equations and appendices are excluded.

Section 2 labels its digester-state descriptions as the student's illustrative
interpretation, not definitions supplied by the brief. Stable suggests steady
methane yield and normal pH; Stressed suggests rising volatile fatty acids or
drifting pH; Critical suggests acidification or process-failure risk. The Alarm
posterior is a model belief requiring investigation, not proof of failure.
Limitations address variable fat/protein loading, ammonia, delayed sensor
responses, pH probe fouling/drift and correlated errors in red-meat digestion.

Section 3 Table 3a compares observation counts, most probable state counts,
Critical peaks and final posteriors across A, B and C. It is generated from
`results/analysis.json`. Figures 1-3 distinguish observations from a thin MAP
strip showing the inferred most probable state; neither gives ground truth.

| Appendix | What to use it for |
| --- | --- |
| A | Check the supplied prior, sensor, transition and utility tables; complete the Generative AI use declaration |
| B | Compare all three actions' expected utilities over time |
| C | Read the sensitivity subsection and Table 6, close-decision margins, switching threshold and full sweeps |
| D | Trace all 90 observations, posterior vectors, most probable states and recommended actions in three generated tables |

The sensitivity subsection was moved out of Section 4 into Appendix C.
Section 4 keeps its decision examples and a short appendix pointer. Appendix D
is generated from `results/scenario_*_results.csv`; do not edit its marked
region by hand. The audit checks all 16 report tables against recomputation.
References [1]-[6] include the supplied brief, Russell and Norvig's textbook
decision-theory chapter, HMM theory and peer-reviewed digestion literature.

## 1. A sensor reading is evidence, not the true state

Stable, Stressed and Critical describe the hidden biological condition.
Normal, Warning and Alarm describe readings you can observe. A stable
digester can still produce an Alarm: the supplied model assigns this a 0.05
probability. A critical digester can produce Normal with probability 0.05.

Start with the prior: 70% Stable, 20% Stressed, 10% Critical.
For Warning, multiply it by the Warning likelihoods:

| State | Calculation | Weight |
| --- | --- | ---: |
| Stable | 0.70 × 0.15 | 0.105 |
| Stressed | 0.20 × 0.60 | 0.120 |
| Critical | 0.10 × 0.25 | 0.025 |

Weights sum to 0.25. Divide each by 0.25 to obtain 42%, 48%, 10%.
Stressed is most likely, but the evidence is not decisive.

To combine Warning and Abnormal pH, multiply by one more likelihood before
normalising. This gives about 11.44% Stable, 65.40% Stressed and 23.16%
Critical. That multiplication assumes the sensors are independent once you
know the hidden state. It could exaggerate confidence if they share evidence.

## 2. The HMM remembers earlier evidence

At the first reading, use the prior directly. From the second reading onwards:

- **Predict:** use the transition table to distribute each old state's
  probability among the possible next states. For example, 80% of the
  probability mass on Stable stays on Stable, 18% moves to Stressed, and
  2% moves to Critical.
- **Update:** multiply each predicted state probability by the current
  observation's likelihood.
- **Normalise:** divide by the sum so that the new probabilities total one.

Do this 30 times for each scenario, resetting the prior before starting the
next scenario. Use only Sensor 1. Do not feed the action recommendation back
into this supplied transition model.

Why does history matter? An Alarm at A's step 20 produces about 24.37%
Critical after mostly normal readings. B's Alarm at step 15 produces about
59.61% Critical after repeated Warnings. The current label is the same, but
the belief before seeing it differs.

Filtering uses readings up to the current time. Smoothing would also use
future readings to revise past beliefs. Viterbi would select a most likely
complete hidden-state path. Neither is required here.

## 3. A likely state is different from a good action

For each action, multiply its utility in each state by that state's posterior
probability, then add the three products. Choose the largest total.

At A's step 20, Stable is the most likely state, but Critical still has 24.37%
probability. Continue carries a -20 utility in Critical. Expected utilities
are approximately -0.098 for Continue, 2.912 for Reduce Feed and 1.363 for
Intervene. Reduce Feed wins because it balances the possible benefit and loss.

At B's step 22, Stressed is most likely, but Intervene wins because a 32.37%
Critical probability makes the risk of reducing feed alone less attractive.
Always show all three expected utilities when explaining a decision.

## Questions to be ready to answer

- **Did you train a model?** No. The brief supplied all probabilities and
  utilities. The work is inference and decision-making with that fixed model.
- **How do you know the code is correct?** Manual Bayesian results agree with
  Python, and the HMM agrees with an independent sum over all hidden-state
  paths for a short sequence. Other tests check conventions and invalid inputs.
- **Is C truly critical at step 25?** The baseline model infers an 87.11%
  probability; there is no hidden-state label proving the real condition.
- **Did intervention cause recovery?** The supplied data cannot demonstrate
  that. Actions do not affect transition probabilities in this implementation.
- **What did sensitivity show?** Some choices change when sensor likelihoods,
  state persistence or failure costs change. None of these experiments proves
  that one variant is the best real-world model.

Start reading `biogas.py` with `bayesian_update`, then `hmm_filter`, then
`recommend_action`. Use a result CSV to follow one complete step from
prediction through posterior to recommendation.

## 4. Following the numerical HMM example

Report Table 3 uses A's second Normal reading. The previous belief is
approximately (0.910569, 0.081301, 0.008130). Multiplying it by the transition
table predicts (0.749187, 0.215122, 0.035691). Multiply these by the Normal
likelihoods (0.80, 0.25, 0.05) to get weights approximately
(0.599350, 0.053780, 0.001785). Divide by their full-precision sum, 0.654915
when rounded, to obtain (0.915157, 0.082118, 0.002725).

The `from_stable`, `from_stressed` and `from_critical` columns of
`results/worked_hmm_step.csv` show exactly where each prediction comes from.

## 5. Understanding decision robustness

This material is in Appendix C; it is separate from the baseline inference
and the Section 4 decision analyses.

At B, step 16, Reduce Feed wins by only 0.245874 utility units over Continue.
This is a close choice under the supplied utility model. It does not mean
there is a 24.59% chance of correctness: utilities and probabilities have
different meanings. `decision_margins.csv` records all 90 comparisons.

At B, step 28, the baseline recommends Continue. Keeping its belief fixed,
vary only the utility of continuing when Critical. Continue and Reduce Feed
tie at approximately -31.303158. A more negative value favours Reduce Feed;
a less negative value favours Continue. Intervene scores below both at this
tie, so the boundary really changes the best action.

Parameter sweeps ask whether this behaviour holds across several settings.
Each family changes one assumption, with all other parts kept baseline.
For example, a 10% uniform sensor mixture changes two C recommendations but
increases its number of action changes from 20 to 21. We should therefore
avoid claiming that greater uncertainty always produces fewer switches.

Use `python verify_submission.py --reproduce --run-tests` to rerun the checks.
This verifies mathematical consistency and reproducibility, not real-world
digester accuracy or the benefits of actually implementing the actions.
GitHub Actions also runs the suite and audit for pushes and pull requests to
`dev`, `master` and `main`. The verification record is
`results/verification.txt`. The AI-use placeholder in README and Appendix A
must be completed with the tools actually used and how they were used.
