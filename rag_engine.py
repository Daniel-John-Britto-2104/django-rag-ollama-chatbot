import os
from langchain_chroma import Chroma
from embeddings import get_embeddings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_DB_PATH = os.path.join(BASE_DIR, "vector_db")

def retrieve_context(question):
    """Retrieve top 5 relevant document chunks for a question."""
    if not os.path.exists(VECTOR_DB_PATH):
        return None

    db = Chroma(
        persist_directory=VECTOR_DB_PATH,
        embedding_function=get_embeddings()
    )

    docs = db.similarity_search(question, k=5)

    if not docs:
        return None

    context = "\n\n--- Chunk Context ---\n".join(doc.page_content for doc in docs)
    return context