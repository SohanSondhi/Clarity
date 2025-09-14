from fastapi import APIRouter, HTTPException
import os
import sys
import json
import subprocess
from dotenv import load_dotenv, find_dotenv

router = APIRouter()

# Load environment variables
load_dotenv(find_dotenv())

# Use relative path from the API routes directory
def get_default_db_path():
    routes_dir = os.path.dirname(__file__)
    return os.path.normpath(os.path.join(routes_dir, "../../../data/index"))

# Defaults (matched with tree_creation.py)
DB_PATH_DEFAULT = get_default_db_path()
DB_TABLE_DEFAULT = "Hello"
OUTPUT_PATH_DEFAULT = "../data/file_tree.json"


def _build_tree_and_read_output():
    """
    Runs the tree builder script and returns the parsed JSON payload.
    """
    # Resolve tree_creation.py path
    routes_dir = os.path.dirname(__file__)
    script_path = os.path.normpath(os.path.join(routes_dir, "../../tree_creation.py"))
    script_dir = os.path.dirname(script_path)

    # Execute the script with current Python
    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True,
        cwd=script_dir,
        env={
            **os.environ,
            "DB_PATH": os.getenv("DB_PATH", DB_PATH_DEFAULT),
            "DB_TABLE": os.getenv("DB_TABLE", DB_TABLE_DEFAULT),
            "OUTPUT_PATH": os.getenv("OUTPUT_PATH", OUTPUT_PATH_DEFAULT),
        },
    )

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Tree build failed: {result.stderr.strip()}")

    # Locate the output file and return its JSON
    output_path_env = os.getenv("OUTPUT_PATH", OUTPUT_PATH_DEFAULT)
    output_abs = os.path.normpath(os.path.join(script_dir, output_path_env))

    if not os.path.exists(output_abs):
        raise HTTPException(status_code=500, detail=f"Tree output not found at {output_abs}")

    with open(output_abs, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post("/refresh")
async def refresh_tree():
    """
    Rebuilds the tree JSON from LanceDB and returns the updated payload.
    """
    try:
        payload = _build_tree_and_read_output()
        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


