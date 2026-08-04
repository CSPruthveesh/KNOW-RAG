# Conversational RAG Improvements & Bug Fixes Plan

Plan to fix streaming endpoint (`/stream`), session memory isolation, and Streamlit UI integration.

## Issues Addressed

1. **Session Memory Isolation**:
   - `session_id` was ignored in `ask()`, `ask_stream()`, and `rewrite_question()`, causing all chats to share default session memory.
   - Now properly passed down to `memory.get_history()` and `memory.add_*_message()`.

2. **API Streaming Route (`/stream`)**:
   - `stream_chat` endpoint in `src/api/main.py` did not accept or pass `session_id`.
   - Generator function `ask_stream()` in `src/core/services.py` crashed when calling `rewrite_question()` without passing `session_id`.

3. **Streamlit Frontend UI (`frontend/streamlit_app.py`)**:
   - HTTP POST request was executing outside the `if question:` block, sending requests on page load.
   - Capitalization mismatch in `message["Sources"]` vs `message["sources"]` caused a `KeyError`.
   - Added `uuid4()` based session ID persistence in Streamlit `session_state`.
   - Integrated live response streaming from `/stream` via `requests.post(..., stream=True)` with real-time text rendering and source parsing.

## Summary of Changes

- `src/core/services.py`: Fixed `rewrite_question`, `ask`, and `ask_stream` to accept and handle `session_id`. Updated streaming generator to safely yield response chunks and metadata JSON.
- `src/api/main.py`: Updated `/stream` route to pass `request.session_id`.
- `frontend/streamlit_app.py`: Rewrote frontend to stream tokens, manage session IDs, handle sources cleanly, and fix top-level request execution bug.
