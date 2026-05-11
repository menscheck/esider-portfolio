import os
import json
import time
import torch
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

def load_model():
    """Load the sentence transformer model with GPU support."""
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"使用裝置: {device}")
        model = SentenceTransformer('BAAI/bge-m3', device=device)
        print('模型載入成功')
        return model, device
    except Exception as e:
        print(f'模型載入失敗: {e}')
        return None, None

def connect_mongodb():
    """Connect to MongoDB (use config.ini so retriever+embedder point to same DB)."""
    try:
        import configparser

        from pathlib import Path

        cp = configparser.ConfigParser()
        config_path = Path(__file__).resolve().parents[2] / "config.ini"
        cp.read(str(config_path), encoding="utf-8")

        mongo_uri = cp["mongodb"]["uri"]
        db_name = cp["mongodb"].get("db_name", "esg_db")
        collection_name = cp["mongodb"].get("collection_name", "chunks")

        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        collection = db[collection_name]
        client.admin.command("ping")

        print("MongoDB連線成功", f"db={db_name}", f"collection={collection_name}")
        return collection
    except Exception as e:
        print(f"MongoDB連線失敗: {e}")
        return None

def load_chunks(chunks_dir, company=None):
    """Load chunk JSON files from data/chunks."""
    if not os.path.isdir(chunks_dir):
        raise FileNotFoundError(f'Chunks 目錄不存在: {chunks_dir}')

    file_paths = []
    if company:
        file_paths.append(os.path.join(chunks_dir, f'{company}.json'))
    else:
        for filename in os.listdir(chunks_dir):
            if filename.lower().endswith('.json'):
                file_paths.append(os.path.join(chunks_dir, filename))

    chunks_data = []
    for path in file_paths:
        if not os.path.exists(path):
            print(f'檔案不存在，跳過: {path}')
            continue
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                chunks_data.extend(data)
            else:
                print(f'意外的 JSON 結構，預期 list: {path}')

    return chunks_data


def process_chunks(model, device, collection, chunks_data, max_chunks: int | None = None):
    """Upsert chunk metadata into MongoDB (optionally also write embeddings)."""
    start_time = time.time()
    upserted_count = 0

    if max_chunks is not None:
        chunks_data = chunks_data[:max_chunks]

    write_embedding_env = os.getenv("ESG_EMBEDDER_WRITE_EMBEDDING", "0").strip()
    write_embedding = write_embedding_env == "1"

    # Process in batches for better throughput
    batch_size = 256
    for i in range(0, len(chunks_data), batch_size):
        batch = chunks_data[i:i + batch_size]
        valid_chunks = []

        for chunk in batch:
            text = chunk.get("text", "")
            if not text:
                continue
            # 只需要 metadata 時，不需要額外預處理
            valid_chunks.append(chunk)

        if not valid_chunks:
            continue

        embeddings = None
        if write_embedding:
            batch_texts = [c.get("text", "") for c in valid_chunks]
            embeddings = model.encode(
                batch_texts,
                batch_size=batch_size,
                device=device,
                show_progress_bar=False,
                convert_to_numpy=True,
            )

        for idx, chunk in enumerate(valid_chunks):
            chunk_id = chunk.get("chunk_id")
            doc = {
                "company": chunk.get("company"),
                "source": chunk.get("source"),
                "page": chunk.get("page"),
                "chunk_id": chunk_id,
                "text": chunk.get("text", ""),
            }
            if write_embedding:
                embedding = embeddings[idx]
                doc["embedding"] = (
                    embedding.tolist() if hasattr(embedding, "tolist") else embedding
                )

            try:
                collection.update_one(
                    {"chunk_id": chunk_id},
                    {"$set": doc},
                    upsert=True,
                )
                upserted_count += 1
            except Exception as e:
                print(f"寫入失敗 {chunk_id}: {e}")

        print(
            f"已處理批次 {i//batch_size + 1}/{(len(chunks_data) + batch_size - 1)//batch_size}",
            f"write_embedding={write_embedding}",
        )

    elapsed_time = time.time() - start_time
    chunks_per_second = len(chunks_data) / elapsed_time if elapsed_time > 0 else 0.0

    print(f'處理速度: {chunks_per_second:.2f} chunk/秒')
    print(f'MongoDB寫入成功: {upserted_count} 筆')
    try:
        total_count = collection.count_documents({})
        print(f'寫入筆數確認: {total_count} 筆')
    except Exception as e:
        print(f'確認寫入筆數失敗: {e}')

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    chunks_dir = os.path.join(base_dir, 'data', 'chunks')

    # 是否需要 embedding（metadata-only 可跳過模型載入，加速）
    write_embedding_env = os.getenv("ESG_EMBEDDER_WRITE_EMBEDDING", "0").strip()
    write_embedding = write_embedding_env == "1"

    model = None
    device = None
    if write_embedding:
        model, device = load_model()
        if not model:
            return

    # Connect to MongoDB
    collection = connect_mongodb()
    if collection is None:
        return

    # 可用參數：company / max_chunks
    company = os.getenv("ESG_EMBEDDER_COMPANY", "台積電")
    if company.strip() == "__ALL__":
        company = None

    max_chunks_env = os.getenv("ESG_EMBEDDER_MAX_CHUNKS", "").strip()
    max_chunks = int(max_chunks_env) if max_chunks_env.isdigit() else None

    chunks_data = load_chunks(chunks_dir, company=company)
    print(f'載入 {len(chunks_data)} 個 chunks', f'company={company}', f'max_chunks={max_chunks}')

    if not chunks_data:
        return

    process_chunks(model, device, collection, chunks_data, max_chunks=max_chunks)

if __name__ == "__main__":
    main()
