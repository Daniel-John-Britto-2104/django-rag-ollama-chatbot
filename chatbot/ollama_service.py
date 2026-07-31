from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

def ask_ollama(context, question):
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

    llm = ChatOllama(
        model="llama3.2",
        temperature=0.1,
        base_url="http://localhost:11434"
    )

    chain = prompt | llm
    response = chain.invoke({"context": context, "question": question})
    return response.content.strip()
