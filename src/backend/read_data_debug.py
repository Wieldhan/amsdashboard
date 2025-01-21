import sqlite3

# Connect to the database
conn = sqlite3.connect('./database/deposito.db')
cursor = conn.cursor()

# Get list of all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Store table names in a list
table_names = [table[0] for table in tables]

print("All available tables:", table_names)
print("\nDetailed table information:")

for table in tables:
    print(f"\nTable: {table[0]}")
    
    # Get table schema
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print("\nColumns:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
    
    # Show sample data and count rows
    cursor.execute(f"SELECT * FROM {table[0]} LIMIT 10 ")
    rows = cursor.fetchall()
    print("\nSample data (up to 10 rows):")
    for row in rows:
        print(row)
        
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    row_count = cursor.fetchone()[0]
    print(f"\nTotal rows: {row_count}")

conn.close()