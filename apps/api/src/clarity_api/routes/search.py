from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import lancedb
import pandas as pd
from typing import List
from .directory import FileSystemItem, get_file_icon
from datetime import datetime
import os

router = APIRouter()

class SearchRequest(BaseModel):
    query: str

class SearchResult(BaseModel):
    query: str
    items: List[FileSystemItem]
    totalResults: int

@router.post("/search")
async def search_files(request: SearchRequest):
    """Search files using semantic similarity"""
    try:
        # Connect to LanceDB
        db = lancedb.connect("data/index/image_db.json")
        table = db.open_table("db")
        
        # Perform semantic search
        results = table.search(request.query).limit(50).to_pandas()
        
        if results.empty:
            return SearchResult(
                query=request.query,
                items=[],
                totalResults=0
            )
        
        # Convert to FileSystemItem format
        items = []
        for _, row in results.iterrows():
            file_type = row['File_type'] if pd.notna(row['File_type']) else ''
            
            # Get file size
            try:
                size = os.path.getsize(row['Path']) if os.path.exists(row['Path']) else 0
            except:
                size = 0
            
            # Parse tags
            tags = []
            if pd.notna(row['Tags']) and row['Tags']:
                try:
                    if isinstance(row['Tags'], str):
                        tags = eval(row['Tags']) if row['Tags'].startswith('[') else [row['Tags']]
                    elif isinstance(row['Tags'], list):
                        tags = row['Tags']
                except:
                    tags = []
            
            item = FileSystemItem(
                name=row['Name'],
                path=row['Path'],
                type='file',
                size=size,
                dateModified=datetime.fromtimestamp(row['When_Last_Modified']),
                extension=file_type,
                icon=get_file_icon(file_type),
                description=row['Description'] if pd.notna(row['Description']) else None,
                tags=[tag[0] if isinstance(tag, tuple) else str(tag) for tag in tags]
            )
            items.append(item)
        
        return SearchResult(
            query=request.query,
            items=items,
            totalResults=len(items)
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Database not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.post("/search/semantic")
async def semantic_search(request: SearchRequest):
    """Advanced semantic search with better ranking"""
    return await search_files(request)

@router.post("/search/text")
async def text_search(request: SearchRequest):
    """Text-based search in file names and descriptions"""
    try:
        # Connect to LanceDB
        db = lancedb.connect("data/index/image_db.json")
        table = db.open_table("db")
        
        # Read all data and filter
        df = table.to_pandas()
        
        if df.empty:
            return SearchResult(query=request.query, items=[], totalResults=0)
        
        # Text search in names and descriptions
        query_lower = request.query.lower()
        mask = (
            df['Name'].str.lower().str.contains(query_lower, na=False) |
            df['Description'].str.lower().str.contains(query_lower, na=False)
        )
        
        filtered_df = df[mask]
        
        # Convert to FileSystemItem format
        items = []
        for _, row in filtered_df.iterrows():
            file_type = row['File_type'] if pd.notna(row['File_type']) else ''
            
            try:
                size = os.path.getsize(row['Path']) if os.path.exists(row['Path']) else 0
            except:
                size = 0
            
            tags = []
            if pd.notna(row['Tags']) and row['Tags']:
                try:
                    if isinstance(row['Tags'], str):
                        tags = eval(row['Tags']) if row['Tags'].startswith('[') else [row['Tags']]
                    elif isinstance(row['Tags'], list):
                        tags = row['Tags']
                except:
                    tags = []
            
            item = FileSystemItem(
                name=row['Name'],
                path=row['Path'],
                type='file',
                size=size,
                dateModified=datetime.fromtimestamp(row['When_Last_Modified']),
                extension=file_type,
                icon=get_file_icon(file_type),
                description=row['Description'] if pd.notna(row['Description']) else None,
                tags=[tag[0] if isinstance(tag, tuple) else str(tag) for tag in tags]
            )
            items.append(item)
        
        return SearchResult(
            query=request.query,
            items=items,
            totalResults=len(items)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text search error: {str(e)}")
