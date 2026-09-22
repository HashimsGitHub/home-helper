import os

import libsql
from dotenv import load_dotenv


load_dotenv()


class UsernameTakenError(ValueError):
    """Raised when a registration uses an existing username."""


def _setting(name, default=""):
    """Read Streamlit Cloud secrets first, then fall back to local environment."""
    try:
        import streamlit as st

        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)


_RAW_URL = _setting("TURSO_DATABASE_URL")
DATABASE_URL = _RAW_URL.replace("turso://", "libsql://") if _RAW_URL.startswith("turso://") else _RAW_URL
AUTH_TOKEN = _setting("TURSO_AUTH_TOKEN", None)


def get_connection():
    """Return a fresh local or Turso libSQL connection."""
    if not DATABASE_URL:
        raise RuntimeError(
            "TURSO_DATABASE_URL is not configured. Add it to Streamlit Secrets "
            "or your local .env file."
        )

    options = {"database": DATABASE_URL}
    if AUTH_TOKEN:
        options["auth_token"] = AUTH_TOKEN
    return libsql.connect(**options)


def _column_names(conn, table_name):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}


def _ensure_user_column(conn, table_name):
    """Add ownership to an existing installation without deleting legacy data."""
    if "user_id" not in _column_names(conn, table_name):
        conn.execute(
            f"ALTER TABLE {table_name} "
            "ADD COLUMN user_id INTEGER REFERENCES homehelper_users(id)"
        )


def init_db():
    """Create the schema and safely migrate pre-login installations."""
    conn = get_connection()
    conn.executescript(
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

    # Existing deployments already have the three data tables. ALTER only when
    # needed; their old rows remain NULL-owned and therefore invisible.
    for table_name in ("grocery", "appointments", "tasks"):
        _ensure_user_column(conn, table_name)

    conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_grocery_user ON grocery(user_id);
        CREATE INDEX IF NOT EXISTS idx_appointments_user ON appointments(user_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
        """
    )
    conn.commit()
    conn.close()


# ---------- USERS ----------
def create_user(username, pin):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO homehelper_users (username, pin) VALUES (?, ?)",
            (username.strip(), pin),
        )
        conn.commit()
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return user_id
    except Exception as exc:
        if "UNIQUE" in str(exc).upper():
            raise UsernameTakenError(username) from exc
        raise
    finally:
        conn.close()


def authenticate_user(username, pin):
    conn = get_connection()
    row = conn.execute(
        """SELECT id, username
           FROM homehelper_users
           WHERE username = ? COLLATE NOCASE AND pin = ?""",
        (username.strip(), pin),
    ).fetchone()
    conn.close()
    return row


# ---------- GROCERY ----------
def add_grocery(user_id, item, quantity, category):
    conn = get_connection()
    conn.execute(
        "INSERT INTO grocery (user_id, item, quantity, category) VALUES (?, ?, ?, ?)",
        (user_id, item, quantity, category),
    )
    conn.commit()
    conn.close()


def get_grocery(user_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, item, quantity, category, purchased, created_at
           FROM grocery
           WHERE user_id = ?
           ORDER BY purchased, id DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def toggle_grocery(user_id, item_id):
    conn = get_connection()
    conn.execute(
        """UPDATE grocery SET purchased = 1 - purchased
           WHERE id = ? AND user_id = ?""",
        (item_id, user_id),
    )
    conn.commit()
    conn.close()


def delete_grocery(user_id, item_id):
    conn = get_connection()
    conn.execute(
        "DELETE FROM grocery WHERE id = ? AND user_id = ?",
        (item_id, user_id),
    )
    conn.commit()
    conn.close()


# ---------- APPOINTMENTS ----------
def add_appointment(user_id, title, description, start_time, end_time, location):
    conn = get_connection()
    conn.execute(
        """INSERT INTO appointments
           (user_id, title, description, start_time, end_time, location)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, title, description, start_time, end_time, location),
    )
    conn.commit()
    conn.close()


def get_appointments(user_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, title, description, start_time, end_time, location
           FROM appointments
           WHERE user_id = ?
           ORDER BY start_time""",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def delete_appointment(user_id, appointment_id):
    conn = get_connection()
    conn.execute(
        "DELETE FROM appointments WHERE id = ? AND user_id = ?",
        (appointment_id, user_id),
    )
    conn.commit()
    conn.close()


# ---------- TASKS ----------
def add_task(user_id, title, description, priority, due_date):
    conn = get_connection()
    conn.execute(
        """INSERT INTO tasks (user_id, title, description, priority, due_date)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, title, description, priority, due_date),
    )
    conn.commit()
    conn.close()


def get_tasks(user_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, title, description, priority, due_date, completed
           FROM tasks
           WHERE user_id = ?
           ORDER BY completed, id DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def toggle_task(user_id, task_id):
    conn = get_connection()
    conn.execute(
        """UPDATE tasks SET completed = 1 - completed
           WHERE id = ? AND user_id = ?""",
        (task_id, user_id),
    )
    conn.commit()
    conn.close()


def delete_task(user_id, task_id):
    conn = get_connection()
    conn.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user_id),
    )
    conn.commit()
    conn.close()
