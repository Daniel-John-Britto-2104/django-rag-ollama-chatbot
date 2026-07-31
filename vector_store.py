from langchain_community.vectorstores import Chroma


def save_vectors(chunks, embeddings):

    db = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory="vector_db"
    )

    return db