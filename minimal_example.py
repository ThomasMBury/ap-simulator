#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  5 09:53:18 2021

Minimal example of running myokit

@author: tbury
"""


import myokit

# Get model, protocol and embedded script
m, p, x = myokit.load('mmt_files/example.mmt')


print('Start 0d simulation')
s0 = myokit.Simulation(m, p)
# Pre pacing
s0.pre(10)
# Pacing
d0 = s0.run(10)
print('Complete')


print('Start 1d simualtion')
s1 = myokit.SimulationOpenCL(m, p, ncells=4)
s1.pre(10)
d1 = s1.run(10)
print('Complete')


print('Start 2d simualtion')
s2 = myokit.SimulationOpenCL(m, p, ncells=(4, 4))
s2.pre(10)
d2 = s1.run(10)
print('Complete')






