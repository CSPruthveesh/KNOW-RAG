from src.config import *
from google import genai
from src.retrieval.retriever import Retriever
from src.core.prompts import RAG_PROMPT, REWRITE_PROMPT
from src.core.memory import ChatMemory
from src.retrieval.hybrid_retriever import HybridRetriever
from langchain_core.documents import Document
import time
from google.genai import errors
from src.retrieval.reranker import Reranker
import json


client = genai.Client(api_key=GOOGLE_API_KEY)
retriever = Retriever()
memory = ChatMemory()
db_data = retriever.vector_store.db.get()
all_docs = [
    Document(page_content=txt, metadata=meta)
    for txt, meta in zip(db_data["documents"], db_data["metadatas"])
]


hybrid_retriever = HybridRetriever(
    vectorstore=retriever.vector_store,
    documents=all_docs
)

reranker = Reranker()

def build_context(documents):
    context = []
    for i ,(doc,score) in enumerate(documents, start=1):
        doc_type = doc.metadata.get("type", "Unknown")
        
        if doc_type=="pdf":
            source = doc.metadata.get("source","Unknown PDF")
            location = f"Page: {doc.metadata.get('page', 'N/A')}"
        else:
            source = doc.metadata.get("url",doc.metadata.get("source", "Unknown Website"))
            location = ""
        context.append(f"""
                       ==============================
Document {i}

Type: {doc_type}
Source: {source}
{location}

Content:
{doc.page_content}
"""
                       )
        
    return "\n".join(context)

def build_sources(documents):
    sources = []
    seen = set()
    for doc, score in documents:
        doc_type = doc.metadata.get("type", "unknown").lower()
        source = doc.metadata.get("source", doc.metadata.get("url", "Unknown Source"))
        page = doc.metadata.get("page")
        url = doc.metadata.get("url") if doc_type != "pdf" else None
        preview = doc.page_content.strip()[:240] + ("..." if len(doc.page_content.strip()) > 240 else "")
        
        key = (source, page)
        if key in seen:
            continue
        seen.add(key)
        
        sources.append({
            "type": doc_type,
            "source": source,
            "page": page,
            "url": url,
            "score": round(float(score), 4),
            "preview": preview
        })
    return sources


def generate_with_retry(prompt, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model=LLM_MODEL,contents=prompt)
            return response.text.strip()
        except errors.ClientError as e:
            if e.code == 429:
                if attempt < max_retries - 1:
                    print(f"\n-----[!] Rate limit hit. Waiting 30 seconds before retrying (Attempt {attempt+1}/{max_retries})-----")
                    time.sleep(30)
                else:
                    print("\n-----[!] Max retires reached. Returning error message-----")
                    return "-----Error: Google Gemini rate limit exceeded. Please wait a minute and try again-----"
            else:
                raise e
    return "-----Error: Failed to generate a response-----"
 
    
def ask(question, session_id="default_session"):
    standalone_question = rewrite_question(question, session_id=session_id)
    if "Error: Google Gemini rate limit exceeded" in standalone_question:
        return question, standalone_question, []
    
    start_retriever = time.perf_counter()
    candidate_docs = hybrid_retriever.search(standalone_question, k=25)
    end_retriever = time.perf_counter()
    retriever_latency = (end_retriever - start_retriever)*1000
    
    start_reranker = time.perf_counter()
    docs = reranker.rerank(standalone_question, candidate_docs, k=TOP_K, alpha=0.5)
    end_reranker = time.perf_counter()
    reranker_latency = (end_reranker-start_reranker)*1000
    
    context = build_context(docs)
    history = memory.get_history(session_id=session_id)
    prompt = RAG_PROMPT.format(history=history,context=context,question=question)
    
    start_llm = time.perf_counter()
    answer_text = generate_with_retry(prompt)
    end_llm = time.perf_counter()
    llm_latency = (end_llm-start_llm)*1000
    if "Error: Google Gemini rate limit exceeded" not in answer_text:
        memory.add_user_message(question, session_id=session_id)
        memory.add_ai_message(answer_text, session_id=session_id)
    
    latencies = {
        "retriever": round(retriever_latency, 1),
        "reranker": round(reranker_latency, 1),
        "llm": round(llm_latency, 1),
        "total": round(retriever_latency + reranker_latency + llm_latency, 1)
    }
    
    print("-"*50)    
    print("-----LATENCY BREAKDOWN-----")
    print(f"Stage 1 (Hybrid Retriever) : {retriever_latency:.2f} ms")
    print(f"Stage 2 (Reranker) : {reranker_latency:.2f} ms")
    print(f"Stage 3 (LLM) : {llm_latency:.2f} ms")
    print(f"Total Latency : {retriever_latency + reranker_latency + llm_latency:.2f} ms")
    print("-"*50)
    
    
    return(
        standalone_question,
        answer_text,
        build_sources(docs),
        latencies
    )
    
def ask_stream(question, session_id="default_session"):
    standalone_question = rewrite_question(question, session_id=session_id)
    if "Error: Google Gemini rate limit exceeded" in standalone_question:
        yield standalone_question
        return
    
    start_retriever = time.perf_counter()
    candidate_docs = hybrid_retriever.search(standalone_question, k=25)
    end_retriever = time.perf_counter()
    retriever_latency = (end_retriever - start_retriever)*1000
    
    start_reranker = time.perf_counter()
    docs = reranker.rerank(standalone_question, candidate_docs, k=TOP_K, alpha=0.5)
    end_reranker = time.perf_counter()
    reranker_latency = (end_reranker-start_reranker)*1000
    
    context = build_context(docs)
    history = memory.get_history(session_id=session_id)
    prompt = RAG_PROMPT.format(history=history,context=context,question=question)
    
    start_llm = time.perf_counter()
    full_answer = ""
    try:
        stream = client.models.generate_content_stream(model=LLM_MODEL, contents=prompt)
        for chunk in stream:
            print("Chunk received:", repr(chunk.text))
            text = getattr(chunk, "text", "")
            if text:
                full_answer += text
                yield text
    except Exception as e:
        yield f"\n\n<END_OF_ANSWER>\n"
        yield json.dumps(
            {
                "error": str(e)
            }
        )
        return
    end_llm = time.perf_counter()
    llm_latency = (end_llm-start_llm)*1000
    if "Error: Google Gemini rate limit exceeded" not in full_answer:
        memory.add_user_message(question, session_id=session_id)
        memory.add_ai_message(full_answer, session_id=session_id)
    
    sources = build_sources(docs)
    latencies = {
        "retriever": round(retriever_latency, 1),
        "reranker": round(reranker_latency, 1),
        "llm": round(llm_latency, 1),
        "total": round(retriever_latency + reranker_latency + llm_latency, 1)
    }
    
    yield "\n\n<END_OF_ANSWER>\n"
    yield json.dumps(
        {
            "standalone_question": standalone_question,
            "sources": sources,
            "latencies": latencies
        }
    )
    
    print("-"*50)    
    print("-----LATENCY BREAKDOWN-----")
    print(f"Stage 1 (Hybrid Retriever) : {retriever_latency:.2f} ms")
    print(f"Stage 2 (Reranker) : {reranker_latency:.2f} ms")
    print(f"Stage 3 (LLM) : {llm_latency:.2f} ms")
    print(f"Total Latency : {retriever_latency + reranker_latency + llm_latency:.2f} ms")
    print("-"*50)
    
    
def rewrite_question(question, session_id="default_session"):
    history = memory.get_history(session_id=session_id)
    if not history.strip():
        return question
    prompt = REWRITE_PROMPT.format(
        history = history,
        question = question
    )
    
    return generate_with_retry(prompt)
    
if __name__ == "__main__":
    while True:
        question = input("\nYou: ")
        if question.lower() == "exit":
            break
        
        if question.lower() == "clear":
            memory.clear()
            print("-----Conversation cleared-----")
            continue
            
        standalone_question,answer, sources = ask(question)
        print("\n" + "-"*50)
        print("\nStandalone Question:")
        print("\n" + "-"*50)
        print(standalone_question)
        print("\n" + "-"*50)
        print("ANSWER")
        print("-"*50)
        print(answer)
        
        print("\n" + "-"*50)
        print("SOURCES")
        print("-"*50)
        for s in sources:
            print("-",s)
        
        
        
