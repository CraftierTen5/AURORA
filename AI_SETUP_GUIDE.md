# AURORA Local Setup Guide (Human + AI Agent)

This is the local setup runbook for a fresh Windows development machine. It is written so an AI coding assistant can guide setup without guessing project configuration.

> **AI-agent instruction:** Read this guide first, then inspect the current repository files it references before changing anything. If this guide and the implementation differ, treat checked-in files as the source of truth. Never invent credentials, overwrite an existing \`.env\`, run the destructive SQL installer without warning and explicit confirmation, or commit/push unless asked.

## 1. Project overview

AURORA is a Python/Pygame desktop application backed by MySQL. It models airport infrastructure, scheduled flight operations, runway-direction assignment and validation, a public departures board, and application-level role-based access control (RBAC).

- Desktop UI: Python + Pygame Community Edition (\`pygame-ce\`; imported in Python as \`pygame\`).
- Database: MySQL Server 8.0+ (MySQL 8.4 LTS is suitable).
- SQL client: MySQL Workbench.
- Python database drivers: \`mysql-connector-python\`, with \`PyMySQL\` fallback.
- Configuration: local, untracked \`.env\` file in the repository root.
- Entry point: \`main.py\`.

This is an academic simulation, not a certified air-traffic-control system.

## 2. Prerequisites

Install these on the Windows laptop:

1. Git for Windows.
2. Python 3.11 or 3.12 (64-bit) is recommended for a predictable environment. Enable the Python launcher (\`py\`) during installation. Check installed interpreters with \`py -0p\`.
3. MySQL Server 8.0+ (the actual database server).
4. MySQL Workbench (the graphical SQL client).
5. Internet access for the initial clone and package installation.

**Important:** Workbench alone is not a database server. Also, do not install regular \`pygame\` separately; this project uses \`pygame-ce\`, which provides the \`pygame\` import.

## 3. Clone the repository

Open **Windows PowerShell**:

\`\`\`powershell
Set-Location "$HOME\Desktop"
git clone https://github.com/CraftierTen5/AURORA.git
Set-Location ".\AURORA"
\`\`\`

If the repository is already cloned, enter that existing directory instead of cloning again:

\`\`\`powershell
Set-Location "C:\path\to\AURORA"
git pull
\`\`\`

The current development branch used by the team is \`feature/aurora-role-based-ui\`. If that branch is still the intended handoff branch and has not been merged/deleted:

\`\`\`powershell
git fetch origin
git switch feature/aurora-role-based-ui
git pull --ff-only origin feature/aurora-role-based-ui
\`\`\`

If that branch has been merged or deleted, stay on the repository's default branch. Do not recreate a deleted branch.

## 4. Install and verify MySQL

1. Install **MySQL Server 8.0+**. During configuration, note the host (normally \`localhost\`), port (normally \`3306\`), username (often \`root\`), and password you choose.
2. Install and open **MySQL Workbench**.
3. Create/open a local connection. Typical values:
   - Hostname: \`127.0.0.1\` or \`localhost\`
   - Port: \`3306\`
   - Username: \`root\` (or the account configured on that machine)
   - Password: the password configured for that MySQL account.
4. Click **Test Connection**. It must succeed before continuing.

If Workbench cannot connect, verify that the MySQL Server Windows service is running. Workbench is only a client.

## 5. Create and seed the database

Use the single-file Workbench installer:

1. In Workbench, choose **File → Open SQL Script**.
2. Open \`database/aurora_workbench_full.sql\` from the cloned repository.
3. Read the warning at the top of the script.
4. Execute the entire script using the lightning-bolt execute button.
5. Wait for completion and inspect the Action Output panel for SQL errors.
6. Refresh the **Schemas** panel. The database should be named \`aurora_db\`.
7. Inspect/run the verification queries at the end of the script. Expected base-table count: **22** (18 operational + 4 RBAC tables). Views are separate objects.

### Destructive installer warning

\`database/aurora_workbench_full.sql\` is a **clean-rebuild installer**. It drops and recreates AURORA's project tables, views, and triggers in \`aurora_db\`, then inserts the demonstration dataset. Do not run it against an existing \`aurora_db\` containing data that must be preserved. Back up important data first. The installer creates the database and schema; do not manually create the tables beforehand.

### Alternative: MySQL command line

If the MySQL client is installed and on PATH, run from the repository root in PowerShell:

\`\`\`powershell
Get-Content -Raw ".\database\aurora_workbench_full.sql" | mysql --host=localhost --port=3306 --user=root --password
\`\`\`

The client prompts for the MySQL password. Workbench is recommended if \`mysql\` is not on PATH.

## 6. Configure the local .env file

From the repository root:

\`\`\`powershell
Copy-Item ".env.example" ".env"
notepad .env
\`\`\`

Set the values to match the MySQL connection that succeeded in Workbench:

\`\`\`dotenv
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=PUT_THE_MYSQL_PASSWORD_HERE
DB_NAME=aurora_db
DB_CONNECT_TIMEOUT=5
\`\`\`

Replace \`PUT_THE_MYSQL_PASSWORD_HERE\` with the actual password for the MySQL account above. Do not include angle brackets or spaces around equals signs. If the password contains \`#\`, \`;\`, or spaces, quote the value, e.g. \`DB_PASSWORD="your password"\`.

| Variable | Meaning |
|---|---|
| \`DB_HOST\` | MySQL host; normally \`localhost\`. |
| \`DB_PORT\` | MySQL TCP port; normally \`3306\`. |
| \`DB_USER\` | MySQL account used in Workbench. |
| \`DB_PASSWORD\` | That MySQL account's password, **not** an AURORA demo-user password. |
| \`DB_NAME\` | Keep this as \`aurora_db\`. |
| \`DB_CONNECT_TIMEOUT\` | Connection timeout in seconds; supplied default is \`5\`. |

Keep \`.env\` private. It belongs in the repository root (beside \`main.py\`) and should be ignored by Git. Never commit it or paste its password into chat. \`.env.example\` is the safe tracked template and should not contain a real password. If \`.env\` already exists, inspect it and do not overwrite it.

## 7. Create a Python virtual environment and install dependencies

Run from the repository root in PowerShell. If Python 3.12 is installed:

\`\`\`powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
\`\`\`

For Python 3.11, replace \`-3.12\` with \`-3.11\`.

If PowerShell blocks activation, run this for the current terminal only, then activate again:

\`\`\`powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
\`\`\`

Verify:

\`\`\`powershell
python --version
python -m pip show pygame-ce mysql-connector-python PyMySQL python-dotenv
\`\`\`

The prompt should show \`(.venv)\`. Use \`python -m pip\` to ensure packages install into the active environment.

The exact dependencies are in \`requirements.txt\`: \`pygame-ce\`, \`mysql-connector-python\`, \`PyMySQL\`, and \`python-dotenv\`. The code imports Pygame as \`pygame\`.

## 8. Launch and log in

Ensure MySQL Server is running, the installer succeeded, and the root \`.env\` has correct connection details. Then:

\`\`\`powershell
python main.py
\`\`\`

The Pygame desktop login window should open. Run from the repository root using \`main.py\`; it sets Windows DPI awareness before the Pygame/SDL application is imported.

### Seeded AURORA application accounts

These are **application login** credentials created by the SQL seed. They are not MySQL credentials.

| Role | Username | Demo password |
|---|---|---|
| Administrator / ATC | \`admin\` | \`AuroraAdmin!2026\` |
| Customer (read-only departures) | \`customer\` | \`AuroraGuest!2026\` |

Administrator gets the controller interface. Customer gets the read-only scheduled departures board. Application RBAC checks permissions in the app. Both roles connect using the MySQL credentials in \`.env\`; do not give customers MySQL credentials or direct database access. These demo passwords are for classroom evaluation; change them before any real deployment.

AURORA requires MySQL and does **not** silently fall back to SQLite. If the database is unavailable, fix the service, schema, or connection settings.

## 9. Run tests

With \`.venv\` active and the terminal at the repository root:

\`\`\`powershell
python -m unittest discover -s tests -v
\`\`\`

The database-backed runway validation test also needs MySQL running, the initialized \`aurora_db\`, and correct \`.env\` values:

\`\`\`powershell
python tests/test_validation.py
\`\`\`

Do not interpret a database connection failure as a runway-logic failure; verify the database setup first.

## 10. Troubleshooting

### Cannot connect to AURORA MySQL database

Check in this order:

1. MySQL **Server** is installed and its Windows service is running.
2. Workbench connects using the same host, port, username, and password.
3. \`aurora_db\` exists in Workbench's Schemas panel.
4. The complete installer ran without SQL errors.
5. \`.env\` is in the repository root beside \`main.py\`.
6. \`DB_HOST\`, \`DB_PORT\`, \`DB_USER\`, \`DB_PASSWORD\`, and \`DB_NAME\` match the working Workbench connection.

### Access denied for user

The MySQL username/password in \`.env\` is wrong or that account lacks access. This is unrelated to the AURORA \`admin\` / \`customer\` application login passwords.

### Unknown database or missing tables

The Workbench installer has not successfully initialized this server. Open and execute \`database/aurora_workbench_full.sql\`, then refresh Schemas.

### No module named pygame

Activate \`.venv\` and reinstall the requirements:

\`\`\`powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
\`\`\`

Install \`pygame-ce\` through the requirements file; do not install regular \`pygame\` separately.

### PowerShell cannot activate .venv

Use the process-scoped execution-policy command in section 7. It applies only to the current PowerShell process.

### Blurry Pygame window on Windows

Launch with \`python main.py\`, not by importing \`app.py\` directly. The entry point configures Windows/SDL DPI awareness before importing the app. Display scaling and monitor changes can affect physical window size; do not remove the DPI setup without testing.

## 11. Key repository files

| File | Purpose |
|---|---|
| \`main.py\` | Entry point and prerequisite check. |
| \`app.py\` | Main Pygame app, login, role-specific screens, event handling. |
| \`auth.py\` | Application password verification and role/permission checks. |
| \`db.py\` | Loads \`.env\` and opens MySQL connections; no SQLite fallback. |
| \`validator.py\` | Runway-assignment validation logic. |
| \`ui_components.py\` | Reusable Pygame buttons, cards, tables, and dialogs. |
| \`airport_map.py\` | Airport map/radar view. |
| \`requirements.txt\` | Python dependencies. |
| \`.env.example\` | Safe template for local database connection settings. |
| \`database/aurora_workbench_full.sql\` | Single-file MySQL clean-rebuild installer (schema + seed). |
| \`database/schema.sql\` | Canonical database DDL. |
| \`database/seed.sql\` | Demo dataset and seeded application users. |
| \`database/setup_db.py\` | Alternative Python schema + seed setup utility; also a clean rebuild. |
| \`tests/\` | Unit and database-backed tests. |
| \`docs/DBMS_CONCEPT_MAPPING.md\` | Mapping of implementation to DBMS concepts. |

## 12. Instructions for an AI setup/coding agent

1. Establish the repository root and OS. Commands in this guide assume **Windows PowerShell**.
2. Read this guide, \`README.md\`, \`requirements.txt\`, \`.env.example\`, \`db.py\`, and \`main.py\` before suggesting setup changes.
3. Check whether \`.venv\` exists and is active before creating another environment.
4. Check whether \`.env\` exists. If it does, **never overwrite it**. If absent, copy \`.env.example\` and ask the user to enter their MySQL password locally; never ask them to paste secrets into chat.
5. Confirm MySQL **Server**, not only Workbench, is installed and running.
6. Confirm Workbench connectivity, then check whether \`aurora_db\` and its objects exist. Do not execute the clean-rebuild installer automatically. Explain that it drops/recreates project objects and obtain explicit confirmation first.
7. Install the dependencies from \`requirements.txt\`. This project uses \`pygame-ce\` (imported as \`pygame\`), \`mysql-connector-python\`, \`PyMySQL\`, and \`python-dotenv\`.
8. Keep application demo credentials separate from MySQL credentials.
9. Launch normally with \`python main.py\` from the repository root.
10. Diagnose the actual error and inspect relevant source before editing. Do not replace MySQL with SQLite, remove authentication, weaken permission checks, or silently alter the schema to force startup.
11. Prefer minimal, reversible changes. Do not commit, push, or switch branches unless requested.
12. If this guide becomes stale, verify the implementation and update this document rather than blindly following outdated instructions.

## 13. Setup completion checklist

- [ ] Repository cloned and intended branch checked out.
- [ ] MySQL Server 8.0+ installed and running.
- [ ] MySQL Workbench connection test succeeds.
- [ ] \`database/aurora_workbench_full.sql\` executed successfully.
- [ ] \`aurora_db\` and expected tables/views visible in Workbench.
- [ ] Root \`.env\` created with correct MySQL connection values.
- [ ] Python virtual environment created and activated.
- [ ] \`requirements.txt\` installed successfully.
- [ ] \`python main.py\` opens the AURORA login screen.
- [ ] Both demo application roles tested.
