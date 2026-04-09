# Airline Crew Assignment Optimization Project
> **IOE 410 Project** | Megan Gottfried, Lukas Mateju
## Overview

This project formulates and solves an airline crew assignment problem using mixed-integer linear programming in Python with Gurobi.

The goal is to determine the **minimum number of crews** required to operate all scheduled flights while satisfying operational constraints such as:

- Maximum shift length  
- Minimum connection time between flights  
- Flight coverage requirements  
- Optional policy constraints (e.g., same start/end airport)


---

## Problem Description

An airline must assign cabin crew to all scheduled flights on a given day across $n$ airports. A crew member may serve a sequence of multiple flights provided there is sufficient transfer time between consecutive flights. There is also a maximum limit on total shift length. The goal is to **minimize the total number of crew members** needed to cover all flights.

---

## Network Formulation

The problem is modeled as a **minimum-flow / set-cover** problem on a directed compatibility graph.

### Sets

| Symbol | Definition |
|--------|-----------|
| $F = \{1, 2, \ldots, n\}$ | Set of all scheduled flights |
| $N = \{s\} \cup F \cup \{t\}$ | Node set: source $s$, all flights, and sink $t$ |
| $A$ | Set of all directed arcs (defined below) |
| $G = (N, A)$ | Directed compatibility graph |

### Arc Types

The arc set $A$ contains three types of arcs:

- **Source arcs** $(s, i)$ for all $i \in F$ — crew starts their shift at flight $i$
- **Compatibility arcs** $(i, j)$ for $i, j \in F,\ i \neq j$, when:
  - $e_i = b_j$
  - $a_i + \delta \le d_j$
- **Ending arcs** $(i, t)$ for all $i \in F$ — crew ends their shift after flight $i$

That is, a compatibility arc $(i, j)$ exists only when the destination of flight $i$ matches the origin of flight $j$, and there is enough time to connect.

Let $A = A^{\text{start}} \cup A^{\text{comp}} \cup A^{\text{end}}$, where:

- $A^{\text{start}} = \{(s,i) : i \in F\}$
- $A^{\text{comp}} = \{(i,j) : i,j \in F,\ i \neq j,\ e_i = b_j,\ a_i + \delta \le d_j\}$
- $A^{\text{end}} = \{(i,t) : i \in F\}$

### Flight Parameters

| Symbol | Definition |
|--------|-----------|
| $d_i$ | Departure time of flight $i$ (minutes after 00:00), $i \in F$ |
| $a_i$ | Arrival time of flight $i$ (minutes after 00:00), $i \in F$ |
| $b_i$ | Origin airport of flight $i$, $i \in F$ |
| $e_i$ | Destination airport of flight $i$, $i \in F$ |
| $r_i$ | Number of crew needed for flight $i$, $i \in F$ |

### Constants

| Symbol | Value | Definition |
|--------|-------|-----------|
| $\delta$ | 60 min | Minimum transfer time between consecutive flights |
| $H$ | 660 min | Maximum total shift length (11 hours) |

---

## Decision Variables

- **Arc selection variable:** for every arc $(i,j) \in A$,
  - $x_{ij} \in \{0,1\}$

where

- $x_{ij} = 1$ if a crew goes directly from node $i$ to node $j$
- $x_{ij} = 0$ otherwise

Interpretation:

- $x_{si} = 1$ means a crew starts with flight $i$
- $x_{ij} = 1$ for $(i,j) \in A^{\text{comp}}$ means the same crew does flight $i$ and then flight $j$
- $x_{it} = 1$ means the crew ends after flight $i$

- **Shift-start-time variable:** for each flight $i \in F$,
  - $S_i \ge 0$

Here, $S_i$ is the start time of the crew assigned to flight $i$, meaning the departure time of the first flight in that crew’s sequence.

---

## Objective Function

Minimize the total number of crew members, equivalent to minimizing the number of source arcs used (each source arc represents one crew member starting a shift):

$$\min \sum_{i \in F} x_{si}$$

---

## Constraints

### 1. Flow Balance — Each Flight Covered per Airplane Capicity

Every flight must have the exact number of crew arriving into it and the exact number of crew departing from it that each airplane requires:

$$\sum_{\substack{k: (k,i) \in A}} x_{ki} = r_i \quad \forall i \in F$$

$$\sum_{\substack{k: (i,k) \in A}} x_{ik} = r_i \quad \forall i \in F$$

### 2. Shift Start Initialization

When crew is assigned to source arc $(s, i)$ (i.e., flight $i$ is the *first* flight in their shift), the shift start time $S_i$ is set to the departure time $d_i$. The following big-$M$ constraints enforce this:

$$S_i \leq d_i + H(1 - x_{si}) \quad \forall i \in F$$

$$S_i \geq d_i - H(1 - x_{si}) \quad \forall i \in F$$

Together, constraints (2a) and (2b) force $S_i = d_i$ when $x_{si} = 1$.

### 3. Shift Start Propagation

For flight-to-flight arcs only:

$$S_j \le S_i + H(1 - x_{ij}) \qquad \forall (i,j) \in A^{\text{comp}}$$

$$S_j \ge S_i - H(1 - x_{ij}) \qquad \forall (i,j) \in A^{\text{comp}}$$

If $x_{ij} = 1$, these force $S_j = S_i$.

So if the same crew does flight $i$ and then flight $j$, the crew’s shift-start time is the same for both flights. That makes sense because both flights belong to the same workday.

### 4. Maximum Shift Duration

The total shift length must not exceed $H$ minutes:

$$a_i - S_i \le H \qquad \forall i \in F$$

### 5. Start and End at the Same Airport 

The total shift length must not exceed $H$ minutes:

$$a_i - S_i \le H \qquad \forall i \in F$$

---

## Complete Model Summary

$$\min \sum_{i \in F} x_{si}$$

**Subject to:**

$$\sum_{\substack{k: (k,i) \in A}} x_{ki} = 1, \quad \forall i \in F$$

$$\sum_{\substack{k: (i,k) \in A}} x_{ik} = 1, \quad \forall i \in F$$

$$S_i \leq d_i + H(1 - x_{si}), \quad \forall i \in F$$

$$S_i \geq d_i - H(1 - x_{si}), \quad \forall i \in F$$

$$S_j \le S_i + H(1 - x_{ij}) \qquad \forall (i,j) \in A^{\text{comp}}$$

$$S_j \ge S_i - H(1 - x_{ij}) \qquad \forall (i,j) \in A^{\text{comp}}$$

$$a_i - S_i \leq H, \quad \forall i \in F$$

$$x_{ij} \in \{0,1\}, \quad \forall (i,j) \in A$$

$$S_i \geq 0, \quad S_i \in \mathbb{R}, \quad \forall i \in F$$

---
