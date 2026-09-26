# API/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from database import inicializar_base_datos
from routers import cursos, estudiantes, carga

inicializar_base_datos()

app = FastAPI(
    title="Sistema de Alerta Temprana de Deserción Escolar",
    description="API REST modular para gestión de trayectorias académicas y asignación de cursos.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cursos.router)
app.include_router(estudiantes.router)
app.include_router(carga.router)

DIR = Path(__file__).resolve().parent

@app.get("/", tags=["Estado"])
def estado_api():
    return {
        "sistema": "Alerta Temprana Deserción Escolar",
        "estado": "Operativo",
        "documentacion": "/docs",
        "portal": "Abre index.html en el navegador para entrar al sistema",
    }
