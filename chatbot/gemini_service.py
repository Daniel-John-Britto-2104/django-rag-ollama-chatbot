from .ollama_service import ask_ollama

def ask_gemini(context, question):
    """Alias for backwards compatibility -- uses Ollama (llama3.2)."""
    return ask_ollama(context, question)