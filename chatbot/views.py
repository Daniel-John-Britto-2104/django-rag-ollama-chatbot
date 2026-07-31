import os
from django.http import JsonResponse
from langchain_chroma import Chroma
from embeddings import get_embeddings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_DB_PATH = os.path.join(BASE_DIR, "vector_db")

def ask_question(request):
    question = request.POST.get("question")
    if not question:
        return JsonResponse({"error": "Question required"})

    if not os.path.exists(VECTOR_DB_PATH):
        return JsonResponse({"answer": "No document indexed yet."})

    db = Chroma(
        persist_directory=VECTOR_DB_PATH,
        embedding_function=get_embeddings()
    )

    docs_with_scores = db.similarity_search_with_score(question, k=5)

    if not docs_with_scores:
        return JsonResponse({
            "answer": "No relevant information found in the document."
        })

    best_doc, score = docs_with_scores[0]

    return JsonResponse({
        "context": best_doc.page_content,
        "score": float(score)
    })