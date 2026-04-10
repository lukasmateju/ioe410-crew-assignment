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

# --- Flight schedule (first non-flag argument, or config default) ---
flight_file = None
for arg in sys.argv[1:]:
    if not arg.startswith("--"):
        flight_file = arg
        break

# --- Run ---
sc_model.run(SHOW_CREW_COUNT, SHOW_ROUTES, SHOW_SHIFT_TIMES, SAVE_OUTPUT, flight_file=flight_file)


# --- Data Visualization ---


