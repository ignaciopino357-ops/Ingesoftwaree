"""Módulo Gestión Académica · ADAPTADOR DE ENTRADA WEB: portal del alumno (Controlador del MVC).

HU-09 ver mis notas y asistencia · HU-16 ver mi asistencia en calendario.
El alumno solo ve sus propios datos (se usa el usuario de la sesión, nunca un id de la URL)
y nunca ve el estado de riesgo.
"""
from datetime import date

from fastapi import APIRouter, Request

from app import contenedor
from app.seguridad.adaptadores.entrada_web import usuario_web
from app.seguridad.dominio import Rol
from app.web.vistas import render

router = APIRouter(prefix="/alumno", include_in_schema=False)


@router.get("")
def portal_alumno(request: Request):
    alumno = usuario_web(request, Rol.ALUMNO)
    return render(request, "alumno/portal.html", datos=contenedor.consultar_mis_datos.ejecutar(alumno))


@router.get("/asistencia")
def mi_calendario(request: Request, mes: str = ""):
    alumno = usuario_web(request, Rol.ALUMNO)
    hoy = date.today()
    try:
        anio, num_mes = (int(x) for x in mes.split("-"))
        date(anio, num_mes, 1)
    except ValueError:
        anio, num_mes = hoy.year, hoy.month
    return render(
        request, "alumno/asistencia.html",
        cal=contenedor.consultar_mi_calendario.ejecutar(alumno, anio, num_mes, hoy),
        datos=contenedor.consultar_mis_datos.ejecutar(alumno),
    )
