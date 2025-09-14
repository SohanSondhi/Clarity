import numpy as np
import lancedb
from sklearn.metrics.pairwise import cosine_similarity
import sys
import os

# Add the project src directory to the path
current_dir = os.path.dirname(__file__)
project_src_dir = os.path.normpath(os.path.join(current_dir, "../../"))
sys.path.insert(0, project_src_dir)

from clarity_api.indexing.image_embed import ImageEmbedder 

class ImageSearcher:
    def __init__(self, db_path: str, table_name: str = "images"):
        self.db = lancedb.connect(db_path)
        if table_name not in self.db.table_names():
            raise ValueError(f"Table '{table_name}' not found in LanceDB.")
        self.table = self.db.open_table(table_name)
        self.embedder = ImageEmbedder()

    def search(self, query: str) -> str:
        try:
            print(f"🔍 Searching for: {query}")
            
            # Check if query is a file path or text description
            if os.path.exists(query):
                # It's a file path - embed the image
                print("📸 Embedding query image...")
                query_vec = self.embedder.embed(query)[0]
            else:
                # It's a text description - embed the text using CLIP
                print("📝 Embedding text description...")
                query_vec = self.embedder.embed_text(query)[0]  # Get first (and only) vector
            
            print(f"✅ Query vector shape: {query_vec.shape}")

            # Pull stored vectors
            print("📊 Loading database vectors...")
            df = self.table.to_pandas()
            print(f"📋 Database has {len(df)} images")
            
            if df.empty:
                raise ValueError("Image table is empty.")
            
            # Check if required columns exist
            if 'Path' not in df.columns or 'Vector' not in df.columns:
                raise ValueError(f"Missing required columns. Available: {df.columns.tolist()}")
            
            df = df[["Path", "Vector"]]
            
            # Convert vectors to numpy array
            print("🔄 Converting vectors to numpy array...")
            vectors = np.vstack(df["Vector"].values)
            print(f"✅ Vectors shape: {vectors.shape}")
            
            # Calculate similarities
            print("🧮 Calculating similarities...")
            sims = cosine_similarity([query_vec], vectors)[0]
            print(f"✅ Similarities calculated: {len(sims)} results")

            # Get index of best match
            best_idx = int(np.argmax(sims))
            best_path = df.iloc[best_idx]["Path"]
            best_score = sims[best_idx]
            
            print(f"🏆 Best match: {best_path} (score: {best_score:.4f})")
            return best_path
            
        except Exception as e:
            print(f"❌ Image search error: {e}")
            raise


if __name__ == "__main__":
    searcher = ImageSearcher("C:/Users/sohan/Clarity/Clarity/apps/api/data/clarity_db")
    query_img = "C:/Users/sohan/Clarity/Clarity/apps/api/data/testdata/cat.png"
    print("Best match path:", searcher.search(query_img))