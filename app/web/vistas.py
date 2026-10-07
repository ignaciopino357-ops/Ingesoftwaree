"""Utilidades del adaptador web (la "Vista" del patrón MVC): plantillas, avisos y redirecciones."""
from pathlib import Path

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.seguridad.dominio import NOMBRE_ROL

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.globals["NOMBRE_ROL"] = NOMBRE_ROL


def avisar(request: Request, texto: str, tipo: str = "ok") -> None:
    """Guarda un mensaje para mostrarlo en la siguiente página (tipo: ok | error)."""
    request.session["aviso"] = {"texto": texto, "tipo": tipo}


def render(request: Request, plantilla: str, status_code: int = 200, **contexto):
    if "usuario" not in contexto:
        from app.seguridad.adaptadores.entrada_web import usuario_en_sesion
        contexto["usuario"] = usuario_en_sesion(request)
    contexto["aviso"] = request.session.pop("aviso", None)
    return templates.TemplateResponse(request, plantilla, contexto, status_code=status_code)


def ir_a(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)
