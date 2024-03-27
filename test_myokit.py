#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 17 17:34:58 2023

@author: tbury
"""


import numpy as np
import pandas as pd


import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import myokit as myokit


# Test myokit functions


def sim_model(
    s,
    plot_vars,
    params={},
    bcl=1000,
    total_beats=100,
    beats_keep=4,
):
    """
    Simulate Torord model with S1-S2 stimulation protocol

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

    Returns
    -------
    df : pd.DataFrame
        Dataframe of variables at each time value.

    """

    # Get default state of model
    default_state = s.default_state()

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


# Load in model from mmt file

filepath_mmt = "mmt_files/torord-2019.mmt"
m = myokit.load_model(filepath_mmt)
# Create simulation object with model
s = myokit.Simulation(m)
plot_vars_def = [
    "membrane.v",
    "INa.INa",
    "INaCa.INaCa_i",
    "ICaL.ICaL",
    "IKr.IKr",
    "IKs.IKs",
]

df = sim_model(s, plot_vars_def)
print(df.head())
