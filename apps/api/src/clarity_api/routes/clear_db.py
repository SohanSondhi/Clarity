import os
import shutil

# Database path
db_path = "../../data"

def clear_entire_database():
    """Delete the entire database directory"""
    abs_path = os.path.abspath(db_path)
    if os.path.exists(abs_path):
        shutil.rmtree(abs_path)
        print(f"Entire database deleted at: {abs_path}")
        return True
    else:
        print(f"Database doesn't exist at: {abs_path}")
        return False

if __name__ == "__main__":
    print("LanceDB Clear - Delete Entire Database")
    print(f"Database path: {os.path.abspath(db_path)}")
    
    confirm = input("This will delete the ENTIRE database. Are you sure? (y/N): ").strip().lower()
    if confirm == 'y':
        clear_entire_database()
    else:
        print("Cancelled")