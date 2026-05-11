"""
app/core/reranker.py
Cross-Encoder Reranker — 對 FAISS 候選 chunks 做精排
"""

import logging
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

_model = None


def get_reranker() -> CrossEncoder:
    global _model
    if _model is None:
        logger.info("載入 reranker model...")
        _model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        logger.info("reranker 載入完成")
    return _model


def rerank(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """
    對候選 chunks 用 Cross-Encoder 重新排序

    Args:
        query:  使用者查詢
        chunks: FAISS 初步撈出的候選清單
        top_k:  重排後取前幾筆

    Returns:
        重排後的 chunks（含 rerank_score 欄位）
    """
    if not chunks:
        return []

    reranker = get_reranker()

    # 組合 query-chunk pairs
    pairs = [(query, chunk["text"]) for chunk in chunks]

    # Cross-Encoder 打分
    scores = reranker.predict(pairs)

    # 加入分數並排序（分數越高越相關）
    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)

    reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)

    return reranked[:top_k]
