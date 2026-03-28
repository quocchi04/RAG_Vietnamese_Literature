"""
Logic retrieval cho hệ thống RAG.

Bao gồm:
- phát hiện tên tác phẩm trong câu hỏi
- lọc vector search theo metadata khi cần
- format context gửi cho LLM
"""

from __future__ import annotations

from typing import List, Optional

from langchain_core.documents import Document

from src.ingest.cleaner import normalize_for_match
from src.utils.config import MAX_CONTEXT_CHARS, MMR_FETCH_K, RETRIEVER_K
from src.utils.helpers import summarize_sources

# Xem câu hỏi có nhắc tới tên tác phẩm cụ thể không
def detect_source_filter(question: str, available_sources: List[str]) -> Optional[str]:
    normalized_question = normalize_for_match(question)     #chuẩn hóa câu hỏi
    for source in available_sources:
        candidate = normalize_for_match(source).replace('_', ' ')
        if candidate in normalized_question:
            return source
    return None


def get_retriever(vectorstore, available_sources: List[str], question: str):
    # tạo cofig cho việc search, nếu có source_name thì thêm filter vào để chỉ search trong tác phẩm đó
    # ngược lại search toàn bộ vector store
    source_name = detect_source_filter(question, available_sources)
    search_kwargs = {'k': RETRIEVER_K, 'fetch_k': MMR_FETCH_K}

    if source_name:
        search_kwargs['filter'] = {'source_name': source_name}

    return vectorstore.as_retriever(search_type='mmr', search_kwargs=search_kwargs)
    # không chỉ lấy chunk giống nhất mà còn đảm bảo: đa dạng, không trùng nội dung

    
def retrieve_with_scores(vectorstore, available_sources: List[str], question: str):
    source_name = detect_source_filter(question, available_sources)

    search_kwargs = {'k': RETRIEVER_K}
    if source_name:
        search_kwargs['filter'] = {'source_name': source_name}

    docs_and_scores = vectorstore.similarity_search_with_relevance_scores(
        question,
        **search_kwargs,
    )
    return docs_and_scores, source_name
# Biến các chunk thành context gửi cho LLM 
def format_context(docs: List[Document], max_chars: int = MAX_CONTEXT_CHARS) -> str:
    blocks = []
    total = 0
    for doc in docs:
        source = doc.metadata.get('source_name', 'Không rõ nguồn')
        page = doc.metadata.get('page_number', '?')
        block = f'[{source} - trang {page}]\n{doc.page_content}'
        total += len(block)
        if total > max_chars:
            break
        blocks.append(block)
    return '\n\n'.join(blocks) if blocks else 'KHÔNG CÓ DỮ LIỆU' 

# gom danh sách nguồn
def build_sources_summary(docs: List[Document]) -> str:
    return summarize_sources(docs)
