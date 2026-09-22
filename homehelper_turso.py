import os
import libsql
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

# The libsql driver requires the libsql:// scheme.
# This replaces 'turso://' with 'libsql://' to ensure compatibility.
RAW_URL = os.getenv("TURSO_DATABASE_URL")
DATABASE_URL = RAW_URL.replace("turso://", "libsql://") if RAW_URL.startswith("turso://") else RAW_URL
AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

def get_connection():
    """Establishes a connection to the Turso Cloud database."""
    return libsql.connect(database=DATABASE_URL, auth_token=AUTH_TOKEN)

def create_table():
    """Creates a 'users' table if it does not already exist."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()
    print("Table 'users' is ready.")

def create_user(name, email):
    """Inserts a new user into the database."""
    conn = get_connection()
    try:
        conn.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
        conn.commit()
        print(f"User '{name}' added successfully.")
    except libsql.IntegrityError:
        print(f"Error: User with email '{email}' already exists.")
    finally:
        conn.close()

def read_users():
    """Fetches and prints all users."""
    conn = get_connection()
    result = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    
    if not result:
        print("No users found.")
    else:
        print("\n--- All Users ---")
        for row in result:
            print(row)
        print("-----------------\n")

def update_user(user_id, new_email):
    """Updates a user's email by their ID."""
    conn = get_connection()
    conn.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id))
    conn.commit()
    # Check if any row was actually updated
    if conn.execute("SELECT changes()").fetchone()[0] > 0:
        print(f"User ID {user_id} updated.")
    else:
        print(f"User ID {user_id} not found.")
    conn.close()

def delete_user(user_id):
    """Deletes a user by their ID."""
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    if conn.execute("SELECT changes()").fetchone()[0] > 0:
        print(f"User ID {user_id} deleted.")
    else:
        print(f"User ID {user_id} not found.")
    conn.close()

# --- Main execution ---
if __name__ == "__main__":
    # 1. Setup table
    create_table()

    # 2. CREATE: Insert some users
    create_user("Alice", "alice@example.com")
    create_user("Bob", "bob@example.com")

    # 3. READ: View all users
    read_users()

    # 4. UPDATE: Change Bob's email
    update_user(2, "bob.new@example.com")
    read_users() # Verify update

    # 5. DELETE: Remove Alice
    delete_user(1)
    read_users() # Verify deletion