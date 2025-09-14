import chromadb

persist_dir = "./chroma_store"
collection_name = "files"

client = chromadb.PersistentClient(path=persist_dir)
col = client.get_collection(collection_name)

print("Total docs in collection:", col.count())

# Fetch a few entries (with embeddings)
res = col.get(limit=5, include=["documents", "metadatas", "embeddings"])

for i, (doc, meta, emb) in enumerate(zip(res["documents"], res["metadatas"], res["embeddings"])):
    print(f"\n--- Document {i+1} ---")
    print("Name:", meta.get("name"))
    print("Parent:", meta.get("parent"))
    print("Type:", meta.get("file_type"))
    print("Created:", meta.get("when_created"))
    print("Last modified:", meta.get("when_last_modified"))
    print("Text sample:", (doc[:200] + "...") if doc else "<no text>")
    if emb is not None:
        print("Embedding length:", len(emb))
        print("Embedding (first 5 values):", emb[:5])

print("\n" + "="*50)
print("TESTING SIMPLE QUERY")
print("="*50)

# Test a simple query
try:
    query_results = col.query(
        query_texts=["CLIP machine learning"],  # Query for CLIP-related content
        n_results=3,
        include=["documents", "metadatas", "distances"]
    )
    
    print(f"\nQuery: 'CLIP machine learning'")
    print(f"Found {len(query_results['documents'][0])} results")
    
    for i, (doc, meta, distance) in enumerate(zip(
        query_results["documents"][0], 
        query_results["metadatas"][0], 
        query_results["distances"][0]
    )):
        print(f"\n--- Result {i+1} ---")
        print("Name:", meta.get("name"))
        print("Path:", meta.get("parent"))
        print("Distance:", round(distance, 4))
        print("Text preview:", (doc[:100] + "...") if doc else "<no text>")

except Exception as e:
    print(f"Query failed: {e}")

# Test another query
print("\n" + "-"*30)
try:
    pdf_results = col.query(
        query_texts=["PDF analysis document"], 
        n_results=2,
        include=["metadatas", "distances"]
    )
    
    print(f"\nQuery: 'PDF analysis document'")
    for i, (meta, distance) in enumerate(zip(pdf_results["metadatas"][0], pdf_results["distances"][0])):
        print(f"Result {i+1}: {meta.get('name')} (distance: {round(distance, 4)})")

except Exception as e:
    print(f"Second query failed: {e}")


