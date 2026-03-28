"""
Pipeline RAG hoàn chỉnh cho hệ thống hỏi đáp.

Luồng xử lý:
question -> retrieve -> format context -> generate -> gắn nguồn
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.generation.generator import AnswerGenerator
from src.retrieval.retriever import (
    build_sources_summary,
    format_context,
    retrieve_with_scores,
)


@dataclass
class RAGResponse:
    answer: str
    sources: str
    documents: List


def is_bibliographic_question(question: str) -> bool:
    """
    Nhận diện các câu hỏi thiên về thông tin thư mục/tác giả.
    Với nhóm câu hỏi này, nếu tài liệu không nói rõ thì chỉ trả fallback,
    không bung các đoạn liên quan trong nội dung truyện.
    """
    q = question.lower().strip()
    keywords = [
        'ai sáng tác',
        'do ai sáng tác',
        'tác giả là ai',
        'ai là tác giả',
        'do ai viết',
        'của ai',
        'nhà văn nào sáng tác',
        'do nhà văn nào sáng tác',
    ]
    return any(k in q for k in keywords)


def deduplicate_docs(docs: List) -> List:
    """
    Loại bỏ các document trùng nhau để tránh hiện lặp chunk.
    """
    seen = set()
    unique_docs = []

    for doc in docs:
        key = (
            doc.metadata.get('source_name'),
            doc.metadata.get('page_number'),
            doc.page_content.strip(),
        )
        if key in seen:
            continue
        seen.add(key)
        unique_docs.append(doc)

    return unique_docs


class LiteratureRAGPipeline:
    def __init__(self, vectorstore, available_sources: List[str]):
        self.vectorstore = vectorstore
        self.available_sources = available_sources
        self.generator = AnswerGenerator()
        self.min_relevance_score = 0.35

    def ask(self, question: str) -> RAGResponse:
        docs_and_scores, detected_source = retrieve_with_scores(
            self.vectorstore,
            self.available_sources,
            question,
        )

        # Không có kết quả nào
        if not docs_and_scores:
            return RAGResponse(
                answer='Tôi không tìm thấy thông tin này trong tài liệu.',
                sources='',
                documents=[],
            )

        # Lọc theo ngưỡng điểm liên quan
        filtered_docs = [
            doc for doc, score in docs_and_scores
            if score is not None and score >= self.min_relevance_score
        ]

        # Nếu không detect được tác phẩm và cũng không có doc đủ liên quan
        # => coi như không có dữ liệu phù hợp
        if not detected_source and not filtered_docs:
            return RAGResponse(
                answer='Tôi không tìm thấy thông tin này trong tài liệu.',
                sources='',
                documents=[],
            )

        # Nếu detect được nguồn thì vẫn ưu tiên docs đã qua lọc score.
        # Nếu lọc xong rỗng nhưng có detect nguồn thì mới dùng tạm toàn bộ docs từ nguồn đó.
        if filtered_docs:
            docs = filtered_docs
        else:
            docs = [doc for doc, _ in docs_and_scores]

        # Bỏ doc trùng
        docs = deduplicate_docs(docs)

        context = format_context(docs)
        sources = build_sources_summary(docs)

        if context == 'KHÔNG CÓ DỮ LIỆU':
            return RAGResponse(
                answer='Tôi không tìm thấy thông tin này trong tài liệu.',
                sources='',
                documents=[],
            )

        answer = self.generator.generate(question=question, context=context)

        # Nếu model xác nhận không đủ dữ liệu
        if answer == 'Tôi không tìm thấy thông tin này trong tài liệu.':
            # Với câu hỏi kiểu tác giả / sáng tác / thư mục:
            # không bung đoạn nội dung truyện vì dễ gây hiểu lầm
            if is_bibliographic_question(question):
                return RAGResponse(
                    answer='Tôi không tìm thấy thông tin này trong tài liệu.',
                    sources='',
                    documents=[],
                )

            # Chỉ bung đoạn liên quan khi:
            # - có detect được đúng tác phẩm
            # - và đây không phải câu hỏi bibliographic
            if detected_source:
                fallback_answer = (
                    'Tôi không tìm thấy thông tin này trong tài liệu.\n\n'
                    f'--- ĐOẠN LIÊN QUAN ---\n{context}'
                )
                if sources:
                    fallback_answer += f'\n\n--- NGUỒN ---\n{sources}'

                return RAGResponse(
                    answer=fallback_answer,
                    sources=sources,
                    documents=docs,
                )

            return RAGResponse(
                answer='Tôi không tìm thấy thông tin này trong tài liệu.',
                sources='',
                documents=[],
            )

        return RAGResponse(
            answer=answer,
            sources=sources,
            documents=docs,
        )