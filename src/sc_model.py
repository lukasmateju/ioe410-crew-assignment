# IOE 410: Airline Crew Assignment Optimization Project (Megan Gottfried, Lukas Mateju)
"""
**sc_model.py**
------------------------------------------------------
Main set cover algoritm modeling functions and gurobi optimation code along with a few additional helper functions.
"""

import os
import math
import networkx as nx

try:
    import gurobipy as gurobi
except ImportError:
    gurobi = None

try:
    import scipy.sparse as sp
    from scipy.optimize import Bounds, LinearConstraint, milp
except ImportError:
    sp = None
    Bounds = None
    LinearConstraint = None
    milp = None

import config
import utils


STATUS_OPTIMAL = "optimal"
STATUS_TIME_LIMIT_FEASIBLE = "time_limit_feasible"
STATUS_INFEASIBLE = "infeasible"
STATUS_ERROR = "error"


class SolverResult:
    def __init__(self, backend, status, objective=None, message="", mip_gap=None, native_model=None):
        self.backend = backend
        self.status = status
        self.objective = objective
        self.message = message
        self.mip_gap = mip_gap
        self.native_model = native_model

    @property
    def feasible(self):
        return self.status in {STATUS_OPTIMAL, STATUS_TIME_LIMIT_FEASIBLE}

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


def build_gurobi_model(F, G, max_shift, slots_per_flight, enforce_same_start_end, model_name):
    if gurobi is None:
        raise RuntimeError("gurobipy is not installed")

    m = gurobi.Model(model_name)
    #m.setParam("OutputFlag", 0)
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


def solve_scipy_model(F, G, max_shift, enforce_same_start_end):
    if milp is None:
        return SolverResult(
            "scipy",
            STATUS_ERROR,
            message="SciPy MILP is not available in this Python environment.",
        ), {}, {}

    H = max_shift
    slot_nodes = [n for n in G.nodes() if is_slot(n)]
    edges = list(G.edges())
    x_idx = {edge: idx for idx, edge in enumerate(edges)}
    s_offset = len(edges)
    s_idx = {slot: s_offset + idx for idx, slot in enumerate(slot_nodes)}
    n_vars = len(edges) + len(slot_nodes)

    c = [0.0] * n_vars
    source_nodes = source_nodes_for_graph(G, enforce_same_start_end)
    for edge, idx in x_idx.items():
        if edge[0] in source_nodes and is_slot(edge[1]):
            c[idx] = 1.0

    integrality = [1] * len(edges) + [0] * len(slot_nodes)
    lower_bounds = [0.0] * n_vars
    upper_bounds = [1.0] * len(edges) + [float("inf")] * len(slot_nodes)

    rows = []
    cols = []
    data = []
    lows = []
    highs = []

    def add_constraint(terms, low, high):
        row = len(lows)
        for col, value in terms:
            rows.append(row)
            cols.append(col)
            data.append(value)
        lows.append(low)
        highs.append(high)

    for slot in slot_nodes:
        add_constraint([(x_idx[(u, slot)], 1.0) for u in G.predecessors(slot)], 1.0, 1.0)
        add_constraint([(x_idx[(slot, v)], 1.0) for v in G.successors(slot)], 1.0, 1.0)

    for slot in slot_nodes:
        i, _ = slot
        d_i = F[i].dep_min
        src = source_for_flight(F[i], enforce_same_start_end)
        add_constraint([(s_idx[slot], 1.0), (x_idx[(src, slot)], H)], -float("inf"), d_i + H)
        add_constraint([(s_idx[slot], 1.0), (x_idx[(src, slot)], -H)], d_i - H, float("inf"))

    for i, j in edges:
        if is_slot(i) and is_slot(j):
            add_constraint([(s_idx[j], 1.0), (s_idx[i], -1.0), (x_idx[(i, j)], H)], -float("inf"), H)
            add_constraint([(s_idx[j], 1.0), (s_idx[i], -1.0), (x_idx[(i, j)], -H)], -H, float("inf"))

    for slot in slot_nodes:
        i, _ = slot
        add_constraint([(s_idx[slot], -1.0)], -float("inf"), H - F[i].arr_min)

    constraints = None
    if lows:
        matrix = sp.coo_matrix((data, (rows, cols)), shape=(len(lows), n_vars)).tocsr()
        constraints = LinearConstraint(matrix, lows, highs)

    options = {
        "time_limit": config.TIME_LIMIT,
        "mip_rel_gap": config.MIP_GAP,
        "disp": False,
    }
    result = milp(
        c=c,
        integrality=integrality,
        bounds=Bounds(lower_bounds, upper_bounds),
        constraints=constraints,
        options=options,
    )

    if result.x is None:
        status = STATUS_INFEASIBLE if result.status == 2 else STATUS_ERROR
        return SolverResult("scipy", status, message=result.message), {}, {}

    selected_arcs = {edge: float(result.x[idx]) for edge, idx in x_idx.items()}
    shift_starts = {slot: float(result.x[idx]) for slot, idx in s_idx.items()}
    status = STATUS_OPTIMAL if result.status == 0 else STATUS_TIME_LIMIT_FEASIBLE
    return SolverResult("scipy", status, objective=result.fun, message=result.message), selected_arcs, shift_starts


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


def source_for_flight(flight, enforce_same_start_end):
    if enforce_same_start_end:
        return ("s", flight.origin)
    return "s"


def source_nodes_for_graph(G, enforce_same_start_end):
    if enforce_same_start_end:
        return [n for n in G.nodes() if isinstance(n, tuple) and n[0] == "s"]
    return ["s"]


def choose_solver_backend():
    backend = config.SOLVER_BACKEND.lower()
    valid_backends = {"auto", "gurobi", "scipy"}

    if backend not in valid_backends:
        raise ValueError(f"Unknown SOLVER_BACKEND '{config.SOLVER_BACKEND}'. Use auto, gurobi, or scipy.")

    if backend == "gurobi":
        if gurobi is None:
            raise RuntimeError("SOLVER_BACKEND='gurobi' was requested, but gurobipy is not installed.")
        return "gurobi"

    if backend == "scipy":
        if milp is None:
            raise RuntimeError("SOLVER_BACKEND='scipy' was requested, but scipy.optimize.milp is unavailable.")
        return "scipy"

    if gurobi is not None:
        return "gurobi"

    if milp is not None:
        return "scipy"

    raise RuntimeError("No supported solver backend is available. Install gurobipy or SciPy with MILP support.")


def solve_gurobi_model(F, G, slots_per_flight, enforce_same_start_end, model_name):
    m, x, S = build_gurobi_model(
        F,
        G,
        config.MAX_SHIFT_TIME,
        slots_per_flight,
        enforce_same_start_end,
        model_name,
    )
    m.optimize()

    if m.Status == gurobi.GRB.OPTIMAL:
        status = STATUS_OPTIMAL
    elif m.Status == gurobi.GRB.TIME_LIMIT and m.SolCount > 0:
        status = STATUS_TIME_LIMIT_FEASIBLE
    elif m.Status in {gurobi.GRB.INFEASIBLE, gurobi.GRB.INF_OR_UNBD}:
        status = STATUS_INFEASIBLE
    else:
        status = STATUS_ERROR

    objective = m.ObjVal if m.SolCount > 0 else None
    mip_gap = m.MIPGap if m.SolCount > 0 else None
    solver_result = SolverResult("gurobi", status, objective=objective, mip_gap=mip_gap, native_model=m)
    return solver_result, x, S


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
    backend = choose_solver_backend()

    if backend == "gurobi":
        try:
            solver_result, x, S = solve_gurobi_model(F, G, slots_per_flight, enforce_same_start_end, model_name)
        except Exception:
            if config.SOLVER_BACKEND.lower() != "auto" or milp is None:
                raise
            print(f"  {model_name}: Gurobi unavailable at runtime; falling back to SciPy MILP")
            solver_result, x, S = solve_scipy_model(F, G, config.MAX_SHIFT_TIME, enforce_same_start_end)
    else:
        solver_result, x, S = solve_scipy_model(F, G, config.MAX_SHIFT_TIME, enforce_same_start_end)

    results = {
        "solver": solver_result,
        "F": F,
        "G": G,
        "x": x,
        "S": S,
        "Count": 0,
        "Routes": [],
        "Shifts": [],
    }

    if solver_result.feasible:
        results["Count"] = int(round(solver_result.objective))
        results["Routes"] = save_routes(F, G, x)
        results["Shifts"] = save_shifts(F, G, x, S)
        
    return results


def save_routes(F, G, x):
    routes = []
    
    for (i, j) in x:
        if is_source(i) and is_slot(j) and var_value(x[(i, j)]) > 0.5:
            route = []
            current = j

            while not is_sink(current):
                flight = G.nodes[current]['flight']
                route.append(flight)

                for next_node in G.successors(current):
                    if var_value(x[(current, next_node)]) > 0.5:
                        current = next_node
                        break
                        
            routes.append(route)

    return routes
 
 
def save_shifts(F, G, x, S):
    shifts = []
    
    for (i, j) in x:
        if is_source(i) and is_slot(j) and var_value(x[(i, j)]) > 0.5:
            first_slot = j
            current = j

            # Find last slot in route
            while not is_sink(current):
                last_slot = current
                
                for next_node in G.successors(current):
                    if var_value(x[(current, next_node)]) > 0.5:
                        current = next_node
                        break
                    
            clock_in = var_value(S[first_slot])
            last_flight_idx = last_slot[0]
            clock_out = F[last_flight_idx].arr_min
            shifts.append((clock_in, clock_out))
    
    return shifts


def var_value(value):
    try:
        return value.getAttr(gurobi.GRB.Attr.X)
    except AttributeError:
        pass
    except Exception:
        pass

    try:
        raw_value = value.X
        if raw_value is not value:
            return raw_value
    except AttributeError:
        return value
    except Exception:
        pass

    return value


def check_feasibility(label, result):
    solver_result = result["solver"]

    if solver_result.status == STATUS_OPTIMAL:
        return True

    if solver_result.status == STATUS_TIME_LIMIT_FEASIBLE:
        if solver_result.mip_gap is None:
            print(f"  {label}: Time limit reached, using best feasible solution")
        else:
            gap = solver_result.mip_gap * 100
            print(f"  {label}: Time limit reached, best solution has {gap:.1f}% gap")
        return True

    print(f"\n  {label}: INFEASIBLE or no feasible solution")
    if solver_result.message:
        print(f"    {solver_result.backend}: {solver_result.message}")

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
