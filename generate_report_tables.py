"""Refresh marked report tables from committed outputs without editing results."""
import csv
import json
from pathlib import Path

from report_contract import scenario_comparison_table, scenario_step_table


def markdown_table(rows):
    lines=['| '+' | '.join(rows[0])+' |','| '+' | '.join(['---']*len(rows[0]))+' |']
    return '\n'.join(lines+['| '+' | '.join(row)+' |' for row in rows[1:]])


def replace_region(text, name, content):
    start=f'<!-- generated:{name}:start -->'
    end=f'<!-- generated:{name}:end -->'
    region=f'{start}\n\n{content.strip()}\n\n{end}'
    if start not in text and end not in text:
        return text.rstrip()+'\n\n'+region+'\n'
    if text.count(start)!=1 or text.count(end)!=1 or text.index(start)>text.index(end):
        raise ValueError(f'Invalid generated region: {name}')
    return text[:text.index(start)]+region+text[text.index(end)+len(end):]


def update_generated_tables(root):
    root=Path(root)
    source=root/'report'/'COMP6009_Part_B_Report.md'
    original=source.read_text(encoding='utf-8')
    text=original
    if '<!-- generated:comparison:start -->' in text:
        payload=json.loads((root/'results'/'analysis.json').read_text(encoding='utf-8'))
        comparison=markdown_table(scenario_comparison_table(payload))
        comparison+='\n\n*Table 3a. Generated scenario comparison. N/W/A = Normal/Warning/Alarm; S/St/C = Stable/Stressed/Critical. Peak ties select the earliest step. Probabilities are rounded to six decimals.*'
        text=replace_region(text,'comparison',comparison)
    parts=['## Appendix D. Complete scenario results',
           'All probabilities are rounded to six decimal places for display. '
           'State labels and actions use the full-precision calculation; rounded probabilities may not sum exactly to one.']
    for index,scenario in enumerate(('A','B','C'),1):
        with (root/'results'/f'scenario_{scenario}_results.csv').open(newline='',encoding='utf-8') as stream:
            records=list(csv.DictReader(stream))
        if [int(r['time']) for r in records]!=list(range(1,31)):
            raise ValueError(f'Scenario {scenario}: expected all 30 consecutive steps')
        rows=[{'time':int(r['time']),'observation':r['observation'],
               'posterior':{s:float(r[f'posterior_{s.lower()}']) for s in ('Stable','Stressed','Critical')},
               'most_probable_state':r['most_probable_state'],'action':r['recommended_action']} for r in records]
        parts.extend([f'### Scenario {scenario}',markdown_table(scenario_step_table(rows)),
                      f'*Table D{index}. All 30 steps for scenario {scenario}, generated from its result CSV.*'])
    updated=replace_region(text,'appendix-d','\n\n'.join(parts))
    if updated!=original:
        source.write_text(updated,encoding='utf-8')
    return updated!=original


if __name__=='__main__':
    update_generated_tables(Path(__file__).resolve().parent)
