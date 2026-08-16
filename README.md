# KNOW-RAG v1.0 — Enterprise Conversational RAG Intelligence Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.138.2-009688.svg)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB%201.5.9-orange.svg)](https://www.trychroma.com/)
[![Gemini](https://img.shields.io/badge/LLM-Gemini%203.1%20Flash--Lite-purple.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**KNOW-RAG v1.0** is an enterprise-grade Conversational Retrieval-Augmented Generation (RAG) platform operating over multi-modal document collections (PDFs and web documentation). Built from scratch, the system integrates a 4-stage hybrid search pipeline, real-time HTTP token streaming, per-stage microsecond latency profiling, and a single-page interface featuring an administrative **Developer Mode** for live ETL document ingestion.

---

## ⚡ Key Features

- **4-Stage Hybrid RAG Pipeline**: Combines history-aware query rewriting, hybrid dense + sparse retrieval (ChromaDB + BM25Okapi) with Reciprocal Rank Fusion (RRF), cross-encoder neural reranking (`ms-marco-MiniLM-L-6-v2`), and LLM generation (Gemini 3.1 Flash-Lite).
- **Minimalist Enterprise SPA**: Single-Page Application (SPA) frontend in Vanilla HTML5, CSS3, and JavaScript adhering to a sleek Zinc color palette, Inter typography, responsive sidebar navigation, and interactive citation grounding drawers.
- **Developer Mode ETL Ingestion Interface**: Zero-reload view toggle allowing administrators to drag and drop PDF files or crawl web documentation URLs in real time.
- **Zero-Downtime Dynamic BM25 Index Refreshing**: Auto-reindexes sparse BM25 memory upon document ingestion without requiring backend server restarts.
- **Real-Time Asynchronous Token Streaming**: Full-stack HTTP streaming via FastAPI `StreamingResponse` and JS `ReadableStream`, delivering first-token candidates in sub-55ms followed by trailing JSON latency breakdown trailers (`🔍 Hybrid`, `🎯 Rerank`, `⚡ Gemini`, `⏱️ Total`).
- **Session-Keyed Memory Isolation**: Session-propagated conversation state ensuring total context isolation across multi-user sessions.
- **Filtering & Chronological Sorting**: Developer Mode file management table featuring document type filtering (PDF vs Website) and timestamp-sorted document tracking.

---

## 🏗️ 4-Stage Architecture Pipeline

```
User Question + Chat History (Session Isolated)
       │
  1. Query Rewriter (Gemini LLM) ────────► Standalone Contextualized Question
       │
  2. Hybrid Candidate Retrieval (Top 25) ─► Dense  : ChromaDB + all-MiniLM-L6-v2
       │                                  ├─ Sparse : BM25Okapi (rank-bm25)
       │                                  └─ Fusion : Reciprocal Rank Fusion (RRF)
  3. Cross-Encoder Reranker (Top 5) ─────► Neural Reranker (ms-marco-MiniLM-L-6-v2)
       │                                  └─ Blended Cross-Encoder & RRF Scores
  4. Generation & Token Streaming ───────► Gemini 3.1 Flash-Lite ──► Live Stream + Citation Trailer
```

---

## 📁 Repository Structure

```
.
├── src/
│   ├── config.py              # Environment configuration & model settings
│   ├── api/
│   │   └── main.py            # FastAPI REST endpoints & static file mounting
│   ├── core/
│   │   ├── services.py        # 4-stage pipeline execution (ask & ask_stream)
│   │   ├── memory.py          # Session-keyed chat history memory
│   │   └── prompts.py         # System prompts for query re-writing & QA
│   ├── ingestion/
│   │   ├── pdf.py             # PyMuPDF page-level extraction & chunking
│   │   └── web.py             # Recursive web scraper & BeautifulSoup loader
│   └── retrieval/
│       ├── vector_store.py    # ChromaDB wrapper
│       ├── retriever.py       # Dense vector search
│       ├── hybrid_retriever.py# Hybrid dense + sparse BM25 RRF retriever
│       └── reranker.py        # Cross-encoder neural reranker
├── frontend/
│   ├── index.html             # Minimalist Enterprise SPA layout & Dev Mode UI
│   ├── style.css              # Custom styling, scrollbars, & streaming cursor micro-animations
│   ├── script.js             # Vanilla JS stream reader, API bindings, & view state handlers
│   └── streamlit_app.py       # Legacy Streamlit prototype
├── scripts/
│   ├── inspect_db.py          # DB inspection script grouping vectors by source
│   └── bench_retrieval.py     # Retrieval latency benchmark script
├── data/
│   └── pdfs/                  # Source document storage
├── contributions_summary.md   # Detailed developer contribution & resume metrics
├── requirements.txt           # Pinned python dependencies
└── README.md                  # Project documentation
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- Python 3.11+
- Virtual environment (`venv`)

### 2. Clone & Environment Setup
```bash
git clone https://github.com/CSPruthveesh/KNOW-RAG.git
cd KNOW-RAG

python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

---

## 🚀 Running the Application

Launch the FastAPI backend server (serves both the REST API and the frontend SPA):

```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

Access the application in your browser:
- **Web Application SPA**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🔌 API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | `GET` | Liveness and health check (`{"status": "Healthy"}`) |
| `/chat` | `POST` | Standard Q&A payload endpoint (`{"question": "...", "session_id": "..."}`) |
| `/stream` | `POST` | Asynchronous token streaming endpoint with trailing `<END_OF_ANSWER>` sentinel & JSON metadata |
| `/ingest-file` | `POST` | Upload & ingest PDF file into ChromaDB and BM25 index |
| `/ingest-web` | `POST` | Scrape & ingest web documentation URL into ChromaDB and BM25 index |
| `/refresh` | `POST` | Manually trigger in-memory BM25 index auto-refresh |
| `/list-sources` | `GET` | List active ingested documents, chunk counts, type metadata, and timestamps |

---

## 🧪 Benchmarking & Database Inspection

To inspect active vector chunks stored in ChromaDB:
```bash
python -m scripts.inspect_db
```

To run retrieval pipeline latency benchmarks:
```bash
python -m scripts.bench_retrieval
```

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
