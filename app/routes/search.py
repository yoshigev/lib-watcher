from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.db import get_watched_books_collection
from app.auth import get_current_user
from app.library.client import catalog_client

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/search", response_class=HTMLResponse)
def search_page(
    request: Request,
    q: Optional[str] = Query(None),
    field: str = Query("General"),
    card_type: str = Query("Card1"),
    user: dict = Depends(get_current_user)
):
    results = None
    watched_col = get_watched_books_collection()
    user_watched = watched_col.find({"user_id": user["username"]}, {"item_id": 1})
    watched_item_ids = set(doc["item_id"] for doc in user_watched)

    if q and q.strip():
        search_data = catalog_client.search(query=q.strip(), field=field, card_type=card_type)
        results = search_data

    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={
            "settings": settings,
            "user": user,
            "query": q or "",
            "field": field,
            "card_type": card_type,
            "results": results,
            "watched_item_ids": watched_item_ids
        }
    )
