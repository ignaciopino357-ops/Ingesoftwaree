# API/main.py
# Punto de entrada de la aplicación FastAPI (Puntos 10.5, 10.16 y 10.19)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import inicializar_base_datos
from routers import cursos

# 1. Inicialización de tablas y precarga de SQLite
inicializar_base_datos()

# 2. Instancia de la aplicación
app = FastAPI(
    title="Sistema de Alerta Temprana de Deserción Escolar",
    description="API REST modular para gestión de trayectorias académicas y asignación de cursos.",
    version="1.0.0"
)

# 3. Configuración de CORS (Punto 10.19 de la guía)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Registro de módulos de ruta
app.include_router(cursos.router)

@app.get("/", tags=["Estado"])
def estado_api():
    """Ruta raíz para comprobación de estado y documentación."""
    return {
        "sistema": "Alerta Temprana Deserción Escolar",
        "estado": "Operativo",
        "documentacion": "/docs",
        "hu_activa": "HU 1 - Visualizar cursos asignados en panel principal"
    }