import sqlite3
from datetime import datetime

DB_FILE = "faces.db"


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def add_user(name):

    init_db()   # ← ensures table always exists

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (name, created_at) VALUES (?, ?)",
            (name, datetime.utcnow().isoformat())
        )

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def delete_user(name):

    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE name=?", (name,))

    conn.commit()
    conn.close()