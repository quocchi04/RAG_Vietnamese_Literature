from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma

from src.embedding.embedder import get_embeddings
from src.ingest.chunker import split_documents
from src.ingest.loader import load_documents
from src.utils.config import PROCESSED_DATA_DIR, VECTOR_STORE_DIR
from src.utils.helpers import documents_to_dicts, ensure_dir, save_json

# Tạo vector store từ các chunk đã xử lý
def build_vector_store(chunks, db_dir: Path = VECTOR_STORE_DIR) -> Chroma:
    embeddings = get_embeddings()               # gọi hàm get_embeddings() để chuyển text thành vector
    ensure_dir(db_dir)
    # Tạo Chroma DB từ danh sách document
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,                       
        persist_directory=str(db_dir),      
    )
    return vectorstore


def load_vector_store(db_dir: Path = VECTOR_STORE_DIR) -> Chroma:
    embeddings = get_embeddings()
    return Chroma(
        persist_directory=str(db_dir),
        embedding_function=embeddings,          # embedding dùng cho câu hỏi truy vấn
    )


# Hàm chính để chạy indexing và lưu debug info vào file JSON để dễ kiểm tra
def build_index_and_save_debug() -> None:
    documents = load_documents()
    chunks = split_documents(documents)
    vectorstore = build_vector_store(chunks)        # dùng các chunk đã có để tạo Chroma DB

    save_json(documents_to_dicts(chunks),           # đổi danh sách Document thành dict thường
               PROCESSED_DATA_DIR / 'chunks.json')

    print(f'Loaded {len(documents)} documents/pages')
    print(f'Created {len(chunks)} chunks')
    print(f'Indexed {vectorstore._collection.count()} chunks into ChromaDB')


if __name__ == '__main__':
    build_index_and_save_debug()
