"""
Các hàm phụ trợ dùng lại ở nhiều module.

Bao gồm:
- tạo thư mục nếu chưa có
- lưu / đọc JSON
- gom nguồn tài liệu đã retrieve
- kiểm tra dữ liệu đầu vào
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from langchain_core.documents import Document


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(data, path: Path) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def load_json(path: Path, default=None):
    if not path.exists():
        return [] if default is None else default
    return json.loads(path.read_text(encoding='utf-8'))


def summarize_sources(docs: Iterable[Document], limit: int = 4) -> str:
    seen = []
    for doc in docs:
        item = (
            doc.metadata.get('source_name', 'Không rõ nguồn'),
            doc.metadata.get('page_number', '?'),
        )
        if item not in seen:
            seen.append(item)
    return '; '.join([f'{name} - trang {page}' for name, page in seen[:limit]])


def documents_to_dicts(docs: Iterable[Document]) -> List[dict]:
    return [
        {
            'page_content': doc.page_content,
            'metadata': dict(doc.metadata),
        }
        for doc in docs
    ]


def validate_raw_data_dir(data_dir: Path) -> None:
    if not data_dir.exists():
        raise FileNotFoundError(f'Không tìm thấy thư mục dữ liệu: {data_dir}')
