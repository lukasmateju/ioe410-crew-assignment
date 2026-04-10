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


def fmt_time(minutes):
    m = int(round(minutes))
    return f"{m // 60:02d}:{m % 60:02d}"


def fmt_duration(minutes):
    m = int(round(minutes))
    h, r = divmod(m, 60)
    
    if h > 0 and r > 0:
        return f"{h}h {r}m"
    elif h > 0:
        return f"{h}h"
    else:
        return f"{r}m"


# ── Deadhead Assignment (Post-Processing) ───────────────

def assign_deadheads(results, flight_file):
    F = load_flights(flight_file)
    transfer_time = config.MIN_TRANSFER_TIME + config.DELAY_BUFFER
    max_shift = config.MAX_SHIFT_TIME

    for atype, result in results["pilots"].items():
        deadheads = []

        for route, shift in zip(result["Routes"], result["Shifts"]):
            start_airport = route[0].origin
            end_airport = route[-1].destination
            end_time = route[-1].arr_min
            clock_in = shift[0]

            # Already ends where they started
            if start_airport == end_airport:
                deadheads.append(None)
                continue

            # Search full schedule for earliest valid repositioning flight
            earliest_dep = end_time + transfer_time

            best = None
            for f in F:
                if (f.origin == end_airport
                        and f.destination == start_airport
                        and f.dep_min >= earliest_dep):

                    # Check that deadhead arrival doesn't exceed max shift
                    deadhead_duration = f.arr_min - clock_in
                    if deadhead_duration > max_shift:
                        continue

                    # Pick the earliest valid option
                    if best is None or f.dep_min < best.dep_min:
                        best = f

            if best is not None:
                deadheads.append(best)
            else:
                deadheads.append("NO_DEADHEAD")

        result["Deadheads"] = deadheads


def print_section(title, result, label="Crew"):
    print(f"\n  {title}: {result['Count']} crew members")
    print("  " + "─" * 50)

    deadheads = result.get("Deadheads", [])

    for i, (route, shift) in enumerate(zip(result["Routes"], result["Shifts"]), start=1):
        clock_in, clock_out = shift
        duration = clock_out - clock_in

        print(f"    {label} {i:>3d}  "
              f"shift {fmt_time(clock_in)}–{fmt_time(clock_out)}  "
              f"({fmt_duration(duration)})  "
              f"{len(route)} flight{'s' if len(route) != 1 else ''}")

        for f in route:
            print(f"              {f.flight_id}  {f.origin}→{f.destination}  "
                  f"{fmt_time(f.dep_min)}–{fmt_time(f.arr_min)}  "
                  f"({f.plane_type})")

        # Deadhead info (pilots only)
        if i <= len(deadheads):
            dh = deadheads[i - 1]
            if dh is None:
                pass  # ends at start airport, no deadhead needed
            elif dh == "NO_DEADHEAD":
                print(f"              ⚠ No deadhead available "
                      f"({route[-1].destination}→{route[0].origin}) "
                      f"— overnight stay required")
            else:
                print(f"              ↩ Deadhead: {dh.flight_id}  "
                      f"{dh.origin}→{dh.destination}  "
                      f"{fmt_time(dh.dep_min)}–{fmt_time(dh.arr_min)}  "
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
    print("=" * 60)

    # Cabin crew
    for key, result in results["cabin"].items():
        print_section("CABIN CREW", result, label="Cabin Crew")

    # Pilots by type
    for atype in sorted(results["pilots"].keys()):
        print_section(f"PILOTS — {atype}", results["pilots"][atype], label="Pilot")

    # Summary
    print()
    print("─" * 60)
    print("  SUMMARY")
    print(f"    Cabin crew:   {results['total_cabin']}")
    for atype in sorted(results["pilots"].keys()):
        print(f"    Pilots ({atype}): {results['pilots'][atype]['Count']}")
    print(f"    Pilots total: {results['total_pilots']}")
    print("    ────────────────────")
    print(f"    TOTAL CREW:   {results['total_crew']}")
    print("─" * 60)
    print()

def save_output(results):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    run_name = f"{timestamp}_{results['csv_name']}"
    archive_path = os.path.join("..", "output", f"{run_name}.tar.gz")

    os.makedirs("../output", exist_ok=True)

    # ── results.txt in memory ───────────────────────
    results_buf = io.StringIO()
    results_buf.write(f"Schedule: {results['csv_name']}\n")
    results_buf.write(f"Flights:  {results['num_flights']}\n")
    results_buf.write(f"Total crew: {results['total_crew']}\n")
    results_buf.write(f"  Cabin crew:   {results['total_cabin']}\n")
    for atype in sorted(results["pilots"].keys()):
        results_buf.write(f"  Pilots ({atype}): {results['pilots'][atype]['Count']}\n")
    results_buf.write(f"  Pilots total: {results['total_pilots']}\n")

    for key, result in results["cabin"].items():
        results_buf.write(f"\nCABIN CREW: {result['Count']} crew members\n")
        write_section(results_buf, result)

    for atype in sorted(results["pilots"].keys()):
        result = results["pilots"][atype]
        results_buf.write(f"\nPILOTS — {atype}: {result['Count']} crew members\n")
        write_section(results_buf, result)

    # ── config.txt in memory ────────────────────────
    config_buf = io.StringIO()
    config_buf.write(f"Schedule:                      {results['csv_name']}\n")
    config_buf.write(f"MAX_SHIFT_TIME:                {config.MAX_SHIFT_TIME} min\n")
    config_buf.write(f"MIN_TRANSFER_TIME:             {config.MIN_TRANSFER_TIME} min\n")
    config_buf.write(f"DELAY_BUFFER:                  {config.DELAY_BUFFER} min\n")
    config_buf.write(f"CALLOUT_RATE:                  {config.CALLOUT_RATE}\n")
    config_buf.write(f"SOLVE_PILOTS:                  {config.SOLVE_PILOTS}\n")
    config_buf.write(f"ENFORCE_SAME_START_END_CABIN:   {config.ENFORCE_SAME_START_END_CABIN}\n")
    config_buf.write(f"ENFORCE_SAME_START_END_PILOTS:  {config.ENFORCE_SAME_START_END_PILOTS}\n")

    # ── Write tar.gz archive ────────────────────────
    with tarfile.open(archive_path, "w:gz") as tar:
        for filename, buf in [("results.txt", results_buf), ("config.txt", config_buf)]:
            encoded = buf.getvalue().encode("utf-8")
            info = tarfile.TarInfo(name=filename)
            info.size = len(encoded)
            tar.addfile(info, io.BytesIO(encoded))

    print(f"  Output saved to: {archive_path}")

def write_section(f, result, label="Crew"):
    deadheads = result.get("Deadheads", [])

    for i, (route, shift) in enumerate(zip(result["Routes"], result["Shifts"]), start=1):
        clock_in, clock_out = shift
        duration = clock_out - clock_in

        legs = " | ".join(
            f"{fl.flight_id} {fl.origin}→{fl.destination} "
            f"{fmt_time(fl.dep_min)}–{fmt_time(fl.arr_min)}"
            for fl in route
        )
        f.write(f"  {label} {i}: shift {fmt_time(clock_in)}–{fmt_time(clock_out)} "
                f"({fmt_duration(duration)}) — {legs}\n")

        if i <= len(deadheads):
            dh = deadheads[i - 1]
            if dh == "NO_DEADHEAD":
                f.write(f"    ⚠ No deadhead available "
                        f"({route[-1].destination}→{route[0].origin}) "
                        f"— overnight stay required\n")
            elif dh is not None:
                f.write(f"    ↩ Deadhead: {dh.flight_id} "
                        f"{dh.origin}→{dh.destination} "
                        f"{fmt_time(dh.dep_min)}–{fmt_time(dh.arr_min)}\n")