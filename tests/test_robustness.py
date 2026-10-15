"""Checks for the four approved analysis improvements."""
import copy
import unittest
from pathlib import Path

from biogas import BASELINE, recommend_action
from run_analysis import analyse_sequence, load_observations, SCENARIOS
from robustness import build_extensions, pairwise_utility_threshold, SWEEP_PARAMETERS


class RobustnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.sequences = {s: load_observations(root/'data'/f) for s,f in SCENARIOS.items()}
        cls.rows = {s: analyse_sequence(obs, BASELINE) for s,obs in cls.sequences.items()}
        cls.original = copy.deepcopy(BASELINE)
        cls.extension = build_extensions(cls.sequences, cls.rows)

    def test_worked_second_step_matches_independent_fractions(self):
        worked = self.extension['worked_hmm_step']
        self.assertEqual((worked['scenario'], worked['time'], worked['observation']), ('A',2,'Normal'))
        self.assertAlmostEqual(worked['evidence_probability'], 80.5545/123, places=12)
        for row, old, prediction, weight in zip(worked['states'], [112/123,10/123,1/123], [92.15/123,26.46/123,4.39/123], [73.72/123,6.615/123,0.2195/123]):
            self.assertAlmostEqual(row['previous_belief'], old, places=12)
            self.assertAlmostEqual(row['prediction'], prediction, places=12)
            self.assertAlmostEqual(row['unnormalised'], weight, places=12)
            self.assertAlmostEqual(row['posterior'], weight/(80.5545/123), places=12)

    def test_closest_choices_and_all_90_margins(self):
        self.assertEqual(len(self.extension['decision_margins']),90)
        closest = self.extension['closest_decisions']
        self.assertEqual([(r['scenario'],r['time']) for r in closest], [('A',6),('B',16),('C',4)])
        self.assertAlmostEqual(closest[1]['decision_margin'], 0.245874279634724, places=12)
        self.assertEqual(closest[1]['runner_up'], 'Continue')

    def test_analytical_threshold_and_zero_mass(self):
        belief={'Stable':0.5,'Stressed':0.4,'Critical':0.1}
        self.assertAlmostEqual(pairwise_utility_threshold(belief, BASELINE['utility'], 'Continue', 'Critical', 'Reduce Feed'),-14,places=12)
        zero={'Stable':1.0,'Stressed':0.0,'Critical':0.0}
        self.assertIsNone(pairwise_utility_threshold(zero, BASELINE['utility'], 'Continue','Critical','Reduce Feed'))

    def test_b28_threshold_is_a_global_switch_not_a_dominated_tie(self):
        belief=self.rows['B'][27]['posterior']
        threshold=pairwise_utility_threshold(belief,BASELINE['utility'],'Continue','Critical','Reduce Feed')
        self.assertAlmostEqual(threshold,-31.30315769309321,places=10)
        table=copy.deepcopy(BASELINE['utility'])
        table['Continue']['Critical']=threshold
        _,utilities=recommend_action(belief,table)
        self.assertAlmostEqual(utilities['Continue'],utilities['Reduce Feed'],places=12)
        self.assertGreater(utilities['Continue'],utilities['Intervene'])
        for delta,expected in [(0.001,'Continue'),(-0.001,'Reduce Feed')]:
            table['Continue']['Critical']=threshold+delta
            self.assertEqual(recommend_action(belief,table)[0],expected)

    def test_sweeps_cover_all_settings_and_baseline_anchors(self):
        summary=self.extension['sweep_summary']
        self.assertEqual(len(summary),3*sum(map(len,SWEEP_PARAMETERS.values())))
        self.assertEqual(len(self.extension['sweep_details']),30*len(summary))
        for row in summary:
            self.assertEqual(row['Continue']+row['Reduce Feed']+row['Intervene'],30)
            if row['parameter']=={'sensor_noise':0,'persistence':0,'critical_utility':-20}[row['family']]:
                self.assertEqual(row['changed_actions'],0)
            self.assertTrue(0 <= row['changed_actions'] <= 30)

    def test_baseline_models_and_scenarios_are_not_mutated(self):
        self.assertEqual(BASELINE,self.original)
        fresh={s:analyse_sequence(obs,BASELINE) for s,obs in self.sequences.items()}
        self.assertEqual(self.rows,fresh)


if __name__=='__main__':
    unittest.main()
