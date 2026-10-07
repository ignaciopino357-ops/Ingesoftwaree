"""Punto de entrada. Ejecutar con:  uvicorn app.main:app --reload"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app import db
from app.auth import NoAutenticado
from app.routers import alumno, directiva, login, profesor
from app.web import ir_a, render


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    db.iniciar()  # crea tablas y datos de prueba si la base está vacía
    yield


app = FastAPI(title="Seguimiento de trayectorias y riesgo de deserción", lifespan=ciclo_de_vida)

# La clave firma la cookie de sesión. En producción se define con la variable SECRET_KEY.
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "cambiar-en-produccion"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

app.include_router(login.router)
app.include_router(directiva.router)
app.include_router(profesor.router)
app.include_router(alumno.router)


@app.exception_handler(NoAutenticado)
async def sin_sesion(request: Request, exc: NoAutenticado):
    return ir_a("/login")


@app.exception_handler(HTTPException)
async def error_http(request: Request, exc: HTTPException):
    return render(request, "error.html", status_code=exc.status_code, mensaje=exc.detail)
