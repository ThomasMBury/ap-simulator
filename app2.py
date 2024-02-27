#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 27 Feb, 2024

Dash app to run simulation of Torod model in myokit
Updates:
    - dropdown box to select sliders that appear

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


# Notes of things to fix
# - labels on sliders same as labels on tabs
# - run button next to save button
# - max value for total_beats
# - timeout for simulation callback
# - pin wheel next to run


# Inspired by this example
# https://dash.gallery/dash-cytoscape-lda/?_gl=1*1n1w6iy*_ga*MTkwMzI4NzAyLjE2NjY4MDg0MDg.*_ga_6G7EE0JNSC*MTcwMDI2MTU3MS4xMDguMS4xNzAwMjYyNTY0LjYwLjAuMA..#

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
    requests_pathname_prefix = "/ap-simulator/"

# Top navigation bar
navbar = dbc.NavbarSimple(
    children=[
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
)
server = app.server


# Dictionary to map paramter label to parameter stored in mmt file
label_to_par = dict(
    INa="INa.GNa",  # membrane_fast_sodium_current_conductance
    INaL="INaL.GNaL_b",  # membrane_persistent_sodium_current_conductance
    ICaL="ICaL.PCa_b",  # membrane_L_type_calcium_current_conductance
    Ito="Ito.Gto_b",  # membrane_transient_outward_current_conductance
    INaCa="INaCa.Gncx_b",  # membrane_sodium_calcium_exchanger_current_conductance
    INaK="INaK.Pnak_b",  # membrane_sodium_potassium_pump_current_permeability
    IKr="IKr.GKr_b",  # membrane_rapid_delayed_rectifier_potassium_current_conductance
    IKs="IKs.GKs_b",  # membrane_slow_delayed_rectifier_potassium_current_conductance
    IK1="IK1.GK1_b",  # membrane_inward_rectifier_potassium_current_conductance
    Jrel="ryr.Jrel_b",  # SR_release_current_max
    Jup="SERCA.Jup_b",  # SR_uptake_current_max
)

# Map for parameters of extracellular matrix
label_to_par_extra = dict(
    Cao="extracellular.cao",  # extracellular_calcium_concentration
    Clo="extracellular.clo",
    Nao="extracellular.nao",  # extracellular_sodium_concentration
    Ko="extracellular.ko",  # extracellular_potassium_concentration
)


# Load in model from mmt file
filepath_mmt = fileroot + "/mmt_files/torord-2019.mmt"
m = myokit.load_model(filepath_mmt)

# Create simulation object with model
s = myokit.Simulation(m)

# Get default parameter values used in Torord (to then apply multipliers)
params_default = {
    label: m.get(label_to_par[label]).value() for label in label_to_par.keys()
}

# Default protocol values
bcl_def = 1000
total_beats_def = 100
beats_keep_def = 1

# # Run default simulation
df_sim = funs.sim_model(
    s, params={}, bcl=bcl_def, total_beats=total_beats_def, beats_keep=beats_keep_def
)

# Make figures and put them into tabs
list_tabs = []
list_vars = [v for v in df_sim.columns if v != "time"]

for var in list_vars:
    fig = dcc.Graph(
        figure=funs.make_simulation_fig(df_sim, var),
        id="fig_{}".format(var),
        style=dict(height=600),
    )
    tab = dcc.Tab(label=var, children=[fig])
    list_tabs.append(tab)

fig_tabs = dcc.Tabs(list_tabs)


# ------------
# App layout
# --------------


def make_slider(label, id_prefix, default_value, slider_range):
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
                                # step=10,
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


# Make sliders for model parameters
list_sliders = []
for par in label_to_par.keys():
    slider = make_slider(par, par, 1, [0, 3])
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
                                    "Basic cycle length =", style=dict(fontSize=14)
                                ),
                                dcc.Input(
                                    id="bcl",
                                    value=bcl_def,
                                    type="number",
                                    style=dict(width=80, display="inline-block"),
                                    placeholder=bcl_def,
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
                                    "Number of beats = ",
                                    style=dict(fontSize=14, display="inline-block"),
                                ),
                                dcc.Input(
                                    id="total_beats",
                                    value=total_beats_def,
                                    type="number",
                                    style=dict(width=80, display="inline-block"),
                                    placeholder=total_beats_def,
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
                                html.Label("Show last ", style=dict(fontSize=14)),
                                dcc.Input(
                                    id="beats_keep",
                                    value=beats_keep_def,
                                    type="number",
                                    style=dict(width=80),
                                    placeholder=beats_keep_def,
                                    min=1,
                                    max=200,
                                    step=1,
                                ),
                                html.Label(" beats ", style=dict(fontSize=14)),
                            ]
                        ),
                        # dbc.Row(
                        #     [
                        #         dbc.Col(
                        #             # Loading animation
                        #             html.Div(
                        #                 [
                        #                     dcc.Loading(
                        #                         id="loading-anim",
                        #                         type="circle",
                        #                         children=html.Div(id="loading-output"),
                        #                         # color="#2ca02c",
                        #                     ),
                        #                 ],
                        #                 style={
                        #                     "padding-bottom": "10px",
                        #                     "padding-top": "20px",
                        #                     "vertical-align": "middle",
                        #                 },
                        #             ),
                        #             width=8,
                        #         ),
                        #     ]
                        # ),
                        dcc.Markdown(
                            """
                            -----
                            **Model selection and parameters**:
                            """
                        ),
                        dbc.Row(
                            [
                                # Model type
                                dbc.Col(
                                    [
                                        html.Label("Model", style=dict(fontSize=14)),
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
                                # # Save button
                                # dbc.Col(
                                #     [
                                #         html.Label(
                                #             "Save myokit", style=dict(fontSize=14)
                                #         ),
                                #         dbc.Button(
                                #             "Save",
                                #             id="example-button",
                                #             className="me-2",
                                #             n_clicks=0,
                                #             style=dict(fontSize=14),
                                #         ),
                                #     ],
                                #     width=4,
                                # ),
                                # # Load button
                                # dbc.Col(
                                #     [
                                #         html.Label(
                                #             "Load myokit", style=dict(fontSize=14)
                                #         ),
                                #         dcc.Upload(
                                #             id="load-myokit",
                                #             children=html.Div(
                                #                 [
                                #                     "drag+drop",
                                #                 ]
                                #             ),
                                #             style={
                                #                 "width": "100%",
                                #                 "height": "35px",
                                #                 "lineHeight": "30px",
                                #                 "borderWidth": "1px",
                                #                 "borderStyle": "dashed",
                                #                 "borderRadius": "5px",
                                #                 "textAlign": "center",
                                #                 "margin": "0px",
                                #                 "fontSize": 14,
                                #             },
                                #             multiple=False,
                                #         ),
                                #     ],
                                #     width=4,
                                # ),
                            ]
                        ),
                        html.Br(),
                    ]
                    # Div for slider and input box
                    + list_sliders,
                    width=4,
                ),
                dbc.Col(
                    [
                        # Figure
                        html.Div(
                            fig_tabs,
                            style={
                                "width": "100%",
                                # "height": "1000px",
                                "fontSize": 12,
                                "padding-left": "2%",
                                "padding-right": "2%",
                                "padding-top": "2%",
                                "vertical-align": "middle",
                                "display": "inline-block",
                            },
                        ),
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
                                    # Save button
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "Save data",
                                                id="button_savedata",
                                                className="d-grid gap-2",
                                                n_clicks=0,
                                                style=dict(fontSize=14),
                                            ),
                                            dcc.Download(id="download_simulation"),
                                            # Storage component for simulation data
                                            dcc.Store(id="simulation_data"),
                                        ],
                                        className="d-grid gap-2",
                                    ),
                                    width=dict(size=2, offset=0),
                                ),
                            ]
                        ),
                    ]
                ),
            ]
        )
    ]
)

# # Button to save simulation data
# html.Div(
#     [
#         dbc.Button(
#             "Save data",
#             id="button_savedata",
#             className="me-2",
#             n_clicks=0,
#             style=dict(fontSize=14),
#         ),
#         dcc.Download(id="download_simulation"),
#     ],
#     style={
#         "width": "100%",
#         "fontSize": 12,
#         "padding-left": "85%",
#         "padding-right": "2%",
#         "padding-top": "0%",
#         "vertical-align": "middle",
#         "display": "inline-block",
#     },
# ),

# ),


app.layout = html.Div([navbar, body_layout])


# ------------------
# Callback functions
# -------------------


### Callback function to sync BCL and BPM boxes
@app.callback(
    [
        Output("bcl", "value"),
        Output("bpm", "value"),
    ],
    [
        Input("bcl", "value"),
        Input("bpm", "value"),
    ],
)
def sync_input(bcl, bpm):
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if input_id == "bcl":
        bpm = None if bcl is None else int(60000 / float(bcl) * 100) / 100
    else:
        bcl = None if bpm is None else int(60000 / float(bpm) * 100) / 100
    return bcl, bpm


### Callback functions to sync sliders with respective input boxes
def sync_slider_box(box_value, slider_value):
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    box_value_out = box_value if trigger_id[-3:] == "box" else slider_value
    slider_value_out = slider_value if trigger_id[-6:] == "slider" else box_value

    return box_value_out, slider_value_out


for par in label_to_par.keys():
    app.callback(
        [
            Output("{}_box".format(par), "value"),
            Output("{}_slider".format(par), "value"),
        ],
        [
            Input("{}_box".format(par), "value"),
            Input("{}_slider".format(par), "value"),
        ],
    )(sync_slider_box)


### Callback to save simulation data
@app.callback(
    Output("download_simulation", "data"),
    Input("button_savedata", "n_clicks"),
    State("simulation_data", "data"),
    prevent_initial_call=True,
)
def func(n_clicks, stored_data):
    df = pd.DataFrame(stored_data["data-frame"])
    return dcc.send_data_frame(df.to_csv, "simulation_data.csv")


### Callback function for model simulation and update of figure
@app.callback(
    [Output("fig_{}".format(var), "figure") for var in list_vars]  # all figure outputs
    + [Output("loading-output", "children")]  # loading output
    + [Output("simulation_data", "data")],  # storage of simulation data
    [Input("run_button", "n_clicks")],
    [
        State("bcl", "value"),
        State("total_beats", "value"),
        State("beats_keep", "value"),
        State("cell_type", "value"),
    ]
    + [
        State("{}_box".format(par), "value") for par in label_to_par.keys()
    ],  # all parameter multipliers
)
def update_fig(
    n_clicks,
    bcl,
    total_beats,
    beats_keep,
    cell_type,
    *par_multipliers,
):
    # Updated parameter values
    params = {}
    for idx, label in enumerate(label_to_par.keys()):
        params[label_to_par[label]] = params_default[label] * par_multipliers[idx]

    cell_type_dict = {"endo": 0, "epi": 1, "mid": 2}

    # Run simulation
    df_sim = funs.sim_model(
        s,
        params=params,
        bcl=bcl,
        total_beats=total_beats,
        beats_keep=beats_keep,
        cell_type=cell_type_dict[cell_type],
    )

    # Need to convert df to dict to store as json
    stored_data = {"data-frame": df_sim.to_dict("records")}

    list_figs = []
    for var in list_vars:
        fig = funs.make_simulation_fig(df_sim, var)
        list_figs.append(fig)

    return list_figs + [""] + [stored_data]


if __name__ == "__main__":
    app.run_server(debug=True)
