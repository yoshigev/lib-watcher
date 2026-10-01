from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.db import get_users_collection
from app.auth import verify_password, create_access_token, get_current_user_optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    user = get_current_user_optional(request)
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "settings": settings,
            "error": None
        }
    )

@router.post("/login")
def handle_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    users_col = get_users_collection()
    normalized_email = email.strip().lower()
    user = users_col.find_one({"email": normalized_email})
    
    if not user or not verify_password(password, user.get("hashed_password", "")):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "settings": settings,
                "error": "כתובת אימייל או סיסמה שגויות",
                "email": email
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    token = create_access_token(data={"sub": user["email"]})
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24 * 30,
        samesite="lax",
        secure=False
    )
    return response

@router.get("/logout")
def handle_logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response
