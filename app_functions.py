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

from dash import Dash, dcc, html


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



def make_simulation_fig(df_sim, var_plot):
    '''
    Make figure showing variable vs time

    Parameters
    ----------
    df_sim : pd.DataFrame
        simulation data of model
    var_plot : variable to plot

    Returns
    -------
    fig

    '''
        
    line_width = 1
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=df_sim['time'],
            y=df_sim[var_plot],
            showlegend=False,
            mode='lines',
            line={'color':cols[0], 
                  'width':line_width,
                  },
            ),
        )

    fig.update_xaxes(title='Time (ms)')
    fig.update_yaxes(title=var_plot)
    
    fig.update_layout(
                      height=600,
                      margin={'l':20,'r':20,'t':20,'b':20},
                      )
    
    return fig
 

def make_fig_tabs(df_sim):
  
    cols = df_sim.columns
    
    list_tabs = []
    
    for var in cols:
        
        if var=='time':
            continue
    
    
        tab = dcc.Tab(
            label=var, 
            children=[dcc.Graph(
                    figure=make_simulation_fig(df_sim,var))],
                )
        
        
        list_tabs.append(tab)

    fig_tabs = dcc.Tabs(list_tabs)
    
    return fig_tabs





# Test functions
if __name__=='__main__':
    
    x=3
    print(x)
    
    
    
    
    
    





