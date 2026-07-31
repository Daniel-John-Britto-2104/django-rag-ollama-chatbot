from gemini_service import ask_gemini
context = """
Python is a programming language.
It was created by Guido van Rossum.
"""

question = "Who created Python?"

response = ask_gemini(context, question)

print(response)