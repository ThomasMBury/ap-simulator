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
    s,
    plot_vars,
    params={},
    bcl=1000,
    total_beats=100,
    beats_keep=4,
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


def sim_s1s2_restitution(
    s,
    params={},
    s1_interval=1000,
    s1_nbeats=10,
    s2_intervals="300:500:20, 500:1000:50",
):
    """
    Simulate Torord model usign S1S2 stimulation protocol for a range of S2 values
    Return time series of final S1 stimulation followed by single S2 stimulation
    Return data on APD and CaT amplitude as a function of S2 interval

    Parameters
    ----------

    s : simulation class (myokit.Simulation)
    params : dict
        Dictionary of user-defined model parameter values. Those that are not
        specified are set to default.
    s1_interval : int
    s1_nbeats : int
        number of s1 beats (prepacing)
    s2_intervals: str
        String input by the user that provides s2 values

    Returns
    -------
    df_ts : pd.DataFrame
        time series
    df_restitution: pd.DataFrame
        apd, di and cat_amplitude as a function of S1

    """

    # Unpack S2 values
    list_s2_intervals = s2_input_to_list(s2_intervals)

    # Get default state of model
    default_state = s.default_state()

    # Assign parameters to simulation object
    for key in params.keys():
        s.set_constant(key, params[key])

    # Pre-pacing with S1 interval (only needs to be done once)
    p = myokit.pacing.blocktrain(s1_interval, duration=0.5, offset=0)
    s.set_protocol(p)
    s.pre(s1_nbeats * s1_interval)

    list_df = []
    list_di_vals = []
    list_apd_vals = []
    list_cat_amplitude_vals = []

    for s2_interval in list_s2_intervals:
        # Set pacing protocol
        p = myokit.Protocol()
        # Single S1 stimulus
        p.schedule(level=1.0, start=0, duration=0.5)
        # Single S2 stimulus
        p.schedule(level=1.0, start=s2_interval, duration=0.5)

        # Update protoocl
        s.set_protocol(p)

        # Pacing simulation
        d = s.run(2 * s1_interval)

        # Collect data
        data_dict = {}
        data_dict["membrane.v"] = d["membrane.v"]
        data_dict["time"] = d["environment.time"]
        data_dict["intracellular_ions.cai"] = d["intracellular_ions.cai"]
        df = pd.DataFrame(data_dict)
        df["s2_interval"] = s2_interval
        list_df.append(df)

        # Compute DI and APD from S2
        voltage_vals = d["membrane.v"]
        time_vals = d["environment.time"]
        thresh = -80  # mV
        crossings_zero_voltage = find_crossings(voltage_vals, 0)
        crossings_thresh = find_crossings(voltage_vals, thresh)

        # Must be 4 crossings at zero voltage to determine DI and APD
        if (len(crossings_zero_voltage) == 4) & (len(crossings_thresh) == 4):
            # Get DI and APD info
            di_start = crossings_thresh[1]
            di_end = crossings_thresh[2]
            ap_end = crossings_thresh[3]
            di = time_vals[di_end] - time_vals[di_start]
            apd = time_vals[ap_end] - time_vals[di_end]

        else:
            di = np.nan
            apd = np.nan

        list_di_vals.append(di)
        list_apd_vals.append(apd)

        # Get calcium transient amplitude (the one after S2)
        local_maxima = find_local_maxima(d["intracellular_ions.cai"])
        # Require at least two peaks
        if len(local_maxima) >= 2:
            cat_amplitude = local_maxima[1]
        else:
            cat_amplitude = np.nan

        list_cat_amplitude_vals.append(cat_amplitude)

        # Reset simulation to pre-paced state
        s.reset()

    df_restitution = pd.DataFrame(
        {
            "s2_interval": list_s2_intervals,
            "di": list_di_vals,
            "apd": list_apd_vals,
            "cat_amplitude": list_cat_amplitude_vals,
        }
    )

    df_ts = pd.concat(list_df)

    # Reset simulation completely (including prepacing)
    s.set_state(default_state)
    s.set_time(0)

    return df_ts, df_restitution


def find_crossings(arr, value):
    crossings = []
    for i in range(len(arr) - 1):
        if (arr[i] < value and arr[i + 1] >= value) or (
            arr[i] > value and arr[i + 1] <= value
        ):
            crossings.append(i)
    return crossings


def find_local_maxima(arr):
    local_maxima = []
    n = len(arr)

    # Check for edge cases where array length is less than 3
    if n < 3:
        return local_maxima

    for i in range(1, n - 1):
        if arr[i] > arr[i - 1] and arr[i] > arr[i + 1]:
            local_maxima.append(arr[i])

    return local_maxima


def make_s1s2_fig(df_ts, plot_var):
    line_width = 1

    fig = px.line(df_ts, x="time", y=plot_var, color="s2_interval")

    fig.update_xaxes(title="Time (ms)")

    fig.update_traces(line={"width": line_width})

    fig.update_layout(
        height=400,
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
    )

    return fig


def make_restitution_fig(df_restitution, plot_var):
    line_width = 1

    fig = go.Figure()

    if plot_var == "membrane.v":
        y_var = "apd"
        y_axes_title = "APD90 (ms)"
    elif plot_var == "intracellular_ions.cai":
        y_var = "cat_amplitude"
        y_axes_title = "CaT amplitude"

    fig.add_trace(
        go.Scatter(
            x=df_restitution["di"],
            y=df_restitution[y_var],
            # showlegend=False,
            mode="lines+markers",
            line={
                "color": cols[0],
                "width": line_width,
            },
        ),
    )

    fig.update_xaxes(title="DI (ms)")
    fig.update_yaxes(title=y_axes_title)

    fig.update_layout(
        height=400,
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
    )

    return fig


def s2_input_to_list(s2_intervals):
    """
    Convert user input for s2 values to list of integers

    Args:
        s2_intervals: str
            String input by the user.
            Can be a comma seperated list of integers
            or of the form min:max:inc
    Returns
    -------
    list(int)
        List of s2 intervals
    """

    try:
        # Remove any whitepsace
        s2_intervals = s2_intervals.replace(" ", "")

        # Separate arguments
        list_entry = s2_intervals.split(",")

        list_s2_intervals = []
        for entry in list_entry:
            if entry.isnumeric():
                list_s2_intervals.append(int(entry))

            else:
                # Unpack range of values
                low, high, inc = [int(s) for s in entry.split(":")]
                for s2 in np.arange(low, high, inc):
                    list_s2_intervals.append(s2)

    except:
        print("invalid input")
        return []

    return list_s2_intervals


# Test functions
if __name__ == "__main__":
    x = 3
    print(x)
