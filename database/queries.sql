-- =============================================================================
-- AURORA: Academic DBMS Concepts & SQL Demonstration Suite
-- Course syllabus demonstration queries for MySQL 8.0+ / 8.4 LTS
-- =============================================================================

USE `aurora_db`;

-- =============================================================================
-- CONCEPT 1: SELECTION, PROJECTION & DUPLICATE ELIMINATION (DISTINCT)
-- Selection: Filtering rows via WHERE clause.
-- Projection: Selecting specific attributes.
-- DISTINCT: Eliminates redundant attribute tuples.
-- =============================================================================
-- Query 1.1: Distinct aircraft manufacturers and categories currently in fleet
SELECT DISTINCT 
  `manufacturer`, 
  `aircraft_category`
FROM `aircraft_type`
ORDER BY `manufacturer`, `aircraft_category`;

-- Query 1.2: Selection of active domestic airports situated at high elevation (> 100m)
SELECT 
  `iata_code`, 
  `airport_name`, 
  `city`, 
  `elevation`, 
  `timezone`
FROM `airport`
WHERE `operating_status` = 'ACTIVE' 
  AND `elevation` > 100.00
ORDER BY `elevation` DESC;


-- =============================================================================
-- CONCEPT 2: MULTI-TABLE INNER JOINS & COMPLEX RELATIONAL COMPOSITION
-- Combining records from multiple tables with matching foreign key relationships.
-- =============================================================================
-- Query 2.1: Complete Flight Manifest & Assigned Runway Overview
-- Joins 7 tables: flight, flight_operation, airline, aircraft, aircraft_type,
-- runway_assignment, runway_direction, runway, and airport.
SELECT 
  f.`flight_number`,
  al.`airline_name`,
  al.`iata_code` AS `airline_code`,
  fo.`operation_type`,
  fo.`scheduled_datetime`,
  ac.`registration_number`,
  act.`model` AS `aircraft_model`,
  ap.`iata_code` AS `station_airport`,
  rd.`designation` AS `assigned_runway_vector`,
  rw.`runway_designation` AS `physical_runway`,
  ra.`assignment_status`,
  ra.`assigned_by`
FROM `flight_operation` fo
INNER JOIN `flight` f ON fo.`flight_id` = f.`flight_id`
INNER JOIN `airline` al ON f.`airline_id` = al.`airline_id`
INNER JOIN `aircraft` ac ON f.`aircraft_id` = ac.`aircraft_id`
INNER JOIN `aircraft_type` act ON ac.`type_id` = act.`type_id`
INNER JOIN `airport` ap ON fo.`airport_id` = ap.`airport_id`
INNER JOIN `runway_assignment` ra ON fo.`operation_id` = ra.`operation_id`
INNER JOIN `runway_direction` rd ON ra.`direction_id` = rd.`direction_id`
INNER JOIN `runway` rw ON rd.`runway_id` = rw.`runway_id`
ORDER BY fo.`scheduled_datetime` ASC;


-- =============================================================================
-- CONCEPT 3: OUTER JOINS (LEFT / RIGHT JOIN) & ANTI-JOINS
-- Finding entities that have no matching records in associated tables.
-- =============================================================================
-- Query 3.1: Operations without runway assignments (Unassigned Operations)
-- Demonstrates LEFT JOIN with IS NULL filter (anti-join).
SELECT 
  fo.`operation_id`,
  f.`flight_number`,
  al.`airline_name`,
  ap.`iata_code` AS `airport_code`,
  fo.`operation_type`,
  fo.`scheduled_datetime`,
  fo.`operation_status`
FROM `flight_operation` fo
JOIN `flight` f ON fo.`flight_id` = f.`flight_id`
JOIN `airline` al ON f.`airline_id` = al.`airline_id`
JOIN `airport` ap ON fo.`airport_id` = ap.`airport_id`
LEFT JOIN `runway_assignment` ra ON fo.`operation_id` = ra.`operation_id`
WHERE ra.`assignment_id` IS NULL
ORDER BY fo.`scheduled_datetime` ASC;

-- Query 3.2: Airports and their runways, including airports without runways
SELECT 
  ap.`airport_id`,
  ap.`iata_code`,
  ap.`airport_name`,
  ap.`city`,
  rw.`runway_designation`,
  rw.`runway_length`,
  rw.`surface_type`,
  COALESCE(rw.`runway_status`, 'NO_RUNWAYS') AS `runway_operational_status`
FROM `airport` ap
LEFT JOIN `runway` rw ON ap.`airport_id` = rw.`airport_id`
ORDER BY ap.`airport_name`, rw.`runway_designation`;


-- =============================================================================
-- CONCEPT 4: SELF JOIN
-- Joining a table with itself to discover relationships among internal rows.
-- =============================================================================
-- Query 4.1: Find paired bidirectional flight operations on the same route on the same day
SELECT 
  f1.`flight_number` AS `outbound_flight`,
  f2.`flight_number` AS `return_flight`,
  al.`airline_name`,
  orig.`iata_code` AS `base_airport`,
  dest.`iata_code` AS `turnaround_airport`,
  f1.`service_date`
FROM `flight` f1
JOIN `flight` f2 
  ON f1.`origin_airport_id` = f2.`destination_airport_id`
 AND f1.`destination_airport_id` = f2.`origin_airport_id`
 AND f1.`airline_id` = f2.`airline_id`
 AND f1.`service_date` = f2.`service_date`
 AND f1.`flight_id` < f2.`flight_id`
JOIN `airline` al ON f1.`airline_id` = al.`airline_id`
JOIN `airport` orig ON f1.`origin_airport_id` = orig.`airport_id`
JOIN `airport` dest ON f1.`destination_airport_id` = dest.`airport_id`;


-- =============================================================================
-- CONCEPT 5: SET OPERATIONS (UNION, INTERSECT & EXCEPT SIMULATION)
-- =============================================================================
-- Query 5.1: UNION - Combined timeline of all air traffic movements at DFW airport
SELECT 
  'DEPARTURE' AS `movement_type`,
  f.`flight_number`,
  dest.`iata_code` AS `destination_or_origin`,
  fo.`scheduled_datetime`,
  fo.`operation_status`
FROM `flight_operation` fo
JOIN `flight` f ON fo.`flight_id` = f.`flight_id`
JOIN `airport` dest ON f.`destination_airport_id` = dest.`airport_id`
WHERE fo.`airport_id` = 1 AND fo.`operation_type` = 'TAKEOFF'

UNION ALL

SELECT 
  'ARRIVAL' AS `movement_type`,
  f.`flight_number`,
  orig.`iata_code` AS `destination_or_origin`,
  fo.`scheduled_datetime`,
  fo.`operation_status`
FROM `flight_operation` fo
JOIN `flight` f ON fo.`flight_id` = f.`flight_id`
JOIN `airport` orig ON f.`origin_airport_id` = orig.`airport_id`
WHERE fo.`airport_id` = 1 AND fo.`operation_type` = 'LANDING'
ORDER BY `scheduled_datetime` ASC;

-- Query 5.2: EXCEPT Simulation (Airports that host Takeoffs but NO Landings on a given date)
-- Uses anti-join to simulate MINUS / EXCEPT across all MySQL versions:
SELECT DISTINCT orig.`iata_code`, orig.`airport_name`
FROM `flight_operation` fo_dep
JOIN `airport` orig ON fo_dep.`airport_id` = orig.`airport_id`
WHERE fo_dep.`operation_type` = 'TAKEOFF'
  AND fo_dep.`airport_id` NOT IN (
    SELECT DISTINCT fo_arr.`airport_id`
    FROM `flight_operation` fo_arr
    WHERE fo_arr.`operation_type` = 'LANDING'
  );


-- =============================================================================
-- CONCEPT 6: NESTED & CORRELATED SUBQUERIES
-- =============================================================================
-- Query 6.1: Correlated Subquery with NOT EXISTS
-- Find aircraft types that have NO incompatible runways (i.e. compatible on all runways)
SELECT 
  act.`type_id`,
  act.`manufacturer`,
  act.`model`,
  act.`aircraft_category`
FROM `aircraft_type` act
WHERE NOT EXISTS (
  SELECT 1 
  FROM `runway` rw
  WHERE NOT EXISTS (
    SELECT 1 
    FROM `aircraft_runway_compatibility` arc
    WHERE arc.`type_id` = act.`type_id`
      AND arc.`runway_id` = rw.`runway_id`
      AND arc.`landing_eligible` = 1
      AND arc.`takeoff_eligible` = 1
  )
);

-- Query 6.2: Subquery with Group Aggregate Comparison
-- Aircraft models with MTOW strictly greater than the average MTOW of their category
SELECT 
  act1.`model`,
  act1.`manufacturer`,
  act1.`aircraft_category`,
  act1.`max_takeoff_weight`,
  (
    SELECT ROUND(AVG(act2.`max_takeoff_weight`), 2)
    FROM `aircraft_type` act2
    WHERE act2.`aircraft_category` = act1.`aircraft_category`
  ) AS `category_avg_mtow`
FROM `aircraft_type` act1
WHERE act1.`max_takeoff_weight` > (
  SELECT AVG(act2.`max_takeoff_weight`)
  FROM `aircraft_type` act2
  WHERE act2.`aircraft_category` = act1.`aircraft_category`
);


-- =============================================================================
-- CONCEPT 7: AGGREGATION, GROUP BY & HAVING
-- =============================================================================
-- Query 7.1: Operations volume by Airline and Operation Type with filter
SELECT 
  al.`airline_name`,
  fo.`operation_type`,
  COUNT(fo.`operation_id`) AS `total_operations`,
  MIN(fo.`scheduled_datetime`) AS `first_scheduled_op`,
  MAX(fo.`scheduled_datetime`) AS `last_scheduled_op`
FROM `airline` al
JOIN `flight` f ON al.`airline_id` = f.`airline_id`
JOIN `flight_operation` fo ON f.`flight_id` = fo.`flight_id`
GROUP BY al.`airline_name`, fo.`operation_type`
HAVING COUNT(fo.`operation_id`) >= 2
ORDER BY `total_operations` DESC;

-- Query 7.2: Runway Utilization and Length Metrics by Airport
SELECT 
  ap.`iata_code` AS `airport_code`,
  ap.`airport_name`,
  COUNT(DISTINCT rw.`runway_id`) AS `number_of_runways`,
  ROUND(AVG(rw.`runway_length`), 1) AS `avg_runway_length_meters`,
  MAX(rw.`runway_length`) AS `longest_runway_meters`,
  COUNT(DISTINCT ra.`assignment_id`) AS `assigned_operations_count`
FROM `airport` ap
JOIN `runway` rw ON ap.`airport_id` = rw.`airport_id`
LEFT JOIN `runway_direction` rd ON rw.`runway_id` = rd.`runway_id`
LEFT JOIN `runway_assignment` ra ON rd.`direction_id` = ra.`direction_id`
GROUP BY ap.`airport_id`, ap.`iata_code`, ap.`airport_name`
HAVING COUNT(DISTINCT rw.`runway_id`) >= 1
ORDER BY `longest_runway_meters` DESC;


-- =============================================================================
-- CONCEPT 8: TRANSACTION PROCESSING (ACID) & CONCURRENCY CONTROLS
-- =============================================================================
-- Example 8.1: Safe Assignment Insert with ACID Transaction and Rollback Test
START TRANSACTION;

-- Step 1: Check if operation 10 has an existing assignment
SELECT `assignment_id` 
FROM `runway_assignment` 
WHERE `operation_id` = 10 
FOR UPDATE;

-- Step 2: Attempt assignment insertion
INSERT INTO `runway_assignment` (
  `operation_id`,
  `direction_id`,
  `assignment_status`,
  `assigned_by`,
  `remarks`
) VALUES (
  10,
  3, -- DFW direction 17C
  'CONFIRMED',
  'TRAINING_AGENT',
  'ACID Demonstration assignment'
);

-- Step 3: Rollback demonstrating transaction isolation and non-persistence
ROLLBACK;


-- =============================================================================
-- CONCEPT 9: QUERY EXECUTION PLAN (EXPLAIN) & INDEX OPTIMIZATION
-- Demonstrates query optimization path utilizing the composite index:
-- `idx_operation_schedule` (`airport_id`, `scheduled_datetime`, `operation_type`)
-- =============================================================================
EXPLAIN 
SELECT 
  fo.`operation_id`, 
  fo.`flight_id`, 
  fo.`scheduled_datetime`, 
  fo.`operation_status`
FROM `flight_operation` fo
WHERE fo.`airport_id` = 1
  AND fo.`scheduled_datetime` BETWEEN '2026-10-15 00:00:00' AND '2026-10-15 23:59:59'
  AND fo.`operation_type` = 'TAKEOFF';


-- =============================================================================
-- CONCEPT 10: APPLICATION RBAC (ROLE-BASED ACCESS CONTROL)
-- Roles and permissions are many-to-many through role_permission.
-- The Customer role should have schedule.read only; Administrator has all
-- application permissions. This is application-level authorization.
-- =============================================================================

-- Query 10.1: Inspect the permission matrix
SELECT
  r.`role_code`,
  r.`role_name`,
  p.`permission_code`,
  p.`permission_name`
FROM `app_role` r
JOIN `role_permission` rp ON rp.`role_id` = r.`role_id`
JOIN `app_permission` p ON p.`permission_id` = rp.`permission_id`
ORDER BY r.`role_code`, p.`permission_code`;

-- Query 10.2: Customer-facing departure schedule (view abstraction)
SELECT
  `flight_number`,
  `airline_name`,
  `departure_airport`,
  `destination_airport`,
  `scheduled_datetime`,
  `operation_status`
FROM `view_scheduled_departures`
ORDER BY `scheduled_datetime`;

-- Query 10.3: Active application users and their assigned roles
SELECT u.`username`, r.`role_name`, u.`is_active`, u.`last_login_at`
FROM `app_user` u
JOIN `app_role` r ON r.`role_id` = u.`role_id`
ORDER BY r.`role_code`, u.`username`;
