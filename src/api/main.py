from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src.core.services import ask, ask_stream
import uuid
import os

app = FastAPI(
    title = "Conversational RAG API",
    description= "PDF + Website RAG Assistant with Hybrid Retrieval and Gemini",
    version= "1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class ChatRequest(BaseModel):
    question: str
    session_id: str = "default_session"

@app.get("/api-info")
def home():
    return {
        "message" : "Conversational RAG API is running!"
    }
    
@app.get("/health")
def health():
    return {
        "status": "Healthy"
    }
    
@app.post("/chat")
def chat(request: ChatRequest):
    try:
        standalone_question, answer, sources, latencies = ask(request.question, request.session_id)
        
        return {
            "session_id": request.session_id,
            "question": request.question,
            "standalone_question": standalone_question,
            "answer": answer,
            "sources": sources,
            "latencies": latencies
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/stream")
def stream_chat(request: ChatRequest):
    try:
        return StreamingResponse(
            ask_stream(request.question, request.session_id),
            media_type="text/plain"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files AT THE END so API routes take priority over static file routes
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")