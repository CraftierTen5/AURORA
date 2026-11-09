# AURORA — Database Design & Concepts Report
**Aircraft & Unified Runway Operations Records Archive**
*Academic Project — Class 12 Computer Science, 12'B'*

---

## 1. Schema Overview

AURORA uses **18 operational InnoDB tables** plus **4 RBAC tables** in MySQL 8.0+. The operational relations are grouped into four domains; views are separate query objects and do not count as base tables.

| Group | Tables |
|---|---|
| Carrier Registry | `airline`, `aircraft_type`, `aircraft` |
| Airport Infrastructure | `airport`, `runway`, `runway_direction`, `taxiway`, `terminal`, `aircraft_stand` |
| Operations | `flight`, `flight_operation`, `runway_assignment`, `assignment_audit` |
| Rules & Metadata | `aircraft_runway_compatibility`, `runway_restriction`, `airport_operating_hours`, `airport_map`, `map_feature` |
| Application Security | `app_user`, `app_role`, `app_permission`, `role_permission` (four additional RBAC tables) |

---

## 2. Key Table Attributes & Design Decisions

### `aircraft_type`
Stores certified physical parameters per model variant.
- `min_runway_length` — simplified compatibility threshold (documented as a demonstration rule, not an aviation certification).
- `CHECK` constraints enforce domain integrity: `wingspan > 0`, `max_landing_weight <= max_takeoff_weight`, etc.
- `UNIQUE (manufacturer, model, variant)` — prevents duplicate type registrations.

### `runway` + `runway_direction`
A **physical runway** (e.g., `17L/35R`) is one row in `runway`; its **two operational directions** (e.g., `17L` and `35R`) are separate rows in `runway_direction`. This is the key decomposition — all assignments reference a *direction*, not just a physical surface, because headings, ILS availability, and permitted operations differ per end.

Key direction attributes: `heading`, `landing_permitted`, `takeoff_permitted`, `ils_available`, `approach_category`.

### `flight_operation`
Separates an individual landing or takeoff event from the flight record itself.
- `scheduled_datetime`, `estimated_datetime`, `actual_datetime` — three temporal columns allow delay tracking without modifying the canonical schedule.
- A single `flight` may produce multiple `flight_operation` rows (e.g., outbound + return, or a diversion) — the relationship is intentionally *one-to-many*.

### `runway_assignment`
Links a `flight_operation` to a specific `runway_direction` with status tracking (`PROPOSED`, `CONFIRMED`, `CANCELLED`). The `assigned_by` column records the operator who made the manual assignment — important for the audit trigger chain.

### `aircraft_runway_compatibility`
A composite-key table `(type_id, runway_id)` acting as an explicit eligibility matrix. Columns `landing_eligible` and `takeoff_eligible` are TINYINT(1) booleans. The `validator.py` module queries this table at runtime to explain why a proposed assignment is or is not valid.

---

## 3. Views — Logic & Algorithms

### View 1: `view_scheduled_arrivals`
```sql
SELECT fo.*, f.flight_number, al.airline_name,
       orig.iata_code AS origin_airport,
       dest.iata_code AS arrival_airport,
       ac.registration_number, act.model,
       rd.designation AS assigned_runway_direction,
       ra.assignment_status
FROM flight_operation fo
JOIN flight f ON fo.flight_id = f.flight_id
JOIN airline al ON f.airline_id = al.airline_id
JOIN aircraft ac ON f.aircraft_id = ac.aircraft_id
JOIN aircraft_type act ON ac.type_id = act.type_id
JOIN airport orig ON f.origin_airport_id = orig.airport_id
JOIN airport dest ON fo.airport_id = dest.airport_id
LEFT JOIN runway_assignment ra ON fo.operation_id = ra.operation_id
LEFT JOIN runway_direction rd ON ra.direction_id = rd.direction_id
LEFT JOIN runway rw ON rd.runway_id = rw.runway_id
WHERE fo.operation_type = 'LANDING';
```
**Logic:** Six INNER JOINs resolve the full chain from operation → flight → airline → aircraft → aircraft type → both airports. Two **LEFT JOINs** on `runway_assignment` and `runway_direction` ensure that unassigned arrivals still appear (with NULLs), rather than being filtered out. The `WHERE` clause applies a **selection** predicate (σ) on `operation_type`.

---

### View 2: `view_scheduled_departures`
Mirror of View 1 with `operation_type = 'TAKEOFF'` and the airport role swapped — `fo.airport_id` joins to the *departure* airport (origin), and `f.destination_airport_id` resolves the destination. The same LEFT JOIN pattern preserves unassigned departures.

---

### View 3: `view_runway_assignment_summary`
```sql
SELECT ra.assignment_id, ra.assignment_datetime, ra.assignment_status,
       fo.operation_type, f.flight_number, al.airline_name,
       act.aircraft_category, ap.iata_code,
       rw.runway_designation, rd.designation, rd.heading, rd.ils_available, ...
FROM runway_assignment ra
JOIN flight_operation fo ...
JOIN flight f ...
JOIN airline al ...
JOIN aircraft ac ...
JOIN aircraft_type act ...
JOIN airport ap ...
JOIN runway_direction rd ...
JOIN runway rw ...
```
**Logic:** This view is a wide **natural join** of 8 tables (all INNER), producing a denormalized projection for reporting. It exposes the full assignment context — who assigned, which runway direction, magnetic heading, ILS status, aircraft category — in a single queryable surface. No aggregation; this is a flat enumeration (one row per confirmed assignment).

---

### View 4: `view_airport_infrastructure_summary`
```sql
SELECT ap.airport_id, ap.iata_code, ap.airport_name, ap.city, ap.country,
       COUNT(DISTINCT rw.runway_id)      AS runway_count,
       COUNT(DISTINCT rd.direction_id)   AS direction_count,
       COUNT(DISTINCT tw.taxiway_id)     AS taxiway_count,
       COUNT(DISTINCT tm.terminal_id)    AS terminal_count,
       COUNT(DISTINCT st.stand_id)       AS stand_count
FROM airport ap
LEFT JOIN runway rw     ON ap.airport_id = rw.airport_id
LEFT JOIN runway_direction rd ON rw.runway_id = rd.runway_id
LEFT JOIN taxiway tw    ON ap.airport_id = tw.airport_id
LEFT JOIN terminal tm   ON ap.airport_id = tm.airport_id
LEFT JOIN aircraft_stand st ON ap.airport_id = st.airport_id
GROUP BY ap.airport_id, ap.iata_code, ap.icao_code, ap.airport_name, ap.city, ap.country;
```
**Logic:** Five **LEFT JOINs** ensure airports with zero infrastructure still appear. `COUNT(DISTINCT ...)` on each child table key correctly handles the Cartesian fan-out produced by joining multiple one-to-many relationships simultaneously — without `DISTINCT` the counts would multiply. `GROUP BY` performs the **aggregation** (γ) over all infrastructure dimensions per airport.

---

## 4. Triggers — Automated Audit Trail

Three `AFTER` triggers on `runway_assignment` write to `assignment_audit`. Two additional `BEFORE` triggers enforce distinct flight origin/destination airports; these use `SIGNAL SQLSTATE '45000'` because MySQL does not permit the relevant `CHECK` constraint to reference those foreign-key columns.

| Trigger | Event | OLD columns | NEW columns |
|---|---|---|---|
| `trg_after_assignment_insert` | INSERT | NULL | `direction_id`, `assignment_status` |
| `trg_after_assignment_update` | UPDATE | prior direction & status | new direction & status |
| `trg_after_assignment_delete` | DELETE | `direction_id`, `assignment_status` | NULL / `'DELETED'` |

**Why `AFTER` for the audit triggers and `BEFORE` for route validation?** The audit triggers fire after the assignment write succeeds, so the audit row reflects the attempted state transition; they remain part of the same transaction. The route-integrity triggers run before the flight write and reject identical endpoints before they are stored.

The AFTER INSERT, AFTER UPDATE, and AFTER DELETE triggers append assignment events to `assignment_audit` within the same transaction as the triggering change. A rollback therefore also rolls back the corresponding audit row. This is trigger-based audit history, not a replacement for InnoDB's internal redo/undo logging.

---

## 5. DBMS Concepts (Korth / Silberschatz-McGraw-Hill)

### 5.1 Normalization

| Normal Form | Condition | AURORA Example |
|---|---|---|
| **1NF** | No repeating groups; all attributes atomic | `runway_direction` stores one heading per row, not a comma-list inside `runway` |
| **2NF** | 1NF + no partial dependency on a composite key | `aircraft_runway_compatibility (type_id, runway_id)` — every non-key attribute (`landing_eligible`, `takeoff_eligible`, `remarks`) depends on the *full* composite key |
| **3NF** | 2NF + no transitive dependency | `flight_operation` stores `airport_id`; airport details (city, timezone) live only in `airport` — no transitive `operation_id → airport_id → timezone` stored redundancy |
| **BCNF** | Every determinant in every non-trivial FD is a superkey | The unique key `(runway_id, designation)` demonstrates one such determinant in `runway_direction`. This example alone does **not** prove that every relation is in BCNF; a complete claim requires listing candidate keys and all relevant FDs for each relation. |

### 5.2 Functional Dependencies & Armstrong's Axioms

Functional dependencies (FDs) supported by declared keys and intended semantics (illustrative excerpt; verify each relation's complete FD set before making a global normal-form claim):

```
airline_id → airline_name, iata_code, icao_code, country, callsign
registration_number → aircraft_id, type_id, owner_airline_id
{runway_id, designation} → direction_id, heading, ils_available
operation_id → flight_id, airport_id, operation_type, scheduled_datetime
{operation_id} → assignment_id   (via runway_assignment, 1:1 at most)
```

**Armstrong's Axioms applied:**
- **Reflexivity:** `{registration_number, type_id} → registration_number` (trivial FD, every superkey implies itself).
- **Augmentation:** `operation_id → flight_id` ∴ `{operation_id, airport_id} → {flight_id, airport_id}`.
- **Transitivity:** `aircraft_id → type_id` and `type_id → min_runway_length` ∴ `aircraft_id → min_runway_length` — used by `validator.py` to derive the minimum runway length for a registered aircraft without storing it redundantly on the `aircraft` table.

### 5.3 ER Model → Relational Schema Mapping

| ER Construct | Relational Mapping |
|---|---|
| Strong entity (e.g., `airline`) | Table with surrogate PK `airline_id` |
| Weak entity (e.g., `runway_direction`) | Table with PK `direction_id`, FK `runway_id` to owner; unique `(runway_id, designation)` replaces the partial key |
| Binary M:N relationship (`aircraft_runway_compatibility`) | Separate intersection table with composite PK `(type_id, runway_id)` |
| Unary / self-referencing | Not present; avoided by design |
| Multi-valued attribute | Decomposed: e.g., runway has multiple direction ends → `runway_direction` child table |
| Derived attribute | Not stored; computed at query time (e.g., infrastructure counts in View 4) |

### 5.4 Integrity Constraints

| Constraint Type | Examples in AURORA |
|---|---|
| **Entity Integrity** | Every table has a NOT NULL PRIMARY KEY (surrogate INT AUTO_INCREMENT or composite) |
| **Referential Integrity** | 23 FOREIGN KEY constraints with `ON DELETE RESTRICT` / `ON UPDATE CASCADE`; `SET FOREIGN_KEY_CHECKS = 0` used only during schema rebuild |
| **Domain Integrity** | `ENUM` on `operation_type ('LANDING','TAKEOFF')`, `aircraft_status`, `runway_status`; `CHECK` on `wingspan > 0`, `max_landing_weight <= max_takeoff_weight`, `runway_length > 0` |
| **Unique Constraints** | `iata_code`, `icao_code` on `airline`; `registration_number` on `aircraft`; `(airport_id, runway_designation)` on `runway`; `(runway_id, designation)` on `runway_direction` |

### 5.5 Relational Algebra Operations Used in Views & Queries

| Operation | SQL Equivalent | Where Used |
|---|---|---|
| **Selection** σ | `WHERE operation_type = 'LANDING'` | Views 1 & 2 |
| **Projection** π | Column lists in SELECT | All views |
| **Natural Join** ⋈ | `JOIN … ON fk = pk` | All 4 views |
| **Left Outer Join** ⟕ | `LEFT JOIN runway_assignment …` | Views 1, 2 (unassigned ops preserved) |
| **Aggregation** γ | `COUNT(DISTINCT …) … GROUP BY` | View 4 |
| **Set operations** | `UNION`, `INTERSECT` (in `docs/queries.sql`) | Advanced query demos |
| **Subquery / EXISTS** | `EXISTS (SELECT 1 FROM … WHERE …)` | Validator compatibility check |

### 5.6 Transactions & ACID

Runway assignments in AURORA are written inside explicit transactions (demonstrated in `docs/queries.sql`):

```sql
START TRANSACTION;
  INSERT INTO runway_assignment (...) VALUES (...);   -- triggers fire here
  UPDATE flight_operation SET operation_status = 'SCHEDULED' WHERE operation_id = ?;
COMMIT;
```

| ACID Property | Mechanism |
|---|---|
| **Atomicity** | `START TRANSACTION / COMMIT / ROLLBACK` — both rows succeed or neither |
| **Consistency** | FK constraints, CHECK constraints, and ENUM domains enforced by InnoDB at commit |
| **Isolation** | InnoDB default: `REPEATABLE READ` — concurrent reads see a consistent snapshot |
| **Durability** | InnoDB redo log (WAL) persists committed writes before acknowledging success |

### 5.7 Views as Virtual Relations

Views in AURORA are **non-materialized virtual relations** (Korth §4.2). They:
- Present a simplified, task-specific schema without repeating joins in every consumer query.
- Are read-only in the current application workflow; the multi-table joins and aggregation make the current views unsuitable for direct updates.
- Improve query organization, but are not by themselves a security boundary. The current role checks are enforced by the desktop application; direct database access still depends on MySQL account privileges.

---

## 6. Tech Stack Summary

| Layer | Technology | Version / Notes |
|---|---|---|
| **Database** | MySQL 8.0+ / InnoDB | 18 operational tables + 4 RBAC tables, four views, indexes and audit triggers |
| **Database handoff** | `database/aurora_workbench_full.sql` | Single-file clean-rebuild installer for the teammate's Workbench setup; generated from `schema.sql` + `seed.sql` |
| **DB access** | `db.py` | MySQL-only connection and transaction helpers; no hidden SQLite fallback |
| **Authentication** | `auth.py` | PBKDF2-HMAC-SHA256 password verification and database-backed role/permission checks |
| **Validation** | `validator.py` | Validates runway eligibility, restrictions and airport alignment; can run inside the assignment transaction |
| **Runtime language** | Python 3.10+ | Pygame desktop application |
| **UI framework** | Pygame | Role-specific login, controller console and read-only customer departures board |
| **Environment config** | `python-dotenv` / `.env` | MySQL connection settings kept out of source |
| **Tests** | `tests/` | Database-backed runway validation suite and isolated authentication unit tests |

> **Scope note:** AURORA does not implement dynamic runway allocation, AI scheduling, or real-time ATC. All operations have predefined scheduled times. Runway assignments are entered manually by the user and validated (not auto-assigned) against the compatibility and restriction tables. This is an academic demonstrator of relational database concepts, not a certified aviation safety system.

---

*Report generated for academic evaluation. AURORA*
