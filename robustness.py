"""Derived explanations and separate sensitivity sweeps; baseline is immutable."""
from collections import Counter
from copy import deepcopy
from math import fsum

from biogas import BASELINE, hmm_filter, recommend_action

SWEEP_PARAMETERS = {
    'sensor_noise': (0.0, 0.10, 0.25, 0.50),
    'persistence': (0.0, 0.25, 0.50, 0.75),
    'critical_utility': (-20, -25, -30, -35, -40, -50),
}


def pairwise_utility_threshold(belief, utility_table, action, state, competitor):
    """Vary one utility cell until two actions tie, holding the belief fixed.

    Return None if the varied state's probability is zero, because that cell
    then cannot affect either expected utility. A pairwise tie is a global
    decision boundary only if no third action has a higher expected utility.
    """
    _, expected = recommend_action(belief, utility_table)
    if action == competitor or action not in utility_table or competitor not in utility_table or state not in belief:
        raise ValueError('Choose two distinct valid actions and a valid state')
    if belief[state] == 0:
        return None
    other_contribution = fsum(belief[s]*utility_table[action][s] for s in belief if s != state)
    return (expected[competitor]-other_contribution)/belief[state]


def _variant(family, parameter):
    model = deepcopy(BASELINE)
    if family == 'sensor_noise':
        for row in model['sensor1'].values():
            for observation in row:
                row[observation] = (1-parameter)*row[observation] + parameter/3
    elif family == 'persistence':
        for state,row in model['transition'].items():
            for next_state in row:
                row[next_state] = (1-parameter)*row[next_state] + parameter*(state == next_state)
    else:
        model['utility']['Continue']['Critical'] = parameter
    return model


def _decision_record(scenario, row):
    ranked = sorted(row['expected_utilities'], key=row['expected_utilities'].get, reverse=True)
    best,runner_up = ranked[:2]
    best_value = row['expected_utilities'][best]
    runner_value = row['expected_utilities'][runner_up]
    return {'scenario':scenario, 'time':row['time'], 'observation':row['observation'],
            'action':best, 'best_utility':best_value, 'runner_up':runner_up,
            'runner_up_utility':runner_value, 'decision_margin':best_value-runner_value}


def build_extensions(sequences, baseline_rows):
    """Return the worked step, utility margins, fixed-belief threshold and sweeps."""
    first,second = baseline_rows['A'][:2]
    states=[]
    for state in BASELINE['prior']:
        contributions={f'from_{s.lower()}':first['posterior'][s]*BASELINE['transition'][s][state] for s in BASELINE['prior']}
        states.append({'state':state, 'previous_belief':first['posterior'][state],
                       **contributions, 'prediction':second['prediction'][state],
                       'likelihood':BASELINE['sensor1'][state][second['observation']],
                       'unnormalised':second['unnormalised'][state],
                       'posterior':second['posterior'][state]})
    worked={'scenario':'A','time':second['time'],'observation':second['observation'],
            'evidence_probability':second['evidence_probability'],'states':states}
    margins=[_decision_record(scenario,row) for scenario,rows in baseline_rows.items() for row in rows]
    closest=[min((r for r in margins if r['scenario']==scenario),key=lambda r:r['decision_margin']) for scenario in baseline_rows]
    b28=baseline_rows['B'][27]['posterior']
    threshold=pairwise_utility_threshold(b28,BASELINE['utility'],'Continue','Critical','Reduce Feed')
    tie_table=deepcopy(BASELINE['utility'])
    tie_table['Continue']['Critical']=threshold
    _,tie_utilities=recommend_action(b28,tie_table)
    switch={'scenario':'B','time':28,'varied_action':'Continue','varied_state':'Critical',
            'competitor':'Reduce Feed','threshold':threshold,'belief':dict(b28),
            'utilities_at_tie':tie_utilities,
            'third_action_dominates':tie_utilities['Intervene']>tie_utilities['Reduce Feed']}
    summary,details=[],[]
    for family,parameters in SWEEP_PARAMETERS.items():
        for parameter in parameters:
            model=_variant(family,parameter)
            for scenario,observations in sequences.items():
                rows=hmm_filter(observations,model['prior'],model['transition'],model['sensor1'])
                for row in rows:
                    row['action'],row['expected_utilities']=recommend_action(row['posterior'],model['utility'])
                    decision=_decision_record(scenario,row)
                    row['decision_margin']=decision['decision_margin']
                    details.append({'family':family,'parameter':parameter,'scenario':scenario,
                                    'time':row['time'],'observation':row['observation'],
                                    **{f'posterior_{s.lower()}':v for s,v in row['posterior'].items()},
                                    **{f'EU_{a.lower().replace(" ","_")}':v for a,v in row['expected_utilities'].items()},
                                    'recommended_action':row['action'],'decision_margin':row['decision_margin']})
                changed=[r['time'] for r,b in zip(rows,baseline_rows[scenario]) if r['action']!=b['action']]
                counts=Counter(r['action'] for r in rows)
                summary.append({'family':family,'parameter':parameter,'scenario':scenario,
                                'changed_actions':len(changed),'changed_times':';'.join(map(str,changed)),
                                **{a:counts[a] for a in BASELINE['utility']},
                                'action_changes':sum(rows[i]['action']!=rows[i-1]['action'] for i in range(1,len(rows))),
                                'minimum_margin':min(r['decision_margin'] for r in rows),
                                'peak_critical':max(r['posterior']['Critical'] for r in rows)})
    return {'worked_hmm_step':worked,'decision_margins':margins,'closest_decisions':closest,
            'switching_threshold':switch,'sweep_summary':summary,'sweep_details':details}
