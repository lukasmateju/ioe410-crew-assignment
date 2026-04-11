# IOE 410: Airline Crew Assignment Optimization Project (Megan Gottfried, Lukas Mateju)
"""
**sc_model.py**
------------------------------------------------------
Main set cover algoritm modeling functions and gurobi optimation code along with a few additional helper functions.
"""

import os
import math
import networkx as nx
import gurobipy as gurobi

import config
import utils

def build_network(F, transfer_time, slots_per_flight, enforce_same_start_end):
    G = nx.DiGraph()
    
    airports = set()
    for f in F:
        airports.add(f.origin)
        airports.add(f.destination)
        
    # TO-DO add in start end flagging code
    if enforce_same_start_end:
        for a in airports:
            G.add_node(("s", a))
            G.add_node(("t", a))
    else:
        G.add_node("s")
        G.add_node("t")

    for i, flight in enumerate(F):
        r_i = slots_per_flight[i]
        
        for k in range(r_i):
            G.add_node((i, k), flight=flight, flight_idx=i, slot_idx=k)

    for i in range(len(F)):
        r_i = slots_per_flight[i]
        
        for k in range(r_i):
            if enforce_same_start_end:
                G.add_edge(("s", F[i].origin), (i, k))
            else:
                G.add_edge("s", (i, k))

            for j in range(len(F)):
                # Arc does not start and end with the same flight
                if i != j:
                    # Destination airport of flight i is the same as the origin airport of flight j
                    # There is enough time to transfer from flight i to flight j
                    if (F[i].destination == F[j].origin and F[i].arr_min + transfer_time <= F[j].dep_min):
                        r_j = slots_per_flight[j]
                        
                        for sl in range(r_j):
                            G.add_edge((i, k), (j, sl))

            if enforce_same_start_end:
                G.add_edge((i, k), ("t", F[i].destination))
            else:
                G.add_edge((i, k), "t")

    return G


def build_model(F, G, max_shift, slots_per_flight, enforce_same_start_end, model_name):
    m = gurobi.Model(model_name)
    m.setParam("OutputFlag", 0)
    m.setParam("TimeLimit", config.TIME_LIMIT)
    m.setParam("MIPGap", config.MIP_GAP)
    H = max_shift
    
    slot_nodes = [n for n in G.nodes() if is_slot(n)]
    
    if enforce_same_start_end:
        source_nodes = [n for n in G.nodes() if isinstance(n, tuple) and n[0] == "s"]
    else:
        source_nodes = ["s"]
    
    # Arc variables
    x = {}
    for (i, j) in G.edges():
        x[(i, j)] = m.addVar(vtype=gurobi.GRB.BINARY, name=f"x_{i}_{j}")
    
    # Shift start variables 
    S = {}
    for (i, k) in slot_nodes:
        S[(i, k)] = m.addVar(lb=0.0, vtype=gurobi.GRB.CONTINUOUS, name=f"S_{i}_{k}")

    m.update()

    # Flow Balance Constraint
    for (i, k) in slot_nodes:
        m.addConstr(gurobi.quicksum(x[(u, (i, k))] for u in G.predecessors((i, k))) == 1, name=f"Flow-Balance(in)_{i}_{k}")
        m.addConstr(gurobi.quicksum(x[((i, k), v)] for v in G.successors((i, k))) == 1, name=f"Flow-Balance(out)_{i}_{k}")

    # Shift Start Initialization Constraint
    for (i, k) in slot_nodes:
        d_i = F[i].dep_min
        
        # TO-DO add in start end flagging code
        if enforce_same_start_end:
            src = ("s", F[i].origin)
        else:
            src = "s"
 
        m.addConstr(S[(i, k)] <= d_i + H * (1 - x[(src, (i, k))]), name=f"Shift-Start-Init(upper)_{i}_{k}")
        m.addConstr(S[(i, k)] >= d_i - H * (1 - x[(src, (i, k))]), name=f"Shift-Start-Init(lower)_{i}_{k}")

    # Shift Start Propagation Constraint
    for (i, j) in G.edges():
        if (isinstance(i, tuple) and len(i) == 2 and isinstance(i[0], int) and isinstance(j, tuple) and len(j) == 2 and isinstance(j[0], int)):
            m.addConstr(S[j] <= S[i] + H * (1 - x[(i, j)]), name=f"Shift-Start-Prop(upper)_{i}_{j}")
            m.addConstr(S[j] >= S[i] - H * (1 - x[(i, j)]), name=f"Shift-Start-Prop(lower)_{i}_{j}")

    # Maximum Shift Duration Constraint
    for (i, k) in slot_nodes:
        a_i = F[i].arr_min
        m.addConstr(a_i - S[(i, k)] <= H, name=f"Max-Shift_{i}_{k}")

    # Objective: minimize number of crew (source arcs used)
    m.setObjective(
        gurobi.quicksum(x[(src, (i, k))] for src in source_nodes for (i, k) in slot_nodes if (src, (i, k)) in x),
        gurobi.GRB.MINIMIZE
    )

    return m, x, S


def load_crew_requirements():
    P = utils.load_airplanes(config.IN_AIRPLANES)
    return {p.aircraft_id.strip(): p for p in P}


def get_slots_per_flight(flight, crew_reqs, crew_type):
    aircraft = crew_reqs.get(flight.plane_type.strip())
    
    if crew_type == "cabin":
        r_min = aircraft.cabin_crew_min
        r_max = aircraft.cabin_crew_max
        
        alpha = config.CALLOUT_RATE
        if alpha >= 1.0:
            return r_max
        
        return min(math.ceil(r_min / (1 - alpha)), r_max)
    else:
        return aircraft.flight_crew
    


def solve(F, crew_type):
    if crew_type == "pilot":
        results = {}
        
        for aircraft_type in sorted(set(f.plane_type for f in F)):
            F_q = [f for f in F if f.plane_type == aircraft_type]
            
            if len(F_q) == 0:
                continue
            
            results[aircraft_type] = solve_helper(F_q, f"Pilots_{aircraft_type}", "pilot")
        
        return results
    else:
        return {"all": solve_helper(F, "Cabin_Crew", "cabin")}


def solve_helper(F, model_name, crew_type):
    crew_reqs = load_crew_requirements()
    slots_per_flight = [get_slots_per_flight(f, crew_reqs, crew_type) for f in F]
    
    if crew_type == "pilot":
        enforce_same_start_end = config.ENFORCE_SAME_START_END_PILOTS
    else:
        enforce_same_start_end = config.ENFORCE_SAME_START_END_CABIN
    
    transfer_time = config.MIN_TRANSFER_TIME + config.DELAY_BUFFER
    G = build_network(F, transfer_time, slots_per_flight, enforce_same_start_end)
    m, x, S = build_model(F, G, config.MAX_SHIFT_TIME, slots_per_flight, enforce_same_start_end, model_name)
    m.optimize()
    
    results = {"m": m, "F": F, "G": G, "x": x, "S": S, "Count": 0, "Routes": [], "Shifts": []}
    
    if m.Status == gurobi.GRB.OPTIMAL:
        results["Count"] = int(m.ObjVal)
        results["Routes"] = save_routes(F, G, x)
        results["Shifts"] = save_shifts(F, G, x, S)
        
    return results


def save_routes(F, G, x):
    routes = []
    
    for (i, j) in x:
        if is_source(i) and is_slot(j) and x[(i, j)].X > 0.5:
            route = []
            current = j

            while not is_sink(current):
                flight = G.nodes[current]['flight']
                route.append(flight)

                for next_node in G.successors(current):
                    if x[(current, next_node)].X > 0.5:
                        current = next_node
                        break
                        
            routes.append(route)

    return routes
 
 
def save_shifts(F, G, x, S):
    shifts = []
    
    for (i, j) in x:
        if is_source(i) and is_slot(j) and x[(i, j)].X > 0.5:
            first_slot = j
            current = j

            # Find last slot in route
            while not is_sink(current):
                last_slot = current
                
                for next_node in G.successors(current):
                    if x[(current, next_node)].X > 0.5:
                        current = next_node
                        break
                    
            clock_in = S[first_slot].X
            last_flight_idx = last_slot[0]
            clock_out = F[last_flight_idx].arr_min
            shifts.append((clock_in, clock_out))
    
    return shifts


def check_feasibility(label, result):
    m = result["m"]
    
    if m.Status == gurobi.GRB.OPTIMAL:
        return True

    if m.Status == gurobi.GRB.TIME_LIMIT and m.SolCount > 0:
        gap = m.MIPGap * 100
        print(f"  {label}: Time limit reached, best solution has {gap:.1f}% gap")
        return True
    
    print(f"\n  {label}: INFEASIBLE")
    m.computeIIS()

    for c in m.getConstrs():
        if c.IISConstr:
            print(f"    {c.ConstrName}")
    
    return False


def is_source(node):
    return node == "s" or (isinstance(node, tuple) and node[0] == "s")


def is_sink(node):
    return node == "t" or (isinstance(node, tuple) and node[0] == "t")


def is_slot(node):
    return (isinstance(node, tuple) and len(node) == 2 and isinstance(node[0], int) and isinstance(node[1], int))


def run(flight_file):
    csv_name = os.path.splitext(os.path.basename(flight_file))[0]
    F = utils.load_flights(flight_file)
    
    print(f"\nSolving {csv_name} ({len(F)} flights) ...")
    
    cabin_crew_results = solve(F, "cabin")
    pilot_results = solve(F, "pilot")
    
    for item, result in cabin_crew_results.items():
        if not check_feasibility(f"Cabin Crew ({item})", result):
            print("Cabin Crew Model is infeasable, fix model or change dataset")
            return None
    
    for airplane, result in pilot_results.items():
        if not check_feasibility(f"Pilot Model ({airplane})", result):
            print(f"Pilot Model ({airplane}) is infeasable, fix model or change dataset")
            return None
    
    total_cabin_crew = sum(r["Count"] for r in cabin_crew_results.values())
    total_pilots = sum(r["Count"] for r in pilot_results.values())
    total_crew = total_pilots + total_cabin_crew
    
    return {
        "csv_name": csv_name,
        "num_flights": len(F),
        "cabin": cabin_crew_results,
        "pilots": pilot_results,
        "total_cabin": total_cabin_crew,
        "total_pilots": total_pilots,
        "total_crew": total_crew,
    }
    