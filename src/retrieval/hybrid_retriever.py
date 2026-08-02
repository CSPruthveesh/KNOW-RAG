from rank_bm25 import BM25Okapi


class HybridRetriever:
    
    def __init__(self, vectorstore, documents):
        self.vectorstore = vectorstore
        self.documents = documents
        tokenized = [
            doc.page_content.lower().split()
            for doc in documents
        ]
        self.bm25 = BM25Okapi(tokenized)
        
    def vector_search(self, query, k=5):
        return self.vectorstore.similarity_search(
            query,
            k=k
        ) 
    
    def bm25_search(self, query, k=5):
        tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)
        
        ranked = sorted(
            zip(self.documents, scores),
            key = lambda x: x[1],
            reverse=True
        )
        
        return [
            (doc,score)
            for doc, score in ranked[:k]
        ]
        
    
    """
    def search(self, query, k=5):
        vector_docs = self.vector_search(query,k)
        bm25_docs = self.bm25_search(query,k)
        
        merged = []
        seen = set()
        for doc,score in vector_docs + bm25_docs:
            text = doc.page_content
            if text not in seen:
                merged.append((doc,score))
                seen.add(text)
                
        return merged
    """
    def search(self, query, k=5, rrf_k=60):
        fetch_k = max(k*2,10)
        vector_docs = self.vector_search(query, k=fetch_k)
        bm25_docs = self.bm25_search(query, k=fetch_k)
        
        rrf_scores = {}
        doc_map = {}
        
        def add_to_rrf(docs):
            for rank, (doc,_raw_score) in enumerate(docs,start=1):
                text = doc.page_content
                if text not in rrf_scores:
                    rrf_scores[text] = 0.0
                    doc_map[text] = doc
                
                rrf_scores[text] += 1.0 / (rank + rrf_k)
                
        add_to_rrf(vector_docs)
        add_to_rrf(bm25_docs)
        
        ranked_docs = sorted(
            [(doc_map[text], score) for text, score in rrf_scores.items()],
            key = lambda x: x[1],
            reverse=True
        )    
        
        return ranked_docs[:k]
    