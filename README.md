# Airline Crew Assignment Optimization Project
> **IOE 410 Project** | Megan Gottfried, Lukas Mateju

## Overview

This project formulates and solves an airline crew assignment problem using mixed-integer linear programming in Python with Gurobi.

The goal is to find the minimum number of crew members needed to operate all scheduled flights while satisfying operational constraints like maximum shift length, minimum connection time between flights, aircraft-specific crew requirements, a same-start/end-airport policy, and configurable buffers for crew callouts and delays.

We model two distinct crew types, **cabin crew** and **pilots**, each with different rules and restrictions. These are solved as parallel optimization problems.

---

## Problem Description

Our original project prompt was:

> An airline wants to assign cabin-crew to all its flights between n airports on a particular day. The same crew can serve a sequence of multiple flights as long as there is sufficient time to transfer from one flight to the next (e.g., at least 1 hour). There is a limit on the total number of hours worked by any crew (e.g., at most 11 hours from the start to end of their shift).
>
> You should also consider some additional restrictions to model. Find the minimum number of crew that is needed to serve all the flights. You should also consider the effect of enforcing policies such as "each crew must start/end their shift at the same airport".

We used this as a starting point and expanded on it considerably. Here is the full problem we ended up modeling:

An airline needs to assign cabin crew and pilots to all scheduled flights on a given day across multiple airports. Each flight uses a specific aircraft model, and each model requires a different number of cabin crew and pilots. For example, a Boeing 737 requires 2 pilots and a minimum of 3 cabin crew, while an Airbus A380 requires 3 pilots and up to 20 cabin crew. Each crew member is an individual person who follows a route, meaning a sequence of one or more flights, through the day. The goal is to minimize the total number of crew members needed to cover all flights.

Every crew member's route must satisfy the following constraints:

- **Minimum transfer time** - When a crew member transitions from one flight to the next, there must be at least 60 minutes between the arrival of the first flight and the departure of the next. The two flights must also connect at the same airport (the first flight's destination must be the next flight's origin).
- **Maximum shift duration** - A crew member's total shift, measured from the departure of their first flight to the arrival of their last flight, cannot exceed 11 hours (660 minutes).
- **Same start/end airport** - Each crew member must begin and end their shift at the same airport. For example, if a crew member's first flight departs from ORD, their last flight must arrive at ORD.
- **Aircraft-specific crew requirements** - Each flight's aircraft type determines how many cabin crew and how many pilots are required. These values come from the aircraft data and vary across types.
- **Robustness to callouts and delays** - The user can configure an expected callout rate that increases crew requirements to account for sick calls, as well as a delay buffer that increases the minimum transfer time to provide slack against schedule disruptions.

The two crew types work differently:

- **Cabin crew** are interchangeable across aircraft types. A cabin crew member can work a B737 flight and then transfer to an A320 flight without restriction. The number of cabin crew required per flight is determined by the aircraft type and ranges from 3 (for narrow-body aircraft like the B737 or A320) to 20 (for the A380).
- **Pilots** are certified for a single aircraft type and may only fly that type. A B737 pilot cannot operate an A320 under any circumstances. Because of this restriction, pilot scheduling splits naturally by aircraft type: B737 pilots only interact with B737 flights, A320 pilots only interact with A320 flights, and so on.

---

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

This base model is enough to solve the original problem prompt with a single crew type, one crew member per flight, and no same-start/end-airport requirement. In the following sections, we expand on this foundation in two ways. First, we adapt the model for pilots by restricting compatibility arcs to flights of the same aircraft type. Then, we improve the model by expanding flight nodes to handle multiple crew members per flight, replacing the single source and sink with airport-specific pairs to enforce same-start/end-airport, and incorporating robustness buffers for callouts and delays.

---

## Pilot Crew Model

As discussed in the Problem Description, pilots are certified for a single aircraft model and can only fly that specific model. A pilot certified for B737s will never interact with A320 flights regardless of airport or timing. This means the pilot scheduling problem organizes itself naturally by aircraft type, and we solve a separate instance of the base model for each type using only the flights that operate that type.

Structurally, this model is identical to the cabin crew model defined above. The only real change is the addition of the aircraft type set and a filtering of the flight set. All other sets, parameters, decision variables, constraints, and the objective function carry over directly.

### Additional Sets

| Symbol | Definition |
|--------|-----------|
| $P$ | Set of all aircraft types (B737, B777, A320, etc.) |
| $p_i \in P$ | Aircraft type assigned to flight $i$ |
| $F_q = \{i \in F : p_i = q\}$ | Subset of flights using aircraft type $q$, for each $q \in P$ |

For each aircraft type $q \in P$, we build a separate network $G_q = (N_q, A_q)$ containing only the flights in $F_q$. All sets, arcs, variables, and constraints from the base model apply within this sub-network exactly as defined above, just restricted to flights in $F_q$.

### Additional Parameters

| Symbol | Definition |
|--------|-----------|
| $r_i^{\text{pilot}}$ | Number of pilots required for flight $i$, determined by aircraft type $p_i$ (from `flight_crew` column in aircraft data) |

For the base pilot model, we set $r_i = 1$ and solve for one pilot per flight. When $r_i^{\text{pilot}} > 1$ (most aircraft require 2-3 pilots), we use the expanded slot approach described in the Full Flight Schedule Model section.

### Compatibility Arcs

Within the sub-network for aircraft type $q$, the compatibility arcs are:

$$A_q^{\text{c}} = \{(i,j) : i,j \in F_q,\ i \neq j,\ e_i = b_j,\ a_i + \delta \leq d_j\}$$

Since all flights in $F_q$ share aircraft type $q$, no explicit type check is needed in the arc definition. The decomposition into sub-networks handles the type restriction automatically.

A compatibility arc from flight $i$ to flight $j$ within sub-network $G_q$ exists when the same three conditions from the cabin crew model are met:

 **1.** $\ i \neq j$ - The arc does not start and end with the same flight

 **2.** $e_i = b_j$ - The destination airport of flight $i$ is the same as the origin airport of flight $j$

 **3.** $a_i + \delta \leq d_j$ - There is enough time to transfer from flight $i$ to flight $j$

The key difference from the cabin crew model is that these arcs only exist between flights of the same aircraft type. A B737 pilot finishing a flight at ORD can only connect to another B737 flight departing from ORD, even if an A320 flight departs sooner with a valid transfer time.

### Pilot Sub-Model Summary (for aircraft type $q$)

$\min \sum_{i \in F_q} x_{si}$

$\text{Subject to:}$

$\sum_{u : (u,i) \in A_q} x_{ui} = 1 \quad \forall i \in F_q$

$\sum_{v : (i,v) \in A_q} x_{iv} = 1 \quad \forall i \in F_q$

$S_i \leq d_i + H(1 - x_{si}) \quad \forall i \in F_q$

$S_i \geq d_i - H(1 - x_{si}) \quad \forall i \in F_q$

$S_j \leq S_i + H(1 - x_{ij}) \quad \forall (i,j) \in A_q^{\text{c}}$

$S_j \geq S_i - H(1 - x_{ij}) \quad \forall (i,j) \in A_q^{\text{c}}$

$a_i - S_i \leq H \quad \forall i \in F_q$

$x_{ij} \in \{0,1\} \quad \forall (i,j) \in A_q$

$S_i \geq 0,\ S_i \in \mathbb{R} \quad \forall i \in F_q$

This model is solved independently for each aircraft type $q \in P$ that appears in the flight schedule. Since each sub-model only contains flights for one aircraft type, these are typically much smaller and faster to solve than a single model over all flights. The total number of pilots needed across all types is:

$$\text{Total pilots} = \sum_{q \in P} \left( \min \sum_{i \in F_q} x_{si} \right)$$

Each sub-model is independent and can be solved in parallel.

---

## Full Flight Schedule Model

The cabin crew and pilot models each assign one crew member per flight. In practice, flights require multiple crew members (a B737 needs 3 cabin crew and 2 pilots) and airlines require crew to return to their starting airport. This model connects the previous formulations to handle both of these requirements, and adds robustness buffers for crew callouts and flight delays to give us a usable model that assigns individual crew members their own unique routes.

Three specific changes are made to the formulation:

- **Expanded flight-slot nodes** - Each flight is split into multiple nodes, one per crew position, so that each node is still served by exactly one person. This allows the model to assign multiple crew members to a single flight while keeping all variables binary and requiring as few changes to the previous models as possible.
- **Airport-indexed sources and sinks** - The single source $s$ and sink $t$ are replaced with a source-sink pair for each airport. A crew member entering through a source at ORD can only exit through the sink at ORD, enforcing same-start/end-airport without additional variables or constraints.
- **Robustness buffers** - A crew callout rate increases the number of crew positions per flight, and a delay buffer increases the minimum transfer time between flights. Both are applied during preprocessing before the model is built.

### Additional Sets

| Symbol | Definition |
|--------|-----------|
| $K$ | Set of all airports, each assigned a unique index |
| $\hat{F} = \{(i,k) : i \in F,\ k = 1,\ldots,r_i\}$ | Expanded flight-slot set. Each flight $i$ is represented by $r_i$ nodes, one per crew position. |
| $N = \{s_a : a \in K\} \cup \hat{F} \cup \{t_a : a \in K\}$ | Full node set: airport source nodes, flight-slot nodes, and airport sink nodes |

The expanded flight-slot set $\hat{F}$ is the central modeling idea here. If a B737 flight needs 3 cabin crew, that flight becomes three separate nodes: $(i,1)$, $(i,2)$, $(i,3)$. Each node represents one crew position that must be filled by one person. This is analogous to the node-splitting transformation used for node capacities in maximum flow problems (IOE 410 Lecture 10).

The airport-indexed sources and sinks enforce the same-start/end-airport constraint through network structure alone. For each airport $a \in K$, source node $s_a$ represents crew members beginning their shift at airport $a$, and sink node $t_a$ represents crew members ending their shift at airport $a$. A crew member who enters the network through $s_{\text{ORD}}$ can only exit through $t_{\text{ORD}}$ because the arc definitions restrict which sources and sinks connect to which flights. This follows the multiple sources/destinations transformation from maximum flow (IOE 410 Lecture 10).

### Additional Parameters

| Symbol | Definition |
|--------|-----------|
| $r_i^{\text{min}}$ | Minimum cabin crew required for the aircraft type of flight $i$ (from `cabin_crew_min` in aircraft data) |
| $r_i^{\text{max}}$ | Maximum cabin crew capacity for the aircraft type of flight $i$ (from `cabin_crew_max` in aircraft data) |
| $\alpha \in [0,1)$ | Expected crew callout rate (fraction of crew expected to call out sick) |
| $\delta_{\text{delay}}$ | Additional transfer time buffer for expected flight delays (minutes) |

### Computed Values (Preprocessing)

Before the model is built, the following values are computed from the parameters above.

**Effective crew requirement:**

$$r_i = \min\!\left(\left\lceil \frac{r_i^{\text{min}}}{1 - \alpha} \right\rceil,\ r_i^{\text{max}}\right)$$

This determines how many slot nodes are created for each flight in $\hat{F}$. With $\alpha = 0$, we just get $r_i = r_i^{\text{min}}$ (the base case with no buffer). As $\alpha$ increases, $r_i$ grows toward $r_i^{\text{max}}$, which is the physical limit of how many crew the aircraft can hold. For example, a B737 flight ($r^{\text{min}} = 3$, $r^{\text{max}} = 5$) with $\alpha = 0.10$ yields $r_i = \lceil 3/0.9 \rceil = 4$.

**Effective transfer time:**

$$\delta_{\text{eff}} = \delta + \delta_{\text{delay}}$$

This replaces $\delta$ in all compatibility arc definitions. Increasing $\delta_{\text{delay}}$ reduces the number of compatible flight pairs, which generally requires more crew but provides resilience against schedule disruptions.

### Arc Types

The same three arc types from the cabin crew and pilot models apply here, adapted for the expanded slot nodes and airport-indexed sources/sinks.

| **Arc Type** | **Definition** |
|:--------:|-----------|
| **Source Arc** $$A^{\text{s}} = \{(s_a, (i,k)) : (i,k) \in \hat{F},\ a = b_i\}$$ | Connects airport source $s_a$ to flight-slot $(i,k)$ only when flight $i$ departs from airport $a$. A crew member starting at ORD can only begin with a flight departing from ORD. |
| **Compatibility Arc** $$A^{\text{c}} = \{((i,k),(j,l)) : (i,k),(j,l) \in \hat{F},\ i \neq j,\ e_i = b_j,\ a_i + \delta_{\text{eff}} \leq d_j\}$$ | Connects flight-slot pairs where the crew member can feasibly transfer. Conditions are the same as before, using $\delta_{\text{eff}}$ instead of $\delta$. Crew from any slot on flight $i$ can connect to any slot on flight $j$ since cabin crew are interchangeable. |
| **Sink Arc** $$A^{\text{e}} = \{((i,k), t_a) : (i,k) \in \hat{F},\ a = e_i\}$$ | Connects flight-slot $(i,k)$ to airport sink $t_a$ only when flight $i$ arrives at airport $a$. Combined with the source arc restriction, this ensures a crew member's first flight departs from and last flight arrives at the same airport. |

A compatibility arc from flight-slot $(i,k)$ to flight-slot $(j,l)$ exists when the same three conditions from the earlier models are met, with $\delta_{\text{eff}}$ replacing $\delta$:

 **1.** $\ i \neq j$ - The arc does not start and end with the same flight

 **2.** $e_i = b_j$ - The destination airport of flight $i$ is the same as the origin airport of flight $j$

 **3.** $a_i + \delta_{\text{eff}} \leq d_j$ - There is enough time to transfer from flight $i$ to flight $j$, including the delay buffer

### Decision Variables

| Variable | Domain | Definition |
|----------|--------|-----------|
| $x_{ij}$ | $\{0,1\}$, $\forall (i,j) \in A$ | **Arc Selection Variable:** Equals 1 if a crew member traverses arc $(i,j)$ as part of their route, 0 otherwise. Arcs now connect flight-slot nodes and airport-indexed sources/sinks. |
| $S_{(i,k)}$ | $\mathbb{R}_{\geq 0}$, $\forall (i,k) \in \hat{F}$ | **Shift Start Time Variable:** Records the clock-in time of the crew member assigned to slot $k$ on flight $i$. Since each slot is one person, this variable unambiguously tracks that individual's shift start. |

### Objective Function

| Function | Definition |
|----------|--------|
| $$\min \sum_{a \in K} \sum_{(i,k) \in \hat{F}} x_{s_a,(i,k)}$$ | Minimize the total number of crew members across all airports (total source arcs used) |

### Constraints

| Constraint | Formulation | Description |
|--------------------|-------------|-------------|
| **Flow Balance** *(in)* | $\sum_{u : (u,(i,k)) \in A} x_{u,(i,k)} = 1 \quad \forall (i,k) \in \hat{F}$ | Exactly one arc enters each flight-slot node. Since flight $i$ has $r_i$ slots, exactly $r_i$ crew members are assigned to flight $i$ in total. |
| **Flow Balance** *(out)* | $\sum_{v : ((i,k),v) \in A} x_{(i,k),v} = 1 \quad \forall (i,k) \in \hat{F}$ | Exactly one arc leaves each flight-slot node. Together with the Flow Balance (in) constraint, these ensure every crew position on every flight is covered exactly once. |
| **Shift Start Initialization** *(upper)* | $S_{(i,k)} \leq d_i + H(1 - x_{s_{b_i},(i,k)}) \quad \forall (i,k) \in \hat{F}$ | When $x_{s_{b_i},(i,k)} = 1$ (this slot's crew member starts at flight $i$), forces $S_{(i,k)} \leq d_i$. When $x_{s_{b_i},(i,k)} = 0$, the big-$M$ term relaxes the constraint. |
| **Shift Start Initialization** *(lower)* | $S_{(i,k)} \geq d_i - H(1 - x_{s_{b_i},(i,k)}) \quad \forall (i,k) \in \hat{F}$ | Combined with the upper constraint, this gives $S_{(i,k)} = d_i$ when flight $i$ is the first flight in this crew member's route. |
| **Shift Start Propagation** *(upper)* | $S_{(j,l)} \leq S_{(i,k)} + H(1 - x_{(i,k),(j,l)}) \quad \forall ((i,k),(j,l)) \in A^{\text{c}}$ | When $x_{(i,k),(j,l)} = 1$ (same crew member operates both slots), forces $S_{(j,l)} \leq S_{(i,k)}$. |
| **Shift Start Propagation** *(lower)* | $S_{(j,l)} \geq S_{(i,k)} - H(1 - x_{(i,k),(j,l)}) \quad \forall ((i,k),(j,l)) \in A^{\text{c}}$ | Combined with the upper constraint, this gives $S_{(j,l)} = S_{(i,k)}$, carrying the shift start time forward along the route. |
| **Max Shift Duration** | $a_i - S_{(i,k)} \leq H \quad \forall (i,k) \in \hat{F}$ | The arrival time of flight $i$ minus the crew member's shift start cannot exceed $H$ minutes. |
| **Symmetry Breaking** *(optional)* | $S_{(i,1)} \leq S_{(i,2)} \leq \cdots \leq S_{(i,r_i)} \quad \forall i \in F$ | Slots within the same flight are interchangeable, so this ordering constraint assigns earlier-starting crew to lower-numbered slots. This helps the solver prune equivalent solutions without changing the optimal objective value. |

### Full Flight Schedule Model Summary

$\min \sum_{a \in K} \sum_{(i,k) \in \hat{F}} x_{s_a,(i,k)}$

$\text{Subject to:}$

$\sum_{u : (u,(i,k)) \in A} x_{u,(i,k)} = 1 \quad \forall (i,k) \in \hat{F}$

$\sum_{v : ((i,k),v) \in A} x_{(i,k),v} = 1 \quad \forall (i,k) \in \hat{F}$

$S_{(i,k)} \leq d_i + H(1 - x_{s_{b_i},(i,k)}) \quad \forall (i,k) \in \hat{F}$

$S_{(i,k)} \geq d_i - H(1 - x_{s_{b_i},(i,k)}) \quad \forall (i,k) \in \hat{F}$

$S_{(j,l)} \leq S_{(i,k)} + H(1 - x_{(i,k),(j,l)}) \quad \forall ((i,k),(j,l)) \in A^{\text{c}}$

$S_{(j,l)} \geq S_{(i,k)} - H(1 - x_{(i,k),(j,l)}) \quad \forall ((i,k),(j,l)) \in A^{\text{c}}$

$a_i - S_{(i,k)} \leq H \quad \forall (i,k) \in \hat{F}$

$S_{(i,1)} \leq S_{(i,2)} \leq \cdots \leq S_{(i,r_i)} \quad \forall i \in F$

$x_{ij} \in \{0,1\} \quad \forall (i,j) \in A$

$S_{(i,k)} \geq 0,\ S_{(i,k)} \in \mathbb{R} \quad \forall (i,k) \in \hat{F}$

We run this model once for cabin crew (using $r_i^{\text{min}}$ and $r_i^{\text{max}}$ from the aircraft data) and once for each aircraft type's pilots (using $r_i^{\text{pilot}}$ within each type-specific sub-network from the pilot model). The total crew for the full flight schedule is:

$$\text{Total crew} = \text{Cabin crew total} + \sum_{q \in P} \text{Pilot total for type } q$$

---