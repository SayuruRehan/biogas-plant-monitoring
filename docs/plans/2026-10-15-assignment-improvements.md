# Assignment improvements implementation plan

Goal: Complete the four approved improvements on `dev`, preserving the supplied
baseline models, every baseline posterior/action, and the 1,800-2,200-word report.

Specification: The assignment brief, existing REQUIREMENTS_CHECKLIST.md, and
the four improvements approved in the conversation on 15 October 2026.

Architecture: Keep `biogas.py` unchanged. Add derived explanations and separate
parameter sweeps in `robustness.py`, orchestrated by `run_analysis.py`. Add an
independently runnable `verify_submission.py` for dataset/output/report audits.
The Markdown remains the editable report source; rebuild its PDF locally.

Constraints: Work and commit on the existing `dev` branch. Push only `dev`;
never update or merge to `master`. Use only Sensor 1 in the HMM. Retain the
first-observation convention and all baseline outputs. No HMM library.

- [x] Add failing tests for a numerical second HMM step, expected-utility
  margins, analytical pairwise thresholds, and separate parameter sweeps.
- [x] Implement `build_extensions(sequences, baseline_rows)` and
  `pairwise_utility_threshold(belief, utility_table, action, state, competitor)`.
  Sweep sensor mixtures [0, .10, .25, .50], persistence mixtures
  [0, .25, .50, .75], and Continue/Critical utilities [-20,-25,-30,-35,-40,-50].
- [x] Export derived CSV/JSON results and a sweep comparison figure. Check
  every pre-existing baseline result against the saved initial snapshot.
- [x] Add failing tests for corrupted/missing output rows, modified inputs,
  and stale report tables. Implement a deterministic verification CLI with
  optional fresh-output reproduction and clear nonzero failure status.
- [x] Add the numerical example, close-decision interpretation, switching
  threshold, and sweep discussion to the report. Put full sweep details in
  an appendix. Verify all report tables against generated output.
- [x] Regenerate figures/PDF, review every page, run the whole test suite and
  verification CLI, and update README/walkthrough/coverage checklist.
- [x] Review the complete diff and prepare the verified dev-only delivery.

Delivery instruction: commit and push only `dev`, then confirm that the remote
`master` SHA still equals c5e19799708ddba7f1c299fab61c9d27458b4421.

Review focus: Wrong first-step transitions; mixing sensitivity into baseline;
pairwise ties dominated by a third action; stale narrative/table numbers;
cross-platform reproduction without access to files outside the repository.

Progress: All four improvements complete. All 27 tests and full fresh-output
reproduction pass. Twelve report tables match computed results; the main body
is 2,173 words. Every report page was visually reviewed. The baseline model,
input datasets and all original numerical result files remain byte-identical.
Independent review found no Critical/Important issues. Its minor surplus-CSV-cell
finding was reproduced with a failing test and fixed; the full suite is green.
Ruling: Use the newly cloned checkout directly on dev, as explicitly requested.
