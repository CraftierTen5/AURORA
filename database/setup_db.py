"""
AURORA - Database Automated Setup Script (Python)
Executes schema.sql and seed.sql using credentials from .env.
Works with either `mysql.connector` or `pymysql`.
"""

import os
import sys
import re

def load_env(env_path=".env"):
    """Loads key-value pairs from .env into os.environ with fallback."""
    if not os.path.exists(env_path):
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        # Fallback custom parser
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def get_connection(include_db=False):
    """Establishes connection using mysql.connector or pymysql."""
    host = os.environ.get("DB_HOST", "localhost")
    port = int(os.environ.get("DB_PORT", 3306))
    user = os.environ.get("DB_USER", "root")
    password = os.environ.get("DB_PASSWORD", "")
    db_name = os.environ.get("DB_NAME", "aurora_db")

    # Try mysql.connector first (as used in original Artos)
    try:
        import mysql.connector
        kwargs = {
            "host": host,
            "port": port,
            "user": user,
            "password": password
        }
        if include_db:
            kwargs["database"] = db_name
        conn = mysql.connector.connect(**kwargs)
        return conn, "mysql.connector"
    except ImportError:
        pass

    # Try pymysql as fallback
    try:
        import pymysql
        kwargs = {
            "host": host,
            "port": port,
            "user": user,
            "password": password
        }
        if include_db:
            kwargs["database"] = db_name
        conn = pymysql.connect(**kwargs)
        return conn, "pymysql"
    except ImportError:
        pass

    raise RuntimeError(
        "Neither 'mysql.connector' nor 'pymysql' is installed.\n"
        "Please run: pip install mysql-connector-python  (or: pip install pymysql)"
    )

def split_sql(sql_content):
    """Parses SQL statements respecting MySQL DELIMITER blocks."""
    statements = []
    current_delim = ";"
    buffer = []

    for line in sql_content.splitlines():
        trimmed = line.strip()
        if trimmed.upper().startswith("DELIMITER "):
            current_delim = trimmed[10:].strip()
            continue

        buffer.append(line)
        joined = "\n".join(buffer)

        if current_delim == ";" and trimmed.endswith(";"):
            statements.append(joined)
            buffer = []
        elif current_delim == "$$" and trimmed.endswith("$$"):
            clean = re.sub(r"\$\$\s*$", "", joined.strip())
            statements.append(clean)
            buffer = []

    if buffer:
        rem = "\n".join(buffer).strip()
        if rem:
            statements.append(rem)

    return statements

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(base_dir, ".env")
    load_env(env_file)

    db_name = os.environ.get("DB_NAME", "aurora_db")
    host = os.environ.get("DB_HOST", "localhost")
    user = os.environ.get("DB_USER", "root")

    print("=" * 60)
    print("   AURORA: Relational Database Initialization (Python)")
    print("=" * 60)
    print(f"Connecting to MySQL server at {host} as user '{user}'...")

    try:
        conn, driver = get_connection(include_db=False)
        print(f"Driver loaded: {driver}")
        cursor = conn.cursor()

        print(f"Creating database '{db_name}' if not exists...")
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
            f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
        cursor.execute(f"USE `{db_name}`;")
        conn.commit()

        # 1. Execute schema.sql
        schema_path = os.path.join(base_dir, "database", "schema.sql")
        print(f"Executing DDL schema from {schema_path}...")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        stmts = split_sql(schema_sql)
        for s in stmts:
            if s.strip():
                try:
                    cursor.execute(s)
                except Exception as ex:
                    print(f"Error on: {s[:100]}...\n{ex}")
                    raise
        conn.commit()
        print("Schema tables, constraints, triggers, and views created.")

        # 2. Execute seed.sql
        seed_path = os.path.join(base_dir, "database", "seed.sql")
        print(f"Populating demonstration seed data from {seed_path}...")
        with open(seed_path, "r", encoding="utf-8") as f:
            seed_sql = f.read()

        seed_stmts = split_sql(seed_sql)
        for s in seed_stmts:
            if s.strip():
                try:
                    cursor.execute(s)
                except Exception as ex:
                    print(f"Error on: {s[:100]}...\n{ex}")
                    raise
        conn.commit()
        print("Seed data inserted successfully.")

        # 3. Verification row counts
        tables = [
            "airline", "aircraft_type", "aircraft", "airport", "runway",
            "runway_direction", "taxiway", "terminal", "aircraft_stand",
            "flight", "flight_operation", "aircraft_runway_compatibility",
            "runway_restriction", "airport_operating_hours", "runway_assignment",
            "airport_map", "map_feature", "assignment_audit",
            "app_role", "app_permission", "role_permission", "app_user"
        ]

        print("\n--- INSTALLED TABLES & ROW COUNTS (18 operational + 4 RBAC) ---")
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM `{t}`")
            row = cursor.fetchone()
            cnt = row[0] if row else 0
            print(f"  Table [{t:<30}]: {cnt} rows")

        cursor.close()
        conn.close()
        print("\n" + "=" * 60)
        print(" Database setup completed successfully!")
        print(" You can now launch AURORA using: python main.py")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
