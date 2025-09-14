from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import sys
import subprocess
from typing import Optional
from dotenv import load_dotenv, find_dotenv
import logging
import traceback
import lancedb
import pandas as pd


router = APIRouter()
logger = logging.getLogger(__name__)

# Load env for configurable paths
load_dotenv(find_dotenv())


class IndexRequest(BaseModel):
    db_path: Optional[str] = None
    table_name: Optional[str] = None  # base table name (we derive _text and _image)
    root_dir: Optional[str] = None
    output_path: Optional[str] = None


def _run_filescraper_local_scrape(db_path: str, text_table: str, image_table: str, root_dir: str) -> str:
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
        f"db.local_scrape({text_table!r}, {image_table!r}, {root_dir!r}); "
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


def _combine_tables_into_base(db_path: str, base_table: str, text_table: str, image_table: str) -> None:
    """
    Combine rows from text_table and image_table into base_table (overwrite).
    """
    db = lancedb.connect(db_path)
    frames = []
    if text_table in db.table_names():
        frames.append(db.open_table(text_table).to_pandas())
    if image_table in db.table_names():
        frames.append(db.open_table(image_table).to_pandas())
    if not frames:
        raise HTTPException(status_code=500, detail="No data found to combine into base table")

    combined: pd.DataFrame = pd.concat(frames, ignore_index=True)
    # Drop high-dimensional vectors to avoid Arrow FixedSizeList casting issues when
    # mixing different embedding dims (e.g., 384 vs 512) across tables.
    if "Vector" in combined.columns:
        try:
            combined = combined.drop(columns=["Vector"])  # not required for tree builder
        except Exception:
            pass
    expected_cols = [
        "Path",
        "Parent",
        "Vector",
        "Name",
        "When_Created",
        "When_Last_Modified",
        "Description",
        "File_type",
    ]
    for col in expected_cols:
        if col not in combined.columns:
            combined[col] = None

    if base_table in db.table_names():
        db.drop_table(base_table)
    db.create_table(base_table, data=combined)


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
        base_table = req.table_name or os.getenv("DB_TABLE", "Hello")
        output_path = req.output_path or os.getenv("OUTPUT_PATH", "../data/file_tree.json")

        # Pick a reasonable default for root_dir if none provided
        root_dir = req.root_dir or os.getenv("INDEX_ROOT", os.path.expanduser("~"))

        # 1) Scrape content into LanceDB -> text and image tables
        text_table = f"{base_table}_text"
        image_table = f"{base_table}_image"
        stdout = _run_filescraper_local_scrape(db_path, text_table, image_table, root_dir)

        # 1b) Combine into base table for tree builder consumption
        _combine_tables_into_base(db_path, base_table, text_table, image_table)

        # 2) Build tree JSON and return
        _run_tree_builder(db_path, base_table, output_path)

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
        # Log full traceback server-side for easier debugging
        logger.error("Indexing failed with an unexpected error: %s", e)
        logger.debug("%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


