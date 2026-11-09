-- =============================================================================
-- AURORA: Seed Data Script
-- Fictional / Demonstration Dataset for DBMS Academic Demonstration
-- Fully mapped to Artos Pygame 2D Radar layouts (Map 1: DFW & Map 2: BOM)
-- =============================================================================

USE `aurora_db`;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE `assignment_audit`;
TRUNCATE TABLE `runway_assignment`;
TRUNCATE TABLE `aircraft_runway_compatibility`;
TRUNCATE TABLE `runway_restriction`;
TRUNCATE TABLE `airport_operating_hours`;
TRUNCATE TABLE `map_feature`;
TRUNCATE TABLE `airport_map`;
TRUNCATE TABLE `flight_operation`;
TRUNCATE TABLE `flight`;
TRUNCATE TABLE `aircraft_stand`;
TRUNCATE TABLE `terminal`;
TRUNCATE TABLE `taxiway`;
TRUNCATE TABLE `runway_direction`;
TRUNCATE TABLE `runway`;
TRUNCATE TABLE `airport`;
TRUNCATE TABLE `aircraft`;
TRUNCATE TABLE `aircraft_type`;
TRUNCATE TABLE `airline`;
SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- 1. AIRLINES (4 airlines)
-- =============================================================================
INSERT INTO `airline` (`airline_id`, `airline_name`, `iata_code`, `icao_code`, `country`, `callsign`, `operating_status`) VALUES
(1, 'American Airlines', 'AA', 'AAL', 'United States', 'AMERICAN', 'ACTIVE'),
(2, 'British Airways', 'BA', 'BAW', 'United Kingdom', 'SPEEDBIRD', 'ACTIVE'),
(3, 'Air India', 'AI', 'AIC', 'India', 'AIRINDIA', 'ACTIVE'),
(4, 'Nordic Regional Air', 'NR', 'NRA', 'Sweden', 'NORDIC', 'ACTIVE');

-- =============================================================================
-- 2. AIRCRAFT TYPES (6 types: Light, Medium, Heavy)
-- =============================================================================
INSERT INTO `aircraft_type` (`type_id`, `manufacturer`, `model`, `variant`, `aircraft_category`, `wingspan`, `aircraft_length`, `max_takeoff_weight`, `max_landing_weight`, `passenger_capacity`, `cargo_capacity`, `min_runway_length`) VALUES
(1, 'Airbus', 'A320neo', 'A320-271N', 'MEDIUM', 35.80, 37.57, 79000.00, 67400.00, 180, 3700.00, 2100.00),
(2, 'Boeing', 'B737-800', 'NG-800', 'MEDIUM', 35.79, 39.47, 79010.00, 66360.00, 189, 4400.00, 2300.00),
(3, 'Boeing', 'B777-300ER', 'Long-Range', 'HEAVY', 64.80, 73.86, 351530.00, 251290.00, 396, 20100.00, 3200.00),
(4, 'Airbus', 'A350-900', 'XWB-900', 'HEAVY', 64.75, 66.80, 280000.00, 207000.00, 350, 16500.00, 2800.00),
(5, 'ATR', 'ATR 72-600', 'Regional Turboprop', 'LIGHT', 27.05, 27.17, 23000.00, 22350.00, 72, 1700.00, 1400.00),
(6, 'Bombardier', 'CRJ-900', 'NextGen', 'MEDIUM', 24.85, 36.20, 38330.00, 34020.00, 90, 2320.00, 1950.00);

-- =============================================================================
-- 3. AIRCRAFT (12 aircraft)
-- =============================================================================
INSERT INTO `aircraft` (`aircraft_id`, `registration_number`, `type_id`, `owner_airline_id`, `operator_airline_id`, `manufacturing_date`, `aircraft_status`, `notes`) VALUES
(1, 'N101AA', 1, 1, 1, '2021-03-15', 'ACTIVE', 'Primary mainline A320neo based at DFW hub'),
(2, 'N102AA', 1, 1, 1, '2022-06-20', 'ACTIVE', 'Mainline A320neo based at DFW'),
(3, 'N777AA', 3, 1, 1, '2019-11-10', 'ACTIVE', 'Widebody international 777-300ER long-hauler'),
(4, 'G-XWBA', 4, 2, 2, '2020-01-18', 'ACTIVE', 'British Airways flagship A350-900 based at LHR'),
(5, 'G-ZBJA', 2, 2, 2, '2021-08-04', 'ACTIVE', 'Skyline European fleet 737-800'),
(6, 'VT-EXA', 3, 3, 3, '2023-04-12', 'ACTIVE', 'Air India flagship B777-300ER based at BOM'),
(7, 'VT-EXB', 1, 3, 3, '2018-05-22', 'ACTIVE', 'Air India domestic trunk A320neo based at BOM'),
(8, 'N802AA', 2, 1, 1, '2019-09-30', 'ACTIVE', 'American domestic trunk carrier B737-800'),
(9, 'SE-NRA1', 5, 4, 4, '2022-02-14', 'ACTIVE', 'Nordic commuter ATR 72'),
(10, 'SE-NRA2', 6, 4, 4, '2020-07-19', 'ACTIVE', 'Nordic regional jet CRJ-900'),
(11, 'N999AA', 1, 1, 1, '2015-04-10', 'MAINTENANCE', 'In routine C-check maintenance at DFW Hangar 5'),
(12, 'G-RETR', 2, 2, 2, '2012-08-01', 'RETIRED', 'Retired from scheduled revenue service');

-- =============================================================================
-- 4. AIRPORTS (3 airports: DFW, LHR, BOM)
-- Airport 1 maps to Artos Map 1 (DFW / Dallas-Fort Worth)
-- Airport 3 maps to Artos Map 2 (BOM / Mumbai Chhatrapati Shivaji)
-- =============================================================================
INSERT INTO `airport` (`airport_id`, `airport_name`, `iata_code`, `icao_code`, `city`, `region_state`, `country`, `latitude`, `longitude`, `elevation`, `timezone`, `operating_status`) VALUES
(1, 'Dallas/Fort Worth International Airport', 'DFW', 'KDFW', 'Dallas-Fort Worth', 'Texas', 'United States', 32.899800, -97.040300, 185.00, 'America/Chicago', 'ACTIVE'),
(2, 'London Heathrow Airport', 'LHR', 'EGLL', 'London', 'Greater London', 'United Kingdom', 51.470000, -0.454300, 25.00, 'Europe/London', 'ACTIVE'),
(3, 'Chhatrapati Shivaji Maharaj International Airport', 'BOM', 'VABB', 'Mumbai', 'Maharashtra', 'India', 19.088600, 72.867900, 11.00, 'Asia/Kolkata', 'ACTIVE');

-- =============================================================================
-- 5. RUNWAYS WITH EXACT RADAR COORDINATES
-- Runways 1, 2, 3 correspond to Artos Map 1 geometry (DFW)!
-- Runways 6, 7 correspond to Artos Map 2 geometry (BOM)!
-- =============================================================================
INSERT INTO `runway` (`runway_id`, `airport_id`, `runway_designation`, `runway_length`, `runway_width`, `surface_type`, `true_heading`, `runway_status`, `start_x`, `start_y`, `end_x`, `end_y`, `notes`) VALUES
(1, 1, '17L/35R', 2591.00, 45.00, 'CONCRETE', 175.00, 'OPEN', 125, 500, 600, 0, 'East parallel runway (Artos Map 1 Runway 1)'),
(2, 1, '17C/35C', 4085.00, 45.00, 'CONCRETE', 175.00, 'OPEN', 125, 200, 1000, 300, 'Central primary long runway (Artos Map 1 Runway 2)'),
(3, 1, '18R/36L', 4084.00, 60.00, 'CONCRETE', 185.00, 'OPEN', 125, 120, 1000, 0, 'West long heavy runway (Artos Map 1 Runway 3)'),
(4, 2, '09L/27R', 3902.00, 50.00, 'ASPHALT', 90.00, 'OPEN', 200, 350, 900, 350, 'Northern runway at EGLL'),
(5, 2, '09R/27L', 3660.00, 50.00, 'ASPHALT', 90.00, 'OPEN', 200, 650, 900, 650, 'Southern runway at EGLL'),
(6, 3, '09/27', 3448.00, 45.00, 'ASPHALT', 92.00, 'OPEN', 800, 600, 100, 200, 'Main primary runway at VABB (Artos Map 2 Runway 9)'),
(7, 3, '14/32', 2925.00, 45.00, 'ASPHALT', 142.00, 'OPEN', 800, 600, 200, 500, 'Secondary intersecting runway at VABB (Artos Map 2 Runway 10)');

-- =============================================================================
-- 6. RUNWAY_DIRECTIONS (14 directions total: 2 per physical runway)
-- =============================================================================
INSERT INTO `runway_direction` (`direction_id`, `runway_id`, `designation`, `heading`, `landing_permitted`, `takeoff_permitted`, `ils_available`, `approach_category`) VALUES
-- DFW Runway 1 (17L/35R)
(1, 1, '17L', 175.00, 1, 1, 1, 'CAT I'),
(2, 1, '35R', 355.00, 1, 1, 1, 'CAT I'),
-- DFW Runway 2 (17C/35C)
(3, 2, '17C', 175.00, 1, 1, 1, 'CAT III'),
(4, 2, '35C', 355.00, 1, 1, 1, 'CAT III'),
-- DFW Runway 3 (18R/36L)
(5, 3, '18R', 185.00, 1, 1, 1, 'CAT III'),
(6, 3, '36L', 5.00, 1, 1, 1, 'CAT III'),
-- LHR Runway 4 (09L/27R)
(7, 4, '09L', 90.00, 1, 1, 1, 'CAT III'),
(8, 4, '27R', 270.00, 1, 1, 1, 'CAT III'),
-- LHR Runway 5 (09R/27L)
(9, 5, '09R', 90.00, 1, 1, 1, 'CAT III'),
(10, 5, '27L', 270.00, 1, 1, 1, 'CAT III'),
-- BOM Runway 6 (09/27)
(11, 6, '09', 92.00, 1, 1, 1, 'CAT II'),
(12, 6, '27', 272.00, 1, 1, 1, 'CAT II'),
-- BOM Runway 7 (14/32)
(13, 7, '14', 142.00, 1, 0, 0, 'NON-PRECISION'),
(14, 7, '32', 322.00, 0, 1, 0, 'VISUAL');

-- =============================================================================
-- 7. TAXIWAYS WITH EXACT RADAR COORDINATES
-- Matches Artos cyan guidance lines
-- =============================================================================
INSERT INTO `taxiway` (`taxiway_id`, `airport_id`, `taxiway_name`, `surface_type`, `taxiway_status`, `start_x`, `start_y`, `end_x`, `end_y`) VALUES
-- DFW Map 1 Taxiways
(1, 1, 'Alpha (A)', 'CONCRETE', 'OPEN', 125, 200, 125, 500),
(2, 1, 'Bravo (B)', 'CONCRETE', 'OPEN', 125, 500, 125, 700),
(3, 1, 'Kilo (K)', 'CONCRETE', 'OPEN', 300, 200, 412, 480),
-- LHR Taxiways
(4, 2, 'Alpha (A)', 'ASPHALT', 'OPEN', 200, 350, 200, 650),
(5, 2, 'November (N)', 'ASPHALT', 'OPEN', 900, 350, 900, 650),
-- BOM Map 2 Taxiways (Exact Artos Map 2 geometry)
(6, 3, 'Echo (E)', 'ASPHALT', 'OPEN', 800, 600, 800, 400),
(7, 3, 'Sierra (S)', 'ASPHALT', 'OPEN', 800, 400, 170, 400),
(8, 3, 'Alpha (A)', 'ASPHALT', 'OPEN', 100, 600, 1000, 600),
(9, 3, 'Bravo (B)', 'ASPHALT', 'OPEN', 800, 200, 800, 600),
(10, 3, 'Charlie (C)', 'ASPHALT', 'OPEN', 100, 200, 200, 500);

-- =============================================================================
-- 8. TERMINALS
-- =============================================================================
INSERT INTO `terminal` (`terminal_id`, `airport_id`, `terminal_name`, `terminal_type`) VALUES
(1, 1, 'Terminal A (American Hub)', 'DOMESTIC'),
(2, 1, 'Terminal D (International)', 'INTERNATIONAL'),
(3, 1, 'Terminal E (Regional & Cargo)', 'CARGO'),
(4, 2, 'Terminal 2 (The Queen\'s Terminal)', 'INTERNATIONAL'),
(5, 2, 'Terminal 5 (British Flagship)', 'INTERNATIONAL'),
(6, 3, 'Terminal 2 (Chhatrapati T2)', 'INTERNATIONAL'),
(7, 3, 'Terminal 1 (Santa Cruz Domestic)', 'DOMESTIC');

-- =============================================================================
-- 9. AIRCRAFT STANDS
-- =============================================================================
INSERT INTO `aircraft_stand` (`stand_id`, `airport_id`, `terminal_id`, `stand_code`, `max_aircraft_size`, `stand_status`) VALUES
(1, 1, 2, 'Gate D18', 'SUPER', 'AVAILABLE'),
(2, 1, 1, 'Gate A24', 'HEAVY', 'AVAILABLE'),
(3, 1, 3, 'Stand E02', 'MEDIUM', 'AVAILABLE'),
(4, 2, 4, 'Gate A10', 'HEAVY', 'AVAILABLE'),
(5, 2, 5, 'Gate 504', 'SUPER', 'AVAILABLE'),
(6, 3, 6, 'Gate 42', 'HEAVY', 'AVAILABLE'),
(7, 3, 7, 'Stand D03', 'MEDIUM', 'AVAILABLE');

-- =============================================================================
-- 10. FLIGHTS (22 distinct flights)
-- Connecting DFW (Dallas), BOM (Mumbai), and LHR (London)
-- =============================================================================
INSERT INTO `flight` (`flight_id`, `flight_number`, `airline_id`, `aircraft_id`, `origin_airport_id`, `destination_airport_id`, `flight_type`, `flight_status`, `service_date`) VALUES
(1, 'AA-101', 1, 1, 1, 3, 'PASSENGER', 'SCHEDULED', '2026-10-15'),
(2, 'AA-102', 1, 2, 3, 1, 'PASSENGER', 'SCHEDULED', '2026-10-15'),
(3, 'AA-201', 1, 3, 1, 2, 'PASSENGER', 'SCHEDULED', '2026-10-15'),
(4, 'AA-202', 1, 3, 2, 1, 'PASSENGER', 'SCHEDULED', '2026-10-16'),
(5, 'BA-192', 2, 4, 2, 1, 'PASSENGER', 'SCHEDULED', '2026-10-15'),
(6, 'BA-193', 2, 5, 1, 2, 'PASSENGER', 'SCHEDULED', '2026-10-15'),
(7, 'BA-138', 2, 4, 2, 3, 'PASSENGER', 'SCHEDULED', '2026-10-15'),
(8, 'AI-191', 3, 6, 2, 1, 'PASSENGER', 'SCHEDULED', '2026-10-15'),
(9, 'AI-102', 3, 7, 1, 3, 'PASSENGER', 'SCHEDULED', '2026-10-15'),
(10, 'NR-801', 4, 9, 1, 3, 'CHARTER', 'SCHEDULED', '2026-10-15'),
(11, 'NR-802', 4, 10, 3, 1, 'PASSENGER', 'SCHEDULED', '2026-10-15'),
(12, 'AA-105', 1, 1, 1, 3, 'PASSENGER', 'SCHEDULED', '2026-10-16'),
(13, 'AA-106', 1, 2, 3, 1, 'PASSENGER', 'SCHEDULED', '2026-10-16'),
(14, 'BA-196', 2, 4, 2, 1, 'PASSENGER', 'SCHEDULED', '2026-10-16'),
(15, 'BA-197', 2, 5, 1, 2, 'PASSENGER', 'SCHEDULED', '2026-10-16'),
(16, 'AI-195', 3, 6, 1, 2, 'PASSENGER', 'SCHEDULED', '2026-10-16'),
(17, 'AA-CARGO1', 1, 3, 1, 2, 'CARGO', 'SCHEDULED', '2026-10-15'),
(18, 'AA-FERRY2', 1, 2, 3, 1, 'FERRY', 'SCHEDULED', '2026-10-15'),
(19, 'BA-139', 2, 4, 3, 2, 'PASSENGER', 'SCHEDULED', '2026-10-16'),
(20, 'NR-805', 4, 10, 1, 3, 'PASSENGER', 'SCHEDULED', '2026-10-16'),
(21, 'AA-109', 1, 1, 3, 1, 'PASSENGER', 'SCHEDULED', '2026-10-17'),
(22, 'AI-199', 3, 7, 3, 2, 'PASSENGER', 'SCHEDULED', '2026-10-17');

-- =============================================================================
-- 11. FLIGHT_OPERATIONS (Predefined Landing and Takeoff events)
-- =============================================================================
INSERT INTO `flight_operation` (`operation_id`, `flight_id`, `airport_id`, `operation_type`, `scheduled_datetime`, `estimated_datetime`, `actual_datetime`, `operation_status`, `notes`) VALUES
-- Flight 1: AA-101 (DFW to BOM)
(1, 1, 1, 'TAKEOFF', '2026-10-15 06:00:00', '2026-10-15 06:05:00', NULL, 'SCHEDULED', 'Morning departure from DFW hub to BOM'),
(2, 1, 3, 'LANDING', '2026-10-15 08:15:00', '2026-10-15 08:20:00', NULL, 'SCHEDULED', 'Arrival at BOM from DFW'),

-- Flight 2: AA-102 (BOM to DFW)
(3, 2, 3, 'TAKEOFF', '2026-10-15 09:30:00', NULL, NULL, 'SCHEDULED', 'Morning return departure from BOM'),
(4, 2, 1, 'LANDING', '2026-10-15 11:45:00', NULL, NULL, 'SCHEDULED', 'Arrival back at DFW base'),

-- Flight 3: AA-201 (DFW to LHR)
(5, 3, 1, 'TAKEOFF', '2026-10-15 02:15:00', NULL, NULL, 'SCHEDULED', 'Long-haul red-eye widebody takeoff DFW to LHR'),
(6, 3, 2, 'LANDING', '2026-10-15 07:10:00', NULL, NULL, 'SCHEDULED', 'LHR early morning arrival'),

-- Flight 4: AA-202 (LHR to DFW)
(7, 4, 2, 'TAKEOFF', '2026-10-16 10:00:00', NULL, NULL, 'SCHEDULED', 'Daytime return flight from LHR'),
(8, 4, 1, 'LANDING', '2026-10-16 23:30:00', NULL, NULL, 'SCHEDULED', 'Late night arrival at DFW'),

-- Flight 5: BA-192 (LHR to DFW)
(9, 5, 2, 'TAKEOFF', '2026-10-15 08:00:00', NULL, NULL, 'SCHEDULED', 'British Airways morning departure from LHR'),
(10, 5, 1, 'LANDING', '2026-10-15 21:15:00', NULL, NULL, 'SCHEDULED', 'DFW evening arrival'),

-- Flight 6: BA-193 (DFW to LHR)
(11, 6, 1, 'TAKEOFF', '2026-10-15 23:00:00', NULL, NULL, 'SCHEDULED', 'Midnight departure DFW to London'),
(12, 6, 2, 'LANDING', '2026-10-16 04:30:00', NULL, NULL, 'SCHEDULED', 'London early morning arrival'),

-- Flight 7: BA-138 (LHR to BOM)
(13, 7, 2, 'TAKEOFF', '2026-10-15 12:00:00', NULL, NULL, 'SCHEDULED', 'LHR to BOM flagship A350 flight'),
(14, 7, 3, 'LANDING', '2026-10-16 01:45:00', NULL, NULL, 'SCHEDULED', 'BOM overnight arrival'),

-- Flight 8: AI-191 (LHR to DFW)
(15, 8, 2, 'TAKEOFF', '2026-10-15 14:30:00', NULL, NULL, 'SCHEDULED', 'Transatlantic continuation departure'),
(16, 8, 1, 'LANDING', '2026-10-16 03:40:00', NULL, NULL, 'SCHEDULED', 'DFW early hours arrival'),

-- Flight 9: AI-102 (DFW to BOM)
(17, 9, 1, 'TAKEOFF', '2026-10-15 15:00:00', NULL, NULL, 'SCHEDULED', 'Direct long-haul takeoff DFW to BOM'),
(18, 9, 3, 'LANDING', '2026-10-15 17:10:00', NULL, NULL, 'SCHEDULED', 'BOM late afternoon arrival'),

-- Flight 10: NR-801 (DFW to BOM)
(19, 10, 1, 'TAKEOFF', '2026-10-15 18:00:00', NULL, NULL, 'SCHEDULED', 'Charter turboprop flight'),
(20, 10, 3, 'LANDING', '2026-10-15 21:00:00', NULL, NULL, 'SCHEDULED', 'Charter arrival BOM'),

-- Flight 17: Cargo AA-CARGO1 (DFW to LHR)
(21, 17, 1, 'TAKEOFF', '2026-10-15 04:00:00', NULL, NULL, 'SCHEDULED', 'Heavy cargo departure from DFW'),
(22, 17, 2, 'LANDING', '2026-10-15 09:30:00', NULL, NULL, 'SCHEDULED', 'Heavy cargo arrival at LHR'),

-- Operations for Oct 16
(23, 12, 1, 'TAKEOFF', '2026-10-16 06:10:00', NULL, NULL, 'SCHEDULED', 'Second day morning departure DFW'),
(24, 12, 3, 'LANDING', '2026-10-16 08:25:00', NULL, NULL, 'SCHEDULED', 'Second day morning arrival BOM'),
(25, 13, 3, 'TAKEOFF', '2026-10-16 10:00:00', NULL, NULL, 'SCHEDULED', 'BOM morning takeoff'),
(26, 13, 1, 'LANDING', '2026-10-16 12:15:00', NULL, NULL, 'SCHEDULED', 'DFW noon arrival'),
(27, 14, 2, 'TAKEOFF', '2026-10-16 08:15:00', NULL, NULL, 'SCHEDULED', 'LHR departure to DFW'),
(28, 14, 1, 'LANDING', '2026-10-16 21:30:00', NULL, NULL, 'SCHEDULED', 'DFW night arrival'),
(29, 15, 1, 'TAKEOFF', '2026-10-16 23:15:00', NULL, NULL, 'SCHEDULED', 'DFW midnight departure'),
(30, 15, 2, 'LANDING', '2026-10-17 04:45:00', NULL, NULL, 'SCHEDULED', 'LHR dawn arrival');

-- =============================================================================
-- 12. AIRCRAFT_RUNWAY_COMPATIBILITY
-- Matrix defining eligibility for each aircraft type on each runway.
-- Heavy widebodies (B777, A350) are NOT eligible on shorter runways (DFW 17L/35R)!
-- =============================================================================
INSERT INTO `aircraft_runway_compatibility` (`type_id`, `runway_id`, `landing_eligible`, `takeoff_eligible`, `remarks`) VALUES
-- A320neo (type 1) across all runways
(1, 1, 1, 1, 'Fully compatible on DFW 17L/35R'),
(1, 2, 1, 1, 'Fully compatible on DFW 17C/35C'),
(1, 3, 1, 1, 'Fully compatible on DFW 18R/36L'),
(1, 4, 1, 1, 'Fully compatible on LHR 09L/27R'),
(1, 5, 1, 1, 'Fully compatible on LHR 09R/27L'),
(1, 6, 1, 1, 'Fully compatible on BOM 09/27'),
(1, 7, 1, 1, 'Compatible on BOM secondary 14/32'),

-- B737-800 (type 2) across all runways
(2, 1, 1, 1, 'Fully compatible on DFW 17L/35R'),
(2, 2, 1, 1, 'Fully compatible on DFW 17C/35C'),
(2, 3, 1, 1, 'Fully compatible on DFW 18R/36L'),
(2, 4, 1, 1, 'Fully compatible on LHR 09L/27R'),
(2, 5, 1, 1, 'Fully compatible on LHR 09R/27L'),
(2, 6, 1, 1, 'Fully compatible on BOM 09/27'),
(2, 7, 1, 1, 'Compatible on BOM secondary 14/32'),

-- B777-300ER (type 3 - Heavy Widebody)
-- Runway 1 (DFW 17L/35R) is 2591m -> Ineligible for B777 MTOW operations! (Simplified rule)
(3, 1, 0, 0, 'INELIGIBLE: Runway length 2591m below B777-300ER minimum MTOW safety envelope 3200m'),
(3, 2, 1, 1, 'Eligible: DFW 17C/35C length 4085m exceeds requirements'),
(3, 3, 1, 1, 'Eligible: DFW 18R/36L length 4084m prime widebody runway'),
(3, 4, 1, 1, 'Eligible: LHR 09L/27R length 3902m'),
(3, 5, 1, 1, 'Eligible: LHR 09R/27L length 3660m'),
(3, 6, 1, 1, 'Eligible: BOM 09/27 length 3448m'),
(3, 7, 0, 0, 'INELIGIBLE: BOM secondary runway 14/32 too short (2925m) for B777-300ER'),

-- A350-900 (type 4 - Heavy Widebody)
(4, 1, 0, 0, 'INELIGIBLE: DFW 17L/35R below A350 recommended field length'),
(4, 2, 1, 1, 'Eligible on DFW 17C/35C'),
(4, 3, 1, 1, 'Eligible on DFW 18R/36L'),
(4, 4, 1, 1, 'Eligible on LHR 09L/27R'),
(4, 5, 1, 1, 'Eligible on LHR 09R/27L'),
(4, 6, 1, 1, 'Eligible on BOM 09/27'),
(4, 7, 0, 0, 'INELIGIBLE: BOM 14/32 wingspan/length clearance constraint'),

-- ATR 72-600 (type 5 - Light Turboprop)
(5, 1, 1, 1, 'Eligible on DFW 17L/35R'),
(5, 2, 1, 1, 'Eligible on DFW 17C/35C'),
(5, 3, 1, 1, 'Eligible on DFW 18R/36L'),
(5, 4, 1, 1, 'Eligible on LHR 09L/27R'),
(5, 5, 1, 1, 'Eligible on LHR 09R/27L'),
(5, 6, 1, 1, 'Eligible on BOM 09/27'),
(5, 7, 1, 1, 'Eligible on BOM 14/32'),

-- CRJ-900 (type 6 - Regional Jet)
(6, 1, 1, 1, 'Eligible on DFW 17L/35R'),
(6, 2, 1, 1, 'Eligible on DFW 17C/35C'),
(6, 3, 1, 1, 'Eligible on DFW 18R/36L'),
(6, 4, 1, 1, 'Eligible on LHR 09L/27R'),
(6, 5, 1, 1, 'Eligible on LHR 09R/27L'),
(6, 6, 1, 1, 'Eligible on BOM 09/27'),
(6, 7, 1, 1, 'Eligible on BOM 14/32');

-- =============================================================================
-- 13. RUNWAY_RESTRICTION (Scheduled closures & maintenance windows)
-- DFW 18R/36L (Runway 3) has scheduled lighting maintenance on Oct 15 from 13:00 to 17:00!
-- =============================================================================
INSERT INTO `runway_restriction` (`restriction_id`, `runway_id`, `restriction_type`, `start_datetime`, `end_datetime`, `description`, `restriction_status`) VALUES
(1, 3, 'LIGHTING_MAINTENANCE', '2026-10-15 13:00:00', '2026-10-15 17:00:00', 'Routine AGL (Aeronautical Ground Lighting) calibration and maintenance window on Runway 18R/36L', 'SCHEDULED'),
(2, 5, 'SURFACE_MAINTENANCE', '2026-10-16 01:00:00', '2026-10-16 05:00:00', 'Night-time rubber removal and friction testing on LHR 09R/27L', 'SCHEDULED'),
(3, 7, 'NOISE_ABATEMENT', '2026-10-15 22:00:00', '2026-10-16 06:00:00', 'Night curfew noise restriction over residential area on BOM 14/32', 'SCHEDULED');

-- =============================================================================
-- 14. AIRPORT OPERATING HOURS
-- =============================================================================
INSERT INTO `airport_operating_hours` (`hours_id`, `airport_id`, `day_of_week`, `opening_time`, `closing_time`, `is_closed`) VALUES
(1, 1, 'MONDAY', '00:00:00', '23:59:59', 0),
(1, 1, 'TUESDAY', '00:00:00', '23:59:59', 0),
(1, 1, 'WEDNESDAY', '00:00:00', '23:59:59', 0),
(1, 1, 'THURSDAY', '00:00:00', '23:59:59', 0),
(1, 1, 'FRIDAY', '00:00:00', '23:59:59', 0),
(1, 1, 'SATURDAY', '00:00:00', '23:59:59', 0),
(1, 1, 'SUNDAY', '00:00:00', '23:59:59', 0),
(2, 2, 'MONDAY', '06:00:00', '23:30:00', 0),
(2, 2, 'TUESDAY', '06:00:00', '23:30:00', 0),
(2, 2, 'WEDNESDAY', '06:00:00', '23:30:00', 0),
(2, 2, 'THURSDAY', '06:00:00', '23:30:00', 0),
(2, 2, 'FRIDAY', '06:00:00', '23:30:00', 0),
(2, 2, 'SATURDAY', '06:00:00', '23:30:00', 0),
(2, 2, 'SUNDAY', '06:00:00', '23:30:00', 0),
(3, 3, 'MONDAY', '00:00:00', '23:59:59', 0),
(3, 3, 'TUESDAY', '00:00:00', '23:59:59', 0),
(3, 3, 'WEDNESDAY', '00:00:00', '23:59:59', 0),
(3, 3, 'THURSDAY', '00:00:00', '23:59:59', 0),
(3, 3, 'FRIDAY', '00:00:00', '23:59:59', 0),
(3, 3, 'SATURDAY', '00:00:00', '23:59:59', 0),
(3, 3, 'SUNDAY', '00:00:00', '23:59:59', 0);

-- =============================================================================
-- 15. AIRPORT_MAP & MAP_FEATURES (Faithfully preserving Artos Waypoints)
-- Map 1: DFW Aerodrome (Artos Map 1 Layout)
-- Map 2: BOM Aerodrome (Artos Map 2 Layout)
-- =============================================================================
INSERT INTO `airport_map` (`map_id`, `airport_id`, `map_name`, `map_type`, `map_version`, `coordinate_reference_system`, `map_status`, `map_asset_url`) VALUES
(1, 1, 'DFW Airfield Radar Layout (Map 1)', 'AIRPORT_LAYOUT', '2.0', 'SCREEN_PIXELS_1000x1000', 'ACTIVE', 'radar://dfw_map1'),
(2, 3, 'BOM Airfield Radar Layout (Map 2)', 'AIRPORT_LAYOUT', '2.0', 'SCREEN_PIXELS_1000x1000', 'ACTIVE', 'radar://bom_map2');

-- Waypoints from Artos Map 1 (DFW)
INSERT INTO `map_feature` (`feature_id`, `map_id`, `feature_type`, `feature_name`, `pos_x`, `pos_y`) VALUES
(1, 1, 'WAYPOINT', 'WP-101 (Apron North)', 125, 120),
(2, 1, 'WAYPOINT', 'WP-102 (Taxiway Alpha)', 125, 200),
(3, 1, 'WAYPOINT', 'WP-103 (Taxiway Bravo)', 125, 500),
(4, 1, 'WAYPOINT', 'WP-104 (Apron South)', 125, 700),
(5, 1, 'WAYPOINT', 'WP-201 (Mid Kilo)', 300, 200),
(6, 1, 'WAYPOINT', 'WP-202 (Intersection)', 412, 480),
(7, 1, 'WAYPOINT', 'WP-301 (Runway 1 Threshold)', 600, 0),
(8, 1, 'WAYPOINT', 'WP-302 (Runway 2 End)', 1000, 300),
(9, 1, 'WAYPOINT', 'WP-303 (Runway 3 End)', 1000, 0),
-- Waypoints from Artos Map 2 (BOM)
(10, 2, 'WAYPOINT', 'WP-B1 (Apron East)', 800, 600),
(11, 2, 'WAYPOINT', 'WP-B2 (Taxiway Echo)', 800, 400),
(12, 2, 'WAYPOINT', 'WP-B3 (Taxiway Sierra)', 170, 400),
(13, 2, 'WAYPOINT', 'WP-B4 (Runway 9 Threshold)', 100, 200),
(14, 2, 'WAYPOINT', 'WP-B5 (Runway 10 Threshold)', 200, 500),
(15, 2, 'WAYPOINT', 'WP-B6 (Taxiway Bravo Mid)', 800, 200),
(16, 2, 'WAYPOINT', 'WP-B7 (East Boundary 1)', 995, 500),
(17, 2, 'WAYPOINT', 'WP-B8 (East Boundary 2)', 995, 200);

-- =============================================================================
-- 16. RUNWAY_ASSIGNMENT (Pre-assigned demonstration records)
-- =============================================================================
INSERT INTO `runway_assignment` (`assignment_id`, `operation_id`, `direction_id`, `assignment_datetime`, `assignment_status`, `assigned_by`, `remarks`) VALUES
-- Operation 1: AA-101 TAKEOFF at DFW (Airport 1) -> Assigned Runway 35C (Direction 4)
(1, 1, 4, '2026-10-15 05:15:00', 'CONFIRMED', 'OPERATOR_ALPHA', 'Assigned central parallel runway 35C for prompt departure'),

-- Operation 2: AA-101 LANDING at BOM (Airport 3) -> Assigned Runway 27 (Direction 12)
(2, 2, 12, '2026-10-15 07:45:00', 'CONFIRMED', 'OPERATOR_BETA', 'Main east-west runway approach BOM 09/27'),

-- Operation 5: AA-201 TAKEOFF at DFW (Airport 1, Heavy B777) -> Assigned Runway 36L (Direction 6)
(3, 5, 6, '2026-10-15 01:30:00', 'CONFIRMED', 'DISPATCHER_DFW', 'Heavy widebody routed to longest west runway 18R/36L'),

-- Operation 6: AA-201 LANDING at LHR (Airport 2) -> Assigned Runway 27R (Direction 8)
(4, 6, 8, '2026-10-15 06:30:00', 'CONFIRMED', 'TOWER_LHR', 'Standard morning arrival flow 27R'),

-- Operation 9: BA-192 TAKEOFF at LHR (Airport 2) -> Assigned Runway 27L (Direction 10)
(5, 9, 10, '2026-10-15 07:15:00', 'CONFIRMED', 'TOWER_LHR', 'Designated departure runway'),

-- Operation 21: AA-CARGO1 TAKEOFF at DFW (Airport 1) -> Assigned Runway 35C (Direction 4)
(6, 21, 4, '2026-10-15 03:20:00', 'CONFIRMED', 'DISPATCHER_DFW', 'Cargo night slot takeoff on 35C');
