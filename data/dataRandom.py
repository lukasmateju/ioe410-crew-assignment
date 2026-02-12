"""
IOE 410: Airline Crew Assignment Optimization Project
Names: Megan Gottfried, Lukas Mateju
File: dataRandom.py
------------------------------------------------------
Helper program that generates flight schedules for use
in optimization model.
"""

import pandas as pd
import random
import csv
import math
import os

# Load data
airports = pd.read_csv("airports.csv")
planes = pd.read_csv("airplanes.csv")

# ----------------------------
# Schedule Configuration
# ----------------------------
USE_ALL_AIRPORTS = False
USE_ALL_AIRPLANES = False
aUsed = ["DFW", "ORD", "DTW", "LAX", "JFK"]
pUsed = ["B737"]

NUM_FLIGHTS = 10
START_TIME = 0
END_TIME = 1440
OUTPUT_FOLDER = "flight-schedules"
OUTPUT_FILE_NAME = "F02-randomtest.csv"

# ----------------------------
# Calculation and Helper Functions
# ----------------------------
def calcDistance(latDepart, lonDepart, latArrive, lonArrive):
    # Radius of the Earth in miles
    R = 3958.8

    # Convert decimal degrees to radians
    lat1 = math.radians(latDepart)
    lon1 = math.radians(lonDepart)
    lat2 = math.radians(latArrive)
    lon2 = math.radians(lonArrive)

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c

    return int(round(distance))  # Return as integer miles

def save_schedule(schedule, folder, filename):
    os.makedirs(folder, exist_ok=True)
    
    # Ensure filename ends with .csv
    if not filename.lower().endswith(".csv"):
        filename += ".csv"
    
    file_path = os.path.join(folder, filename)
    
    fieldnames = ["flight_id", "plane_type", "origin", "destination", "dep_min", "arr_min", "distance_mi", "duration"]
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for flight in schedule:
            writer.writerow(flight)
    print(f"Flight schedule saved to: {file_path}")

# ----------------------------
# Flight schedule generator
# ----------------------------
def generate_flight_schedule(num_flights, start_time, end_time):
    schedule = []

    # Airports and planes
    available_airports = airports['airport_id'].tolist() if USE_ALL_AIRPORTS else aUsed
    available_planes = planes['aircraft_id'].tolist() if USE_ALL_AIRPLANES else pUsed

    PLANE_SPEED = 550  # mph, same for all planes

    for i in range(num_flights):
        origin = random.choice(available_airports)
        destination = random.choice([a for a in available_airports if a != origin])
        plane = random.choice(available_planes)

        # Get lat/lon from airports.csv
        origin_row = airports[airports['airport_id'] == origin].iloc[0]
        dest_row = airports[airports['airport_id'] == destination].iloc[0]

        distance = calcDistance(
            float(origin_row['loc_x']),
            float(origin_row['loc_y']),
            float(dest_row['loc_x']),
            float(dest_row['loc_y'])
        )

        duration_min = int(round(distance / PLANE_SPEED * 60))  # minutes

        # Random departure time within schedule window
        dep_min = random.randint(start_time, end_time - duration_min)
        arr_min = dep_min + duration_min

        flight = {
            "flight_id": f"F{i+1:03}",
            "plane_type": plane,
            "origin": origin,
            "destination": destination,
            "dep_min": dep_min,
            "arr_min": arr_min,
            "distance_mi": distance,
            "duration": duration_min
        }

        schedule.append(flight)

    return schedule

# ----------------------------
# Function Calls
# ----------------------------
flight_schedule = generate_flight_schedule(NUM_FLIGHTS, START_TIME, END_TIME)

# --- SORT BY DEPARTURE TIME AND UPDATE FLIGHT IDS ---
flight_schedule.sort(key=lambda x: x['dep_min'])  # Sort flights by departure time
for i, flight in enumerate(flight_schedule):
    flight['flight_id'] = f"F{i+1:03}"           # Reassign flight IDs in order

save_schedule(flight_schedule, OUTPUT_FOLDER, OUTPUT_FILE_NAME)