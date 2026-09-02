from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.db import get_watched_books_collection
from app.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    user: dict = Depends(get_current_user)
):
    watched_col = get_watched_books_collection()
    cursor = watched_col.find({"user_id": user["username"]}).sort("created_at", -1)
    books = list(cursor)

    available_count = sum(1 for b in books if b.get("is_available"))
    total_watched = len(books)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "settings": settings,
        "user": user,
        "books": books,
        "available_count": available_count,
        "total_watched": total_watched
    })
