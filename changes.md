# Conversational RAG Improvements & Frontend Migration Log

Comprehensive summary of all bug fixes, pipeline updates, and frontend migration from Streamlit to a Minimalist HTML/CSS/JS Enterprise UI ("KNOW-RAG v1.0").

## 1. Core Services & Pipeline Improvements (`src/core/services.py`)

- **Session Memory Propagation**: Updated `rewrite_question(question, session_id)` default parameter. Propagated `session_id` cleanly through `ask()` and `ask_stream()` to isolate chat history per session.
- **Latency Breakdown**: Calculated latency metrics (`retriever_latency`, `reranker_latency`, `llm_latency`, `total_latency`) and included a `latencies` dictionary in both `ask()` return values and `ask_stream()` metadata JSON trailers.
- **Structured Source Citations**: Refactored `build_sources(documents)` to return rich structured objects containing `type` (`pdf` / `website`), `source`, `page`, `url`, `score`, and `preview` text snippets.

## 2. API Backend & Route Precedence (`src/api/main.py`)

- **Session Passing**: Updated `/stream` and `/chat` routes to extract and forward `request.session_id` to the RAG pipeline.
- **Latencies Output**: Unpacked and returned `latencies` dictionary in `/chat` JSON responses.
- **Static File Mounting**: Added `app.mount("/", StaticFiles(directory="frontend", html=True))` at the very bottom of `main.py` after all `@app.post` and `@app.get` routes to ensure API routes take precedence over static file routing.

## 3. Frontend Overhaul (Migrated to Vanilla HTML / CSS / JavaScript)

Shifted frontend from Streamlit to a standalone HTML/CSS/JS architecture located in `frontend/`:

- **`frontend/index.html`**:
  - Implemented minimalist zinc enterprise theme ("KNOW-RAG v1.0") using Tailwind CSS CDN, Inter font, and JetBrains Mono code font.
  - Added collapsible left sidebar featuring connected source indicators (`attention.pdf`, `docs.langchain.com`), streaming toggle switch, and user profile badge (`Pruthveesh A.`).
  - Added right collapsible **Citation & Grounding Drawer** displaying retrieved document chunk cards.
  - Added empty state **1-click Suggested Question Cards** grid.
  - Built bottom-anchored chat input area with context badges and send actions.

- **`frontend/style.css`**:
  - Custom scrollbar styling.
  - Text streaming pulse cursor animation (`.streaming-cursor::after`).
  - Smooth fade-in message entry keyframes (`@keyframes fadeIn`).

- **`frontend/script.js`**:
  - Native `Fetch` API streaming reader (`response.body.getReader()`) for real-time response token rendering.
  - Automatic `crypto.randomUUID()` session ID management.
  - Parsing of `<END_OF_ANSWER>` sentinel and JSON metadata trailers for sources and stage latencies.
  - Dynamic rendering of latency badges (`🔍 Hybrid`, `🎯 Rerank`, `⚡ Gemini`, `⏱️ Total`) and source chunk cards.
