# Sơ đồ cấu trúc hoạt động của project 
### 1. Sơ đồ tổng quát
~~~
Người dùng đặt câu hỏi
        │
        ▼
[1] Nhận câu hỏi
        │
        ▼
[2] Tiền xử lý câu hỏi
- làm sạch câu hỏi
- nhận diện tên tác phẩm / chủ đề
        │
        ▼
[3] Truy xuất dữ liệu liên quan
- tìm trong vector store
- ưu tiên lọc theo tác phẩm nếu có
        │
        ▼
[4] Lấy ra top-k đoạn văn phù hợp nhất
        │
        ▼
[5] Ghép prompt
- câu hỏi người dùng
- ngữ cảnh được truy xuất
- hướng dẫn trả lời
        │
        ▼
[6] Gọi LLM sinh câu trả lời
        │
        ▼
[7] Trả kết quả cho người dùng
~~~
### Output:
- câu trả lời
- nguồn tham chiếu (nếu có)
### 2. Sơ đồ đầy đủ từ lúc nạp dữ liệu đến lúc trả lời
~~~
                ┌──────────────────────────┐
                │   Dữ liệu gốc (PDF/TXT)  │
                │ Chí Phèo, Lão Hạc, ca dao│
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │       Loader             │
                │ Đọc file và trích xuất   │
                │ nội dung văn bản         │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │       Cleaner            │
                │ Làm sạch, chuẩn hóa text │
                │ bỏ ký tự thừa            │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │       Chunker            │
                │ Chia văn bản thành các   │
                │ đoạn nhỏ (chunk)         │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │       Embedder           │
                │ Chuyển từng chunk thành  │
                │ vector embedding         │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │      Vector Store        │
                │ Lưu embedding + metadata │
                │ (Chroma / FAISS)         │
                └────────────┬─────────────┘
                             │
                 ────────────┼────────────────
                             │
                             ▼
                ┌──────────────────────────┐
                │  Người dùng nhập câu hỏi │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │      Retriever           │
                │ Tìm các chunk liên quan  │
                │ nhất với câu hỏi         │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │      Prompt Builder      │
                │ Ghép question + context  │
                │ + hướng dẫn trả lời      │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │       Generator          │
                │ Gọi LLM sinh câu trả lời │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │      Kết quả trả về      │
                │ Câu trả lời + nguồn      │
                └──────────────────────────┘
  ~~~
### 3. Sơ đồ theo đúng cấu trúc source bạn đang dùng
~~~data/raw
   │
   ▼
src/ingest/loader.py
   │
   ▼
src/ingest/cleaner.py
   │
   ▼
src/ingest/chunker.py
   │
   ▼
src/embedding/embedder.py
   │
   ▼
src/retrieval/indexer.py
   │
   ▼
data/vector_store
   │
   ├───────────────────────────────┐
   │                               │
   ▼                               │
src/retrieval/retriever.py         │
   │                               │
   ▼                               │
src/generation/prompt.py           │
   │                               │
   ▼                               │
src/generation/generator.py        │
   │                               │
   ▼                               │
src/pipeline/rag_pipeline.py       │
   │                               │
   ▼                               │
src/app.py ◄───────────────────────┘
~~~
### 4. Luồng xử lý chi tiết
* **Giai đoạn 1:** Xây dựng cơ sở tri thức
Hệ thống nhận các file tác phẩm văn học như **PDF**, **TXT**.
Dữ liệu được đọc và chuyển thành văn bản thô.
Văn bản được làm sạch để loại bỏ nhiễu.
Sau đó hệ thống chia văn bản thành nhiều đoạn nhỏ.
Mỗi đoạn được chuyển thành vector embedding.
Các vector này được lưu vào vector database để phục vụ tìm kiếm ngữ nghĩa.
* **Giai đoạn 2:** Hỏi đáp
Người dùng nhập câu hỏi.
Hệ thống phân tích câu hỏi, có thể nhận diện tên tác phẩm.
Retriever tìm những đoạn văn bản liên quan nhất trong vector store.
Các đoạn này được đưa vào prompt làm ngữ cảnh.
LLM dựa trên ngữ cảnh để sinh câu trả lời.
Kết quả trả về cho người dùng là câu trả lời bám sát dữ liệu nguồn.
### 5. Điểm tối ưu

* **Thứ nhất,** hệ thống không để LLM trả lời tự do hoàn toàn, mà bắt buộc dựa trên dữ liệu tác phẩm đã nạp.

* **Thứ hai,** dữ liệu được chia chunk và embedding trước, nên tăng tốc độ truy xuất khi người dùng hỏi.

* **Thứ ba,** hệ thống có thể lọc theo tên tác phẩm, giúp tăng độ chính xác khi câu hỏi liên quan đến một bài cụ thể.

* **Thứ tư,** vector search giúp tìm theo ngữ nghĩa chứ không chỉ theo từ khóa, phù hợp với câu hỏi phân tích văn học.