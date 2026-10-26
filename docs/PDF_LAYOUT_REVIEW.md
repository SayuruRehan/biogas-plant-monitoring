# PDF layout review

Reviewed on 26 October 2026. The rebuilt report has **14 A4 pages**. The earlier
layout revision reduced the report to 11 pages; the complete 90-step Appendix D
adds three pages. Every final page was rendered to PNG at 120 dpi and
individually inspected after PDF compaction.

Rechecked after the biogas-context revision: the main body is now **1,961
words**, three fewer than the preceding report. Two peer-reviewed domain
references and the corrected textbook entry still fit on page 7. All 14 pages
were rendered again and individually inspected; no page count or font-size
change was needed. Bibliographic evidence is recorded in
`REFERENCE_VERIFICATION.md`.

Appendix A contains only the supplied baseline model tables. Its title and all
four tables fit on page 8. Pages 7-9 were re-rendered and checked after the
latest cleanup; the main-body text and count remain unchanged.

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
- Added the generated Section 3 comparison and one compact 30-step table per
  scenario in Appendix D. Checked that step numbers remain on one line and
  headers wrap at word boundaries.
- Added a thin MAP strip and a separate legend row beneath the observed readings
  in each belief figure. State colours match the posterior curves.

## Page inspection

| Page | Content and inspection result |
| --- | --- |
| 1 | Title block, introduction, illustrative digester-state interpretations and Bayesian setup; equation complete and clear. |
| 2 | Bayesian Tables 1 and 2 stay with their introductions and captions; Alarm interpretation and red-meat limitations readable; HMM heading has following prose. |
| 3 | HMM equation, worked example, Table 3 and caption; comparison introduction, Table 3a and caption; Scenario A heading, plot, MAP strip and caption paired. |
| 4 | Scenario A continuation and Scenario B plot, strip, legend, caption and interpretation; no orphaned heading. |
| 5 | Scenario C plot, strip and caption; loading-response delay and probe-error discussion; decision section and equation complete. |
| 6 | Action plot and Table 4 with captions; decision introduction and Table 5 paired; decision analysis flows naturally. |
| 7 | Decision discussion continuation, conclusion and all six references; bibliography fits above the footer with no spillover page. |
| 8 | Appendix A starts at the top of a fresh page; corrected title and all four baseline tables readable and complete; no stray heading or template text. |
| 9 | Appendix B starts on a fresh page; full expected-utility figure and caption together. |
| 10 | Appendix C starts on a fresh page; sensitivity introduction, Table 6 and caption together; closest-decision table and caption together. |
| 11 | Full sweep introduction, Table C2 and caption, then sweep figure and caption; all fit with a clear footer. |
| 12 | Appendix D introduction and Scenario A's complete 30-step table; step numbers and all probabilities readable; caption paired. |
| 13 | Scenario B's complete 30-step table, heading and caption together; no split rows or truncated values. |
| 14 | Scenario C's complete 30-step table, heading and caption together; no split rows or truncated values. |

## Remaining layout observations

- Short Appendices A and B leave space below their content on pages 8 and 9
  because each appendix starts on a fresh page. Compact Appendix D tables also
  leave space below the captions; each scenario table remains on one page.
- Page 10 leaves room at the bottom because the next sweep introduction and
  table are kept together on page 11. Page 11 is denser but remains readable.
- Page 4 retains space below Scenario B because the next scenario's heading,
  complete figure and caption are kept together on page 5.
- No detached captions, orphaned headings, clipped text, missing mathematical
  glyphs or overlapping content were observed.

## Verification

All four required commands passed: `python -m unittest discover -s tests`,
`python run_analysis.py`, `python build_report.py`, and
`python verify_submission.py --reproduce --run-tests`. The suite contains 46 tests and the audit checks
all 16 tables, including the original 12. Full numerical and PNG reproduction
also passed. Tests also pass without third-party site packages.

The protected functions and numerical result files are unchanged. Generated
tables are read from CSV/JSON outputs and checked against recomputed results.
Prose trims offset the comparison table and domain context; the main-body count
is 1,961 words (S1 189, S2 446, S3 648, S4 487, S5 191).
Additional PDF geometry checks confirmed 14 pages, 12 captioned table pairs and their
explicit lead-ins, six figure-caption pairs, fresh appendix starts and text
inside the page bounds. The other four tables are the uncaptioned baseline
model tables in Appendix A.

To recreate page PNGs for review, run:

```bash
pdftoppm -r 120 -png report/COMP6009_Part_B_Report.pdf /tmp/biogas-page
```
