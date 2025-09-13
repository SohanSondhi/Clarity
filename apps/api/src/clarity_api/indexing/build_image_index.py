import os
import json
from datetime import datetime
from image_embed import ImageEmbedder

# Where to scan for images
ROOT_DIR = "data/sample_images"   # change this to wherever your images live
DB_PATH = "data/index/image_db.json"

# Init embedder
embedder = ImageEmbedder()
db = []

def is_system_file(fname: str) -> bool:
    """Check if file is a system/hidden file we should skip."""
    return (
        fname.startswith(".")                # hidden files (.DS_Store, .gitignore)
        or fname.lower() in ["thumbs.db", "desktop.ini"]  # Windows system files
    )

def embed_image_file(path: str):
    """Create a JSON DB entry for one image file."""
    vec = embedder.embed(path)[0].tolist()  # numpy -> python list

    # Detect file type based on extension
    ext = os.path.splitext(path)[1].lower()
    if ext in [".jpg", ".jpeg"]:
        file_type = "image/jpeg"
    elif ext == ".png":
        file_type = "image/png"
    else:
        file_type = "image/unknown"

    entry = {
        "Path": path,
        "Parent": os.path.dirname(path),
        "Tags": [],  # empty for now, can fill later
        "Embeddings": vec,
        "Name": os.path.basename(path),
        "When Created": datetime.fromtimestamp(os.path.getctime(path)).isoformat(),
        "When Last Modified": datetime.fromtimestamp(os.path.getmtime(path)).isoformat(),
        "Description": None,   # optional: BLIP caption or other description
        "File type": file_type
    }
    return entry

# Walk the folder tree
for root, _, files in os.walk(ROOT_DIR):
    for fname in files:
        if is_system_file(fname):
            print(f"Skipped system file: {fname}")
            continue

        # Only accept .jpg/.jpeg/.png
        if fname.lower().endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(root, fname)
            try:
                entry = embed_image_file(path)
                db.append(entry)
                print(f"Indexed {fname}")
            except Exception as e:
                print(f"Skipped {fname}: {e}")

# Save JSON DB
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
with open(DB_PATH, "w") as f:
    json.dump(db, f, indent=2)

print(f"Done. Indexed {len(db)} images into {DB_PATH}")