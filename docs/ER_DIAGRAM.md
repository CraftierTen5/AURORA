# AURORA — Entity-Relationship (ER) Schema Diagram
### Aircraft & Unified Runway Operations Records Archive
*MySQL 8.0+ / 8.4 LTS InnoDB Normalized Relational Architecture*

---

## 1. High-Level Entity-Relationship Model (Mermaid ERD)

```mermaid
erDiagram
    AIRLINE ||--o{ AIRCRAFT : "owns / operates"
    AIRLINE ||--o{ FLIGHT : "schedules"
    
    AIRCRAFT_TYPE ||--o{ AIRCRAFT : "categorizes"
    AIRCRAFT_TYPE ||--o{ AIRCRAFT_RUNWAY_COMPATIBILITY : "certified for"
    
    AIRPORT ||--o{ RUNWAY : "contains"
    AIRPORT ||--o{ TAXIWAY : "contains"
    AIRPORT ||--o{ TERMINAL : "contains"
    AIRPORT ||--o{ AIRCRAFT_STAND : "contains"
    AIRPORT ||--o{ AIRPORT_OPERATING_HOURS : "operates on"
    AIRPORT ||--o{ AIRPORT_MAP : "mapped by"
    AIRPORT ||--o{ FLIGHT : "origin / destination"
    AIRPORT ||--o{ FLIGHT_OPERATION : "hosts"
    
    TERMINAL ||--o{ AIRCRAFT_STAND : "serves"
    
    RUNWAY ||--|{ RUNWAY_DIRECTION : "has vectors (09/27)"
    RUNWAY ||--o{ AIRCRAFT_RUNWAY_COMPATIBILITY : "evaluated for"
    RUNWAY ||--o{ RUNWAY_RESTRICTION : "subject to"
    
    AIRPORT_MAP ||--o{ MAP_FEATURE : "includes waypoints & features"
    
    AIRCRAFT ||--o{ FLIGHT : "assigned to"
    
    FLIGHT ||--|{ FLIGHT_OPERATION : "consists of (takeoff/landing)"
    
    FLIGHT_OPERATION ||--o| RUNWAY_ASSIGNMENT : "manually assigned to"
    RUNWAY_DIRECTION ||--o{ RUNWAY_ASSIGNMENT : "allocated vector"
    
    RUNWAY_ASSIGNMENT ||--o{ ASSIGNMENT_AUDIT : "trigger logged to"

    %% Entity definitions with PK and FK
    AIRLINE {
        int airline_id PK
        string airline_name
        string iata_code UK
        string icao_code UK
        string country
        string callsign
        string operating_status
    }

    AIRCRAFT_TYPE {
        int type_id PK
        string manufacturer
        string model
        string variant
        string aircraft_category
        decimal wingspan
        decimal aircraft_length
        decimal max_takeoff_weight
        decimal max_landing_weight
        int passenger_capacity
        decimal min_runway_length
    }

    AIRCRAFT {
        int aircraft_id PK
        string registration_number UK
        int type_id FK
        int owner_airline_id FK
        int operator_airline_id FK
        date manufacturing_date
        string aircraft_status
    }

    AIRPORT {
        int airport_id PK
        string airport_name
        string iata_code UK
        string icao_code UK
        string city
        string country
        decimal latitude
        decimal longitude
        decimal elevation
        string timezone
    }

    RUNWAY {
        int runway_id PK
        int airport_id FK
        string runway_designation
        decimal runway_length
        decimal runway_width
        string surface_type
        string runway_status
        int start_x
        int start_y
        int end_x
        int end_y
    }

    RUNWAY_DIRECTION {
        int direction_id PK
        int runway_id FK
        string designation
        decimal heading
        boolean landing_permitted
        boolean takeoff_permitted
        boolean ils_available
        string approach_category
    }

    TAXIWAY {
        int taxiway_id PK
        int airport_id FK
        string taxiway_name
        string surface_type
        int start_x
        int start_y
        int end_x
        int end_y
    }

    TERMINAL {
        int terminal_id PK
        int airport_id FK
        string terminal_name
        string terminal_type
    }

    AIRCRAFT_STAND {
        int stand_id PK
        int airport_id FK
        int terminal_id FK
        string stand_code
        string max_aircraft_size
        string stand_status
    }

    FLIGHT {
        int flight_id PK
        string flight_number
        int airline_id FK
        int aircraft_id FK
        int origin_airport_id FK
        int destination_airport_id FK
        string flight_type
        date service_date
    }

    FLIGHT_OPERATION {
        int operation_id PK
        int flight_id FK
        int airport_id FK
        string operation_type
        datetime scheduled_datetime
        datetime actual_datetime
        string operation_status
    }

    AIRCRAFT_RUNWAY_COMPATIBILITY {
        int type_id PK, FK
        int runway_id PK, FK
        boolean landing_eligible
        boolean takeoff_eligible
        string remarks
    }

    RUNWAY_RESTRICTION {
        int restriction_id PK
        int runway_id FK
        string restriction_type
        datetime start_datetime
        datetime end_datetime
        string restriction_status
    }

    AIRPORT_OPERATING_HOURS {
        int hours_id PK
        int airport_id FK
        string day_of_week
        time opening_time
        time closing_time
    }

    RUNWAY_ASSIGNMENT {
        int assignment_id PK
        int operation_id UK, FK
        int direction_id FK
        datetime assignment_datetime
        string assignment_status
        string assigned_by
    }

    AIRPORT_MAP {
        int map_id PK
        int airport_id FK
        string map_name
        string map_type
        string coordinate_reference_system
    }

    MAP_FEATURE {
        int feature_id PK
        int map_id FK
        string feature_type
        string feature_name
        int pos_x
        int pos_y
    }

    ASSIGNMENT_AUDIT {
        int audit_id PK
        int assignment_id
        int operation_id
        int old_direction_id
        int new_direction_id
        string old_status
        string new_status
        string action_type
        string changed_by
        datetime changed_at
    }
```

---

## 2. Cardinality and Relationship Analysis

| Parent Entity | Child Entity | Cardinality | Business Semantics |
| :--- | :--- | :---: | :--- |
| `AIRPORT` | `RUNWAY` | 1 : N | An airport manages 1 or more physical runways. |
| `RUNWAY` | `RUNWAY_DIRECTION` | 1 : N (typically 1:2) | Each physical runway strip encompasses opposite directional vectors (e.g. 09 and 27). |
| `AIRPORT` | `TAXIWAY` | 1 : N | Aerodromes maintain named surface taxi links. |
| `AIRPORT` | `TERMINAL` | 1 : N | Passenger and cargo terminal facilities. |
| `TERMINAL` | `AIRCRAFT_STAND` | 1 : N (optional) | Parking stands/gates affiliated with terminals. |
| `AIRCRAFT_TYPE` | `AIRCRAFT` | 1 : N | Certified specifications instantiated by physical airframes. |
| `AIRLINE` | `AIRCRAFT` | 1 : N | Airlines own and operate specific airframes. |
| `FLIGHT` | `FLIGHT_OPERATION` | 1 : N (typically 1:2) | A scheduled flight splits into distinct takeoff and landing events. |
| `FLIGHT_OPERATION` | `RUNWAY_ASSIGNMENT` | 1 : 1 (or 1:0) | Each operation has at most one current manual runway assignment. |
| `RUNWAY_DIRECTION` | `RUNWAY_ASSIGNMENT` | 1 : N | Directions accept multiple sequential flight operations. |
| `AIRCRAFT_TYPE` + `RUNWAY` | `AIRCRAFT_RUNWAY_COMPATIBILITY` | M : N | Composite bridge validating airframe-to-runway suitability. |
| `RUNWAY` | `RUNWAY_RESTRICTION` | 1 : N | Scheduled closures, maintenance windows, and curfews. |
| `RUNWAY_ASSIGNMENT` | `ASSIGNMENT_AUDIT` | 1 : N | Audit log populated automatically via MySQL database triggers. |
