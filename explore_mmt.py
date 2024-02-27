#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2024-02-27.

Explore mmt files

@author: Thomas Bury, thomasbury.net
"""

import os
import numpy as np
import pandas as pd

from dash import Dash, html, dcc, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import myokit as myokit

import app_functions as funs


# Dictionary to map paramter label to parameter stored in mmt file
label_to_par = dict(
    INa="INa.GNa",  # inward sodium current
    Ito="Ito.Gto_b",  # transient outward current
    ICaL="ICaL.PCa_b",  # L-type calcium current
    IKr="IKr.GKr_b",  # Rapid late potassium current
    IKs="IKs.GKs_b",  # Slow late potassium current
    INaCa="INaCa.Gncx_b",  # sodium calcium exchange current
    tjca="ICaL.tjca",  # relaxation time of L-type Ca current
)

# Map for parameters of extracellular matrix
label_to_par_extra = dict(
    Cao="extracellular.cao",
    Clo="extracellular.clo",
    Nao="extracellular.nao",
    Ko="extracellular.ko",
)

# Load in model from mmt file
fileroot = "/Users/tbury/Google Drive/research/postdoc_23/ap-simulator"

filepath_mmt = fileroot + "/mmt_files/torord-2019.mmt"
m = myokit.load_model(filepath_mmt)

# Validate model (check mmt was parsed correctly)
m.validate()

# # List all parameters
# for par in m.variables(const=True):
#     print(par)
print(len(list(m.variables(const=True))))


# List all state variables
for state in m.states():
    print(state)
print(len(list(m.states())))
