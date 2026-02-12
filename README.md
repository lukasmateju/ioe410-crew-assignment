# Airline Crew Assignment Optimization Project
IOE 410
Project Members: Megan Gottfried, Lukas Mateju

## Overview

This project formulates and solves an airline crew assignment problem using mixed-integer linear programming in Python with Gurobi.

The goal is to determine the **minimum number of crews** required to operate all scheduled flights while satisfying operational constraints such as:

- Maximum shift length  
- Minimum connection time between flights  
- Flight coverage requirements  
- Optional policy constraints (e.g., same start/end airport)

