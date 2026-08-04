import streamlit as st
import requests
import uuid
import json

st.set_page_config(
    page_title="RAG Intelligence — Minimalist Interface",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# MINIMALIST ZINC DESIGN SYSTEM (Custom CSS)
# ---------------------------------------------------------
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Light Zinc Theme Background */
    .stApp {
        background-color: #FAFAFA !important;
        color: #18181B !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E4E4E7 !important;
    }

    /* Header Bar */
    .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.85rem 1.25rem;
        background: #FFFFFF;
        border: 1px solid #E4E4E7;
        border-radius: 14px;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.03);
    }

    .brand-logo {
        width: 26px;
        height: 26px;
        background: #18181B;
        color: #FFFFFF;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.75rem;
        margin-right: 0.5rem;
    }

    .version-tag {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        text-transform: uppercase;
        padding: 2px 6px;
        border-radius: 4px;
        background: #F4F4F5;
        color: #52525B;
        border: 1px solid #E4E4E7;
        margin-left: 0.5rem;
    }

    /* Chat Messages Glass & Minimal Container */
    div[data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E4E4E7 !important;
        border-radius: 16px !important;
        padding: 1.25rem !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.03) !important;
    }

    /* Expanders */
    .stExpander {
        background: #F4F4F5 !important;
        border: 1px solid #E4E4E7 !important;
        border-radius: 12px !important;
        overflow: hidden;
    }

    /* Source Citation Minimal Cards */
    .source-card-minimal {
        background: #FFFFFF;
        border: 1px solid #E4E4E7;
        border-radius: 10px;
        padding: 0.85rem;
        margin-bottom: 0.65rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02);
    }

    .source-snippet {
        background: #FAFAFA;
        border: 1px solid #E4E4E7;
        border-radius: 6px;
        padding: 0.5rem 0.75rem;
        font-size: 0.78rem;
        color: #3F3F46;
        font-style: italic;
        margin-top: 0.4rem;
    }

    /* Latency Metric Badges */
    .latency-pill {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        padding: 3px 8px;
        border-radius: 6px;
        background: #F4F4F5;
        color: #3F3F46;
        border: 1px solid #E4E4E7;
    }

    /* Buttons Styling */
    .stButton > button {
        background: #18181B !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        transition: all 0.15s ease !important;
        width: 100% !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    }

    .stButton > button:hover {
        background: #27272A !important;
        transform: translateY(-1px) !important;
    }

    /* Chat Input Field */
    div[data-testid="stChatInput"] {
        border-radius: 16px !important;
        border: 1px solid #D4D4D8 !important;
        background: #FFFFFF !important;
        box-shadow: 0 2px 6px 0 rgba(0, 0, 0, 0.03) !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ---------------------------------------------------------
# TOP APP HEADER
# ---------------------------------------------------------
st.markdown("""
<div class="app-header">
    <div style="display: flex; align-items: center;">
        <span class="brand-logo">K</span>
        <span style="font-weight: 600; font-size: 0.95rem; color: #18181B; letter-spacing: -0.01em;">KNOW-RAG</span>
        <span class="version-tag">v1.0 Enterprise</span>
    </div>
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #71717A;">
        RAG Mode: <strong style="color: #18181B;">Hybrid Vector + Keyword Search</strong>
    </div>
</div>
""", unsafe_allow_html=True)

API_BASE_URL = "http://127.0.0.1:8000"

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------
# SIDEBAR: KNOWLEDGE BASE & THREAD HISTORY
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; padding-bottom: 0.75rem; border-bottom: 1px solid #E4E4E7; margin-bottom: 1rem;">
        <div style="display: flex; align-items: center;">
            <span style="font-weight: 600; font-size: 0.9rem; color: #18181B;">Navigation</span>
        </div>
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #71717A; background: #F4F4F5; padding: 2px 6px; border-radius: 4px; border: 1px solid #E4E4E7;">⌘K</span>
    </div>
    """, unsafe_allow_html=True)

    use_streaming = st.toggle("Enable Token Streaming", value=True)
    
    if st.button("+ New Conversation", type="primary"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    # Connected Sources Section
    st.markdown("""
    <div style="margin-top: 1.5rem; margin-bottom: 0.5rem; font-size: 0.72rem; font-weight: 600; color: #A1A1AA; text-transform: uppercase; letter-spacing: 0.05em;">
        Connected Sources
    </div>
    <div style="space-y: 0.5rem;">
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0.65rem; background: #F4F4F5; border: 1px solid #E4E4E7; border-radius: 8px; font-size: 0.78rem; font-weight: 500; color: #18181B; margin-bottom: 0.4rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem; overflow: hidden;">
                <span>📄</span> <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">attention.pdf</span>
            </div>
            <span style="width: 7px; height: 7px; background: #10B981; border-radius: 50%;"></span>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0.65rem; background: #FFFFFF; border: 1px solid #E4E4E7; border-radius: 8px; font-size: 0.78rem; color: #52525B;">
            <div style="display: flex; align-items: center; gap: 0.5rem; overflow: hidden;">
                <span>🌐</span> <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">docs.langchain.com</span>
            </div>
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #A1A1AA;">Active</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # User Info Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 0.65rem; padding: 0.5rem; background: #FAFAFA; border-radius: 8px; border: 1px solid #E4E4E7;">
        <div style="width: 28px; height: 28px; background: #E4E4E7; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; color: #27272A;">PA</div>
        <div>
            <div style="font-size: 0.78rem; font-weight: 600; color: #18181B;">Pruthveesh A.</div>
            <div style="font-size: 0.68rem; color: #71717A;">Session: <code style="font-family: monospace;">{st.session_state.session_id[:8]}</code></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# LATENCY BAR & SOURCE CARDS RENDERERS
# ---------------------------------------------------------
def render_latency_bar(latencies):
    if not latencies:
        return
    retriever_ms = latencies.get("retriever", 0)
    reranker_ms = latencies.get("reranker", 0)
    llm_ms = latencies.get("llm", 0)
    total_ms = latencies.get("total", 0)
    
    st.markdown(f"""
    <div style="display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.65rem; margin-bottom: 0.65rem;">
        <span class="latency-pill">🔍 Hybrid: <b>{retriever_ms} ms</b></span>
        <span class="latency-pill">🎯 Rerank: <b>{reranker_ms} ms</b></span>
        <span class="latency-pill">⚡ Gemini: <b>{llm_ms} ms</b></span>
        <span class="latency-pill" style="background: #18181B; color: #FFFFFF; border: none;">⏱️ Total: <b>{total_ms} ms</b></span>
    </div>
    """, unsafe_allow_html=True)

def render_source_cards(sources):
    if not sources:
        return
    with st.expander(f"📚 Grounded in {len(sources)} Retrieved Chunks"):
        for s in sources:
            if isinstance(s, dict):
                doc_type = s.get("type", "unknown").upper()
                source_name = s.get("source", "Unknown")
                page = s.get("page")
                url = s.get("url")
                score = s.get("score", 0.0)
                preview = s.get("preview", "")
                
                location_str = f"[Doc, p.{page}]" if page else "[Web Doc]"
                score_str = f"Score: {score:.2f}"
                title_html = f'<a href="{url}" target="_blank" style="color: #18181B; font-weight: 600; text-decoration: underline;">{source_name}</a>' if url else f'<b>{source_name}</b>'
                
                st.markdown(f"""
                <div class="source-card-minimal">
                    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem;">
                        <span style="font-family: 'JetBrains Mono', monospace; font-weight: 600; color: #18181B;">
                            {location_str} {title_html}
                        </span>
                        <span style="background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; padding: 2px 6px; border-radius: 4px;">
                            {score_str}
                        </span>
                    </div>
                    {f'<div class="source-snippet">"{preview}"</div>' if preview else ''}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.write(str(s))

# ---------------------------------------------------------
# DISPLAY CHAT HISTORY
# ---------------------------------------------------------
for message in st.session_state.messages:
    avatar_icon = "👤" if message["role"] == "user" else "⚡"
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if message.get("latencies"):
                render_latency_bar(message["latencies"])
            if message.get("sources"):
                render_source_cards(message["sources"])

# ---------------------------------------------------------
# EMPTY STATE: RECOMMENDED STARTER QUESTIONS
# ---------------------------------------------------------
pending_question = None
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align: center; padding: 2.5rem 1rem 1.5rem 1rem;">
        <h3 style="font-weight: 700; font-size: 1.35rem; color: #18181B; margin-bottom: 0.35rem; letter-spacing: -0.02em;">What would you like to synthesize today?</h3>
        <p style="color: #71717A; font-size: 0.88rem;">Select a prompt below or type your question to start retrieving context.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Summarize 'Attention Is All You Need' paper"):
            pending_question = "Summarize the Attention Is All You Need paper and its key architecture."
        if st.button("🌐 Explain LangChain Middleware & packages"):
            pending_question = "What is LangChain middleware and what packages does it support?"
    with col2:
        if st.button("⚡ How to configure LangSmith tracing"):
            pending_question = "How do I configure LangSmith tracing for monitoring and debugging?"
        if st.button("🔍 Explain Hybrid Search & RRF score blending"):
            pending_question = "Explain how hybrid retrieval and reciprocal rank fusion work in this app."

# ---------------------------------------------------------
# INPUT PROCESSING
# ---------------------------------------------------------
chat_input_val = st.chat_input("Ask a question about your documents...")
question = pending_question or chat_input_val

if question:
    # Append & display user message
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="👤"):
        st.markdown(question)

    # Process assistant response
    with st.chat_message("assistant", avatar="⚡"):
        full_text = ""
        sources = []
        latencies = {}
        
        if use_streaming:
            message_placeholder = st.empty()
            try:
                res = requests.post(
                    f"{API_BASE_URL}/stream",
                    json={
                        "question": question,
                        "session_id": st.session_state.session_id
                    },
                    stream=True,
                    timeout=120
                )
                
                if res.status_code == 200:
                    buffer = ""
                    is_metadata = False
                    metadata_str = ""
                    
                    for chunk in res.iter_content(chunk_size=None, decode_unicode=True):
                        if not chunk:
                            continue
                        
                        if is_metadata:
                            metadata_str += chunk
                        else:
                            buffer += chunk
                            if "<END_OF_ANSWER>" in buffer:
                                parts = buffer.split("<END_OF_ANSWER>", 1)
                                full_text += parts[0]
                                message_placeholder.markdown(full_text)
                                is_metadata = True
                                metadata_str += parts[1]
                                buffer = ""
                            else:
                                if "<" in buffer:
                                    idx = buffer.find("<")
                                    full_text += buffer[:idx]
                                    buffer = buffer[idx:]
                                else:
                                    full_text += buffer
                                    buffer = ""
                                message_placeholder.markdown(full_text + "▌")
                    
                    if buffer and not is_metadata:
                        full_text += buffer
                    
                    message_placeholder.markdown(full_text)
                    
                    if metadata_str.strip():
                        try:
                            meta = json.loads(metadata_str.strip())
                            sources = meta.get("sources", [])
                            latencies = meta.get("latencies", {})
                        except Exception:
                            pass
                    
                    if latencies:
                        render_latency_bar(latencies)
                    if sources:
                        render_source_cards(sources)
                else:
                    full_text = f"Error {res.status_code}: {res.text}"
                    st.error(full_text)
            except Exception as e:
                full_text = f"Connection error: {e}"
                st.error(full_text)
        else:
            try:
                res = requests.post(
                    f"{API_BASE_URL}/chat",
                    json={
                        "question": question,
                        "session_id": st.session_state.session_id
                    },
                    timeout=120
                )
                if res.status_code == 200:
                    data = res.json()
                    full_text = data.get("answer", "")
                    sources = data.get("sources", [])
                    latencies = data.get("latencies", {})
                    st.markdown(full_text)
                    if latencies:
                        render_latency_bar(latencies)
                    if sources:
                        render_source_cards(sources)
                else:
                    full_text = f"Error {res.status_code}: {res.text}"
                    st.error(full_text)
            except Exception as e:
                full_text = f"Connection error: {e}"
                st.error(full_text)

        # Store assistant response in history
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": full_text,
                "sources": sources,
                "latencies": latencies
            }
        )