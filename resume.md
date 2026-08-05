# Conversational RAG — Resume Points

Every number below was measured against the live index in this repo, not estimated.
Reproduce with `python -m scripts.bench_retrieval` (measurements section at the bottom).

---

## Project header (for the CV)

**Conversational RAG over PDFs and Websites** — Python, FastAPI, LangChain, ChromaDB, Sentence-Transformers, Gemini 2.5 Flash

---

## CV — 3 bullet points

Use these three verbatim if you only have room for one project block. Every number is
measured (see *Verified measurements*), and each bullet covers a different competency:
**system build**, **retrieval engineering**, **performance measurement**.

- Built a conversational RAG service over a **1,693-chunk, 49-source** PDF + website index using **Python, FastAPI, ChromaDB and Gemini 2.5 Flash**, exposing chat, streaming and health endpoints with session-keyed memory and page-level source citations on every answer.

- Engineered a hybrid retrieval pipeline combining **dense vector search (384-dim MiniLM) with BM25 via Reciprocal Rank Fusion**, followed by cross-encoder reranking of 25 candidates down to 5 — which **reordered the top-5 results in 10 of 10 benchmark queries**, replacing **44% of the context** that dense-only retrieval would have passed to the model.

- Profiled per-stage latency across the request path to reach **19 ms hybrid retrieval and ~950 ms end-to-end retrieval on CPU**, and cut the LLM prompt to **4,273 characters — 0.30% of the 1.44 M-character corpus** — identifying the reranker (**98% of retrieval time**) and the LLM call (**63–88% of total latency**) as the two optimisation targets.

---

## Single-liner bullets

One line each, for tight CV layouts or a skills-heavy format. Mix and match.

- Built a 4-stage conversational RAG pipeline over a 1,693-chunk PDF + website index.
- Fused dense vector search with BM25 using Reciprocal Rank Fusion in 19 ms mean.
- Reranked 25 candidates to 5 with a cross-encoder, reordering the top-5 in 10/10 queries.
- Compressed LLM context to 4,273 chars — 0.30% of a 1.44 M-character corpus.
- Cut dense-only overlap to 56%, replacing 44% of retrieved context via fusion + reranking.
- Served the pipeline through FastAPI with chat, streaming, and health endpoints.
- Profiled per-stage latency, isolating the reranker as 98% of retrieval time.
- Ingested PDFs with PyMuPDF at page granularity, yielding citable page-numbered sources.
- Crawled documentation sites to depth 2 into one metadata-tagged 49-source store.
- Resolved multi-turn follow-ups via LLM query rewriting over a 10-message memory window.
- Hardened the Gemini client with bounded retry and backoff across 5 attempts on HTTP 429.
- Refactored a 165-line prototype into a layered ~650-LOC package across 4 modules.
- Wrote a reproducible benchmark harness measuring latency, rerank displacement, and top-k overlap.

---

## Primary bullets (pick 4–6)

- Built a four-stage conversational RAG service (history-aware query rewriting → hybrid retrieval → cross-encoder reranking → grounded generation) over a **1,693-chunk, 49-source index** spanning PDFs and recursively crawled documentation sites, served through a FastAPI app with chat, streaming, and health endpoints.

- Implemented hybrid retrieval fusing dense vector search (ChromaDB, 384-dim `all-MiniLM-L6-v2`) with sparse BM25 via **Reciprocal Rank Fusion**, combining the two ranked lists by rank rather than score so incomparable similarity scales never have to be normalised against each other.

- Added a cross-encoder reranking stage (`ms-marco-MiniLM-L-6-v2`) that scores 25 fused candidates and blends the cross-encoder score with the retrieval score through a tunable `alpha`; the stage **reordered the top-5 in 10 of 10 benchmark queries**, and only **2.8 of 5 final chunks (56%) matched what dense-only retrieval would have returned** — i.e. ~44% of the context reaching the LLM is material dense search alone ranked below the cut.

- Cut the prompt payload to **4,273 characters mean — 0.30% of the 1.44 M-character corpus** — by narrowing 1,693 chunks → 25 fused candidates → 5 reranked chunks, keeping generation cost flat as the corpus grows.

- Instrumented per-stage latency on every request, which localised the bottleneck to the reranker: it accounts for **98% of local retrieval time (931 ms of 950 ms mean)** while dense search costs 37 ms and BM25 5 ms — making it the one stage worth GPU-hosting or batching before anything else is optimised.

- Profiled the full request path at **~6.0 s p50 end-to-end**, with the Gemini call consuming **63–88% of wall-clock**, establishing that response-time work belongs in streaming and prompt-size reduction rather than in retrieval micro-optimisation.

- Engineered page-level PDF ingestion with PyMuPDF (page-scoped chunks preserve citable page numbers; a 15-page paper yields 52 chunks at 1,000/200 chunk/overlap) and a depth-2 recursive web crawler with BeautifulSoup extraction, unifying both into one metadata-tagged store that returns **typed, page-cited sources with confidence scores on every answer**.

- Designed session-keyed conversational memory with a 10-message sliding window feeding an LLM query-rewriter that resolves follow-up references into standalone questions before retrieval, so pronouns and elisions in multi-turn chat don't silently degrade recall.

- Hardened the Gemini integration against 429 rate limiting with bounded retry and backoff (5 attempts), degrading to a typed error response instead of a 500, and kept memory writes transactional — a failed generation never pollutes conversation history.

---

## Optional bullets (depth / engineering-judgment signal)

- Measured that BM25 contributed **zero unique chunks to the final top-5 across 50 slots** on this corpus — dense top-50 already contained every survivor — showing the fusion's value here is *re-ranking* rather than *recall expansion*, and flagging the corpus-dependence of hybrid retrieval instead of assuming it.

- Refactored a 165-line prototype into a layered package (`api` / `core` / `ingestion` / `retrieval`, ~650 LOC) with dependency-injected retrievers and a config module centralising model, chunk, and top-k settings, retaining superseded prototypes under `legacy/` as a documented migration trail.

- Wrote a reproducible retrieval benchmark harness measuring per-stage latency, rerank displacement, and dense-vs-hybrid top-k overlap across a fixed query set, so retrieval changes are evaluated against numbers rather than spot-checks.

---

## Skills line

`Python · FastAPI · LangChain · ChromaDB · Sentence-Transformers · Cross-Encoder Reranking · BM25 · Reciprocal Rank Fusion · Gemini API · PyMuPDF · BeautifulSoup · Streamlit · RAG architecture · Latency profiling`

---

## Verified measurements

Environment: Windows 11, CPU-only inference, live `chroma_db` index, 10-query benchmark set spanning both corpora.

**Corpus**

| Metric | Value |
|---|---|
| Indexed chunks | 1,693 |
| Distinct sources | 49 |
| Chunk types | 1,641 website / 52 PDF |
| Embedding dimension | 384 (`all-MiniLM-L6-v2`) |
| Mean chunk size | 838 chars (cap 1,000, overlap 200) |
| Total corpus text | 1,436,206 chars |

**Per-stage latency** (10 queries, CPU)

| Stage | Mean | Median | Max |
|---|---|---|---|
| Dense search (Chroma, k=50) | 37.0 ms | 20.3 ms | 190.1 ms |
| Sparse search (BM25, k=50) | 5.2 ms | 5.2 ms | 8.9 ms |
| Hybrid + RRF (k=25) | 19.0 ms | 18.4 ms | 25.1 ms |
| Cross-encoder rerank (25→5) | 930.6 ms | 948.1 ms | 1,441.6 ms |
| **Retrieval end-to-end** | **949.6 ms** | **964.8 ms** | **1,459.5 ms** |

Cold start (index load + both models): 18.9 s — one-time, amortised across the process lifetime.

**Full request path** (3 live Gemini calls)

| Query | Retrieval | Rerank | LLM | Total | LLM share |
|---|---|---|---|---|---|
| 1 | 74 ms | 672 ms | 5,241 ms | 5,987 ms | 88% |
| 2 | 19 ms | 887 ms | 5,402 ms | 6,308 ms | 86% |
| 3 | 31 ms | 1,099 ms | 1,939 ms | 3,069 ms | 63% |

End-to-end (including the query-rewrite round-trip): mean 6,091 ms, median 5,987 ms.

**Retrieval quality**

| Metric | Value |
|---|---|
| Queries where rerank changed the top-5 | 10 / 10 |
| Overlap, dense-only top-5 vs final top-5 | 2.8 / 5 (56%) |
| Final top-5 chunks absent from dense top-50 | 0 / 50 |
| Context sent to LLM | 4,273 chars mean (0.30% of corpus) |

---

## Notes before you use these

- The retrieval-quality figures measure **displacement** (how much the pipeline changes what the LLM sees), not **accuracy** — there is no labelled relevance set in this repo. Say "changed the top-5 ranking" in an interview, not "improved accuracy by X%". A hit-rate / MRR evaluation over a labelled query set is the honest next step and the strongest thing you could add.
- The 6 s end-to-end figure is CPU-only and single-user. Don't present it as a production SLA.
- Every bullet above is defensible from code and measurement in this repo — expect follow-up questions on RRF (why rank-based fusion), the `alpha` blend, and why reranking sits after retrieval rather than replacing it.
