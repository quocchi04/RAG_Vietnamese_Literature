import gradio as gr

from src.ingest.loader import load_documents
from src.pipeline.rag_pipeline import LiteratureRAGPipeline
from src.retrieval.indexer import load_vector_store
from src.utils.config import GRADIO_DESCRIPTION, GRADIO_TITLE


def build_app():
    documents = load_documents()
    available_sources = sorted({doc.metadata['source_name'] for doc in documents})
    vectorstore = load_vector_store()
    rag = LiteratureRAGPipeline(vectorstore, available_sources)

    def chat(message, history):
        _ = history                         # không dùng lịch sử hội thoại, mỗi câu hỏi đều được xử lý độc lập
        response = rag.ask(message)
        return response.answer
    # mẫu câu hỏi để người dùng dễ hình dung cách hỏi
    examples = [
        'Tóm tắt tác phẩm Chí Phèo.',
        'Lão Hạc có những phẩm chất gì?',
        'Tác giả của Chí Phèo là ai?',
    ]

    return gr.ChatInterface(
        fn=chat,                            # mỗi lần nhập -> gọi hàm chat -> gọi RAG pipeline
        title=GRADIO_TITLE,
        description=GRADIO_DESCRIPTION,
        examples=examples,
    )


if __name__ == '__main__':
    demo = build_app()
    demo.launch(inbrowser=True)
