## Cabin Crew Model

This is the foundational model we started with and later modified for use with the pilot-specific model. It finds the minimum number of crew routes needed to cover every flight exactly once, subject to transfer time and shift duration constraints. Each flight requires exactly one crew member ($r_i = 1$), there is a single source and single sink node, and there is no requirement for crew to return to their starting airport. We spent the most time on this model since the other two build directly on top of it.


### Sets
 
| Symbol | Definition |
|--------|-----------|
| $F = \{1, 2, \ldots, n\}$ | Set of all scheduled flights |
| $N = \{s\} \cup F \cup \{t\}$ | Set of all nodes including source $s$, all flight nodes, and sink $t$ |
| $A = A^{\text{s}} \cup A^{\text{c}} \cup A^{\text{e}}$ | Set of all directed arcs (expanded on in Arc Types section) |
| $G = (N, A)$ | Directed compatibility graph containing all nodes from $N$ and arcs from $A$ |


### Arc Types

Three types of directed arcs connect the nodes, determining which crew routes are feasible.

| **Arc Type** | **Definition** |
|:--------:|-----------|
| **Source Arc** $$A^{\text{s}} = \{(s,i) : i \in F\}$$ | Connects the source to every flight. A crew member starting their shift at flight $i$ uses the arc $(s, i)$. Every flight is a candidate for being the first flight in someone's day. |
| **Compatibility Arc** $$A^{\text{c}} = \{(i,j) : i,j \in F,\ i \neq j,\ e_i = b_j,\ a_i + \delta \leq d_j\}$$| Connects pairs of flights that the same crew member could work in sequence. The conditions for this arc are described below. |
| **Sink Arc** $$A^{\text{e}} = \{(i,t) : i \in F\}$$ | Connects every flight to the sink. A crew member ending their shift after flight $i$ uses the arc $(i, t)$. Every flight is a candidate for being the last flight in someone's day. |

A compatibility arc from flight $i$ to flight $j$ exists when three conditions are all met:

 **1.** $\ i \neq j$ - The arc does not start and end with the same flight

 **2.** $e_i = b_j$ - The destination airport of flight $i$ is the same as the origin airport of flight $j$

 **3.** $a_i + \delta \leq d_j\ $ - There is enough time to transfer from flight $i$ to flight $j$


### Parameters

| Symbol | Definition |
|--------|-----------|
| $d_i$ | Departure time of flight $i$ (minutes after 00:00) |
| $a_i$ | Arrival time of flight $i$ (minutes after 00:00) |
| $b_i$ | Origin airport of flight $i$ |
| $e_i$ | Destination airport of flight $i$ |
| $\delta = 60$ | Minimum transfer time between consecutive flights (60 min) |
| $H = 660$ | Maximum total shift length (660 min / 11 hours) |


### Decision Variables

| Variable | Domain | Definition |
|----------|--------|-----------|
| $x_{ij}$ | $\{0,1\}$, $\forall (i,j) \in A$ | **Arc Selection Variable:** Equals 1 if a crew member traverses arc $(i,j)$ as part of their route, 0 otherwise. Source arcs $x_{si}$ indicate shift starts, compatibility arcs $x_{ij}$ indicate consecutive flights by the same crew member, and sink arcs $x_{it}$ indicate shift ends. The set of all arcs with $x_{ij} = 1$ forms paths from $s$ to $t$, each representing one crew member's complete route for the day. |
| $S_i$ | $\mathbb{R}_{\geq 0}$, $\forall i \in F$ | **Shift Start Time Variable:** Records the clock-in time (departure of first flight) of the crew member assigned to flight $i$. This value is the same for every flight in a given crew member's route and is what lets us enforce the maximum shift duration constraint. |


### Objective Function

| Function | Definition |
|----------|--------|
| $$\min \sum_{i \in F} x_{si}$$ | Minimize the total number of crew members, which is equivalent to minimizing the total number of source arcs used |


### Constraints

| Constraint | Formulation | Description |
|--------------------|-------------|-------------|
| **Flow Balance** *(in)* | $\sum_{u : (u,i) \in A} x_{ui} = 1 \quad \forall i \in F$ | Exactly one arc enters each flight node. This means exactly one crew member is assigned to each flight, whether they are starting fresh from the source or continuing from a previous flight. |
| **Flow Balance** *(out)* | $\sum_{v : (i,v) \in A} x_{iv} = 1 \quad \forall i \in F$ | Exactly one arc leaves each flight node. The crew member either continues to another flight or ends their shift at the sink. Together with **Flow Balance** *(in)*, these ensure every flight is covered exactly once and the arcs form valid $s$-to-$t$ paths. |
| **Shift Start Initialization** *(upper)* | $S_i \leq d_i + H(1 - x_{si}) \quad \forall i \in F$ | When $x_{si} = 1$ (flight $i$ is the first in the crew member's route), this forces $S_i \leq d_i$. When $x_{si} = 0$, the big-$M$ term $H$ relaxes the constraint so $S_i$ is set by propagation instead. |
| **Shift Start Initialization** *(lower)* | $S_i \geq d_i - H(1 - x_{si}) \quad \forall i \in F$ | When $x_{si} = 1$, this forces $S_i \geq d_i$. Combined with the upper constraint, this gives $S_i = d_i$ when flight $i$ starts a route. |
| **Shift Start Propagation** *(upper)* | $S_j \leq S_i + H(1 - x_{ij}) \quad \forall (i,j) \in A^{\text{c}}$ | When $x_{ij} = 1$ (same crew member operates flight $i$ then flight $j$), this forces $S_j \leq S_i$. When $x_{ij} = 0$, the constraint is relaxed and $S_i$, $S_j$ are independent. |
| **Shift Start Propagation** *(lower)* | $S_j \geq S_i - H(1 - x_{ij}) \quad \forall (i,j) \in A^{\text{c}}$ | When $x_{ij} = 1$, this forces $S_j \geq S_i$. Together with the upper constraint, this gives $S_j = S_i$, meaning the shift start time carries forward unchanged along the crew member's route. Every flight in the same route shares the same $S$ value, which makes sense since both flights belong to the same workday. |
| **Max Shift Duration** | $a_i - S_i \leq H \quad \forall i \in F$ | The arrival time of flight $i$ minus the crew member's shift start cannot exceed $H$ minutes. This ensures no crew member works longer than the maximum allowed shift length. |
| **Airport-Indexed Source/Sink Structure** *(optional)* | Replace $s,t$ with airport-indexed nodes $s_a,t_a$ | When enabled, the code replaces the single source and sink with airport-indexed source and sink nodes, and source/sink arcs are restricted by flight origin and destination airport. |

### Cabin Crew Model Summary

$\min \sum_{i \in F} x_{si}$

$\text{Subject to:}$

$\sum_{u : (u,i) \in A} x_{ui} = 1 \quad \forall i \in F$

$\sum_{v : (i,v) \in A} x_{iv} = 1 \quad \forall i \in F$

$S_i \leq d_i + H(1 - x_{si}) \quad \forall i \in F$

$S_i \geq d_i - H(1 - x_{si}) \quad \forall i \in F$

$S_j \leq S_i + H(1 - x_{ij}) \quad \forall (i,j) \in A^{\text{c}}$

$S_j \geq S_i - H(1 - x_{ij}) \quad \forall (i,j) \in A^{\text{c}}$

$a_i - S_i \leq H \quad \forall i \in F$

$x_{ij} \in \{0,1\} \quad \forall (i,j) \in A$

$S_i \geq 0,\ S_i \in \mathbb{R} \quad \forall i \in F$

When airport-indexed source/sink nodes are enabled, $s$ and $t$ are replaced with $s_a$ and $t_a$ for each airport $a \in K$, the source/sink arcs are restricted accordingly, and the objective becomes $\min \sum_{a \in K} \sum_{i \in F} x_{s_a, i}$.

This base model is enough to solve the original problem prompt with a single crew type, one crew member per flight, and optional airport-indexed source/sink nodes. In the following sections, we expand on this foundation in two ways. First, we adapt the model for pilots by restricting compatibility arcs to flights of the same aircraft type. Then, we improve the model by expanding flight nodes to handle multiple crew members per flight and incorporating robustness buffers for callouts and delays.
