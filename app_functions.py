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


def sim_model(
    s, plot_vars, params={}, bcl=1000, total_beats=100, beats_keep=4, cell_type=0
):
    """
    Simulate Torord model

    Parameters
    ----------

    s : simulation class (myokit.Simulation)
    params : dict
        Dictionary of user-defined model parameter values. Those that are not
        specified are set to default.
    bcl : float
        basic cycle length
    total_beats : int
        total number of beats to simulate
    beats_kepp: int
        number of beats to display in figure (from the end of the simulation)
    cell_type: int
        cell type (0: endo;  1: epi;  2: mid)

    Returns
    -------
    df : pd.DataFrame
        Dataframe of variables at each time value.

    """

    # Get default state of model
    default_state = s.default_state()

    params["environment.celltype"] = cell_type

    # Assign parameters to simulation object
    for key in params.keys():
        s.set_constant(key, params[key])

    # Set pacing protocol and assign to simulation object
    p = myokit.pacing.blocktrain(bcl, duration=0.5, offset=20)
    s.set_protocol(p)

    # Pre-pacing simulation
    num_beats_pre = max(total_beats - beats_keep, 0)
    print("Begin prepacing")
    s.pre(num_beats_pre * bcl)

    # Pacing simulation
    print("Begin recorded simulation")
    d = s.run(bcl * beats_keep)

    # Collect data specified in plot_vars
    data_dict = {key: d[key] for key in plot_vars}
    data_dict["time"] = d["environment.time"]
    df = pd.DataFrame(data_dict)

    # Reset simulation (don't use s.reset as this only goes to end of pre-pacing)
    s.set_state(default_state)
    s.set_time(0)

    return df


def make_simulation_fig(df_sim, plot_var):
    """
    Make figure showing variable vs time
    If plot_var is not in df_sim, output empty graph

    Parameters
    ----------
    df_sim : pd.DataFrame
        simulation data of model
    var_plot : variable to plot

    Returns
    -------
    fig

    """

    line_width = 1

    fig = go.Figure()

    if plot_var in df_sim.columns:
        fig.add_trace(
            go.Scatter(
                x=df_sim["time"],
                y=df_sim[plot_var],
                showlegend=False,
                mode="lines",
                line={
                    "color": cols[0],
                    "width": line_width,
                },
            ),
        )

    fig.update_xaxes(title="Time (ms)")
    fig.update_yaxes(title=plot_var)

    fig.update_layout(
        height=600,
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
    )

    return fig


# Test functions
if __name__ == "__main__":
    x = 3
    print(x)
