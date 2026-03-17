# IOE 410: Airline Crew Assignment Optimization Project (Megan Gottfried, Lukas Mateju)
"""
**utils.py**
------------------------------------------------------
Helper functions for results output, file read-in, and visualization code for optimization model.
"""

import pandas as pd
import os
import tarfile
import datetime
import io
import config

def load_flights(filepath: str):
    F = list(pd.read_csv(filepath, skipinitialspace=True).itertuples(index=False))
    return F

def load_airports(filepath: str):
    A = list(pd.read_csv(filepath, skipinitialspace=True).itertuples(index=False))
    return A

def load_airplanes(filepath: str):
    P = list(pd.read_csv(filepath, skipinitialspace=True).itertuples(index=False))
    return P

def print_crew_count(m):
    print("\n--- Crew Count ---")
    print(f"Minimum crew needed: {int(m.objVal)}")

def print_routes(F, G, x):
    print("\n--- Crew Routes ---")
    crew = 1
    for i in range(len(F)):
        if x[("s", i)].X > 0.5:
            route = []
            current = i
            while current != "t":
                flight = G.nodes[current]['flight']
                route.append(f"{flight.flight_id} ({flight.origin} -> {flight.destination}, dep:{flight.dep_min}, arr:{flight.arr_min})")
                for v in G.successors(current):
                    if x[(current, v)].X > 0.5:
                        current = v
                        break
            print(f"Crew {crew}: {' | '.join(route)}")
            crew += 1

def print_shift_times(F, S):
    print("\n--- Shift Times ---")
    for i in range(len(F)):
        if S[i].X > 0:
            flight = F[i]
            print(f"Flight {flight.flight_id}: clock-in {S[i].X} min, shift end {flight.arr_min} min, duration {flight.arr_min - S[i].X} min")
            
def save_output(m, F, G, x, S, show_routes, show_shift_times):
    # --- Build run name from date and CSV filename ---
    date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    csv_name = os.path.splitext(os.path.basename(config.IN_FLIGHTS))[0]
    run_name = f"{date}_{csv_name}"
    archive_path = f"../output/{run_name}.tar.gz"

    # --- Create output folder if it doesn't exist ---
    os.makedirs("../output", exist_ok=True)

    # --- Build results.txt in memory ---
    results = io.StringIO()
    results.write(f"Minimum crew needed: {int(m.objVal)}\n")
    if show_routes:
        results.write("\n--- Crew Routes ---\n")
        crew = 1
        for i in range(len(F)):
            if x[("s", i)].X > 0.5:
                route = []
                current = i
                while current != "t":
                    flight = G.nodes[current]['flight']
                    route.append(f"{flight.flight_id} ({flight.origin} -> {flight.destination},"
                                 f" dep:{flight.dep_min}, arr:{flight.arr_min})")
                    for v in G.successors(current):
                        if x[(current, v)].X > 0.5:
                            current = v
                            break
                results.write(f"Crew {crew}: {' | '.join(route)}\n")
                crew += 1
    if show_shift_times:
        results.write("\n--- Shift Times ---\n")
        for i in range(len(F)):
            if S[i].X > 0:
                flight = F[i]
                results.write(f"Flight {flight.flight_id}: clock-in {S[i].X} min,"
                              f" shift end {flight.arr_min} min,"
                              f" duration {flight.arr_min - S[i].X} min\n")

    # --- Build config.txt in memory ---
    cfg = io.StringIO()
    cfg.write(f"IN_FLIGHTS:            {config.IN_FLIGHTS}\n")
    cfg.write(f"MAX_SHIFT_HOURS:       {config.MAX_SHIFT_HOURS}\n")
    cfg.write(f"MIN_TRANSFER_TIME:     {config.MIN_TRANSFER_TIME}\n")
    cfg.write(f"ENFORCE_SAME_START_END:{config.ENFORCE_SAME_START_END}\n")
    cfg.write(f"MULTIPLE_AIRPLANE_TYPES:{config.MULTIPLE_AIRPLANE_TYPES}\n")

    # --- Write tar.gz archive ---
    with tarfile.open(archive_path, "w:gz") as tar:
        for filename, content in [("results.txt", results), ("config.txt", cfg)]:
            encoded = content.getvalue().encode("utf-8")
            info = tarfile.TarInfo(name=filename)
            info.size = len(encoded)
            tar.addfile(info, io.BytesIO(encoded))

        # model.lp — write to temp file then add to archive
        m.write("/tmp/model.lp")
        tar.add("/tmp/model.lp", arcname="model.lp")

    print(f"\nOutput saved to: {archive_path}")
