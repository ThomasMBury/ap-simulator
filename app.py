#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 26 15:26:03 2021

Dash app to run simulation of Torod model in myokit

@author: tbury
"""


import numpy as np
import pandas as pd

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px

import time
import os

import myokit as myokit

# Get app functions
from app_functions import sim_model, make_simulation_fig, make_fig_tabs


# Useful example
# https://dash.gallery/dash-cytoscape-lda/?_gl=1*1n1w6iy*_ga*MTkwMzI4NzAyLjE2NjY4MDg0MDg.*_ga_6G7EE0JNSC*MTcwMDI2MTU3MS4xMDguMS4xNzAwMjYyNTY0LjYwLjAuMA..#


# Determine if running app locally or on cloud
fileroot_local = '/Users/tbury/Google Drive/research/postdoc_23/ap_simulation_app/'
fileroot_cloud = '/home/ubuntu/ap_simulation_app/'


if os.getcwd()==fileroot_local[:-1]:
    run_cloud=False
    fileroot = fileroot_local
else:
    run_cloud=True
    fileroot = fileroot_cloud


# # Time function
# tic = time.perf_counter()
# df = sim_br_model(ina_multiplier=10)
# toc = time.perf_counter()
# print(f'Ran function in {toc - tic:0.4f} seconds')


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


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


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server=app.server

# # If running in cloud, adjust prefix
# if run_cloud:
# 	app.config.update({  
# 	# Change this to directory name used in WSGIAlias
# 		'requests_pathname_prefix': '/ap_exploration/',
# 	})
# 	print('Updated prefix')


# Dictionary to map to param labels used in Torord
dict_par_labels = {'ina':'INa.GNa', # inward sodium current
                   'ito':'Ito.Gto_b', # transient outward current
                   'ical':'ICaL.PCa_b', # L-type calcium current
                   'ikr':'IKr.GKr_b', # Rapid late potassium current
                   'iks':'IKs.GKs_b', # Slow late potassium current
                   'inaca':'INaCa.Gncx_b', # sodium calcium exchange current
                   'tjca':'ICaL.tjca', # relaxation time of L-type Ca current
                   }
                   

# Load in model from mmt file
filepath_mmt = fileroot+'mmt_files/torord-2019.mmt'
m = myokit.load_model(filepath_mmt)

# Create simulation object with model
s = myokit.Simulation(m)

# Get default parameter values used in Torord (required to apply multipliers)
params_default = {
    par:m.get(dict_par_labels[par]).value() for par in dict_par_labels.keys()}


# Default multiplier values
bcl_def = 1000
num_beats_def = 4
ina_mult_def = 1
ito_mult_def = 1
ical_mult_def = 1
ikr_mult_def = 1
iks_mult_def = 1
inaca_mult_def = 1
tjca_mult_def = 1


# # Run simulation
df_sim = sim_model(s, params={}, bcl=bcl_def, num_beats=num_beats_def)

# # Make figure
plot_var='voltage'
fig = make_simulation_fig(df_sim, plot_var)

fig_tabs = make_fig_tabs(df_sim)


#------------
# App layout
#--------------


# Slider tick marks
slider_min = 0
slider_max = 3
slider_marks = {int(x) if x % 1 == 0 else x:str(x) for x in np.arange(
    slider_min,slider_max+0.01,0.5)}
slider_step = 0.01 # seperation between values on slider

slider_marks_bcl = {int(x) if x % 1 == 0 else x:str(int(x)) for x in np.arange(
    500,2000+0.01,500)}

slider_marks_num_beats = {
    int(x) if x % 1 == 0 else x:str(int(x)) for x in np.arange(0,101,20)}

slider_marks_bcl = {
    int(x) if x % 1 == 0 else x:str(int(x)) for x in np.arange(0,4001,1000)}



body_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            
            
            dcc.Markdown(
                """
                -----
                **Protocol**:
                """
                ),            
            
                
            # # Div for dropdown
            # html.Div([
            #     # Slider for BCL
            #     html.Label('Pacing cycle length = {}ms'.format(bcl_def),
            #                 id='dropdown',
            #                 style={'fontSize':14}),   
                           
            #     dcc.Slider(id='bcl_slider',
            #                 min=200, 
            #                 max=4000, 
            #                 step=10, 
            #                 marks=slider_marks_bcl,
            #                 value=bcl_def,
            #                 )
            #     ]),                
                
            # Div for sliders
            html.Div([
                # Slider for BCL
                html.Label('Pacing cycle length = {}ms'.format(bcl_def),
                            id='bcl_slider_text',
                            style={'fontSize':14}),   
                           
                dcc.Slider(id='bcl_slider',
                            min=200, 
                            max=4000, 
                            step=10, 
                            marks=slider_marks_bcl,
                            value=bcl_def,
                            )
                ]),
            
            ],
                
                
            width=4,
            ),
        
        dbc.Col(
    
        
            # Figure
            html.Div(
                fig_tabs,
                # dcc.Graph(
                #     id='fig_voltage',
                #     figure=fig
                #     ),        
        
        
                style={'width':'100%',
                        'height':'1000px',
                        'fontSize':'10px',
                        'padding-left':'2%',
                        'padding-right':'2%',
                        'padding-top':'2%',
                        'vertical-align': 'middle',
                        'display':'inline-block'},
            ),

            width=8,
            ),        
        
        ])
    ])

    
    # # Div for title
    # html.Div([
    #     html.H1(children='Human ventricular cardiomyocyte simulator'),
    #     ],
    #     style={'width':'96%',
    #            'height':'40px',
    #            # 'fontSize':'14px',
    #            'padding-left':'2%',
    #            'padding-right':'2%',
    #             'padding-bottom':'20px',
    #             'display':'inline-block',
    #            },        
    #     ),  


    
    # # Loading animation
    # html.Div(
    #     [       
    #     dcc.Loading(
    #         id="loading-anim",
    #         type="circle",
    #         children=html.Div(id="loading-output",
    #                           ),
    #         # color='#2ca02c',
    #     ),
        
    #     ],
    #     style={'width':'96%',
    #            # 'height':'40px',
    #             # 'fontSize':'12px',
    #             'padding-left':'2%',
    #             'padding-right':'2%',
    #             'padding-bottom':'20px',
    #             # 'padding-top':'20px',
    #             'vertical-align': 'middle',
    #             # 'display':'inline-block',
    #             },
            
    # ),    
    
        
    # # Div for sliders
    # html.Div([

    #     # Slider for BCL
    #     html.Label('Pacing cycle length = {}ms'.format(bcl_def),
    #                 id='bcl_slider_text',
    #                 style={'fontSize':14}),   
                   
    #     dcc.Slider(id='bcl_slider',
    #                 min=200, 
    #                 max=4000, 
    #                 step=10, 
    #                 marks=slider_marks_bcl,
    #                 value=bcl_def,
    #     ),
    #     # html.Br(),
    

    #     # Slider for num_beats
    #     html.Label('Number of beats = {}'.format(num_beats_def),
    #                 id='num_beats_slider_text',
    #                 style={'fontSize':14}),   
                   
    #     dcc.Slider(id='num_beats_slider',
    #                 min=1, 
    #                 max=100, 
    #                 step=1, 
    #                 marks=slider_marks_num_beats,
    #                 value=num_beats_def,
    #     ),
    #     # html.Br(),    
    

    #     # Slider for Ina multiplier 
    #     html.Label('INa multiplier = {}'.format(ina_mult_def),
    #                id='ina_slider_text',
    #                style={'fontSize':14}),   
                   
    #     dcc.Slider(id='ina_slider',
    #                min=slider_min, 
    #                max=slider_max, 
    #                step=slider_step, 
    #                marks=slider_marks,
    #                value=ina_mult_def,
    #     ),
    #     # html.Br(),
        
    #     # Slider for ICaL multiplier 
    #     html.Label('ICaL multiplier = {}'.format(ical_mult_def),
    #                id='ical_slider_text',
    #                style={'fontSize':14}),   
                   
    #     dcc.Slider(id='ical_slider',
    #                min=slider_min, 
    #                max=slider_max, 
    #                step=slider_step, 
    #                marks=slider_marks,
    #                value=ical_mult_def,
    #     ),
    #     # html.Br(),      
        
    #     # Slider for IKr multiplier 
    #     html.Label('IKr multiplier = {}'.format(ical_mult_def),
    #                id='ikr_slider_text',
    #                style={'fontSize':14}),   
                   
    #     dcc.Slider(id='ikr_slider',
    #                min=slider_min, 
    #                max=slider_max, 
    #                step=slider_step, 
    #                marks=slider_marks,
    #                value=ikr_mult_def,
    #     ),
    #     # html.Br(),         
        
        
    #     # Slider for IKs multiplier 
    #     html.Label('IKs multiplier = {}'.format(inaca_mult_def),
    #                id='iks_slider_text',
    #                style={'fontSize':14}),   
                   
    #     dcc.Slider(id='iks_slider',
    #                min=slider_min, 
    #                max=slider_max, 
    #                step=slider_step, 
    #                marks=slider_marks,
    #                value=iks_mult_def,
    #     ),
    #     # html.Br(),
        
        
    #     # Slider for INaCa multiplier 
    #     html.Label('INaCa multiplier = {}'.format(inaca_mult_def),
    #                id='inaca_slider_text',
    #                style={'fontSize':14}),   
                   
    #     dcc.Slider(id='inaca_slider',
    #                min=slider_min, 
    #                max=slider_max, 
    #                step=slider_step, 
    #                marks=slider_marks,
    #                value=inaca_mult_def,
    #     ),
    #     # html.Br(), 
        
        
    #     # Slider for Ito multiplier 
    #     html.Label('Ito multiplier = {}'.format(ito_mult_def),
    #                id='ito_slider_text',
    #                style={'fontSize':14}),   
                   
    #     dcc.Slider(id='ito_slider',
    #                min=slider_min, 
    #                max=slider_max, 
    #                step=slider_step, 
    #                marks=slider_marks,
    #                value=ito_mult_def,
    #     ),
        
    #     # html.Br(), 
        
        
    #     # Slider for tjca multiplier
    #     html.Label('tjca multiplier = {}'.format(tjca_mult_def),
    #                id='tjca_slider_text',
    #                style={'fontSize':14}),   
                   
    #     dcc.Slider(id='tjca_slider',
    #                min=slider_min, 
    #                max=slider_max, 
    #                step=slider_step, 
    #                marks=slider_marks,
    #                value=tjca_mult_def,
    #     ),
        

           
    #     # Glossary
    #     dcc.Markdown(
    #         '''
    #         ## Glossary
    #         * **INa**: Sodium current
    #         * **ICaL**: L-type calcium current
    #         * **IKr**: Rapid, delayed rectifier potassium current
    #         * **IKs**: Slow, delayed rectifier potassium current
    #         * **INaCa**: Sodium-calcium exchange current
    #         * **Ito**: Transient outward current
    #         * **tjca**: Relaxation time of L-type Ca current
    #         ''',
    #         style={'fontSize':'14px',
    #                },
    #     ),

    #     ],
        
        
    #     style={'width':'28%',
    #            'height':'1000px',
    #            'fontSize':'10px',
    #            'padding-left':'2%',
    #            'padding-right':'0%',
    #            'padding-bottom':'0px',
    #            'vertical-align': 'middle',
    #            'display':'inline-block'},        
    #     ),
    
    
    
    # # Figure
    # html.Div(
    
    #     dcc.Graph(
    #         id='fig_voltage',
    #         figure=fig
    #         ),        


    #     style={'width':'63%',
    #            'height':'1000px',
    #            'fontSize':'10px',
    #            'padding-left':'5%',
    #            'padding-right':'2%',
    #            'vertical-align': 'middle',
    #            'display':'inline-block'},
    # ),


    # html.Br(),

    # # Footer
    # html.Footer(
    #     [
    #     # 'Created and maintained by ',
    #     # html.A('Thomas Bury',
    #     #        href='http://thomas-bury.research.mcgill.ca/', 
    #     #        target="_blank",
    #     #        ),
    #         'Hosted on the ',
    #     html.A('Digital Research Alliance of Canada',
    #            href='https://alliancecan.ca/en', 
    #            target="_blank",
    #            ),    
    #     '.' 
    #     ],
        
    #     style={'fontSize':'14px',
    #            'width':'100%',
    #            'padding-bottom':'5px',
    #             # 'horizontal-align':'middle',
    #             'textAlign':'center',
    #            },
                
    #     ),]
    

    
app.layout = html.Div([navbar, body_layout])

    
#------------------
# Callback functions
#-------------------



# # Update text for sliders             
# @app.callback([
#                Output('bcl_slider_text','children'),
#                Output('num_beats_slider_text','children'),
#                Output('ina_slider_text','children'),
#                Output('ical_slider_text','children'),
#                Output('ikr_slider_text','children'),
#                Output('inaca_slider_text','children'),
#                Output('iks_slider_text','children'),
#                Output('ito_slider_text','children'),
#                Output('tjca_slider_text','children'),
#                ],
#               [
#                Input('bcl_slider','value'),
#                Input('num_beats_slider','value'),
#                Input('ina_slider','value'),
#                Input('ical_slider','value'),
#                Input('ikr_slider','value'),
#                Input('inaca_slider','value'),
#                Input('iks_slider','value'),
#                Input('ito_slider','value'),
#                Input('tjca_slider','value'),
#                ],

# )

# def update_slider_text(
#         bcl, num_beats,
#         ina_mult,ical_mult,ikr_mult,inaca_mult,
#         iks_mult, ito_mult, tjca_mult):
    
#     # Slider text update
#     text_bcl = 'Pacing cycle length = {}ms'.format(bcl),
#     text_num_beats = 'Number of beats = {}'.format(num_beats),
#     text_ina = 'INa multiplier = {}'.format(ina_mult)
#     text_ical = 'ICaL multiplier = {}'.format(ical_mult)
#     text_ikr = 'IKr multiplier = {}'.format(ikr_mult)
#     text_inaca = 'INaCa multiplier = {}'.format(inaca_mult)
#     text_iks = 'IKs multiplier = {}'.format(iks_mult)
#     text_ito = 'Ito multiplier = {}'.format(ito_mult)
#     text_tjca = 'tjca multiplier = {}'.format(tjca_mult)

#     return text_bcl, text_num_beats, \
#            text_ina, text_ical, text_ikr, text_inaca, text_iks, \
#            text_ito, text_tjca
            
      
        
      
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


if __name__ == '__main__':
    app.run_server(debug=True)





