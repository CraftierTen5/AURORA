"""
AURORA Assignment Engine Package
Provides feasibility checking and runway assignment policy.
"""
from .engine import AssignmentEngine, AssignmentResult, FeasibilityStatus
from .config import SEPARATION_MINUTES

__all__ = ["AssignmentEngine", "AssignmentResult", "FeasibilityStatus", "SEPARATION_MINUTES"]
