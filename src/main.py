# IOE 410: Airline Crew Assignment Optimization Project (Megan Gottfried, Lukas Mateju)
"""
**main.py**
------------------------------------------------------
Main driver program for optimation model.
"""

#import pandas as pd

#import utils
#import config
import sys
import sc_model

# --- Output toggles ---
SHOW_CREW_COUNT  = True
SHOW_ROUTES      = True
SHOW_SHIFT_TIMES = False
SAVE_OUTPUT      = "--save" in sys.argv


# --- Run ---
sc_model.run(SHOW_CREW_COUNT, SHOW_ROUTES, SHOW_SHIFT_TIMES, SAVE_OUTPUT)



#def main():
#
#    flights = pd.read_csv("../data/flights.csv")
#
#    model = build_model(flights)
#    model.optimize()
#
#    if model.status == 2:
#        for v in model.getVars():
#            if v.x > 0.5:
#                print(v.varName, v.x)
