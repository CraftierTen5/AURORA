"""
AURORA Assignment Engine — Simulation Configuration
----------------------------------------------------
SEPARATION_MINUTES: minimum runway occupancy interval between two operations
on the same physical runway. This is a SIMULATION PARAMETER for academic
demonstration purposes and does not represent any real-world aviation
separation standard or ATC rule.

Edit SEPARATION_MINUTES here to change the simulation's time-window rule.
"""

# Minimum time separation (in minutes) between operations on the same physical runway.
# Two operations whose scheduled_datetime values differ by less than this value
# are considered conflicting and cannot share the same physical runway.
SEPARATION_MINUTES = 15   # ← configurable simulation parameter
