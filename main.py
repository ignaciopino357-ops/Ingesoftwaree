# main.py  (raíz del proyecto)
# Ejecutar desde esta carpeta:  uvicorn main:app --reload
# Portal web:                   http://127.0.0.1:8000/app/
# Documentación interactiva:    http://127.0.0.1:8000/docs

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from API.database import inicializar_base_datos
from API.routers import auth, carga, cursos, estudiantes

DIRECTORIO_FRONTEND = Path(__file__).resolve().parent / "frontend"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    inicializar_base_datos()  # crea tablas y datos de prueba al arrancar
    yield


app = FastAPI(
    title="Sistema de Alerta Temprana de Deserción Escolar",
    description="API REST modular para gestión de trayectorias académicas y asignación de cursos.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cursos.router)
app.include_router(estudiantes.router)
app.include_router(carga.router)


@app.get("/", tags=["Estado"])
def estado_api():
    return {
        "sistema": "Alerta Temprana Deserción Escolar",
        "estado": "Operativo",
        "documentacion": "/docs",
        "portal": "/app/",
    }


# El frontend se sirve desde el mismo servidor (se monta al final para no tapar las rutas /api)
if DIRECTORIO_FRONTEND.is_dir():
    app.mount("/app", StaticFiles(directory=DIRECTORIO_FRONTEND, html=True), name="frontend")
