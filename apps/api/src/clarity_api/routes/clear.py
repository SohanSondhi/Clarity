from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import shutil
from typing import Optional
from dotenv import load_dotenv, find_dotenv


router = APIRouter()

load_dotenv(find_dotenv())


class ClearRequest(BaseModel):
    db_path: Optional[str] = None
    table_name: Optional[str] = None  # Not strictly needed to clear the dir
    output_path: Optional[str] = None  # Tree JSON relative to project src by default


def _resolve_project_src_dir() -> str:
    routes_dir = os.path.dirname(__file__)
    return os.path.normpath(os.path.join(routes_dir, "../../"))


def _remove_path_safely(path: str) -> None:
    try:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.isfile(path):
            os.remove(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove {path}: {str(e)}")


@router.post("/clear")
async def clear_data(req: ClearRequest):
    """
    Clears the LanceDB database directory and deletes the generated tree JSON file.
    Defaults:
      - DB_PATH from env or relative path to data/index
      - OUTPUT_PATH from env or "../data/file_tree.json"
    """
    try:
        project_src_dir = _resolve_project_src_dir()
        if req.db_path:
            db_path = req.db_path
        else:
            # Use relative path from the API routes directory
            routes_dir = os.path.dirname(__file__)
            default_db_path = os.path.normpath(os.path.join(routes_dir, "../../../data/index"))
            db_path = os.getenv("DB_PATH", default_db_path)
        output_path = req.output_path or os.getenv("OUTPUT_PATH", "../data/file_tree.json")

        # Clear LanceDB directory
        db_abs = os.path.abspath(db_path)
        if os.path.exists(db_abs):
            _remove_path_safely(db_abs)

        # Remove tree JSON file (path relative to project src)
        tree_abs = os.path.normpath(os.path.join(project_src_dir, output_path))
        if os.path.exists(tree_abs):
            _remove_path_safely(tree_abs)

        return {
            "ok": True,
            "cleared_db_path": db_abs,
            "cleared_tree_path": tree_abs,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


