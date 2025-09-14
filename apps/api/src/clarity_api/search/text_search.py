import numpy as np
import lancedb
from sklearn.metrics.pairwise import cosine_similarity
from apps.api.data.FileScraper import Summarizer


class TextSearcher:
    def __init__(self, db_path: str, table_name: str = "text"):
        self.db = lancedb.connect(db_path)
        if table_name not in self.db.table_names():
            raise ValueError(f"Table '{table_name}' not found in LanceDB.")
        self.table = self.db.open_table(table_name)
        self.summarizer = Summarizer()

    def search(self, query: str) -> str:
        # Embed query with Summarizer (prefer summarize_query, fallback to raw embed)
        if hasattr(self.summarizer, "summarize_query"):
            query_vec, _ = self.summarizer.summarize_query(query)
        else:
            query_vec = self.summarizer._embedder.encode(query)

        # Pull stored vectors
        df = self.table.to_pandas()
        df = df[["Path", "Vector"]]
        if df.empty:
            raise ValueError("Text table is empty.")

        vectors = np.vstack(df["Vector"].values)
        sims = cosine_similarity([query_vec], vectors)[0]

        # Get index of best match
        best_idx = int(np.argmax(sims))
        best_path = df.iloc[best_idx]["Path"]

        return best_path


if __name__ == "__main__":
    searcher = TextSearcher("apps/api/data/clarity_db")
    query = "deep learning methods for image recognition"
    print("Best match path:", searcher.search(query))