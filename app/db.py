import logging
from pymongo import MongoClient
from app.config import settings

logger = logging.getLogger(__name__)

# Lazy MongoDB client initialization
_client = None

def get_mongo_client():
    global _client
    if _client is None:
        try:
            _client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
            # Ping test
            _client.admin.command('ping')
            logger.info("Connected to MongoDB successfully.")
        except Exception as e:
            logger.warning(f"Could not connect to MongoDB at {settings.MONGODB_URI}: {e}")
            logger.info("Falling back to local in-memory mongomock if available or continuing...")
            try:
                import mongomock
                _client = mongomock.MongoClient()
                logger.info("Using in-memory mock MongoDB.")
            except ImportError:
                # Keep real client, will raise on query if disconnected
                pass
    return _client

def get_database():
    client = get_mongo_client()
    return client[settings.DATABASE_NAME]

def get_users_collection():
    return get_database()["users"]

def get_watched_books_collection():
    return get_database()["watched_books"]

def get_notifications_log_collection():
    return get_database()["notifications_log"]

def init_db_indexes():
    """Ensure essential indexes exist in MongoDB."""
    try:
        users = get_users_collection()
        users.create_index("username", unique=True)
        users.create_index("email", unique=True)

        watched = get_watched_books_collection()
        watched.create_index([("user_id", 1), ("item_id", 1)], unique=True)
        watched.create_index("item_id")
        watched.create_index("notify_on_available")

        notifs = get_notifications_log_collection()
        notifs.create_index("user_id")
        notifs.create_index("sent_at")
        logger.info("MongoDB indexes verified.")
    except Exception as e:
        logger.error(f"Error creating MongoDB indexes: {e}")
