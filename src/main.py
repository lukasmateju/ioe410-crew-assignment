# IOE 410: Airline Crew Assignment Optimization Project (Megan Gottfried, Lukas Mateju)
"""
**main.py**
------------------------------------------------------
Main driver program for optimation model.
"""

import sys
import sc_model
import utils

# Flight Schedule CSV File and Save Argument Parsing
save_output = "--save" in sys.argv
flight_file = None
for arg in sys.argv[1:]:
    if not arg.startswith("--"):
        flight_file = arg
        break

if flight_file is None:
    sys.exit(1)

# Model Run Function
results = sc_model.run(flight_file)

# If we have infeasable result, exit
if results is None:
    sys.exit(1)


# Data Visualization





if save_output:
    utils.save_output(results)
