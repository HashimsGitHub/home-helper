"""Small administrator utility for viewing registered Home Helper users.

Run from the project folder after configuring the same Turso environment
variables used by the app:

    python homehelper_turso.py

PINs are displayed because this prototype intentionally stores them as plain
text for administrator-assisted recovery.
"""

from database import get_connection, init_db


def list_users():
    init_db()
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, username, pin, created_at
           FROM homehelper_users
           ORDER BY username COLLATE NOCASE"""
    ).fetchall()
    conn.close()

    if not rows:
        print("No Home Helper users are registered.")
        return

    print("ID | User name | PIN | Created")
    print("---|-----------|-----|--------------------")
    for user_id, username, pin, created_at in rows:
        print(f"{user_id} | {username} | {pin} | {created_at}")


if __name__ == "__main__":
    list_users()
