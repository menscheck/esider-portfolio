"""
app/core/retriever.py
ESG語意搜尋 Retriever — Pinecone（thin wrapper）
"""
from __future__ import annotations

from retriever import ESGRetriever as _BaseESGRetriever

__all__ = ["ESGRetriever"]


class ESGRetriever(_BaseESGRetriever):
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        super().__init__(model_name=model_name)
