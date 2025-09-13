import lancedb
import os

# connect to your database (relative to project root)
db_path = os.path.join(os.path.dirname(__file__), "../../../../../data")
db = lancedb.connect(db_path)

# check available tables
print("Available tables:", db.table_names())

# try to open the table (adjust name based on what's available)
if db.table_names():
    table_name = db.table_names()[0]  # use first available table
    table = db.open_table(table_name)
    
    # look at a few rows
    print(f"\nTable '{table_name}' schema:")
    print(table.schema)
    
    print(f"\nFirst 5 rows of '{table_name}':")
    print(table.head(5))
else:
    print("No tables found in database")