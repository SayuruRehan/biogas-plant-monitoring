# PDF layout review

Reviewed on 26 October 2026. The rebuilt report has **11 A4 pages**, compared
with 14 before the layout change. Every final page was rendered to PNG at
130 dpi and individually inspected after PDF compaction.

## Changes

- Replaced whole-scenario, whole-conclusion and whole-reference grouping with
  local groups for each visual and its caption.
- Kept immediate table lead-ins with the relevant table and caption, including
  the full sweep introduction on the final appendix page.
- Included immediate figure headings in their visual groups to prevent orphaned
  scenario and appendix headings.
- Retained a fresh page for each appendix. Used half-inch vertical margins,
  slightly tighter paragraph spacing and table padding, and an inset sweep
  figure to fit the final table and chart together. Body type remains 10.4 pt.
- Rendered equations using DejaVu Serif math at 12 pt, matching the body family.

## Page inspection

| Page | Content and inspection result |
| --- | --- |
| 1 | Title block, introduction and Bayesian setup; equation complete and clear. |
| 2 | Bayesian Tables 1 and 2 stay with their introductions and captions; HMM heading has following prose; equation fits above the footer. |
| 3 | Worked HMM introduction, Table 3 and caption together; Scenario A heading, figure and caption together; interpretation follows. |
| 4 | Scenario B and C headings, figures and captions paired; body text flows across the page boundary normally. |
| 5 | HMM discussion and decision section; equation, action figure and caption clear; Table 4 and caption together. |
| 6 | Decision introduction, Table 5 and caption together; decision analysis flows naturally; conclusion heading has a full opening paragraph. |
| 7 | Conclusion continuation and complete references; no short reference spillover page. |
| 8 | Appendix A starts at the top of a fresh page; all four baseline tables readable and complete. |
| 9 | Appendix B starts on a fresh page; full expected-utility figure and caption together. |
| 10 | Appendix C starts on a fresh page; sensitivity introduction, Table 6 and caption together; closest-decision table and caption together. |
| 11 | Full sweep introduction, Table C2 and caption, then sweep figure and caption; all fit with a clear footer. |

## Remaining layout observations

- Page 7 has unused space after the references because Appendix A starts on
  a fresh page. Short Appendices A and B leave space below their content on
  pages 8 and 9 for the same reason.
- Page 10 leaves room at the bottom because the next sweep introduction and
  table are kept together on page 11. Page 11 is denser but remains readable.
- No detached captions, orphaned headings, clipped text, missing mathematical
  glyphs or overlapping content were observed.

## Verification

All four required commands passed: `python -m unittest discover -s tests`,
`python run_analysis.py`, `python build_report.py`, and
`python verify_submission.py`. The suite retains 35 tests and the audit retains
all 12 numeric-table checks. Full numerical and PNG reproduction also passed.

The report Markdown, section counts, protected functions and numerical result
files are unchanged. The main-body count remains 1,966 words. Additional PDF
geometry checks confirmed 11 pages, eight captioned table pairs and their
explicit lead-ins, six figure-caption pairs, fresh appendix starts and text
inside the page bounds. The other four tables are the uncaptioned baseline
model tables in Appendix A.

To recreate page PNGs for review, run:

```bash
pdftoppm -r 130 -png report/COMP6009_Part_B_Report.pdf /tmp/biogas-page
```
