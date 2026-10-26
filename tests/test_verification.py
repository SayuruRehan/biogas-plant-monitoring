"""End-to-end audit tests, including deliberately corrupted submissions."""
import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from verify_submission import VerificationError, verify_submission


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        original=Path(__file__).resolve().parents[1]
        for folder in ('data','results','report','figures'):
            shutil.copytree(original/folder,self.root/folder,ignore=shutil.ignore_patterns('_equations'))

    def edit_csv(self, filename, change):
        path=self.root/'results'/filename
        with path.open(newline='') as stream:
            reader=csv.DictReader(stream)
            fields=reader.fieldnames
            rows=list(reader)
        change(rows)
        with path.open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_complete_submission_passes(self):
        checks=verify_submission(self.root)
        self.assertTrue(any('90' in check for check in checks))
        self.assertTrue(any('report' in check.lower() for check in checks))

    def test_modified_dataset_is_rejected(self):
        path=self.root/'data'/'scenario_A_stable.csv'
        path.write_text(path.read_text().replace('1,Normal','1,Alarm',1))
        with self.assertRaisesRegex(VerificationError,'hash'):
            verify_submission(self.root)

    def test_missing_baseline_row_is_rejected(self):
        self.edit_csv('scenario_A_results.csv',lambda rows:rows.pop())
        with self.assertRaisesRegex(VerificationError,'scenario_A_results.csv'):
            verify_submission(self.root)

    def test_surplus_csv_cells_are_rejected(self):
        path=self.root/'results'/'scenario_A_results.csv'
        lines=path.read_text().splitlines()
        lines[1]+=',UNEXPECTED EXTRA CELL'
        path.write_text('\n'.join(lines)+'\n')
        with self.assertRaisesRegex(VerificationError,'extra cells'):
            verify_submission(self.root)

    def test_wrong_recommendation_is_rejected(self):
        self.edit_csv('scenario_B_results.csv',lambda rows:rows[0].update(recommended_action='Intervene'))
        with self.assertRaisesRegex(VerificationError,'recommended_action'):
            verify_submission(self.root)

    def test_nonfinite_probability_is_rejected(self):
        self.edit_csv('scenario_C_results.csv',lambda rows:rows[0].update(posterior_stable='nan'))
        with self.assertRaisesRegex(VerificationError,'posterior_stable'):
            verify_submission(self.root)

    def test_stale_sweep_table_is_rejected(self):
        self.edit_csv('parameter_sweep_summary.csv',lambda rows:rows[0].update(changed_actions=99))
        with self.assertRaisesRegex(VerificationError,'parameter_sweep_summary.csv'):
            verify_submission(self.root)

    def test_stale_report_table_is_rejected(self):
        path=self.root/'report'/'COMP6009_Part_B_Report.md'
        path.write_text(path.read_text().replace('| Normal | 0.910569 |','| Normal | 0.900000 |',1))
        with self.assertRaisesRegex(VerificationError,'report table'):
            verify_submission(self.root)

    def test_missing_figure_is_rejected(self):
        (self.root/'figures'/'parameter_sweeps.png').unlink()
        with self.assertRaisesRegex(VerificationError,'parameter_sweeps.png'):
            verify_submission(self.root)

    def test_pdf_becomes_stale_after_a_narrative_edit(self):
        path=self.root/'report'/'COMP6009_Part_B_Report.md'
        path.write_text(path.read_text().replace('## 5. Conclusion','## 5. Overall conclusion',1))
        with self.assertRaisesRegex(VerificationError,'PDF is stale: source-sha256'):
            verify_submission(self.root)

    def test_pdf_becomes_stale_after_an_embedded_figure_changes(self):
        path=self.root/'figures'/'parameter_sweeps.png'
        path.write_bytes(path.read_bytes()+b'changed')
        with self.assertRaisesRegex(VerificationError,'PDF is stale: figures-sha256'):
            verify_submission(self.root)


if __name__=='__main__':
    unittest.main()
