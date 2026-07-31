from ollama_service import ask_ollama

context = """
Python is a programming language.
It was created by Guido van Rossum.
"""

question = "Who created Python?"

response = ask_ollama(context, question)

print("Ollama Response:")
print(response)
