from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from app.db import get_watched_books_collection
from app.auth import get_current_user
from app.library.client import catalog_client

router = APIRouter()

@router.post("/watch")
def add_to_watchlist(
    request: Request,
    item_id: str = Form(...),
    card_type: str = Form("Card1"),
    title: str = Form(...),
    author: str = Form(""),
    redirect_url: str = Form("/"),
    user: dict = Depends(get_current_user)
):
    watched_col = get_watched_books_collection()
    existing = watched_col.find_one({"user_id": user["username"], "item_id": item_id})

    if not existing:
        # Check initial availability immediately
        avail_data = catalog_client.get_book_availability(item_id, card_type)
        
        new_doc = {
            "user_id": user["username"],
            "item_id": item_id,
            "card_type": card_type,
            "title": title.strip() or avail_data.get('title', 'ספר ללא שם'),
            "author": author.strip() or avail_data.get('author', ''),
            "is_available": avail_data.get('is_available', False),
            "copies_available": avail_data.get('copies_available', 0),
            "copies_total": avail_data.get('copies_total', 0),
            "copies": avail_data.get('copies_list', []),
            "notify_on_available": True,
            "last_notified_at": None,
            "last_checked_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        watched_col.insert_one(new_doc)

    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

@router.post("/unwatch/{watch_id}")
def remove_from_watchlist(
    watch_id: str,
    redirect_url: str = Form("/"),
    user: dict = Depends(get_current_user)
):
    watched_col = get_watched_books_collection()
    query = {"user_id": user["username"]}
    if ObjectId.is_valid(watch_id):
        query["_id"] = ObjectId(watch_id)
    else:
        query["item_id"] = watch_id

    watched_col.delete_one(query)
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

@router.post("/check-now/{watch_id}")
def check_single_book_now(
    watch_id: str,
    user: dict = Depends(get_current_user)
):
    watched_col = get_watched_books_collection()
    query = {"user_id": user["username"]}
    if ObjectId.is_valid(watch_id):
        query["_id"] = ObjectId(watch_id)
    else:
        query["item_id"] = watch_id

    doc = watched_col.find_one(query)
    if doc:
        avail = catalog_client.get_book_availability(doc["item_id"], doc.get("card_type", "Card1"))
        watched_col.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "is_available": avail.get('is_available', False),
                    "copies_available": avail.get('copies_available', 0),
                    "copies_total": avail.get('copies_total', 0),
                    "copies": avail.get('copies_list', []),
                    "last_checked_at": datetime.utcnow()
                }
            }
        )

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
