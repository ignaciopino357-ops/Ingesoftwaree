"""Portal alumno. HU-09 (ver mis notas y asistencia) está planificada para el Sprint 3."""
from fastapi import APIRouter, Request

from app.auth import exigir_rol
from app.web import render

router = APIRouter(prefix="/alumno")


@router.get("")
def portal_alumno(request: Request):
    exigir_rol(request, "alumno")
    return render(request, "alumno/portal.html")
