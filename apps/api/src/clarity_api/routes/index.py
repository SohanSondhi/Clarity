from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import sys
import subprocess
from typing import Optional
from dotenv import load_dotenv, find_dotenv


router = APIRouter()

# Load env for configurable paths
load_dotenv(find_dotenv())


class IndexRequest(BaseModel):
    db_path: Optional[str] = None
    table_name: Optional[str] = None
    root_dir: Optional[str] = None
    output_path: Optional[str] = None


def _run_filescraper_local_scrape(db_path: str, table_name: str, root_dir: str) -> str:
    """
    Calls FileScraper.py's LanceDBManager.local_scrape via a subprocess to avoid import side-effects.
    Expects FileScraper.py to be resolvable relative to this routes module.
    """
    routes_dir = os.path.dirname(__file__)
    project_src_dir = os.path.normpath(os.path.join(routes_dir, "../../"))
    script_path = os.path.normpath(os.path.join(project_src_dir, "FileScraper.py"))

    if not os.path.exists(script_path):
        raise HTTPException(status_code=500, detail=f"FileScraper.py not found at {script_path}")

    # We execute a small python snippet that imports FileScraper.py and runs local_scrape
    code = (
        "import sys, os; "
        f"sys.path.insert(0, {project_src_dir!r}); "
        "from FileScraper import LanceDBManager; "
        f"db=LanceDBManager({db_path!r}); "
        f"db.local_scrape({table_name!r}, {root_dir!r}); "
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=project_src_dir,
        env={**os.environ},
    )

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"File scrape failed: {result.stderr.strip()}")
    return result.stdout or ""


def _run_tree_builder(db_path: str, table_name: str, output_path: str):
    routes_dir = os.path.dirname(__file__)
    project_src_dir = os.path.normpath(os.path.join(routes_dir, "../../"))
    script_path = os.path.normpath(os.path.join(project_src_dir, "tree_creation.py"))
    script_dir = os.path.dirname(script_path)

    if not os.path.exists(script_path):
        raise HTTPException(status_code=500, detail=f"tree_creation.py not found at {script_path}")

    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True,
        cwd=script_dir,
        env={
            **os.environ,
            "DB_PATH": db_path,
            "DB_TABLE": table_name,
            "OUTPUT_PATH": output_path,
        },
    )

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Tree build failed: {result.stderr.strip()}")


@router.post("/index")
async def run_full_index(req: IndexRequest):
    """
    Run indexing pipeline:
      1) Scrape files into LanceDB (create/overwrite table)
      2) Build tree JSON from LanceDB and return the payload

    Body overrides are optional; environment defaults are used otherwise.
    """
    try:
        # Defaults aligned with tree_creation.py and refresh.py
        db_path = req.db_path or os.getenv("DB_PATH", "C:/Professional/test-db")
        table_name = req.table_name or os.getenv("DB_TABLE", "Hello")
        output_path = req.output_path or os.getenv("OUTPUT_PATH", "../data/file_tree.json")

        # Pick a reasonable default for root_dir if none provided
        root_dir = req.root_dir or os.getenv("INDEX_ROOT", os.path.expanduser("~"))

        # 1) Scrape content into LanceDB
        stdout = _run_filescraper_local_scrape(db_path, table_name, root_dir)

        # 2) Build tree JSON and return
        _run_tree_builder(db_path, table_name, output_path)

        # After successful build, read JSON and return
        project_src_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../"))
        output_abs = os.path.normpath(os.path.join(project_src_dir, output_path))
        if not os.path.exists(output_abs):
            raise HTTPException(status_code=500, detail=f"Tree output not found at {output_abs}")

        with open(output_abs, "r", encoding="utf-8") as f:
            import json
            tree = json.load(f)

        # Attach a lightweight log extract of processed files
        log_lines = []
        for line in (stdout or "").splitlines():
            # Capture lines indicating a file was processed
            if "Inserted data for" in line or "Processing" in line:
                log_lines.append(line.strip())
            # Keep size reasonable
            if len(log_lines) >= 200:
                break

        # Non-invasive: include logs at top-level without changing required schema fields
        if isinstance(tree, dict):
            tree["index_logs"] = log_lines

        return tree

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


