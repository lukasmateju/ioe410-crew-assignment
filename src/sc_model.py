# IOE 410: Airline Crew Assignment Optimization Project (Megan Gottfried, Lukas Mateju)
"""
**sc_model.py**
------------------------------------------------------
Main set cover algoritm modeling functions and gurobi optimation code along with a few additional helper functions.
"""

import networkx as nx
import gurobipy as gurobi

import config
import utils


def build_network(F, transfer_time):
    G = nx.DiGraph()

    G.add_node("s")
    G.add_node("t")

    for i, flight in enumerate(F):
        G.add_node(i, flight=flight)

    for i in range(len(F)):
        G.add_edge("s", i)

        for j in range(len(F)):
            if i != j:
                if (F[i].destination == F[j].origin
                    and F[i].arr_min + transfer_time <= F[j].dep_min):
                    G.add_edge(i, j)

        G.add_edge(i, "t")

    return G

def build_model(F, G, max_shift, model_name="CrewAssignment"):
    m = gurobi.Model(model_name)
    H = max_shift

    # Arc variables x[(i,j)] for every edge in G
    x = {}
    for (i, j) in G.edges():
        x[(i, j)] = m.addVar(vtype=gurobi.GRB.BINARY, name=f"x_{i}_{j}")

    # Shift start variables S[i] for every flight node
    S = m.addVars(range(len(F)), lb=0.0, vtype=gurobi.GRB.CONTINUOUS, name="S")

    # Flow balance constraint
    for i in range(len(F)):
        m.addConstr(gurobi.quicksum(x[(u, i)] for u in G.predecessors(i)) == 1,
                    name=f"flow_in_{i}")
        m.addConstr(gurobi.quicksum(x[(i, v)] for v in G.successors(i)) == 1,
                    name=f"flow_out_{i}")

    # Shift start initialization constraint
    for i in range(len(F)):
        d_i = G.nodes[i]['flight'].dep_min
        m.addConstr(S[i] <= d_i + H * (1 - x[("s", i)]), name=f"sinit_ub_{i}")
        m.addConstr(S[i] >= d_i - H * (1 - x[("s", i)]), name=f"sinit_lb_{i}")

    # Shift start propagation constraint
    for (i, j) in G.edges():
        if i != "s" and j != "t":
            m.addConstr(S[j] <= S[i] + H * (1 - x[(i, j)]), name=f"sprop_ub_{i}_{j}")
            m.addConstr(S[j] >= S[i] - H * (1 - x[(i, j)]), name=f"sprop_lb_{i}_{j}")

    # Maximum shift duration constraint
    for i in range(len(F)):
        a_i = G.nodes[i]['flight'].arr_min
        m.addConstr(a_i - S[i] <= H, name=f"shift_limit_{i}")

    # Objective: minimize number of crew (source arcs used)
    m.setObjective(
        gurobi.quicksum(x[("s", i)] for i in range(len(F))),
        gurobi.GRB.MINIMIZE
    )

    return m, x, S

def solve_cabin_crew(F):
    transfer_time = config.MIN_TRANSFER_TIME + config.DELAY_BUFFER

    G = build_network(F, transfer_time)
    m, x, S = build_model(F, G, config.MAX_SHIFT_TIME, model_name="CabinCrew")
    m.optimize()

    return m, F, G, x, S
    
def solve_pilots(F, P):
    transfer_time = config.MIN_TRANSFER_TIME + config.DELAY_BUFFER
    results = {}

    # Get set of aircraft types that actually appear in the flight schedule
    types_in_schedule = set(f.plane_type for f in F)

    for aircraft_type in types_in_schedule:
        # Filter flights to only this aircraft type
        F_q = [f for f in F if f.plane_type == aircraft_type]

        if len(F_q) == 0:
            continue

        G_q = build_network(F_q, transfer_time)
        m, x, S = build_model(F_q, G_q, config.MAX_SHIFT_TIME,
                              model_name=f"Pilots_{aircraft_type}")
        m.optimize()

        results[aircraft_type] = (m, F_q, G_q, x, S)

    return results

def run(show_crew_count, show_routes, show_shift_times, save_output, flight_file=None):
    F = utils.load_flights(flight_file or config.IN_FLIGHTS)

    # --- Cabin Crew ---
    print("=" * 50)
    print("CABIN CREW MODEL")
    print("=" * 50)

    cabin_m, cabin_F, cabin_G, cabin_x, cabin_S = solve_cabin_crew(F)

    if cabin_m.status == gurobi.GRB.INFEASIBLE:
        print("INFEASIBLE - Computing IIS...")
        cabin_m.computeIIS()
        for c in cabin_m.getConstrs():
            if c.IISConstr:
                print(f"  {c.ConstrName}")
    elif cabin_m.status == gurobi.GRB.OPTIMAL:
        if show_crew_count:
            utils.print_crew_count(cabin_m)
        if show_routes:
            utils.print_routes(cabin_F, cabin_G, cabin_x)
        if show_shift_times:
            utils.print_shift_times(cabin_F, cabin_S)
    else:
        print("No optimal solution found. Status:", cabin_m.status)

    # --- Pilots ---
    if config.SOLVE_PILOTS:
        P = utils.load_airplanes(config.IN_AIRPLANES)

        print("\n" + "=" * 50)
        print("PILOT MODELS")
        print("=" * 50)

        pilot_results = solve_pilots(F, P)
        total_pilots = 0

        for aircraft_type, (m, F_q, G_q, x, S) in pilot_results.items():
            print(f"\n--- {aircraft_type} ---")

            if m.status == gurobi.GRB.INFEASIBLE:
                print(f"  INFEASIBLE - Computing IIS...")
                m.computeIIS()
                for c in m.getConstrs():
                    if c.IISConstr:
                        print(f"    {c.ConstrName}")
            elif m.status == gurobi.GRB.OPTIMAL:
                total_pilots += int(m.objVal)
                if show_crew_count:
                    print(f"  Pilots needed: {int(m.objVal)}")
                if show_routes:
                    utils.print_routes(F_q, G_q, x)
                if show_shift_times:
                    utils.print_shift_times(F_q, S)
            else:
                print(f"  No optimal solution found. Status: {m.status}")

        if show_crew_count:
            print(f"\nTotal pilots across all types: {total_pilots}")

    # --- Summary ---
    if show_crew_count and config.SOLVE_PILOTS:
        if cabin_m.status == gurobi.GRB.OPTIMAL:
            print("\n" + "=" * 50)
            print(f"TOTAL CREW: {int(cabin_m.objVal) + total_pilots}")
            print(f"  Cabin crew: {int(cabin_m.objVal)}")
            print(f"  Pilots:     {total_pilots}")
            print("=" * 50)
