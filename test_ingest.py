import os
from app.services.pdf_service import extract_text_from_pdf, chunk_text
from app.services.embedding_service import embed_text
from app.services.vector_service import vector_db, cosine_similarity

# ✅ 取得專案根目錄
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ 組 PDF 路徑
pdf_path = os.path.join(BASE_DIR, "report", "2024", "tsmc.pdf")

print(f"📂 PDF 路徑: {pdf_path}")

# 1️⃣ 讀 PDF
text = extract_text_from_pdf(pdf_path)

# 2️⃣ 切 chunk
chunks = chunk_text(text)
print(f"總 chunk 數: {len(chunks)}")

# 3️⃣ embedding + 存
for chunk in chunks[:20]:  # 先限制 20 段避免太慢
    vector = embed_text(chunk)

    vector_db.append({
        "text": chunk,
        "embedding": vector
    })

print("✅ ingestion 完成")

# 4️⃣ 測試 query
query = "governance risk"
query_vec = embed_text(query)

scores = []
for item in vector_db:
    sim = cosine_similarity(query_vec, item["embedding"])
    scores.append((sim, item["text"]))

scores.sort(reverse=True)

print("\n🔥 最相關段落:\n")
for s in scores[:3]:
    print(s[1])
    print("------")