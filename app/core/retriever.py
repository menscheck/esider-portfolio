"""
app/core/retriever.py
ESG語意搜尋 Retriever — FAISS + MongoDB
"""
from __future__ import annotations

from retriever import ESGRetriever as _BaseESGRetriever

from app.core.config import get_config as _get_config

__all__ = ["ESGRetriever"]


class ESGRetriever(_BaseESGRetriever):
    def __init__(
        self,
        faiss_index_path: str = "data/faiss_index/esg.index",
        id_map_path: str = "data/faiss_index/id_map.json",
        mongo_uri: str | None = None,
        db_name: str = "esg_db",
        collection_name: str = "chunks",
        model_name: str = "BAAI/bge-m3",
    ):
        if mongo_uri is None:
            mongo_uri = _get_config()["mongodb"]["uri"]

        super().__init__(
            faiss_index_path=faiss_index_path,
            id_map_path=id_map_path,
            mongo_uri=mongo_uri,
            db_name=db_name,
            collection_name=collection_name,
            model_name=model_name,
        )
