"""
retriever.py
ESG語意搜尋 Retriever — Pinecone
"""

import configparser
import logging
from typing import Optional

import numpy as np
import torch
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class ESGRetriever:
    """
    Pinecone 語意搜尋
    用法：
        retriever = ESGRetriever()
        results = retriever.search("碳排放減量目標", company="台積電", top_k=5)
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        config_path: str = "config.ini",
    ):
        cp = configparser.ConfigParser()
        cp.read(config_path, encoding="utf-8")

        pc = Pinecone(api_key=cp["pinecone"]["api_key"])
        self.index = pc.Index(cp["pinecone"]["index_name"])

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"載入 embedding model，device={self.device}")
        self.model = SentenceTransformer(model_name, device=self.device)

    def reload_index(self):
        """相容舊介面，Pinecone 無需重載"""
        pass

    def search(
        self,
        query: str,
        company: Optional[str] = None,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
    ) -> list[dict]:
        """
        語意搜尋

        Args:
            query:           使用者查詢文字
            company:         限定公司名稱（None = 全部公司）
            top_k:           回傳筆數
            score_threshold: cosine 相似度下限（越大越相似，None = 不過濾）

        Returns:
            List[dict]，每筆包含：
                text, company, source, page, chunk_id, score
        """
        if not query.strip():
            return []

        query_vec = self.model.encode(
            [query],
            device=self.device,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)[0].tolist()

        pinecone_filter = {"company": {"$eq": company}} if company else None

        response = self.index.query(
            vector=query_vec,
            top_k=top_k,
            filter=pinecone_filter,
            include_metadata=True,
        )

        results = []
        for match in response.matches:
            score = match.score
            if score_threshold is not None and score < score_threshold:
                continue
            meta = match.metadata or {}
            results.append({
                "chunk_id": meta.get("chunk_id", match.id),
                "company":  meta.get("company", ""),
                "source":   meta.get("source", ""),
                "page":     meta.get("page", ""),
                "text":     meta.get("text", ""),
                "score":    score,
            })

        return results

    def search_multi_company(
        self,
        query: str,
        companies: list[str],
        top_k_per_company: int = 3,
    ) -> dict[str, list[dict]]:
        """
        跨多家公司搜尋，回傳 {公司名: [chunks]}
        """
        return {
            company: self.search(query, company=company, top_k=top_k_per_company)
            for company in companies
        }

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass
