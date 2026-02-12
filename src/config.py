"""
IOE 410: Airline Crew Assignment Optimization Project
Names: Megan Gottfried, Lukas Mateju
File: config.py
------------------------------------------------------
Global configuration parameters for the crew assignment model. All
modafiable variables and input files are set and changed here.
"""

# Input Files
IN_FLIGHTS = "dummy_file.csv"
IN_AIRPORTS = "dummy_file.csv"
IN_AIRPLANES = "dummy_file.csv"

# Crew Behavior Settings
MAX_SHIFT_HOURS = 11
MIN_TRANSFER_TIME = 1
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

