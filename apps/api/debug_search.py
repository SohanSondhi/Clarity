#!/usr/bin/env python3
"""
Debug script to test the search functionality
"""
import sys
import os

# Add the project src directory to the path
current_dir = os.path.dirname(__file__)
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

import lancedb
from clarity_api.search.text_search import TextSearcher
from clarity_api.search.image_search import ImageSearcher

def debug_database():
    """Debug what's in the database"""
    db_path = "C:/Users/sohan/Clarity/Clarity/apps/api/data/clarity_db"
    
    print(f"Connecting to database: {db_path}")
    db = lancedb.connect(db_path)
    
    print(f"Available tables: {db.table_names()}")
    
    for table_name in db.table_names():
        print(f"\n--- Table: {table_name} ---")
        table = db.open_table(table_name)
        df = table.to_pandas()
        print(f"Shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        if not df.empty:
            print("First few rows:")
            print(df.head())
            
            # Check if Vector column exists and has data
            if 'Vector' in df.columns:
                print(f"Vector column type: {type(df['Vector'].iloc[0])}")
                print(f"Vector length: {len(df['Vector'].iloc[0]) if hasattr(df['Vector'].iloc[0], '__len__') else 'N/A'}")
        else:
            print("Table is empty!")

def test_text_search():
    """Test text search"""
    print("\n=== Testing Text Search ===")
    try:
        searcher = TextSearcher("C:/Users/sohan/Clarity/Clarity/apps/api/data/clarity_db", "text")
        result = searcher.search("study guide")
        print(f"Text search result: {result}")
    except Exception as e:
        print(f"Text search error: {e}")

def test_image_search():
    """Test image search"""
    print("\n=== Testing Image Search ===")
    try:
        searcher = ImageSearcher("C:/Users/sohan/Clarity/Clarity/apps/api/data/clarity_db", "images")
        result = searcher.search("C:/Users/sohan/Clarity/Clarity/apps/api/data/testdata/cat.png")
        print(f"Image search result: {result}")
    except Exception as e:
        print(f"Image search error: {e}")

if __name__ == "__main__":
    debug_database()
    test_text_search()
    test_image_search()
