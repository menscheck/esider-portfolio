import configparser
import os
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


def _get_mongo_uri() -> str:
    cp = configparser.ConfigParser()
    cp.read(
        os.path.join(os.path.dirname(__file__), "..", "..", "config.ini"),
        encoding="utf-8",
    )
    return cp.get(
        "mongodb",
        "uri",
        fallback=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
    )


MONGO_URI = _get_mongo_uri()
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "esg_agent")

mongo_client: Optional[AsyncIOMotorClient] = None
mongo_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    global mongo_client, mongo_database

    if mongo_client is None:
        mongo_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_database = mongo_client[MONGO_DB_NAME]


async def close_mongo_connection() -> None:
    global mongo_client, mongo_database

    if mongo_client is not None:
        mongo_client.close()
        mongo_client = None
        mongo_database = None


def get_database() -> AsyncIOMotorDatabase:
    if mongo_database is None:
        raise RuntimeError("MongoDB connection has not been initialized.")
    return mongo_database
