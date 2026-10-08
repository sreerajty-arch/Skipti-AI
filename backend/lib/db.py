"""Shared Mongo handle — import `client`/`db` from here (server.py, routers, seed.py)."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, IndexModel

load_dotenv(Path(__file__).parent.parent / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

logger = logging.getLogger(__name__)

# One entry per collection: every field a route filters, sorts, or dedupes on. Applied by ensure_indexes() at startup.
INDEXES: dict[str, list[IndexModel]] = {
    "status_checks": [IndexModel([("timestamp", DESCENDING)], name="timestamp_desc")],
    "auth_sessions": [
        IndexModel([("token_hash", ASCENDING)], name="token_hash", unique=True),
        IndexModel([("expires_at", ASCENDING)], name="expires_at_ttl", expireAfterSeconds=0),
    ],
    "persona_entries": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("owner_id", ASCENDING), ("category", ASCENDING)], name="owner_category"),
    ],
    "interview_sessions": [IndexModel([("id", ASCENDING)], name="id", unique=True)],
    "projects": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("owner_id", ASCENDING), ("updated_at", DESCENDING)], name="owner_updated"),
    ],
    "project_context_entries": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("owner_id", ASCENDING), ("project_id", ASCENDING)], name="owner_project"),
    ],
    "project_update_proposals": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("owner_id", ASCENDING), ("project_id", ASCENDING), ("created_at", DESCENDING)], name="owner_project_created"),
    ],
    "project_checkpoints": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("owner_id", ASCENDING), ("project_id", ASCENDING), ("revision", DESCENDING)], name="owner_project_revision", unique=True),
    ],
    "temporary_grants": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("redeem_hash", ASCENDING)], name="redeem_hash", unique=True),
        IndexModel([("expires_at", ASCENDING)], name="expires_at_ttl", expireAfterSeconds=0),
    ],
    "guest_sessions": [
        IndexModel([("session_hash", ASCENDING)], name="session_hash", unique=True),
        IndexModel([("expires_at", ASCENDING)], name="expires_at_ttl", expireAfterSeconds=0),
    ],
    "guest_chat_messages": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("session_id", ASCENDING), ("created_at", ASCENDING)], name="session_created"),
        IndexModel([("grant_id", ASCENDING), ("created_at", DESCENDING)], name="grant_created"),
        IndexModel([("expires_at", ASCENDING)], name="expires_at_ttl", expireAfterSeconds=0),
    ],
    "context_access_logs": [IndexModel([("owner_id", ASCENDING), ("created_at", DESCENDING)], name="owner_created")],
    "project_files": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("owner_id", ASCENDING), ("project_id", ASCENDING), ("created_at", DESCENDING)], name="owner_project_created"),
    ],
    "mcp_tokens": [
        IndexModel([("token_hash", ASCENDING)], name="token_hash", unique=True),
        IndexModel([("owner_id", ASCENDING), ("created_at", DESCENDING)], name="owner_created"),
    ],
}


async def ensure_indexes() -> None:
    for collection, models in INDEXES.items():
        for model in models:  # one at a time so a bad spec skips only itself
            try:
                await db[collection].create_indexes([model])
            except Exception as exc:  # never block boot on an index; the log line names what to fix
                logger.error("ensure_indexes(%s.%s): %s", collection, model.document["name"], exc)
