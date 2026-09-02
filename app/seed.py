import logging
from datetime import datetime
from app.config import settings
from app.db import get_users_collection
from app.auth import hash_password

logger = logging.getLogger(__name__)

def seed_predefined_users():
    """Seed users defined in config/env into MongoDB if not present."""
    users_col = get_users_collection()
    users_to_seed = settings.parsed_seed_users
    
    for u_data in users_to_seed:
        username = u_data.get("username", "").strip()
        email = u_data.get("email", "").strip()
        password = u_data.get("password", "")
        if not username or not password:
            continue
        
        existing = users_col.find_one({
            "$or": [{"username": username}, {"email": email}]
        })
        
        if not existing:
            new_doc = {
                "username": username,
                "email": email or f"{username}@example.local",
                "hashed_password": hash_password(password),
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            users_col.insert_one(new_doc)
            logger.info(f"Seeded user into MongoDB: {username} ({email})")
        else:
            logger.info(f"User '{username}' already exists in MongoDB.")
