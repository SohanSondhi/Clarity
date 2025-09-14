from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import sys
import json
from typing import List, Dict, Any

# Add the project src directory to the path
routes_dir = os.path.dirname(__file__)
project_src_dir = os.path.normpath(os.path.join(routes_dir, "../../"))
sys.path.insert(0, project_src_dir)

from clarity_api.search.text_search import TextSearcher

router = APIRouter()

def get_tree_data():
    """Load the current tree structure to validate search results"""
    try:
        # Use the same logic as tree.py to find the tree file
        tree_candidates = [
            os.path.normpath(os.path.join(routes_dir, "../../../data/file_tree.json")),
            os.path.normpath(os.path.join(routes_dir, "../../../../data/file_tree.json"))
        ]
        
        for tree_path in tree_candidates:
            if os.path.exists(tree_path):
                with open(tree_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        return None
    except Exception:
        return None

def normalize_path_for_comparison(path: str) -> str:
    """Normalize path for comparison with tree data"""
    return path.replace("\\", "|").replace("/", "|")

class TextSearchRequest(BaseModel):
    query: str
    db_path: str = None
    table_name: str = "text"  # Default table name

class TextSearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_results: int

@router.post("/search-text", response_model=TextSearchResponse)
async def search_text(req: TextSearchRequest):
    """
    Search for text content using semantic similarity.
    """
    try:
        # Use provided db_path or default to relative path
        if req.db_path:
            db_path = req.db_path
        else:
            # Use relative path from the API routes directory
            routes_dir = os.path.dirname(__file__)
            # Go up to api/src, then down to data
            default_db_path = os.path.normpath(os.path.join(routes_dir, "../../../data/index"))
            db_path = os.getenv("DB_PATH", default_db_path)
        
        # Check if database exists and has the required table
        import lancedb
        try:
            db = lancedb.connect(db_path)
            available_tables = db.table_names()
            
            if req.table_name not in available_tables:
                # Return empty results if table doesn't exist
                return TextSearchResponse(
                    query=req.query,
                    results=[],
                    total_results=0
                )
                
        except Exception as db_error:
            # Database connection failed
            return TextSearchResponse(
                query=req.query,
                results=[],
                total_results=0
            )
        
        # Initialize searcher
        searcher = TextSearcher(db_path, req.table_name)
        
        # Perform search
        best_match_path = searcher.search(req.query)
        
        # Load tree data to validate and enrich results
        tree_data = get_tree_data()
        results = []
        
        if best_match_path:
            normalized_path = normalize_path_for_comparison(best_match_path)
            
            # Try to find the file in the tree structure
            file_info = None
            if tree_data and "nodes" in tree_data:
                for node_id, node in tree_data["nodes"].items():
                    if node.get("path_abs") == normalized_path:
                        file_info = node
                        break
            
            result_item = {
                "path": best_match_path,
                "normalized_path": normalized_path,
                "score": 1.0,  # You can calculate actual similarity score
                "type": "text"
            }
            
            # Add tree metadata if found
            if file_info:
                result_item.update({
                    "name": file_info.get("name", ""),
                    "size_bytes": file_info.get("size_bytes"),
                    "ext": file_info.get("ext", ""),
                    "is_dir": file_info.get("is_dir", 0),
                    "in_tree": True
                })
            else:
                result_item["in_tree"] = False
                
            results.append(result_item)
        
        return TextSearchResponse(
            query=req.query,
            results=results,
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text search failed: {str(e)}")
