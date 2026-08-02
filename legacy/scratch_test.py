"""from vector_store import VectorStore
vs = VectorStore()
print("-----Initiating test.py-----")
print("Documents:", vs.count())"""

"""from ingest_pdf import PDFIngestor
pdf = PDFIngestor()
pdf.ingest("data/pdfs/attention.pdf")"""

"""from ingest_web import WebsiteIngestor
web = WebsiteIngestor()
web.ingest("https://docs.langchain.com/oss/python/langchain/overview")"""

from retriever import Retriever
retriever = Retriever()
docs = retriever.search("What is attention?")
retriever.display(docs)
