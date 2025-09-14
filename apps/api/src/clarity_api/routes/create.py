from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import sys
import subprocess
import time
import lancedb
import pyarrow as pa
from dotenv import load_dotenv, find_dotenv
import shutil

router = APIRouter()

load_dotenv(find_dotenv())

DB_PATH_DEFAULT = "C:/Professional/test-db"
DB_TABLE_DEFAULT = "Hello"


class CreateFolderRequest(BaseModel):
    parent_path: str  # '|' delimited absolute path where folder will be created
    name: str         # folder name only


def normalize_path(path: str) -> str:
    if not path:
        return ""
    s = str(path).replace("\\", "|").replace("/", "|")
    while "||" in s:
        s = s.replace("||", "|")
    return s.strip("|")


def regenerate_tree():
    routes_dir = os.path.dirname(__file__)
    script_path = os.path.normpath(os.path.join(routes_dir, "../../tree_creation.py"))
    script_dir = os.path.dirname(script_path)
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, cwd=script_dir)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Tree regeneration failed: {result.stderr.strip()}")


@router.post("/create-folder")
async def create_folder(req: CreateFolderRequest):
    try:
        parent_norm = normalize_path(req.parent_path)
        folder_name = (req.name or '').strip()
        if not folder_name:
            raise HTTPException(status_code=400, detail="Folder name is required")

        # Build target folder path
        target_path = f"{parent_norm}|{folder_name}" if parent_norm else folder_name

        db_path = os.getenv("DB_PATH", DB_PATH_DEFAULT)
        table_name = os.getenv("DB_TABLE", DB_TABLE_DEFAULT)

        db = lancedb.connect(db_path)
        if table_name not in db.table_names():
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

        table = db.open_table(table_name)
        df = table.to_pandas()

        # Idempotent behavior: if the folder row already exists, treat as success
        if (df['Path'] == target_path).any():
            regenerate_tree()
            return {"success": True, "path": target_path, "existed": True}

        # Create folder on filesystem
        try:
            fs_path = target_path.replace('|', os.sep)
            os.makedirs(fs_path, exist_ok=True)
        except Exception as fs_err:
            print(f"Filesystem mkdir warning: {fs_err}")

        now = float(time.time())

        # New folder entry (mark as directory via File_type)
        new_row = {
            "Path": target_path,
            "Parent": parent_norm,
            "Vector": [],
            "Similarities": [],
            "Name": folder_name,
            "When_Created": now,
            "When_Last_Modified": now,
            "Description": "",
            "File_type": "folder",
        }

        df = df.copy()
        # Use concat for forward-compat with pandas
        import pandas as pd
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

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

        db.create_table(table_name, schema=schema, data=df.to_dict('records'), mode="overwrite")

        regenerate_tree()

        return {"success": True, "path": target_path, "existed": False}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


