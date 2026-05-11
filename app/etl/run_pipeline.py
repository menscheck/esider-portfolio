import os
import sys
import json
import time
from typing import List, Dict, Any
import torch
print(f"[DEBUG] torch={torch.__version__}, CUDA={torch.cuda.is_available()}, device={'cuda' if torch.cuda.is_available() else 'cpu'}")
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
import logging

# 添加項目根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.vector_service import add_chunks

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ESGPipeline:
    def __init__(self):
        self.model = None
        self.mongo_client = None
        self.mongo_collection = None
        self.chunks_dir = "data/chunks"
        self.processed_count = 0
        self.start_time = time.time()

    def load_model(self):
        """載入 SentenceTransformer 模型，優先使用 GPU，沒有時 fallback 到 CPU"""
        logger.info("載入 SentenceTransformer 模型...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"選擇 device={device}")
        self.model = SentenceTransformer('BAAI/bge-m3', device=device)
        logger.info("模型載入完成")

    def connect_mongodb(self):
        """連接到 MongoDB"""
        import configparser as _cp, os as _os
        _cfg = _cp.ConfigParser()
        _cfg.read(_os.path.join(_os.path.dirname(__file__), '..', '..', 'config.ini'), encoding='utf-8')
        mongo_uri = _cfg.get('mongodb', 'uri', fallback='mongodb://localhost:27017')
        logger.info("連接到 MongoDB...")
        self.mongo_client = MongoClient(mongo_uri)
        db = self.mongo_client['esg_db']
        self.mongo_collection = db['chunks']
        logger.info("MongoDB 連接成功")

    def clear_mongodb(self):
        """清除 MongoDB 集合"""
        logger.info("清除 MongoDB esg_db.chunks 集合...")
        self.mongo_collection.drop()
        logger.info("MongoDB 集合已清除")

    def load_chunks(self) -> List[Dict[str, Any]]:
        """載入所有 chunks"""
        logger.info(f"從 {self.chunks_dir} 載入 chunks...")
        all_chunks = []

        if not os.path.exists(self.chunks_dir):
            raise FileNotFoundError(f"目錄 {self.chunks_dir} 不存在")

        json_files = [f for f in os.listdir(self.chunks_dir) if f.endswith('.json')]
        logger.info(f"找到 {len(json_files)} 個 JSON 文件")

        for filename in json_files:
            filepath = os.path.join(self.chunks_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    chunks = json.load(f)
                    all_chunks.extend(chunks)
                    logger.info(f"從 {filename} 載入 {len(chunks)} 個 chunks")
            except Exception as e:
                logger.error(f"載入 {filename} 時出錯: {e}")
                continue

        logger.info(f"總共載入 {len(all_chunks)} 個 chunks")
        return all_chunks

    def process_chunks(self, chunks: List[Dict[str, Any]]):
        """處理 chunks：生成 embeddings，存儲到 MongoDB 和 ChromaDB"""
        logger.info("開始處理 chunks...")

        batch_size = 100  # 每批處理 100 個 chunks
        total_chunks = len(chunks)

        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]

            # 準備數據
            texts = [chunk['text'] for chunk in batch]
            chunk_ids = [chunk['chunk_id'] for chunk in batch]

            # 生成 embeddings
            logger.info(f"生成第 {i+1} 到 {min(i+batch_size, total_chunks)} 個 chunks 的 embeddings...")
            embeddings = self.model.encode(texts)
            # 轉換為 list 格式
            embeddings = [emb.tolist() if hasattr(emb, 'tolist') else emb for emb in embeddings]

            # 存儲到 MongoDB（使用 upsert）
            mongo_docs = []
            for chunk, embedding in zip(batch, embeddings):
                doc = {
                    'company': chunk['company'],
                    'source': chunk['source'],
                    'page': chunk['page'],
                    'chunk_id': chunk['chunk_id'],
                    'text': chunk['text'],
                    'embedding': embedding
                }
                mongo_docs.append(doc)

            # 批量 upsert 到 MongoDB
            for doc in mongo_docs:
                self.mongo_collection.update_one(
                    {'chunk_id': doc['chunk_id']},
                    {'$set': doc},
                    upsert=True
                )

            # 存儲到 ChromaDB
            metadatas = [{
                'company': chunk['company'],
                'source': chunk['source'],
                'page': chunk['page'],
                'chunk_id': chunk['chunk_id']
            } for chunk in batch]

            add_chunks(texts, embeddings, metadatas)

            self.processed_count += len(batch)

            # 記錄進度
            elapsed_time = time.time() - self.start_time
            chunks_per_sec = self.processed_count / elapsed_time if elapsed_time > 0 else 0
            eta = (total_chunks - self.processed_count) / chunks_per_sec if chunks_per_sec > 0 else float('inf')
            logger.info(
                f"已處理 {self.processed_count}/{total_chunks} 個 chunks；"
                f"速率 {chunks_per_sec:.2f} chunks/s；"
                f"預估剩餘 {eta/60:.1f} 分鐘"
            )

    def run_pipeline(self):
        """執行完整的 ETL 管道"""
        try:
            logger.info("開始 ESG ETL 管道...")

            # 1. 載入模型
            self.load_model()

            # 2. 連接到 MongoDB
            self.connect_mongodb()

            # 3. 清除 MongoDB 集合
            self.clear_mongodb()

            # 4. 載入所有 chunks
            chunks = self.load_chunks()

            # 5. 處理 chunks
            self.process_chunks(chunks)

            # 6. 總結
            total_time = time.time() - self.start_time
            logger.info("ETL 管道完成！")
            logger.info(f"總處理時間: {total_time:.2f} 秒")
            logger.info(f"總 chunks 數: {self.processed_count}")
        except Exception as e:
            logger.error(f"ETL 管道執行失敗: {e}", exc_info=True)
            raise
        finally:
            if self.mongo_client:
                self.mongo_client.close()

def main():
    pipeline = ESGPipeline()
    pipeline.run_pipeline()

if __name__ == "__main__":
    main()