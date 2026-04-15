# IOE 410: Airline Crew Assignment Optimization Project (Megan Gottfried, Lukas Mateju)
"""
**utils.py**
------------------------------------------------------
Helper functions for results output, file read-in, and visualization code for optimization model.
"""

import pandas as pd
import os
import sys
import config


def load_flights(filepath):
    F = list(pd.read_csv(filepath, skipinitialspace=True).itertuples(index=False))
    return F
 
 
def load_airports(filepath):
    A = list(pd.read_csv(filepath, skipinitialspace=True).itertuples(index=False))
    return A
 
 
def load_airplanes(filepath):
    P = list(pd.read_csv(filepath, skipinitialspace=True).itertuples(index=False))
    return P
 
 
def fmt_time(minutes):
    m = int(round(minutes))
    return f"{m // 60:02d}:{m % 60:02d}"
 
 
def assign_deadheads(results, flight_file):
    F = load_flights(flight_file)
 
    for atype, result in results["pilots"].items():
        deadheads = []
 
        # go through each pilot route and check if they need a deadhead
        for route, shift in zip(result["Routes"], result["Shifts"]):
            start = route[0].origin
            end = route[-1].destination
            end_time = route[-1].arr_min
            clock_in = shift[0]
            
            if start == end:
                deadheads.append(None)
                continue
 
            # look through all flights for a valid repositioning option
            best = None
            for f in F:
                if f.origin != end or f.destination != start:
                    continue
                if f.dep_min < end_time + config.MIN_TRANSFER_TIME + config.DELAY_BUFFER:
                    continue
                if f.arr_min - clock_in > config.MAX_SHIFT_TIME:
                    continue
                # if f.plane_type != atype:
                #     continue
                if best is None or f.dep_min < best.dep_min:
                    best = f
 
            if best is not None:
                deadheads.append(best)
            else:
                deadheads.append("NO_DEADHEAD")
 
        result["Deadheads"] = deadheads
 
 
def print_section(title, result, label="Crew"):
    print(f"\n  {title}: {result['Count']} crew members")
    print("  " + "-" * 50)
 
    deadheads = result.get("Deadheads", [])
 
    for i, (route, shift) in enumerate(zip(result["Routes"], result["Shifts"]), start=1):
        clock_in, clock_out = shift
        duration = clock_out - clock_in
 
        # print crew member shift info and number of flights
        print(f"    {label} {i:>3d}  "
              f"shift {fmt_time(clock_in)}-{fmt_time(clock_out)}  "
              f"({int(duration)} min)  "
              f"{len(route)} flights")
 
        # print each flight in the route
        for f in route:
            print(f"              {f.flight_id}  {f.origin}->{f.destination}  "
                  f"{fmt_time(f.dep_min)}-{fmt_time(f.arr_min)}  "
                  f"({f.plane_type})")
 
        # Deadhead info (pilots only)
        if i <= len(deadheads):
            dh = deadheads[i - 1]
            if dh is None:
                pass
            elif dh == "NO_DEADHEAD":
                print(f"              No deadhead available "
                      f"({route[-1].destination}->{route[0].origin}) "
                      f"- overnight stay required")
            else:
                print(f"              Deadhead: {dh.flight_id}  "
                      f"{dh.origin}->{dh.destination}  "
                      f"{fmt_time(dh.dep_min)}-{fmt_time(dh.arr_min)}  "
                      f"({dh.plane_type})")
 
 
def print_results(results):
    if results is None:
        return
 
    print()
    print("=" * 60)
    print("  CREW ASSIGNMENT RESULTS")
    print(f"  Schedule:     {results['csv_name']}")
    print(f"  Flights:      {results['num_flights']}")
    print(f"  Total crew:   {results['total_crew']}")
    # print(f"  Config:       shift={config.MAX_SHIFT_TIME}min, transfer={config.MIN_TRANSFER_TIME}min")
    print("=" * 60)
 
    for key, result in results["cabin"].items():
        print_section("CABIN CREW", result, label="Cabin Crew")
 
    for atype in sorted(results["pilots"].keys()):
        print_section(f"PILOTS - {atype}", results["pilots"][atype], label="Pilot")
 
    # summary section
    print()
    print("-" * 60)
    print("  SUMMARY")
    print(f"    Cabin crew:   {results['total_cabin']}")
    for atype in sorted(results["pilots"].keys()):
        print(f"    Pilots ({atype}): {results['pilots'][atype]['Count']}")
    print(f"    Pilots total: {results['total_pilots']}")
    print("    --------------------")
    print(f"    TOTAL CREW:   {results['total_crew']}")
    print("-" * 60)
    print()
 
#def save_output(results):
#    os.makedirs("../output", exist_ok=True)
#    out_path = os.path.join("../output", results['csv_name'] + "_results.txt")
#    
#    with open(out_path, 'w') as f:
#        old_stdout = sys.stdout
#        sys.stdout = f
#        print_results(results)
#        sys.stdout = old_stdout
#    
#    print(f"  Output saved to: {out_path}")