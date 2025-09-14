from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv, find_dotenv

router = APIRouter()

# Load env for dynamic OUTPUT_PATH if provided
load_dotenv(find_dotenv())

class TreeNodeResponse(BaseModel):
    id: str
    path_abs: str
    parent_id: Optional[str]
    name: str
    is_dir: int
    ext: str
    size_bytes: Optional[int]
    when_created: Optional[float]
    when_modified: Optional[float]
    is_synthetic: bool

class TreeDataResponse(BaseModel):
    nodes: Dict[str, TreeNodeResponse]
    adjacency_list: Dict[str, List[str]]
    root_ids: List[str]
    metadata: Dict[str, int]

def resolve_tree_data_path() -> str:
    """
    Resolve the most likely file_tree.json location by trying:
      1) OUTPUT_PATH env (absolute)
      2) repo_root + OUTPUT_PATH (relative)
      3) apps/api/data/file_tree.json (legacy default)
      4) repo_root/data/file_tree.json
    Returns the first path that exists, otherwise the legacy default.
    """
    routes_dir = os.path.dirname(__file__)
    # repo root from routes: ../../../.. (to apps) then .. (to root)
    repo_root = os.path.abspath(os.path.join(routes_dir, "../../../../.."))

    env_output = os.getenv("OUTPUT_PATH")
    candidates: List[str] = []
    if env_output:
        if os.path.isabs(env_output):
            candidates.append(env_output)
        else:
            candidates.append(os.path.normpath(os.path.join(repo_root, env_output)))

    legacy_default = os.path.normpath(os.path.join(routes_dir, "../../../data/file_tree.json"))
    candidates.append(legacy_default)
    candidates.append(os.path.join(repo_root, "data", "file_tree.json"))

    for p in candidates:
        if os.path.exists(p):
            return p
    # Fallback to legacy default
    return legacy_default

@router.get("/tree", response_model=TreeDataResponse)
async def get_tree_structure():
    """
    Get the complete file tree structure from the generated tree data.
    This endpoint serves the tree structure created by the tree.py script.
    """
    try:
        tree_path = resolve_tree_data_path()
        # Check if tree data file exists
        if not os.path.exists(tree_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Tree data not found. Please run the tree generation script first. Looking for: {tree_path}"
            )
        
        # Load and return the tree data
        with open(tree_path, 'r', encoding='utf-8') as f:
            tree_data = json.load(f)
        
        return tree_data
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON in tree data file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading tree data: {str(e)}"
        )

@router.get("/tree/stats")
async def get_tree_stats():
    """
    Get basic statistics about the tree structure.
    """
    try:
        tree_path = resolve_tree_data_path()
        if not os.path.exists(tree_path):
            raise HTTPException(status_code=404, detail="Tree data not found")
        
        with open(tree_path, 'r', encoding='utf-8') as f:
            tree_data = json.load(f)
        
        # Return just the metadata
        return {
            "metadata": tree_data.get("metadata", {}),
            "data_file_path": tree_path,
            "file_exists": True,
            "last_modified": os.path.getmtime(tree_path) if os.path.exists(tree_path) else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading tree stats: {str(e)}"
        )

@router.post("/tree/refresh")
async def refresh_tree():
    """
    Trigger a refresh of the tree data by running the tree generation script.
    Note: This is a placeholder - you might want to implement actual script execution.
    """
    try:
        # For now, just check if the file exists and return its stats
        tree_path = resolve_tree_data_path()
        if os.path.exists(tree_path):
            stat = os.stat(tree_path)
            return {
                "message": "Tree data file found",
                "last_modified": stat.st_mtime,
                "size_bytes": stat.st_size,
                "path": tree_path
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Tree data file not found. Please run tree.py script to generate it."
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking tree data: {str(e)}"
        )
