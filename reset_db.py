import sqlite3

# Connect to the database
conn = sqlite3.connect('parking.db')

# Read and execute the SQL script
with open('init_db.sql', 'r') as f:
    sql = f.read()
    conn.executescript(sql)

# Commit changes and close connection
conn.commit()
conn.close()
