# AURORA — Relational Schema & Normalization Analysis
### Aircraft & Unified Runway Operations Records Archive
*Academic DBMS Course Design Documentation*

---

## 1. Relational Database Schema Specification

Below is the formal relational schema notation. Primary keys are marked with `[PK]`, Foreign keys with `[FK]`, and Unique constraints with `[UQ]`.

1. **`AIRLINE`** (
   `airline_id` [PK], `airline_name`, `iata_code` [UQ], `icao_code` [UQ], `country`, `callsign`, `operating_status`
)

2. **`AIRCRAFT_TYPE`** (
   `type_id` [PK], `manufacturer`, `model`, `variant`, `aircraft_category`, `wingspan`, `aircraft_length`, `max_takeoff_weight`, `max_landing_weight`, `passenger_capacity`, `cargo_capacity`, `min_runway_length`
   *Candidate Key:* (`manufacturer`, `model`, `variant`) [UQ]
)

3. **`AIRCRAFT`** (
   `aircraft_id` [PK], `registration_number` [UQ], `type_id` [FK -> `AIRCRAFT_TYPE.type_id`], `owner_airline_id` [FK -> `AIRLINE.airline_id`], `operator_airline_id` [FK -> `AIRLINE.airline_id`], `manufacturing_date`, `aircraft_status`, `notes`
)

4. **`AIRPORT`** (
   `airport_id` [PK], `airport_name`, `iata_code` [UQ], `icao_code` [UQ], `city`, `region_state`, `country`, `latitude`, `longitude`, `elevation`, `timezone`, `operating_status`
)

5. **`RUNWAY`** (
   `runway_id` [PK], `airport_id` [FK -> `AIRPORT.airport_id`], `runway_designation`, `runway_length`, `runway_width`, `surface_type`, `true_heading`, `runway_status`, `start_x`, `start_y`, `end_x`, `end_y`, `notes`
   *Candidate Key:* (`airport_id`, `runway_designation`) [UQ]
)

6. **`RUNWAY_DIRECTION`** (
   `direction_id` [PK], `runway_id` [FK -> `RUNWAY.runway_id`], `designation`, `heading`, `landing_permitted`, `takeoff_permitted`, `ils_available`, `approach_category`
   *Candidate Key:* (`runway_id`, `designation`) [UQ]
)

7. **`TAXIWAY`** (
   `taxiway_id` [PK], `airport_id` [FK -> `AIRPORT.airport_id`], `taxiway_name`, `surface_type`, `taxiway_status`, `start_x`, `start_y`, `end_x`, `end_y`
   *Candidate Key:* (`airport_id`, `taxiway_name`) [UQ]
)

8. **`TERMINAL`** (
   `terminal_id` [PK], `airport_id` [FK -> `AIRPORT.airport_id`], `terminal_name`, `terminal_type`
   *Candidate Key:* (`airport_id`, `terminal_name`) [UQ]
)

9. **`AIRCRAFT_STAND`** (
   `stand_id` [PK], `airport_id` [FK -> `AIRPORT.airport_id`], `terminal_id` [FK -> `TERMINAL.terminal_id`], `stand_code`, `max_aircraft_size`, `stand_status`
   *Candidate Key:* (`airport_id`, `stand_code`) [UQ]
)

10. **`FLIGHT`** (
    `flight_id` [PK], `flight_number`, `airline_id` [FK -> `AIRLINE.airline_id`], `aircraft_id` [FK -> `AIRCRAFT.aircraft_id`], `origin_airport_id` [FK -> `AIRPORT.airport_id`], `destination_airport_id` [FK -> `AIRPORT.airport_id`], `flight_type`, `flight_status`, `service_date`
)

11. **`FLIGHT_OPERATION`** (
    `operation_id` [PK], `flight_id` [FK -> `FLIGHT.flight_id`], `airport_id` [FK -> `AIRPORT.airport_id`], `operation_type`, `scheduled_datetime`, `estimated_datetime`, `actual_datetime`, `operation_status`, `notes`
)

12. **`AIRCRAFT_RUNWAY_COMPATIBILITY`** (
    `type_id` [PK, FK -> `AIRCRAFT_TYPE.type_id`], `runway_id` [PK, FK -> `RUNWAY.runway_id`], `landing_eligible`, `takeoff_eligible`, `remarks`
)

13. **`RUNWAY_RESTRICTION`** (
    `restriction_id` [PK], `runway_id` [FK -> `RUNWAY.runway_id`], `restriction_type`, `start_datetime`, `end_datetime`, `description`, `restriction_status`
)

14. **`AIRPORT_OPERATING_HOURS`** (
    `hours_id` [PK], `airport_id` [FK -> `AIRPORT.airport_id`], `day_of_week`, `opening_time`, `closing_time`, `is_closed`
    *Candidate Key:* (`airport_id`, `day_of_week`) [UQ]
)

15. **`RUNWAY_ASSIGNMENT`** (
    `assignment_id` [PK], `operation_id` [UQ, FK -> `FLIGHT_OPERATION.operation_id`], `direction_id` [FK -> `RUNWAY_DIRECTION.direction_id`], `assignment_datetime`, `assignment_status`, `assigned_by`, `remarks`
)

16. **`AIRPORT_MAP`** (
    `map_id` [PK], `airport_id` [FK -> `AIRPORT.airport_id`], `map_name`, `map_type`, `map_version`, `coordinate_reference_system`, `map_status`, `map_asset_url`
)

17. **`MAP_FEATURE`** (
    `feature_id` [PK], `map_id` [FK -> `AIRPORT_MAP.map_id`], `feature_type`, `feature_name`, `pos_x`, `pos_y`, `latitude`, `longitude`, `elevation`, `properties_json`
)

18. **`ASSIGNMENT_AUDIT`** (
    `audit_id` [PK], `assignment_id`, `operation_id`, `old_direction_id`, `new_direction_id`, `old_status`, `new_status`, `action_type`, `changed_by`, `changed_at`
)

---

## 2. Normalization Analysis (1NF to BCNF)

### First Normal Form (1NF)
* **Criterion:** All attributes contain atomic, non-composite, single-valued domain entries; there are no repeating groups.
* **Analysis:**
  - In `AIRCRAFT_TYPE`, dimensions (wingspan, length, weights) are isolated into individual DECIMAL scalar columns.
  - In `RUNWAY`, multidimensional coordinate bounds (`start_x`, `start_y`, `end_x`, `end_y`) and operational heading are individual numeric primitives.
  - Multi-stop flights or multiple runways are never stored as comma-separated strings inside a single row. Instead, separate rows in `RUNWAY_DIRECTION` and `FLIGHT_OPERATION` are maintained.
* **Conclusion:** Satisfies 1NF.

### Second Normal Form (2NF)
* **Criterion:** The relation is in 1NF and every non-prime attribute is fully functionally dependent on the entire candidate key (no partial key dependencies).
* **Analysis:**
  - Tables with single-column surrogate primary keys (`aircraft_id`, `airport_id`, `operation_id`, etc.) automatically satisfy 2NF because partial dependency is impossible when the candidate key consists of a single attribute.
  - In composite key table `AIRCRAFT_RUNWAY_COMPATIBILITY` (`type_id`, `runway_id`):
    - `landing_eligible` and `takeoff_eligible` depend strictly on both the aircraft type AND the specific runway strip simultaneously:
      $$\{\text{type\_id}, \text{runway\_id}\} \rightarrow \{\text{landing\_eligible}, \text{takeoff\_eligible}, \text{remarks}\}$$
    - Neither attribute depends solely on `type_id` nor solely on `runway_id`.
* **Conclusion:** Satisfies 2NF.

### Third Normal Form (3NF)
* **Criterion:** The relation is in 2NF and no non-prime attribute is transitively dependent on the primary key (no $X \rightarrow Y$ and $Y \rightarrow Z$ where $X$ is key and $Y, Z$ are non-prime).
* **Analysis:**
  - Notice the design of `AIRCRAFT`:
    - Instead of storing `aircraft_model`, `wingspan`, and `passenger_capacity` directly in `AIRCRAFT`, those attributes are segregated into `AIRCRAFT_TYPE`.
    - If they were stored in `AIRCRAFT`, we would have had:
      $$\text{aircraft\_id} \rightarrow \text{model} \rightarrow \text{wingspan}$$
      which is a transitive dependency violating 3NF!
    - By decoupling `AIRCRAFT_TYPE` from `AIRCRAFT`, transitive dependencies are completely eliminated.
  - Similarly, `RUNWAY_DIRECTION` links to `RUNWAY`, and `RUNWAY` links to `AIRPORT`. `FLIGHT_OPERATION` tracks the airport directly while the runway direction is only referenced during assignment.
* **Conclusion:** Satisfies 3NF.

### Boyce-Codd Normal Form (BCNF)
* **Criterion:** For every non-trivial functional dependency $X \rightarrow Y$, $X$ must be a superkey.
* **Analysis:**
  - In `AIRCRAFT`: `registration_number` is a candidate key. Both `aircraft_id` and `registration_number` are superkeys.
  - In `AIRLINE`: `airline_id` is PK; `iata_code` and `icao_code` have UNIQUE constraints and act as alternative candidate keys.
  - In `RUNWAY_DIRECTION`: PK is `direction_id`; alternative candidate key is (`runway_id`, `designation`). All determinants are superkeys.
* **Conclusion:** Satisfies BCNF.

---

## 3. Referential Actions & Integrity Policies

- `ON DELETE RESTRICT`: Used on core operational links (e.g. `flight -> airport`, `aircraft -> aircraft_type`, `runway -> airport`) to preserve flight audit history and prevent orphaned historical data.
- `ON DELETE SET NULL`: Used on `aircraft.owner_airline_id` and `aircraft_stand.terminal_id` where parent entities may be reallocated without discarding the child.
- `ON DELETE CASCADE`: Used for tightly bound components (e.g. `runway_direction -> runway`, `taxiway -> airport`, `terminal -> airport`, `map_feature -> airport_map`) where removing the parent aerodrome logically removes its internal infrastructure.
