# IOE 410: Airline Crew Assignment Optimization Project (Megan Gottfried, Lukas Mateju)
"""
**config.py**
------------------------------------------------------
Global configuration parameters for the crew assignment model. All modafiable variables and input files are set and changed here.
"""

# Input Files
IN_FLIGHTS   = "../data/flight-schedules/F01-simple.csv"
IN_AIRPORTS  = "../data/flight-schedules/airports.csv"
IN_AIRPLANES = "../data/flight-schedules/airplanes.csv"

# Crew Behavior Settings
MAX_SHIFT_HOURS = 11 * 60
MIN_TRANSFER_TIME = 1 * 60
ENFORCE_SAME_START_END = False
MULTIPLE_AIRPLANE_TYPES = False
MULTIPLE_CREW_TYPES = False
# Other restriction ideas
#  - Mandatory crew breaks (30 extra minutes without flight during shift)
#  - Pilot certification restrictions (If using multiple crew types, pilots can only operate x types of planes)
#  - Crew redundancy (If there will x number of crew that have to miss their shift, how many should be scheduled to avoid issues, ie. overload flight crews)
#  - Balanced workload (Each crew member needs x number of hours at a minimum to be scheduled)
#  - Allow deadheads (Crew members can fly be on flights without working to get back to orgional airport)
#  - Multiday schedule (Add in international and overnight flights with additional crew restrictions)

