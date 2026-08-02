# Conversational RAG

A conversational retrieval-augmented generation assistant over PDFs and websites.
Queries run through a four-stage pipeline: history-aware query rewriting, hybrid
retrieval, cross-encoder reranking, then generation with Gemini.

## Pipeline

```
question
   └─► query rewrite (LLM, using chat history) ──► standalone question
          └─► hybrid retrieval (top 25)
                 ├─ dense    : Chroma + all-MiniLM-L6-v2
                 ├─ sparse   : BM25 (rank-bm25)
                 └─ fusion   : Reciprocal Rank Fusion
                 └─► rerank (top 5)
                        └─ cross-encoder/ms-marco-MiniLM-L-6-v2
                        └─ blended with RRF score via alpha
                        └─► Gemini 2.5 Flash ──► answer + cited sources
```

Retrieval and reranking are timed per stage and the breakdown is logged on every
request.

## Layout

```
src/
├── config.py              env + model/chunk settings
├── api/main.py            FastAPI app
├── core/
│   ├── services.py        the ask() / ask_stream() pipeline
│   ├── memory.py          session-keyed chat history
│   └── prompts.py         RAG + query-rewrite prompts
├── ingestion/
│   ├── pdf.py             PyMuPDF extraction, page-level chunking
│   └── web.py             recursive URL loader + BeautifulSoup
└── retrieval/
    ├── vector_store.py    Chroma wrapper
    ├── retriever.py       dense search
    ├── hybrid_retriever.py  dense + BM25 with RRF
    └── reranker.py        cross-encoder rerank

frontend/streamlit_app.py  Streamlit chat UI
scripts/inspect_db.py      dump indexed chunks grouped by source
legacy/                    superseded prototypes, kept for reference
data/pdfs/                 source PDFs
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Create a `.env` in the repo root:

```
GOOGLE_API_KEY=your_key_here
```

## Ingesting documents

Run from the repo root so the `src` package resolves.

```python
from src.ingestion.pdf import PDFIngestor
PDFIngestor().ingest("data/pdfs/attention.pdf")

from src.ingestion.web import WebsiteIngestor
WebsiteIngestor().ingest("https://example.com/docs")
```

Inspect what's indexed:

```bash
python -m scripts.inspect_db
```

## Running

API:

```bash
uvicorn src.api.main:app --reload
```

- `GET  /health` — liveness check
- `POST /chat` — `{"question": "...", "session_id": "..."}` → answer + sources
- `POST /stream` — token streaming; the answer is followed by an
  `<END_OF_ANSWER>` sentinel and a JSON trailer with sources

Streamlit UI (expects the API on `127.0.0.1:8000`):

```bash
streamlit run frontend/streamlit_app.py
```

## Status

The `/chat` path is the working end-to-end route. Streaming and per-session
memory isolation are still being wired up — `/stream` and the Streamlit client
have known issues.

## Configuration

Tunable in `src/config.py`: embedding model, LLM model, chunk size/overlap, and
`TOP_K`. Retrieval breadth (25 candidates) and the rerank blend weight (`alpha`)
are set at the call sites in `src/core/services.py`.
