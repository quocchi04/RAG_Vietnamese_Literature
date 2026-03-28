from langchain_huggingface import HuggingFaceEmbeddings

from src.utils.config import EMBEDDING_MODEL

def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)        # gọi model đã định nghĩa ở file config 