import lancedb
import pandas as pd
import os

# Connect to your database with correct path
db_path = "../../data/index/image_db.json"
print(f"Connecting to database at: {os.path.abspath(db_path)}")

db = lancedb.connect(db_path)

# Check what tables exist
print(f"Available tables: {db.table_names()}")

# Check if the 'db' table exists
if "db" in db.table_names():
    # Open your table
    table = db.open_table("db")
    
    # Read all data
    df = table.to_pandas()
    print(f"Table shape: {df.shape}")
    print(df.head())
    
    # Count total rows
    print(f"Total entries: {len(table)}")
    
    # Get schema info
    print(f"Schema: {table.schema}")
    
    # Show column names
    print(f"Columns: {df.columns.tolist()}")
else:
    print("Table 'db' does not exist. You may need to run the FileScraper first to create the table.")
    print("The database exists but is empty or the table hasn't been created yet.")