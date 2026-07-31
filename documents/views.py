from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import os
import shutil
import tempfile
from dotenv import load_dotenv

# Ensure temp files, SQLite locks, and HuggingFace caches use D: drive
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

os.environ["TEMP"] = TEMP_DIR
os.environ["TMP"] = TEMP_DIR
os.environ["TMPDIR"] = TEMP_DIR
os.environ["SQLITE_TMPDIR"] = TEMP_DIR
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = CACHE_DIR
os.environ["TORCH_HOME"] = CACHE_DIR
tempfile.tempdir = TEMP_DIR

from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from embeddings import get_embeddings
from .models import Document
from chatbot.models import ChatMessage

load_dotenv()

VECTOR_DB_PATH = os.path.join(BASE_DIR, "vector_db")


# -------------------------
# Chat Page
# -------------------------

def upload_document(request):
    return render(
        request,
        "documents/upload.html"
    )


# -------------------------
# PDF Upload + Indexing
# -------------------------

@csrf_exempt
def upload_pdf(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"})

    pdf = request.FILES.get("document")
    if not pdf:
        return JsonResponse({"error": "PDF required"})

    file_path = os.path.join(TEMP_DIR, f"temp_{pdf.name}")

    with open(file_path, "wb+") as destination:
        for chunk in pdf.chunks():
            destination.write(chunk)

    print("\n" + "="*60)
    print(" 📄 [STEP 1: PDF TEXT EXTRACTION]")
    print("="*60)
    print(f"File Name: {pdf.name}")
    print(f"File Size: {pdf.size / 1024:.2f} KB")

    # Extract PDF text
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    full_extracted_text = "\n".join([doc.page_content for doc in documents])
    print(f"Total Pages Loaded: {len(documents)}")
    print(f"Total Character Count: {len(full_extracted_text)}")
    print("\n--- Extracted Text Preview (First 400 chars) ---")
    print(full_extracted_text[:400])
    print("--------------------------------------------------\n")

    # Optimized Text Chunking
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = splitter.split_documents(documents)

    print("="*60)
    print(f" 🧩 [STEP 2: CHUNKING RESULT - Total Chunks: {len(chunks)}]")
    print("="*60)
    for idx, c in enumerate(chunks, 1):
        print(f"Chunk #{idx} | Page: {c.metadata.get('page', 0)} | Length: {len(c.page_content)} chars")
        print(f"Content: {c.page_content[:150].strip()}...\n")

    # Clear previous ChromaDB vector store automatically
    print("="*60)
    print(" 🧹 [STEP 3: CLEARING STALE VECTORS]")
    print("="*60)
    if os.path.exists(VECTOR_DB_PATH):
        try:
            shutil.rmtree(VECTOR_DB_PATH, ignore_errors=True)
            print(f"Successfully purged previous vector DB at: {VECTOR_DB_PATH}")
        except Exception as e:
            print(f"Error purging old vector database: {e}")

    # Generate Embeddings & Store Vectors
    print("="*60)
    print(" 🧠 [STEP 4: GENERATING EMBEDDINGS & STORING IN CHROMADB]")
    print("="*60)
    embeddings = get_embeddings()

    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_DB_PATH
    )

    print(f"✓ Indexed {len(chunks)} chunks into ChromaDB at '{VECTOR_DB_PATH}'")
    print("="*60 + "\n")

    # Save Document record to Django Database
    try:
        doc_record = Document.objects.create(
            title=pdf.name,
            file=pdf,
            content=full_extracted_text
        )
        print(f"✓ Saved Document ID #{doc_record.id} '{pdf.name}' to Django Database")
    except Exception as e:
        print(f"Error saving Document to database: {e}")

    # Clean up uploaded temporary file
    if os.path.exists(file_path):
        os.remove(file_path)

    return JsonResponse({
        "message": f"PDF '{pdf.name}' uploaded and indexed successfully ({len(chunks)} chunks)."
    })


# -------------------------
# Ask Question
# -------------------------

@csrf_exempt
def ask_question(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"})

    question = request.POST.get("question")
    if not question:
        return JsonResponse({"error": "Question required"})

    print("\n" + "="*60)
    print(f" ❓ [STEP 1: USER QUESTION]: '{question}'")
    print("="*60)

    # Load Vector Database
    embeddings = get_embeddings()
    db = Chroma(
        persist_directory=VECTOR_DB_PATH,
        embedding_function=embeddings
    )

    # Improved Similarity Search with Scores (k=5)
    docs_with_scores = db.similarity_search_with_score(
        question,
        k=5
    )

    print(f" 🔍 [STEP 2: RETRIEVAL RESULTS - Retrieved {len(docs_with_scores)} Chunks]")
    print("="*60)

    if not docs_with_scores:
        print("❌ No relevant chunks found in vector database.")
        return JsonResponse({
            "answer": "Information not available in the document."
        })

    docs = []
    for i, (doc, score) in enumerate(docs_with_scores, 1):
        docs.append(doc)
        print(f"\n--- Retrieved Chunk #{i} (Distance Score: {score:.4f}) ---")
        print(f"Page: {doc.metadata.get('page', 0)}")
        print(f"Snippet: {doc.page_content[:250].strip()}...")

    # Prepare Context
    context = "\n\n--- Chunk Context ---\n".join([doc.page_content for doc in docs])

    # Strict RAG Prompt Template
    prompt = PromptTemplate(
        template="""You are a strict, factual AI assistant.

CRITICAL RULES:
1. Answer the question DIRECTLY and PRECISELY using ONLY the information provided in the Context below.
2. Do NOT hedge or use filler phrases like "It appears to be", "Based on the document", "The candidate seems to be", or "According to the context". State the answer immediately and directly.
3. Do NOT use any outside knowledge, assumptions, or extra facts.
4. Never summarize unless explicitly requested.
5. If the exact answer exists in the Context, return it directly and concisely.
6. If the answer is NOT present in the Context, reply EXACTLY: "Information not available in the document."

Context:
{context}

Question:
{question}

Answer:""",
        input_variables=["context", "question"]
    )

    formatted_prompt = prompt.format(context=context, question=question)
    print("\n" + "="*60)
    print(" 📤 [STEP 3: PROMPT SENT TO OLLAMA]")
    print("="*60)
    print(formatted_prompt[:500] + "\n...[truncated context]...")

    # Ollama LLM Execution (llama3.2)
    llm = ChatOllama(
        model="llama3.2",
        temperature=0.1,
        base_url="http://localhost:11434"
    )

    chain = prompt | llm

    response = chain.invoke({
        "context": context,
        "question": question
    })

    answer = response.content.strip()

    print("\n" + "="*60)
    print(f" 🤖 [STEP 4: OLLAMA RESPONSE]:\n{answer}")
    print("="*60 + "\n")

    # Save ChatMessage record to Django Database
    try:
        chat_record = ChatMessage.objects.create(
            question=question,
            answer=answer
        )
        print(f"✓ Saved ChatMessage ID #{chat_record.id} to Django Database")
    except Exception as e:
        print(f"Error saving ChatMessage to database: {e}")

    return JsonResponse({
        "answer": answer
    })