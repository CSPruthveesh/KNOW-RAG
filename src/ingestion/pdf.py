import fitz
import os
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.config import CHUNK_SIZE, CHUNK_OVERLAP
from src.retrieval.vector_store import VectorStore

class PDFIngestor:
    def __init__(self):
        self.vector_store = VectorStore()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = CHUNK_SIZE,
            chunk_overlap = CHUNK_OVERLAP,
            separators=["\n\n","\n",". "," ",""]
        )
        
    def clean_text(self,text):
        text = " ".join(text.split())
        return text
    
    def extract_text(self,pdf_path):
        pdf = fitz.open(pdf_path)
        pages = []
        
        for page_num, page in enumerate(pdf):
            text = self.clean_text(page.get_text())
            if(len(text) < 50):
                continue
            pages.append((page_num+1,text))
        
        pdf.close()
        return pages

    def create_documents(self, pdf_path):
        pages = self.extract_text(pdf_path)
        documents = []
        filename = os.path.basename(pdf_path)
        
        for page_num, text in pages:
            chunks = self.text_splitter.split_text(text)
            for chunk in chunks:
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata = {
                            "source": filename,
                            "page": page_num,
                            "type": "pdf"
                        }
                        )
                )
                
        return documents
    
    def ingest(self, pdf_path):
        docs = self.create_documents(pdf_path)
        self.vector_store.add_documents(docs)
        print(f"-----Ingested {len(docs)} chunks-----")
        try:
            from src.core.services import refresh_index
            refresh_index()
            print("-----BM25 Index Refreshed-----")
        except Exception:
            pass 
    
    