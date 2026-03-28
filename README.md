# RAG hỏi đáp văn học Việt Nam

Project này refactor lại notebook RAG thành cấu trúc module rõ ràng hơn để dễ đọc, dễ bảo trì và dễ trình bày trong báo cáo.

## Cấu trúc thư mục

```text
RAG/
├── data/
│   ├── raw/                  # dữ liệu gốc: PDF/TXT/DOCX
│   ├── processed/            # text/chunk đã xử lý, có thể lưu JSON để debug
│   └── vector_store/         # Chroma DB hoặc vector index đã persist
│
├── src/
│   ├── ingest/
│   │   ├── loader.py         # đọc file đầu vào và gắn metadata
│   │   ├── cleaner.py        # làm sạch, chuẩn hóa tiếng Việt
│   │   └── chunker.py        # chia chunk cho retrieval
│   │
│   ├── embedding/
│   │   └── embedder.py       # khởi tạo embedding model
│   │
│   ├── retrieval/
│   │   ├── indexer.py        # build/load Chroma vector store
│   │   └── retriever.py      # retrieve top-k, ưu tiên lọc theo tác phẩm
│   │
│   ├── generation/
│   │   ├── prompt.py         # prompt system và prompt answer
│   │   └── generator.py      # gọi LLM để sinh câu trả lời
│   │
│   ├── pipeline/
│   │   └── rag_pipeline.py   # ghép retrieve + generate thành pipeline hoàn chỉnh
│   │
│   ├── evaluation/
│   │   └── evaluate.py       # script đánh giá đơn giản cho retrieval/answer
│   │
│   ├── utils/
│   │   ├── config.py         # cấu hình chung toàn project
│   │   └── helpers.py        # hàm phụ trợ xử lý metadata và I/O
│   │
│   └── app.py                # giao diện Gradio
│
├── tests/
├── notebooks/
├── .env
├── requirements.txt
└── README.md
```

## Những gì đã tối ưu

### 1. Tách notebook thành module rõ chức năng
Notebook ban đầu có nhiều cell lặp và khó bảo trì. Bản này tách thành từng phần riêng:
- ingest dữ liệu
- embedding
- retrieval
- generation
- pipeline
- evaluation

### 2. Không build lại DB mỗi lần mở app
- `src/retrieval/indexer.py` chịu trách nhiệm build/load index
- `src/app.py` chỉ load DB để chạy hỏi đáp

### 3. Tối ưu chunk cho văn bản văn học
Chunk được chia với separator thân thiện với đoạn văn tự nhiên, giữ ngữ nghĩa tốt hơn cho truy vấn kiểu tóm tắt, phân tích nhân vật, tìm chi tiết.

### 4. Chuẩn hóa tiếng Việt và metadata
Text được normalize Unicode, xóa khoảng trắng thừa và gắn metadata:
- `source_file`
- `source_name`
- `source_slug`
- `page_number`
- `chunk_id`

### 5. Lọc theo tên tác phẩm khi người dùng hỏi trực tiếp
Nếu câu hỏi chứa tên như `Chí Phèo`, `Lão Hạc`, retriever sẽ ưu tiên lọc theo đúng tài liệu đó trước khi search.

### 6. Giảm trùng lặp kết quả retrieve
Retriever dùng `mmr` để top-k đa dạng hơn, bớt lặp chunk giống nhau.

### 7. Prompt chặt để giảm hallucination
Model chỉ được trả lời theo context đã retrieve. Không đủ dữ liệu thì trả về câu cố định.

### 8. Có module evaluation để viết báo cáo dễ hơn
`src/evaluation/evaluate.py` cho phép chạy một tập câu hỏi mẫu và thống kê đơn giản.

## Note mô tả nhanh từng file

- `src/ingest/loader.py`: đọc PDF/TXT và chuẩn hóa về `Document`.
- `src/ingest/cleaner.py`: làm sạch text, chuẩn hóa tiếng Việt và slug.
- `src/ingest/chunker.py`: chia chunk, loại chunk rỗng hoặc trùng.
- `src/embedding/embedder.py`: tạo embedding model dùng chung.
- `src/retrieval/indexer.py`: build/load vector store Chroma.
- `src/retrieval/retriever.py`: truy xuất top-k và format context.
- `src/generation/prompt.py`: định nghĩa system prompt và answer template.
- `src/generation/generator.py`: gọi Groq LLM để tạo câu trả lời.
- `src/pipeline/rag_pipeline.py`: pipeline hoàn chỉnh cho hệ thống RAG.
- `src/evaluation/evaluate.py`: đánh giá thử nghiệm bằng danh sách query.
- `src/utils/config.py`: đường dẫn, tên model, chunk size, retrieval k.
- `src/utils/helpers.py`: save/load JSON, gom nguồn, kiểm tra dữ liệu.
- `src/app.py`: giao diện Gradio.

## Cách dùng

### 1. Cài thư viện

```bash
pip install -r requirements.txt
```

### 2. Chuẩn bị dữ liệu
Đặt file PDF vào thư mục:

```text
data/raw/
```

Ví dụ:
- `data/raw/Chí_Phèo.pdf`
- `data/raw/Lão_Hạc.pdf`

### 3. Tạo file `.env`

```env
GROQ_API_KEY=your_api_key
GROQ_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
CHUNK_SIZE=800
CHUNK_OVERLAP=120
RETRIEVER_K=6
MMR_FETCH_K=20
```

### 4. Build index

```bash
python -m src.retrieval.indexer
```

### 5. Chạy app

```bash
python -m src.app
```

## Gợi ý mở rộng tiếp
- thêm reranker
- thêm hybrid search BM25 + dense
- thêm memory hội thoại
- thêm trích dẫn nguyên văn theo chunk
- thêm bộ test câu hỏi đánh giá chính thức
