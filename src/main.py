"""
IOE 410: Airline Crew Assignment Optimization Project
Names: Megan Gottfried, Lukas Mateju
File: main.py
------------------------------------------------------
Main driver program for optimation model.
"""

import pandas as pd
from model import build_model


def main():

    flights = pd.read_csv("../data/flights.csv")

    model = build_model(flights)
    model.optimize()

    if model.status == 2:
        for v in model.getVars():
            if v.x > 0.5:
                print(v.varName, v.x)


if __name__ == "__main__":
    main()