from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import lancedb
import pandas as pd
import os
import json
from typing import Optional, List
from dotenv import load_dotenv, find_dotenv
import shutil

router = APIRouter()

# Load environment configuration
load_dotenv(find_dotenv())

# Use relative path from the API routes directory
def get_default_db_path():
    routes_dir = os.path.dirname(__file__)
    return os.path.normpath(os.path.join(routes_dir, "../../../data/index"))

# Defaults if not set in environment
DB_PATH_DEFAULT = get_default_db_path()
DB_TABLE_DEFAULT = "Hello"

class RenameRequest(BaseModel):
    old_path: str  # Path with | delimiters (e.g., "C:|Professional|oldname.pdf")
    new_name: str  # Just the new name (e.g., "newname.pdf")

class RenameResponse(BaseModel):
    success: bool
    message: str
    old_path: str
    new_path: str
    updated_entries: int

def normalize_path(path):
    """
    Normalize paths by replacing both forward and backward slashes with | delimiter.
    """
    if not path:
        return ""
    
    normalized = str(path).replace("\\", "|").replace("/", "|")
    while "||" in normalized:
        normalized = normalized.replace("||", "|")
    return normalized.strip("|")

def get_parent_path(path: str) -> str:
    """Get parent path from normalized path."""
    parts = path.split("|")
    if len(parts) <= 1:
        return ""
    return "|".join(parts[:-1])

def get_filename_from_path(path: str) -> str:
    """Get filename from normalized path."""
    parts = path.split("|")
    return parts[-1] if parts else ""

def regenerate_tree():
    """Regenerate the tree structure after database changes."""
    try:
        # Import and run the tree generation
        import sys
        import subprocess
        
        # Correct path to tree builder script relative to this file
        # routes/ -> ../.. leads to apps/api/src where tree_creation.py resides
        tree_script_path = os.path.join(os.path.dirname(__file__), "../../tree_creation.py")
        
        # Run tree.py to regenerate the tree structure
        result = subprocess.run([sys.executable, tree_script_path], 
                              capture_output=True, text=True, cwd=os.path.dirname(tree_script_path))
        
        if result.returncode == 0:
            print("Tree regenerated successfully")
            return True
        else:
            print(f"Tree regeneration failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error regenerating tree: {e}")
        return False

@router.post("/rename", response_model=RenameResponse)
async def rename_item(request: RenameRequest, background_tasks: BackgroundTasks):
    
    try:
        # Normalize the old path
        old_path_normalized = normalize_path(request.old_path)
        parent_path = get_parent_path(old_path_normalized)
        
        # Connect to LanceDB (from environment with sensible defaults)
        db_path = os.getenv("DB_PATH", DB_PATH_DEFAULT)
        table_name = os.getenv("DB_TABLE", DB_TABLE_DEFAULT)
        
        try:
            db = lancedb.connect(db_path)
            if table_name not in db.table_names():
                raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
            
            table = db.open_table(table_name)
            df = table.to_pandas()
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
        
        # Track updates
        updated_entries = 0
        
        # Find main item. If it doesn't exist, we may still process as a directory pivot (synthetic folder)
        main_item_mask = df['Path'] == old_path_normalized
        main_items = df[main_item_mask]

        treat_as_directory = False
        if main_items.empty:
            # No explicit row for this path – treat it as a directory path pivot and update all descendants
            treat_as_directory = True
            orig_name = get_filename_from_path(old_path_normalized)
            was_directory = True
        else:
            # Preserve original file extension for files when new_name omits it
            orig_name = str(main_items.iloc[0]['Name'])
            file_type_value = str(main_items.iloc[0].get('File_type', '')).lower()
            was_directory = file_type_value in {'folder', 'dir', 'directory'} or ('.' not in orig_name)

        safe_new_name = request.new_name
        if not was_directory:
            if '.' not in request.new_name and '.' in orig_name:
                orig_ext = orig_name.rsplit('.', 1)[1]
                safe_new_name = f"{request.new_name}.{orig_ext}"

        # Create new path
        if parent_path:
            new_path_normalized = f"{parent_path}|{safe_new_name}"
        else:
            new_path_normalized = safe_new_name

        print(f"Renaming: {old_path_normalized} -> {new_path_normalized}")

        # Perform filesystem rename if possible
        try:
            old_fs = old_path_normalized.replace('|', os.sep)
            new_fs = new_path_normalized.replace('|', os.sep)
            old_fs_abs = old_fs
            new_fs_abs = new_fs
            if os.path.exists(old_fs_abs):
                os.makedirs(os.path.dirname(new_fs_abs), exist_ok=True) if os.path.dirname(new_fs_abs) else None
                os.replace(old_fs_abs, new_fs_abs)
        except Exception as fs_err:
            # Do not fail the whole request on FS error; continue to DB update
            print(f"Filesystem rename warning: {fs_err}")

        # Update the main item if it exists
        if not main_items.empty:
            df.loc[main_item_mask, 'Path'] = new_path_normalized
            df.loc[main_item_mask, 'Name'] = safe_new_name
            updated_entries += len(main_items)

        # If it's a directory (or synthetic directory), update all children
        if was_directory or treat_as_directory:
            # Update all items where Parent starts with the old path
            children_mask = df['Parent'] == old_path_normalized
            df.loc[children_mask, 'Parent'] = new_path_normalized
            updated_entries += children_mask.sum()
            
            # Update all items where Path starts with old_path (subdirectories and files)
            for index, row in df.iterrows():
                current_path = str(row['Path'])
                if current_path.startswith(old_path_normalized + "|"):
                    # Replace the old path prefix with new path
                    new_child_path = current_path.replace(old_path_normalized + "|", new_path_normalized + "|", 1)
                    df.at[index, 'Path'] = new_child_path
                    updated_entries += 1
                
                # Also update Parent paths for deeper nesting
                current_parent = str(row['Parent'])
                if current_parent.startswith(old_path_normalized + "|"):
                    new_parent_path = current_parent.replace(old_path_normalized + "|", new_path_normalized + "|", 1)
                    df.at[index, 'Parent'] = new_parent_path
        
        # Save updated data back to LanceDB
        try:
            # Convert back to records for LanceDB
            updated_data = df.to_dict('records')
            
            # Create new table with same schema
            import pyarrow as pa
            schema = pa.schema([
                pa.field("Path", pa.string()),
                pa.field("Parent", pa.string()),
                pa.field("Vector", pa.list_(pa.float32())),
                pa.field("Similarities", pa.list_(pa.list_(pa.float32()))),
                pa.field("Name", pa.string()),
                pa.field("When_Created", pa.float64()),
                pa.field("When_Last_Modified", pa.float64()),
                pa.field("Description", pa.string()),
                pa.field("File_type", pa.string()),
            ])
            
            # Overwrite the table atomically
            db.create_table(table_name, schema=schema, data=updated_data, mode="overwrite")
            print(f"Updated {updated_entries} entries in database")
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update database: {str(e)}")
        
        # Regenerate tree structure in background
        background_tasks.add_task(regenerate_tree)
        
        return RenameResponse(
            success=True,
            message=f"Successfully renamed '{get_filename_from_path(old_path_normalized)}' to '{safe_new_name}'",
            old_path=old_path_normalized,
            new_path=new_path_normalized,
            updated_entries=updated_entries
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rename operation failed: {str(e)}")

@router.get("/rename/check")
async def check_rename_availability():
    """
    Check if rename functionality is available (database accessible, etc.)
    """
    try:
        db_path = get_default_db_path()
        table_name = "Hello"
        
        db = lancedb.connect(db_path)
        if table_name not in db.table_names():
            return {"available": False, "reason": f"Table '{table_name}' not found"}
        
        table = db.open_table(table_name)
        count = len(table)
        
        return {
            "available": True,
            "database_path": db_path,
            "table_name": table_name,
            "total_entries": count
        }
        
    except Exception as e:
        return {"available": False, "reason": str(e)}
