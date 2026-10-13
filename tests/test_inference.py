"""Independent numerical and edge-case checks for the assignment algorithms."""
import itertools
import math
import unittest

from biogas import bayesian_update, hmm_filter, recommend_action, BASELINE


class InferenceTests(unittest.TestCase):
    def setUp(self):
        self.states = tuple(BASELINE['prior'])

    def close(self, actual, expected):
        for state, value in expected.items():
            self.assertAlmostEqual(actual[state], value, places=12)

    def test_warning_matches_manual_fraction(self):
        got = bayesian_update(BASELINE['prior'], [('Warning', BASELINE['sensor1'])])
        self.close(got, dict(zip(self.states, [0.105/0.25, 0.12/0.25, 0.025/0.25])))

    def test_combined_evidence_matches_manual_fraction(self):
        got = bayesian_update(BASELINE['prior'], [('Warning', BASELINE['sensor1']), ('Abnormal pH', BASELINE['sensor2'])])
        self.close(got, dict(zip(self.states, [0.0105/0.09175, 0.06/0.09175, 0.02125/0.09175])))

    def test_general_observations_and_sensor_order(self):
        for observation in ('Normal', 'Warning', 'Alarm'):
            got = bayesian_update(BASELINE['prior'], [(observation, BASELINE['sensor1'])])
            self.assertAlmostEqual(sum(got.values()), 1.0)
        a = [('Alarm', BASELINE['sensor1']), ('Normal pH', BASELINE['sensor2'])]
        self.close(bayesian_update(BASELINE['prior'], a), bayesian_update(BASELINE['prior'], list(reversed(a))))

    def test_first_step_has_no_transition(self):
        rows = hmm_filter(['Warning'], BASELINE['prior'], BASELINE['transition'], BASELINE['sensor1'])
        self.close(rows[0]['prediction'], BASELINE['prior'])
        self.close(rows[0]['posterior'], dict(zip(self.states, [0.42, 0.48, 0.10])))

    def test_filter_matches_enumeration_of_all_hidden_paths(self):
        observations = ['Normal', 'Alarm', 'Warning', 'Normal']
        rows = hmm_filter(observations, BASELINE['prior'], BASELINE['transition'], BASELINE['sensor1'])
        # Brute force sums over 3^t paths, independent of the filtering recurrence.
        for length in range(1, len(observations)+1):
            totals = dict.fromkeys(self.states, 0.0)
            for path in itertools.product(self.states, repeat=length):
                weight = BASELINE['prior'][path[0]] * BASELINE['sensor1'][path[0]][observations[0]]
                for i in range(1, length):
                    weight *= BASELINE['transition'][path[i-1]][path[i]] * BASELINE['sensor1'][path[i]][observations[i]]
                totals[path[-1]] += weight
            evidence = sum(totals.values())
            self.close(rows[length-1]['posterior'], {s: totals[s]/evidence for s in self.states})

    def test_utility_can_disagree_with_most_likely_state(self):
        belief = {'Stable': 0.52, 'Stressed': 0.36, 'Critical': 0.12}
        action, utilities = recommend_action(belief, BASELINE['utility'])
        self.assertEqual(action, 'Reduce Feed')
        self.close(utilities, {'Continue': 3.52, 'Reduce Feed': 4.16, 'Intervene': -0.04})

    def test_pure_states_and_deterministic_ties(self):
        for state, expected in zip(self.states, ('Continue', 'Reduce Feed', 'Intervene')):
            action, _ = recommend_action({s: float(s == state) for s in self.states}, BASELINE['utility'])
            self.assertEqual(action, expected)
        table = {'First': dict.fromkeys(self.states, 1), 'Second': dict.fromkeys(self.states, 1)}
        self.assertEqual(recommend_action(BASELINE['prior'], table)[0], 'First')

    def test_invalid_probability_and_observation_rejected(self):
        for prior in ({'Stable': -0.1, 'Stressed': 0.5, 'Critical': 0.6}, {'Stable': math.nan, 'Stressed': 0.2, 'Critical': 0.1}, {'Stable': 0.2, 'Stressed': 0.2, 'Critical': 0.1}):
            with self.assertRaises(ValueError):
                bayesian_update(prior, [('Normal', BASELINE['sensor1'])])
        with self.assertRaises(ValueError):
            bayesian_update(BASELINE['prior'], [('Unknown', BASELINE['sensor1'])])

    def test_impossible_evidence_rejected(self):
        sensor = {s: {'Impossible': 0.0, 'Possible': 1.0} for s in self.states}
        with self.assertRaises(ValueError):
            bayesian_update(BASELINE['prior'], [('Impossible', sensor)])

    def test_empty_sequence_and_bad_transition(self):
        self.assertEqual(hmm_filter([], BASELINE['prior'], BASELINE['transition'], BASELINE['sensor1']), [])
        transition = {s: dict(row) for s, row in BASELINE['transition'].items()}
        transition['Stable']['Stable'] = 0.1
        with self.assertRaises(ValueError):
            hmm_filter(['Normal'], BASELINE['prior'], transition, BASELINE['sensor1'])


if __name__ == '__main__':
    unittest.main()
