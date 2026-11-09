-- =============================================================================
-- AURORA: Aircraft & Unified Runway Operations Records Archive
-- Relational Database DDL Schema (MySQL 8.0+ / 8.4 LTS Compatible)
-- Engine: InnoDB | Character Set: utf8mb4 | Collation: utf8mb4_unicode_ci
-- Integrates with Artos 2D Pygame Radar Visualizer & Operations Suite
-- =============================================================================

CREATE DATABASE IF NOT EXISTS `aurora_db`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `aurora_db`;

-- Set session flags for strict schema generation
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `assignment_audit`;
DROP TABLE IF EXISTS `runway_assignment`;
DROP TABLE IF EXISTS `aircraft_runway_compatibility`;
DROP TABLE IF EXISTS `runway_restriction`;
DROP TABLE IF EXISTS `airport_operating_hours`;
DROP TABLE IF EXISTS `map_feature`;
DROP TABLE IF EXISTS `airport_map`;
DROP TABLE IF EXISTS `flight_operation`;
DROP TABLE IF EXISTS `flight`;
DROP TABLE IF EXISTS `aircraft_stand`;
DROP TABLE IF EXISTS `terminal`;
DROP TABLE IF EXISTS `taxiway`;
DROP TABLE IF EXISTS `runway_direction`;
DROP TABLE IF EXISTS `runway`;
DROP TABLE IF EXISTS `airport`;
DROP TABLE IF EXISTS `aircraft`;
DROP TABLE IF EXISTS `aircraft_type`;
DROP TABLE IF EXISTS `airline`;

DROP VIEW IF EXISTS `view_scheduled_arrivals`;
DROP VIEW IF EXISTS `view_scheduled_departures`;
DROP VIEW IF EXISTS `view_runway_assignment_summary`;
DROP VIEW IF EXISTS `view_airport_infrastructure_summary`;
SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- 1. AIRLINE
-- Represents an air carrier entity holding operator or owner rights.
-- =============================================================================
CREATE TABLE `airline` (
  `airline_id` INT AUTO_INCREMENT PRIMARY KEY,
  `airline_name` VARCHAR(100) NOT NULL,
  `iata_code` CHAR(2) NULL,
  `icao_code` CHAR(3) NULL,
  `country` VARCHAR(100) NOT NULL,
  `callsign` VARCHAR(100) NULL,
  `operating_status` ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED') NOT NULL DEFAULT 'ACTIVE',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `uq_airline_iata` UNIQUE (`iata_code`),
  CONSTRAINT `uq_airline_icao` UNIQUE (`icao_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 2. AIRCRAFT_TYPE
-- Certified aircraft physical and operational specification model.
-- =============================================================================
CREATE TABLE `aircraft_type` (
  `type_id` INT AUTO_INCREMENT PRIMARY KEY,
  `manufacturer` VARCHAR(100) NOT NULL,
  `model` VARCHAR(100) NOT NULL,
  `variant` VARCHAR(50) NOT NULL DEFAULT 'Standard',
  `aircraft_category` ENUM('LIGHT', 'MEDIUM', 'HEAVY', 'SUPER') NOT NULL,
  `wingspan` DECIMAL(6,2) NOT NULL COMMENT 'Wingspan in meters',
  `aircraft_length` DECIMAL(6,2) NOT NULL COMMENT 'Length in meters',
  `max_takeoff_weight` DECIMAL(10,2) NOT NULL COMMENT 'MTOW in kilograms',
  `max_landing_weight` DECIMAL(10,2) NOT NULL COMMENT 'MLW in kilograms',
  `passenger_capacity` INT NOT NULL DEFAULT 0,
  `cargo_capacity` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT 'Payload in kilograms',
  `min_runway_length` DECIMAL(8,2) NOT NULL COMMENT 'Simplified baseline minimum runway length (meters)',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `uq_type_model_variant` UNIQUE (`manufacturer`, `model`, `variant`),
  CONSTRAINT `chk_wingspan_positive` CHECK (`wingspan` > 0),
  CONSTRAINT `chk_length_positive` CHECK (`aircraft_length` > 0),
  CONSTRAINT `chk_mtow_positive` CHECK (`max_takeoff_weight` > 0),
  CONSTRAINT `chk_mlw_positive` CHECK (`max_landing_weight` > 0),
  CONSTRAINT `chk_mlw_lte_mtow` CHECK (`max_landing_weight` <= `max_takeoff_weight`),
  CONSTRAINT `chk_pax_capacity_nonneg` CHECK (`passenger_capacity` >= 0),
  CONSTRAINT `chk_cargo_capacity_nonneg` CHECK (`cargo_capacity` >= 0),
  CONSTRAINT `chk_min_runway_positive` CHECK (`min_runway_length` > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 3. AIRCRAFT
-- Individual physical airframe registered with civil aviation authorities.
-- =============================================================================
CREATE TABLE `aircraft` (
  `aircraft_id` INT AUTO_INCREMENT PRIMARY KEY,
  `registration_number` VARCHAR(20) NOT NULL,
  `type_id` INT NOT NULL,
  `owner_airline_id` INT NULL,
  `operator_airline_id` INT NOT NULL,
  `manufacturing_date` DATE NULL,
  `aircraft_status` ENUM('ACTIVE', 'MAINTENANCE', 'RETIRED', 'STORED') NOT NULL DEFAULT 'ACTIVE',
  `notes` TEXT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `uq_aircraft_registration` UNIQUE (`registration_number`),
  CONSTRAINT `fk_aircraft_type` FOREIGN KEY (`type_id`)
    REFERENCES `aircraft_type` (`type_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_aircraft_owner` FOREIGN KEY (`owner_airline_id`)
    REFERENCES `airline` (`airline_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_aircraft_operator` FOREIGN KEY (`operator_airline_id`)
    REFERENCES `airline` (`airline_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 4. AIRPORT
-- Aerodrome installation with geographic coordinates and operational baseline.
-- =============================================================================
CREATE TABLE `airport` (
  `airport_id` INT AUTO_INCREMENT PRIMARY KEY,
  `airport_name` VARCHAR(150) NOT NULL,
  `iata_code` CHAR(3) NULL,
  `icao_code` CHAR(4) NULL,
  `city` VARCHAR(100) NOT NULL,
  `region_state` VARCHAR(100) NULL,
  `country` VARCHAR(100) NOT NULL,
  `latitude` DECIMAL(9,6) NOT NULL,
  `longitude` DECIMAL(9,6) NOT NULL,
  `elevation` DECIMAL(7,2) NOT NULL DEFAULT 0.00 COMMENT 'Elevation above sea level in meters',
  `timezone` VARCHAR(50) NOT NULL DEFAULT 'UTC' COMMENT 'IANA standard timezone name',
  `operating_status` ENUM('ACTIVE', 'RESTRICTED', 'CLOSED') NOT NULL DEFAULT 'ACTIVE',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `uq_airport_iata` UNIQUE (`iata_code`),
  CONSTRAINT `uq_airport_icao` UNIQUE (`icao_code`),
  CONSTRAINT `chk_latitude_valid` CHECK (`latitude` BETWEEN -90.000000 AND 90.000000),
  CONSTRAINT `chk_longitude_valid` CHECK (`longitude` BETWEEN -180.000000 AND 180.000000)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 5. RUNWAY
-- Physical runway strip with operational specifications and radar map coordinates.
-- =============================================================================
CREATE TABLE `runway` (
  `runway_id` INT AUTO_INCREMENT PRIMARY KEY,
  `airport_id` INT NOT NULL,
  `runway_designation` VARCHAR(10) NOT NULL COMMENT 'e.g. 09/27, 10/28, 11/29',
  `runway_length` DECIMAL(8,2) NOT NULL COMMENT 'Physical length in meters',
  `runway_width` DECIMAL(6,2) NOT NULL COMMENT 'Physical width in meters',
  `surface_type` ENUM('ASPHALT', 'CONCRETE', 'BITUMEN', 'GRASS', 'TURF') NOT NULL DEFAULT 'ASPHALT',
  `true_heading` DECIMAL(5,2) NULL COMMENT 'Heading in degrees',
  `runway_status` ENUM('OPEN', 'CLOSED', 'RESTRICTED', 'MAINTENANCE') NOT NULL DEFAULT 'OPEN',
  `start_x` INT NOT NULL DEFAULT 125 COMMENT 'Pygame Radar X start',
  `start_y` INT NOT NULL DEFAULT 500 COMMENT 'Pygame Radar Y start',
  `end_x` INT NOT NULL DEFAULT 600 COMMENT 'Pygame Radar X end',
  `end_y` INT NOT NULL DEFAULT 0 COMMENT 'Pygame Radar Y end',
  `notes` TEXT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `uq_airport_runway_designation` UNIQUE (`airport_id`, `runway_designation`),
  CONSTRAINT `fk_runway_airport` FOREIGN KEY (`airport_id`)
    REFERENCES `airport` (`airport_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_runway_length_positive` CHECK (`runway_length` > 0),
  CONSTRAINT `chk_runway_width_positive` CHECK (`runway_width` > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 6. RUNWAY_DIRECTION
-- Individual operational vector/direction along a physical runway (e.g. 09 vs 27).
-- =============================================================================
CREATE TABLE `runway_direction` (
  `direction_id` INT AUTO_INCREMENT PRIMARY KEY,
  `runway_id` INT NOT NULL,
  `designation` VARCHAR(5) NOT NULL COMMENT 'e.g. 09, 27, 10, 28',
  `heading` DECIMAL(5,2) NOT NULL COMMENT 'Magnetic heading in degrees',
  `landing_permitted` BOOLEAN NOT NULL DEFAULT TRUE,
  `takeoff_permitted` BOOLEAN NOT NULL DEFAULT TRUE,
  `ils_available` BOOLEAN NOT NULL DEFAULT FALSE,
  `approach_category` ENUM('CAT I', 'CAT II', 'CAT III', 'NON-PRECISION', 'VISUAL', 'NONE') NOT NULL DEFAULT 'CAT I',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `uq_runway_direction` UNIQUE (`runway_id`, `designation`),
  CONSTRAINT `fk_direction_runway` FOREIGN KEY (`runway_id`)
    REFERENCES `runway` (`runway_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_direction_heading` CHECK (`heading` >= 0 AND `heading` <= 360)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 7. TAXIWAY
-- Ground circulation link with radar map coordinates.
-- =============================================================================
CREATE TABLE `taxiway` (
  `taxiway_id` INT AUTO_INCREMENT PRIMARY KEY,
  `airport_id` INT NOT NULL,
  `taxiway_name` VARCHAR(20) NOT NULL COMMENT 'e.g. Alpha, Bravo, Kilo',
  `surface_type` ENUM('ASPHALT', 'CONCRETE', 'BITUMEN') NOT NULL DEFAULT 'ASPHALT',
  `taxiway_status` ENUM('OPEN', 'CLOSED', 'RESTRICTED') NOT NULL DEFAULT 'OPEN',
  `start_x` INT NOT NULL DEFAULT 125,
  `start_y` INT NOT NULL DEFAULT 200,
  `end_x` INT NOT NULL DEFAULT 500,
  `end_y` INT NOT NULL DEFAULT 200,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `uq_airport_taxiway` UNIQUE (`airport_id`, `taxiway_name`),
  CONSTRAINT `fk_taxiway_airport` FOREIGN KEY (`airport_id`)
    REFERENCES `airport` (`airport_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 8. TERMINAL
-- Passenger or cargo terminal structure at the airport.
-- =============================================================================
CREATE TABLE `terminal` (
  `terminal_id` INT AUTO_INCREMENT PRIMARY KEY,
  `airport_id` INT NOT NULL,
  `terminal_name` VARCHAR(50) NOT NULL,
  `terminal_type` ENUM('DOMESTIC', 'INTERNATIONAL', 'CARGO', 'GENERAL_AVIATION') NOT NULL DEFAULT 'DOMESTIC',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `uq_airport_terminal` UNIQUE (`airport_id`, `terminal_name`),
  CONSTRAINT `fk_terminal_airport` FOREIGN KEY (`airport_id`)
    REFERENCES `airport` (`airport_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 9. AIRCRAFT_STAND
-- Designated apron parking position / gate for aircraft turnaround.
-- =============================================================================
CREATE TABLE `aircraft_stand` (
  `stand_id` INT AUTO_INCREMENT PRIMARY KEY,
  `airport_id` INT NOT NULL,
  `terminal_id` INT NULL,
  `stand_code` VARCHAR(20) NOT NULL COMMENT 'e.g. Gate 14, Stand 201',
  `max_aircraft_size` ENUM('LIGHT', 'MEDIUM', 'HEAVY', 'SUPER') NOT NULL DEFAULT 'HEAVY',
  `stand_status` ENUM('AVAILABLE', 'OCCUPIED', 'MAINTENANCE', 'CLOSED') NOT NULL DEFAULT 'AVAILABLE',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `uq_airport_stand` UNIQUE (`airport_id`, `stand_code`),
  CONSTRAINT `fk_stand_airport` FOREIGN KEY (`airport_id`)
    REFERENCES `airport` (`airport_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_stand_terminal` FOREIGN KEY (`terminal_id`)
    REFERENCES `terminal` (`terminal_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 10. FLIGHT
-- Distinct scheduled flight service route instance.
-- =============================================================================
CREATE TABLE `flight` (
  `flight_id` INT AUTO_INCREMENT PRIMARY KEY,
  `flight_number` VARCHAR(10) NOT NULL COMMENT 'e.g. AG-101, SK-501',
  `airline_id` INT NOT NULL,
  `aircraft_id` INT NOT NULL,
  `origin_airport_id` INT NOT NULL,
  `destination_airport_id` INT NOT NULL,
  `flight_type` ENUM('PASSENGER', 'CARGO', 'FERRY', 'CHARTER', 'TRAINING') NOT NULL DEFAULT 'PASSENGER',
  `flight_status` ENUM('SCHEDULED', 'ACTIVE', 'DELAYED', 'CANCELLED', 'COMPLETED') NOT NULL DEFAULT 'SCHEDULED',
  `service_date` DATE NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `fk_flight_airline` FOREIGN KEY (`airline_id`)
    REFERENCES `airline` (`airline_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_flight_aircraft` FOREIGN KEY (`aircraft_id`)
    REFERENCES `aircraft` (`aircraft_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_flight_origin` FOREIGN KEY (`origin_airport_id`)
    REFERENCES `airport` (`airport_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_flight_destination` FOREIGN KEY (`destination_airport_id`)
    REFERENCES `airport` (`airport_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_flight_endpoints_differ` CHECK (`origin_airport_id` <> `destination_airport_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 11. FLIGHT_OPERATION
-- Explicit landing or takeoff event at a specific airport.
-- =============================================================================
CREATE TABLE `flight_operation` (
  `operation_id` INT AUTO_INCREMENT PRIMARY KEY,
  `flight_id` INT NOT NULL,
  `airport_id` INT NOT NULL,
  `operation_type` ENUM('LANDING', 'TAKEOFF') NOT NULL,
  `scheduled_datetime` DATETIME NOT NULL,
  `estimated_datetime` DATETIME NULL,
  `actual_datetime` DATETIME NULL,
  `operation_status` ENUM('SCHEDULED', 'DELAYED', 'CANCELLED', 'COMPLETED') NOT NULL DEFAULT 'SCHEDULED',
  `notes` TEXT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `fk_operation_flight` FOREIGN KEY (`flight_id`)
    REFERENCES `flight` (`flight_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_operation_airport` FOREIGN KEY (`airport_id`)
    REFERENCES `airport` (`airport_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 12. AIRCRAFT_RUNWAY_COMPATIBILITY
-- Simplified eligibility matrix for demo/academic testing.
-- =============================================================================
CREATE TABLE `aircraft_runway_compatibility` (
  `type_id` INT NOT NULL,
  `runway_id` INT NOT NULL,
  `landing_eligible` BOOLEAN NOT NULL DEFAULT TRUE,
  `takeoff_eligible` BOOLEAN NOT NULL DEFAULT TRUE,
  `remarks` VARCHAR(255) NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`type_id`, `runway_id`),
  CONSTRAINT `fk_arc_type` FOREIGN KEY (`type_id`)
    REFERENCES `aircraft_type` (`type_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_arc_runway` FOREIGN KEY (`runway_id`)
    REFERENCES `runway` (`runway_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 13. RUNWAY_RESTRICTION
-- Operational restrictions and scheduled closures / maintenance intervals.
-- =============================================================================
CREATE TABLE `runway_restriction` (
  `restriction_id` INT AUTO_INCREMENT PRIMARY KEY,
  `runway_id` INT NOT NULL,
  `restriction_type` ENUM(
    'SCHEDULED_CLOSURE',
    'SURFACE_MAINTENANCE',
    'LIGHTING_MAINTENANCE',
    'WEATHER_RESTRICTION',
    'NOISE_ABATEMENT',
    'EMERGENCY_CLOSURE'
  ) NOT NULL,
  `start_datetime` DATETIME NOT NULL,
  `end_datetime` DATETIME NOT NULL,
  `description` TEXT NULL,
  `restriction_status` ENUM('SCHEDULED', 'ACTIVE', 'COMPLETED', 'CANCELLED') NOT NULL DEFAULT 'SCHEDULED',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `fk_restriction_runway` FOREIGN KEY (`runway_id`)
    REFERENCES `runway` (`runway_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_restriction_times` CHECK (`end_datetime` > `start_datetime`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 14. AIRPORT_OPERATING_HOURS
-- Baseline airfield operating schedule per day of the week.
-- =============================================================================
CREATE TABLE `airport_operating_hours` (
  `hours_id` INT AUTO_INCREMENT PRIMARY KEY,
  `airport_id` INT NOT NULL,
  `day_of_week` ENUM('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY') NOT NULL,
  `opening_time` TIME NOT NULL,
  `closing_time` TIME NOT NULL,
  `is_closed` BOOLEAN NOT NULL DEFAULT FALSE,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `uq_airport_day_hours` UNIQUE (`airport_id`, `day_of_week`),
  CONSTRAINT `fk_hours_airport` FOREIGN KEY (`airport_id`)
    REFERENCES `airport` (`airport_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 15. RUNWAY_ASSIGNMENT
-- Manually recorded runway direction assignment for a flight operation.
-- Strictly 1:1 with flight_operation via UNIQUE(operation_id).
-- =============================================================================
CREATE TABLE `runway_assignment` (
  `assignment_id` INT AUTO_INCREMENT PRIMARY KEY,
  `operation_id` INT NOT NULL,
  `direction_id` INT NOT NULL,
  `assignment_datetime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `assignment_status` ENUM('PROPOSED', 'CONFIRMED', 'CANCELLED') NOT NULL DEFAULT 'CONFIRMED',
  `assigned_by` VARCHAR(50) NOT NULL DEFAULT 'OPERATIONS_DESK',
  `remarks` TEXT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `uq_assignment_operation` UNIQUE (`operation_id`),
  CONSTRAINT `fk_assignment_operation` FOREIGN KEY (`operation_id`)
    REFERENCES `flight_operation` (`operation_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_assignment_direction` FOREIGN KEY (`direction_id`)
    REFERENCES `runway_direction` (`direction_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 16. AIRPORT_MAP
-- Metadata container for airport layout representations.
-- =============================================================================
CREATE TABLE `airport_map` (
  `map_id` INT AUTO_INCREMENT PRIMARY KEY,
  `airport_id` INT NOT NULL,
  `map_name` VARCHAR(100) NOT NULL,
  `map_type` ENUM('AIRPORT_LAYOUT', 'RUNWAY', 'TAXIWAY', 'TERMINAL', 'PARKING') NOT NULL,
  `map_version` VARCHAR(20) NOT NULL DEFAULT '1.0',
  `coordinate_reference_system` VARCHAR(50) NOT NULL DEFAULT 'SCREEN_PIXELS_1000x1000',
  `map_status` ENUM('ACTIVE', 'DRAFT', 'SUPERSEDED') NOT NULL DEFAULT 'ACTIVE',
  `map_asset_url` VARCHAR(255) NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `fk_map_airport` FOREIGN KEY (`airport_id`)
    REFERENCES `airport` (`airport_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 17. MAP_FEATURE
-- Individual geographical and radar waypoint features from Artos.
-- =============================================================================
CREATE TABLE `map_feature` (
  `feature_id` INT AUTO_INCREMENT PRIMARY KEY,
  `map_id` INT NOT NULL,
  `feature_type` ENUM('WAYPOINT', 'RUNWAY_THRESHOLD', 'CENTERLINE', 'TAXIWAY_NODE', 'TERMINAL_GATE', 'NAV_AID') NOT NULL,
  `feature_name` VARCHAR(100) NOT NULL,
  `pos_x` INT NOT NULL DEFAULT 0 COMMENT 'Radar X coordinate',
  `pos_y` INT NOT NULL DEFAULT 0 COMMENT 'Radar Y coordinate',
  `latitude` DECIMAL(9,6) NULL,
  `longitude` DECIMAL(9,6) NULL,
  `elevation` DECIMAL(7,2) NULL,
  `properties_json` JSON NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_feature_map` FOREIGN KEY (`map_id`)
    REFERENCES `airport_map` (`map_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- 18. ASSIGNMENT_AUDIT
-- Course demonstration audit trail populated via database triggers.
-- =============================================================================
CREATE TABLE `assignment_audit` (
  `audit_id` INT AUTO_INCREMENT PRIMARY KEY,
  `assignment_id` INT NOT NULL,
  `operation_id` INT NOT NULL,
  `old_direction_id` INT NULL,
  `new_direction_id` INT NULL,
  `old_status` VARCHAR(30) NULL,
  `new_status` VARCHAR(30) NOT NULL,
  `action_type` ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
  `changed_by` VARCHAR(50) NOT NULL DEFAULT 'SYSTEM',
  `changed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- INDEXES FOR PERFORMANCE AND ACCESS PATH OPTIMIZATION
-- =============================================================================
CREATE INDEX `idx_flight_lookup` ON `flight` (`service_date`, `origin_airport_id`, `destination_airport_id`);
CREATE INDEX `idx_flight_airline` ON `flight` (`airline_id`);
CREATE INDEX `idx_operation_schedule` ON `flight_operation` (`airport_id`, `scheduled_datetime`, `operation_type`);
CREATE INDEX `idx_operation_status` ON `flight_operation` (`operation_status`);
CREATE INDEX `idx_assignment_direction` ON `runway_assignment` (`direction_id`, `assignment_status`);
CREATE INDEX `idx_restriction_window` ON `runway_restriction` (`runway_id`, `start_datetime`, `end_datetime`);
CREATE INDEX `idx_aircraft_operator` ON `aircraft` (`operator_airline_id`, `aircraft_status`);

-- =============================================================================
-- AUDIT TRIGGERS
-- =============================================================================
DELIMITER $$

CREATE TRIGGER `trg_after_assignment_insert`
AFTER INSERT ON `runway_assignment`
FOR EACH ROW
BEGIN
  INSERT INTO `assignment_audit` (
    `assignment_id`,
    `operation_id`,
    `old_direction_id`,
    `new_direction_id`,
    `old_status`,
    `new_status`,
    `action_type`,
    `changed_by`,
    `changed_at`
  ) VALUES (
    NEW.`assignment_id`,
    NEW.`operation_id`,
    NULL,
    NEW.`direction_id`,
    NULL,
    NEW.`assignment_status`,
    'INSERT',
    NEW.`assigned_by`,
    NOW()
  );
END$$

CREATE TRIGGER `trg_after_assignment_update`
AFTER UPDATE ON `runway_assignment`
FOR EACH ROW
BEGIN
  INSERT INTO `assignment_audit` (
    `assignment_id`,
    `operation_id`,
    `old_direction_id`,
    `new_direction_id`,
    `old_status`,
    `new_status`,
    `action_type`,
    `changed_by`,
    `changed_at`
  ) VALUES (
    NEW.`assignment_id`,
    NEW.`operation_id`,
    OLD.`direction_id`,
    NEW.`direction_id`,
    OLD.`assignment_status`,
    NEW.`assignment_status`,
    'UPDATE',
    NEW.`assigned_by`,
    NOW()
  );
END$$

CREATE TRIGGER `trg_after_assignment_delete`
AFTER DELETE ON `runway_assignment`
FOR EACH ROW
BEGIN
  INSERT INTO `assignment_audit` (
    `assignment_id`,
    `operation_id`,
    `old_direction_id`,
    `new_direction_id`,
    `old_status`,
    `new_status`,
    `action_type`,
    `changed_by`,
    `changed_at`
  ) VALUES (
    OLD.`assignment_id`,
    OLD.`operation_id`,
    OLD.`direction_id`,
    NULL,
    OLD.`assignment_status`,
    'DELETED',
    'DELETE',
    'SYSTEM',
    NOW()
  );
END$$

DELIMITER ;

-- =============================================================================
-- VIEWS FOR REPORTING AND CONVENIENCE
-- =============================================================================

CREATE OR REPLACE VIEW `view_scheduled_arrivals` AS
SELECT 
  fo.`operation_id`,
  f.`flight_id`,
  f.`flight_number`,
  al.`airline_name`,
  al.`iata_code` AS `airline_code`,
  orig.`iata_code` AS `origin_airport`,
  dest.`iata_code` AS `arrival_airport`,
  ac.`registration_number`,
  act.`model` AS `aircraft_model`,
  fo.`scheduled_datetime`,
  fo.`estimated_datetime`,
  fo.`actual_datetime`,
  fo.`operation_status`,
  rd.`designation` AS `assigned_runway_direction`,
  rw.`runway_designation` AS `assigned_runway`,
  ra.`assignment_status`
FROM `flight_operation` fo
JOIN `flight` f ON fo.`flight_id` = f.`flight_id`
JOIN `airline` al ON f.`airline_id` = al.`airline_id`
JOIN `aircraft` ac ON f.`aircraft_id` = ac.`aircraft_id`
JOIN `aircraft_type` act ON ac.`type_id` = act.`type_id`
JOIN `airport` orig ON f.`origin_airport_id` = orig.`airport_id`
JOIN `airport` dest ON fo.`airport_id` = dest.`airport_id`
LEFT JOIN `runway_assignment` ra ON fo.`operation_id` = ra.`operation_id`
LEFT JOIN `runway_direction` rd ON ra.`direction_id` = rd.`direction_id`
LEFT JOIN `runway` rw ON rd.`runway_id` = rw.`runway_id`
WHERE fo.`operation_type` = 'LANDING';

CREATE OR REPLACE VIEW `view_scheduled_departures` AS
SELECT 
  fo.`operation_id`,
  f.`flight_id`,
  f.`flight_number`,
  al.`airline_name`,
  al.`iata_code` AS `airline_code`,
  orig.`iata_code` AS `departure_airport`,
  dest.`iata_code` AS `destination_airport`,
  ac.`registration_number`,
  act.`model` AS `aircraft_model`,
  fo.`scheduled_datetime`,
  fo.`estimated_datetime`,
  fo.`actual_datetime`,
  fo.`operation_status`,
  rd.`designation` AS `assigned_runway_direction`,
  rw.`runway_designation` AS `assigned_runway`,
  ra.`assignment_status`
FROM `flight_operation` fo
JOIN `flight` f ON fo.`flight_id` = f.`flight_id`
JOIN `airline` al ON f.`airline_id` = al.`airline_id`
JOIN `aircraft` ac ON f.`aircraft_id` = ac.`aircraft_id`
JOIN `aircraft_type` act ON ac.`type_id` = act.`type_id`
JOIN `airport` orig ON fo.`airport_id` = orig.`airport_id`
JOIN `airport` dest ON f.`destination_airport_id` = dest.`airport_id`
LEFT JOIN `runway_assignment` ra ON fo.`operation_id` = ra.`operation_id`
LEFT JOIN `runway_direction` rd ON ra.`direction_id` = rd.`direction_id`
LEFT JOIN `runway` rw ON rd.`runway_id` = rw.`runway_id`
WHERE fo.`operation_type` = 'TAKEOFF';

CREATE OR REPLACE VIEW `view_runway_assignment_summary` AS
SELECT 
  ra.`assignment_id`,
  ra.`assignment_datetime`,
  ra.`assignment_status`,
  ra.`assigned_by`,
  fo.`operation_id`,
  fo.`operation_type`,
  fo.`scheduled_datetime`,
  f.`flight_number`,
  al.`airline_name`,
  ac.`registration_number`,
  act.`manufacturer`,
  act.`model` AS `aircraft_model`,
  act.`aircraft_category`,
  ap.`airport_id`,
  ap.`iata_code` AS `airport_code`,
  ap.`airport_name`,
  rw.`runway_id`,
  rw.`runway_designation`,
  rd.`direction_id`,
  rd.`designation` AS `direction_designation`,
  rd.`heading` AS `magnetic_heading`,
  rd.`ils_available`,
  ra.`remarks`
FROM `runway_assignment` ra
JOIN `flight_operation` fo ON ra.`operation_id` = fo.`operation_id`
JOIN `flight` f ON fo.`flight_id` = f.`flight_id`
JOIN `airline` al ON f.`airline_id` = al.`airline_id`
JOIN `aircraft` ac ON f.`aircraft_id` = ac.`aircraft_id`
JOIN `aircraft_type` act ON ac.`type_id` = act.`type_id`
JOIN `airport` ap ON fo.`airport_id` = ap.`airport_id`
JOIN `runway_direction` rd ON ra.`direction_id` = rd.`direction_id`
JOIN `runway` rw ON rd.`runway_id` = rw.`runway_id`;

CREATE OR REPLACE VIEW `view_airport_infrastructure_summary` AS
SELECT 
  ap.`airport_id`,
  ap.`iata_code`,
  ap.`icao_code`,
  ap.`airport_name`,
  ap.`city`,
  ap.`country`,
  COUNT(DISTINCT rw.`runway_id`) AS `runway_count`,
  COUNT(DISTINCT rd.`direction_id`) AS `direction_count`,
  COUNT(DISTINCT tw.`taxiway_id`) AS `taxiway_count`,
  COUNT(DISTINCT tm.`terminal_id`) AS `terminal_count`,
  COUNT(DISTINCT st.`stand_id`) AS `stand_count`
FROM `airport` ap
LEFT JOIN `runway` rw ON ap.`airport_id` = rw.`airport_id`
LEFT JOIN `runway_direction` rd ON rw.`runway_id` = rd.`runway_id`
LEFT JOIN `taxiway` tw ON ap.`airport_id` = tw.`airport_id`
LEFT JOIN `terminal` tm ON ap.`airport_id` = tm.`airport_id`
LEFT JOIN `aircraft_stand` st ON ap.`airport_id` = st.`airport_id`
GROUP BY ap.`airport_id`, ap.`iata_code`, ap.`icao_code`, ap.`airport_name`, ap.`city`, ap.`country`;
