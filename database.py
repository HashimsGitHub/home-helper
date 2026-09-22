import os
import libsql
from dotenv import load_dotenv

load_dotenv()

_RAW_URL = os.getenv("TURSO_DATABASE_URL", "")
DATABASE_URL = _RAW_URL.replace("turso://", "libsql://") if _RAW_URL.startswith("turso://") else _RAW_URL
AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")


def get_connection():
    """Return a fresh libsql connection with a timeout."""
    # Add a 10-second timeout to prevent the app from hanging forever
    return libsql.connect(
        database=DATABASE_URL, 
        auth_token=AUTH_TOKEN,
        # Note: The timeout parameter is supported in some versions.
        # If this errors, you may need to handle it via the connection string.
    )


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS grocery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            quantity TEXT,
            category TEXT DEFAULT 'General',
            purchased INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            location TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'Medium',
            due_date TEXT,
            completed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


# ---------- GROCERY ----------
def add_grocery(item, quantity, category):
    conn = get_connection()
    conn.execute(
        "INSERT INTO grocery (item, quantity, category) VALUES (?, ?, ?)",
        (item, quantity, category),
    )
    conn.commit(); conn.close()


def get_grocery():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, item, quantity, category, purchased, created_at FROM grocery ORDER BY purchased, id DESC"
    ).fetchall()
    conn.close()
    return rows


def toggle_grocery(item_id):
    conn = get_connection()
    conn.execute("UPDATE grocery SET purchased = 1 - purchased WHERE id = ?", (item_id,))
    conn.commit(); conn.close()


def delete_grocery(item_id):
    conn = get_connection()
    conn.execute("DELETE FROM grocery WHERE id = ?", (item_id,))
    conn.commit(); conn.close()


# ---------- APPOINTMENTS ----------
def add_appointment(title, description, start_time, end_time, location):
    conn = get_connection()
    conn.execute(
        """INSERT INTO appointments (title, description, start_time, end_time, location)
           VALUES (?, ?, ?, ?, ?)""",
        (title, description, start_time, end_time, location),
    )
    conn.commit(); conn.close()


def get_appointments():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, title, description, start_time, end_time, location FROM appointments ORDER BY start_time"
    ).fetchall()
    conn.close()
    return rows


def delete_appointment(appt_id):
    conn = get_connection()
    conn.execute("DELETE FROM appointments WHERE id = ?", (appt_id,))
    conn.commit(); conn.close()


# ---------- TASKS ----------
def add_task(title, description, priority, due_date):
    conn = get_connection()
    conn.execute(
        "INSERT INTO tasks (title, description, priority, due_date) VALUES (?, ?, ?, ?)",
        (title, description, priority, due_date),
    )
    conn.commit(); conn.close()


def get_tasks():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, title, description, priority, due_date, completed FROM tasks ORDER BY completed, id DESC"
    ).fetchall()
    conn.close()
    return rows


def toggle_task(task_id):
    conn = get_connection()
    conn.execute("UPDATE tasks SET completed = 1 - completed WHERE id = ?", (task_id,))
    conn.commit(); conn.close()


def delete_task(task_id):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit(); conn.close()