RAG_PROMPT = """
You are an expert AI assistant.

Use the conversation history when interpreting the current question.

Answer ONLY from the retrieved documents.

If the answer is not available, respond:

"I could not find the answer in the provided documents."

Conversation History:

{history}

Retrieved Documents:

{context}

Current Question:

{question}

Answer:
"""


REWRITE_PROMPT = """
You are an AI assistant.

Your task is to rewrite the user's latest question into a complete standalone question.

Use the conversation history only if necessary.

If the latest question is already complete, return it unchanged.

Conversation History:

{history}

Latest Question:

{question}

Standalone Question:
"""