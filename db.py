"""AURORA MySQL access layer.

The application deliberately uses the same MySQL database created by the
Workbench script. It never silently switches to a private SQLite database.
"""
import os
from contextlib import contextmanager

_DB_DRIVER = None


def load_env(env_path=None):
    """Load project .env values without overriding existing environment vars."""
    env_path = env_path or os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        with open(env_path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()


def _settings():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "aurora_db"),
        "connection_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
    }


def get_connection():
    """Return a MySQL connection, with an explicit error if it is unavailable."""
    global _DB_DRIVER
    config = _settings()
    if _DB_DRIVER in (None, "mysql.connector"):
        try:
            import mysql.connector
            connection = mysql.connector.connect(**config)
            _DB_DRIVER = "mysql.connector"
            return connection
        except ImportError:
            if _DB_DRIVER == "mysql.connector":
                raise
        except Exception:
            if _DB_DRIVER == "mysql.connector":
                raise

    if _DB_DRIVER in (None, "pymysql"):
        try:
            import pymysql
            connection = pymysql.connect(
                host=config["host"], port=config["port"], user=config["user"],
                password=config["password"], database=config["database"],
                connect_timeout=config["connection_timeout"],
                cursorclass=pymysql.cursors.DictCursor,
            )
            _DB_DRIVER = "pymysql"
            return connection
        except ImportError:
            if _DB_DRIVER == "pymysql":
                raise
        except Exception:
            if _DB_DRIVER == "pymysql":
                raise

    raise RuntimeError(
        "Cannot connect to the AURORA MySQL database. Start MySQL Server, "
        "run database/aurora_workbench_full.sql in Workbench, and check "
        "DB_HOST, DB_PORT, DB_USER, DB_PASSWORD and DB_NAME in .env. "
        "AURORA does not use a separate SQLite fallback."
    )


def _cursor(connection):
    if _DB_DRIVER == "mysql.connector":
        return connection.cursor(dictionary=True)
    return connection.cursor()


@contextmanager
def transaction():
    """Yield a dictionary-row cursor and commit/rollback as one unit."""
    connection = get_connection()
    cursor = _cursor(connection)
    try:
        yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


@contextmanager
def get_cursor():
    """Compatibility context for a single committed query."""
    with transaction() as cursor:
        yield cursor


def fetch_all(query, params=None):
    with get_cursor() as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchall()


def fetch_one(query, params=None):
    with get_cursor() as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchone()


def execute(query, params=None):
    with get_cursor() as cursor:
        cursor.execute(query, params or ())
        return cursor.lastrowid
