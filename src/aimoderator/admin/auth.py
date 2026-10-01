"""Autenticación del panel (login por env + cookie de sesión firmada)."""

from __future__ import annotations

import hmac

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from aimoderator.admin.templates_env import templates
from aimoderator.config import get_settings

router = APIRouter(tags=["admin-auth"])


def _check_credentials(username: str, password: str) -> bool:
    settings = get_settings()
    return hmac.compare_digest(username, settings.admin_username) and hmac.compare_digest(
        password, settings.admin_password
    )


@router.get("/admin/login")
async def login_form(request: Request) -> object:
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/admin/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
) -> object:
    if not _check_credentials(username, password):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Credenciales inválidas"},
            status_code=401,
        )
    request.session["admin"] = username
    return RedirectResponse("/admin", status_code=303)


@router.get("/admin/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=303)
