"""Publication-quality charts from computed results, with no inference logic."""
from pathlib import Path

COLORS = {'Stable': '#176B65', 'Stressed': '#B97812', 'Critical': '#B4444A'}
TITLES = {'A':'Stable operation', 'B':'Deteriorating operation', 'C':'Noisy monitoring'}
ACTION_COLORS = ['#176B65', '#B97812', '#B4444A']


def most_probable_strip(rows):
    """Encode inferred labels in the same Stable/Stressed/Critical colour order."""
    states=list(COLORS)
    return [states.index(row['most_probable_state']) for row in rows]


def make_figures(payload, destination, extension=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    destination = Path(destination)
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False, 'axes.titleweight':'bold', 'savefig.facecolor':'white'})
    for scenario, rows in payload['scenarios'].items():
        times = [r['time'] for r in rows]
        fig, (ax, sensor_ax, state_ax) = plt.subplots(3,1,figsize=(8.0,4.05),sharex=True, layout='constrained', gridspec_kw={'height_ratios':[5,0.6,0.25],'hspace':0.05})
        for state,color in COLORS.items():
            ax.plot(times, [r['posterior'][state] for r in rows], label=f'Belief: {state}', color=color, linewidth=2, marker='o', markersize=2.5)
        ax.set(ylim=(0,1), ylabel='Filtered state probability', title=f'Scenario {scenario}: {TITLES[scenario]}')
        ax.grid(axis='y', alpha=0.2)
        handles=[]
        for line,(state,color) in zip(ax.lines,COLORS.items()):
            handles.extend([line,Patch(facecolor=color,label=f'Most probable: {state}')])
        fig.legend(handles=handles,ncol=3,loc='outside lower center',fontsize=8,frameon=False)
        sensor_colors={'Normal':'#176B65','Warning':'#B97812','Alarm':'#B4444A'}
        for r in rows:
            sensor_ax.text(r['time'],0.5,r['observation'][0],ha='center',va='center',fontsize=9,color=sensor_colors[r['observation']],fontweight='bold')
        sensor_ax.set(xlim=(0.4,30.6),ylim=(0,1),yticks=[])
        sensor_ax.set_ylabel('Obs.',rotation=0,ha='right',va='center',fontsize=8)
        sensor_ax.tick_params(axis='x',bottom=False,labelbottom=False)
        sensor_ax.spines['left'].set_visible(False)
        sensor_ax.spines['bottom'].set_visible(False)
        state_ax.imshow([most_probable_strip(rows)],cmap=ListedColormap(list(COLORS.values())),vmin=-0.5,vmax=2.5,
                        aspect='auto',interpolation='nearest',extent=(0.5,30.5,0,1))
        state_ax.set(xlabel='Time step (N = Normal, W = Warning, A = Alarm)',xlim=(0.4,30.6),ylim=(0,1),yticks=[],xticks=[1,5,10,15,20,25,30])
        state_ax.set_ylabel('MAP',rotation=0,ha='right',va='center',fontsize=8)
        state_ax.spines['left'].set_visible(False)
        state_ax.spines['bottom'].set_visible(False)
        fig.savefig(destination/f'scenario_{scenario}_beliefs.png',dpi=220,bbox_inches='tight')
        fig.savefig(destination/f'scenario_{scenario}_beliefs.pdf',bbox_inches='tight')
        plt.close(fig)
    actions=list(payload['baseline_model']['utility'])
    heatmap=[[actions.index(r['action']) for r in payload['scenarios'][s]] for s in ('A','B','C')]
    fig,ax=plt.subplots(figsize=(8,2.0))
    ax.imshow(heatmap,cmap=ListedColormap(ACTION_COLORS),vmin=-0.5,vmax=2.5,aspect='auto',interpolation='nearest',extent=(0.5,30.5,2.5,-0.5))
    for i,row in enumerate(heatmap):
        for j,v in enumerate(row):
            ax.text(j+1,i,['C','R','I'][v],ha='center',va='center',color='white',fontsize=8)
    ax.set(yticks=[0,1,2],yticklabels=['A: stable','B: deteriorating','C: noisy'],xticks=[1,5,10,15,20,25,30],xlabel='Time step',title='Recommended actions from expected utility')
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=c,label=l) for c,l in zip(ACTION_COLORS,['C: Continue','R: Reduce Feed','I: Intervene'])],ncol=3,loc='upper center',bbox_to_anchor=(0.5,-0.34),frameon=False,fontsize=9)
    fig.savefig(destination/'recommended_actions.png',dpi=220,bbox_inches='tight')
    fig.savefig(destination/'recommended_actions.pdf',bbox_inches='tight')
    plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(8,6.4),sharex=True)
    for ax,(scenario,rows) in zip(axes,payload['scenarios'].items()):
        for action,color in zip(actions,ACTION_COLORS):
            ax.plot([r['time'] for r in rows],[r['expected_utilities'][action] for r in rows],label=action,color=color,linewidth=1.8)
        ax.set(ylabel='Expected utility',title=f'Scenario {scenario}')
        ax.grid(alpha=0.2)
        ax.axhline(0,color='#666666',linewidth=0.6)
    axes[0].legend(ncol=3,frameon=False,fontsize=9)
    axes[-1].set(xlabel='Time step',xticks=[1,5,10,15,20,25,30])
    fig.tight_layout()
    fig.savefig(destination/'expected_utilities.png',dpi=220,bbox_inches='tight')
    fig.savefig(destination/'expected_utilities.pdf',bbox_inches='tight')
    plt.close(fig)
    if extension is not None:
        make_sweep_figure(extension['sweep_summary'], destination)


def make_sweep_figure(summary, destination):
    """Show how each separate assumption changes the 30 baseline decisions."""
    import matplotlib.pyplot as plt
    specifications=[('sensor_noise','Uniform sensor mixture (fraction)'),
                    ('persistence','Identity transition mixture (fraction)'),
                    ('critical_utility','Magnitude of Continue/Critical penalty')]
    ceiling=max(row['changed_actions'] for row in summary)+1
    fig,axes=plt.subplots(3,1,figsize=(8,6.8),layout='constrained')
    for ax,(family,label) in zip(axes,specifications):
        for scenario,color in zip(('A','B','C'),('#28658C','#A36217','#80508E')):
            rows=[r for r in summary if r['family']==family and r['scenario']==scenario]
            xs=[-r['parameter'] if family=='critical_utility' else r['parameter'] for r in rows]
            ax.plot(xs,[r['changed_actions'] for r in rows],marker='o',color=color,label=f'Scenario {scenario}')
        ax.set(xlabel=label,ylabel='Changed actions / 30',ylim=(-0.2,ceiling))
        from matplotlib.ticker import MaxNLocator
        ax.yaxis.set_major_locator(MaxNLocator(integer=True,nbins=5))
        ax.grid(alpha=0.2)
    axes[0].legend(ncol=3,frameon=False,fontsize=9)
    fig.savefig(destination/'parameter_sweeps.png',dpi=220,bbox_inches='tight')
    fig.savefig(destination/'parameter_sweeps.pdf',bbox_inches='tight')
    plt.close(fig)
