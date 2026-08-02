from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from src.config import(
    CHROMA_PATH,
    EMBEDDING_MODEL
)

class VectorStore:
    
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.db = Chroma(persist_directory=CHROMA_PATH, embedding_function=self.embeddings)
       
    def add_documents(self, documents):
        self.db.add_documents(documents)
        print(f"-----Added {len(documents)} documents-----") 
    
    def similarity_search(self, query, k=5):
        return self.db.similarity_search_with_score(query,k=k)
    
    def get_retriever(self, k=5):
        return self.db.as_retriever(search_kwargs={"k": k})
    
    def count(self):
        return self.db._collection.count()
    
    def reset(self):
        self.db.reset_collection()
        print("-----Database cleared-----")