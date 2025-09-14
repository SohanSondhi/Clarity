#!/usr/bin/env python3
"""
Simple debug script to check database contents
"""
import sys
import os

# Add the project src directory to the path
current_dir = os.path.dirname(__file__)
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

import lancedb

def check_database():
    """Check what's in the database"""
    db_path = "C:/Users/sohan/Clarity/Clarity/apps/api/data/clarity_db"
    
    print(f"Checking database: {db_path}")
    
    try:
        db = lancedb.connect(db_path)
        print(f"✅ Database connected successfully")
        
        tables = db.table_names()
        print(f"📋 Available tables: {tables}")
        
        if not tables:
            print("❌ No tables found in database!")
            return
            
        for table_name in tables:
            print(f"\n🔍 Checking table: {table_name}")
            try:
                table = db.open_table(table_name)
                df = table.to_pandas()
                print(f"   📊 Shape: {df.shape}")
                print(f"   📝 Columns: {df.columns.tolist()}")
                
                if df.empty:
                    print(f"   ⚠️  Table '{table_name}' is empty!")
                else:
                    print(f"   ✅ Table has {len(df)} rows")
                    if 'Path' in df.columns:
                        print(f"   📁 Sample paths:")
                        for i, path in enumerate(df['Path'].head(3)):
                            print(f"      {i+1}. {path}")
                    
                    if 'Vector' in df.columns:
                        first_vector = df['Vector'].iloc[0]
                        print(f"   🧮 Vector type: {type(first_vector)}")
                        if hasattr(first_vector, '__len__'):
                            print(f"   📏 Vector length: {len(first_vector)}")
                        
            except Exception as e:
                print(f"   ❌ Error reading table '{table_name}': {e}")
                
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")

if __name__ == "__main__":
    check_database()
