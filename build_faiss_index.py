import json
import numpy as np
import faiss
from pathlib import Path
from pymongo import MongoClient

# 設定
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "esg_db"
COLLECTION_NAME = "chunks"
FAISS_DIR = Path("data/faiss_index")
INDEX_PATH = FAISS_DIR / "esg.index"
ID_MAP_PATH = FAISS_DIR / "id_map.json"

FAISS_DIR.mkdir(parents=True, exist_ok=True)

# 從 MongoDB 讀取所有 embedding
client = MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION_NAME]

print("讀取 MongoDB chunks...")
total = collection.count_documents({"embedding": {"$exists": True}})
print(f"有 embedding 的 chunk 數: {total}")

embeddings = []
id_map = []

cursor = collection.find(
    {"embedding": {"$exists": True}},
    {"chunk_id": 1, "embedding": 1, "_id": 0}
)

for i, doc in enumerate(cursor):
    embeddings.append(doc["embedding"])
    id_map.append(doc["chunk_id"])
    if (i + 1) % 1000 == 0:
        print(f"  讀取中... {i+1}/{total}")

print(f"共讀取 {len(embeddings)} 筆")

# 建 FAISS index
vectors = np.array(embeddings, dtype=np.float32)
dim = vectors.shape[1]
print(f"向量維度: {dim}")

index = faiss.IndexFlatL2(dim)
index.add(vectors)
print(f"FAISS index 建立完成，向量數: {index.ntotal}")

# 存檔
faiss.write_index(index, str(INDEX_PATH))
with open(ID_MAP_PATH, "w", encoding="utf-8") as f:
    json.dump(id_map, f, ensure_ascii=False)

print(f"已存：{INDEX_PATH}")
print(f"已存：{ID_MAP_PATH}")
client.close()
