import logging
from datetime import datetime
from app.config import settings
from app.db import (
    get_notifications_log_collection,
    get_users_collection,
    get_watched_books_collection,
)
from app.auth import hash_password, verify_password

logger = logging.getLogger(__name__)

def seed_predefined_users():
    """Seed users defined in config/env into MongoDB if not present."""
    users_col = get_users_collection()
    users_to_seed = settings.parsed_seed_users
    
    for u_data in users_to_seed:
        email = str(u_data.get("email") or u_data.get("username") or "").strip().lower()
        password = str(u_data.get("password") or "")
        if not email or not password:
            continue
        username = email
        
        existing = users_col.find_one({
            "$or": [{"email": email}, {"username": email}]
        })
        
        if not existing:
            new_doc = {
                "username": username,
                "email": email,
                "hashed_password": hash_password(password),
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            users_col.insert_one(new_doc)
            logger.info(f"Seeded user into MongoDB: {username} ({email})")
        else:
            old_username = existing.get("username")
            update_fields = {}
            if old_username != username:
                update_fields["username"] = username
            if existing.get("email") != email:
                update_fields["email"] = email
            if not verify_password(password, existing.get("hashed_password", "")):
                update_fields["hashed_password"] = hash_password(password)

            if update_fields:
                users_col.update_one({"_id": existing["_id"]}, {"$set": update_fields})
                if old_username and old_username != username:
                    get_watched_books_collection().update_many(
                        {"user_id": old_username}, {"$set": {"user_id": username}}
                    )
                    get_notifications_log_collection().update_many(
                        {"user_id": old_username}, {"$set": {"user_id": username}}
                    )
                logger.info(f"Updated seeded user account: {username}")
            else:
                logger.info(f"Seeded user account is current: {username}")
