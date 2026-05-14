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
    'Tóm tắt tác phẩm Chí Phèo.',
    'Lão Hạc có những phẩm chất gì?',
    'Tác giả của Chí Phèo là ai?',
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
    """Định dạng câu trả lời để dùng chung cho giao diện chat."""
    answer = response.answer.strip()
    if response.sources and response.sources not in answer:
        answer += f'\n\n**Nguồn truy xuất:** {response.sources}'
    return answer


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

    with st.sidebar:
        st.header('Thông tin hệ thống')
        st.write(f'**Số nguồn tài liệu:** {len(available_sources)}')
        if vector_count is not None:
            st.write(f'**Số vector chunks:** {vector_count}')

        with st.expander('Danh sách nguồn'):
            for source in available_sources:
                st.write('- ' + source)

        if st.button('Tải lại pipeline'):
            st.cache_resource.clear()
            st.rerun()

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    st.subheader('Hỏi đáp')

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
