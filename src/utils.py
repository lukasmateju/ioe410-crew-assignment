# IOE 410: Airline Crew Assignment Optimization Project (Megan Gottfried, Lukas Mateju)
"""
**utils.py**
------------------------------------------------------
Helper functions for results output, file read-in, and visualization code for optimization model.
"""

import pandas as pd
import os
from contextlib import redirect_stdout
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
 
 
def print_results(results, show_viz=False):
    if results is None:
        return
 
    print()
    print("=" * 60)
    print("  CREW ASSIGNMENT RESULTS")
    print(f"  Schedule:     {results['csv_name']}")
    print(f"  Flights:      {results['num_flights']}")
    print(f"  Total crew:   {results['total_crew']}")
    print(f"  Solver:       {solver_summary(results)}")
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

    if show_viz:
        print_cli_visualizations(results)

    print()
 

def solver_summary(results):
    backends = set()

    for result in results["cabin"].values():
        backends.add(result["solver"].backend)

    for result in results["pilots"].values():
        backends.add(result["solver"].backend)

    return ", ".join(sorted(backends))


def save_output(results, show_viz=False):
    os.makedirs("../output", exist_ok=True)
    out_path = os.path.join("../output", results['csv_name'] + "_results.txt")

    with open(out_path, 'w') as f:
        with redirect_stdout(f):
            print_results(results, show_viz=show_viz)

    print(f"  Output saved to: {out_path}")


def print_cli_visualizations(results):
    print()
    print("-" * 60)
    print("  QUICK VISUALS")
    print("-" * 60)
    print_crew_mix_chart(results)
    print_route_length_chart(results)
    print_airport_flow_chart(results)


def print_crew_mix_chart(results):
    values = [("Cabin", results["total_cabin"])]

    for atype in sorted(results["pilots"].keys()):
        values.append((f"Pilot {atype.strip()}", results["pilots"][atype]["Count"]))

    print("\n  Crew by group")
    print_bar_chart(values)


def print_route_length_chart(results):
    buckets = {}

    for label, result in iter_result_groups(results):
        route_lengths = [len(route) for route in result["Routes"]]
        if route_lengths:
            buckets[label] = sum(route_lengths) / len(route_lengths)

    print("\n  Average flights per route")
    print_bar_chart([(label, value) for label, value in buckets.items()], width=24, precision=1)


def print_airport_flow_chart(results):
    flow_counts = {}

    for _, result in iter_result_groups(results):
        for route in result["Routes"]:
            for flight in route:
                key = f"{flight.origin.strip()}->{flight.destination.strip()}"
                flow_counts[key] = flow_counts.get(key, 0) + 1

    top_flows = sorted(flow_counts.items(), key=lambda item: (-item[1], item[0]))[:8]

    print("\n  Busiest crew-covered flight legs")
    print_bar_chart(top_flows, width=24)


def print_bar_chart(values, width=28, precision=0):
    if not values:
        print("    No data")
        return

    max_value = max(value for _, value in values)
    if max_value <= 0:
        max_value = 1

    label_width = min(max(len(label) for label, _ in values), 22)

    for label, value in values:
        bar_len = int(round((value / max_value) * width))
        bar = "#" * max(1, bar_len)
        if precision == 0:
            value_text = str(int(round(value)))
        else:
            value_text = f"{value:.{precision}f}"
        print(f"    {label[:label_width]:<{label_width}} | {bar:<{width}} {value_text}")


def iter_result_groups(results):
    for result in results["cabin"].values():
        yield "Cabin", result

    for atype in sorted(results["pilots"].keys()):
        yield f"Pilot {atype.strip()}", results["pilots"][atype]
