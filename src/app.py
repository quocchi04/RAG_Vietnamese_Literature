from __future__ import annotations

import sys
from pathlib import Path

# Đưa thư mục gốc project vào Python path để Streamlit Cloud import được package src
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import List, Optional, Tuple

from src.ingest.loader import load_documents
from src.ingest.chunker import split_documents
from src.pipeline.rag_pipeline import LiteratureRAGPipeline, RAGResponse
from src.retrieval.indexer import load_vector_store, build_vector_store
from src.utils.config import GRADIO_DESCRIPTION, GRADIO_TITLE, GROQ_API_KEY

EXAMPLES = [
    'Tác phẩm Chí Phèo do ai sáng tác?',
    'Thị Nỡ là ai?',
    'Chí Phèo là người như thế nào?'
]

# =========================================================
# PHẦN DÙNG CHUNG CHO GRADIO VÀ STREAMLIT
# =========================================================
def build_rag_pipeline() -> Tuple[LiteratureRAGPipeline, List[str], Optional[int]]:
    """
    Khởi tạo RAG pipeline một lần:
    - đọc danh sách tài liệu trong data/raw
    - load Chroma vector store trong data/vector_store
    - tạo LiteratureRAGPipeline để hỏi đáp
    """
    if not GROQ_API_KEY:
        raise RuntimeError(
            'Chưa tìm thấy GROQ_API_KEY. Hãy tạo file .env ở thư mục gốc dự án và thêm: GROQ_API_KEY=your_key'
        )

    documents = load_documents()
    if not documents:
        raise RuntimeError('Thư mục data/raw chưa có tài liệu .pdf hoặc .txt để nạp vào hệ thống.')

    available_sources = sorted({doc.metadata['source_name'] for doc in documents})
    vectorstore = load_vector_store()

    vector_count: Optional[int] = None
    try:
        vector_count = vectorstore._collection.count()
    except Exception:
        vector_count = None

    if vector_count == 0:
        raise RuntimeError(
            'Vector store đang rỗng. Hãy chạy lệnh: python -m src.retrieval.indexer trước khi mở giao diện.'
        )

    rag = LiteratureRAGPipeline(vectorstore, available_sources)
    return rag, available_sources, vector_count


def format_rag_response(response: RAGResponse) -> str:
    answer = response.answer.strip()

    if response.sources and '[Nguồn:' not in answer:
        answer += f'\n\n**Nguồn truy xuất:** {response.sources}'

    return answer

# =========================================================
# XỬ LÝ FILE UPLOAD VÀ TẠO PIPELINE MỚI
def load_uploaded_file_to_documents(uploaded_file):
    """
    Đọc file người dùng upload trong Streamlit.
    Hỗ trợ PDF và TXT.
    Trả về list Document giống loader mặc định của project.
    """
    import tempfile

    from langchain_community.document_loaders import PyPDFLoader
    from langchain_core.documents import Document

    from src.ingest.cleaner import normalize_text, slugify_vi
    from src.utils.config import DEFAULT_ENCODING

    file_name = uploaded_file.name
    suffix = Path(file_name).suffix.lower()
    source_name = Path(file_name).stem
    source_slug = slugify_vi(source_name)

    if suffix == '.pdf':
        temp_dir = Path(tempfile.mkdtemp(prefix='rag_uploaded_raw_'))
        temp_path = temp_dir / file_name
        temp_path.write_bytes(uploaded_file.getvalue())

        loader = PyPDFLoader(str(temp_path))
        pages = loader.load()

        for page in pages:
            page.page_content = normalize_text(page.page_content)
            page.metadata.update(
                {
                    'source_file': file_name,
                    'source_name': source_name,
                    'source_slug': source_slug,
                    'page_number': int(page.metadata.get('page', 0)) + 1,
                }
            )

        return pages

    if suffix == '.txt':
        raw_bytes = uploaded_file.getvalue()
        try:
            text = raw_bytes.decode(DEFAULT_ENCODING)
        except UnicodeDecodeError:
            text = raw_bytes.decode('utf-8', errors='ignore')

        text = normalize_text(text)

        return [
            Document(
                page_content=text,
                metadata={
                    'source_file': file_name,
                    'source_name': source_name,
                    'source_slug': source_slug,
                    'page_number': 1,
                },
            )
        ]

    raise RuntimeError('Chỉ hỗ trợ file PDF hoặc TXT.')


def build_rag_pipeline_with_uploaded_file(uploaded_file) -> Tuple[LiteratureRAGPipeline, List[str], Optional[int]]:
    """
    Tạo pipeline mới chỉ từ file người dùng upload.

    Khi upload file mới:
    - không dùng tài liệu mẫu trong data/raw
    - chỉ hỏi đáp trên file upload
    - vector store là tạm thời, không ghi đè data/vector_store gốc
    """
    import tempfile

    if not GROQ_API_KEY:
        raise RuntimeError('Chưa tìm thấy GROQ_API_KEY.')

    uploaded_documents = load_uploaded_file_to_documents(uploaded_file)
    chunks = split_documents(uploaded_documents)

    if not chunks:
        raise RuntimeError('Không tạo được chunk nào từ tài liệu upload.')

    temp_vector_dir = Path(tempfile.mkdtemp(prefix='rag_uploaded_vector_'))
    vectorstore = build_vector_store(chunks, db_dir=temp_vector_dir)

    available_sources = sorted({doc.metadata['source_name'] for doc in uploaded_documents})

    vector_count: Optional[int] = None
    try:
        vector_count = vectorstore._collection.count()
    except Exception:
        vector_count = None

    rag = LiteratureRAGPipeline(vectorstore, available_sources)
    return rag, available_sources, vector_count

# =========================================================
# CHẠY BẰNG GRADIO: python src/app.py
# =========================================================
def build_gradio_app():
    import gradio as gr

    rag, available_sources, vector_count = build_rag_pipeline()

    def chat(message, history):
        _ = history  # pipeline hiện tại xử lý từng câu hỏi độc lập, không dùng lịch sử hội thoại
        if not message or not message.strip():
            return 'Bạn hãy nhập câu hỏi về tài liệu văn học.'
        response = rag.ask(message.strip())
        return format_rag_response(response)

    description = GRADIO_DESCRIPTION
    if vector_count is not None:
        description += f'\n\nĐã nạp {len(available_sources)} nguồn tài liệu, {vector_count} vector chunks.'

    return gr.ChatInterface(
        fn=chat,
        title=GRADIO_TITLE,
        description=description,
        examples=EXAMPLES,
    )


# =========================================================
# CHẠY BẰNG STREAMLIT: streamlit run src/app.py
# =========================================================
def run_streamlit_app() -> None:
    import streamlit as st

    st.set_page_config(
        page_title=GRADIO_TITLE,
        page_icon='📚',
        layout='wide',
    )
    st.markdown(
        """
        <style>
        /* Nền tổng thể */
        .stApp {
            background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 45%, #fff7ed 100%);
        }

        /* Khối nội dung chính */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e5e7eb;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #1f2937;
        }

        /* Hero box */
        .hero-card {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(226, 232, 240, 0.9);
            border-radius: 26px;
            padding: 34px 38px;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
            margin-bottom: 28px;
        }

        .hero-title {
            font-size: 44px;
            font-weight: 800;
            letter-spacing: -0.04em;
            color: #111827;
            margin-bottom: 10px;
        }

        .hero-subtitle {
            font-size: 17px;
            line-height: 1.7;
            color: #4b5563;
            max-width: 920px;
        }

        .badge-row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 18px;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 13px;
            border-radius: 999px;
            background: #eef2ff;
            color: #3730a3;
            font-size: 14px;
            font-weight: 600;
            border: 1px solid #c7d2fe;
        }

        /* Card thống kê */
        .metric-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 16px 18px;
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
            margin-bottom: 12px;
        }

        .metric-label {
            color: #6b7280;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .metric-value {
            color: #111827;
            font-size: 26px;
            font-weight: 800;
        }

        /* Nút */
        div.stButton > button {
            border-radius: 14px;
            border: 1px solid #cbd5e1;
            background: #ffffff;
            font-weight: 650;
            min-height: 44px;
            transition: all 0.2s ease;
        }

        div.stButton > button:hover {
            border-color: #6366f1;
            color: #4338ca;
            box-shadow: 0 8px 22px rgba(99, 102, 241, 0.18);
            transform: translateY(-1px);
        }

        /* File uploader */
        div[data-testid="stFileUploader"] {
            background: #f8fafc;
            border: 1px dashed #94a3b8;
            border-radius: 18px;
            padding: 12px;
        }

        /* Chat */
        div[data-testid="stChatMessage"] {
            border-radius: 18px;
            padding: 10px;
        }

        /* Input chat */
        div[data-testid="stChatInput"] {
            border-radius: 20px;
        }

        /* Expander */
        details {
            border-radius: 16px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    @st.cache_resource(show_spinner=False)
    def get_cached_pipeline() -> Tuple[LiteratureRAGPipeline, List[str], Optional[int]]:
        return build_rag_pipeline()

    st.title('📚 ' + GRADIO_TITLE)
    st.write(GRADIO_DESCRIPTION)

    with st.spinner('Đang tải mô hình embedding, vector store và pipeline RAG...'):
        try:
            rag, available_sources, vector_count = get_cached_pipeline()
        except Exception as exc:
            st.error(str(exc))
            st.info(
                'Kiểm tra lại: file .env, thư mục data/raw, và vector store. '
                'Sau khi thêm tài liệu, hãy chạy: python -m src.retrieval.indexer'
            )
            st.stop()

    # Lưu pipeline vào session_state để tái sử dụng khi upload file mới
    if 'custom_pipeline' not in st.session_state:
        st.session_state.custom_pipeline = None

    if st.session_state.custom_pipeline is not None:
        rag, available_sources, vector_count = st.session_state.custom_pipeline

    
    with st.sidebar:
        st.markdown("## 📤 Tài liệu")

        if st.session_state.custom_pipeline is not None:
            st.success("Đang dùng tài liệu mẫu + file upload.")
        else:
            st.info("Đang dùng 2 tài liệu mẫu mặc định.")

        uploaded_file = st.file_uploader(
            "Tải thêm PDF hoặc TXT",
            type=["pdf", "txt"],
            accept_multiple_files=False,
            help="File upload sẽ được đọc, chia chunk, embedding và tạo vector store tạm.",
        )

        if uploaded_file is not None:
            st.caption(f"Đã chọn: **{uploaded_file.name}**")

        process_upload = st.button(
            "🚀 Xử lý tài liệu",
            disabled=uploaded_file is None,
            use_container_width=True,
        )

        reset_default = st.button(
            "↩️ Quay về tài liệu mẫu",
            use_container_width=True,
        )

        if process_upload and uploaded_file is not None:
            with st.spinner("Đang đọc file, chia chunk, embedding và tạo vector store tạm..."):
                try:
                    st.session_state.custom_pipeline = build_rag_pipeline_with_uploaded_file(uploaded_file)
                    st.session_state.messages = []
                    st.success(f"Đã nạp thêm file: {uploaded_file.name}")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Lỗi khi xử lý file upload: {exc}")

        if reset_default:
            st.session_state.custom_pipeline = None
            st.session_state.messages = []
            st.rerun()

        st.divider()

        st.markdown("## 📊 Hệ thống")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Nguồn", len(available_sources))
        with col2:
            st.metric("Chunks", vector_count if vector_count is not None else "?")

        with st.expander("📚 Danh sách nguồn", expanded=False):
            for source in available_sources:
                st.write("• " + source)

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    st.markdown("## 💬 Hỏi đáp tài liệu")

    cols = st.columns(len(EXAMPLES))
    selected_example = None
    for idx, example in enumerate(EXAMPLES):
        if cols[idx].button(example, use_container_width=True):
            selected_example = example

    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])

    user_question = st.chat_input('Nhập câu hỏi về tác phẩm, nhân vật, chi tiết văn học...')
    question = user_question or selected_example

    if question:
        question = question.strip()
        st.session_state.messages.append({'role': 'user', 'content': question})
        with st.chat_message('user'):
            st.markdown(question)

        with st.chat_message('assistant'):
            with st.spinner('Đang truy xuất ngữ cảnh và sinh câu trả lời...'):
                try:
                    response = rag.ask(question)
                    answer = format_rag_response(response)
                except Exception as exc:
                    answer = f'Có lỗi khi xử lý câu hỏi: {exc}'
                    response = None

            st.markdown(answer)

            if response and response.documents:
                with st.expander('Xem các đoạn tài liệu đã truy xuất'):
                    for i, doc in enumerate(response.documents, start=1):
                        source = doc.metadata.get('source_name', 'Không rõ nguồn')
                        page = doc.metadata.get('page_number', '?')
                        st.markdown(f'**Đoạn {i}: {source} - trang {page}**')
                        st.write(doc.page_content)

        st.session_state.messages.append({'role': 'assistant', 'content': answer})


# =========================================================
# TỰ NHẬN DIỆN MÔI TRƯỜNG CHẠY
# =========================================================
def is_running_in_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except Exception:
        return False


if is_running_in_streamlit():
    run_streamlit_app()
elif __name__ == '__main__':
    demo = build_gradio_app()
    demo.launch(inbrowser=True)
