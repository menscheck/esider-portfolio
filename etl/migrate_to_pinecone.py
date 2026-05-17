"""
app/etl/migrate_to_pinecone.py
將 MongoDB chunks + 本機 FAISS embeddings 遷移到 Pinecone
"""

import os
import sys
import json
import hashlib
import logging
import configparser
import numpy as np
from pymongo import MongoClient
from pinecone import Pinecone

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 讀取 config
cp = configparser.ConfigParser()
cp.read('config.ini', encoding='utf-8')

MONGO_URI    = cp['mongodb']['uri']
DB_NAME      = cp['mongodb']['db_name']
COLLECTION   = cp['mongodb']['collection_name']
PINECONE_KEY = cp['pinecone']['api_key']
INDEX_NAME   = cp['pinecone']['index_name']
FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'faiss_index', 'esg.index')
FAISS_ID_MAP_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'faiss_index', 'id_map.json')

BATCH_SIZE = 100

def load_faiss_embeddings():
    """載入 FAISS index 的所有向量"""
    import faiss
    logger.info("載入 FAISS index...")
    index = faiss.read_index(FAISS_INDEX_PATH)
    n = index.ntotal
    dim = index.d
    logger.info(f"FAISS: {n} 筆向量, {dim} 維")
    
    # 取出所有向量
    embeddings = np.zeros((n, dim), dtype=np.float32)
    index.reconstruct_n(0, n, embeddings)
    
    # 載入 id_map（List[chunk_id]，index位置對應FAISS向量位置）
    with open(FAISS_ID_MAP_PATH, 'r', encoding='utf-8') as f:
        id_map = json.load(f)  # list of chunk_ids
    return embeddings, id_map

def migrate():
    # 連線
    mongo_client = MongoClient(MONGO_URI)
    col = mongo_client[DB_NAME][COLLECTION]
    pc = Pinecone(api_key=PINECONE_KEY)
    index = pc.Index(INDEX_NAME)

    # 載入 FAISS
    embeddings, id_map = load_faiss_embeddings()
    
    # 反轉 id_map：chunk_id → faiss_position（id_map 是 List[chunk_id]）
    chunk_id_to_pos = {str(chunk_id): pos for pos, chunk_id in enumerate(id_map)}
    logger.info(f"id_map 筆數: {len(chunk_id_to_pos)}")

    # 從 MongoDB 取所有 chunks
    total = col.count_documents({})
    logger.info(f"MongoDB chunks: {total} 筆，開始遷移...")

    batch = []
    success = 0
    skip = 0

    for doc in col.find({}, {'_id':0, 'chunk_id':1, 'company':1, 'text':1, 'page':1, 'source':1}):
        chunk_id = str(doc.get('chunk_id', ''))
        
        if chunk_id not in chunk_id_to_pos:
            skip += 1
            continue
        
        pos = chunk_id_to_pos[chunk_id]
        vector = embeddings[pos].tolist()
        
        # Pinecone ID 必須純 ASCII，用 MD5 hash；原 chunk_id 存入 metadata
        pinecone_id = hashlib.md5(chunk_id.encode('utf-8')).hexdigest()
        batch.append({
            'id': pinecone_id,
            'values': vector,
            'metadata': {
                'chunk_id': chunk_id,
                'company': doc.get('company', ''),
                'text': doc.get('text', '')[:1000],  # Pinecone metadata 限制
                'page': str(doc.get('page', '')),
                'source': doc.get('source', ''),
            }
        })
        
        if len(batch) >= BATCH_SIZE:
            index.upsert(vectors=batch)
            success += len(batch)
            logger.info(f"進度: {success}/{total}")
            batch = []

    if batch:
        index.upsert(vectors=batch)
        success += len(batch)

    logger.info(f"遷移完成：成功 {success} 筆，跳過 {skip} 筆（無對應 FAISS 向量）")
    
    # 驗證
    stats = index.describe_index_stats()
    logger.info(f"Pinecone index 統計: {stats}")

if __name__ == '__main__':
    migrate()