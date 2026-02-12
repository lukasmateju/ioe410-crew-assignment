# IOE 410: Airline Crew Assignment Optimization Project (Megan Gottfried, Lukas Mateju)
"""
**model.py**
------------------------------------------------------
Main modeling functions and gurobi optimation code along with a few additional helper functions.
"""

from gurobipy import Model, GRB, quicksum
import config 


def build_model(flights):

    m = Model("CrewAssignment")

    J = flights.index.tolist()
    I = range(len(J))

    X = m.addVars(I, J, vtype=GRB.BINARY, name="X")
    Y = m.addVars(I, vtype=GRB.BINARY, name="Y")

    for j in J:
        m.addConstr(quicksum(X[i, j] for i in I) == 1)

    for i in I:
        for j in J:
            m.addConstr(X[i, j] <= Y[i])

    m.setObjective(quicksum(Y[i] for i in I), GRB.MINIMIZE)

    return m





