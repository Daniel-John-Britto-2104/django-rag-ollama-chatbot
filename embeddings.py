from langchain_community.embeddings import HuggingFaceEmbeddings


from langchain_huggingface import HuggingFaceEmbeddings


def get_embeddings():

    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )