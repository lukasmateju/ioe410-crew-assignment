# IOE 410: Airline Crew Assignment Optimization Project (Megan Gottfried, Lukas Mateju)
"""
**config.py**
------------------------------------------------------
Global configuration parameters for the crew assignment model. All modafiable variables and input files are set and changed here.
"""

# Input Files
IN_FLIGHTS   = "../data/flight-schedules/F01-simple.csv"
IN_AIRPORTS  = "../data/airports.csv"
IN_AIRPLANES = "../data/airplanes.csv"

# Core Constraints
MAX_SHIFT_TIME = 11 * 60
MIN_TRANSFER_TIME = 1 * 60

# Model Settings
ALLOW_DEADHEADS = False
ENFORCE_SAME_START_END_CABIN = True
ENFORCE_SAME_START_END_PILOTS = True

# Redundancy Buffer Multipliers
CALLOUT_RATE = 0.05
DELAY_BUFFER = 15

# Solver Settings
SOLVER_BACKEND = "auto"  # auto, gurobi, scipy
TIME_LIMIT = 120
MIP_GAP = 0.075

# Other restriction ideas
#  - Mandatory crew breaks (30 extra minutes without flight during shift)
#  - Balanced workload (Each crew member needs x number of hours at a minimum to be scheduled)
#  - Multiday schedule (Add in international and overnight flights with additional crew restrictions)
