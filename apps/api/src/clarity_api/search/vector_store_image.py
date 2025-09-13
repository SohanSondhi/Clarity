# vector_store_image.py
import json
import numpy as np
from image_embed import ImageEmbedder

DB_PATH = "data/index/image_db.json"
embedder = ImageEmbedder()

def load_image_db():
    """Load the JSON database of indexed images."""
    with open(DB_PATH, "r") as f:
        return json.load(f)

def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    a = np.array(a, dtype="float32")
    b = np.array(b, dtype="float32")
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

def search_by_image(query_path: str, k: int = 5):
    """Search the DB using an image query."""
    db = load_image_db()

    # Embed the query image
    qvec = embedder.embed(query_path)[0].tolist()

    # Compare against stored embeddings
    results = []
    for entry in db:
        score = cosine_similarity(qvec, entry["Embeddings"])
        results.append({
            "Path": entry["Path"],
            "Name": entry["Name"],
            "Score": score,
            "When Created": entry["When Created"],
            "When Last Modified": entry["When Last Modified"],
            "Description": entry["Description"],
            "File type": entry["File type"],
            "Tags": entry["Tags"]
        })

    # Sort by similarity (highest first)
    results.sort(key=lambda x: x["Score"], reverse=True)
    return results[:k]

# Example usage
if __name__ == "__main__":
    results = search_by_image("data/sample_images/query.jpg", k=5)
    for r in results:
        print(f"{r['Score']:.3f} | {r['Name']} ({r['Path']})")