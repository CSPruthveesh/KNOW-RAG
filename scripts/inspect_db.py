from collections import defaultdict
from src.retrieval.vector_store import VectorStore


def inspect_database():
    vs = VectorStore()

    collection = vs.db._collection

    data = collection.get(
        include=["documents", "metadatas"]
    )

    documents = data["documents"]
    metadatas = data["metadatas"]

    print("\n" + "=" * 80)
    print(f"Total Chunks : {len(documents)}")
    print("=" * 80)

    grouped = defaultdict(list)

    for doc, meta in zip(documents, metadatas):
        source = (
            meta.get("filename")
            or meta.get("source")
            or meta.get("url")
            or "Unknown Source"
        )

        grouped[source].append((doc, meta))

    for source, chunks in grouped.items():
        print(f"\n📄 {source}")
        print("-" * 80)

        for i, (doc, meta) in enumerate(chunks, start=1):
            chunk_type = meta.get("type", "unknown")

            if chunk_type == "pdf":
                page = meta.get("page", "?")
                header = f"Chunk {i} | Page {page}"

            elif chunk_type == "website":
                header = f"Chunk {i}"

            else:
                header = f"Chunk {i}"

            print(f"\n{header}")
            print(f"Metadata : {meta}")

            preview = doc.replace("\n", " ")[:200]
            print(f"Preview  : {preview}...")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    inspect_database()