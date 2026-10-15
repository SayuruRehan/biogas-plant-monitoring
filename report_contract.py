"""Shared, standard-library-only contract for report numbers and provenance."""
import hashlib
import re


def report_word_count(text):
    body=text.split('## References')[0]
    lines=[line for line in body.splitlines() if line and not line.startswith(('![','*Table','*Figure','$$'))]
    return len(re.findall(r"\b[\w]+(?:[-'][\w]+)*\b",'\n'.join(lines)))


def report_fingerprints(root):
    source=root/'report'/'COMP6009_Part_B_Report.md'
    numeric=b''.join((root/'results'/name).read_bytes() for name in ('analysis.json','robustness.json'))
    figures=b''
    for name in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',source.read_text(encoding='utf-8')):
        path=(source.parent/name).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError('Report images must remain inside the assignment directory')
        figures+=name.encode()+b'\0'+path.read_bytes()
    return {'source-sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'results-sha256':hashlib.sha256(numeric).hexdigest(),
            'figures-sha256':hashlib.sha256(figures).hexdigest()}


def parse_tables(text):
    tables=[]
    for block in text.split('\n\n'):
        if block.startswith('|'):
            tables.append([[cell.strip() for cell in line.strip('|').split('|')]
                           for line in block.splitlines() if not re.match(r'^\|\s*:?-',line)])
    return tables


def expected_report_tables(payload, extension):
    """Construct every displayed table from checked full-precision results."""
    model=payload['baseline_model']
    states=list(model['prior'])
    fmt=lambda value:f'{value:.6f}'
    tables=[]
    tables.append([['Evidence','Stable','Stressed','Critical']]+[
        [r['evidence']]+[fmt(r[s]) for s in states] for r in payload['task1']])
    tables.append([['State','Prior × Warning likelihood × Abnormal pH likelihood','Weight']]+[
        [s,f"{model['prior'][s]:.2f} × {model['sensor1'][s]['Warning']:.2f} × {model['sensor2'][s]['Abnormal pH']:.2f}",
         f"{model['prior'][s]*model['sensor1'][s]['Warning']*model['sensor2'][s]['Abnormal pH']:.5f}"] for s in states])
    tables.append([['State','Previous','Prediction','Likelihood','Weight','Posterior']]+[
        [r['state']]+[fmt(r[k]) for k in ('previous_belief','prediction','likelihood','unnormalised','posterior')]
        for r in extension['worked_hmm_step']['states']])
    tables.append([['Scenario','Continue','Reduce Feed','Intervene','Action changes']]+[
        [s]+[str(payload['summary'][s]['action_counts'].get(a,0)) for a in model['utility']]
        +[str(len(payload['summary'][s]['action_changes']))] for s in payload['scenarios']])
    selected=[]
    for scenario,t in [('A',20),('B',15),('B',22)]:
        row=payload['scenarios'][scenario][t-1]
        selected.append([f'{scenario}, t={t}',' / '.join(fmt(row['posterior'][s]).removeprefix('0') for s in states)]
                        +[fmt(row['expected_utilities'][a]) for a in model['utility']]+[row['action']])
    tables.append([['Point','Belief: Stable / Stressed / Critical','EU Continue','EU Reduce','EU Intervene','Choice']]+selected)
    sensitivity=[]
    labels=['25% uniform sensor mixture','50% identity transition mixture','Continue/Critical utility -40']
    for i,label in enumerate(labels):
        sensitivity.append([label]+[str(r['changed_actions']) for r in payload['sensitivity'][3*i:3*i+3]])
    tables.append([['Separate perturbation','Changed actions: A','B','C']]+sensitivity)
    tables.append([['True state','Prior','Sensor 1: Normal','Warning','Alarm']]+[
        [s,f"{model['prior'][s]:.2f}"]+[f"{model['sensor1'][s][o]:.2f}" for o in ('Normal','Warning','Alarm')] for s in states])
    tables.append([['True state','Sensor 2: Normal pH','Abnormal pH']]+[
        [s]+[f"{model['sensor2'][s][o]:.2f}" for o in ('Normal pH','Abnormal pH')] for s in states])
    tables.append([['Current → Next','Stable','Stressed','Critical']]+[
        [s]+[f"{model['transition'][s][x]:.2f}" for x in states] for s in states])
    tables.append([['Action','Stable','Stressed','Critical']]+[
        [a]+[f'{row[s]:+d}' for s in states] for a,row in model['utility'].items()])
    tables.append([['Scenario / step','Choice','Runner-up','EU choice','EU runner-up','Margin']]+[
        [f"{r['scenario']}, t={r['time']}",r['action'],r['runner_up'],fmt(r['best_utility']),fmt(r['runner_up_utility']),fmt(r['decision_margin'])]
        for r in extension['closest_decisions']])
    sweep=[]
    labels={'sensor_noise':'Sensor noise','persistence':'Persistence','critical_utility':'Critical utility'}
    seen=set()
    for row in extension['sweep_summary']:
        key=(row['family'],row['parameter'])
        if key in seen:
            continue
        seen.add(key)
        setting=str(row['parameter']) if row['family']=='critical_utility' else f"{row['parameter']:.2f}"
        matches=[r for r in extension['sweep_summary'] if (r['family'],r['parameter'])==key]
        sweep.append([labels[row['family']],setting]+[str(r['changed_actions']) for r in matches])
    tables.append([['Family','Setting','Changed actions: A','B','C']]+sweep)
    return tables
