"""
Script đánh giá đơn giản cho hệ thống RAG.

Mục đích:
- thử một tập câu hỏi mẫu
- xem hệ thống trả lời gì
- xem retrieve được nguồn nào

Đây là bản đánh giá nhẹ để dễ viết báo cáo. Sau này có thể mở rộng thành
bộ benchmark chuẩn với expected answer và metrics cụ thể.
"""

from __future__ import annotations

from src.ingest.loader import load_documents
from src.pipeline.rag_pipeline import LiteratureRAGPipeline
from src.retrieval.indexer import load_vector_store


SAMPLE_QUESTIONS = [
    'Tóm tắt tác phẩm Chí Phèo.',
    'Lão Hạc có những phẩm chất gì?',
    'Người bạn thân của Lão Hạc là ai?',
]


def main() -> None:
    documents = load_documents()
    available_sources = sorted({doc.metadata['source_name'] for doc in documents})
    vectorstore = load_vector_store()
    pipeline = LiteratureRAGPipeline(vectorstore, available_sources)

    for idx, question in enumerate(SAMPLE_QUESTIONS, start=1):
        result = pipeline.ask(question)
        print(f'\n===== CASE {idx} =====')
        print('Q:', question)
        print('A:', result.answer)
        print('Sources:', result.sources or 'Không có nguồn')


if __name__ == '__main__':
    main()
