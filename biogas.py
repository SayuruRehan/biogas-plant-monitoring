"""Bayesian inference, explicit HMM filtering, and expected-utility decisions.

The inference code uses only the Python standard library; no HMM or Bayesian
inference library is used. State and action order follows dictionary insertion
order. Exact ties choose the first entry, making results reproducible.
"""
from math import isclose, isfinite, fsum

BASELINE = {
    'prior': {'Stable': 0.70, 'Stressed': 0.20, 'Critical': 0.10},
    'sensor1': {
        'Stable': {'Normal': 0.80, 'Warning': 0.15, 'Alarm': 0.05},
        'Stressed': {'Normal': 0.25, 'Warning': 0.60, 'Alarm': 0.15},
        'Critical': {'Normal': 0.05, 'Warning': 0.25, 'Alarm': 0.70},
    },
    'sensor2': {
        'Stable': {'Normal pH': 0.90, 'Abnormal pH': 0.10},
        'Stressed': {'Normal pH': 0.50, 'Abnormal pH': 0.50},
        'Critical': {'Normal pH': 0.15, 'Abnormal pH': 0.85},
    },
    # Rows = current state; columns = next state.
    'transition': {
        'Stable': {'Stable': 0.80, 'Stressed': 0.18, 'Critical': 0.02},
        'Stressed': {'Stable': 0.25, 'Stressed': 0.60, 'Critical': 0.15},
        'Critical': {'Stable': 0.05, 'Stressed': 0.30, 'Critical': 0.65},
    },
    # Rows = action; columns = hidden state.
    'utility': {
        'Continue': {'Stable': 10, 'Stressed': 2, 'Critical': -20},
        'Reduce Feed': {'Stable': 5, 'Stressed': 6, 'Critical': -5},
        'Intervene': {'Stable': -4, 'Stressed': 3, 'Critical': 8},
    },
}


def validate_distribution(values, label='distribution'):
    """Require a finite, nonnegative probability vector summing to one."""
    if not values or any(not isfinite(v) or v < 0 or v > 1 for v in values.values()):
        raise ValueError(f'{label} must contain finite probabilities in [0, 1]')
    if not isclose(fsum(values.values()), 1.0, rel_tol=0, abs_tol=1e-10):
        raise ValueError(f'{label} must sum to one')


def validate_table(table, states, columns=None, label='probability table'):
    """Validate row probabilities and consistent state/observation labels."""
    if set(table) != set(states):
        raise ValueError(f'{label}: row states do not match belief states')
    expected = set(columns) if columns is not None else set(next(iter(table.values())))
    for state, row in table.items():
        if set(row) != expected:
            raise ValueError(f'{label}: inconsistent columns in row {state}')
        validate_distribution(row, f'{label} row {state}')


def normalise(weights):
    """Return a posterior and evidence probability; reject impossible evidence."""
    evidence_probability = fsum(weights.values())
    if not isfinite(evidence_probability) or evidence_probability <= 0:
        raise ValueError('Evidence has zero or invalid probability under this model')
    return {s: value/evidence_probability for s, value in weights.items()}, evidence_probability


def bayesian_update(prior, evidence):
    """Update with (observation, sensor_table) pairs, independent given state.

    Passing no observations returns a copy of the prior. Observations must be
    valid labels in their sensor model. Tables and prior are never modified.
    """
    validate_distribution(prior, 'prior')
    weights = dict(prior)
    for observation, sensor in evidence:
        validate_table(sensor, prior, label='sensor model')
        if observation not in next(iter(sensor.values())):
            raise ValueError(f'Unknown sensor observation: {observation!r}')
        for state in prior:
            weights[state] *= sensor[state][observation]
    return normalise(weights)[0]


def hmm_filter(observations, prior, transition, sensor):
    """Filter an iterable of observations using prediction/update/normalisation.

    At t=1, prediction is the supplied prior (no transition). At t>=2:
      prediction[x] = sum(previous[s] * transition[s][x] for s in states)
      unnormalised[x] = prediction[x] * sensor[x][observation]
      posterior[x] = unnormalised[x] / sum(unnormalised.values())
    This is online filtering, not smoothing or Viterbi path decoding.
    """
    validate_distribution(prior, 'prior')
    validate_table(transition, prior, columns=prior, label='transition')
    validate_table(sensor, prior, label='sensor model')
    previous = dict(prior)
    records = []
    for t, observation in enumerate(observations, start=1):
        if observation not in next(iter(sensor.values())):
            raise ValueError(f'Unknown observation at time {t}: {observation!r}')
        # Step 1: prediction (prior used directly for the first observation).
        prediction = dict(previous) if t == 1 else {
            x: fsum(previous[s] * transition[s][x] for s in prior) for x in prior
        }
        # Step 2: observation update.
        weights = {s: prediction[s] * sensor[s][observation] for s in prior}
        # Step 3: normalisation.
        posterior, evidence_probability = normalise(weights)
        records.append({
            'time': t, 'observation': observation, 'prediction': prediction,
            'unnormalised': weights, 'evidence_probability': evidence_probability,
            'posterior': posterior, 'most_probable_state': max(posterior, key=posterior.get),
        })
        previous = posterior
    return records


def recommend_action(belief, utility_table):
    """Return (best action, expected utility per action) for any valid belief."""
    validate_distribution(belief, 'belief')
    if not utility_table:
        raise ValueError('At least one action is required')
    for action, row in utility_table.items():
        if set(row) != set(belief) or any(not isfinite(v) for v in row.values()):
            raise ValueError(f'Invalid utility row for {action}')
    expected = {a: fsum(belief[s] * row[s] for s in belief) for a, row in utility_table.items()}
    return max(expected, key=expected.get), expected
