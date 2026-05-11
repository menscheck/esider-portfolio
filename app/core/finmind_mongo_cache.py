"""
MongoDB-backed cache for FinMind API responses.

Design goals:
- Do NOT modify existing app/core/finmind_client.py
- Provide a drop-in cache layer usable by a separate FinMind client
- Safety-first: if Mongo is unavailable, caller should fallback to memory cache
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from pymongo import MongoClient

from app.core.config import get_config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CacheKey:
    stock_id: str
    dataset: str


@dataclass
class CacheDocument:
    key_stock_id: str
    key_dataset: str
    updated_at: datetime
    data: list[dict[str, Any]]


DEFAULT_CACHE_TTL_HOURS = 24
DEFAULT_CACHE_COLLECTION = "finmind_cache"


def _get_mongo_uri() -> str | None:
    # env override (Atlas / staging)
    env_uri = os.getenv("FINMIND_MONGO_URI")
    if env_uri:
        short = env_uri.strip()
        logger.info("[FinMind Mongo cache] using FINMIND_MONGO_URI prefix=%s", short[:18])
        return short

    cfg = get_config()
    if not cfg.has_section("mongodb"):
        return None
    mongo_cfg = cfg["mongodb"]
    uri = mongo_cfg.get("uri")
    if not uri:
        return None
    return uri


def _get_cache_collection() -> str:
    cfg = get_config()
    if not cfg.has_section("mongodb"):
        return DEFAULT_CACHE_COLLECTION
    mongo_cfg = cfg["mongodb"]
    # keep the same collection_name style if caller wants
    return mongo_cfg.get("finmind_cache_collection", DEFAULT_CACHE_COLLECTION)


def _get_db_name() -> str:
    cfg = get_config()
    if not cfg.has_section("mongodb"):
        return "esg_db"
    mongo_cfg = cfg["mongodb"]
    return mongo_cfg.get("db_name", "esg_db")


def _get_collection() -> Any:
    uri = _get_mongo_uri()
    if not uri:
        raise RuntimeError("MongoDB uri missing from config.ini [mongodb].uri")

    db_name = _get_db_name()
    coll_name = _get_cache_collection()

    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    return client[db_name][coll_name]


def get_cached(cache_key: CacheKey, ttl_hours: int = DEFAULT_CACHE_TTL_HOURS) -> list[dict[str, Any]] | None:
    """
    Return cached data if present and not expired, else None.
    """
    try:
        coll = _get_collection()
        doc = coll.find_one({"key.stock_id": cache_key.stock_id, "key.dataset": cache_key.dataset})
        if not doc:
            return None

        updated_at = doc.get("updated_at")
        if not updated_at:
            return None

        cutoff = datetime.now() - timedelta(hours=ttl_hours)
        if updated_at < cutoff:
            # expired: return None (do not delete aggressively)
            return None

        data = doc.get("data", [])
        if isinstance(data, list):
            return [d for d in data if isinstance(d, dict)]
        return None
    except Exception:
        logger.exception("[FinMind Mongo cache] read failed; fallback to memory")
        return None


def save_cached(cache_key: CacheKey, data: list[dict[str, Any]]) -> None:
    """
    Save cached data into MongoDB with upsert.
    """
    try:
        coll = _get_collection()
        payload = {
            "key": {"stock_id": cache_key.stock_id, "dataset": cache_key.dataset},
            "updated_at": datetime.utcnow(),
            "data": data,
        }
        coll.update_one(
            {"key.stock_id": cache_key.stock_id, "key.dataset": cache_key.dataset},
            {"$set": payload},
            upsert=True,
        )
    except Exception:
        logger.exception("[FinMind Mongo cache] write failed; ignore")
        return None


def ensure_indexes() -> None:
    """
    Create indexes for performance (safe to call).
    """
    try:
        coll = _get_collection()
        coll.create_index([("key.stock_id", 1), ("key.dataset", 1)], unique=True)
        coll.create_index([("updated_at", 1)])
    except Exception:
        logger.exception("[FinMind Mongo cache] ensure_indexes failed")
        return None
