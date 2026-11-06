"""COMP6009 Assignment Part B - run Tasks 1 to 3 and the sensitivity experiments.

Usage:  python main.py
Reads the three scenario CSV files in data/ and writes every numerical result
to results/ and every figure to results/figures/.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from src.biogas_model import BASELINE, analyse_sequence, bayesian_update
from src.report_figures import make_figures
from src.sensitivity import build_extensions, sensitivity_models

SCENARIOS = {'A': 'scenario_A_stable.csv', 'B': 'scenario_B_deteriorating.csv', 'C': 'scenario_C_noisy.csv'}


def load_observations(path):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ['time', 'observation']:
            raise ValueError(f'{path.name}: expected time,observation columns')
        rows = list(reader)
    if len(rows) != 30:
        raise ValueError(f'{path.name}: assignment expects exactly 30 observations')
    if [int(r['time']) for r in rows] != list(range(1, 31)):
        raise ValueError(f'{path.name}: time must be consecutive from 1 to 30')
    return [r['observation'].strip() for r in rows]


def write_csv(path, rows):
    if not rows:
        raise ValueError('Cannot write an empty result table')
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def flatten(row):
    result = {'time': row['time'], 'observation': row['observation']}
    for key in ('prediction', 'unnormalised', 'posterior'):
        result.update({f'{key}_{s.lower()}': v for s, v in row[key].items()})
    result['evidence_probability'] = row['evidence_probability']
    result['most_probable_state'] = row['most_probable_state']
    result.update({f'EU_{a.lower().replace(" ", "_")}': v for a, v in row['expected_utilities'].items()})
    result['recommended_action'] = row['action']
    result['decision_margin'] = row['decision_margin']
    return result


def main(data_dir=None, output_dir=None):
    root = Path(__file__).resolve().parent
    data_dir = Path(data_dir) if data_dir else root/'data'
    results = Path(output_dir) if output_dir else root/'results'
    figures = results/'figures'
    results.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    bayes_rows = []
    for observation in ('Normal', 'Warning', 'Alarm'):
        posterior = bayesian_update(BASELINE['prior'], [(observation, BASELINE['sensor1'])])
        bayes_rows.append({'evidence': observation, **posterior})
    posterior = bayesian_update(BASELINE['prior'], [('Warning', BASELINE['sensor1']), ('Abnormal pH', BASELINE['sensor2'])])
    bayes_rows.append({'evidence': 'Warning + Abnormal pH', **posterior})
    write_csv(results/'task1_bayesian_results.csv', bayes_rows)
    all_rows, sequences, summary = {}, {}, {}
    for scenario, filename in SCENARIOS.items():
        sequences[scenario] = load_observations(data_dir/filename)
        rows = analyse_sequence(sequences[scenario], BASELINE)
        all_rows[scenario] = rows
        write_csv(results/f'scenario_{scenario}_results.csv', [flatten(r) for r in rows])
        summary[scenario] = {
            'observations': dict(Counter(sequences[scenario])),
            'state_counts': dict(Counter(r['most_probable_state'] for r in rows)),
            'action_counts': dict(Counter(r['action'] for r in rows)),
            'action_changes': [{'time': rows[i]['time'], 'from': rows[i-1]['action'], 'to': rows[i]['action']} for i in range(1,len(rows)) if rows[i]['action'] != rows[i-1]['action']],
            'final_posterior': rows[-1]['posterior'],
            'map_action_disagreements': [r['time'] for r in rows if r['action'] != {'Stable':'Continue','Stressed':'Reduce Feed','Critical':'Intervene'}[r['most_probable_state']]],
            'peak_critical': max(r['posterior']['Critical'] for r in rows),
        }
    sensitivity, sensitivity_details = [], []
    for name, model in sensitivity_models().items():
        for scenario in SCENARIOS:
            rows = analyse_sequence(sequences[scenario], model)
            changed = [r['time'] for r,b in zip(rows,all_rows[scenario]) if r['action'] != b['action']]
            sensitivity.append({'experiment': name, 'scenario': scenario, 'changed_actions': len(changed), 'changed_times': ';'.join(map(str,changed)), **dict(Counter(r['action'] for r in rows))})
            for r in rows:
                sensitivity_details.append({'experiment': name, 'scenario': scenario, **flatten(r)})
    # Ensure fixed CSV columns even when a variant never recommends an action.
    for row in sensitivity:
        for action in BASELINE['utility']:
            row.setdefault(action, 0)
    sensitivity = [{k:r[k] for k in ('experiment','scenario','changed_actions','changed_times',*BASELINE['utility'])} for r in sensitivity]
    write_csv(results/'sensitivity_summary.csv', sensitivity)
    write_csv(results/'sensitivity_details.csv', sensitivity_details)
    payload = {'baseline_model': BASELINE, 'task1': bayes_rows, 'scenarios': all_rows, 'summary': summary, 'sensitivity': sensitivity}
    (results/'analysis.json').write_text(json.dumps(payload, indent=2)+'\n', encoding='utf-8')
    # These additions never feed back into the baseline filtering or choices.
    extension = build_extensions(sequences, all_rows)
    for name, rows in (
        ('worked_hmm_step', extension['worked_hmm_step']['states']),
        ('decision_margins', extension['decision_margins']),
        ('closest_decisions', extension['closest_decisions']),
        ('parameter_sweep_summary', extension['sweep_summary']),
        ('parameter_sweep_details', extension['sweep_details']),
    ):
        write_csv(results/f'{name}.csv', rows)
    (results/'robustness.json').write_text(json.dumps(extension, indent=2)+'\n', encoding='utf-8')
    make_figures(payload, figures, extension)
    print('Bayesian results:')
    for row in bayes_rows:
        print(row)
    print('Scenario summaries:')
    print(json.dumps(summary, indent=2))
    print('Sensitivity:', json.dumps(sensitivity, indent=2))
    return payload


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, help='folder containing the three supplied CSV files')
    parser.add_argument('--output-dir', type=Path, help='destination folder for results (default: results/)')
    args = parser.parse_args()
    main(args.data_dir, args.output_dir)
