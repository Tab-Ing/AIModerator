"""Dependencias del panel de administración."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status


def require_admin(request: Request) -> str:
    """Exige sesión de administrador; si no, redirige al login."""
    admin = request.session.get("admin")
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/admin/login"},
        )
    return str(admin)


def flash(request: Request, message: str) -> None:
    request.session["flash"] = message


AdminParam = Annotated[str, Depends(require_admin)]
