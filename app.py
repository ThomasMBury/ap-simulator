#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 26 15:26:03 2021

Dash app to run simulation of Torod model in myokit

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

# Dictionary to map to param labels used in Torord
dict_par_labels = {
    "ina": "INa.GNa",  # inward sodium current
    "ito": "Ito.Gto_b",  # transient outward current
    "ical": "ICaL.PCa_b",  # L-type calcium current
    "ikr": "IKr.GKr_b",  # Rapid late potassium current
    "iks": "IKs.GKs_b",  # Slow late potassium current
    "inaca": "INaCa.Gncx_b",  # sodium calcium exchange current
    "tjca": "ICaL.tjca",  # relaxation time of L-type Ca current
}

# Load in model from mmt file
filepath_mmt = fileroot + "/mmt_files/torord-2019.mmt"
m = myokit.load_model(filepath_mmt)

# Create simulation object with model
s = myokit.Simulation(m)

# Get default parameter values used in Torord (required to apply multipliers)
params_default = {
    par: m.get(dict_par_labels[par]).value() for par in dict_par_labels.keys()
}

# Default multiplier values
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
    )
    tab = dcc.Tab(label=var, children=[fig])
    list_tabs.append(tab)

fig_tabs = dcc.Tabs(list_tabs)


# ------------
# App layout
# --------------

# # Slider tick marks
# slider_marks_multipliers = {
#     int(x) if x % 1 == 0 else x: str(x)
#     for x in np.arange(slider_min, slider_max + 0.01, 0.5)
# }


def make_slider(label, id_stem, default_value, slider_range):
    slider = html.Div(
        [
            # Title for slider
            html.Label(
                label,
                id="{}_slider_text".format(id_stem),
                style={"fontSize": 14},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            # Slider
                            dcc.Slider(
                                id="{}_slider".format(id_stem),
                                min=slider_range[0],
                                max=slider_range[1],
                                # step=10,
                                # marks=slider_marks,
                                value=default_value,
                            ),
                        ],
                        width=9,
                    ),
                    dbc.Col(
                        [
                            # Input box
                            dcc.Input(
                                id="{}_box".format(id_stem),
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
for par in dict_par_labels.keys():
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
                                    value=1000,
                                    type="number",
                                    style=dict(width=80, display="inline-block"),
                                    placeholder=1000,
                                ),
                                html.Label(", BPM = ", style=dict(fontSize=14)),
                                dcc.Input(
                                    id="bpm",
                                    value=60,
                                    type="number",
                                    style=dict(width=80, display="inline-block"),
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
                                    id="num_beats",
                                    value=10,
                                    type="number",
                                    style=dict(width=80, display="inline-block"),
                                    placeholder=10,
                                ),
                            ],
                            style=dict(display="inline-block", width="100%"),
                        ),
                        # Input box for show last
                        html.Div(
                            [
                                html.Label("Show last ", style=dict(fontSize=14)),
                                dcc.Input(
                                    id="show_last",
                                    value=1,
                                    type="number",
                                    style=dict(width=80),
                                    placeholder=1,
                                ),
                                html.Label(" beats ", style=dict(fontSize=14)),
                            ]
                        ),
                        # Run button
                        html.Div(
                            [
                                dbc.Button(
                                    "Run",
                                    id="run_button",
                                    className="me-2",
                                    n_clicks=0,
                                    style=dict(fontSize=14),
                                ),
                            ]
                        ),
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
                                            id="demo-dropdown",
                                            clearable=False,
                                            style=dict(fontSize=14),
                                        ),
                                    ],
                                    width=4,
                                ),
                                # Save button
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Save myokit", style=dict(fontSize=14)
                                        ),
                                        dbc.Button(
                                            "Save",
                                            id="example-button",
                                            className="me-2",
                                            n_clicks=0,
                                            style=dict(fontSize=14),
                                        ),
                                    ],
                                    width=4,
                                ),
                                # Load button
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Load myokit", style=dict(fontSize=14)
                                        ),
                                        dcc.Upload(
                                            id="load-myokit",
                                            children=html.Div(
                                                [
                                                    "drag+drop",
                                                ]
                                            ),
                                            style={
                                                "width": "100%",
                                                "height": "35px",
                                                "lineHeight": "30px",
                                                "borderWidth": "1px",
                                                "borderStyle": "dashed",
                                                "borderRadius": "5px",
                                                "textAlign": "center",
                                                "margin": "0px",
                                                "fontSize": 14,
                                            },
                                            multiple=False,
                                        ),
                                    ],
                                    width=4,
                                ),
                            ]
                        ),
                        html.Br(),
                    ]
                    # Div for slider and input box
                    + list_sliders,
                    width=4,
                ),
                dbc.Col(
                    # Figure
                    html.Div(
                        fig_tabs,
                        style={
                            "width": "100%",
                            "height": "1000px",
                            "fontSize": "10px",
                            "padding-left": "2%",
                            "padding-right": "2%",
                            "padding-top": "2%",
                            "vertical-align": "middle",
                            "display": "inline-block",
                        },
                    ),
                    width=8,
                ),
            ]
        )
    ]
)

app.layout = html.Div([navbar, body_layout])


# ------------------
# Callback functions
# -------------------


# Callback function to sync BCL and BPM boxes
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


# Callback functions to sync sliders with input box
def sync_slider_box(box_value, slider_value):
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    box_value_out = box_value if trigger_id[-3:] == "box" else slider_value
    slider_value_out = slider_value if trigger_id[-6:] == "slider" else box_value

    return box_value_out, slider_value_out


for par in dict_par_labels.keys():
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


# Callback function for model simulation and update of figure
@app.callback(
    [Output("fig_{}".format(var), "figure") for var in list_vars],
    [Input("run_button", "n_clicks")],
    [State("{}_box".format(par), "value") for par in dict_par_labels.keys()],
)
def update_fig(n_clicks, a, b, c, d, e, f, g):
    # Run simulation
    df_sim = funs.sim_model(
        s, params={}, bcl=1000, total_beats=100, beats_keep=4, cell_type=0
    )

    list_figs = []
    for var in list_vars:
        fig = funs.make_simulation_fig(df_sim, var)
        list_figs.append(fig)

    return list_figs


# # Update figure based on change in a model parameter
# @app.callback([Output('fig_voltage','figure'),
#                 Output('loading-output','children'),
#                 ],
#               [
#                 Input('bcl_slider','value'),
#                 Input('num_beats_slider','value'),
#                 Input('ina_slider','value'),
#                 Input('ical_slider','value'),
#                 Input('ikr_slider','value'),
#                 Input('iks_slider','value'),
#                 Input('inaca_slider','value'),
#                 Input('ito_slider','value'),
#                 Input('tjca_slider','value'),
#                 ]
#               )

# def update_fig(bcl, num_beats,
#                 ina_mult, ical_mult, ikr_mult,
#                 iks_mult, inaca_mult, ito_mult,
#                 tjca_mult):

#     # print('using inaca={}'.format(inaca_mult))

#     # Make dict of updated model parameter vlaues
#     params = {}
#     params[dict_par_labels['ina']] = params_default['ina']*ina_mult
#     params[dict_par_labels['ical']] = params_default['ical']*ical_mult
#     params[dict_par_labels['ikr']] = params_default['ikr']*ikr_mult
#     params[dict_par_labels['iks']] = params_default['iks']*iks_mult
#     params[dict_par_labels['inaca']] = params_default['inaca']*inaca_mult
#     params[dict_par_labels['ito']] = params_default['ito']*ito_mult
#     params[dict_par_labels['tjca']] = params_default['tjca']*tjca_mult


#     # Run simulation
#     df_mod = sim_model(s,
#                         params=params,
#                         bcl=bcl,
#                         num_beats = num_beats
#                         )

#     # Make figure
#     fig = generate_fig(df_base, df_mod)

#     return [fig, '']


if __name__ == "__main__":
    app.run_server(debug=True)
