import streamlit as st
import requests

st.set_page_config(
    page_title="Conversational RAG",
    page_icon="🤖",
    layout="wide"
)

st.title("Conversational RAG Assistant")
st.caption("PDF + Website RAG • Hybrid Retrieval • Gemini ")

API_URL = "http://127.0.0.1:8000/chat"

if "messages" not in st.session_state:
    st.session_state.messages = []
    
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if "sources" in message:
                with st.expander("Sources"):
                    for source in message["Sources"]:
                        st.write(source)
                        
question = st.chat_input("Ask a question...")
if question:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )
    
    with st.chat_message("user"):
        st.markdown(question)
        
        
response = requests.post(
    API_URL,
    json={
        "question": question
    }
)

data = response.json()
answer = data["answer"]
sources = data['sources']

with st.chat_message("assistant"):
    st.markdown(answer)
    with st.expander("Sources"):
        for source in sources:
            st.write(source)
            
st.session_state.messages.append(
    {
        "role": "assistant",
        "content": answer,
        "sources": sources
    }
)