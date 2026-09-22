import os

import libsql
import streamlit as st
from dotenv import load_dotenv


load_dotenv()

_CONNECTION_KEY = "_homehelper_db_connection"
CACHE_TTL_SECONDS = 5


class UsernameTakenError(ValueError):
    """Raised when a registration uses an existing username."""


def _setting(name, default=""):
    """Read Streamlit Cloud secrets first, then fall back to local environment."""
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)


_RAW_URL = _setting("TURSO_DATABASE_URL")
DATABASE_URL = _RAW_URL.replace("turso://", "libsql://") if _RAW_URL.startswith("turso://") else _RAW_URL
AUTH_TOKEN = _setting("TURSO_AUTH_TOKEN", None)


def _new_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "TURSO_DATABASE_URL is not configured. Add it to Streamlit Secrets "
            "or your local .env file."
        )

    options = {"database": DATABASE_URL}
    if AUTH_TOKEN:
        options["auth_token"] = AUTH_TOKEN
    return libsql.connect(**options)


def _has_streamlit_session():
    """Return True only while code is executing inside a Streamlit session."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        return get_script_run_ctx(suppress_warning=True) is not None
    except (ImportError, TypeError):
        return False


def get_connection():
    """Reuse one connection per Streamlit session; use a fresh one for scripts."""
    if _has_streamlit_session():
        connection = st.session_state.get(_CONNECTION_KEY)
        if connection is None:
            connection = _new_connection()
            st.session_state[_CONNECTION_KEY] = connection
        return connection
    return _new_connection()


def _release_connection(connection):
    """Close transient script connections but retain the session connection."""
    if _has_streamlit_session() and st.session_state.get(_CONNECTION_KEY) is connection:
        return
    connection.close()


def close_session_connection():
    """Close the current session's connection, normally when signing out."""
    connection = st.session_state.pop(_CONNECTION_KEY, None)
    if connection is not None:
        try:
            connection.close()
        except Exception:
            pass


def _column_names(connection, table_name):
    return {
        row[1]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }


def _ensure_user_column(connection, table_name):
    """Add ownership to an existing installation without deleting legacy data."""
    if "user_id" not in _column_names(connection, table_name):
        connection.execute(
            f"ALTER TABLE {table_name} "
            "ADD COLUMN user_id INTEGER REFERENCES homehelper_users(id)"
        )


def init_db():
    """Create the schema and safely migrate pre-login installations."""
    connection = get_connection()
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS homehelper_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                pin TEXT NOT NULL CHECK(
                    length(pin) = 4 AND pin NOT GLOB '*[^0-9]*'
                ),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS grocery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                quantity TEXT,
                category TEXT DEFAULT 'General',
                purchased INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER REFERENCES homehelper_users(id)
            );
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                location TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER REFERENCES homehelper_users(id)
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'Medium',
                due_date TEXT,
                completed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER REFERENCES homehelper_users(id)
            );
            """
        )

        for table_name in ("grocery", "appointments", "tasks"):
            _ensure_user_column(connection, table_name)

        connection.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_grocery_user ON grocery(user_id);
            CREATE INDEX IF NOT EXISTS idx_appointments_user ON appointments(user_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
            """
        )
        connection.commit()
    finally:
        _release_connection(connection)


# ---------- CACHE MANAGEMENT ----------
def _clear_grocery_cache():
    get_grocery.clear()
    get_dashboard.clear()


def _clear_appointment_cache():
    get_appointments.clear()
    get_dashboard.clear()


def _clear_task_cache():
    get_tasks.clear()
    get_dashboard.clear()


# ---------- USERS ----------
def create_user(username, pin):
    connection = get_connection()
    try:
        connection.execute(
            "INSERT INTO homehelper_users (username, pin) VALUES (?, ?)",
            (username.strip(), pin),
        )
        connection.commit()
        return connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    except Exception as exc:
        if "UNIQUE" in str(exc).upper():
            raise UsernameTakenError(username) from exc
        raise
    finally:
        _release_connection(connection)


def authenticate_user(username, pin):
    connection = get_connection()
    try:
        row = connection.execute(
            """SELECT id, username
               FROM homehelper_users
               WHERE username = ? COLLATE NOCASE AND pin = ?""",
            (username.strip(), pin),
        ).fetchone()
        return tuple(row) if row else None
    finally:
        _release_connection(connection)


# ---------- DASHBOARD ----------
@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_dashboard(user_id):
    """Load all dashboard records in one remote query instead of three."""
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT 'grocery', id, item, quantity, category, purchased, created_at
            FROM grocery WHERE user_id = ?
            UNION ALL
            SELECT 'appointment', id, title, description, start_time, end_time, location
            FROM appointments WHERE user_id = ?
            UNION ALL
            SELECT 'task', id, title, description, priority, due_date, completed
            FROM tasks WHERE user_id = ?
            """,
            (user_id, user_id, user_id),
        ).fetchall()
    finally:
        _release_connection(connection)

    result = {"groceries": [], "appointments": [], "tasks": []}
    for row in rows:
        record = tuple(row[1:])
        if row[0] == "grocery":
            result["groceries"].append(record)
        elif row[0] == "appointment":
            result["appointments"].append(record)
        else:
            result["tasks"].append(record)

    result["groceries"].sort(key=lambda row: (row[4], -row[0]))
    result["appointments"].sort(key=lambda row: row[3] or "")
    result["tasks"].sort(key=lambda row: (row[5], -row[0]))
    return result


# ---------- GROCERY ----------
def add_grocery(user_id, item, quantity, category):
    connection = get_connection()
    try:
        connection.execute(
            "INSERT INTO grocery (user_id, item, quantity, category) VALUES (?, ?, ?, ?)",
            (user_id, item, quantity, category),
        )
        connection.commit()
    finally:
        _release_connection(connection)
    _clear_grocery_cache()


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_grocery(user_id):
    connection = get_connection()
    try:
        rows = connection.execute(
            """SELECT id, item, quantity, category, purchased, created_at
               FROM grocery
               WHERE user_id = ?
               ORDER BY purchased, id DESC""",
            (user_id,),
        ).fetchall()
        return [tuple(row) for row in rows]
    finally:
        _release_connection(connection)


def toggle_grocery(user_id, item_id):
    connection = get_connection()
    try:
        connection.execute(
            """UPDATE grocery SET purchased = 1 - purchased
               WHERE id = ? AND user_id = ?""",
            (item_id, user_id),
        )
        connection.commit()
    finally:
        _release_connection(connection)
    _clear_grocery_cache()


def delete_grocery(user_id, item_id):
    connection = get_connection()
    try:
        connection.execute(
            "DELETE FROM grocery WHERE id = ? AND user_id = ?",
            (item_id, user_id),
        )
        connection.commit()
    finally:
        _release_connection(connection)
    _clear_grocery_cache()


# ---------- APPOINTMENTS ----------
def add_appointment(user_id, title, description, start_time, end_time, location):
    connection = get_connection()
    try:
        connection.execute(
            """INSERT INTO appointments
               (user_id, title, description, start_time, end_time, location)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, title, description, start_time, end_time, location),
        )
        connection.commit()
    finally:
        _release_connection(connection)
    _clear_appointment_cache()


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_appointments(user_id):
    connection = get_connection()
    try:
        rows = connection.execute(
            """SELECT id, title, description, start_time, end_time, location
               FROM appointments
               WHERE user_id = ?
               ORDER BY start_time""",
            (user_id,),
        ).fetchall()
        return [tuple(row) for row in rows]
    finally:
        _release_connection(connection)


def delete_appointment(user_id, appointment_id):
    connection = get_connection()
    try:
        connection.execute(
            "DELETE FROM appointments WHERE id = ? AND user_id = ?",
            (appointment_id, user_id),
        )
        connection.commit()
    finally:
        _release_connection(connection)
    _clear_appointment_cache()


# ---------- TASKS ----------
def add_task(user_id, title, description, priority, due_date):
    connection = get_connection()
    try:
        connection.execute(
            """INSERT INTO tasks (user_id, title, description, priority, due_date)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, title, description, priority, due_date),
        )
        connection.commit()
    finally:
        _release_connection(connection)
    _clear_task_cache()


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_tasks(user_id):
    connection = get_connection()
    try:
        rows = connection.execute(
            """SELECT id, title, description, priority, due_date, completed
               FROM tasks
               WHERE user_id = ?
               ORDER BY completed, id DESC""",
            (user_id,),
        ).fetchall()
        return [tuple(row) for row in rows]
    finally:
        _release_connection(connection)


def toggle_task(user_id, task_id):
    connection = get_connection()
    try:
        connection.execute(
            """UPDATE tasks SET completed = 1 - completed
               WHERE id = ? AND user_id = ?""",
            (task_id, user_id),
        )
        connection.commit()
    finally:
        _release_connection(connection)
    _clear_task_cache()


def delete_task(user_id, task_id):
    connection = get_connection()
    try:
        connection.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        )
        connection.commit()
    finally:
        _release_connection(connection)
    _clear_task_cache()
