"""End-to-end audit tests, including deliberately corrupted submissions."""
import csv
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from verify_submission import VerificationError, verify_submission
from report_contract import report_word_count


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        original=Path(__file__).resolve().parents[1]
        for folder in ('data','results','report','figures'):
            shutil.copytree(original/folder,self.root/folder,ignore=shutil.ignore_patterns('_equations'))
        shutil.copy2(original/'README.md',self.root/'README.md')

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
        self.assertTrue(any('title block' in check.lower() for check in checks))

    def test_title_block_is_excluded_from_word_count(self):
        title='''<!-- title-block -->
# Biogas Plant Intelligent Monitoring and Decision System

Unit: COMP6009

Assignment Part B

Student name: Sayuru Bopitiya

Student ID: 24071158

Date: 26 October 2026
<!-- /title-block -->'''
        body='## 1. Introduction\n\nThree body words.\n\n## References\n\nExcluded reference.'
        self.assertEqual(report_word_count(title+'\n\n'+body),report_word_count(body))
        self.assertEqual(report_word_count(body),5)

    def test_incorrect_appendix_a_title_is_rejected(self):
        path=self.root/'report'/'COMP6009_Part_B_Report.md'
        title='## Appendix A. Baseline model tables\n\n'
        self.assertIn(title,path.read_text())
        path.write_text(path.read_text().replace(title,'## Appendix A. Baseline model tables and declaration\n\n',1))
        with self.assertRaisesRegex(VerificationError,'Appendix A.*title'):
            verify_submission(self.root)

    def test_unfilled_template_marker_is_rejected(self):
        for filename,marker in [('report/COMP6009_Part_B_Report.md','[DECLARE missing details]'),
                                ('README.md','[declare missing details]')]:
            with self.subTest(filename=filename):
                path=self.root/filename
                original=path.read_text()
                try:
                    path.write_text(original+'\n'+marker+'\n')
                    with self.assertRaisesRegex(VerificationError,'unfilled template marker'):
                        verify_submission(self.root)
                finally:
                    path.write_text(original)

    def test_missing_title_block_is_rejected(self):
        path=self.root/'report'/'COMP6009_Part_B_Report.md'
        report=path.read_text()
        path.write_text(report[report.index('## 1. Introduction'):])
        with self.assertRaisesRegex(VerificationError,'title block'):
            verify_submission(self.root)

    def test_incorrect_student_id_is_rejected(self):
        path=self.root/'report'/'COMP6009_Part_B_Report.md'
        path.write_text(path.read_text().replace('24071158','99999999',1))
        with self.assertRaisesRegex(VerificationError,'title block'):
            verify_submission(self.root)

    def test_incorrect_pdf_author_is_rejected(self):
        path=self.root/'report'/'COMP6009_Part_B_Report.pdf'
        content,count=re.subn(rb'/Author\s*\([^)]*\)',b'/Author (Incorrect Student)',path.read_bytes(),count=1)
        self.assertEqual(count,1)
        path.write_bytes(content)
        with self.assertRaisesRegex(VerificationError,'PDF Author'):
            verify_submission(self.root)

    def test_report_sections_meet_their_word_budgets(self):
        text=(self.root/'report'/'COMP6009_Part_B_Report.md').read_text()
        sections=re.findall(r'^## ([1-5])\. .*?(?=^## |\Z)',text,re.M|re.S)
        self.assertEqual(sections,['1','2','3','4','5'])
        for number,lower,upper in [(1,150,200),(2,400,450),(3,550,650),(4,400,500),(5,150,200)]:
            section=re.search(rf'^## {number}\. .*?(?=^## |\Z)',text,re.M|re.S).group()
            with self.subTest(section=number):
                self.assertGreaterEqual(report_word_count(section),lower)
                self.assertLessEqual(report_word_count(section),upper)
        self.assertGreaterEqual(report_word_count(text),1950)
        self.assertLessEqual(report_word_count(text),2100)

    def test_oversized_introduction_is_rejected(self):
        path=self.root/'report'/'COMP6009_Part_B_Report.md'
        text=path.read_text().replace('## 2. Probabilistic','Extra words. '*101+'\n\n## 2. Probabilistic',1)
        path.write_text(text)
        with self.assertRaisesRegex(VerificationError,'Section 1 word count'):
            verify_submission(self.root)

    def test_missing_numbered_section_is_rejected(self):
        path=self.root/'report'/'COMP6009_Part_B_Report.md'
        path.write_text(path.read_text().replace('## 3. HMM','## 6. HMM',1))
        with self.assertRaisesRegex(VerificationError,'report sections'):
            verify_submission(self.root)

    def test_sensitivity_in_main_body_is_rejected(self):
        path=self.root/'report'/'COMP6009_Part_B_Report.md'
        text=path.read_text().replace('## 5. Conclusion','### Sensitivity to modelling choices\n\n## 5. Conclusion',1)
        path.write_text(text)
        with self.assertRaisesRegex(VerificationError,'Sensitivity.*Appendix C'):
            verify_submission(self.root)

    def test_appendix_d_contains_all_90_steps(self):
        from report_contract import parse_tables
        text=(self.root/'report'/'COMP6009_Part_B_Report.md').read_text()
        tables=[t for t in parse_tables(text) if t[0][0]=='t']
        self.assertEqual(len(tables),3)
        for table in tables:
            self.assertEqual(len(table),31)
            self.assertEqual([row[0] for row in table[1:]],[str(t) for t in range(1,31)])

    def test_corrupt_appendix_probability_is_rejected(self):
        path=self.root/'report'/'COMP6009_Part_B_Report.md'
        text=path.read_text()
        row='| 1 | Normal | 0.910569 | 0.081301 | 0.008130 | Stable | Continue |'
        self.assertIn(row,text)
        path.write_text(text.replace(row,row.replace('0.910569','0.900000'),1))
        with self.assertRaisesRegex(VerificationError,'report table'):
            verify_submission(self.root)

    def test_appendix_generator_reads_csv(self):
        import importlib.util
        self.assertIsNotNone(importlib.util.find_spec('generate_report_tables'))
        from generate_report_tables import update_generated_tables
        self.edit_csv('scenario_A_results.csv',lambda rows:rows[0].update(posterior_stable='0.123456'))
        update_generated_tables(self.root)
        text=(self.root/'report'/'COMP6009_Part_B_Report.md').read_text()
        self.assertIn('| 1 | Normal | 0.123456 | 0.081301 | 0.008130 | Stable | Continue |',text)

    def test_scenario_comparison_contains_counts_peaks_and_final_beliefs(self):
        text=(self.root/'report'/'COMP6009_Part_B_Report.md').read_text()
        self.assertIn('| A | 26 / 3 / 1 | 27 / 3 / 0 | 0.243657 | 20 | 0.910045 / 0.087120 / 0.002835 |',text)
        self.assertIn('| C | 15 / 10 / 5 | 14 / 12 / 4 | 0.871110 | 25 | 0.350838 / 0.596407 / 0.052755 |',text)

    def test_incorrect_comparison_peak_time_is_rejected(self):
        path=self.root/'report'/'COMP6009_Part_B_Report.md'
        text=path.read_text();self.assertIn('| 0.243657 | 20 |',text)
        path.write_text(text.replace('| 0.243657 | 20 |','| 0.243657 | 21 |',1))
        with self.assertRaisesRegex(VerificationError,'report table'):
            verify_submission(self.root)

    def test_comparison_generator_reads_analysis_json(self):
        from generate_report_tables import update_generated_tables
        path=self.root/'results'/'analysis.json'
        data=json.loads(path.read_text());data['summary']['A']['observations']['Normal']=99
        path.write_text(json.dumps(data))
        update_generated_tables(self.root)
        text=(self.root/'report'/'COMP6009_Part_B_Report.md').read_text()
        self.assertIn('| A | 99 / 3 / 1 | 27 / 3 / 0 |',text)

    def test_generation_markers_are_not_report_words(self):
        body='## 3. Results\n\n| A | 26 | 3 | 1 |'
        marked='<!-- generated:comparison:start -->\n\n'+body+'\n\n<!-- generated:comparison:end -->'
        self.assertEqual(report_word_count(marked),report_word_count(body))

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
