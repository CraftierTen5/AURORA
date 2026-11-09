# AURORA — Relational Schema & Normalization Analysis
### Airport Runway & Operations Management
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

19. **`APP_ROLE`** (
   `role_id` [PK], `role_code` [UQ], `role_name`
)

20. **`APP_PERMISSION`** (
   `permission_id` [PK], `permission_code` [UQ], `permission_name`
)

21. **`ROLE_PERMISSION`** (
   `role_id` [PK, FK -> `APP_ROLE.role_id`], `permission_id` [PK, FK -> `APP_PERMISSION.permission_id`]
)

22. **`APP_USER`** (
   `user_id` [PK], `username` [UQ], `password_hash`, `password_salt`, `role_id` [FK -> `APP_ROLE.role_id`], `is_active`, `created_at`, `last_login_at`
)

---

## 2. Normalization Analysis (1NF to BCNF)

The following is a defensible analysis of representative relations, not a blanket claim that all 22 relations have been formally proven to BCNF. A full proof requires the complete set of functional dependencies and candidate keys for each relation.

### First Normal Form (1NF)
- Most operational attributes are stored as single typed columns (for example, one runway direction and heading per row).
- The exception to discuss is `MAP_FEATURE.properties_json`: it stores a structured JSON document. It is one SQL column, but if its internal members are treated as relational attributes, the design is not strictly atomic. This is a deliberate flexible metadata field and should be acknowledged in the viva.

### Second Normal Form (2NF)
- Relations with a single-attribute candidate key cannot have partial dependency on a proper subset of that key.
- The composite-key relation `AIRCRAFT_RUNWAY_COMPATIBILITY(type_id, runway_id)` is the clearest demonstration: eligibility and remarks depend on the aircraft-type/runway pair, not on either side alone.
- `ROLE_PERMISSION(role_id, permission_id)` is a pure junction relation with a composite primary key and no non-key attributes.

### Third Normal Form (3NF)
- Aircraft model specifications are stored in `AIRCRAFT_TYPE`, rather than repeated on each `AIRCRAFT` row. This avoids storing manufacturer/model specifications redundantly for every individual airframe.
- Airport descriptive attributes remain in `AIRPORT`; operational records reference the airport by key rather than copying its name, city and timezone.

### Boyce-Codd Normal Form (BCNF)
- A declared unique key such as `RUNWAY_DIRECTION(runway_id, designation)` is a candidate key and therefore a superkey; the corresponding FD to heading and direction permissions satisfies the BCNF determinant condition.
- This example does not establish BCNF for every relation. The complete proof must inspect all non-trivial FDs, including those arising from composite candidate keys such as `AIRCRAFT_TYPE(manufacturer, model, variant)`.

## 3. Referential Actions & Integrity Policies

- `ON DELETE RESTRICT`: Used on core operational links (e.g. `flight -> airport`, `aircraft -> aircraft_type`, `runway -> airport`) to preserve flight audit history and prevent orphaned historical data.
- `ON DELETE SET NULL`: Used on `aircraft.owner_airline_id` and `aircraft_stand.terminal_id` where parent entities may be reallocated without discarding the child.
- `ON DELETE CASCADE`: Used for tightly bound components (e.g. `runway_direction -> runway`, `taxiway -> airport`, `terminal -> airport`, `map_feature -> airport_map`) where removing the parent aerodrome logically removes its internal infrastructure.
