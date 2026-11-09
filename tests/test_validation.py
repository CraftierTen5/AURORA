"""
AURORA - Automated Test Suite
Verifies validation rules, constraints, edge cases, and transaction handling.
Requires the MySQL database initialized by the Workbench installer or setup_db.py.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validator import validate_runway_assignment
from db import fetch_one, execute

def run_tests():
    print("=" * 65)
    print("   AURORA: Automated Validation & Database Test Suite")
    print("=" * 65)

    passed = 0
    failed = 0

    def assert_test(name, condition, msg=""):
        nonlocal passed, failed
        if condition:
            print(f" [PASS] {name}")
            passed += 1
        else:
            print(f" [FAIL] {name}: {msg}")
            failed += 1

    try:
        # TEST 1: Valid Manual Runway Assignment
        # Operation 1 is TAKEOFF at DFW (Airport 1). Direction 4 is Runway 35C at DFW.
        res1 = validate_runway_assignment(1, 4)
        assert_test("Valid Assignment (DFW TAKEOFF on Runway 35C)", res1.is_valid, res1.reason)

        # TEST 2: Wrong Airport Rejection
        # Operation 1 is at DFW (Airport 1). Direction 8 belongs to LHR (Airport 2)!
        res2 = validate_runway_assignment(1, 8)
        assert_test("Airport Mismatch Rejection", 
                    (not res2.is_valid and "AIRPORT MISMATCH" in res2.reason), 
                    f"Expected rejection, got: {res2.reason}")

        # TEST 3: Direction Restriction Rejection
        # Direction 13 (BOM Runway 14) has takeoff_permitted = 0
        # Find an operation at BOM (Airport 3) with operation_type = TAKEOFF (e.g. Operation 3)
        res3 = validate_runway_assignment(3, 13)
        assert_test("Direction Takeoff Restriction Rejection",
                    (not res3.is_valid and "DIRECTION RESTRICTION" in res3.reason),
                    f"Expected rejection, got: {res3.reason}")

        # TEST 4: Direction Landing Restriction Rejection
        # Direction 14 (BOM Runway 32) has landing_permitted = 0
        # Find an operation at BOM (Airport 3) with operation_type = LANDING (e.g. Operation 2)
        res4 = validate_runway_assignment(2, 14)
        assert_test("Direction Landing Restriction Rejection",
                    (not res4.is_valid and "DIRECTION RESTRICTION" in res4.reason),
                    f"Expected rejection, got: {res4.reason}")

        # TEST 5: Aircraft Type Compatibility Rejection (B777 on DFW 17L/35R)
        # Operation 5 is B777-300ER TAKEOFF at DFW.
        # Direction 1 (Runway 1 DFW 17L/35R) is only 2591m -> Ineligible for B777!
        res5 = validate_runway_assignment(5, 1)
        assert_test("Aircraft Incompatibility Rejection (Heavy B777 on short 17L/35R)",
                    (not res5.is_valid and "INCOMPATIBLE AIRFRAME" in res5.reason),
                    f"Expected rejection, got: {res5.reason}")

        # TEST 6: Compatible Aircraft Acceptance (B777 on DFW 18R/36L)
        # Direction 6 (Runway 3 DFW 18R/36L) is 4084m -> Eligible for B777!
        res6 = validate_runway_assignment(5, 6)
        assert_test("Compatible Aircraft Acceptance (Heavy B777 on wide 18R/36L)",
                    res6.is_valid,
                    res6.reason)

        # TEST 7: Active Restriction / Maintenance Window Conflict
        # Runway 3 (DFW 18R/36L) has LIGHTING_MAINTENANCE on Oct 15 from 13:00 to 17:00.
        # Find an operation on DFW between 13:00 and 17:00 (e.g. Operation 17 scheduled at 15:00:00)
        res7 = validate_runway_assignment(17, 6) # Direction 6 belongs to Runway 3
        assert_test("Runway Restriction Window Rejection (Scheduled Maintenance)",
                    (not res7.is_valid and "RUNWAY RESTRICTION CONFLICT" in res7.reason),
                    f"Expected restriction conflict, got: {res7.reason}")

        # TEST 8: Non-existent Operation Error
        res8 = validate_runway_assignment(99999, 1)
        assert_test("Non-existent Operation Error Handling",
                    not res8.is_valid,
                    res8.reason)

        # TEST 9: Non-existent Direction Error
        res9 = validate_runway_assignment(1, 99999)
        assert_test("Non-existent Direction Error Handling",
                    not res9.is_valid,
                    res9.reason)

        # TEST 10: Manual Input Validation (Valid)
        from validator import validate_manual_input
        res10 = validate_manual_input(1, "AA-101", "08:00:00", 160, "35C")
        assert_test("Manual Input Validation (Valid Runway 35C)", res10.is_valid, res10.reason)

        # TEST 11: Manual Input Validation (Weight Incompatible on short 17L/35R)
        res11 = validate_manual_input(1, "B777-Heavy", "08:00:00", 350, "17L")
        assert_test("Manual Input Validation (Heavy Weight Rejection)",
                    (not res11.is_valid and "INCOMPATIBLE AIRFRAME" in res11.reason),
                    f"Expected rejection, got: {res11.reason}")

        # TEST 12: Manual Input Validation (Maintenance Window Rejection)
        res12 = validate_manual_input(1, "Flight-X", "14:30:00", 160, "36L")
        assert_test("Manual Input Validation (Maintenance Window Conflict)",
                    (not res12.is_valid and "RUNWAY RESTRICTION CONFLICT" in res12.reason),
                    f"Expected conflict, got: {res12.reason}")

    except Exception as e:
        print(f"\n[ERROR] Test run encountered database exception: {e}")
        print("Note: Ensure MySQL is running and setup_db.py has been executed.")
        failed += 1

    print("\n" + "=" * 65)
    print(f" Test Results: {passed} PASSED, {failed} FAILED")
    print("=" * 65)

    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
