"""
IOE 410: Airline Crew Assignment Optimization Project
Names: Megan Gottfried, Lukas Mateju
File: utils.py
------------------------------------------------------
Helper functions for results output, file read-in, and visualization
code for optimization model.
"""

import pandas as pd


def load_flights(path):
    return pd.read_csv(path)


def print_solution(model):
    if model.status == 2:
        for v in model.getVars():
            if v.x > 0.5:
                print(v.varName, v.x)
    else:
        print("No optimal solution found.")