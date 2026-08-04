from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import RecursiveUrlLoader

from src.config import CHUNK_SIZE, CHUNK_OVERLAP
from src.retrieval.vector_store import VectorStore

class WebsiteIngestor:
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = CHUNK_SIZE,
            chunk_overlap = CHUNK_OVERLAP,
            separators=["\n\n","\n",". "," ",""]
        )
        
    def extract_text(self, html):
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    
    def load(self,url):
        loader = RecursiveUrlLoader(
            url = url,
            extractor=self.extract_text,
            max_depth=2
        )
        
        return loader.load()
    
    def create_documents(self, url):
        docs = self.load(url)
        return self.text_splitter.split_documents(docs)
    
    def add_metadata(self,docs):
        for doc in docs:
            doc.metadata["type"] = "website"
            
        return docs
    
    def ingest(self,url):
        docs = self.create_documents(url)
        docs = self.add_metadata(docs)
        self.vector_store.add_documents(docs)
        print(f"-----Ingested {len(docs)} website chunks-----")
        try:
            from src.core.services import refresh_index
            refresh_index()
            print("-----BM25 Index Refreshed-----")
        except Exception:
            pass