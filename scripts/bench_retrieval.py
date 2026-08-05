"""Measure per-stage retrieval latency and how much each stage reorders results.

Local stages only (no LLM call): dense search, BM25, RRF fusion, cross-encoder
rerank. Run from the repo root: python -m scripts.bench_retrieval
"""
import statistics
import time

from langchain_core.documents import Document

from src.config import TOP_K
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.reranker import Reranker
from src.retrieval.retriever import Retriever

QUERIES = [
    "What is multi-head attention?",
    "How does positional encoding work in the transformer?",
    "What is the computational complexity of self-attention per layer?",
    "How do I stream tokens from a LangChain model?",
    "What is middleware in LangChain and when should I write a custom one?",
    "How does short-term memory differ from long-term memory?",
    "What optimizer and learning rate schedule were used for training?",
    "How do I connect an MCP server to an agent?",
    "What BLEU score did the base model reach on English-to-German?",
    "How are tools bound to a chat model?",
]


def main():
    t0 = time.perf_counter()
    retriever = Retriever()
    db_data = retriever.vector_store.db.get()
    all_docs = [
        Document(page_content=txt, metadata=meta)
        for txt, meta in zip(db_data["documents"], db_data["metadatas"])
    ]
    hybrid = HybridRetriever(vectorstore=retriever.vector_store, documents=all_docs)
    reranker = Reranker()
    load_ms = (time.perf_counter() - t0) * 1000

    print(f"corpus chunks       : {len(all_docs)}")
    print(f"cold start (index + models loaded): {load_ms:.0f} ms\n")

    dense_ms, bm25_ms, hybrid_ms, rerank_ms = [], [], [], []
    reordered = 0
    dense_only_overlap = []

    for q in QUERIES:
        t = time.perf_counter()
        dense = hybrid.vector_search(q, k=50)
        dense_ms.append((time.perf_counter() - t) * 1000)

        t = time.perf_counter()
        hybrid.bm25_search(q, k=50)
        bm25_ms.append((time.perf_counter() - t) * 1000)

        t = time.perf_counter()
        candidates = hybrid.search(q, k=25)
        hybrid_ms.append((time.perf_counter() - t) * 1000)

        t = time.perf_counter()
        final = reranker.rerank(q, candidates, k=TOP_K, alpha=0.5)
        rerank_ms.append((time.perf_counter() - t) * 1000)

        pre = [d.page_content for d, _ in candidates[:TOP_K]]
        post = [d.page_content for d, _ in final]
        if pre != post:
            reordered += 1

        dense_top = {d.page_content for d, _ in dense[:TOP_K]}
        dense_only_overlap.append(len(dense_top & set(post)))

    def report(name, xs):
        print(
            f"{name:<28} mean {statistics.mean(xs):7.1f} ms   "
            f"median {statistics.median(xs):7.1f} ms   max {max(xs):7.1f} ms"
        )

    report("dense (Chroma, k=50)", dense_ms)
    report("sparse (BM25, k=50)", bm25_ms)
    report("hybrid + RRF (k=25)", hybrid_ms)
    report("cross-encoder rerank 25->5", rerank_ms)
    e2e = [h + r for h, r in zip(hybrid_ms, rerank_ms)]
    report("retrieval end-to-end", e2e)

    n = len(QUERIES)
    print(f"\nqueries where rerank changed the top-{TOP_K} order : {reordered}/{n}")
    print(
        f"mean overlap between dense-only top-{TOP_K} and final top-{TOP_K} : "
        f"{statistics.mean(dense_only_overlap):.1f}/{TOP_K} "
        f"({statistics.mean(dense_only_overlap) / TOP_K * 100:.0f}%)"
    )


if __name__ == "__main__":
    main()
