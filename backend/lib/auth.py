import os
from typing import Any

import httpx
from fastapi import HTTPException, Request, Response
from sqlalchemy import text

from lib.supabase_db import SessionFactory
from models.skipti import UserView


SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
PUBLISHABLE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
ACCESS_COOKIE = "skipti_access"
REFRESH_COOKIE = "skipti_refresh"


def _auth_headers(token: str | None = None) -> dict[str, str]:
    headers = {"apikey": PUBLISHABLE_KEY, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _set_session_cookies(response: Response, session: dict[str, Any]) -> None:
    secure = os.environ.get("COOKIE_SECURE", "true").lower() == "true"
    response.set_cookie(ACCESS_COOKIE, session["access_token"], httponly=True, secure=secure, samesite="lax", path="/", max_age=int(session.get("expires_in", 3600)))
    if session.get("refresh_token"):
        response.set_cookie(REFRESH_COOKIE, session["refresh_token"], httponly=True, secure=secure, samesite="lax", path="/", max_age=60 * 60 * 24 * 30)


def clear_session_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


async def supabase_signup(email: str, password: str, display_name: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20) as client:
        result = await client.post(
            f"{SUPABASE_URL}/auth/v1/signup",
            headers=_auth_headers(),
            json={"email": email, "password": password, "data": {"display_name": display_name}},
        )
    if result.status_code >= 400:
        detail = result.json().get("msg") or result.json().get("message") or "Could not create account"
        raise HTTPException(status_code=400, detail=detail)
    return result.json()


async def supabase_login(email: str, password: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20) as client:
        result = await client.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers=_auth_headers(),
            json={"email": email, "password": password},
        )
    if result.status_code >= 400:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return result.json()


async def _fetch_user(access_token: str) -> dict[str, Any] | None:
    async with httpx.AsyncClient(timeout=12) as client:
        result = await client.get(f"{SUPABASE_URL}/auth/v1/user", headers=_auth_headers(access_token))
    return result.json() if result.status_code == 200 else None


async def _refresh_session(refresh_token: str) -> dict[str, Any] | None:
    async with httpx.AsyncClient(timeout=20) as client:
        result = await client.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
            headers=_auth_headers(),
            json={"refresh_token": refresh_token},
        )
    return result.json() if result.status_code == 200 else None


async def require_user(request: Request, response: Response) -> str:
    access_token = request.cookies.get(ACCESS_COOKIE)
    user = await _fetch_user(access_token) if access_token else None
    if not user:
        refresh = request.cookies.get(REFRESH_COOKIE)
        session = await _refresh_session(refresh) if refresh else None
        if session:
            _set_session_cookies(response, session)
            user = session.get("user") or await _fetch_user(session["access_token"])
    if not user or not user.get("id"):
        clear_session_cookies(response)
        raise HTTPException(status_code=401, detail="Authentication required")
    request.state.user = user
    return str(user["id"])


async def get_user_view(owner_id: str) -> UserView:
    if SessionFactory is None:
        raise HTTPException(status_code=503, detail="Account service unavailable")
    async with SessionFactory() as session:
        row = (await session.execute(
            text("select email, display_name from public.users where user_id = cast(:user_id as uuid)"),
            {"user_id": owner_id},
        )).mappings().one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Account profile not found")
    return UserView(id=owner_id, email=row["email"], display_name=row["display_name"], auth_mode="supabase_email")


async def establish_session(response: Response, auth_result: dict[str, Any]) -> UserView | None:
    if not auth_result.get("access_token"):
        return None
    _set_session_cookies(response, auth_result)
    user = auth_result["user"]
    return await get_user_view(str(user["id"]))