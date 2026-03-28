from __future__ import annotations

import re
import unicodedata

# clean text
def normalize_text(text: str) -> str:
    text = unicodedata.normalize('NFC', text or '')
    text = text.replace('\x00', ' ')
    text = re.sub(r'\s+', ' ', text).strip() # gộp khoảng trắng, xóa khoảng trắng đầu cuối
    return text

# tạo tên slug không dấu để so sánh tên tác phẩm khi tìm kiếm
def slugify_vi(text: str) -> str:
    text = unicodedata.normalize('NFD', text or '')
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn') # loại bỏ dấu tiếng Việt
    text = text.replace('đ', 'd').replace('Đ', 'D')
    text = re.sub(r'[^\w\s-]', ' ', text.lower())
    text = re.sub(r'[_\s-]+', '_', text).strip('_')
    return text

# xử lý text để so sánh khi tìm kiếm, tương tự slug nhưng giữ nguyên khoảng trắng để match tốt hơn
def normalize_for_match(text: str) -> str:
    text = unicodedata.normalize('NFD', text or '')
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    text = text.lower().replace('đ', 'd')
    return re.sub(r'[^\w\s]', ' ', text)
