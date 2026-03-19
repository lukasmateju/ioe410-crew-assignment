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
import argparse
import csv
import math
import os

# Load data
airports = pd.read_csv("airports.csv", skipinitialspace=True)
airports.columns = airports.columns.str.strip()
airports['airport_id'] = airports['airport_id'].str.strip()

planes = pd.read_csv("airplanes.csv", skipinitialspace=True)
planes.columns = planes.columns.str.strip()
planes['aircraft_id'] = planes['aircraft_id'].str.strip()
PLANE_SPEED = 550  # mph, same for all planes


def calcDistance(latDepart, lonDepart, latArrive, lonArrive):
    R = 3958.8
    lat1, lon1 = math.radians(latDepart), math.radians(lonDepart)
    lat2, lon2 = math.radians(latArrive), math.radians(lonArrive)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return int(round(3958.8 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))))


def save_schedule(schedule, folder, filename):
    os.makedirs(folder, exist_ok=True)
    if not filename.lower().endswith(".csv"):
        filename += ".csv"
    file_path = os.path.join(folder, filename)
    fieldnames = ["flight_id", "plane_type", "origin", "destination",
                  "dep_min", "arr_min", "distance_mi", "duration"]
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for flight in schedule:
            writer.writerow(flight)
    print(f"Flight schedule saved to: {file_path}")


def generate_flight_schedule(num_flights, start_time, end_time, use_all_airports, use_all_airplanes, airports_used, planes_used):
    schedule = []
    available_airports = airports['airport_id'].tolist() if use_all_airports else airports_used
    available_planes = planes['aircraft_id'].tolist() if use_all_airplanes else planes_used

    for i in range(num_flights):
        origin = random.choice(available_airports)
        destination = random.choice([a for a in available_airports if a != origin])
        plane = random.choice(available_planes)

        origin_row = airports[airports['airport_id'] == origin].iloc[0]
        dest_row = airports[airports['airport_id'] == destination].iloc[0]

        distance = calcDistance(
            float(origin_row['loc_x']), float(origin_row['loc_y']),
            float(dest_row['loc_x']), float(dest_row['loc_y'])
        )

        duration_min = int(round(distance / PLANE_SPEED * 60))
        dep_min = random.randint(start_time, end_time - duration_min)
        arr_min = dep_min + duration_min
        
        if duration_min > 660:
            continue

        if arr_min > 1440:
            continue

        schedule.append({
            "flight_id": f"F{i+1:03}",
            "plane_type": plane,
            "origin": origin,
            "destination": destination,
            "dep_min": dep_min,
            "arr_min": arr_min,
            "distance_mi": distance,
            "duration": duration_min
        })

    schedule.sort(key=lambda x: x['dep_min'])
    for i, flight in enumerate(schedule):
        flight['flight_id'] = f"F{i+1:03}"

    return schedule


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate random flight schedules")
    parser.add_argument("--flights",    type=int,   default=10,                  help="Number of flights")
    parser.add_argument("--start",      type=int,   default=0,                   help="Start time (minutes)")
    parser.add_argument("--end",        type=int,   default=1440,                help="End time (minutes)")
    parser.add_argument("--output",     type=str,   default="F02-randomtest.csv", help="Output filename")
    parser.add_argument("--all-airports", action="store_true",                   help="Use all airports")
    parser.add_argument("--all-planes",   action="store_true",                   help="Use all plane types")
    args = parser.parse_args()

    schedule = generate_flight_schedule(
        num_flights=args.flights,
        start_time=args.start,
        end_time=args.end,
        use_all_airports=args.all_airports,
        use_all_airplanes=args.all_planes,
        airports_used=["DFW", "ORD", "DTW", "LAX", "JFK"],
        planes_used=["B737"]
    )

    save_schedule(schedule, "flight-schedules", args.output)