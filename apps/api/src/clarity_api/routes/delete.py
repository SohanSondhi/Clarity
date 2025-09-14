from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import sys
import subprocess
import lancedb
import pandas as pd
from typing import List
from dotenv import load_dotenv, find_dotenv
import shutil

router = APIRouter()

load_dotenv(find_dotenv())

# Use relative path from the API routes directory
def get_default_db_path():
    routes_dir = os.path.dirname(__file__)
    return os.path.normpath(os.path.join(routes_dir, "../../../data/index"))

DB_PATH_DEFAULT = get_default_db_path()
DB_TABLE_DEFAULT = "Hello"


class DeleteRequest(BaseModel):
    path: str  # Original path using '|' delimiters (e.g., "C:|Folder|file.txt")
    recursive: bool = True  # If True and target is dir, delete all descendants


def normalize_path(path: str) -> str:
    if not path:
        return ""
    s = str(path).replace("\\", "|").replace("/", "|")
    while "||" in s:
        s = s.replace("||", "|")
    return s.strip("|")


def regenerate_tree():
    try:
        routes_dir = os.path.dirname(__file__)
        script_path = os.path.normpath(os.path.join(routes_dir, "../../tree_creation.py"))
        script_dir = os.path.dirname(script_path)

        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=script_dir,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tree regeneration failed: {str(e)}")


@router.post("/delete")
async def delete_item(req: DeleteRequest):
    try:
        target = normalize_path(req.path)

        db_path = os.getenv("DB_PATH", DB_PATH_DEFAULT)
        table_name = os.getenv("DB_TABLE", DB_TABLE_DEFAULT)

        db = lancedb.connect(db_path)
        if table_name not in db.table_names():
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

        table = db.open_table(table_name)
        df = table.to_pandas()

        # Determine deletion set
        to_delete_mask = (df['Path'] == target)

        # If recursive or target appears to be a directory (no extension), delete descendants
        is_dir_guess = ('.' not in target.split('|')[-1])
        if req.recursive or is_dir_guess:
            to_delete_mask |= df['Path'].str.startswith(target + '|')

        deleted_count = int(to_delete_mask.sum())
        if deleted_count == 0:
            # Also consider items whose Parent is the target (in case of synthetic dir)
            to_delete_mask |= (df['Parent'] == target)
            deleted_count = int(to_delete_mask.sum())

        if deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"No entries found for path: {target}")

        # Attempt filesystem deletion
        try:
            fs_path = target.replace('|', os.sep)
            if os.path.exists(fs_path):
                if os.path.isdir(fs_path):
                    if req.recursive:
                        shutil.rmtree(fs_path)
                    else:
                        os.rmdir(fs_path)
                else:
                    os.remove(fs_path)
        except Exception as fs_err:
            print(f"Filesystem delete warning: {fs_err}")

        # Drop rows and write back
        remaining = df.loc[~to_delete_mask].copy()

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

        db.create_table(table_name, schema=schema, data=remaining.to_dict('records'), mode="overwrite")

        # Regenerate tree
        regenerate_tree()

        return {"success": True, "deleted": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


