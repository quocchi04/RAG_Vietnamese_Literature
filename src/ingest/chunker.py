from __future__ import annotations

from typing import Iterable, List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.ingest.cleaner import normalize_text
from src.utils.config import CHUNK_OVERLAP, CHUNK_SIZE, MIN_CHUNK_LENGTH


def split_documents(documents: Iterable[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=['\n\n', '\n', '. ', '? ', '! ', '; ', ', ', ' ', ''],    # thứ tự cắt
    )
    chunks = splitter.split_documents(list(documents))

    cleaned_chunks: List[Document] = []
    seen = set()
    for idx, chunk in enumerate(chunks):
        content = normalize_text(chunk.page_content)
        #lọc chun quá ngắn
        if len(content) < MIN_CHUNK_LENGTH:
            continue

        fingerprint = (
            chunk.metadata.get('source_file'),
            chunk.metadata.get('page_number'),
            content,
        )
        if fingerprint in seen:     #nếu trùng lặp thì bỏ qua
            continue
        seen.add(fingerprint)
        chunk.page_content = content
        chunk.metadata['chunk_id'] = idx  #gắn id cho mỗi chunk để dễ theo dõi
        cleaned_chunks.append(chunk)

    return cleaned_chunks