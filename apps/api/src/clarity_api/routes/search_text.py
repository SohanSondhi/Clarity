from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import sys
from typing import List, Dict, Any

# Add the project src directory to the path
routes_dir = os.path.dirname(__file__)
project_src_dir = os.path.normpath(os.path.join(routes_dir, "../../"))
sys.path.insert(0, project_src_dir)

from clarity_api.search.text_search import TextSearcher

router = APIRouter()

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
        # Use provided db_path or default
        db_path = req.db_path or os.getenv("DB_PATH", "C:/Users/sohan/Clarity/Clarity/apps/api/data/clarity_db")
        
        # Initialize searcher
        searcher = TextSearcher(db_path, req.table_name)
        
        # Perform search
        best_match_path = searcher.search(req.query)
        
        # Return the best match as a single result
        results = [{
            "path": best_match_path,
            "score": 1.0,  # You can calculate actual similarity score
            "type": "text"
        }]
        
        return TextSearchResponse(
            query=req.query,
            results=results,
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text search failed: {str(e)}")
