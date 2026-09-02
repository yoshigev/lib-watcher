import logging
from datetime import datetime
from collections import defaultdict
from typing import Dict, Any
from app.db import get_watched_books_collection, get_notifications_log_collection, get_users_collection
from app.library.client import catalog_client
from app.email_sender import send_book_available_email

logger = logging.getLogger(__name__)

def check_all_watched_books() -> Dict[str, Any]:
    """
    Polls the catalog for all watched books in MongoDB:
    1. Fetches all watched_books with notify_on_available=True
    2. Groups by (item_id, card_type)
    3. Fetches live availability
    4. Sends Brevo notification if status changed from Unavailable -> Available
    5. Updates MongoDB documents
    """
    logger.info("Starting availability check for watched books in MongoDB...")
    watched_col = get_watched_books_collection()
    notifs_col = get_notifications_log_collection()
    users_col = get_users_collection()

    watched_entries = list(watched_col.find({"notify_on_available": True}))
    if not watched_entries:
        logger.info("No books currently in watchlist. Skipping check.")
        return {"status": "ok", "checked_count": 0, "notified_count": 0}

    # Group by item_id
    grouped = defaultdict(list)
    for entry in watched_entries:
        grouped[(entry.get("item_id"), entry.get("card_type", "Card1"))].append(entry)

    logger.info(f"Checking {len(grouped)} unique books across {len(watched_entries)} watch subscriptions...")
    notified_count = 0

    for (item_id, card_type), subscriptions in grouped.items():
        avail_data = catalog_client.get_book_availability(item_id, card_type)
        is_now_available = avail_data.get('is_available', False)
        copies_avail = avail_data.get('copies_available', 0)
        copies_tot = avail_data.get('copies_total', 0)
        copies_list = avail_data.get('copies_list', [])

        for sub in subscriptions:
            prev_available = sub.get("is_available")
            user_id = sub.get("user_id")
            sub_id = sub.get("_id")
            title = sub.get("title") or avail_data.get("title", "ספר ללא שם")
            author = sub.get("author") or avail_data.get("author", "")

            # Update document fields
            update_fields = {
                "is_available": is_now_available,
                "copies_available": copies_avail,
                "copies_total": copies_tot,
                "copies": copies_list,
                "last_checked_at": datetime.utcnow()
            }
            if not sub.get("title") and avail_data.get("title"):
                update_fields["title"] = avail_data["title"]
            if not sub.get("author") and avail_data.get("author"):
                update_fields["author"] = avail_data["author"]

            # Check if notification should fire
            should_notify = (
                is_now_available and 
                (prev_available is False or prev_available is None or sub.get("last_notified_at") is None)
            )

            if should_notify:
                user = users_col.find_one({"username": user_id})
                recipient_email = user.get("email") if user else None

                if recipient_email:
                    logger.info(
                        f"Book '{title}' (#{item_id}) became available ({copies_avail}/{copies_tot})! Sending email to {recipient_email}..."
                    )
                    sent = send_book_available_email(
                        to_email=recipient_email,
                        book_title=title,
                        book_author=author,
                        item_id=item_id,
                        copies_available=copies_avail,
                        copies_total=copies_tot,
                        copies_details=copies_list
                    )

                    notifs_col.insert_one({
                        "user_id": user_id,
                        "item_id": item_id,
                        "title": title,
                        "recipient_email": recipient_email,
                        "status": "sent" if sent else "failed",
                        "details": f"Available copies: {copies_avail}/{copies_tot}",
                        "sent_at": datetime.utcnow()
                    })
                    update_fields["last_notified_at"] = datetime.utcnow()
                    notified_count += 1

            watched_col.update_one({"_id": sub_id}, {"$set": update_fields})

    logger.info("Availability check completed successfully.")
    return {
        "status": "success",
        "unique_books_checked": len(grouped),
        "total_subscriptions": len(watched_entries),
        "notified_count": notified_count,
        "timestamp": datetime.utcnow().isoformat()
    }
