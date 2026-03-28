from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
VECTOR_STORE_DIR = DATA_DIR / 'vector_store'
NOTEBOOKS_DIR = BASE_DIR / 'notebooks'

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
MODEL_NAME = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

EMBEDDING_MODEL = os.getenv(
    'EMBEDDING_MODEL',
    'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
)

CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '800'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '120'))
MIN_CHUNK_LENGTH = int(os.getenv('MIN_CHUNK_LENGTH', '60'))
RETRIEVER_K = int(os.getenv('RETRIEVER_K', '6'))
MMR_FETCH_K = int(os.getenv('MMR_FETCH_K', '20'))
MAX_CONTEXT_CHARS = int(os.getenv('MAX_CONTEXT_CHARS', '3500'))

GRADIO_TITLE = 'RAG hỏi đáp văn học Việt Nam'
GRADIO_DESCRIPTION = (
    'Hệ thống hỏi đáp RAG cho tác phẩm văn học, ca dao và tài liệu học tập. '
    'Mô hình chỉ trả lời dựa trên nội dung đã nạp vào vector store.'
)

SUPPORTED_EXTENSIONS = {'.pdf', '.txt'}
DEFAULT_ENCODING = 'utf-8'
