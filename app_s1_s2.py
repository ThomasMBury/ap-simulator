#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 27 Feb, 2024

Dash app to run simulation of Torod model in myokit
- S1S2 stimulation protocol

@author: tbury
"""

import os
import numpy as np
import pandas as pd

from dash import Dash, html, dcc, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import myokit as myokit

import app_functions as funs


# Determine if running app locally or on cloud
fileroot_local = "/Users/tbury/Google Drive/research/postdoc_23/ap-simulator"
fileroot_cloud = "/home/ubuntu/ap-simulator/"

if os.getcwd() == fileroot_local:
    run_cloud = False
    fileroot = fileroot_local
    requests_pathname_prefix = "/"
else:
    run_cloud = True
    fileroot = fileroot_cloud
    requests_pathname_prefix = "/ap-simulator/s1-s2/"

# Top navigation bar
navbar = dbc.NavbarSimple(
    children=[
        dbc.DropdownMenu(
            [
                dbc.DropdownMenuItem("Regular stimulation", href="/reg-stim/"),
                dbc.DropdownMenuItem("S1-S2 restitution", href="/s1-s2/"),
                dbc.DropdownMenuItem(
                    "Rate dependence and alternans", href="/rate-dep/"
                ),
            ],
            label="Protocol",
            nav=True,
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Article",
                href="https://elifesciences.org/articles/48890",
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Source Code",
                href="https://github.com/ThomasMBury/ap_simulation_app",
            )
        ),
    ],
    brand="Human ventricular cardiomyocyte simulator",
    brand_href="#",
    color="dark",
    dark=True,
)


# Initialise app
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    requests_pathname_prefix=requests_pathname_prefix,
    suppress_callback_exceptions=True,
)
server = app.server


list_params_cond = [
    "INa.GNa",
    "INaL.GNaL_b",
    "ICaL.PCa_b",
    "Ito.Gto_b",
    "INaCa.Gncx_b",
    "INaK.Pnak_b",
    "IKr.GKr_b",
    "IKs.GKs_b",
    "IK1.GK1_b",
    "ryr.Jrel_b",
    "SERCA.Jup_b",
]

list_params_extracell = [
    "extracellular.cao",
    "extracellular.clo",
    "extracellular.nao",
    "extracellular.ko",
]

list_params_other = ["environment.celltype"]

# Load in model from mmt file
filepath_mmt = fileroot + "/mmt_files/torord-2019.mmt"
m = myokit.load_model(filepath_mmt)

# Get names of all variables in model
var_names = [var.qname() for var in list(m.variables(const=False))]
# State variables to plot by default
plot_vars = ["membrane.v", "intracellular_ions.cai"]
plot_var_def = "membrane.v"
# plot_var_def = "intracellular_ions.cai"

# Create simulation object with model
s = myokit.Simulation(m)

# Preset parameter configurations - default values
params_default = {
    par: m.get(par).value()
    for par in list_params_cond + list_params_extracell + list_params_other
}

# Default protocol values
s1_interval_def = 1000
s1_nbeats_def = 10
s2_intervals_def = "300:500:20, 500:1000:50"

# Run default S1S2 simulation
df_ts, df_restitution = funs.sim_s1s2_restitution(
    s,
    params={},
    s1_interval=s1_interval_def,
    s1_nbeats=s1_nbeats_def,
    s2_intervals=s2_intervals_def,
)

# Need to convert df to dict to store as json on app
ts_data = {"data-frame": df_ts.to_dict("records")}
restitution_data = {"data-frame": df_restitution.to_dict("records")}

# Make dict contianing all parameter values to save
parameter_data = params_default.copy()
parameter_data["s1_interval"] = s1_interval_def
parameter_data["s1_nbeats"] = s1_nbeats_def
parameter_data["s2_intervals"] = s2_intervals_def

# Make default figs
fig_ts = funs.make_s1s2_fig(df_ts, plot_var_def)
fig_restitution = funs.make_restitution_fig(df_restitution, plot_var_def)
div_fig = html.Div([dcc.Graph(figure=fig_ts), dcc.Graph(figure=fig_restitution)])

# Setup figure tabs
list_tabs = [dcc.Tab(value=var, label=var) for var in plot_vars]
tabs = dcc.Tabs(list_tabs, id="tabs", value=plot_var_def)


# ------------
# App layout
# --------------


def make_slider(label="ICaL", id_prefix="ical", default_value=1, slider_range=[0, 3]):
    """Make a connected slider and input box for a parameter in the model

    Args:
        label: label shown on slider
        id_prefix: prefix for reference ID used in callbacks
        default_value: default value
        slider_range: slider range

    Returns:
        Dash slider object in a Div
    """

    slider = html.Div(
        [
            # Title for slider
            html.Label(
                label,
                id="{}_slider_text".format(id_prefix),
                style={"fontSize": 14},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            # Slider
                            dcc.Slider(
                                id="{}_slider".format(id_prefix),
                                min=slider_range[0],
                                max=slider_range[1],
                                marks={i: "{}".format(i) for i in range(4)},
                                value=default_value,
                            ),
                        ],
                        width=9,
                    ),
                    dbc.Col(
                        [
                            # Input box
                            dcc.Input(
                                id="{}_box".format(id_prefix),
                                type="number",
                                min=slider_range[0],
                                max=slider_range[1],
                                step=0.001,
                                value=default_value,
                                style=dict(width=80, display="inline-block"),
                            ),
                        ],
                        width=3,
                    ),
                ]
            ),
        ]
    )
    return slider


# Make sliders for conductances
list_sliders = []
for par in list_params_cond:
    slider = make_slider(
        label=par, id_prefix=par.replace(".", "_"), default_value=1, slider_range=[0, 3]
    )
    list_sliders.append(slider)


body_layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Markdown(
                            """
                            -----
                            **Protocol**:
                            """
                        ),
                        # Input box for BCL
                        html.Div(
                            [
                                html.Label(
                                    "S1 cycle length =", style=dict(fontSize=14)
                                ),
                                dcc.Input(
                                    id="s1_interval",
                                    value=s1_interval_def,
                                    type="number",
                                    style=dict(width=80, display="inline-block"),
                                    placeholder=s1_interval_def,
                                    min=1,
                                    max=10000,
                                ),
                                html.Label(", BPM = ", style=dict(fontSize=14)),
                                dcc.Input(
                                    id="bpm",
                                    value=60,
                                    type="number",
                                    style=dict(width=80, display="inline-block"),
                                    min=6,
                                    max=60000,
                                ),
                            ],
                        ),
                        # Input box for number of beats
                        html.Div(
                            [
                                html.Label(
                                    "Number of S1 pulses = ",
                                    style=dict(fontSize=14, display="inline-block"),
                                ),
                                dcc.Input(
                                    id="s1_nbeats",
                                    value=s1_nbeats_def,
                                    type="number",
                                    style=dict(width=80, display="inline-block"),
                                    placeholder=s1_nbeats_def,
                                    min=1,
                                    max=200,
                                    step=1,
                                ),
                            ],
                            style=dict(display="inline-block", width="100%"),
                        ),
                        # Input box for show last
                        html.Div(
                            [
                                html.Label(
                                    "S2 intervals (comma separated list, min:max:inc) ",
                                    style=dict(fontSize=14),
                                ),
                                dcc.Input(
                                    id="s2_intervals",
                                    value=s2_intervals_def,
                                    type="text",
                                    style=dict(width=300),
                                    placeholder=s2_intervals_def,
                                ),
                            ]
                        ),
                        dcc.Markdown(
                            """
                            -----
                            **Cell type and current multipliers**:
                            """
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Cell type", style=dict(fontSize=14)
                                        ),
                                        dcc.Dropdown(
                                            ["endo", "epi", "mid"],
                                            "endo",
                                            id="cell_type",
                                            clearable=False,
                                            style=dict(fontSize=14),
                                        ),
                                    ],
                                    width=4,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Preset", style=dict(fontSize=14)),
                                        dcc.Dropdown(
                                            ["default", "EAD"],
                                            "default",
                                            id="dropdown_presets",
                                            clearable=False,
                                            style=dict(fontSize=14),
                                        ),
                                    ],
                                    width=4,
                                ),
                            ]
                        ),
                        html.Br(),
                    ]
                    # Div for slider and input box
                    + list_sliders
                    + [
                        dcc.Markdown(
                            """
                            -----
                            **Extracellular concentrations**:
                            """
                        ),
                        html.Div(
                            [
                                html.Label("Cao =", style=dict(fontSize=14)),
                                dcc.Input(
                                    id="extracellular_cao_box",
                                    value=params_default["extracellular.cao"],
                                    type="number",
                                    style=dict(width=80, display="inline-block"),
                                    placeholder=params_default["extracellular.cao"],
                                    min=0,
                                    max=1000,
                                    step=0.1,
                                ),
                            ],
                        ),
                        html.Div(
                            [
                                html.Label(
                                    "Clo =", style=dict(fontSize=14, marginRight=5)
                                ),
                                dcc.Input(
                                    id="extracellular_clo_box",
                                    value=params_default["extracellular.clo"],
                                    type="number",
                                    style=dict(width=80, display="inline-block"),
                                    placeholder=params_default["extracellular.clo"],
                                    min=0,
                                    max=1000,
                                    step=0.1,
                                ),
                            ],
                        ),
                        html.Div(
                            [
                                html.Label(
                                    "Ko =", style=dict(fontSize=14, marginRight=10)
                                ),
                                dcc.Input(
                                    id="extracellular_ko_box",
                                    value=params_default["extracellular.ko"],
                                    type="number",
                                    style=dict(width=80, display="inline-block"),
                                    placeholder=params_default["extracellular.ko"],
                                    min=0,
                                    max=1000,
                                    step=0.1,
                                ),
                            ],
                        ),
                        html.Div(
                            [
                                html.Label("Nao =", style=dict(fontSize=14)),
                                dcc.Input(
                                    id="extracellular_nao_box",
                                    value=params_default["extracellular.nao"],
                                    type="number",
                                    style=dict(width=80, display="inline-block"),
                                    placeholder=params_default["extracellular.nao"],
                                    min=0,
                                    max=1000,
                                    step=0.1,
                                ),
                            ],
                        ),
                    ],
                    width=4,
                ),
                dbc.Col(
                    [
                        dcc.Markdown(
                            """
                            -----
                            **Plot variables**:
                            """
                        ),
                        # Tabs
                        html.Div(tabs, id="tabs_container_div"),
                        # Figure
                        html.Div(id="tabs_container_output_div", children=div_fig),
                        # # Figure
                        # div_tabs,
                        # html.Div(div_tabs, id="div_tabs"),
                        # Row for loading bar, run button and save button
                        dbc.Row(
                            [
                                dbc.Col(
                                    # Loading animation
                                    html.Div(
                                        [
                                            dcc.Loading(
                                                id="loading-anim",
                                                type="circle",
                                                children=html.Div(id="loading-output"),
                                                # color="#2ca02c",
                                            ),
                                        ],
                                        style={
                                            "padding-bottom": "10px",
                                            "padding-top": "20px",
                                            "vertical-align": "middle",
                                        },
                                    ),
                                    width=dict(size=1, offset=7),
                                ),
                                dbc.Col(
                                    # Run button
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Run",
                                                id="run_button",
                                                color="success",
                                                n_clicks=0,
                                                style=dict(fontSize=14),
                                            ),
                                        ],
                                        className="d-grid gap-2",
                                    ),
                                    width=2,
                                ),
                                dbc.Col(
                                    # SAVE BUTTON
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Save data",
                                                id="button_savedata",
                                                className="d-grid gap-2",
                                                n_clicks=0,
                                                style=dict(fontSize=14),
                                            ),
                                            dcc.Download(id="download_ts"),
                                            dcc.Download(id="download_restitution"),
                                            dcc.Download(id="download_parameters"),
                                            # Storage component for time series data
                                            dcc.Store(
                                                id="ts_data",
                                                data=ts_data,
                                            ),
                                            # Storage component for restitution data
                                            dcc.Store(
                                                id="restitution_data",
                                                data=restitution_data,
                                            ),
                                            # Storage component for time series data
                                            dcc.Store(
                                                id="parameter_data", data=parameter_data
                                            ),
                                        ],
                                        className="d-grid gap-2",
                                    ),
                                    width=dict(size=2, offset=0),
                                ),
                            ]
                        ),
                    ],
                    width=8,
                ),
            ]
        )
    ]
)


app.layout = html.Div([navbar, body_layout])


# -----------------
# Callback function to sync BCL and BPM boxes
# -----------------
@app.callback(
    [
        Output(
            "s1_interval",
            "value",
            allow_duplicate=True,
        ),
        Output("bpm", "value"),
    ],
    [
        Input("s1_interval", "value"),
        Input("bpm", "value"),
    ],
    prevent_initial_call=True,
)
def sync_input(bcl, bpm):
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if input_id == "s1_interval":
        bpm = None if bcl is None else int(60000 / float(bcl) * 100) / 100
    else:
        bcl = None if bpm is None else int(60000 / float(bpm) * 100) / 100
    return bcl, bpm


# --------------
# Callback functions to sync sliders with respective input boxes
# ---------------


def sync_slider_box(box_value, slider_value):
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    box_value_out = box_value if trigger_id[-3:] == "box" else slider_value
    slider_value_out = slider_value if trigger_id[-6:] == "slider" else box_value

    return box_value_out, slider_value_out


for par in list_params_cond:
    par_id = par.replace(".", "_")
    app.callback(
        [
            Output("{}_box".format(par_id), "value", allow_duplicate=True),
            Output("{}_slider".format(par_id), "value", allow_duplicate=True),
        ],
        [
            Input("{}_box".format(par_id), "value"),
            Input("{}_slider".format(par_id), "value"),
        ],
        prevent_initial_call=True,
    )(sync_slider_box)

# -------------
# Callback to update sliders and ECM boxes with a change in preset param config
# --------------

# Default slider and box parameters
pars_slider_box_default = params_default.copy()
# Don't need cell type here
cell_type = pars_slider_box_default.pop("environment.celltype")
# Note using multipliers
for key in list_params_cond:
    pars_slider_box_default[key] = 1

# EAD slider and box parameters
pars_slider_box_ead = pars_slider_box_default.copy()
pars_slider_box_ead["IKr.GKr_b"] = 0.15
pars_slider_box_ead["ICaL.PCa_b"] = 1
pars_slider_box_ead["INaCa.Gncx_b"] = 1
pars_slider_box_ead["extracellular.nao"] = 137
pars_slider_box_ead["extracellular.clo"] = 148
pars_slider_box_ead["extracellular.cao"] = 2
bcl_ead = 4000

# Output includes all sliders and ECM boxes
outputs_callback_preset = (
    [
        Output(
            "{}_slider".format(prefix).replace(".", "_"), "value", allow_duplicate=True
        )
        for prefix in list_params_cond
    ]
    + [
        Output("{}_box".format(prefix).replace(".", "_"), "value", allow_duplicate=True)
        for prefix in list_params_extracell
    ]
    + [Output("s1_interval", "value", allow_duplicate=True)]
)
# Input is dropdown box that contains preset labels
inputs_callback_presets = Input("dropdown_presets", "value")


@app.callback(
    outputs_callback_preset,
    inputs_callback_presets,
    prevent_initial_call=True,
    allow_duplicate=True,
)
def udpate_sliders_and_boxes(preset):
    if preset == "default":
        return list(pars_slider_box_default.values()) + [s1_interval_def]
    elif preset == "EAD":
        return list(pars_slider_box_ead.values()) + [bcl_ead]
    else:
        return 0


# # ---------
# # Callback to sync tabs with variables selected in dropdown box
# # ---------


# @callback(
#     Output("tabs_container_div", "children"), Input("dropdown_plot_vars", "value")
# )
# def display_tabs(plot_vars):
#     tabs = [dcc.Tab(value=var, label=var) for var in plot_vars]
#     children = (
#         dcc.Tabs(
#             id="tabs",
#             value="membrane.v",
#             children=tabs,
#         ),
#     )
#     return children


# ---------
# Callback to save simulation and parameter data
# ---------
@app.callback(
    [
        Output("download_ts", "data"),
        Output("download_restitution", "data"),
        Output("download_parameters", "data"),
    ],
    Input("button_savedata", "n_clicks"),
    State("ts_data", "data"),
    State("restitution_data", "data"),
    State("parameter_data", "data"),
    prevent_initial_call=True,
)
def func(n_clicks, ts_data, restitution_data, parameter_data):
    df_ts = pd.DataFrame(ts_data["data-frame"])
    df_restitution = pd.DataFrame(restitution_data["data-frame"])
    df_pars = pd.DataFrame()
    df_pars["name"] = parameter_data.keys()
    df_pars["value"] = parameter_data.values()
    # df_pars = df_pars.astype("object")
    out1 = dcc.send_data_frame(df_ts.to_csv, "ts.csv")
    out2 = dcc.send_data_frame(df_restitution.to_csv, "restitution.csv")
    out3 = dcc.send_data_frame(df_pars.to_csv, "parameters.csv")

    return [out1, out2, out3]


# -----------
# Callback function on RUN button click - run simulation and make figure
# ------------

# Output includes (i) all figures, (ii) loading sign (iii) simulation and parameter data for download
outputs_callback_run = (
    Output("tabs_container_output_div", "children"),
    Output("loading-output", "children"),
    Output("ts_data", "data"),
    Output("restitution_data", "data"),
    Output("parameter_data", "data"),
)
# Input is click of run button
inputs_callback_run = dict(n_clicks=[Input("run_button", "n_clicks")])

# State values are all parameters contained in sliders + boxes
states_callback_run = dict(
    s1_interval=State("s1_interval", "value"),
    s1_nbeats=State("s1_nbeats", "value"),
    s2_intervals=State("s2_intervals", "value"),
    cell_type=State("cell_type", "value"),
    current_plot_var=State("tabs", "value"),
    params_cond={
        par: State("{}_box".format(par.replace(".", "_")), "value")
        for par in list_params_cond
    },
    params_extracell={
        par: State("{}_box".format(par.replace(".", "_")), "value")
        for par in list_params_extracell
    },
)


@app.callback(
    output=outputs_callback_run,
    inputs=inputs_callback_run,
    state=states_callback_run,
    prevent_initial_call=True,
)
def run_sim_and_update_fig(
    n_clicks,
    s1_interval,
    s1_nbeats,
    s2_intervals,
    cell_type,
    current_plot_var,
    params_cond,
    params_extracell,
):
    # Updated parameter values
    params = {}

    # Multipliers
    for par in list_params_cond:
        params[par] = params_default[par] * params_cond[par]

    # Extracellular
    for par in list_params_extracell:
        params[par] = params_extracell[par]

    # Cell type
    cell_type_dict = {"endo": 0, "epi": 1, "mid": 2}
    params["environment.celltype"] = cell_type_dict[cell_type]

    # Make dict contianing all parameter values to save
    parameter_data = params.copy()
    parameter_data["s1_interval"] = s1_interval
    parameter_data["s1_nbeats"] = s1_nbeats
    parameter_data["s2_intervals"] = s2_intervals

    # Run simulation
    df_ts, df_restitution = funs.sim_s1s2_restitution(
        s,
        params=params,
        s1_interval=s1_interval,
        s1_nbeats=s1_nbeats,
        s2_intervals=s2_intervals,
    )

    # Need to convert df to dict to store as json on app
    ts_data = {"data-frame": df_ts.to_dict("records")}
    restitution_data = {"data-frame": df_restitution.to_dict("records")}

    # Make figs
    fig_ts = funs.make_s1s2_fig(df_ts, current_plot_var)
    fig_restitution = funs.make_restitution_fig(df_restitution, current_plot_var)
    div_fig = html.Div([dcc.Graph(figure=fig_ts), dcc.Graph(figure=fig_restitution)])

    return [div_fig, "", ts_data, restitution_data, parameter_data]


# ---------
# Callback to switch between tabs
# ---------
@callback(
    Output("tabs_container_output_div", "children", allow_duplicate=True),
    Input("tabs", "value"),
    State("ts_data", "data"),
    State("restitution_data", "data"),
    prevent_initial_call=True,
)
def render_content(tab, ts_data, restitution_data):
    df_ts = pd.DataFrame(ts_data["data-frame"])
    df_restitution = pd.DataFrame(restitution_data["data-frame"])
    # Make figs
    fig_ts = funs.make_s1s2_fig(df_ts, tab)
    fig_restitution = funs.make_restitution_fig(df_restitution, tab)
    div_fig = html.Div([dcc.Graph(figure=fig_ts), dcc.Graph(figure=fig_restitution)])

    return div_fig


if __name__ == "__main__":
    app.run_server(debug=True)
