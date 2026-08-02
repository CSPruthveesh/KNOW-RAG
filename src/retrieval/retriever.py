from src.retrieval.vector_store import VectorStore

class Retriever:
    
    def __init__(self):
        self.vector_store = VectorStore()
        
    def search(self,query,k=5):
        return self.vector_store.db.similarity_search_with_score(query=query,k=k)
    
    def search_pdf(self,query,k=5):
        return self.vector_store.db.similarity_search_with_score(query,k=k,filter={"type":"pdf"})
    
    def search_website(self,query,k=5):
        return self.vector_store.db.similarity_search_with_score(query,k=k,filter={"type":"website"})
    
    def display(self,docs):
        for i, doc in enumerate(docs,1):
            print("-"*70)
            print(f"Result {i}")
            print()
            print(doc.page_content[:300])
            print()
            print(doc.metadata)
            