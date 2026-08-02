from rank_bm25 import BM25Okapi
import numpy as np
import re
from vector_store import VectorStore

def tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())

class HybridRetriever:
    
    def __init__(self, vectorstore, documents):
        self.vectorstore = VectorStore()
        self.documents = documents
        self.corpus = [
            tokenize(doc.page_content)
            for doc in documents
        ]
        self.bm25 = BM25Okapi(self.corpus)
        
    def vector_search(self, query, k=5):
        results = self.vectorstore.db.similarity_search_with_score(query, k=k)
        return results
        
    def bm25_search(self, query, k=5):
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        top_idx = np.argsort(scores)[::-1][:k]
        
        return [(self.documents[i], float(scores[i])) for i in top_idx]
    
    def search(self, query, k=5):
        vec_results = self.vector_search(query, k)
        bm25_results = self.bm25_search(query, k)
        
        merged = vec_results + bm25_results
        score_map = {}
        for doc, score in merged:
            key = doc.page_content
            
            if key not in score_map:
                score_map[key] = (doc,score)
            else:
                score_map[key] = (
                    doc,
                    max(score_map[key][1], score)
                )
        
        final = sorted(score_map.values(), key = lambda x: x[1], reverse=True)
        return final[:k]