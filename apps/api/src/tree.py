#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

import lancedb
import pandas as pd


# ----------------------------- Utilities ----------------------------- #

def md5_hexdigest(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def human_is_folder_label(value: Optional[str]) -> bool:
    if not isinstance(value, str):
        return False
    v = value.strip().lower()
    return v in {"folder", "dir", "directory"}


# ------------------------ File Tree Builder -------------------------- #

class FileTreeBuilder:
    """
    Builds a Windows-friendly tree from a LanceDB table of file metadata.
    """

    def __init__(self, db_path: str, table_name: str):
        self.db_path = db_path
        self.table_name = table_name
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.adjacency_list: Dict[str, List[str]] = {}

    # -------- Path normalization (critical) -------- #

    def normalize_path(self, raw: str) -> str:
        """
        Simple path normalization using | as delimiter.
        Convert backslashes and forward slashes to | for consistent parsing.
        """
        if raw is None:
            return ""
        s = str(raw).strip()
        if not s:
            return ""

        # Replace both backslashes and forward slashes with |
        normalized = s.replace("\\", "|").replace("/", "|")
        
        # Remove any double pipes that might occur
        while "||" in normalized:
            normalized = normalized.replace("||", "|")
        
        # Remove leading/trailing pipes
        normalized = normalized.strip("|")
        
        return normalized

    def normalized_parent(self, path_abs: str) -> str:
        """
        Return the parent path using | delimiter.
        Empty string means "no parent" (root).
        """
        if not path_abs:
            return ""
        
        # Split by | and remove the last part to get parent
        parts = path_abs.split("|")
        if len(parts) <= 1:
            return ""  # No parent (this is root)
        
        # Join all parts except the last one
        parent_parts = parts[:-1]
        return "|".join(parent_parts)

    def generate_id(self, canonical_path_abs: str) -> str:
        """
        Stable ID derived from lowercased canonical path (case-insensitive like Windows).
        """
        return md5_hexdigest(canonical_path_abs.lower())

    # ---------------- LanceDB I/O ---------------- #

    def load_table(self) -> pd.DataFrame:
        print(f"   Connecting to database: {self.db_path}")
        db = lancedb.connect(self.db_path)
        
        print(f"   Available tables: {db.table_names()}")
        if self.table_name not in db.table_names():
            raise ValueError(f"Table '{self.table_name}' not found in LanceDB at {self.db_path}")
        
        print(f"   Opening table: {self.table_name}")
        table = db.open_table(self.table_name)
        df = table.to_pandas()
        print(f"   Loaded {len(df)} rows from table")

        # Ensure expected columns exist; create empties if missing
        print(f"   Original columns: {list(df.columns)}")
        for col in ("Path", "Parent", "Name", "File_type", "When_Created", "When_Last_Modified"):
            if col not in df.columns:
                df[col] = None
                print(f"   Added missing column: {col}")

        # Normalize columns (strings)
        df["Path"] = df["Path"].astype(str)
        df["Parent"] = df["Parent"].astype(str)
        df["Name"] = df["Name"].astype(str)
        
        print(f"   Data preprocessing complete")
        return df

    # ---------------- Build logic ---------------- #

    def is_directory_row(self, path_norm: str, file_type: Optional[str], parent_set: Set[str]) -> bool:
        """
        Decide if a given path should be treated as a directory.
        Priority:
          1) Explicit File_type label (folder/dir/directory)
          2) Path appears as a Parent somewhere
          3) Heuristic: no file extension → likely a directory
        """
        if human_is_folder_label(file_type):
            return True
        if path_norm in parent_set:
            return True
        # Extension heuristic: if the last part has no extension, likely a directory
        parts = path_norm.split("|")
        if parts:
            last_part = parts[-1]
            return "." not in last_part
        return False

    def create_node(
        self,
        path_abs: str,
        parent_abs: str,
        *,
        name: Optional[str],
        is_dir: bool,
        file_type: Optional[str],
        when_created: Optional[float],
        when_modified: Optional[float],
        is_synthetic: bool,
        size_bytes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a node record. `path_abs` and `parent_abs` must already be canonical (normalize_path).
        """
        # Fallback name from path using | delimiter
        if name and name.strip():
            disp_name = name
        else:
            # Get the last part of the path (after last |)
            parts = path_abs.split("|")
            disp_name = parts[-1] if parts else path_abs
        
        # Extract extension from display name
        if is_dir:
            ext = ""
        else:
            # Find the last dot in the name
            if "." in disp_name:
                ext = disp_name.split(".")[-1].lower()
            else:
                ext = ""

        node_id = self.generate_id(path_abs)
        parent_id = self.generate_id(parent_abs) if parent_abs else None

        return {
            "id": node_id,
            "path_abs": path_abs,
            "parent_id": parent_id,
            "name": disp_name,
            "is_dir": 1 if is_dir else 0,
            "ext": ext,
            "size_bytes": size_bytes,
            "when_created": float(when_created) if when_created else None,
            "when_modified": float(when_modified) if when_modified else None,
            "is_synthetic": bool(is_synthetic),
        }

    def build(self) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[str]], List[str], Dict[str, Any]]:
        """
        Build the complete tree:
          - synthesize any missing directories
          - add file/dir nodes from the table
          - build adjacency (sorted, deduped)
        Returns: nodes, adjacency_list, root_ids, metadata
        """
        print("Step 1: Loading and preprocessing data...")
        df = self.load_table()

        print("Step 2: Normalizing paths...")
        # Canonicalize Path and Parent
        df["Path_norm"] = df["Path"].map(self.normalize_path)
        # If Parent empty, we'll derive from Path later per row
        df["Parent_norm"] = df["Parent"].map(self.normalize_path)

        print(f"   Sample normalized paths:")
        for i, (orig, norm) in enumerate(zip(df["Path"].head(3), df["Path_norm"].head(3))):
            print(f"     {orig} -> {norm}")

        # Sets for quick checks
        file_paths: Set[str] = set(df["Path_norm"])
        parent_set: Set[str] = set(x for x in df["Parent_norm"] if x)
        print(f"   Found {len(file_paths)} file paths")
        print(f"   Found {len(parent_set)} parent paths")

        print("Step 3: Finding required directories...")
        # Also make sure every ancestor directory of every file is represented
        required_dirs: Set[str] = set()
        for p in file_paths:
            cur = self.normalized_parent(p)
            while cur:
                required_dirs.add(cur)
                cur = self.normalized_parent(cur)
        required_dirs |= parent_set  # anything that was listed as a Parent must exist as a dir
        print(f"   Found {len(required_dirs)} required directories")

        print("Step 4: Creating synthetic directory nodes...")
        # Synthesize directory nodes (including roots not explicitly present)
        synthetic_dir_ids: Set[str] = set()
        for i, d in enumerate(sorted(required_dirs)):
            if i < 5:  # Show first 5
                print(f"   Creating synthetic dir: {d}")
            parent_d = self.normalized_parent(d)
            node = self.create_node(
                path_abs=d,
                parent_abs=parent_d,
                name=None,
                is_dir=True,
                file_type="folder",
                when_created=None,
                when_modified=None,
                is_synthetic=True,
            )
            self.nodes[node["id"]] = node
            synthetic_dir_ids.add(node["id"])
        print(f"   Created {len(synthetic_dir_ids)} synthetic directories")

        print("Step 5: Processing real files and directories...")
        # Add real rows (files and real dirs)
        files_processed = 0
        dirs_processed = 0
        for row in df.itertuples(index=False):
            path_norm: str = getattr(row, "Path_norm")
            print(f"   Processing row: {path_norm}")
            if not path_norm:
                continue

            # Prefer provided Parent; otherwise derive from Path
            parent_norm_raw = getattr(row, "Parent_norm")
            parent_norm = parent_norm_raw if parent_norm_raw else self.normalized_parent(path_norm)

            name = getattr(row, "Name", None)
            file_type = getattr(row, "File_type", None)
            when_created = getattr(row, "When_Created", None)
            when_modified = getattr(row, "When_Last_Modified", None)

            # Decide if this row is a directory
            is_dir = self.is_directory_row(path_norm, file_type, parent_set)

            if is_dir:
                dirs_processed += 1
            else:
                files_processed += 1
            
            if files_processed + dirs_processed <= 5:  # Show first 5
                print(f"   Processing {'DIR' if is_dir else 'FILE'}: {name} -> {path_norm}")

            node = self.create_node(
                path_abs=path_norm,
                parent_abs=parent_norm,
                name=name,
                is_dir=is_dir,
                file_type=file_type,
                when_created=when_created,
                when_modified=when_modified,
                is_synthetic=False,
            )
            self.nodes[node["id"]] = node  # upsert
        
        print(f"   Processed {files_processed} files and {dirs_processed} directories from data")

        print("Step 6: Building adjacency list...")
        # Build adjacency with dedupe+sort (dirs first, then name A→Z)
        by_parent: Dict[str, Set[str]] = defaultdict(set)
        for n in self.nodes.values():
            pid = n["parent_id"]
            if pid and pid in self.nodes:
                by_parent[pid].add(n["id"])

        adj: Dict[str, List[str]] = {}
        for pid, children_ids in by_parent.items():
            ordered = list(children_ids)
            ordered.sort(key=lambda nid: (1 - self.nodes[nid]["is_dir"], self.nodes[nid]["name"].lower()))
            adj[p] = ordered if (p := pid) else ordered  # keep mypy calm

        self.adjacency_list = adj
        print(f"   Built adjacency list with {len(adj)} parent nodes")

        print("Step 7: Finding root nodes...")
        # Root nodes: nodes with no parent_id or parent not present (drive roots)
        root_ids = [
            n["id"]
            for n in self.nodes.values()
            if (n["parent_id"] is None) or (n["parent_id"] not in self.nodes)
        ]
        root_ids.sort(key=lambda nid: self.nodes[nid]["name"].lower())
        print(f"   Found {len(root_ids)} root nodes")
        
        for root_id in root_ids[:3]:  # Show first 3 roots
            root_node = self.nodes[root_id]
            print(f"     Root: {root_node['name']} ({root_node['path_abs']})")

        print("Step 8: Generating metadata...")
        metadata = {
            "total_nodes": len(self.nodes),
            "total_files": sum(1 for n in self.nodes.values() if n["is_dir"] == 0),
            "total_directories": sum(1 for n in self.nodes.values() if n["is_dir"] == 1),
            "synthetic_directories": sum(1 for nid in synthetic_dir_ids if nid in self.nodes),
        }
        print(f"   Total nodes: {metadata['total_nodes']}")
        print(f"   Files: {metadata['total_files']}")
        print(f"   Directories: {metadata['total_directories']}")
        print(f"   Synthetic directories: {metadata['synthetic_directories']}")

        return self.nodes, self.adjacency_list, root_ids, metadata

    # ---------------- Save ---------------- #

    def save_json(self, out_path: str) -> Dict[str, Any]:
        nodes, adjacency, root_ids, metadata = self.build()

        print("Step 9: Saving to JSON file...")
        # Ensure directory exists
        out_dir = os.path.dirname(out_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            print(f"   Created output directory: {out_dir}")

        payload = {
            "nodes": nodes,
            "adjacency_list": adjacency,
            "root_ids": root_ids,
            "metadata": metadata,
        }

        print(f"   Writing JSON to: {out_path}")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"[OK] Tree saved → {out_path}")
        print(f"[SUMMARY] {metadata}")
        return payload


# ------------------------ Configuration ------------------------ #

def main() -> None:
    """
    Main function - Edit the parameters below to configure your tree builder.
    """
    
    # ========== EDIT THESE PARAMETERS ========== #
    
    # Path to your LanceDB database directory
    DB_PATH = "C:/Professional/test-db"
    
    # Name of the table in LanceDB containing your file metadata
    TABLE_NAME = "Hello"
    
    # Where to save the output JSON file (where the API expects it)
    OUTPUT_PATH = "../data/file_tree.json"
    
    # =========================================== #
    
    print(f"Configuration:")
    print(f"   Database: {DB_PATH}")
    print(f"   Table: {TABLE_NAME}")
    print(f"   Output: {OUTPUT_PATH}")
    print()
    
    try:
        # Build the tree
        print("Building file tree...")
        builder = FileTreeBuilder(DB_PATH, TABLE_NAME)
        result = builder.save_json(OUTPUT_PATH)
        
        print()
        print("Success! Tree structure created.")
        print(f"Output saved to: {OUTPUT_PATH}")
        print(f"Total nodes: {result['metadata']['total_nodes']}")
        print(f"Directories: {result['metadata']['total_directories']}")
        print(f"Files: {result['metadata']['total_files']}")
        print(f"Synthetic dirs: {result['metadata']['synthetic_directories']}")
        
        # Show sample of nodes
        sample_nodes = list(result['nodes'].items())[:5]
        if sample_nodes:
            print()
            print("Sample nodes:")
            for node_id, node in sample_nodes:
                node_type = "DIR " if node['is_dir'] else "FILE"
                print(f"   {node_type} {node['name']} ({node['path_abs']})")
                
    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Tips:")
        print("   - Check that the database path exists and is correct")
        print("   - Verify the table name matches your LanceDB table")
        print("   - Ensure the output directory can be created")
        raise

if __name__ == "__main__":
    main()
