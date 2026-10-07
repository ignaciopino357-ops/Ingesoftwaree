"""Punto de entrada. Ejecutar con:  uvicorn app.main:app --reload

Monolito modular con arquitectura hexagonal (Hito 1):
  - app/seguridad   Seguridad y Usuarios
  - app/academico   Gestión Académica
  - app/riesgo      Motor de Riesgo
Cada módulo tiene dominio.py, puertos.py, casos_uso.py y adaptadores/.
Este archivo solo arma la aplicación y traduce los errores de negocio a HTTP.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.academico.adaptadores import entrada_api as api_academico
from app.academico.adaptadores import entrada_web_directiva, entrada_web_profesor
from app.compartido import db
from app.compartido.errores import ErrorDeNegocio, NoAutenticado
from app.riesgo.adaptadores import entrada_api as api_riesgo
from app.seguridad.adaptadores import entrada_api as api_seguridad
from app.seguridad.adaptadores import entrada_web, entrada_web_alumno
from app.web.vistas import ir_a, render


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    db.iniciar()  # crea tablas y datos de prueba si la base está vacía
    yield


app = FastAPI(
    title="Seguimiento de trayectorias y riesgo de deserción",
    description="API REST del monolito modular hexagonal. Use POST /api/login y luego el botón Authorize.",
    version="2.0",
    lifespan=ciclo_de_vida,
)
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "cambiar-en-produccion"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "web" / "static")), name="static")

# Adaptadores de entrada: páginas web (MVC) y API REST, conectados a los mismos casos de uso
for router in (entrada_web.router, entrada_web_alumno.router, entrada_web_profesor.router,
               entrada_web_directiva.router, api_seguridad.router, api_academico.router, api_riesgo.router):
    app.include_router(router)


def _es_api(request: Request) -> bool:
    return request.url.path.startswith("/api")


@app.exception_handler(ErrorDeNegocio)
async def error_de_negocio(request: Request, error: ErrorDeNegocio):
    """Traduce los errores del núcleo: 400, 401, 403, 404 o 409."""
    if _es_api(request):
        cuerpo = {"detail": error.mensaje}
        if error.detalles:
            cuerpo["errores"] = error.detalles
        headers = {"WWW-Authenticate": "Bearer"} if isinstance(error, NoAutenticado) else None
        return JSONResponse(cuerpo, status_code=error.codigo_http, headers=headers)
    if isinstance(error, NoAutenticado):
        return ir_a("/login")
    return render(request, "error.html", status_code=error.codigo_http, mensaje=error.mensaje)


@app.exception_handler(StarletteHTTPException)
async def error_http(request: Request, error: StarletteHTTPException):
    if _es_api(request):
        return JSONResponse({"detail": error.detail}, status_code=error.status_code)
    mensaje = "La página no existe" if error.status_code == 404 else str(error.detail)
    return render(request, "error.html", status_code=error.status_code, mensaje=mensaje)
