from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import lancedb
import pandas as pd
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

router = APIRouter()

class DirectoryRequest(BaseModel):
    path: str

class FileSystemItem(BaseModel):
    name: str
    path: str
    type: str  # 'file' or 'folder'
    size: int
    dateModified: datetime
    extension: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

def get_file_icon(file_type: str) -> str:
    """Get emoji icon for file type"""
    icons = {
        '.pdf': '📄', '.docx': '📄', '.doc': '📄', '.txt': '📝',
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
        '.mp4': '🎬', '.avi': '🎬', '.mov': '🎬',
        '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
        '.zip': '📦', '.rar': '📦', '.7z': '📦',
        '.py': '🐍', '.js': '💛', '.html': '🌐', '.css': '🎨',
        '.exe': '⚙️', '.msi': '⚙️'
    }
    return icons.get(file_type.lower(), '📄')

def build_directory_tree(df: pd.DataFrame, requested_path: str) -> List[FileSystemItem]:
    """Build directory tree from flat database records"""
    items = []
    
    # Normalize requested path
    requested_path = os.path.normpath(requested_path)
    if requested_path == '.':
        requested_path = ''
    
    # Get all unique directories to create folder structure
    all_dirs = set()
    
    for _, row in df.iterrows():
        file_path = os.path.normpath(row['Path'])
        parent_path = os.path.normpath(row['Parent'])
        
        # Add all parent directories
        current_dir = parent_path
        while current_dir and current_dir != os.path.dirname(current_dir):
            all_dirs.add(current_dir)
            current_dir = os.path.dirname(current_dir)
    
    # If requesting root or empty, show top-level directories
    if not requested_path or requested_path == os.sep:
        # Get top-level directories
        top_dirs = set()
        for dir_path in all_dirs:
            parts = dir_path.split(os.sep)
            if len(parts) > 1:
                top_dirs.add(parts[0] + os.sep if parts[0] else os.sep + parts[1])
        
        for dir_path in sorted(top_dirs):
            items.append(FileSystemItem(
                name=os.path.basename(dir_path) or dir_path,
                path=dir_path,
                type='folder',
                size=0,
                dateModified=datetime.now(),
                icon='📁'
            ))
    else:
        # Get immediate children of requested path
        immediate_dirs = set()
        immediate_files = []
        
        # Find subdirectories
        for dir_path in all_dirs:
            if dir_path.startswith(requested_path + os.sep):
                relative_path = dir_path[len(requested_path) + 1:]
                if os.sep not in relative_path:  # Immediate child
                    immediate_dirs.add(dir_path)
        
        # Add subdirectories
        for dir_path in sorted(immediate_dirs):
            items.append(FileSystemItem(
                name=os.path.basename(dir_path),
                path=dir_path,
                type='folder',
                size=0,
                dateModified=datetime.now(),
                icon='📁'
            ))
        
        # Find files in this directory
        for _, row in df.iterrows():
            parent_path = os.path.normpath(row['Parent'])
            if parent_path == requested_path:
                file_path = os.path.normpath(row['Path'])
                file_type = row['File_type'] if pd.notna(row['File_type']) else ''
                
                # Get file size (default to 0 if not available)
                try:
                    size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                except:
                    size = 0
                
                # Parse tags
                tags = []
                if pd.notna(row['Tags']) and row['Tags']:
                    try:
                        # Tags might be stored as string representation of list
                        if isinstance(row['Tags'], str):
                            tags = eval(row['Tags']) if row['Tags'].startswith('[') else [row['Tags']]
                        elif isinstance(row['Tags'], list):
                            tags = row['Tags']
                    except:
                        tags = []
                
                items.append(FileSystemItem(
                    name=row['Name'],
                    path=file_path,
                    type='file',
                    size=size,
                    dateModified=datetime.fromtimestamp(row['When_Last_Modified']),
                    extension=file_type,
                    icon=get_file_icon(file_type),
                    description=row['Description'] if pd.notna(row['Description']) else None,
                    tags=[tag[0] if isinstance(tag, tuple) else str(tag) for tag in tags]
                ))
    
    return items

@router.post("/directory")
async def get_directory_contents(request: DirectoryRequest):
    """Get directory contents from scraped files database"""
    try:
        # Connect to LanceDB
        db = lancedb.connect("data/index/image_db.json")
        table = db.open_table("db")
        
        # Read all data
        df = table.to_pandas()
        
        if df.empty:
            return []
        
        # Build directory tree for requested path
        items = build_directory_tree(df, request.path)
        
        return [item.dict() for item in items]
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Database not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading directory: {str(e)}")

@router.get("/drives")
async def get_drives():
    """Get available drives (for Windows compatibility)"""
    # This is a simplified version - you might want to detect actual drives
    return [
        {
            "name": "Local Disk (C:)",
            "path": "C:/",
            "label": "Windows", 
            "totalSpace": 500000000000,
            "freeSpace": 250000000000,
            "type": "NTFS"
        }
    ]

@router.get("/quick-access") 
async def get_quick_access():
    """Get quick access items"""
    try:
        # Connect to LanceDB to get common directories
        db = lancedb.connect("data/index/image_db.json")
        table = db.open_table("db")
        df = table.to_pandas()
        
        # Get most common parent directories
        if not df.empty:
            common_dirs = df['Parent'].value_counts().head(4).index.tolist()
            quick_access = []
            
            for dir_path in common_dirs:
                dir_name = os.path.basename(dir_path) or dir_path
                quick_access.append({
                    "name": dir_name,
                    "path": dir_path,
                    "icon": "📁"
                })
            
            return quick_access
            
    except Exception as e:
        print(f"Error getting quick access: {e}")
    
    # Fallback to default items
    return [
        {"name": "Documents", "path": "C:/Users/User/Documents", "icon": "📁"},
        {"name": "Downloads", "path": "C:/Users/User/Downloads", "icon": "⬇️"},
        {"name": "Pictures", "path": "C:/Users/User/Pictures", "icon": "🖼️"},
        {"name": "Desktop", "path": "C:/Users/User/Desktop", "icon": "🖥️"}
    ]
