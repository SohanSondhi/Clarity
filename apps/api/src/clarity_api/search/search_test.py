import sys, os

# Add project root to sys.path so imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from text_search import TextSearcher
from image_search import ImageSearcher

# Resolve DB path relative to project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
DB_PATH = os.path.join(BASE_DIR, "apps/api/data/clarity_db")

TEXT_TABLE = "text"
IMAGE_TABLE = "images"


def test_text_search():
    print("Using DB:", DB_PATH)
    if not os.path.exists(DB_PATH):
        print("❌ DB path does not exist:", DB_PATH)
        return

    searcher = TextSearcher(DB_PATH, table_name=TEXT_TABLE)
    query = "physics study guide"
    best_path = searcher.search(query)
    print("Text search result:", best_path)
    if os.path.basename(best_path) == "PH-UY_Final_Study_Guide.pdf":
        print("✅ Text search worked correctly!")
    else:
        print("❌ Text search returned unexpected result")


def test_image_search():
    searcher = ImageSearcher(DB_PATH, table_name=IMAGE_TABLE)
    query_img = os.path.join(BASE_DIR, "apps/api/data/testdata/cat.png")
    best_path = searcher.search(query_img)
    print("Image search result:", best_path)
    if os.path.basename(best_path) == "cat.png":
        print("✅ Image search worked correctly!")
    else:
        print("❌ Image search returned unexpected result")


if __name__ == "__main__":
    test_text_search()
    test_image_search()