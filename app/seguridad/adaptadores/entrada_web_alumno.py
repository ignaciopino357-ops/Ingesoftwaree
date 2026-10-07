"""ADAPTADOR DE ENTRADA WEB: portal alumno. HU-09 (ver mis notas y asistencia) está planificada para el Sprint 3."""
from fastapi import APIRouter, Request

from app.seguridad.adaptadores.entrada_web import usuario_web
from app.seguridad.dominio import Rol
from app.web.vistas import render

router = APIRouter(prefix="/alumno", include_in_schema=False)


@router.get("")
def portal_alumno(request: Request):
    usuario_web(request, Rol.ALUMNO)
    return render(request, "alumno/portal.html")
