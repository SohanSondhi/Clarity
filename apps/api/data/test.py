from FileScraper import LanceDBManager

# Connect to your database with correct path
db_path = "apps/api/data/clarity_db"
db = LanceDBManager(db_path)

db.local_scrape("text", "images", "apps/api/data/testdata")
lancedb = db.get_db()
# Check what tables exist
print(f"Available tables: {lancedb.table_names()}")

# Check if the 'Hello' table exists
for table_name in lancedb.table_names():
    # Open your table
    table = lancedb.open_table(table_name)
    
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
