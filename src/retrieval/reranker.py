from sentence_transformers import CrossEncoder
import numpy as np

class Reranker:
    
    def __init__(self):
        self.model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        
    def rerank(self, query, documents, k=5, alpha=0.5):
        if not documents:
            return []
        
        if isinstance(documents[0], tuple):
            docs_to_score = [doc for doc, _ in documents]
            rrf_scores = np.array([float(score) for _, score in documents])
        else:
            docs_to_score = documents
            rrf_scores = np.zeros(len(documents))
            
        pairs = [(query, doc.page_content) for doc in docs_to_score]
        ce_scores = np.array([float(s) for s in self.model.predict(pairs)])
        
        def normalize(arr):
            low, high = arr.min(), arr.max()
            if high == low:
                return np.zeros_like(arr)
            return (arr-low)/(high-low)
        
        norm_ce = normalize(ce_scores)
        norm_retrieval = normalize(rrf_scores) if rrf_scores.any() else rrf_scores
        
        blended_results = []
        for i, doc in enumerate(docs_to_score):
            final_score = (alpha*norm_ce[i]) + ((1.0-alpha) * norm_retrieval[i]) 
            blended_results.append((doc, final_score))       
        ranked = sorted(blended_results, key= lambda x: x[1], reverse=True)
        
        return ranked[:k]