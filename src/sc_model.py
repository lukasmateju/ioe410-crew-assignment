# IOE 410: Airline Crew Assignment Optimization Project (Megan Gottfried, Lukas Mateju)
"""
**sc_model.py**
------------------------------------------------------
Main set cover algoritm modeling functions and gurobi optimation code along with a few additional helper functions.
"""

import networkx as nx
import gurobipy as gurobi
#import pandas as pd

import config
import utils


def build_network(F):
    G = nx.DiGraph()
    
    # Source and Sink Nodes (start and end)
    G.add_node("s")
    G.add_node("t")
    
    # Flight Nodes
    for i, flight in enumerate(F):
        G.add_node(i, flight=flight)

    # All Arcs for G
    for i in range(len(F)):
        # Source arcs
        G.add_edge("s", i)

        # Compatibility arcs
        for j in range(len(F)):
            if i != j:
                if (F[i].destination == F[j].origin and F[i].arr_min + config.MIN_TRANSFER_TIME <= F[j].dep_min and F[j].arr_min - F[i].dep_min <= config.MAX_SHIFT_HOURS):
                    G.add_edge(i, j)

        # Sink arcs
        G.add_edge(i, "t")

    return G


def build_model(F, G):
    m = gurobi.Model("CrewAssignment")
    H = config.MAX_SHIFT_HOURS
    
    # Arc variables x[(i,j)] for every edge in G
    x = {}
    
    for (i, j) in G.edges():
        x[(i, j)] = m.addVar(vtype=gurobi.GRB.BINARY, name=f"x_{i}_{j}")

    # Shift start variables S[i] for every flight node
    S = m.addVars(range(len(F)), lb=0.0, vtype=gurobi.GRB.CONTINUOUS, name="S")

    # Flow balance Constraint
    for i in range(len(F)):
        # Exactly one arc into flight i
        m.addConstr(gurobi.quicksum(x[(u, i)] for u in G.predecessors(i)) == 1, name=f"flow_in_{i}")
        
        # Exactly one arc out of flight i
        m.addConstr(gurobi.quicksum(x[(i, v)] for v in G.successors(i)) == 1, name=f"flow_out_{i}")

    # Shift Start Initialization Constraint
    for i in range(len(F)):
        d_i = G.nodes[i]['flight'].dep_min
        m.addConstr(S[i] <= d_i + H * (1 - x[("s", i)]), name=f"sinit_ub_{i}")
        m.addConstr(S[i] >= d_i - H * (1 - x[("s", i)]), name=f"sinit_lb_{i}")
        
    # Shift Start Propagation Constraint
    for (i, j) in G.edges():
        if i != "s" and j != "t":
            m.addConstr(S[j] <= S[i] + H * (1 - x[(i, j)]), name=f"sprop_ub_{i}_{j}")
            m.addConstr(S[j] >= S[i] - H * (1 - x[(i, j)]), name=f"sprop_lb_{i}_{j}")
    
    # Maximum Shift Duration Constraint
    for i in range(len(F)):
        a_i = G.nodes[i]['flight'].arr_min
        m.addConstr(a_i - S[i] <= H, name=f"shift_limit_{i}")
    
    # Objective Function - Minimize number of crew members (source arcs used)
    m.setObjective(
        gurobi.quicksum(x[("s", i)] for i in range(len(F))),
        gurobi.GRB.MINIMIZE
    )
    
    return m, x, S

def run(show_crew_count, show_routes, show_shift_times, save_output):
    F = utils.load_flights(config.IN_FLIGHTS)
    #A = utils.load_airports(config.IN_AIRPORTS)
    #P = utils.load_airplanes(config.IN_AIRPLANES)
    
    G = build_network(F)
    m, x, S = build_model(F, G)
    m.optimize()
    
    if m.status == gurobi.GRB.INFEASIBLE:
        print("Computing IIS (Irreducible Infeasible Subsystem)...")
        m.computeIIS()
        print("Infeasible constraints:")
        for c in m.getConstrs():
            if c.IISConstr:
                print(f"  {c.ConstrName}")

    if m.status == gurobi.GRB.OPTIMAL:
        if show_crew_count:
            utils.print_crew_count(m)
        if show_routes:
            utils.print_routes(F, G, x)
        if show_shift_times:
            utils.print_shift_times(F, S)
        if save_output:
            utils.save_output(m, F, G, x, S, show_routes, show_shift_times)
    else:
        print("No optimal solution found. Status:", m.status)