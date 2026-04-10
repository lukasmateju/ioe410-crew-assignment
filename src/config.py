# IOE 410: Airline Crew Assignment Optimization Project (Megan Gottfried, Lukas Mateju)
"""
**config.py**
------------------------------------------------------
Global configuration parameters for the crew assignment model. All modafiable variables and input files are set and changed here.
"""

# Input Files
IN_FLIGHTS   = "../data/flight-schedules/F03-largerandom.csv"
IN_AIRPORTS  = "../data/flight-schedules/airports.csv"
IN_AIRPLANES = "../data/flight-schedules/airplanes.csv"

# Core Constraints
MAX_SHIFT_TIME = 11 * 60
MIN_TRANSFER_TIME = 1 * 60

# Model Settings
SOLVE_PILOTS = True
ALLOW_DEADHEADS = False
ENFORCE_SAME_START_END_CABIN = False
ENFORCE_SAME_START_END_PILOTS = False

# Redundancy Buffer Multipliers
CALLOUT_RATE = 0.0
DELAY_BUFFER = 0

# Other restriction ideas
#  - Mandatory crew breaks (30 extra minutes without flight during shift)
#  - Balanced workload (Each crew member needs x number of hours at a minimum to be scheduled)
#  - Multiday schedule (Add in international and overnight flights with additional crew restrictions)