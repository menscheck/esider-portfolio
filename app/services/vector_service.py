import chromadb
from chromadb.config import Settings
from typing import List, Dict
import uuid

# 持久化目錄
client = chromadb.Client(Settings(
    persist_directory="./chroma_db",
    anonymized_telemetry=False
))

collection = client.get_or_create_collection(name="esg_chunks")

def add_chunks(chunks: List[str], embeddings: List[List[float]], metadatas: List[Dict] = None):
    if not metadatas:
        metadatas = [{} for _ in chunks]
        
    ids = [str(uuid.uuid4()) for _ in chunks]
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

def search_similar_chunks(query_embedding: List[float], top_k: int = 5):
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    docs = results.get("documents", [[]])[0]
    scores = results.get("distances", [[]])[0]  # 距離越小越相似（Chroma）
    out = []
    for d, s in zip(docs, scores):
        out.append({"text": d, "score": float(1 - s)})  # 轉成相似度
    return out
