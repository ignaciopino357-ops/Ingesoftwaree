"""Utilidades compartidas por los routers: plantillas, avisos y redirecciones."""
from pathlib import Path

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import usuario_actual

BASE = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE / "templates"))


def avisar(request: Request, texto: str, tipo: str = "ok") -> None:
    """Guarda un mensaje para mostrarlo en la siguiente página (tipo: ok | error)."""
    request.session["aviso"] = {"texto": texto, "tipo": tipo}


def render(request: Request, plantilla: str, status_code: int = 200, **contexto):
    contexto.setdefault("usuario", usuario_actual(request))
    contexto["aviso"] = request.session.pop("aviso", None)
    return templates.TemplateResponse(request, plantilla, contexto, status_code=status_code)


def ir_a(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)
