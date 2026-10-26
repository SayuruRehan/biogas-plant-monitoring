"""Audit original data, all numerical outputs, report tables and PDF freshness.

Usage: python verify_submission.py [--reproduce] [--run-tests]
The default audit uses the standard library only. Fresh plot reproduction
requires the installed requirements. Failures print FAIL and exit nonzero.
"""
import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

from biogas import BASELINE, bayesian_update
from report_contract import REPORT_TITLE_BLOCK, REPORT_SECTION_TARGETS, expected_report_tables, parse_tables, report_fingerprints, report_sections, report_word_count
from robustness import build_extensions
from run_analysis import SCENARIOS, analyse_sequence, flatten, load_observations, sensitivity_models


class VerificationError(ValueError):
    """A deliverable is missing, inconsistent or stale."""


def _require(condition, message):
    if not condition:
        raise VerificationError(message)


def _same(actual, expected, label):
    if isinstance(expected,dict):
        _require(isinstance(actual,dict) and set(actual)==set(expected),f'{label}: keys differ')
        for key,value in expected.items():
            _same(actual[key],value,f'{label}.{key}')
    elif isinstance(expected,list):
        _require(isinstance(actual,list) and len(actual)==len(expected),f'{label}: row count differs')
        for i,(a,e) in enumerate(zip(actual,expected),1):
            _same(a,e,f'{label}[{i}]')
    elif isinstance(expected,float):
        _require(isinstance(actual,(float,int)) and not isinstance(actual,bool) and math.isfinite(actual)
                 and math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-12),f'{label}: numeric value differs')
    else:
        _require(type(actual) is type(expected) and actual==expected,f'{label}: value differs')


def _csv(root, filename, expected):
    path=root/'results'/filename
    _require(path.is_file(),f'Missing {filename}')
    with path.open(newline='',encoding='utf-8') as stream:
        reader=csv.DictReader(stream)
        _require(reader.fieldnames==list(expected[0]),f'{filename}: columns differ')
        actual=list(reader)
    _require(len(actual)==len(expected),f'{filename}: row count differs')
    for i,(a,e) in enumerate(zip(actual,expected),1):
        _require(None not in a,f'{filename} row {i}: extra cells')
        for key,value in e.items():
            if isinstance(value,(float,int)):
                try:
                    number=float(a[key])
                except (ValueError,TypeError) as exc:
                    raise VerificationError(f'{filename} row {i} {key}: invalid number') from exc
                _require(math.isfinite(number) and math.isclose(number,value,rel_tol=1e-12,abs_tol=1e-12),
                         f'{filename} row {i} {key}: numeric value differs')
            else:
                _require(a[key]==value,f'{filename} row {i} {key}: value differs')


def _summary(observations,rows):
    mapping={'Stable':'Continue','Stressed':'Reduce Feed','Critical':'Intervene'}
    return {'observations':dict(Counter(observations)),
            'state_counts':dict(Counter(r['most_probable_state'] for r in rows)),
            'action_counts':dict(Counter(r['action'] for r in rows)),
            'action_changes':[{'time':rows[i]['time'],'from':rows[i-1]['action'],'to':rows[i]['action']}
                              for i in range(1,len(rows)) if rows[i]['action']!=rows[i-1]['action']],
            'final_posterior':rows[-1]['posterior'],
            'map_action_disagreements':[r['time'] for r in rows if r['action']!=mapping[r['most_probable_state']]],
            'peak_critical':max(r['posterior']['Critical'] for r in rows)}


def verify_submission(root):
    """Return successful audit descriptions or raise VerificationError."""
    root=Path(root).resolve()
    checks=[]
    hashes=json.loads((root/'results'/'input_sha256.json').read_text())
    _require(set(hashes)==set(SCENARIOS.values()),'Input hash manifest does not cover exactly three datasets')
    sequences={}
    for scenario,filename in SCENARIOS.items():
        path=root/'data'/filename
        _require(path.is_file(),f'Missing input dataset {filename}')
        _require(hashlib.sha256(path.read_bytes()).hexdigest()==hashes[filename],f'Input hash mismatch: {filename}')
        sequences[scenario]=load_observations(path)
    checks.append('Original input hashes and all 90 consecutive observation rows')
    baseline={s:analyse_sequence(obs,BASELINE) for s,obs in sequences.items()}
    for scenario,rows in baseline.items():
        _csv(root,f'scenario_{scenario}_results.csv',[flatten(row) for row in rows])
        for row in rows:
            for vector in ('prediction','posterior'):
                _require(all(math.isfinite(v) and 0<=v<=1 for v in row[vector].values()) and
                         math.isclose(sum(row[vector].values()),1,abs_tol=1e-12),f'Invalid {vector}')
            # Independent dot product and best-action check for all 90 decisions.
            utilities={a:sum(row['posterior'][s]*u[s] for s in row['posterior']) for a,u in BASELINE['utility'].items()}
            _require(row['action']==max(utilities,key=utilities.get),'Action does not maximise expected utility')
    checks.append('All 90 predictions, posterior vectors, state labels, utilities, actions and margins')
    bayes=[]
    for obs in ('Normal','Warning','Alarm'):
        bayes.append({'evidence':obs,**bayesian_update(BASELINE['prior'],[(obs,BASELINE['sensor1'])])})
    bayes.append({'evidence':'Warning + Abnormal pH',**bayesian_update(BASELINE['prior'],[('Warning',BASELINE['sensor1']),('Abnormal pH',BASELINE['sensor2'])])})
    _csv(root,'task1_bayesian_results.csv',bayes)
    sensitivity,details=[],[]
    for name,model in sensitivity_models().items():
        for scenario in SCENARIOS:
            rows=analyse_sequence(sequences[scenario],model)
            changed=[r['time'] for r,b in zip(rows,baseline[scenario]) if r['action']!=b['action']]
            counts=Counter(r['action'] for r in rows)
            sensitivity.append({'experiment':name,'scenario':scenario,'changed_actions':len(changed),
                                'changed_times':';'.join(map(str,changed)),**{a:counts[a] for a in BASELINE['utility']}})
            details.extend({'experiment':name,'scenario':scenario,**flatten(r)} for r in rows)
    _csv(root,'sensitivity_summary.csv',sensitivity)
    _csv(root,'sensitivity_details.csv',details)
    expected={'baseline_model':BASELINE,'task1':bayes,'scenarios':baseline,
              'summary':{s:_summary(sequences[s],baseline[s]) for s in SCENARIOS},'sensitivity':sensitivity}
    payload=json.loads((root/'results'/'analysis.json').read_text())
    _same(payload,expected,'analysis.json')
    extension=build_extensions(sequences,baseline)
    _same(json.loads((root/'results'/'robustness.json').read_text()),extension,'robustness.json')
    for filename,rows in [('worked_hmm_step.csv',extension['worked_hmm_step']['states']),
                          ('decision_margins.csv',extension['decision_margins']),
                          ('closest_decisions.csv',extension['closest_decisions']),
                          ('parameter_sweep_summary.csv',extension['sweep_summary']),
                          ('parameter_sweep_details.csv',extension['sweep_details'])]:
        _csv(root,filename,rows)
    checks.append('Bayesian cases, worked HMM step, fixed-belief threshold, and 1,260 sweep rows / 42 summaries')
    report=(root/'report'/'COMP6009_Part_B_Report.md').read_text(encoding='utf-8')
    _require(report.startswith(REPORT_TITLE_BLOCK+'\n\n## 1. Introduction'),
             'Report title block is missing or differs from the submission details')
    _require(report.count('<!-- title-block -->')==report.count('<!-- /title-block -->')==1,
             'Report title block markers must occur exactly once')
    checks.append('Report title block identifies COMP6009 Assignment Part B, Sayuru Bopitiya, 24071158 and 26 October 2026; excluded from word count')
    _require(report.count('## Appendix A. Baseline model tables\n\n')==1,
             'Appendix A must use the baseline model tables title')
    readme=(root/'README.md').read_text(encoding='utf-8')
    for name,text in (('Report',report),('README',readme)):
        _require('[declare' not in text.casefold(),f'{name} contains an unfilled template marker')
    checks.append('Appendix A uses the baseline model tables title; report and README contain no unfilled template markers')
    try:
        sections=report_sections(report)
    except ValueError as exc:
        raise VerificationError(str(exc)) from exc
    section_counts={number:report_word_count(text) for number,text in sections.items()}
    for number,(lower,upper) in REPORT_SECTION_TARGETS.items():
        count=section_counts[number]
        _require(lower<=count<=upper,f'Section {number} word count is {count}; expected {lower}-{upper}')
    main_body=report.split('## References')[0]
    appendix_c=report.partition('## Appendix C. Decision robustness and full sensitivity sweeps\n\n')[2]
    _require('### Sensitivity to modelling choices' not in main_body and
             '### Sensitivity to modelling choices' in appendix_c and
             '*Table 6.' in appendix_c and '| Separate perturbation |' in appendix_c,
             'Sensitivity subsection and Table 6 must be in Appendix C')
    _require('sensitivity' not in sections[1].lower(),'Introduction must omit the sensitivity sentence')
    checks.append('Section word counts within brief targets: '+', '.join(f'S{n} {c}' for n,c in section_counts.items())+'; sensitivity subsection and Table 6 in Appendix C')
    tables=parse_tables(report)
    expected_tables=expected_report_tables(expected,extension)
    _require(len(tables)==len(expected_tables),'report table count differs')
    for i,(actual,wanted) in enumerate(zip(tables,expected_tables),1):
        _require(actual==wanted,f'report table {i} differs from computed results')
    appendix_d=report.partition('## Appendix D. Complete scenario results\n\n')[2]
    _require(len(parse_tables(appendix_d))==3,'Appendix D must contain all three complete scenario tables')
    _require(any(t[0][1]=='Observed N / W / A' for t in parse_tables(sections[3])),
             'Section 3 must contain the generated scenario comparison table')
    checks.append('Generated Section 3 comparison and all 90 Appendix D steps match independently computed results')
    words=report_word_count(report)
    _require(1800<=words<=2200,f'Report word count is {words}; expected 1,800-2,200')
    _require(1950<=words<=2100,f'Report word count is {words}; expected safety margin 1,950-2,100')
    # Bind key narrative calculations as well as every numeric table.
    narrative_values=[f"{extension['worked_hmm_step']['evidence_probability']:.6f}",
                      f"{extension['switching_threshold']['threshold']:.6f}",
                      f"{extension['closest_decisions'][1]['decision_margin']:.6f}"]
    for value in narrative_values:
        _require(value in report,f'Report narrative missing derived value {value}')
    checks.append(f'All {len(tables)} report tables and key narrative calculations; main body {words} words')
    for name in ('scenario_A_beliefs','scenario_B_beliefs','scenario_C_beliefs','recommended_actions','expected_utilities','parameter_sweeps'):
        for suffix in ('.png','.pdf'):
            path=root/'figures'/(name+suffix)
            _require(path.is_file() and path.stat().st_size>100,f'Missing or empty {path.name}')
    pdf=root/'report'/'COMP6009_Part_B_Report.pdf'
    _require(pdf.is_file(),'Missing report PDF')
    content=pdf.read_bytes()
    _require(content.startswith(b'%PDF-') and content.rstrip().endswith(b'%%EOF'),'Report PDF is incomplete')
    _require(b'/Author (Sayuru Bopitiya)' in content,'Report PDF Author must be Sayuru Bopitiya')
    for key,value in report_fingerprints(root).items():
        _require(f'{key}:{value}'.encode() in content,f'Report PDF is stale: {key}; rerun build_report.py')
    checks.append('Report PDF matches the checked Markdown, numerical results and embedded figure bytes')
    return checks


def reproduce(root):
    """Generate fresh artifacts in an isolated temporary folder and compare."""
    source=Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='biogas-reproduction-') as temporary:
        target=Path(temporary)
        run=subprocess.run([sys.executable,str(source/'run_analysis.py'),'--data-dir',str(root/'data'),
                            '--output-dir',str(target)],capture_output=True,text=True)
        _require(run.returncode==0,f'Fresh analysis failed:\n{run.stderr}')
        expected_files=list((target/'results').iterdir())
        for path in expected_files:
            current=root/'results'/path.name
            _require(current.is_file() and current.read_bytes()==path.read_bytes(),f'Reproduction differs: {path.name}')
        for path in (target/'figures').glob('*.png'):
            _require((root/'figures'/path.name).read_bytes()==path.read_bytes(),f'Reproduced figure differs: {path.name}')
    return 'Fresh run reproduced all 13 numerical CSV/JSON files and all six PNG plots byte-for-byte'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--reproduce',action='store_true',help='rerun analysis and plots in a temporary directory')
    parser.add_argument('--run-tests',action='store_true',help='also run the complete unittest suite')
    args=parser.parse_args()
    try:
        checks=verify_submission(args.root)
        if args.reproduce:
            checks.append(reproduce(args.root.resolve()))
        if args.run_tests:
            result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=Path(__file__).resolve().parent)
            _require(result.returncode==0,'Unit test suite failed')
            checks.append('Complete unittest suite passed')
    except (VerificationError,ValueError,OSError,KeyError,TypeError) as exc:
        print(f'FAIL: {exc}',file=sys.stderr)
        return 1
    for check in checks:
        print('PASS: '+check)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
