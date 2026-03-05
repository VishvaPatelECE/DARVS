import sqlite3

conn = sqlite3.connect("faces.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM users")

conn.commit()
conn.close()

print("All users removed from database.")