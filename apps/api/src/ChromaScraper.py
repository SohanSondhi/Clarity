import os
import mimetypes
import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime
from PyPDF2 import PdfReader

# ---- setup ----
persist_dir = "./chroma_store"
collection_name = "files"

ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
client = chromadb.PersistentClient(path=persist_dir)
try:
    col = client.get_collection(collection_name)
except:
    col = client.create_collection(name=collection_name, embedding_function=ef)

# ---- helpers ----
def get_text(path):
    if path.lower().endswith(".pdf"):
        try:
            reader = PdfReader(path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            print(f"  [PDF ERROR] {path}: {e}")
            return ""
    mt, _ = mimetypes.guess_type(path)
    if mt and "text" in mt:
        try:
            return open(path, "r", encoding="utf-8", errors="ignore").read()
        except Exception as e:
            print(f"  [TEXT ERROR] {path}: {e}")
            return ""
    return ""

def add_file(path):
    print(f"Indexing: {path}")
    try:
        stat = os.stat(path)
        metadata = {
            "parent": os.path.dirname(path),
            "name": os.path.basename(path),
            "file_type": mimetypes.guess_type(path)[0] or "unknown",
            "when_created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "when_last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
        text = get_text(path)
        col.add(ids=[path], documents=[text], metadatas=[metadata])
        print(f"  Added: {metadata['name']}")
    except Exception as e:
        print(f"  Failed to index {path}: {e}")

def index_dir(start_path):
    count = 0
    for root, _, files in os.walk(start_path):
        for f in files:
            fpath = os.path.join(root, f)
            add_file(fpath)
            count += 1
    print(f"\nDone! Indexed {count} files into collection '{collection_name}'.")

# ---- run ----
if __name__ == "__main__":
    index_dir("C:\Professional\CLIP_PAPERS\Papers")
