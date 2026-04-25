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
show_viz = "--viz" in sys.argv
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

# Data Output and Visualization
#utils.assign_deadheads(results, flight_file)

utils.print_results(results, show_viz=show_viz)

if save_output:
    utils.save_output(results, show_viz=show_viz)
