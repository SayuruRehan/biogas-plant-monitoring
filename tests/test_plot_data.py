"""The strip shows inferred state labels, independently of observations."""
import unittest

import plot_results


class PlotDataTests(unittest.TestCase):
    def test_strip_encodes_most_probable_state_not_observation(self):
        self.assertTrue(hasattr(plot_results,'most_probable_strip'))
        rows=[{'observation':'Alarm','most_probable_state':'Stable'},
              {'observation':'Normal','most_probable_state':'Stressed'},
              {'observation':'Warning','most_probable_state':'Critical'}]
        self.assertEqual(plot_results.most_probable_strip(rows),[0,1,2])

    def test_unknown_state_label_is_rejected(self):
        self.assertTrue(hasattr(plot_results,'most_probable_strip'))
        with self.assertRaises(ValueError):
            plot_results.most_probable_strip([{'most_probable_state':'Normal'}])


if __name__=='__main__':
    unittest.main()
