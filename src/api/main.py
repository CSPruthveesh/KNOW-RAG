from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src.core.services import ask, ask_stream, refresh_index
from src.ingestion.pdf import PDFIngestor
from src.ingestion.web import WebsiteIngestor
import uuid
import os
import shutil

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

class WebIngestRequest(BaseModel):
    url: str

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

@app.get("/list-sources")
def list_sources():
    try:
        from collections import defaultdict
        from src.retrieval.vector_store import VectorStore
        vs = VectorStore()
        collection = vs.db._collection
        data = collection.get(include=["metadatas"])
        metadatas = data.get("metadatas", [])
        
        grouped = defaultdict(int)
        types = {}
        timestamps = defaultdict(float)
        for meta in metadatas:
            if not meta:
                continue
            source = meta.get("source") or meta.get("filename") or meta.get("url") or "Unknown"
            grouped[source] += 1
            types[source] = meta.get("type", "pdf")
            ts = meta.get("timestamp", 0.0)
            if ts > timestamps[source]:
                timestamps[source] = ts
            
        sources_list = []
        for name, count in grouped.items():
            sources_list.append({
                "source": name,
                "type": types[name],
                "chunks": count,
                "status": "Indexed",
                "timestamp": timestamps[name]
            })
            
        # Sort by timestamp descending (recent first)
        sources_list.sort(key=lambda x: x["timestamp"], reverse=True)
        return {"sources": sources_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refresh")
def refresh():
    total_docs = refresh_index()
    return {
        "status": "Index refreshed successfully",
        "total_documents": total_docs
    }

@app.post("/ingest-file")
async def ingest_file(file: UploadFile = File(...)):
    try:
        os.makedirs("temp_uploads", exist_ok=True)
        file_path = os.path.join("temp_uploads", file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        ingestor = PDFIngestor()
        ingestor.ingest(file_path)
        
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return {"status": "Success", "message": f"Successfully ingested {file.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest-web")
def ingest_web(request: WebIngestRequest):
    try:
        ingestor = WebsiteIngestor()
        ingestor.ingest(request.url)
        return {"status": "Success", "message": f"Successfully ingested website {request.url}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
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