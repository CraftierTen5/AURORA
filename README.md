# AURORA — Airport Runway & Operations Management

AURORA is a desktop DBMS project for managing predefined airport takeoff and landing operations, runway-direction assignments, aircraft/runway compatibility, airport infrastructure, and public departure information.

**Stack:** Python · Pygame · MySQL 8.0+ · MySQL Workbench

It is an academic simulation, not a certified air-traffic-control system.

## Two application roles

- **Administrator / ATC Controller:** operational dashboard, full schedule, runway assignment and validation, airport radar, fleet/infrastructure data, SQL reports, and audit history.
- **Customer:** read-only departures board showing scheduled takeoffs. No controller navigation or assignment actions are exposed.

The application uses database-backed RBAC tables and PBKDF2-HMAC-SHA256 password verification. The demo accounts are seeded for evaluation; change these credentials before any real deployment.

| Role | Username | Demo password |
|---|---|---|
| Administrator | `admin` | `AuroraAdmin!2026` |
| Customer | `customer` | `AuroraGuest!2026` |

## Database design

The operational model has **18 core tables**. Four additional tables implement application RBAC; views are separate database objects and do not count toward the table total.

### Operational tables (18)

`airline`, `aircraft_type`, `aircraft`, `airport`, `runway`, `runway_direction`, `taxiway`, `terminal`, `aircraft_stand`, `flight`, `flight_operation`, `aircraft_runway_compatibility`, `runway_restriction`, `airport_operating_hours`, `runway_assignment`, `airport_map`, `map_feature`, `assignment_audit`.

The model distinguishes a **physical runway** from its two **runway directions** (for example, 09/27). A scheduled movement is represented by `flight_operation`; the optional `runway_assignment` row records the manually selected direction. Assignment validation checks airport alignment, direction permissions, runway status, aircraft/runway certification, and restriction windows. Assignment revalidation and the write occur in one transaction, and triggers write the audit trail.

### RBAC tables (4)

- `app_user`: salted password hash, account state, and role reference.
- `app_role`: Administrator and Customer roles.
- `app_permission`: named application capabilities.
- `role_permission`: many-to-many role/permission mapping.

The seeded Customer role receives only `schedule.read`; the Administrator role receives all defined capabilities.

### Views, indexes and triggers

The schema currently defines four views for arrivals, departures, runway-assignment summaries, and airport-infrastructure summaries. It also defines seven explicit secondary indexes and five triggers (three assignment-audit triggers and two flight-endpoint integrity triggers). Add further views as useful for reports; they do not increase the core table count.

## MySQL Workbench setup (friend's laptop)

The **single-file Workbench installer** is the handoff artifact. Your teammate does not need the Python setup script or separate schema/seed files to create the database.

1. Install and start MySQL Server 8.0+ and MySQL Workbench.
2. Open `database/aurora_workbench_full.sql` in Workbench.
3. Execute the entire script (lightning bolt / Ctrl+Shift+Enter).
4. Refresh the Schemas panel and confirm `aurora_db` appears.
5. Run the verification queries at the end of the script. Expect 22 tables (18 operational + 4 RBAC) and four views.

> **Important:** This is a clean-rebuild installer. It drops and recreates AURORA's existing project tables, views, and triggers before loading the demo dataset. Do not run it against a database containing data you need to keep.

For command-line setup, run the same file with the MySQL client:
```bash
mysql -u root -p < database/aurora_workbench_full.sql
```

## Run the desktop application

Create a local `.env` from `.env.example` and set the MySQL connection details:

```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=aurora_db
```

Then install dependencies and launch:

```bash
python -m pip install -r requirements.txt
python main.py
```

AURORA now requires the configured MySQL database. It intentionally does **not** fall back to a private SQLite file, because that could make the application display data different from the database your team created in Workbench.

## Developer setup

For separate schema and seed execution:

```bash
python database/setup_db.py
```

This script is also a clean rebuild and executes `database/schema.sql` followed by `database/seed.sql`.

Run the authentication unit tests:

```bash
python -m unittest discover -s tests -v
```

After initializing MySQL, run the database-backed runway validation cases:

```bash
python tests/test_validation.py
```

## DBMS syllabus coverage

See [DBMS concept mapping](docs/DBMS_CONCEPT_MAPPING.md) for the concepts, SQL demonstrations, and honest boundaries of what the project implements. Other design references:

- [ER diagram](docs/ER_DIAGRAM.md)
- [Relational schema](docs/RELATIONAL_SCHEMA.md)
- [Database report](docs/AURORA_DATABASE_REPORT.md)
- [SQL query demonstrations](database/queries.sql)

## Repository structure

```
AURORA/
├── main.py
├── app.py
├── auth.py
├── db.py
├── validator.py
├── ui_components.py
├── airport_map.py
├── database/
│   ├── aurora_workbench_full.sql  # single-file handoff installer
│   ├── schema.sql                 # canonical DDL
│   ├── seed.sql                   # demo dataset + demo accounts
│   ├── queries.sql                # syllabus demonstrations
│   └── setup_db.py                # developer setup utility
├── docs/
└── tests/
```
