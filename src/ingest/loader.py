from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from src.ingest.cleaner import normalize_text, slugify_vi
from src.utils.config import DEFAULT_ENCODING, RAW_DATA_DIR, SUPPORTED_EXTENSIONS
from src.utils.helpers import validate_raw_data_dir


def _load_pdf(pdf_path: Path) -> List[Document]:
    # Đọc PDF thành nhiều Document, mỗi trang là một Document riêng biệt
    loader = PyPDFLoader(str(pdf_path)) 
    pages = loader.load()

    # Lấy tên file để làm source_name và source_slug 
    source_name = pdf_path.stem
    source_slug = slugify_vi(source_name)

    for page in pages:
        page.page_content = normalize_text(page.page_content) # Làm sạch nội dung của từng trang
        # Gắn metadata 
        page.metadata.update(
            {
                'source_file': pdf_path.name,
                'source_name': source_name,
                'source_slug': source_slug, # Tên tác phẩm dạng chuẩn hóa
                'page_number': int(page.metadata.get('page', 0)) + 1,
            }
        )
    return pages


def _load_txt(txt_path: Path) -> List[Document]:
    text = normalize_text(txt_path.read_text(encoding=DEFAULT_ENCODING)) # Dùng ecoding sẳn để làm sạch text 
    source_name = txt_path.stem     #txt thường chỉ có 1 page -> gắn page_number = 1
    return [
        Document(
            page_content=text,
            metadata={
                'source_file': txt_path.name,
                'source_name': source_name,
                'source_slug': slugify_vi(source_name),
                'page_number': 1,
            },
        )
    ]


def load_documents(data_dir: Path = RAW_DATA_DIR) -> List[Document]:
    validate_raw_data_dir(data_dir)
    documents: List[Document] = []  #tạo danh sách rỗng để chứa các Document sau khi load xong

    for path in sorted(data_dir.iterdir()):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if path.suffix.lower() == '.pdf':
            documents.extend(_load_pdf(path))
        elif path.suffix.lower() == '.txt':
            documents.extend(_load_txt(path))

    return documents