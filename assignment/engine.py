"""
AURORA Assignment Engine
------------------------
Core runway-assignment logic, independent of Pygame rendering.
Implements a deterministic feasibility-aware assignment policy:
  1. Validate the operation (fields, direction permissions, compat matrix, restrictions).
  2. Check availability against existing assignments (separation window).
  3. Try the preferred direction first, then alternatives in stable order.
  4. Persist successful assignments; leave unassignable operations unassigned.

This is an academic simulator. Assignment decisions are NOT certified aviation
safety guidance and must not be used for real air traffic control.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from .config import SEPARATION_MINUTES


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

class FeasibilityStatus(Enum):
    PASS = "PASS"
    FAIL_NO_OPERATION = "FAIL_NO_OPERATION"
    FAIL_NO_DIRECTION = "FAIL_NO_DIRECTION"
    FAIL_AIRPORT_MISMATCH = "FAIL_AIRPORT_MISMATCH"
    FAIL_DIRECTION_PERMISSION = "FAIL_DIRECTION_PERMISSION"
    FAIL_RUNWAY_CLOSED = "FAIL_RUNWAY_CLOSED"
    FAIL_INCOMPATIBLE = "FAIL_INCOMPATIBLE"
    FAIL_NO_COMPAT_RECORD = "FAIL_NO_COMPAT_RECORD"
    FAIL_RESTRICTION = "FAIL_RESTRICTION"
    FAIL_MISSING_DATA = "FAIL_MISSING_DATA"
    FAIL_OCCUPIED = "FAIL_OCCUPIED"
    FAIL_NO_ALTERNATIVE = "FAIL_NO_ALTERNATIVE"
    FAIL_DB_ERROR = "FAIL_DB_ERROR"


@dataclass
class FeasibilityResult:
    status: FeasibilityStatus
    reason: str
    direction_id: Optional[int] = None
    runway_id: Optional[int] = None


@dataclass
class AssignmentResult:
    operation_id: int
    flight_number: str
    operation_type: str
    scheduled_datetime: str
    airport_code: str
    preferred_direction: Optional[str] = None
    assigned_direction_id: Optional[int] = None
    assigned_direction: Optional[str] = None
    assigned_runway: Optional[str] = None
    success: bool = False
    reason: str = ""
    messages: list[str] = field(default_factory=list)

    def add_msg(self, msg: str):
        self.messages.append(msg)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class AssignmentEngine:
    """
    Runway assignment engine.

    Parameters
    ----------
    db_fetch_all : callable — wraps db.fetch_all
    db_fetch_one : callable — wraps db.fetch_one
    db_execute   : callable — wraps db.execute
    separation_minutes : int — configurable simulation occupancy window
    """

    def __init__(self, db_fetch_all, db_fetch_one, db_execute,
                 separation_minutes: int = SEPARATION_MINUTES):
        self._fetch_all = db_fetch_all
        self._fetch_one = db_fetch_one
        self._execute   = db_execute
        self.separation_minutes = separation_minutes

        # Track assignments made during the current batch (operation_id → runway_id)
        # so that within-batch conflicts are also detected.
        self._batch_assignments: dict[int, tuple[int, datetime]] = {}

    def reset_batch(self):
        """Call before processing a new batch of operations."""
        self._batch_assignments = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assign_operation(
        self,
        operation_id: int,
        preferred_direction_id: Optional[int] = None,
        overwrite_existing: bool = False,
    ) -> AssignmentResult:
        """
        Attempt to assign a runway to one flight operation.

        Policy
        ------
        1. Load the operation.
        2. Check if already assigned; respect overwrite_existing flag.
        3. Validate and try the preferred direction.
        4. If preferred fails, evaluate alternatives in stable order.
        5. Assign the first eligible alternative.
        6. If none, leave unassigned with reason.
        """
        # 1. Load operation
        op = self._load_operation(operation_id)
        if op is None:
            return AssignmentResult(
                operation_id=operation_id, flight_number="?",
                operation_type="?", scheduled_datetime="?", airport_code="?",
                success=False,
                reason=f"Operation ID {operation_id} not found in database.",
            )

        result = AssignmentResult(
            operation_id=operation_id,
            flight_number=op["flight_number"],
            operation_type=op["operation_type"],
            scheduled_datetime=str(op["scheduled_datetime"]),
            airport_code=op["airport_code"],
        )

        # 2. Check existing assignment
        existing = self._get_existing_assignment(operation_id)
        if existing and not overwrite_existing:
            assigned_dir = self._fetch_one(
                "SELECT designation, runway_id FROM runway_direction WHERE direction_id = %s",
                (existing["direction_id"],)
            )
            rw_desig = ""
            if assigned_dir:
                rw = self._fetch_one(
                    "SELECT runway_designation FROM runway WHERE runway_id = %s",
                    (assigned_dir["runway_id"],)
                )
                rw_desig = rw["runway_designation"] if rw else ""
            result.assigned_direction_id = existing["direction_id"]
            result.assigned_direction = assigned_dir["designation"] if assigned_dir else "?"
            result.assigned_runway = rw_desig
            result.success = True
            result.reason = "Already assigned (skipped — use overwrite_existing=True to re-run)."
            result.add_msg(f"[SKIP] {op['flight_number']}: already has assignment (direction {result.assigned_direction}). Skipping.")
            return result

        # 3. Load all eligible directions for this airport
        all_directions = self._get_directions_for_airport(op["airport_id"])
        if not all_directions:
            result.success = False
            result.reason = "No runway directions defined for this airport in the database."
            result.add_msg(f"[FAIL] {op['flight_number']}: No directions found for airport_id={op['airport_id']}.")
            return result

        # Stable ordering: preferred first, then by direction_id ASC
        ordered = []
        if preferred_direction_id:
            preferred = [d for d in all_directions if d["direction_id"] == preferred_direction_id]
            others    = [d for d in all_directions if d["direction_id"] != preferred_direction_id]
            ordered   = preferred + sorted(others, key=lambda d: d["direction_id"])
            if preferred:
                result.preferred_direction = preferred[0]["designation"]
                result.add_msg(f"[INFO] {op['flight_number']}: Trying preferred direction {preferred[0]['designation']} first.")
            else:
                result.add_msg(f"[WARN] {op['flight_number']}: Preferred direction_id={preferred_direction_id} not found for this airport; trying alternatives.")
        else:
            ordered = sorted(all_directions, key=lambda d: d["direction_id"])
            result.add_msg(f"[INFO] {op['flight_number']}: No preferred direction specified; evaluating all {len(ordered)} direction(s) in order.")

        # 4. Try each direction
        last_reason = "No eligible runway direction found."
        for direction in ordered:
            feas = self._check_feasibility(op, direction)
            is_preferred = (direction["direction_id"] == preferred_direction_id)
            tag = "PREFERRED" if is_preferred else "ALT"

            if feas.status != FeasibilityStatus.PASS:
                result.add_msg(
                    f"[{tag}] Direction {direction['designation']} ({direction['runway_designation']}): REJECTED — {feas.reason}"
                )
                last_reason = feas.reason
                continue

            # Availability check
            avail = self._check_availability(op, direction)
            if avail.status != FeasibilityStatus.PASS:
                result.add_msg(
                    f"[{tag}] Direction {direction['designation']}: OCCUPIED — {avail.reason}"
                )
                last_reason = avail.reason
                continue

            # 5. Commit assignment
            commit_ok, commit_msg = self._commit_assignment(
                op, direction, existing, overwrite_existing
            )
            if commit_ok:
                result.assigned_direction_id = direction["direction_id"]
                result.assigned_direction = direction["designation"]
                result.assigned_runway = direction["runway_designation"]
                result.success = True
                result.reason = f"Assigned direction {direction['designation']} on {direction['runway_designation']}."
                result.add_msg(f"[OK] {op['flight_number']}: {result.reason}")
                # Track in batch
                sched_dt = self._parse_dt(str(op["scheduled_datetime"]))
                if sched_dt:
                    self._batch_assignments[operation_id] = (direction["runway_id"], sched_dt)
                return result
            else:
                result.add_msg(f"[ERR] DB write failed for direction {direction['designation']}: {commit_msg}")
                last_reason = f"Database error: {commit_msg}"

        result.success = False
        result.reason = last_reason
        result.add_msg(f"[FAIL] {op['flight_number']}: Unassigned. Last reason: {last_reason}")
        return result

    def assign_batch(
        self,
        operation_ids: list[int],
        preferred_map: Optional[dict[int, int]] = None,
        overwrite_existing: bool = False,
    ) -> list[AssignmentResult]:
        """
        Process a list of operations in deterministic order (scheduled_datetime ASC, then operation_id ASC).

        Parameters
        ----------
        operation_ids    : list of operation IDs to process
        preferred_map    : {operation_id: preferred_direction_id}
        overwrite_existing: if True, re-assign already-assigned operations
        """
        self.reset_batch()
        preferred_map = preferred_map or {}

        # Sort by scheduled_datetime then operation_id for determinism
        ops_with_time = []
        for oid in operation_ids:
            op = self._load_operation(oid)
            if op:
                ops_with_time.append((str(op["scheduled_datetime"]), oid))
            else:
                ops_with_time.append(("9999", oid))
        ops_with_time.sort()

        results = []
        for _, oid in ops_with_time:
            pref = preferred_map.get(oid)
            r = self.assign_operation(oid, preferred_direction_id=pref,
                                      overwrite_existing=overwrite_existing)
            results.append(r)
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_operation(self, operation_id: int) -> Optional[dict]:
        return self._fetch_one("""
            SELECT fo.operation_id, fo.airport_id, fo.operation_type,
                   fo.scheduled_datetime, fo.operation_status,
                   f.flight_number, f.aircraft_id,
                   ac.type_id, ac.registration_number,
                   act.model AS aircraft_model,
                   act.min_runway_length,
                   ap.iata_code AS airport_code
            FROM flight_operation fo
            JOIN flight f ON fo.flight_id = f.flight_id
            JOIN aircraft ac ON f.aircraft_id = ac.aircraft_id
            JOIN aircraft_type act ON ac.type_id = act.type_id
            JOIN airport ap ON fo.airport_id = ap.airport_id
            WHERE fo.operation_id = %s
        """, (operation_id,))

    def _get_existing_assignment(self, operation_id: int) -> Optional[dict]:
        return self._fetch_one(
            "SELECT assignment_id, direction_id FROM runway_assignment WHERE operation_id = %s",
            (operation_id,)
        )

    def _get_directions_for_airport(self, airport_id: int) -> list[dict]:
        return self._fetch_all("""
            SELECT rd.direction_id, rd.designation, rd.heading,
                   rd.landing_permitted, rd.takeoff_permitted,
                   rd.ils_available, rd.approach_category,
                   rw.runway_id, rw.runway_designation,
                   rw.runway_length, rw.runway_status,
                   rw.airport_id
            FROM runway_direction rd
            JOIN runway rw ON rd.runway_id = rw.runway_id
            WHERE rw.airport_id = %s
            ORDER BY rd.direction_id ASC
        """, (airport_id,))

    def _check_feasibility(self, op: dict, direction: dict) -> FeasibilityResult:
        """Run all feasibility checks for one (operation, direction) pair."""

        # A. Airport alignment
        if op["airport_id"] != direction["airport_id"]:
            return FeasibilityResult(
                FeasibilityStatus.FAIL_AIRPORT_MISMATCH,
                f"Airport mismatch: operation at airport_id={op['airport_id']}, "
                f"direction belongs to airport_id={direction['airport_id']}."
            )

        # B. Direction permission
        op_type = op["operation_type"]
        if op_type == "LANDING" and not direction["landing_permitted"]:
            return FeasibilityResult(
                FeasibilityStatus.FAIL_DIRECTION_PERMISSION,
                f"Direction {direction['designation']} does not permit LANDING."
            )
        if op_type == "TAKEOFF" and not direction["takeoff_permitted"]:
            return FeasibilityResult(
                FeasibilityStatus.FAIL_DIRECTION_PERMISSION,
                f"Direction {direction['designation']} does not permit TAKEOFF."
            )

        # C. Runway physical status
        if direction["runway_status"] != "OPEN":
            return FeasibilityResult(
                FeasibilityStatus.FAIL_RUNWAY_CLOSED,
                f"Runway {direction['runway_designation']} status is '{direction['runway_status']}', not OPEN."
            )

        # D. Aircraft type compatibility matrix
        compat = self._fetch_one("""
            SELECT landing_eligible, takeoff_eligible, remarks
            FROM aircraft_runway_compatibility
            WHERE type_id = %s AND runway_id = %s
        """, (op["type_id"], direction["runway_id"]))

        if compat is None:
            # No record = not certified in this simulation
            return FeasibilityResult(
                FeasibilityStatus.FAIL_NO_COMPAT_RECORD,
                f"No compatibility record for aircraft type_id={op['type_id']} "
                f"on runway {direction['runway_designation']}. "
                f"This is treated as ineligible (missing mandatory data)."
            )

        if op_type == "LANDING" and not compat["landing_eligible"]:
            return FeasibilityResult(
                FeasibilityStatus.FAIL_INCOMPATIBLE,
                f"Aircraft {op['aircraft_model']} cannot LAND on {direction['runway_designation']}. "
                f"Remarks: {compat['remarks'] or 'Ineligible per compatibility matrix.'}"
            )
        if op_type == "TAKEOFF" and not compat["takeoff_eligible"]:
            return FeasibilityResult(
                FeasibilityStatus.FAIL_INCOMPATIBLE,
                f"Aircraft {op['aircraft_model']} cannot TAKEOFF from {direction['runway_designation']}. "
                f"Remarks: {compat['remarks'] or 'Ineligible per compatibility matrix.'}"
            )

        # E. Runway length vs aircraft minimum requirement
        min_len = op.get("min_runway_length")
        rwy_len = direction.get("runway_length")
        if min_len is not None and rwy_len is not None:
            try:
                if float(rwy_len) < float(min_len):
                    return FeasibilityResult(
                        FeasibilityStatus.FAIL_INCOMPATIBLE,
                        f"Runway {direction['runway_designation']} length {float(rwy_len):.0f}m "
                        f"is shorter than aircraft minimum {float(min_len):.0f}m."
                    )
            except (TypeError, ValueError):
                pass  # If conversion fails, do not silently pass — but data was present

        # F. Active restrictions
        sched = str(op["scheduled_datetime"])
        restriction = self._fetch_one("""
            SELECT restriction_id, restriction_type, start_datetime, end_datetime, description
            FROM runway_restriction
            WHERE runway_id = %s
              AND restriction_status IN ('SCHEDULED', 'ACTIVE')
              AND %s BETWEEN start_datetime AND end_datetime
        """, (direction["runway_id"], sched))

        if restriction:
            return FeasibilityResult(
                FeasibilityStatus.FAIL_RESTRICTION,
                f"Active {restriction['restriction_type']} restriction on runway "
                f"{direction['runway_designation']} during scheduled time {sched}. "
                f"Window: {restriction['start_datetime']} → {restriction['end_datetime']}. "
                f"Details: {restriction['description'] or 'N/A'}"
            )

        return FeasibilityResult(FeasibilityStatus.PASS, "All feasibility checks passed.")

    def _check_availability(self, op: dict, direction: dict) -> FeasibilityResult:
        """
        Check whether the physical runway (not just direction) is free during
        the required separation window for the operation's scheduled time.

        Both directions of the same physical runway share the same surface resource.
        An existing assignment to EITHER direction of the same runway within
        SEPARATION_MINUTES of this operation's scheduled_datetime is a conflict.
        """
        sched_dt = self._parse_dt(str(op["scheduled_datetime"]))
        if sched_dt is None:
            return FeasibilityResult(
                FeasibilityStatus.FAIL_MISSING_DATA,
                "Cannot parse scheduled_datetime; availability check skipped as fail-safe."
            )

        window_start = sched_dt - timedelta(minutes=self.separation_minutes)
        window_end   = sched_dt + timedelta(minutes=self.separation_minutes)
        runway_id    = direction["runway_id"]

        # Check DB-committed assignments on the same physical runway
        conflicts = self._fetch_all("""
            SELECT ra.operation_id, ra.assignment_id,
                   fo.scheduled_datetime, rd.designation
            FROM runway_assignment ra
            JOIN flight_operation fo ON ra.operation_id = fo.operation_id
            JOIN runway_direction rd ON ra.direction_id = rd.direction_id
            WHERE rd.runway_id = %s
              AND ra.assignment_status = 'CONFIRMED'
              AND fo.operation_id != %s
        """, (runway_id, op["operation_id"]))

        for c in conflicts:
            c_dt = self._parse_dt(str(c["scheduled_datetime"]))
            if c_dt and window_start <= c_dt <= window_end:
                diff = abs((c_dt - sched_dt).total_seconds() / 60)
                return FeasibilityResult(
                    FeasibilityStatus.FAIL_OCCUPIED,
                    f"Runway {direction['runway_designation']} is occupied: operation "
                    f"{c['operation_id']} assigned direction {c['designation']} "
                    f"at {c['scheduled_datetime']} ({diff:.0f} min apart, "
                    f"minimum separation {self.separation_minutes} min)."
                )

        # Also check within-batch assignments (not yet committed to DB)
        for batch_op_id, (batch_rwy_id, batch_dt) in self._batch_assignments.items():
            if batch_rwy_id == runway_id and batch_op_id != op["operation_id"]:
                if window_start <= batch_dt <= window_end:
                    diff = abs((batch_dt - sched_dt).total_seconds() / 60)
                    return FeasibilityResult(
                        FeasibilityStatus.FAIL_OCCUPIED,
                        f"Runway {direction['runway_designation']} is occupied (within-batch): "
                        f"operation {batch_op_id} assigned to same physical runway "
                        f"at {batch_dt.isoformat()} ({diff:.0f} min apart)."
                    )

        return FeasibilityResult(FeasibilityStatus.PASS, "Runway is available.")

    def _commit_assignment(
        self, op: dict, direction: dict, existing: Optional[dict], overwrite: bool
    ) -> tuple[bool, str]:
        """Insert or update runway_assignment. Returns (success, error_msg)."""
        try:
            if existing and overwrite:
                self._execute("""
                    UPDATE runway_assignment
                    SET direction_id = %s,
                        assignment_status = 'CONFIRMED',
                        assignment_datetime = NOW(),
                        assigned_by = 'AURORA_ENGINE',
                        remarks = 'Re-assigned by AURORA engine'
                    WHERE operation_id = %s
                """, (direction["direction_id"], op["operation_id"]))
            else:
                self._execute("""
                    INSERT INTO runway_assignment
                        (operation_id, direction_id, assignment_status, assigned_by, remarks)
                    VALUES (%s, %s, 'CONFIRMED', 'AURORA_ENGINE',
                            'Auto-assigned by AURORA engine')
                """, (op["operation_id"], direction["direction_id"]))
            return True, ""
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def _parse_dt(dt_str: str) -> Optional[datetime]:
        """Parse ISO or SQLite datetime string to datetime object."""
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
            try:
                return datetime.strptime(dt_str.strip(), fmt)
            except ValueError:
                continue
        return None
