# AURORA — Technical Feasibility and Architecture Note

## 1. Project scope

AURORA is a local desktop DBMS application for a modeled airport network. It stores airline and aircraft data, airport infrastructure, predefined takeoff/landing operations, runway-direction assignments, compatibility rules, restrictions, and assignment audit history.

The application has two roles:

- **Administrator / ATC Controller:** operational dashboard, assignment validation, airport map, fleet/infrastructure views, and SQL reports.
- **Customer:** read-only scheduled departures board.

This is an academic model. It is not certified aviation software and does not implement real-world separation minima, dynamic runway allocation, or live air-traffic data.

## 2. Technology choices

| Layer | Choice | Rationale |
|---|---|---|
| Relational DBMS | MySQL 8.0+ with InnoDB | Foreign keys, unique/check constraints, transactions, row locking, views, triggers, and EXPLAIN support the DBMS syllabus and the assignment workflow. |
| Desktop UI | Python + Pygame | Keeps the project local and avoids a separate web server or frontend build pipeline. |
| Connectivity | mysql-connector-python / PyMySQL | Standard Python database drivers with parameterized SQL execution. |
| Authentication | Python PBKDF2-HMAC-SHA256 + MySQL RBAC tables | Passwords are stored as salted hashes; roles resolve named permissions through a junction table. |
| Configuration | `.env` + python-dotenv | Database connection settings stay outside source control. |

## 3. Database architecture

The model contains:

- **18 operational tables** covering the traffic-regulation workflow and supporting airport infrastructure, compatibility, schedules, restrictions, assignments, and audit history.
- **4 RBAC tables:** `app_user`, `app_role`, `app_permission`, and `role_permission`.
- **4 views** for arrivals, departures, assignment summaries, and airport infrastructure.
- **7 explicit secondary indexes** and **5 triggers (3 assignment-audit + 2 flight-endpoint integrity)**.

Views are virtual query objects and do not count toward the base-table total.

The Workbench handoff script, `database/aurora_workbench_full.sql`, is assembled from `database/schema.sql` and `database/seed.sql`. This keeps the teammate's one-file setup aligned with the developer setup. It is a clean-rebuild script: it drops and recreates the project's objects and reloads demonstration data.

## 4. Transaction and integrity strategy

Runway assignment is a multi-step operation:

1. Read and lock the selected operation and candidate runway direction.
2. Revalidate airport alignment, direction permissions, runway status, compatibility, and restriction windows inside the transaction.
3. Insert or update the unique assignment for that operation.
4. Let the database trigger append the audit event.
5. Commit all changes together, or roll back if an error occurs.

The assignment table has a unique constraint on `operation_id`, enforcing at most one current assignment per operation. Foreign keys protect references to operations and runway directions.

## 5. RBAC boundary

The desktop application checks the user's role permissions before exposing controller navigation or executing assignment actions. The Customer role is seeded with `schedule.read` only; the Administrator role receives the defined application permissions.

This is **application-level RBAC**. Both roles currently use the database connection configured in the local `.env` file. If customers are ever given direct MySQL access, separate MySQL accounts and server-side `GRANT` privileges must also be configured; application checks alone cannot constrain direct SQL access.

## 6. Operational feasibility

The deployment target is a teammate's laptop with MySQL Server, MySQL Workbench, Python, and the required Python packages installed.

Setup path:

1. Run `database/aurora_workbench_full.sql` in MySQL Workbench.
2. Copy `.env.example` to `.env` and configure the local MySQL connection.
3. Install dependencies with `python -m pip install -r requirements.txt`.
4. Launch with `python main.py`.

AURORA deliberately has no SQLite fallback. A hidden local database could diverge from the database created in Workbench and produce misleading demonstration results.

## 7. Limitations and future improvements

- The airport and runway data are demonstration records, not authoritative aeronautical data.
- Compatibility checks use a simplified eligibility matrix; they are not aircraft performance calculations.
- The customer role is restricted in the desktop application, not by separate MySQL grants.
- Demo credentials are included for classroom evaluation and should be changed before any real deployment.
- A future production-oriented version would need account-management screens, password-change/reset flows, server-side database privileges, stronger session handling, and additional concurrency tests.

## 8. Conclusion

The chosen stack is feasible for a local academic DBMS demonstration. MySQL provides the relational integrity and transaction mechanisms required by the model, while Python/Pygame provides a self-contained desktop interface. The single-file Workbench installer makes the database reproducible on the teammate's computer, and the role-specific UI demonstrates application authorization without changing the operational schema's scope.
