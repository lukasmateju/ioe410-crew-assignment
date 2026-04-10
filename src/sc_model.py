# IOE 410: Airline Crew Assignment Optimization Project (Megan Gottfried, Lukas Mateju)
"""
**sc_model.py**
------------------------------------------------------
Main set cover algoritm modeling functions and gurobi optimation code along with a few additional helper functions.
"""

import os
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
            # Arc does not start and end with the same flight
            if i != j:
                # Destination airport of flight i is the same as the origin airport of flight j
                # There is enough time to transfer from flight i to flight j
                if (F[i].destination == F[j].origin and F[i].arr_min + transfer_time <= F[j].dep_min):
                    G.add_edge(i, j)

        G.add_edge(i, "t")

    return G


def build_model(F, G, max_shift, model_name):
    m = gurobi.Model(model_name)
    H = max_shift

    # Arc variables x[(i,j)] for every edge in G
    x = {}
    for (i, j) in G.edges():
        x[(i, j)] = m.addVar(vtype=gurobi.GRB.BINARY, name=f"x_{i}_{j}")

    # Shift start variables S[i] for every flight node
    S = m.addVars(range(len(F)), lb=0.0, vtype=gurobi.GRB.CONTINUOUS, name="S")

    # Flow Balance Constraint
    for i in range(len(F)):
        m.addConstr(gurobi.quicksum(x[(u, i)] for u in G.predecessors(i)) == 1, name=f"Flow-Balance(in)_{i}")
        m.addConstr(gurobi.quicksum(x[(i, v)] for v in G.successors(i)) == 1, name=f"Flow-Balance(out)_{i}")

    # Shift Start Initialization Constraint
    for i in range(len(F)):
        d_i = G.nodes[i]['flight'].dep_min
        
        m.addConstr(S[i] <= d_i + H * (1 - x[("s", i)]), name=f"Shift-Start-Init(upper)_{i}")
        m.addConstr(S[i] >= d_i - H * (1 - x[("s", i)]), name=f"Shift-Start-Init(lower)_{i}")

    # Shift Start Propagation Constraint
    for (i, j) in G.edges():
        if i != "s" and j != "t":
            m.addConstr(S[j] <= S[i] + H * (1 - x[(i, j)]), name=f"Shift-Start-Prop(upper)_{i}_{j}")
            m.addConstr(S[j] >= S[i] - H * (1 - x[(i, j)]), name=f"Shift-Start-Prop(lower)_{i}_{j}")

    # Maximum Shift Duration Constraint
    for i in range(len(F)):
        a_i = G.nodes[i]['flight'].arr_min
        m.addConstr(a_i - S[i] <= H, name=f"Max-Shift_{i}")

    # Objective: minimize number of crew (source arcs used)
    m.setObjective(
        gurobi.quicksum(x[("s", i)] for i in range(len(F))),
        gurobi.GRB.MINIMIZE
    )

    return m, x, S


def solve(F, crew_type):
    if crew_type == "pilot":
        results = {}
        
        for aircraft_type in sorted(set(f.plane_type for f in F)):
            F_q = [f for f in F if f.plane_type == aircraft_type]
            
            if len(F_q) == 0:
                continue
            
            results[aircraft_type] = solve_helper(F_q, f"Pilots_{aircraft_type}")
        
        return results
    else:
        return {"all": solve_helper(F, "Cabin_Crew")}


def solve_helper(F, model_name):
    transfer_time = config.MIN_TRANSFER_TIME + config.DELAY_BUFFER
    G = build_network(F, transfer_time)
    m, x, S = build_model(F, G, config.MAX_SHIFT_TIME, model_name=model_name)
    m.optimize()
    
    results = {"m": m, "F": F, "G": G, "x": x, "S": S, "Count": 0, "Routes": [], "Shifts": []}
    
    if m.Status == gurobi.GRB.OPTIMAL:
        results["Count"] = int(m.ObjVal)
        results["Routes"] = save_routes(F, G, x)
        results["Shifts"] = save_shifts(F, G, x, S)
        
    return results


def save_routes(F, G, x):
    routes = []
    
    for i in range(len(F)):
        if x[("s", i)].X > 0.5:
            route = []
            current = i
            
            while current != "t":
                route.append(G.nodes[current]['flight'])
                
                for v in G.successors(current):
                    if x[(current, v)].X > 0.5:
                        current = v
                        break
                    
            routes.append(route)
            
    return routes
 
 
def save_shifts(F, G, x, S):
    shifts = []
    
    for i in range(len(F)):
        if x[("s", i)].X > 0.5:
            route_indices = []
            current = i
            
            while current != "t":
                route_indices.append(current)
                
                for v in G.successors(current):
                    if x[(current, v)].X > 0.5:
                        current = v
                        break
                    
            clock_in = S[route_indices[0]].X
            clock_out = F[route_indices[-1]].arr_min
            shifts.append((clock_in, clock_out))
        
    return shifts


def check_feasibility(label, result):
    m = result["m"]
    
    if m.Status == gurobi.GRB.OPTIMAL:
        return True

    print(f"\n  {label}: INFEASIBLE")
    m.computeIIS()

    for c in m.getConstrs():
        if c.IISConstr:
            print(f"    {c.ConstrName}")
    
    return False


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
    