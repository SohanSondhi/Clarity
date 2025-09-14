import numpy as np
import lancedb
from sklearn.metrics.pairwise import cosine_similarity
from apps.api.data.image_embed import ImageEmbedder 

class ImageSearcher:
    def __init__(self, db_path: str, table_name: str = "images"):
        self.db = lancedb.connect(db_path)
        if table_name not in self.db.table_names():
            raise ValueError(f"Table '{table_name}' not found in LanceDB.")
        self.table = self.db.open_table(table_name)
        self.embedder = ImageEmbedder()

    def search(self, query_image_path: str) -> str:
        # Embed the query image
        query_vec = self.embedder.embed(query_image_path)[0]

        # Pull stored vectors
        df = self.table.to_pandas()
        df = df[["Path", "Vector"]]
        if df.empty:
            raise ValueError("Image table is empty.")

        vectors = np.vstack(df["Vector"].values)
        sims = cosine_similarity([query_vec], vectors)[0]

        # Get index of best match
        best_idx = int(np.argmax(sims))
        best_path = df.iloc[best_idx]["Path"]

        return best_path


if __name__ == "__main__":
    searcher = ImageSearcher("apps/api/data/clarity_db")
    query_img = "apps/api/data/testdata/cat.png"
    print("Best match path:", searcher.search(query_img))