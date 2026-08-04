import streamlit as st
import requests
import uuid
import json

st.set_page_config(
    page_title="Conversational RAG Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("Conversational RAG Assistant")
st.caption("PDF + Website RAG • Hybrid Retrieval • Cross-Encoder Rerank • Gemini")

API_BASE_URL = "http://127.0.0.1:8000"

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar options
with st.sidebar:
    st.header("Settings & Session")
    use_streaming = st.toggle("Enable Token Streaming", value=True)
    st.caption(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
    
    if st.button("Clear Chat History", type="secondary"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("sources"):
            with st.expander("Sources"):
                for source in message["sources"]:
                    st.write(source)

# Process user input
question = st.chat_input("Ask a question...")

if question:
    # Append & display user message
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Process assistant response
    with st.chat_message("assistant"):
        full_text = ""
        sources = []
        
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
                        except Exception:
                            pass
                    
                    if sources:
                        with st.expander("Sources"):
                            for source in sources:
                                st.write(source)
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
                    st.markdown(full_text)
                    if sources:
                        with st.expander("Sources"):
                            for source in sources:
                                st.write(source)
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
                "sources": sources
            }
        )