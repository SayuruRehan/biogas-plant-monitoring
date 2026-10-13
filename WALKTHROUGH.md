# Understanding the assignment

The system answers three related questions:

1. **What condition is the digester probably in after one reading?** Bayesian inference.
2. **How does that belief evolve as readings arrive?** HMM filtering.
3. **Which action has the best expected consequence?** Expected utility.

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
