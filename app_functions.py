#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  1 18:04:21 2021

App functions for AP explorer

@author: tbury
"""


import numpy as np
import pandas as pd


import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


import myokit as myokit



cols = px.colors.qualitative.Plotly


def sim_model(s, params={}, bcl=1000, num_beats=4):
    '''
    Simulate Torord model of CM in endocardium.

    Parameters
    ----------
    
    s : simulation class (myokit.Simulation)
    params : dict
        Dictionary of user-defined model parameter values. Those that are not
        specified are set to default.
    bcl : float
        basic cycle length
    num_beats : int
        number of beats to simulate (after pre-pacing)
        

    Returns
    -------
    df : pd.DataFrame
        Dataframe of variables at each time value.

    '''
    
    # Set cell type (0: endo;  1: epi;  2: mid)
    params['environment.celltype'] = 0  
    
    # Extracellular cell concentrations used to simulate EADs (Tomek et al.)
    params['extracellular.nao'] = 137
    params['extracellular.clo'] = 148
    params['extracellular.cao'] = 2
    
    # Assign parameters to simulation object
    for key in params.keys():
        s.set_constant(key,params[key])

    # Set pacing protocol and assign to simulation object
    p = myokit.pacing.blocktrain(bcl, duration=0.5, offset=20) 
    s.set_protocol(p)   
    
    
    # Pre-pacing simulation
    num_beats_pre = 50
    print('Begin prepacing')
    s.pre(num_beats_pre*bcl)
    
    # Pacing simulation
    print('Begin recorded simulation')
    d = s.run(bcl*num_beats)
    
    # Put desired data into dataframe
    df = pd.DataFrame(
        {'time':np.array(d['environment.time']),
         'voltage':np.array(d['membrane.v']),
         'ina':np.array(d['INa.INa']),
         'inaca':np.array(d['INaCa.INaCa_i']),
         'ical':np.array(d['ICaL.ICaL']),
         'ikr':np.array(d['IKr.IKr']),
         'iks':np.array(d['IKs.IKs']),
        }
        )

    # Reset simulation
    s.reset()

    return df



def generate_fig(df_base, df_mod):
    '''
    Generate figure of currents vs time

    Parameters
    ----------
    df_base : pd.DataFrame
        simulation data of model at baseline parameters
    df_mod : pd.DataFrame
        simulation data of model at modified parameters 

    Returns
    -------
    fig

    '''
        
    line_width = 1
    
    fig = make_subplots(rows=5, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.02
                        )
    

    ## Voltage plot
    # baseline
    fig.add_trace(
        go.Scatter(
            x=df_base['time'],
            y=df_base['voltage'],
            name='baseline',
            legendgroup='baseline', # this allows traces to be connected by legend
            showlegend=True,
            mode='lines',
            line={'color':cols[0], 
                  'width':line_width,
                  },
            ),
        row=1,col=1,
        )
    
    # modified
    if not df_mod.empty:
        fig.add_trace(
            go.Scatter(
                x=df_mod['time'],
                y=df_mod['voltage'],
                name='modified',
                legendgroup='modified',
                showlegend=True,
                mode='lines',
                line={'color':cols[1], 
                      'width':line_width,
                      },
                ),
            row=1,col=1,
            )
    

    ## INa plot
    # baseline
    fig.add_trace(
        go.Scatter(
            x=df_base['time'],
            y=df_base['ina'],
            name='baseline',
            legendgroup='baseline', # this allows traces to be connected by legend
            showlegend=False,
            mode='lines',
            line={'color':cols[0], 
                  'width':line_width,
                  },
            ),
        row=2,col=1,
        )
    
    # modified
    if not df_mod.empty:
        fig.add_trace(
            go.Scatter(
                x=df_mod['time'],
                y=df_mod['ina'],
                name='modified',
                legendgroup='modified',
                showlegend=False,
                mode='lines',
                line={'color':cols[1], 
                      'width':line_width,
                      },
                ),
            row=2,col=1,
            )
    
    ## ICaL plot
    # baseline
    fig.add_trace(
        go.Scatter(
            x=df_base['time'],
            y=df_base['ical'],
            name='baseline',
            legendgroup='baseline', # this allows traces to be connected by legend
            showlegend=False,
            mode='lines',
            line={'color':cols[0], 
                  'width':line_width,
                  },
            ),
        row=3,col=1,
        )
    
    # modified
    if not df_mod.empty:
        fig.add_trace(
            go.Scatter(
                x=df_mod['time'],
                y=df_mod['ical'],
                name='modified',
                legendgroup='modified',
                showlegend=False,
                mode='lines',
                line={'color':cols[1], 
                      'width':line_width,
                      },
                ),
            row=3,col=1,
            )
    
    ## Ikr plot
    # baseline
    fig.add_trace(
        go.Scatter(
            x=df_base['time'],
            y=df_base['ikr'],
            name='baseline',
            legendgroup='baseline', # this allows traces to be connected by legend
            showlegend=False,
            mode='lines',
            line={'color':cols[0], 
                  'width':line_width,
                  },
            ),
        row=4,col=1,
        )
    
    # modified
    if not df_mod.empty:
        fig.add_trace(
            go.Scatter(
                x=df_mod['time'],
                y=df_mod['ikr'],
                name='modified',
                legendgroup='modified',
                showlegend=False,
                mode='lines',
                line={'color':cols[1], 
                      'width':line_width,
                      },
                ),
            row=4,col=1,
            )
    
    ## INaCa plot
    # baseline
    fig.add_trace(
        go.Scatter(
            x=df_base['time'],
            y=df_base['inaca'],
            name='baseline',
            legendgroup='baseline', # this allows traces to be connected by legend
            showlegend=False,
            mode='lines',
            line={'color':cols[0], 
                  'width':line_width,
                  },
            ),
        row=5,col=1,
        )
    
    # modified
    if not df_mod.empty:
        fig.add_trace(
            go.Scatter(
                x=df_mod['time'],
                y=df_mod['inaca'],
                name='modified',
                legendgroup='modified',
                showlegend=False,
                mode='lines',
                line={'color':cols[1], 
                      'width':line_width,
                      },
                ),
            row=5,col=1,
            )    
    
    fig.update_yaxes(title='Voltage (mV)',
                      row=1,
                      )
   
    fig.update_yaxes(title='INa (pA/pF)',
                      row=2,
                      )
        
    fig.update_yaxes(title='ICaL (pA/pF)',
                      row=3,
                      )
    
    fig.update_yaxes(title='IKr (pA/pF)',
                      row=4,
                      )
    
    fig.update_yaxes(title='INaCa (pA/pF)',
                      row=5,
                      )

    
    
    # fig.update_xaxes(range=[-10,500],
    #                   )
    
    fig.update_xaxes(title='Time (ms)',
                      row=5,
                      )
    
    fig.update_layout(
                      # width=500,
                      height=800,
                      margin={'l':20,'r':20,'t':20,'b':20},
                      # legend={'yanchor':'top',
                      #         'xanchor':'right',
                      #         'x':0.99,
                      #         'y':0.99,
                      #         },
                      )
    
    return fig



# Test functions
if __name__=='__main__':
    
    x=3
    print(x)
    
    
    
    
    
    





